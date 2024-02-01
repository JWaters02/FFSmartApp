import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from .custom_exceptions import BadRequestException
from .get import get_all_orders, get_order
from .post import order_check
from .delete import delete_order


def handler(event, context):

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
            if action == 'create_order':
                response = order_check(dynamodb_client, event_dict, table, __master_db_name__)
        elif httpMethod == 'GET':
            if action == 'get_all_orders':
                response = get_all_orders(event_dict, table)
            elif action == 'get_order':
                response = get_order(event_dict, table)
        elif httpMethod == 'DELETE':
            if action == 'delete_order':
                response = delete_order(event_dict, table)

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