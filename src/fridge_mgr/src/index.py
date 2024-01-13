import os
import boto3
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
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
        else:
            raise ValueError(f"Invalid action specified: {action}")

        return response
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return generate_response(500, f"An error occurred: {str(e)}")

def view_inventory(table, pk):
    try:
        response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
        item = response.get('Item', {})
        return generate_response(200, 'Inventory retrieved successfully', item)
    except Exception as e:
        logger.error(f"An error occurred during inventory retrieval: {str(e)}")
        return generate_response(500, f"An error occurred during inventory retrieval: {str(e)}")

def manage_inventory(table, pk, body, action):
    try:
        current_time = get_current_time_gmt()
        response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
        item = response.get('Item')

        if not item:
            item = {'pk': pk, 'type': 'fridge', 'items': [], 'is_front_door_open': False, 'is_back_door_open': False}

        if action in ["add_item", "update_item", "delete_item"]:
            modify_items(item, body, action, current_time)
        elif action in ["open_door", "close_door"]:
            modify_door_state(item, body, action)

        table.put_item(Item=item)
        return generate_response(200, f'Inventory {action} successful', item)
    except Exception as e:
        logger.error(f"An error occurred during DynamoDB update: {str(e)}")
        return generate_response(500, f"An error occurred during DynamoDB update: {str(e)}")

def modify_items(item, body, action, current_time):
    item_name = body.get('item_name')
    quantity_change = body.get('quantity_change', 0)
    expiry_date = body.get('expiry_date')
    desired_quantity = body.get('desired_quantity', None)

    item_found = False
    if 'items' in item:
        for stored_item in item['items']:
            if stored_item['item_name'] == item_name:
                if action == "delete_item":
                    for item_detail in stored_item['item_list']:
                        if item_detail['expiry_date'] == expiry_date:
                            item_detail['current_quantity'] = max(item_detail['current_quantity'] - quantity_change, 0)
                            item_found = True
                            break
                else:  # Handle add/update item
                    for item_detail in stored_item['item_list']:
                        if item_detail['expiry_date'] == expiry_date:
                            item_detail['current_quantity'] += quantity_change
                            item_found = True
                            break
                    if not item_found:
                        stored_item['item_list'].append({
                            'current_quantity': quantity_change,
                            'expiry_date': expiry_date,
                            'date_added': current_time,
                            'date_removed': 0
                        })
                        item_found = True
                if item_found:
                    break

    if not item_found:
        item['items'].append({
            'item_name': item_name,
            'desired_quantity': desired_quantity if desired_quantity is not None else quantity_change,
            'item_list': [{
                'current_quantity': quantity_change,
                'expiry_date': expiry_date,
                'date_added': current_time,
                'date_removed': 0
            }]
        })

def modify_door_state(item, body, action):
    if action == "open_door":
        item['is_front_door_open'] = body.get('is_front_door_open', False)
        item['is_back_door_open'] = body.get('is_back_door_open', False)
    elif action == "close_door":
        item['is_front_door_open'] = False
        item['is_back_door_open'] = False

def generate_response(status_code, message, additional_details=None):
    body = {'details': message}
    if additional_details:
        body['additional_details'] = additional_details
    return {
        'statusCode': status_code,
        'body': body
    }

def get_current_time_gmt():
    utc_time = datetime.utcnow()
    gmt_time = utc_time + timedelta(hours=0)
    return int(gmt_time.timestamp())