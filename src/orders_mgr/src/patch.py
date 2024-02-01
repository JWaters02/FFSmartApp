from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from .custom_exceptions import BadRequestException


def update_fridge_with_delivery(event, table):
    """
    Adds items to their existing fridge entries in fridge table

    :param event: Event passed to lambda.
    :param table: MasterDB table resource.
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 200 - Successful.
        404 - Restaurant or item does not exist.
        500 - Internal Server Error.
    """

    response = None

    if 'body' not in event and 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    restaurant_name = event['body']['restaurant_id']

    try:
        table_response = table.query(
            KeyConditionExpression=Key('pk').eq(restaurant_name) & Key('type').eq('fridge')
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