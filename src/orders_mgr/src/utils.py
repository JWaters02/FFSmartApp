import secrets
import time


def generate_order_id(table, restaurant_id):
    dynamo_response = table.get_item(
        Key={
            'pk': restaurant_id,
            'type': 'orders'
        }
    )
    item = dynamo_response.get('Item', None)

    if item is None:
        raise NotFoundException('Restaurant does not exist.')

    response = None
    count = 3
    while count > 0:
        order_id = str(secrets.randbits(64))
        if is_order_id_valid(order_id, item):
            response = order_id
            break
        count -= 1
            
    return response
        
        
def is_order_id_valid(order_id, item):
    for index, order in enumerate(item['orders']):
        if order_id == order['id']:
            return False

    return True


def get_item_quantity(order_items, item_name):
    for item in order_items:
        if item['item_name'] == item_name:
            return item['quantity']
    return 0


def get_total_item_quantity(fridge_item, orders):
    # Count from fridge entry
    item_quantity = 0
    for entry in fridge_item['item_list']:
        if entry['expiry_date'] > int(time.time()):
            item_quantity += entry['current_quantity']
    # Count from orders
    for order in orders:
        item_quantity += get_item_quantity(order['items'], fridge_item['item_name'])

    return item_quantity
