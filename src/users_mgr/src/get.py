from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from src.custom_exceptions import BadRequestException


def get_all_users(event, table):
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
            KeyConditionExpression=Key('pk').eq(restaurant_name) & Key('type').eq('users')
        )

        # Can throw key error if not found
        users = table_response['Items'][0]['users']

        response = {
            'statusCode': 200,
            'body': {
                'items': users
            }
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


def get_user(event, table):
    """
    Gets a specific user, for a given restaurant_id and username.

    :param event: Event passed to lambda.
    :param table: Client for Master DB.
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 200 - All the user entries contents.
        404 - User not found.
        500 - Internal error.
    """
    response = None

    if 'body' not in event:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'username' not in event['body']:
        raise BadRequestException('Bad request username not found in body.')

    restaurant_name = event['body']['restaurant_id']
    username = event['body']['username']

    try:
        table_response = table.query(
            KeyConditionExpression=Key('pk').eq(restaurant_name) & Key('type').eq('users')
        )

        # Can throw key error if not found
        users = table_response['Items'][0]['users']

        user_in_question = None
        for user in users:
            if 'username' in user and user['username'] == username:
                user_in_question = user
                break

        response = {
            'statusCode': 200,
            'body': user_in_question
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
