import json
import logging
import os
from datetime import UTC, datetime

from foxess_client import FoxESSClient
from octopus_energy import OctopusEnergyConsumerClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(event: dict, context: dict) -> dict:
    logger.info('Fox ESS Discharge Predictor started')
    logger.info(f'Event: {json.dumps(event)}')
    logger.info(f'Context: {json.dumps(context)}')

    foxess_api_key = os.environ.get('FOXESS_API_KEY')
    foxess_device_sn = os.environ.get('FOXESS_DEVICE_SN')
    if foxess_api_key and foxess_device_sn:
        try:
            client = FoxESSClient(api_key=foxess_api_key)
            detail = client.get_device_detail(sn=foxess_device_sn)
            for battery in detail.battery_list:
                logger.info(
                    'Battery capacity: sn=%s, model=%s, capacity=%d',
                    battery.battery_sn,
                    battery.model,
                    battery.capacity,
                )
        except Exception:
            logger.warning('Failed to fetch FoxESS device details', exc_info=True)
    else:
        logger.warning('FOXESS_API_KEY or FOXESS_DEVICE_SN not set, skipping FoxESS data')

    octopus_api_key = os.environ.get('OCTOPUS_API_KEY')
    octopus_account_number = os.environ.get('OCTOPUS_ACCOUNT_NUMBER')
    if octopus_api_key and octopus_account_number:
        try:
            octopus_client = OctopusEnergyConsumerClient(api_token=octopus_api_key)
            meters = octopus_client.get_meters(account_number=octopus_account_number)
            for meter in meters:
                logger.info(
                    'Octopus product: serial=%s, type=%s, generation=%s',
                    meter.serial_number,
                    meter.energy_type,
                    meter.generation,
                )
        except Exception:
            logger.warning('Failed to fetch Octopus account products', exc_info=True)
    else:
        logger.warning('OCTOPUS_API_KEY or OCTOPUS_ACCOUNT_NUMBER not set, skipping Octopus data')

    current_time = datetime.now(UTC)

    prediction_data = {
        'timestamp': current_time.isoformat(),
        'function_name': context.get('function_name', 'fox-ess-discharge-predictor'),
        'execution_time': current_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'status': 'completed',
        'prediction': {
            'discharge_probability': 0.65,
            'recommended_depth': 80,
            'optimal_window_start': '16:00',
            'optimal_window_end': '20:00',
        },
    }

    logger.info(f'Prediction result: {json.dumps(prediction_data)}')
    logger.info('Fox ESS Discharge Predictor completed successfully')

    return {
        'statusCode': 200,
        'body': json.dumps(prediction_data),
    }


if __name__ == '__main__':
    test_event = {}
    test_context = {
        'function_name': 'fox-ess-discharge-predictor',
        'aws_request_id': 'test-123',
    }
    result = handler(test_event, test_context)
    print(json.dumps(result, indent=2))
