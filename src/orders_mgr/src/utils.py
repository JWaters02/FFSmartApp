import secrets
import time
from src.custom_exceptions import NotFoundException

from src.custom_exceptions import NotFoundException


def generate_order_id(table, restaurant_id):
    """
    Creates a new order id for a given restaurant id.

    :param table: DynamoDB table resource for specified table_name.
    :param restaurant_id: Name of restaurant.
    :raises NotFoundException: Thrown if restaurant does not exist.
    :return: order id
    """
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
    """
    Validates generated order id by checking it doesn't match existing order ids.

    :param order_id: Generated order id.
    :param item: Restaurant containing orders.
    :raises NotFoundException: Thrown if restaurant does not exist.
    :return: True if order id valid, False if invalid.
    """
    for index, order in enumerate(item['orders']):
        if order_id == order['id']:
            return False

    return True


def get_expired_item_quantity_fridge(fridge_item, expiry_time):
    """
    Gets quantity of expired fridge item.

    :param fridge_item: Item to be checked for expired entries.
    :param expiry_time: The unix time when the food will be considered to have expired.
    :return: Quantity of expired fridge item.
    """
    quantity = 0
    for entry in fridge_item['item_list']:
        print(entry['expiry_date'], end=' ')
        print('<=', end=' ')
        print(expiry_time, end=' ')
        print(entry['expiry_date'] <= expiry_time)
        if entry['expiry_date'] <= expiry_time:
            quantity += entry['current_quantity']
    return quantity


def get_item_quantity_fridge(fridge_item):
    """
    Gets quantity of unexpired fridge item.

    :param fridge_item: Item to be checked for unexpired entries.
    :return: Quantity of unexpired fridge item.
    """
    quantity = 0
    for entry in fridge_item['item_list']:
        if entry['expiry_date'] > int(time.time()):
            quantity += entry['current_quantity']
    return quantity


def get_item_quantity_orders(order_items, item_name):
    """
    Gets quantity of item from order.

    :param order_items: Items in order.
    :param item_name: Name of item being added to order.
    :return: Quantity of item in order.
    """
    for item in order_items:
        if item['item_name'] == item_name:
            return item['quantity']
    return 0


def get_total_item_quantity(fridge_item, orders):
    """
    Gets total quantity of item from fridge and order.

    :param fridge_item: Item in fridge.
    :param orders: All orders for restaurant.
    :return: Combined quantity of item in orders and fridge.
    """
    # Count from fridge entry
    item_quantity = get_item_quantity_fridge(fridge_item)
    # Count from orders
    for order in orders:
        item_quantity += get_item_quantity_orders(order['items'], fridge_item['item_name'])

    return item_quantity
