import hashlib

import pytest
import requests
from foxess_client import (
    BatteryInfo,
    DeviceDetail,
    DeviceFunction,
    FoxESSClient,
    FoxESSClientError,
    HistoryDataPoint,
    HistoryDeviceResult,
    HistoryVariable,
)

MOCK_API_KEY = 'test-api-key-12345'
MOCK_SN = 'ABC123DEF'

HISTORY_PATH = '/op/v0/device/history/query'
DEVICE_DETAIL_PATH = '/op/v1/device/detail'

MOCK_SUCCESS_BODY = {
    'errno': 0,
    'result': [
        {
            'deviceSN': MOCK_SN,
            'datas': [
                {
                    'variable': 'pvPower',
                    'unit': 'kW',
                    'name': 'PVPower',
                    'data': [
                        {'time': 1712534400000, 'value': 1.5},
                        {'time': 1712534700000, 'value': 1.8},
                    ],
                },
                {
                    'variable': 'feedinPower',
                    'unit': 'kW',
                    'name': 'FeedinPower',
                    'data': [
                        {'time': 1712534400000, 'value': 0.3},
                        {'time': 1712534700000, 'value': 0.5},
                    ],
                },
            ],
        },
    ],
}


MOCK_DEVICE_DETAIL_BODY = {
    'errno': 0,
    'result': {
        'deviceSN': MOCK_SN,
        'moduleSN': 'MOD123',
        'stationID': 'STN456',
        'stationName': 'Test Station',
        'afciVersion': '1.0',
        'managerVersion': '2.0',
        'masterVersion': '3.0',
        'slaveVersion': '4.0',
        'hardwareVersion': '5.0',
        'status': 1,
        'capacity': 5.0,
        'thirdPartyGen': False,
        'function': {'scheduler': True},
        'batteryList': [
            {
                'batterySN': 'BAT001',
                'type': 'master',
                'version': '1.1',
                'model': 'LV5200',
                'capicty': 5200,
                'productDate': 1700000000000,
            },
        ],
    },
}


@pytest.fixture
def client(httpserver):
    base_url = httpserver.url_for('').rstrip('/')
    return FoxESSClient(api_key=MOCK_API_KEY, base_url=base_url)


def _mock_auth_headers(request):
    token = request.headers.get('token', '')
    timestamp = request.headers.get('timestamp', '')
    signature = request.headers.get('signature', '')
    expected_raw = f'{request.path}\r\n{token}\r\n{timestamp}'
    expected_sig = hashlib.md5(expected_raw.encode('utf-8')).hexdigest()
    return token == MOCK_API_KEY and signature == expected_sig


class TestFoxESSClientAuth:
    def test_build_headers_contains_required_fields(self):
        client = FoxESSClient(api_key='my-key')
        headers = client._build_headers(HISTORY_PATH)
        assert 'token' in headers
        assert 'timestamp' in headers
        assert 'signature' in headers
        assert 'lang' in headers
        assert 'Content-Type' in headers

    def test_build_headers_signature_is_valid_md5(self):
        client = FoxESSClient(api_key='my-key')
        headers = client._build_headers(HISTORY_PATH)
        raw = rf'{HISTORY_PATH}\r\nmy-key\r\n{headers["timestamp"]}'
        expected = hashlib.md5(raw.encode('utf-8')).hexdigest()
        assert headers['signature'] == expected

    def test_build_headers_lang_is_en(self):
        client = FoxESSClient(api_key='my-key')
        headers = client._build_headers(HISTORY_PATH)
        assert headers['lang'] == 'en'

    def test_build_headers_token_matches_api_key(self):
        client = FoxESSClient(api_key='my-key')
        headers = client._build_headers(HISTORY_PATH)
        assert headers['token'] == 'my-key'


class TestFoxESSClientRequests:
    def test_get_device_history_returns_list(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        results = client.get_device_history(sn=MOCK_SN)
        assert isinstance(results, list)
        assert len(results) == 1

    def test_get_device_history_returns_device_sn(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        results = client.get_device_history(sn=MOCK_SN)
        assert results[0].device_sn == MOCK_SN

    def test_get_device_history_returns_expected_variables(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        results = client.get_device_history(sn=MOCK_SN, variables=['pvPower', 'feedinPower'])
        assert len(results[0].variables) == 2
        assert results[0].variables[0].variable == 'pvPower'
        assert results[0].variables[1].variable == 'feedinPower'

    def test_get_device_history_returns_datapoints(self, httpserver, client):
        body = {
            'errno': 0,
            'result': [
                {
                    'deviceSN': MOCK_SN,
                    'datas': [
                        {
                            'variable': 'pvPower',
                            'unit': 'kW',
                            'name': 'PVPower',
                            'data': [
                                {'time': 1712534400000, 'value': 1.5},
                                {'time': 1712534700000, 'value': 1.8},
                            ],
                        },
                    ],
                },
            ],
        }
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(body)
        results = client.get_device_history(sn=MOCK_SN, variables=['pvPower'])
        var = results[0].variables[0]
        assert len(var.data) == 2
        assert var.data[0].time == 1712534400000
        assert var.data[0].value == 1.5
        assert var.data[1].time == 1712534700000
        assert var.data[1].value == 1.8

    def test_get_device_history_no_variables_returns_all(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        results = client.get_device_history(sn=MOCK_SN)
        assert len(results[0].variables) > 0

    def test_get_device_history_with_time_range(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        begin = 1712534400000
        end = 1712620800000
        results = client.get_device_history(sn=MOCK_SN, variables=['pvPower'], begin=begin, end=end)
        assert results[0].variables[0].variable == 'pvPower'

    def test_get_device_history_unit_is_returned(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        results = client.get_device_history(sn=MOCK_SN, variables=['pvPower'])
        assert results[0].variables[0].unit == 'kW'

    def test_get_device_history_empty_variable_returns_empty_data(self, httpserver, client):
        body = {
            'errno': 0,
            'result': [
                {
                    'deviceSN': MOCK_SN,
                    'datas': [
                        {'variable': 'unknownVar', 'unit': '', 'name': '', 'data': []},
                    ],
                },
            ],
        }
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(body)
        results = client.get_device_history(sn=MOCK_SN, variables=['unknownVar'])
        assert len(results[0].variables) == 1
        assert results[0].variables[0].variable == 'unknownVar'
        assert results[0].variables[0].data == []


class TestFoxESSClientErrors:
    def test_api_error_raises_exception(self, httpserver, client):
        body = {'errno': 40001, 'msg': 'device not found'}
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(body)
        with pytest.raises(FoxESSClientError) as exc:
            client.get_device_history(sn='ERROR-SN')
        assert 'device not found' in str(exc.value)

    def test_invalid_api_key_raises_exception(self, httpserver):
        bad_client = FoxESSClient(api_key='wrong-key', base_url=httpserver.url_for('').rstrip('/'))
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(
            {'errno': 40256, 'msg': 'invalid auth'}, status=401
        )
        with pytest.raises(requests.HTTPError):
            bad_client.get_device_history(sn=MOCK_SN)

    def test_missing_sn_raises_exception(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(
            {'errno': 40257, 'msg': 'missing sn'}, status=400
        )
        with pytest.raises(requests.HTTPError):
            client.get_device_history(sn='')


class TestFoxESSClientDeviceDetail:
    def test_get_device_detail_success(self, httpserver, client):
        httpserver.expect_request(DEVICE_DETAIL_PATH, method='GET').respond_with_json(
            MOCK_DEVICE_DETAIL_BODY
        )
        detail = client.get_device_detail(sn=MOCK_SN)
        assert isinstance(detail, DeviceDetail)
        assert detail.device_sn == MOCK_SN
        assert detail.module_sn == 'MOD123'
        assert detail.station_id == 'STN456'
        assert detail.station_name == 'Test Station'
        assert detail.afci_version == '1.0'
        assert detail.manager_version == '2.0'
        assert detail.master_version == '3.0'
        assert detail.slave_version == '4.0'
        assert detail.hardware_version == '5.0'
        assert detail.status == 1
        assert detail.capacity == 5.0
        assert detail.third_party_gen is False

    def test_get_device_detail_with_batteries(self, httpserver, client):
        httpserver.expect_request(DEVICE_DETAIL_PATH, method='GET').respond_with_json(
            MOCK_DEVICE_DETAIL_BODY
        )
        detail = client.get_device_detail(sn=MOCK_SN)
        assert len(detail.battery_list) == 1
        bat = detail.battery_list[0]
        assert bat.battery_sn == 'BAT001'
        assert bat.type == 'master'
        assert bat.version == '1.1'
        assert bat.model == 'LV5200'
        assert bat.capacity == 5200
        assert bat.product_date == 1700000000000

    def test_get_device_detail_with_function(self, httpserver, client):
        httpserver.expect_request(DEVICE_DETAIL_PATH, method='GET').respond_with_json(
            MOCK_DEVICE_DETAIL_BODY
        )
        detail = client.get_device_detail(sn=MOCK_SN)
        assert detail.function is not None
        assert detail.function.scheduler is True

    def test_get_device_detail_no_batteries(self, httpserver, client):
        body = {
            'errno': 0,
            'result': {
                'deviceSN': MOCK_SN,
                'moduleSN': 'MOD123',
                'stationID': 'STN456',
                'stationName': 'Test Station',
                'capacity': 3.6,
                'status': 1,
            },
        }
        httpserver.expect_request(DEVICE_DETAIL_PATH, method='GET').respond_with_json(body)
        detail = client.get_device_detail(sn=MOCK_SN)
        assert detail.battery_list == []
        assert detail.function is None

    def test_get_device_detail_api_error(self, httpserver, client):
        body = {'errno': 40001, 'msg': 'device not found'}
        httpserver.expect_request(DEVICE_DETAIL_PATH, method='GET').respond_with_json(body)
        with pytest.raises(FoxESSClientError) as exc:
            client.get_device_detail(sn='UNKNOWN')
        assert 'device not found' in str(exc.value)

    def test_get_device_detail_empty_result(self, httpserver, client):
        body = {'errno': 0, 'result': {}}
        httpserver.expect_request(DEVICE_DETAIL_PATH, method='GET').respond_with_json(body)
        with pytest.raises(FoxESSClientError) as exc:
            client.get_device_detail(sn=MOCK_SN)
        assert 'empty result' in str(exc.value)


class TestHistoryDeviceResultDataclass:
    def test_defaults(self):
        result = HistoryDeviceResult(device_sn='SN123')
        assert result.device_sn == 'SN123'
        assert result.variables == []

    def test_with_variables(self):
        var = HistoryVariable(
            variable='pvPower', unit='kW', data=[HistoryDataPoint(time=1, value=2.0)]
        )
        result = HistoryDeviceResult(device_sn='SN123', variables=[var])
        assert len(result.variables) == 1
        assert result.variables[0].data[0].value == 2.0


class TestHistoryVariableDataclass:
    def test_defaults(self):
        var = HistoryVariable(variable='pvPower', unit='kW')
        assert var.data == []
        assert var.name == ''

    def test_with_data(self):
        dp = HistoryDataPoint(time=1712534400000, value=1.5)
        var = HistoryVariable(variable='pvPower', unit='kW', name='PVPower', data=[dp])
        assert var.data[0].time == 1712534400000
        assert var.data[0].value == 1.5
        assert var.name == 'PVPower'


class TestHistoryDataPointDataclass:
    def test_time_as_int(self):
        dp = HistoryDataPoint(time=1712534400000, value=1.5)
        assert dp.time == 1712534400000

    def test_time_as_str(self):
        dp = HistoryDataPoint(time='2024-04-07T18:00:00Z', value=1.5)
        assert dp.time == '2024-04-07T18:00:00Z'


class TestDeviceDetailDataclass:
    def test_defaults(self):
        detail = DeviceDetail()
        assert detail.device_sn == ''
        assert detail.battery_list == []
        assert detail.function is None

    def test_with_all_fields(self):
        func = DeviceFunction(scheduler=True)
        bat = BatteryInfo(battery_sn='BAT001', model='LV5200')
        detail = DeviceDetail(
            device_sn='SN123',
            module_sn='MOD456',
            status=1,
            capacity=5.0,
            third_party_gen=True,
            function=func,
            battery_list=[bat],
        )
        assert detail.device_sn == 'SN123'
        assert detail.module_sn == 'MOD456'
        assert detail.status == 1
        assert detail.capacity == 5.0
        assert detail.third_party_gen is True
        assert detail.function is func
        assert detail.battery_list == [bat]


class TestBatteryInfoDataclass:
    def test_defaults(self):
        bat = BatteryInfo()
        assert bat.battery_sn == ''
        assert bat.type == ''
        assert bat.capacity == 0

    def test_with_fields(self):
        bat = BatteryInfo(battery_sn='BAT001', type='master', model='LV5200', capacity=5200)
        assert bat.battery_sn == 'BAT001'
        assert bat.type == 'master'
        assert bat.model == 'LV5200'
        assert bat.capacity == 5200


class TestDeviceFunctionDataclass:
    def test_defaults(self):
        func = DeviceFunction()
        assert func.scheduler is False

    def test_with_fields(self):
        func = DeviceFunction(scheduler=True)
        assert func.scheduler is True
