import json
import boto3
from botocore.exceptions import ClientError, BotoCoreError


def create_user(cognito_client, username, email, restaurant_id, user_pool_id):
    """
    Creates a new cognito user.
    :param cognito_client: Client for cognito.
    :param username: New user's username.
    :param email: New user's email.
    :param restaurant_id: ID of restaurant the user belongs to.
    :param user_pool_id: ID of user pool.
    :return: True if successful.
    """
    user_attributes = [
        {
            'Name': 'email',
            'Value': email
        },
        {
            'Name': 'custom:restaurant_id',
            'Value': restaurant_id
        }
    ]

    try:
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=user_attributes,
            DesiredDeliveryMediums=['EMAIL']
        )

        return True

    except ClientError as e:
        return False


def make_lambda_request(lambda_client, payload, function_name):
    """
    Makes a lambda request.
    :param lambda_client: Client of lambda function.
    :param payload: Content to be sent to the event of the lambda.
    :param function_name: Name of the lambda function.
    :return: The response payload.
    """
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    response_payload = json.loads(response['Payload'].read().decode('utf-8'))

    return response_payload


def get_email_by_username(cognito_client, user_pool_id, username):
    """
    Gets the email for a given username.
    :param cognito_client: Client for cognito.
    :param user_pool_id: ID of the user pool.
    :param username: Username in question.
    :return: None if user not found, otherwise, the email if found.
    """

    email = None

    try:
        cognito_response = cognito_client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )

        for attribute in cognito_response['UserAttributes']:
            if attribute['Name'] == 'email':
                email = attribute['Value']

    except ClientError as e:
        print(e)

    return email


def delete_user_by_username(cognito_client, user_pool_id, username):
    """
    Deletes a cognito user.
    :param cognito_client: Client for cognito.
    :param user_pool_id: ID of the user pool.
    :param username: Username in question.
    :return: 200 - Success.
        404 - User was not found.
        500 - Internal error.
    """

    response = 200

    try:
        cognito_response = cognito_client.admin_delete_user(
            UserPoolId=user_pool_id,
            Username=username
        )

        print(cognito_response)

    except ClientError as e:
        print(e)
        error_code = e.response['Error']['Code']

        if error_code == 'UserNotFoundException':
            response = 404
        else:
            response = 500

    return response


def is_user_signed_in(cognito_client, access_token, username):
    """
    Validates a users access token against their username.
    :param cognito_client: Client for cognito.
    :param username: User's username.
    :param access_token: Access token for current sign in session.
    :return: True if valid.
    """

    try:
        user_details = cognito_client.get_user(
            AccessToken=access_token
        )

        if 'Username' in user_details and user_details['Username'] == username:
            return True
        else:
            return False

    except ClientError as ignore:
        return False

    except BotoCoreError as ignore:
        return False
