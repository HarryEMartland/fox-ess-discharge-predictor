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
    time: int
    value: float


@dataclass
class HistoryVariable:
    variable: str
    unit: str
    data: list[HistoryDataPoint] = field(default_factory=list)


@dataclass
class HistoryResult:
    sn: str
    variables: list[HistoryVariable] = field(default_factory=list)


class FoxESSClientError(Exception):
    pass


class FoxESSClient:
    def __init__(self, api_key: str, base_url: str = BASE_URL):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')

    def _build_headers(self, path: str) -> dict:
        timestamp = str(int(time.time() * 1000))
        raw = f'{path}\r\n{self.api_key}\r\n{timestamp}'
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
    ) -> HistoryResult:
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

        result_data = payload.get('result', {})
        sn_value = result_data.get('sn', sn)
        variables_raw = result_data.get('data', [])

        variables_list = []
        for var_item in variables_raw:
            points = [
                HistoryDataPoint(time=dp['time'], value=dp['value'])
                for dp in var_item.get('data', [])
            ]
            variables_list.append(
                HistoryVariable(
                    variable=var_item.get('variable', ''),
                    unit=var_item.get('unit', ''),
                    data=points,
                )
            )

        return HistoryResult(sn=sn_value, variables=variables_list)
