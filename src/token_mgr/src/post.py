import time
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from .custom_exceptions import BadRequestException, NotFoundException, UnauthorizedException


def validate_token(event, table):
    """
    Validates a given token for a given restaurant, the token cannot have expired.
    :param event: Event passed to lambda.
    :param table: MasterDB resource.
    :return: 200 - Success user is authorized.
        401 - Unauthorized.
        404 - Restaurant not found.
        500 - Internal Server Error.
    """
    response = None

    if 'body' not in event:
        raise BadRequestException('No request body exists.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'request_token' not in event['body']:
        raise BadRequestException('Bad request request_token not found in body.')

    restaurant_id = event['body']['restaurant_id']
    request_token = event['body']['request_token']

    try:
        is_valid = False

        dynamo_response = table.get_item(
            Key={
                'pk': restaurant_id,
                'type': 'tokens'
            }
        )
        item = dynamo_response.get('Item', None)

        if item is None:
            raise NotFoundException('Restaurant does not exist.')

        current_time = int(time.time())

        for token in item['tokens']:
            if request_token == token['token'] and current_time < token['expiry_date']:
                is_valid = True
                break
        else:
            raise UnauthorizedException('Invalid token.')

        response = {
            'statusCode': 200,
        }

    except UnauthorizedException as e:
        response = {
            'statusCode': 401,
            'body': str(e)
        }

    except NotFoundException as e:
        response = {
            'statusCode': 404,
            'body': str(e)
        }

    except ClientError as e:
        response = {
            'statusCode': 500,
            'body': 'Client Error: ' + str(e)
        }

    return response
