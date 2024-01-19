from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from .custom_exceptions import BadRequestException


def get_all_orders(event, table):
    """
    Returns all the users given a restaurant_id.

    :param event: Event passed to lambda.
    :param table: Client for Master DB.
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 200 - list of items containing all the users.
        404 - User not found.
        500 - Internal error.
    """

    response = None

    if 'body' not in event and 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    restaurant_name = event['body']['restaurant_id']

    try:
        table_response = table.query(
            KeyConditionExpression=Key('pk').eq(restaurant_name) & Key('type').eq('orders')
        )

        # Can throw key error if not found
        orders = table_response['Items'][0]['orders']

        response = {
            'statusCode': 200,
            'body': {
                'items': orders
            }
        }

    except KeyError as ignore:
        response = {
            'statusCode': 404,
            'body': 'Orders not found.'
        }

    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': 'Error accessing DynamoDB: ' + str(e)
        }

    return response


def get_order(event, table):
    """
    Gets a specific user, for a given restaurant_id and username.

    :param event: Event passed to lambda.
    :param table: Client for Master DB.
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 200 - All the order entries contents.
        404 - User not found.
        500 - Internal error.
    """
    response = None

    if 'body' not in event:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'order_id' not in event['body']:
        raise BadRequestException('Bad request username not found in body.')

    restaurant_name = event['body']['restaurant_id']
    order_id = event['body']['order_id']

    try:
        table_response = table.query(
            KeyConditionExpression=Key('pk').eq(restaurant_name) & Key('type').eq('orders')
        )

        # Can throw key error if not found
        orders = table_response['Items'][0]['orders']

        order_in_question = None
        for order in orders:
            if 'id' in order and order['id'] == order_id:
                order_in_question = order
                break

        response = {
            'statusCode': 200,
            'body': order_in_question
        }

    except KeyError as ignore:
        response = {
            'statusCode': 404,
            'body': 'User not found.'
        }

    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': 'Error accessing DynamoDB: ' + str(e)
        }

    return response