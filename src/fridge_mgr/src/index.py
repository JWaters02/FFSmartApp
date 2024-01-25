import os
import boto3
import json
import logging
from .inventory_utils import (view_inventory, delete_item, add_new_item,
                              add_delivery_item, update_item_quantity, modify_door_state,
                              get_low_stock, update_desired_quantity, generate_response)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Processes incoming Lambda events and routes them to appropriate functions.
    :param event: Event data from AWS Lambda.
    :param context: Lambda execution context.
    :return: Response based on processed action.
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
        elif action == "add_new_item":
            return add_new_item(table, pk, body)
        elif action == "add_delivery_item":
            return add_delivery_item(table, pk, body)
        elif action == "update_item_quantity":
            return update_item_quantity(table, pk, body)
        elif action == "delete_item":
            return delete_item(table, pk, body)
        elif action in ["open_back_door", "close_back_door", "open_front_door", "close_front_door"]:
            return modify_door_state(table, pk, body, action)
        elif action == "get_low_stock":
            return get_low_stock(table, pk)
        elif action == "update_desired_quantity":
            return update_desired_quantity(table, pk, body)
        else:
            raise ValueError(f"Invalid action specified: {action}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return generate_response(500, f"An error occurred: {str(e)}")
