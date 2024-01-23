import json
import os
from flask import flash
from botocore.exceptions import ClientError, BotoCoreError
from datetime import datetime

from lib.globals import (
    users_mgr_lambda
)


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


def get_restaurant_id(cognito_client, access_token):
    """
    Gets the restaurant id for the current user.
    :param cognito_client: Client for cognito.
    :param access_token: Users access token.
    :return: The current users restaurant_id, admin users have their username returned.
    """
    try:
        user_details = cognito_client.get_user(
            AccessToken=access_token
        )

        if 'UserAttributes' not in user_details:
            return None

        for attribute in user_details['UserAttributes']:
            if 'custom:restaurant_id' == attribute['Name']:
                return attribute['Value']
        else:
            # If there is no restaurant id, then the current user must be a restaurant
            return user_details['Username']

    except ClientError as ignore:
        return None

    except BotoCoreError as ignore:
        return None


def get_user_role(cognito_client, access_token, lambda_client, username):
    """
    Gets the job role for the current user, restaurant accounts are assumed to be Admin.
    :param cognito_client: Client for Cognito.
    :param access_token: Current users access token.
    :param lambda_client: Client for lambda.
    :param username: Username of current user.
    :return: Role of current user, restaurant accounts are assumed to be
    Admin. If anything goes wrong, chef is returned.
    """
    try:
        restaurant_id = get_restaurant_id(cognito_client, access_token)

        if username == restaurant_id:
            return 'Admin'

        payload = {
            'httpMethod': 'GET',
            'action': 'get_user',
            'body': {
                'restaurant_id': restaurant_id,
                'username': username
            }
        }

        response = make_lambda_request(lambda_client, payload, users_mgr_lambda)
        if response['statusCode'] != 200:
            return 'Chef'

        return response['body']['role']

    except ClientError as ignore:
        return 'Chef'

    except BotoCoreError as ignore:
        return 'Chef'


def get_admin_settings(username, lambda_client, function_name):
    """
    Gets the admin settings.

    :param username: Username to get the settings for.
    :param lambda_client: Client of the lambda.
    :param function_name: Function name of the lambda.
    :return: The lambda's response.
    """
    payload = json.dumps({
            "httpMethod": "GET",
            "action": "get_admin_settings",
            "body": {
                "restaurant_id": username
            }
        })

    return make_lambda_request(lambda_client, payload, function_name)


def get_order_data(lambda_client, function_name, restaurant_id):
    """
    Gets the order data for the current restaurant.
    :param lambda_client: Client of the lambda.
    :param function_name: ID of the restaurant.
    :param restaurant_id: Current restaurant_id.
    :return: The order data.
    """

    try:
        payload = json.dumps({
            "httpMethod": "GET",
            "action": "get_all_orders",
            "body": {
                "restaurant_id": restaurant_id
            }
        })

        response = make_lambda_request(lambda_client, payload, function_name)
        if response['statusCode'] == 200:
            orders = response['body']['items']
            for order in orders:
                order['date_ordered'] = datetime.fromtimestamp(order['date_ordered']).strftime('%Y-%m-%d')
                order['delivery_date'] = datetime.fromtimestamp(order['delivery_date']).strftime('%Y-%m-%d')
            return orders
        else:
            return []

    except Exception as e:
        print(e)
        return []


def validate_token(token, lambda_client, restaurant_id, token_mgr_lambda):
    """
    Validates a token.
    :param token: Token to validate.
    :param lambda_client: Client of the lambda.
    :param restaurant_id: ID of the restaurant.
    :param token_mgr_lambda: Name of the lambda.
    :return: True if valid.
    """
    
    try:
        payload = {
            "httpMethod": "POST",
            "action": "validate_token",
            "body": {
                "restaurant_id": restaurant_id,
                "request_token": token
            }
        }

        response = make_lambda_request(lambda_client, payload, token_mgr_lambda)
        if response['statusCode'] == 200:
            return True
        else:
            flash('Invalid or expired token.', 'danger')
            return False

    except Exception as e:
        print(e)
        flash('Invalid or expired token.', 'danger')
        return False