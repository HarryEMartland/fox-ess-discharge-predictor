import hashlib
import logging
import time
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.foxesscloud.com'
HISTORY_PATH = '/op/v0/device/history/query'
DEVICE_DETAIL_PATH = '/op/v1/device/detail'
SCHEDULER_ENABLE_PATH = '/op/v2/device/scheduler/enable'


@dataclass
class HistoryDataPoint:
    time: int | str
    value: float


@dataclass
class HistoryVariable:
    variable: str
    unit: str
    name: str = ''
    data: list[HistoryDataPoint] = field(default_factory=list)


@dataclass
class HistoryDeviceResult:
    device_sn: str
    variables: list[HistoryVariable] = field(default_factory=list)


@dataclass
class DeviceFunction:
    scheduler: bool = False


@dataclass
class BatteryInfo:
    battery_sn: str = ''
    type: str = ''
    version: str = ''
    model: str = ''
    capacity: int = 0
    product_date: int = 0


@dataclass
class DeviceDetail:
    device_sn: str = ''
    module_sn: str = ''
    station_id: str = ''
    station_name: str = ''
    afci_version: str = ''
    manager_version: str = ''
    master_version: str = ''
    slave_version: str = ''
    hardware_version: str = ''
    status: int = 0
    capacity: float = 0.0
    third_party_gen: bool = False
    function: DeviceFunction | None = None
    battery_list: list[BatteryInfo] = field(default_factory=list)


@dataclass
class SchedulerExtraParam:
    minSocOnGrid: float | None = None
    fdSoc: float | None = None
    fdPwr: float | None = None
    maxSoc: float | None = None
    importLimit: float | None = None
    exportLimit: float | None = None
    pvLimit: float | None = None
    reactivePower: float | None = None


@dataclass
class TimeSegment:
    enable: int
    startHour: int
    startMinute: int
    endHour: int
    endMinute: int
    workMode: str
    extraParam: SchedulerExtraParam | None = None


@dataclass
class SchedulerEnableResult:
    device_sn: str
    is_default: bool = False


class FoxESSClientError(Exception):
    pass


class FoxESSClient:
    def __init__(self, api_key: str, base_url: str = BASE_URL):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')

    def _build_headers(self, path: str) -> dict:
        timestamp = str(int(time.time() * 1000))
        raw = rf'{path}\r\n{self.api_key}\r\n{timestamp}'
        signature = hashlib.md5(raw.encode('utf-8')).hexdigest()
        return {
            'token': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'lang': 'en',
            'Content-Type': 'application/json',
        }

    def get_device_history(
        self,
        sn: str,
        variables: list[str] | None = None,
        begin: int | None = None,
        end: int | None = None,
    ) -> list[HistoryDeviceResult]:
        body: dict = {'sn': sn}
        if variables is not None:
            body['variables'] = variables
        if begin is not None:
            body['begin'] = begin
        if end is not None:
            body['end'] = end

        url = f'{self.base_url}{HISTORY_PATH}'
        headers = self._build_headers(HISTORY_PATH)

        logger.info('Fetching history data for device %s', sn)
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()

        payload = resp.json()
        errno = payload.get('errno', -1)
        if errno != 0:
            raise FoxESSClientError(f'API error (errno={errno}): {payload.get("msg", "unknown")}')

        results: list[HistoryDeviceResult] = []
        for device_result in payload.get('result', []):
            device_sn = device_result.get('deviceSN', sn)
            variables_list = []
            for var_item in device_result.get('datas', []):
                points = [
                    HistoryDataPoint(time=dp['time'], value=dp['value'])
                    for dp in var_item.get('data', [])
                ]
                variables_list.append(
                    HistoryVariable(
                        variable=var_item.get('variable', ''),
                        unit=var_item.get('unit', ''),
                        name=var_item.get('name', ''),
                        data=points,
                    )
                )
            results.append(HistoryDeviceResult(device_sn=device_sn, variables=variables_list))

        return results

    def get_device_detail(self, sn: str) -> DeviceDetail:
        url = f'{self.base_url}{DEVICE_DETAIL_PATH}'
        headers = self._build_headers(DEVICE_DETAIL_PATH)
        params = {'sn': sn}

        logger.info('Fetching device detail for %s', sn)
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()

        payload = resp.json()
        errno = payload.get('errno', -1)
        if errno != 0:
            raise FoxESSClientError(f'API error (errno={errno}): {payload.get("msg", "unknown")}')

        result = payload.get('result', {})
        if not result:
            raise FoxESSClientError('API returned empty result')

        function = None
        func_data = result.get('function')
        if func_data is not None:
            function = DeviceFunction(scheduler=func_data.get('scheduler', False))

        battery_list = []
        for bat in result.get('batteryList', []):
            battery_list.append(
                BatteryInfo(
                    battery_sn=bat.get('batterySN', ''),
                    type=bat.get('type', ''),
                    version=bat.get('version', ''),
                    model=bat.get('model', ''),
                    capacity=bat.get('capicty', 0),
                    product_date=bat.get('productDate', 0),
                )
            )

        return DeviceDetail(
            device_sn=result.get('deviceSN', ''),
            module_sn=result.get('moduleSN', ''),
            station_id=result.get('stationID', ''),
            station_name=result.get('stationName', ''),
            afci_version=result.get('afciVersion', ''),
            manager_version=result.get('managerVersion', ''),
            master_version=result.get('masterVersion', ''),
            slave_version=result.get('slaveVersion', ''),
            hardware_version=result.get('hardwareVersion', ''),
            status=result.get('status', 0),
            capacity=result.get('capacity', 0.0),
            third_party_gen=result.get('thirdPartyGen', False),
            function=function,
            battery_list=battery_list,
        )


    def set_time_segment(
        self,
        device_sn: str,
        groups: list[TimeSegment],
        is_default: bool = False,
    ) -> SchedulerEnableResult:
        body: dict = {'deviceSN': device_sn, 'groups': []}
        for g in groups:
            group_dict = {
                'enable': g.enable,
                'startHour': g.startHour,
                'startMinute': g.startMinute,
                'endHour': g.endHour,
                'endMinute': g.endMinute,
                'workMode': g.workMode,
            }
            if g.extraParam is not None:
                extra = {k: v for k, v in vars(g.extraParam).items() if v is not None}
                if extra:
                    group_dict['extraParam'] = extra
            body['groups'].append(group_dict)

        if is_default:
            body['isDefault'] = True

        url = f'{self.base_url}{SCHEDULER_ENABLE_PATH}'
        headers = self._build_headers(SCHEDULER_ENABLE_PATH)

        logger.info('Setting time segment for device %s (%d groups)', device_sn, len(groups))
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()

        payload = resp.json()
        errno = payload.get('errno', -1)
        if errno != 0:
            raise FoxESSClientError(f'API error (errno={errno}): {payload.get("msg", "unknown")}')

        result = payload.get('result', {})
        return SchedulerEnableResult(
            device_sn=result.get('deviceSN', ''),
            is_default=result.get('isDefault', False),
        )


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='FoxESS device history query')
    parser.add_argument('api_key', help='FoxESS API key')
    parser.add_argument('sn', help='Device serial number')
    parser.add_argument('--variables', nargs='*', default=None, help='Variables to query')
    parser.add_argument('--begin', type=int, default=None, help='Start timestamp (ms)')
    parser.add_argument('--end', type=int, default=None, help='End timestamp (ms)')
    parser.add_argument('--base-url', default=BASE_URL, help='API base URL')
    args = parser.parse_args()

    client = FoxESSClient(api_key=args.api_key, base_url=args.base_url)

    sn = args.sn
    print(f'Querying history for device {sn}...', file=sys.stderr)

    results = client.get_device_history(
        sn=sn,
        variables=args.variables,
        begin=args.begin,
        end=args.end,
    )

    for device_result in results:
        print(f'\nDevice: {device_result.device_sn}')
        for var in device_result.variables:
            print(f'\n  Variable: {var.variable} ({var.unit})')
            if not var.data:
                print('    (no data)')
            for dp in var.data:
                print(f'    time={dp.time}  value={dp.value}')
