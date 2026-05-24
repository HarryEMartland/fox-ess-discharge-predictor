import json
from datetime import datetime, timezone
from unittest.mock import patch

from index import handler


def test_handler_returns_200():
    event = {}
    context = {'function_name': 'fox-ess-discharge-predictor'}

    result = handler(event, context)

    assert result['statusCode'] == 200


def test_handler_returns_valid_json_body():
    event = {}
    context = {'function_name': 'fox-ess-discharge-predictor'}

    result = handler(event, context)
    body = json.loads(result['body'])

    assert isinstance(body, dict)


def test_handler_body_contains_expected_keys():
    event = {}
    context = {'function_name': 'fox-ess-discharge-predictor'}

    result = handler(event, context)
    body = json.loads(result['body'])

    assert 'timestamp' in body
    assert 'function_name' in body
    assert 'execution_time' in body
    assert 'status' in body
    assert 'prediction' in body


def test_handler_prediction_contains_expected_keys():
    event = {}
    context = {'function_name': 'fox-ess-discharge-predictor'}

    result = handler(event, context)
    prediction = json.loads(result['body'])['prediction']

    assert 'discharge_probability' in prediction
    assert 'recommended_depth' in prediction
    assert 'optimal_window_start' in prediction
    assert 'optimal_window_end' in prediction


def test_handler_prediction_values():
    event = {}
    context = {'function_name': 'fox-ess-discharge-predictor'}

    result = handler(event, context)
    prediction = json.loads(result['body'])['prediction']

    assert prediction['discharge_probability'] == 0.65
    assert prediction['recommended_depth'] == 80
    assert prediction['optimal_window_start'] == '16:00'
    assert prediction['optimal_window_end'] == '20:00'


def test_handler_status_is_completed():
    event = {}
    context = {'function_name': 'fox-ess-discharge-predictor'}

    result = handler(event, context)
    body = json.loads(result['body'])

    assert body['status'] == 'completed'


def test_handler_uses_context_function_name():
    event = {}
    context = {'function_name': 'custom-function-name'}

    result = handler(event, context)
    body = json.loads(result['body'])

    assert body['function_name'] == 'custom-function-name'


def test_handler_uses_default_function_name_when_missing():
    event = {}
    context = {}

    result = handler(event, context)
    body = json.loads(result['body'])

    assert body['function_name'] == 'fox-ess-discharge-predictor'


def test_handler_timestamp_is_iso_format():
    event = {}
    context = {'function_name': 'fox-ess-discharge-predictor'}

    result = handler(event, context)
    body = json.loads(result['body'])
    timestamp = body['timestamp']

    datetime.fromisoformat(timestamp)


@patch('index.datetime')
def test_handler_timestamp_is_current_time(mock_datetime):
    fixed_time = datetime(2025, 6, 15, 14, 30, 0, tzinfo=timezone.utc)  # noqa: UP017
    mock_datetime.now.return_value = fixed_time
    mock_datetime.timezone = timezone

    event = {}
    context = {'function_name': 'fox-ess-discharge-predictor'}

    result = handler(event, context)
    body = json.loads(result['body'])

    assert body['timestamp'] == fixed_time.isoformat()
    assert body['execution_time'] == '2025-06-15 14:30:00 UTC'
