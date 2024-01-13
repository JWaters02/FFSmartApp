from botocore.exceptions import ClientError
from src.custom_exceptions import BadRequestException, NotFoundException


def delete_user(event, table):
    """
    Removes a user for a given username and restaurant_id.

    :param event: Event passed to lambda.
    :param table: MasterDB table resource.
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 200 - Successful.
        404 - Restaurant or user does not exist.
        500 - Internal Server Error.
    """
    response = {
        'statusCode': 200
    }

    if 'body' not in event:
        raise BadRequestException('No request body exists.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'username' not in event['body']:
        raise BadRequestException('Bad request username not found in body.')

    restaurant_name = event['body']['restaurant_id']
    username_to_delete = event['body']['username']

    try:
        table_response = table.get_item(Key={'pk': restaurant_name, 'type': 'users'})

        if 'Item' not in table_response:
            raise NotFoundException('Restaurant does not exist.')

        all_users = table_response['Item']['users']
        if not any(user['username'] == username_to_delete for user in all_users):
            raise NotFoundException('User does not exist.')

        updated_users = [user for user in all_users if user['username'] != username_to_delete]
        table.update_item(
            Key={
                'pk': restaurant_name,
                'type': 'users'
            },
            UpdateExpression="SET #usr = :val",
            ExpressionAttributeNames={
                '#usr': 'users'
            },
            ExpressionAttributeValues={
                ':val': updated_users
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
