import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_current_time_gmt():
    """
    Gets current GMT time.
    :return: Current GMT timestamp.
    """
    utc_time = datetime.utcnow()
    gmt_time = utc_time + timedelta(hours=0)
    return int(gmt_time.timestamp())


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


def add_new_item(table, pk, body):
    """
    Adds a new item to the inventory if it doesn't exist.
    :param table: DynamoDB table.
    :param pk: Primary key.
    :param body: Request data.
    :return: API response with operation result.
    """
    item_name = body.get('item_name').lower()
    desired_quantity = body.get('desired_quantity', 0)
    expiry_date = body.get('expiry_date')
    quantity = body.get('quantity', 0)  # delivery of new item edge case
    current_time = get_current_time_gmt()

    table_response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
    item = table_response.get('Item', {'items': []})

    for stored_item in item['items']:
        if stored_item['item_name'].lower() == item_name:
            return generate_response(409, f'Item {item_name} already exists')

    item['items'].append({
        'item_name': item_name,
        'desired_quantity': desired_quantity,
        'item_list': [{
            'current_quantity': quantity,
            'expiry_date': expiry_date,
            'date_added': current_time,
            'date_removed': 0
        }]
    })

    table.put_item(Item=item)
    return generate_response(200, f'New item {item_name} added successfully')


def add_delivery_item(table, pk, body):
    """
    Adds delivered items to existing inventory.
    :param table: DynamoDB table.
    :param pk: Primary key.
    :param body: Delivery details.
    :return: API response with operation result.
    """
    item_name = body.get('item_name').lower()
    quantity = body.get('quantity', 0)
    expiry_date = body.get('expiry_date')
    current_time = get_current_time_gmt()

    table_response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
    item = table_response.get('Item')

    if not item:
        return generate_response(404, 'Inventory item not found')

    for stored_item in item['items']:
        if stored_item['item_name'].lower() == item_name:
            stored_item['item_list'].append({
                'current_quantity': quantity,
                'expiry_date': expiry_date,
                'date_added': current_time,
                'date_removed': 0
            })

            table.put_item(Item=item)
            return generate_response(200, f'Delivery item {item_name} added successfully')

    # add the item as a new item
    body['desired_quantity'] = quantity
    return add_new_item(table, pk, body)


def update_item_quantity(table, pk, body):
    """
    Updates the quantity of an existing inventory item.
    :param table: DynamoDB table.
    :param pk: Primary key.
    :param body: Update details.
    :return: API response with operation result.
    """
    item_name = body.get('item_name').lower()
    quantity_change = body.get('quantity_change', 0)
    expiry_date = body.get('expiry_date')

    table_response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
    item = table_response.get('Item')

    if not item:
        return generate_response(404, 'Inventory item not found')

    for stored_item in item['items']:
        if stored_item['item_name'].lower() == item_name:
            for item_detail in stored_item['item_list']:
                if item_detail['expiry_date'] == expiry_date:
                    item_detail['current_quantity'] += quantity_change
                    if item_detail['current_quantity'] < 0: 
                        return generate_response(400, f'Quantity cannot be negative for {item_name}')

                    table.put_item(Item=item)

                    # if current_quantity is 0, delete the item
                    if item_detail['current_quantity'] == 0:
                        return delete_item(table, pk, body)
                    else:
                        return generate_response(200, f'Quantity updated for {item_name}')
    return generate_response(404, f'Item {item_name} not found in inventory')


def delete_item(table, pk, body):
    """
    Deletes an item entirely from the inventory.
    :param table: DynamoDB table.
    :param pk: Primary key.
    :param body: Deletion details.
    :return: API response with operation result.
    """
    item_name = body.get('item_name')
    current_quantity = body.get('current_quantity', 0)
    expiry_date = body.get('expiry_date')

    table_response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
    item = table_response.get('Item')

    if not item:
        return generate_response(404, 'Inventory item not found')

    for stored_item in item['items']:
        if stored_item['item_name'] == item_name:
            for detail in stored_item['item_list']:
                if detail['current_quantity'] == 0:
                    detail['date_removed'] = get_current_time_gmt()
            if current_quantity == 0:
                stored_item['item_list'] = [detail for detail in stored_item['item_list']
                                            if not detail['current_quantity'] == current_quantity]
            else:
                stored_item['item_list'] = [detail for detail in stored_item['item_list']
                                            if not (detail['expiry_date'] == expiry_date and
                                                    detail['current_quantity'] == current_quantity)]
                if not stored_item['item_list']:
                    item['items'] = [i for i in item['items'] if i['item_name'] != item_name]
            table.put_item(Item=item, overwrite=True)
            return generate_response(200, f'Item {item_name} updated successfully')

    return generate_response(404, f'Item {item_name} not found in inventory')


def modify_door_state(table, pk, body, action):
    """
    Modifies the state of the door (open/close) in inventory.
    :param table: DynamoDB table.
    :param pk: Primary key.
    :param body: State details.
    :param action: Specific door action.
    :return: API response with operation result.
    """
    table_response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
    item = table_response.get('Item')

    if not item:
        return generate_response(404, 'Inventory item not found')

    # Handle each action separately
    if action == "open_back_door":
        item['is_back_door_open'] = True
    elif action == "close_back_door":
        item['is_back_door_open'] = False
    elif action == "open_front_door":
        item['is_front_door_open'] = True
    elif action == "close_front_door":
        item['is_front_door_open'] = False

    table.put_item(Item=item)
    return generate_response(200, 'Door state updated successfully',
                             {'is_front_door_open': item.get('is_front_door_open', False),
                              'is_back_door_open': item.get('is_back_door_open', False)})


def get_low_stock(table, pk):
    """
    Retrieves items that are low in stock.
    :param table: DynamoDB table.
    :param pk: Primary key.
    :return: API response with low stock items.
    """
    try:
        dynamo_response = table.get_item(
            Key={
                'pk': pk,
                'type': 'fridge'
            }
        )
        item = dynamo_response.get('Item', {'items': []})

        low_stock = []

        for food_item in item['items']:
            name = food_item['item_name']
            desired_quantity = food_item['desired_quantity']

            current_quantity = 0
            for entry in food_item['item_list']:
                current_quantity += entry['current_quantity']

            if current_quantity < desired_quantity:
                low_stock.append({
                    'item_name': name,
                    'desired_quantity': desired_quantity,
                    'current_quantity': current_quantity
                })

        return generate_response(200, 'Low stock items retrieved successfully', {'low_stock': low_stock})
    except ClientError as e:
        return generate_response(500, 'Error accessing DynamoDB: ' + str(e))
    except Exception as e:
        return generate_response(500, 'Internal Server Error: ' + str(e))


def update_desired_quantity(table, pk, body):
    """
    Updates desired quantity of an inventory item.
    :param table: DynamoDB table.
    :param pk: Primary key.
    :param body: Update details.
    :return: API response with operation result.
    """
    item_name = body.get('item_name')
    desired_quantity = body.get('desired_quantity')

    table_response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
    item = table_response.get('Item')

    if not item:
        return generate_response(404, 'Inventory item not found')

    for stored_item in item['items']:
        if stored_item['item_name'] == item_name:
            stored_item['desired_quantity'] = desired_quantity
            table.put_item(Item=item)
            return generate_response(200, f'Desired quantity updated for {item_name}')

    return generate_response(404, f'Item {item_name} not found in inventory')


def view_inventory(table, pk):
    """
    Retrieves the current state of inventory.
    :param table: DynamoDB table.
    :param pk: Primary key.
    :return: API response with inventory details.
    """
    try:
        table_response = table.get_item(Key={'pk': pk, 'type': 'fridge'})
        item = table_response.get('Item', {})

        delete_removed_items(item)

        return generate_response(200, 'Inventory retrieved successfully', item)
    except Exception as e:
        return generate_response(500, 'Error retrieving inventory: ' + str(e))


def delete_zero_quantity_items(item):
    """
    Removes items with zero quantity from inventory.
    :param item: Inventory data.
    :return: None.
    """
    if 'items' in item:
        for stored_item in item['items']:
            stored_item['item_list'] = [detail for detail in stored_item['item_list'] if detail['current_quantity'] > 0]
        item['items'] = [stored_item for stored_item in item['items'] if stored_item['item_list']]


def delete_removed_items(item):
    """
    Removes items with a populated date removed field from inventory.
    :param item: Inventory data.
    :return: None.
    """
    if 'items' in item:
        for stored_item in item['items']:
            stored_item['item_list'] = [detail for detail in stored_item['item_list'] if detail['date_removed'] == 0]
        item['items'] = [stored_item for stored_item in item['items'] if stored_item['item_list']]