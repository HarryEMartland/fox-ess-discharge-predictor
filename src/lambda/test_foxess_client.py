import hashlib

import pytest
import requests
from foxess_client import (
    FoxESSClient,
    FoxESSClientError,
    HistoryDataPoint,
    HistoryResult,
    HistoryVariable,
)

MOCK_API_KEY = 'test-api-key-12345'
MOCK_SN = 'ABC123DEF'

HISTORY_PATH = '/op/v0/device/history/query'

MOCK_SUCCESS_BODY = {
    'errno': 0,
    'result': {
        'sn': MOCK_SN,
        'data': [
            {
                'variable': 'pvPower',
                'unit': 'kW',
                'data': [
                    {'time': 1712534400000, 'value': 1.5},
                    {'time': 1712534700000, 'value': 1.8},
                ],
            },
            {
                'variable': 'feedinPower',
                'unit': 'kW',
                'data': [
                    {'time': 1712534400000, 'value': 0.3},
                    {'time': 1712534700000, 'value': 0.5},
                ],
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
        raw = f'{HISTORY_PATH}\r\nmy-key\r\n{headers["timestamp"]}'
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
    def test_get_device_history_returns_result(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        result = client.get_device_history(sn=MOCK_SN)
        assert isinstance(result, HistoryResult)
        assert result.sn == MOCK_SN

    def test_get_device_history_returns_expected_variables(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        result = client.get_device_history(sn=MOCK_SN, variables=['pvPower', 'feedinPower'])
        assert len(result.variables) == 2
        assert result.variables[0].variable == 'pvPower'
        assert result.variables[1].variable == 'feedinPower'

    def test_get_device_history_returns_datapoints(self, httpserver, client):
        body = {
            'errno': 0,
            'result': {
                'sn': MOCK_SN,
                'data': [
                    {
                        'variable': 'pvPower',
                        'unit': 'kW',
                        'data': [
                            {'time': 1712534400000, 'value': 1.5},
                            {'time': 1712534700000, 'value': 1.8},
                        ],
                    },
                ],
            },
        }
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(body)
        result = client.get_device_history(sn=MOCK_SN, variables=['pvPower'])
        assert len(result.variables) == 1
        var = result.variables[0]
        assert len(var.data) == 2
        assert var.data[0].time == 1712534400000
        assert var.data[0].value == 1.5
        assert var.data[1].time == 1712534700000
        assert var.data[1].value == 1.8

    def test_get_device_history_no_variables_returns_all(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        result = client.get_device_history(sn=MOCK_SN)
        assert len(result.variables) > 0

    def test_get_device_history_with_time_range(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        begin = 1712534400000
        end = 1712620800000
        result = client.get_device_history(sn=MOCK_SN, variables=['pvPower'], begin=begin, end=end)
        assert result.variables[0].variable == 'pvPower'

    def test_get_device_history_unit_is_returned(self, httpserver, client):
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(MOCK_SUCCESS_BODY)
        result = client.get_device_history(sn=MOCK_SN, variables=['pvPower'])
        assert result.variables[0].unit == 'kW'

    def test_get_device_history_empty_variable_returns_empty_data(self, httpserver, client):
        body = {
            'errno': 0,
            'result': {
                'sn': MOCK_SN,
                'data': [
                    {'variable': 'unknownVar', 'unit': '', 'data': []},
                ],
            },
        }
        httpserver.expect_request(HISTORY_PATH, method='POST').respond_with_json(body)
        result = client.get_device_history(sn=MOCK_SN, variables=['unknownVar'])
        assert len(result.variables) == 1
        assert result.variables[0].variable == 'unknownVar'
        assert result.variables[0].data == []


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


class TestHistoryResultDataclass:
    def test_history_result_defaults(self):
        result = HistoryResult(sn='SN123')
        assert result.sn == 'SN123'
        assert result.variables == []

    def test_history_result_with_variables(self):
        var = HistoryVariable(
            variable='pvPower', unit='kW', data=[HistoryDataPoint(time=1, value=2.0)]
        )
        result = HistoryResult(sn='SN123', variables=[var])
        assert len(result.variables) == 1
        assert result.variables[0].data[0].value == 2.0


class TestHistoryVariableDataclass:
    def test_history_variable_defaults(self):
        var = HistoryVariable(variable='pvPower', unit='kW')
        assert var.data == []

    def test_history_variable_with_data(self):
        dp = HistoryDataPoint(time=1712534400000, value=1.5)
        var = HistoryVariable(variable='pvPower', unit='kW', data=[dp])
        assert var.data[0].time == 1712534400000
        assert var.data[0].value == 1.5
