import os
import boto3
import json
from .custom_exceptions import BadRequestException
from .patch import set_token
from .post import validate_token
from .delete import delete_token


def handler(event, context):
    response = None

    # ensures that requests are dicts
    if isinstance(event, str):
        event_dict = json.loads(event)
    else:
        event_dict = event

    try:
        __master_db_name__ = os.environ.get('MASTER_DB')
        dynamodb_resource = boto3.resource('dynamodb')
        dynamodb_client = boto3.client('dynamodb')
        table = dynamodb_resource.Table(__master_db_name__)

        if 'httpMethod' not in event_dict:
            raise BadRequestException('Bad request httpMethod does not exist.')

        if 'action' not in event_dict:
            raise BadRequestException('Bad request action does not exist.')

        httpMethod = event_dict['httpMethod']
        action = event_dict['action']

        if httpMethod == 'PATCH':
            if action == 'set_token':
                response = set_token(event, table)
        if httpMethod == 'POST':
            if action == 'validate_token':
                response = validate_token(event, table)
        elif httpMethod == 'DELETE':
            if action == 'delete_token':
                response = delete_token(event, table)
            elif action == 'clean_up_old_tokens':
                pass

        if response is None:
            response = {
                'statusCode': 400,
                'body': 'Bad request.'
            }

    except BadRequestException as e:
        response = {
            'statusCode': 400,
            'body': str(e)
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': {
                'details': str(e)
            }
        }

    return response
