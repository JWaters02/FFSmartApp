import os
import boto3
import logging
import json
from .inventory_utils import view_inventory, delete_entire_item, modify_items, modify_door_state,\
    generate_response, get_current_time_gmt, get_low_stock

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Handles AWS Lambda events.
    :param event: Event data from AWS Lambda.
    :param context: Lambda execution context.
    :return: Response based on action.
    """
    try:
        if isinstance(event.get('body'), dict):
            body = event.get('body')
        else:
            body = json.loads(event.get('body', '{}'))

        master_db_name = os.environ.get('MASTER_DB')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(master_db_name)

        pk = body.get('restaurant_name')
        action = event.get('action')

        if action == "view_inventory":
            return view_inventory(table, pk)
        elif action in ["add_item", "update_item", "delete_item", "open_door", "close_door"]:
            response = manage_inventory(table, pk, body, action)
        elif action == "get_low_stock":
            response = get_low_stock(table, pk)
        else:
            raise ValueError(f"Invalid action specified: {action}")

        return response
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return generate_response(500, f"An error occurred: {str(e)}")


def manage_inventory(table, pk, body, action):
    """
    Manages inventory based on action.
    :param table: DynamoDB table name.
    :param pk: Primary key for inventory record.
    :param body: Request body details.
    :param action: Action to perform.
    :return: 200 - Successful.
        500 - Internal Server Error.
    """
    try:
        current_time = get_current_time_gmt()
        table_response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
        item = table_response.get('Item')

        if not item:
            item = {'pk': pk, 'type': 'fridge', 'items': [], 'is_front_door_open': False, 'is_back_door_open': False}

        if action in ["add_item", "update_item"]:
            modify_items(item, body, action, current_time)
        elif action == "delete_item":
            delete_entire_item(item, body)
        elif action in ["open_door", "close_door"]:
            modify_door_state(item, body, action)

        table.put_item(Item=item)
        return generate_response(200, f'Inventory {action} successful', item)
    except Exception as e:
        logger.error(f"An error occurred during DynamoDB update: {str(e)}")
        return generate_response(500, f"An error occurred during DynamoDB update: {str(e)}")
        