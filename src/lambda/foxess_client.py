import hashlib
import logging
import time
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.foxesscloud.com'
HISTORY_PATH = '/op/v0/device/history/query'


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
