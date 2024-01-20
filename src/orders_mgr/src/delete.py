from botocore.exceptions import ClientError
from .custom_exceptions import BadRequestException, NotFoundException


def delete_order(event, table):
    """
    Deletes an order for a given order_id and restaurant_id.

    :param event: Event passed to lambda.
    :param table: MasterDB table resource.
    :raises BadRequestException: Thrown if format is not as expected.
    :raises NotFoundException: Thrown if restaurant not found or order does not exist
    :return: 200 - Successful.
        404 - Restaurant or order does not exist.
        500 - Internal Server Error.
    """
    response = {
        'statusCode': 200
    }

    if 'body' not in event:
        raise BadRequestException('No request body exists.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'order_id' not in event['body']:
        raise BadRequestException('Bad request order_id not found in body.')

    restaurant_name = event['body']['restaurant_id']
    order_to_delete = event['body']['order_id']

    try:
        table_response = table.get_item(Key={'pk': restaurant_name, 'type': 'orders'})

        if 'Item' not in table_response:
            raise NotFoundException('Restaurant does not exist.')

        all_orders = table_response['Item']['orders']
        if not any(order['id'] == order_to_delete for order in all_orders):
            raise NotFoundException('Order does not exist.')

        updated_orders = [order for order in all_orders if order['id'] != order_to_delete]
        table.update_item(
            Key={
                'pk': restaurant_name,
                'type': 'orders'
            },
            UpdateExpression="SET #ord = :val",
            ExpressionAttributeNames={
                '#ord': 'orders'
            },
            ExpressionAttributeValues={
                ':val': updated_orders
            }
        )

    except NotFoundException as e:
        response = {
            'statusCode': 404,
            'body': str(e)
        }

    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': 'Error accessing DynamoDB: ' + str(e)
        }

    return response