import secrets
import time
from botocore.exceptions import ClientError
from .custom_exceptions import BadRequestException, NotFoundException


def set_token(event, table):
    """
    Creates a token.
    :param event: Event passed to lambda.
    :param table: MasterDB resource.
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 200 & token - Success.
        500 - Internal Error and failed to create new token.
    """

    response = None

    if 'body' not in event:
        raise BadRequestException('No request body exists.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'id_type' not in event['body']:
        raise BadRequestException('Bad request id_type not found in body.')

    if event['body']['id_type'] not in ['order']:
        raise BadRequestException(f"Bad request {event['body']['id_type']} is not a valid type.")

    if 'id_to_store' not in event['body']:
        raise BadRequestException('Bad request id not found in body.')

    restaurant_id = event['body']['restaurant_id']
    id_type = event['body']['id_type']
    id_to_store = event['body']['id_to_store']

    try:
        random_number = str(secrets.randbits(64))
        expiry_date_unix_time = int(time.time() + 259200)  # Expires in 3 days

        dynamo_response = table.update_item(
            Key={
                'pk': restaurant_id,
                'type': 'tokens'
            },
            UpdateExpression="SET tokens = list_append(tokens, :val)",
            ExpressionAttributeValues={
                ':val': [{
                    'token': random_number,
                    'expiry_date': expiry_date_unix_time,
                    'id_type': id_type,
                    'id_to_store': id_to_store
                }]
            },
        )

        response = {
            'statusCode': 200,
            'body': {
                'token': random_number,

            }
        }

    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': 'Client Error: ' + str(e)
        }

    return response
