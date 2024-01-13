import json
import os
import boto3
from .custom_exceptions import BadRequestException
from .post import create_new_restaurant_dynamodb_entries, create_user, update_user
from .get import get_all_users
from .delete import delete_user


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

        if httpMethod == 'POST':
            if action == 'create_new_restaurant_dynamodb_entries':
                response = create_new_restaurant_dynamodb_entries(dynamodb_client, event_dict, __master_db_name__)
            elif action == 'create_user':
                response = create_user(dynamodb_client, event_dict, __master_db_name__)
            elif action == 'update_user':
                response = update_user(event_dict, table)
        elif httpMethod == 'GET':
            if action == 'get_all_users':
                response = get_all_users(event_dict, table)
        elif httpMethod == 'DELETE':
            if action == 'delete_user':
                response = delete_user(event_dict, table)

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
            'body': 'Error: ' + str(e)
        }

    return response
