import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_low_stock(table, pk):
    """

    :param table:
    :param pk:
    :return:
    """
    try:
        response = generate_response(500, 'Internal Server Error')

        dynamo_response = table.get_item(
            Key={
                'pk': pk,
                'type': 'fridge'
            }
        )
        item = dynamo_response.get('Item', {'items': []})

        low_stock = []

        for food_item in item['items']:
            print(food_item)
            name = food_item['item_name']
            desired_quantity = food_item['desired_quantity']

            current_quantity = 0

            for entry in food_item['item_list']:
                current_quantity += entry['current_quantity']

            if current_quantity < 2 and desired_quantity > 2:
                low_stock.append({
                    'item_name': name,
                    'desired_quantity': desired_quantity,
                    'current_quantity': current_quantity
                })

        response = {
            'statusCode': 200,
            'body': {
                'low_stock': low_stock
            }
        }

    except ClientError as ignore:
        response = generate_response(500, 'Internal Server Error1' + str(ignore))

    except Exception as ignore:
        response = generate_response(500, 'Internal Server Error2' + str(ignore))

    return response


def view_inventory(table, pk):
    """
    Retrieves inventory for a restaurant.
    :param table: DynamoDB table object.
    :param pk: Primary key for inventory.
    :return: 200 - Successful.
        500 - Internal Server Error.
    """
    try:
        response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
        item = response.get('Item', {})

        delete_zero_quantity_items(item)

        return generate_response(200, 'Inventory retrieved successfully', item)
    except Exception as e:
        logger.error(f"An error occurred during inventory retrieval: {str(e)}")
        return generate_response(500, f"An error occurred during inventory retrieval: {str(e)}")


def delete_entire_item(item, body):
    """
    Deletes an item from inventory.
    :param item: Inventory item.
    :param body: Request body details.
    """
    logger.info("Entering delete_entire_item function")

    item_name = body.get('item_name')
    quantity_change = body.get('quantity_change', 0)
    expiry_date = body.get('expiry_date')

    logger.info(f"Deleting item: {item_name}, Quantity: {quantity_change}, Expiry Date: {expiry_date}")

    item_found = False
    for stored_item in item['items']:
        if stored_item['item_name'] == item_name:
            item_found = True
            logger.info(f"Found item: {item_name}")
            before_delete_count = len(stored_item['item_list'])
            stored_item['item_list'] = [detail for detail in stored_item['item_list']
                                        if not (detail['expiry_date'] == expiry_date and
                                                detail['current_quantity'] == quantity_change)]

            after_delete_count = len(stored_item['item_list'])
            logger.info(f"Item list size before: {before_delete_count}, after: {after_delete_count}")

            if not stored_item['item_list']:
                item['items'] = [i for i in item['items'] if i['item_name'] != item_name]
                logger.info(f"Removed {item_name} entirely as no more details left")
            break

    if not item_found:
        logger.warning(f"Item {item_name} not found in inventory")

    logger.info("Exiting delete_entire_item function")


def delete_zero_quantity_items(item):
    """
    Removes zero quantity items from inventory.
    :param item: Inventory item.
    """
    if 'items' in item:
        for stored_item in item['items']:
            stored_item['item_list'] = [detail for detail in stored_item['item_list'] if detail['current_quantity'] > 0]
        item['items'] = [stored_item for stored_item in item['items'] if stored_item['item_list']]

def modify_items(item, body, action, current_time):
    """
    Adds or updates items in the inventory.
    :param item: Inventory item.
    :param body: Request body details.
    :param action: Action to perform.
    :param current_time: Current time stamp.
    :return: status code and response object.
    """
    item_name = body.get('item_name').lower()
    quantity_change = body.get('quantity_change', 0)
    expiry_date = body.get('expiry_date')
    desired_quantity = body.get('desired_quantity', None)
    
    if desired_quantity is not None and desired_quantity <= 0:
        return False, generate_response(400, 'Quantity and desired quantity must be greater than 0')

    item_found = False
    duplicate_found = False
    if 'items' in item:
        for stored_item in item['items']:
            if stored_item['item_name'].lower() == item_name:
                if action == 'add_item':
                    logger.info(f'Found existing item: {item_name} with action {action}')
                    duplicate_found = True
                    break
                elif action == 'update_item':
                    for item_detail in stored_item['item_list']:
                        if item_detail['expiry_date'] == expiry_date:
                            logger.info(f'Found existing item: {item_name} with expiry: {expiry_date} for update')
                            item_detail['current_quantity'] += quantity_change
                            item_found = True
                            break
                    if item_found:
                        break

    if duplicate_found:
        return False, generate_response(409, 'Item with the same name already exists')

    if not item_found and action == 'add_item':
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
        return True, generate_response(200, 'Item added successfully')

    if not item_found and action == 'update_item':
        return False, generate_response(404, 'Item not found for update')

    return True, generate_response(200, 'Item updated successfully')

def update_desired_quantity(table, pk, body):
    """
    Updates the desired quantity of an item in the inventory, ensuring it's greater than 0.
    :param table: DynamoDB table object.
    :param pk: Primary key for inventory record.
    :param body: Request body details.
    :return: Response object.
    """
    try:
        desired_quantity = body.get('desired_quantity')
        if desired_quantity is None or desired_quantity <= 0:
            return generate_response(400, 'Desired quantity must be greater than 0')

        table_response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
        item = table_response.get('Item')

        if not item:
            return generate_response(404, 'Inventory item not found')

        item_name = body.get('item_name')
        item_updated = False

        for stored_item in item.get('items', []):
            if stored_item['item_name'] == item_name:
                stored_item['desired_quantity'] = desired_quantity
                item_updated = True
                break

        if item_updated:
            table.put_item(Item=item)
            return generate_response(200, 'Desired quantity updated successfully', item)
        else:
            return generate_response(404, 'Item not found in inventory')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return generate_response(500, f"An error occurred: {str(e)}")

def modify_door_state(item, body, action):
    """
    Changes door state in inventory for front and back door.
    :param item: Inventory item.
    :param body: Request body details.
    :param action: Door action.
    """
    if action == "open_door":
        if 'is_front_door_open' in body:
            item['is_front_door_open'] = body['is_front_door_open']
        if 'is_back_door_open' in body:
            item['is_back_door_open'] = body['is_back_door_open']
    elif action == "close_door":
        if 'is_front_door_open' in body:
            item['is_front_door_open'] = body['is_front_door_open']
        if 'is_back_door_open' in body:
            item['is_back_door_open'] = body['is_back_door_open']


def generate_response(status_code, message, additional_details=None):
    """
    Generates a standard API response for lambda.
    :param status_code: HTTP status code.
    :param message: Response message.
    :param additional_details: Additional response details.
    :return: Formatted response.
    """
    body = {'details': message}
    if additional_details:
        body['additional_details'] = additional_details
    return {
        'statusCode': status_code,
        'body': body
    }


def get_current_time_gmt():
    """
    Gets current GMT time.
    :return: Current GMT timestamp.
    """
    utc_time = datetime.utcnow()
    gmt_time = utc_time + timedelta(hours=0)
    return int(gmt_time.timestamp())
