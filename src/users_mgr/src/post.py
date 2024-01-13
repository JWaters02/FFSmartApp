from botocore.exceptions import ClientError
from src.custom_exceptions import NotFoundException, BadRequestException


def create_new_restaurant_dynamodb_entries(dynamodb_client, event, table_name):
    """
    Creates a new restaurant entry in MasterDB.

    :param dynamodb_client: Client for MasterDB.
    :param event: Event passed to lambda.
    :param table_name: Name of MasterDB.
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 200 - Successful entry.
        409 - Entry already exists.
        500 - Internal error.
    """

    if 'body' not in event and 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    restaurant_name = event['body']['restaurant_name']

    try:
        dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    'Put': {
                        'TableName': table_name,
                        'Item': {
                            'pk': {'S': restaurant_name},
                            'type': {'S': 'fridge'},
                            'is_front_door_open': {'BOOL': False},
                            'is_back_door_open': {'BOOL': False},
                            'items': {'L': []}
                        },
                        'ConditionExpression': 'attribute_not_exists(pk) AND attribute_not_exists(#type)',
                        'ExpressionAttributeNames': {
                            '#type': 'type'
                        }
                    }
                },
                {
                    'Put': {
                        'TableName': table_name,
                        'Item': {
                            'pk': {'S': restaurant_name},
                            'type': {'S': 'orders'},
                            'orders': {'L': []}
                        },
                        'ConditionExpression': 'attribute_not_exists(pk) AND attribute_not_exists(#type)',
                        'ExpressionAttributeNames': {
                            '#type': 'type'
                        }
                    }
                },
                {
                    'Put': {
                        'TableName': table_name,
                        'Item': {
                            'pk': {'S': restaurant_name},
                            'type': {'S': 'users'},
                            'users': {'L': []}
                        },
                        'ConditionExpression': 'attribute_not_exists(pk) AND attribute_not_exists(#type)',
                        'ExpressionAttributeNames': {
                            '#type': 'type'
                        }
                    }
                },
                {
                    'Put': {
                        'TableName': table_name,
                        'Item': {
                            'pk': {'S': restaurant_name},
                            'type': {'S': 'tokens'},
                            'tokens': {'L': []}
                        },
                        'ConditionExpression': 'attribute_not_exists(pk) AND attribute_not_exists(#type)',
                        'ExpressionAttributeNames': {
                            '#type': 'type'
                        }
                    }
                }
            ]
        )

        response = {'statusCode': 200}

    except ClientError as e:
        # catch if at least one entry already exists
        if 'TransactionCanceledException' in e.response['Error']['Code'] \
                and 'ConditionalCheckFailed' in e.response['Error']['Message']:
            response = {
                'statusCode': 409,
                'body': 'ConditionalCheckFailedException: ' + str(e)
            }
        # all other cases
        else:
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


def create_user(dynamodb_client, event, table_name):
    """
    Creates a new user entry for a given restaurant_id.

    :param dynamodb_client: The MasterDB client.
    :param event: Event passed to lambda.
    :param table_name: Name of MasterDB
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 200 - Success.
        500 - Internal error resulting in entry not being added.
    """
    response = None

    if 'body' not in event:
        raise BadRequestException('No request body exists.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'username' not in event['body']:
        raise BadRequestException('Bad request username not found in body.')

    if 'role' not in event['body']:
        raise BadRequestException('Bad request role not found in body.')

    restaurant_id = event['body']['restaurant_id']
    username = event['body']['username']
    role = event['body']['role']

    try:
        dynamodb_client.update_item(
            TableName=table_name,
            Key={
                'pk': {'S': restaurant_id},
                'type': {'S': 'users'}
            },
            UpdateExpression="SET #usr = list_append(#usr, :new_user)",
            ExpressionAttributeNames={
                '#usr': 'users'
            },
            ExpressionAttributeValues={
                ':new_user': {
                    'L': [
                        {
                            'M': {
                                'username': {'S': username},
                                'role': {'S': role}
                            }
                        }
                    ]
                }
            },
            ReturnValues="UPDATED_NEW"
        )

        response = {'statusCode': 200}

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


def update_user(event, table):
    """
    Updates the contents of a user entry for a given username and restaurant_id.
    :param event: Event passed to lambda.
    :param table: Table resource for MasterDB.
    :raises BadRequestException: Thrown if format is not as expected.
    :return: 200 - Success.
        404 - Restaurant or user not found.
        500 - Internal Server Error.
    """

    response = {
        'statusCode': 200,
    }

    if 'body' not in event:
        raise BadRequestException('No request body exists.')

    if 'restaurant_id' not in event['body']:
        raise BadRequestException('Bad request restaurant_id not found in body.')

    if 'username' not in event['body']:
        raise BadRequestException('Bad request username not found in body.')

    if 'new_role' not in event['body']:
        raise BadRequestException('Bad request new_role not found in body.')

    username = event['body']['username']
    new_role = event['body']['new_role']
    restaurant_id = event['body']['restaurant_id']

    try:
        dynamo_response = table.get_item(
            Key={
                'pk': restaurant_id,
                'type': 'users'
            }
        )

        if 'Item' not in dynamo_response:
            raise NotFoundException("Item not found: " + restaurant_id)

        users = dynamo_response['Item']['users']

        for user in users:
            if user['username'] == username:
                user['role'] = new_role
                break

        else:
            raise NotFoundException("User was not found.")

        table.update_item(
            Key={
                'pk': restaurant_id,
                'type': 'users'
            },
            UpdateExpression="SET #usr = :val",
            ExpressionAttributeNames={
                '#usr': 'users'
            },
            ExpressionAttributeValues={
                ':val': users
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
            'body': 'Client Error: ' + str(e)
        }

    return response
