import time
from botocore.exceptions import ClientError
from .custom_exceptions import BadRequestException, NotFoundException


def delete_token(event, table):
    """
    Removes a token for a given restaurant.
    :param event: Event passed to lambda.
    :param table: MasterDB resource.
    :return: 200 - Successfully deleted token.
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

        for index, token in enumerate(item['tokens']):
            if request_token == token['token']:
                item['tokens'].pop(index)
                response = {
                    'statusCode': 200,
                    'body': {
                        'object_id': token['object_id'],
                        'id_type': token['id_type']
                    }
                }
                break
        else:
            raise NotFoundException('Token does not exist.')

        table.update_item(
            Key={
                'pk': restaurant_id,
                'type': 'tokens'
            },
            UpdateExpression="SET tokens = :val",
            ExpressionAttributeValues={
                ':val': item['tokens']
            },
        )

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


def clean_up_old_tokens(event, table):
    """
    Removes every expired token for a restaurant.
    :param event: Event passed to lambda.
    :param table: MasterDB resource.
    :return: 200 - Successful clean-up.
        404 - Restaurant not found.
        500 - Internal Server Error.
    """
    response = None

    if 'body' not in event:
        raise BadRequestException('No request body exists.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    restaurant_id = event['body']['restaurant_id']

    try:
        all_removed_objects = []

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

        new_token_list = []
        for index, token in enumerate(item['tokens']):
            if current_time > token['expiry_date']:
                all_removed_objects.append({
                    'object_id': token['object_id'],
                    'id_type': token['id_type']
                })
            else:
                new_token_list.append(token)

        table.update_item(
            Key={
                'pk': restaurant_id,
                'type': 'tokens'
            },
            UpdateExpression="SET tokens = :val",
            ExpressionAttributeValues={
                ':val': new_token_list
            },
        )

        response = {
            'statusCode': 200,
            'body': {
                'objects_removed': all_removed_objects
            }
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
