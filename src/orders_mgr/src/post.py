from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from .custom_exceptions import NotFoundException, BadRequestException
from .utils import generate_order_id, get_total_item_quantity, get_expired_item_quantity_fridge
import time
import json


def order_check(dynamodb_client, event, table, table_name):
    """
    Check fridge for a given restaurant_id, create order if necessary.

    :param dynamodb_client: The MasterDB client.
    :param event: Event passed to lambda.
    :param table: DynamoDB table resource for specified table_name.
    :param table_name: Name of MasterDB.
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 201 - Success: Order was created
        204 - Success: No order necessary.
        404 - Fridge not found.
        500 - Internal error resulting in entry not being added.
    """

    response = None

    if 'body' not in event:
        raise BadRequestException('No request body exists.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    restaurant_name = event['body']['restaurant_id']

    try:
        fridge_response = table.query(
            KeyConditionExpression=Key('pk').eq(restaurant_name) & Key('type').eq('fridge')
        )

        # Can throw key error if not found
        fridge_items = fridge_response['Items'][0]['items']

        # Call orders
        orders_response = table.query(
            KeyConditionExpression=Key('pk').eq(restaurant_name) & Key('type').eq('orders')
        )

        orders = orders_response['Items'][0]['orders']

        order_items = []
        expired_items = []
        for fridge_item in fridge_items:
            item_quantity = get_total_item_quantity(fridge_item, orders)

            if item_quantity < fridge_item['desired_quantity']:
                # add item to order
                item_to_order = {
                    'M': {
                        'item_name': {'S': fridge_item['item_name']},
                        'quantity': {'N': str(fridge_item['desired_quantity'] - item_quantity)}
                    }
                }
                order_items.append(item_to_order)

            expired_item_quantity = get_expired_item_quantity_fridge(fridge_item)

            if expired_item_quantity > 0:
                expired_item = {
                    'item_name': fridge_item['item_name'],
                    'quantity': expired_item_quantity
                }

                expired_items.append(expired_item)

        if order_items:
            response = create_order(dynamodb_client, table, restaurant_name, order_items, expired_items, table_name)
        else:
            # return success, no order necessary
            response = {
                'statusCode': 204,
                'body': {
                    'expired_items': expired_items
                }
            }

    except KeyError as ignore:
        response = {
            'statusCode': 404,
            'body': 'Fridge not found.'
        }
        print(ignore)

    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': 'Error accessing DynamoDB: ' + str(e)
        }

    return response


def create_order(dynamodb_client, table, restaurant_name, order_items, expired_items, table_name):
    """
    Creates a new order for a given restaurant_id.

    :param dynamodb_client: The MasterDB client.
    :param table: DynamoDB table resource for specified table_name.
    :param restaurant_name: Name of restaurant.
    :param order_items: Items to be added to order.
    :param expired_items: Expired item entries from fridge.
    :param table_name: Name of MasterDB.
    :raises Exception: Thrown if order id could not be generated.
    :return: 201 - Success: order created.
        500 - Internal error resulting in entry not being added.
    """
    response = None

    restaurant_id = restaurant_name
    order_date = int(time.time())
    day_in_secs = 86400
    delivery_date = order_date + day_in_secs

    try:
        order_id = generate_order_id(table, restaurant_id)
        if order_id is None:
            raise Exception('Order ID could not be generated.')

        dynamodb_client.update_item(
            TableName=table_name,
            Key={
                'pk': {'S': restaurant_id},
                'type': {'S': 'orders'}
            },
            UpdateExpression="SET #ord = list_append(#ord, :new_order)",
            ExpressionAttributeNames={
                '#ord': 'orders'
            },
            ExpressionAttributeValues={
                ':new_order': {
                    'L': [
                        {
                            'M': {
                                'id': {'S': order_id},
                                'delivery_date': {'N': str(delivery_date)},
                                'date_ordered': {'N': str(order_date)},
                                'items': {'L': order_items}
                            }
                        }
                    ]
                },
            },
        )

        response = {
            'statusCode': 201,
            'body': {
                'order_id': order_id,
                'expired_items': expired_items
            }
        }

    except NotFoundException as e:
        response = {
            'statusCode': 500,
            'body': 'Exception: Restaurant does not exist.'
        }

    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': 'ClientError: ' + str(e)
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': 'Exception: ' + str(e)
        }

    return response