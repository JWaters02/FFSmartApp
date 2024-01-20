import os
import boto3

from .emails import send_delivery_email, send_expired_items
from .lambda_requests import create_new_order, create_a_token, remove_old_tokens
from .utils import make_lambda_request, list_of_all_pks_and_delivery_emails, generate_and_send_email, \
    generate_token_email_body


def handler(event, data):
    __token_mgr_arn__ = os.environ.get('TOKEN_MGR_ARN')
    __orders_mgr_arn__ = os.environ.get('ORDERS_MGR_ARN')
    __master_db_name__ = os.environ.get('MASTER_DB')

    ses_client = boto3.client('ses')
    lambda_client = boto3.client('lambda', region_name='eu-west-1')
    dynamodb_resource = boto3.resource('dynamodb')
    table = dynamodb_resource.Table(__master_db_name__)

    all_items = list_of_all_pks_and_delivery_emails(table)

    for restaurant in all_items:
        # Create new order
        orders_response = create_new_order(lambda_client, __orders_mgr_arn__, restaurant)

        if 200 > orders_response['statusCode'] > 299:
            continue

        # Email the restaurant with all the expired items
        if orders_response['body']['expired_items']:
            send_expired_items(ses_client, restaurant, orders_response['body']['expired_items'])

        # Order is created, so an email must be sent to the delivery man
        if orders_response['statusCode'] == 201:
            token = create_a_token(lambda_client, __token_mgr_arn__, restaurant)
            send_delivery_email(ses_client, restaurant, token)

        # Clean up
        remove_old_tokens(lambda_client, __token_mgr_arn__, restaurant)

    response = {
        'statusCode': 200,
    }

    return response
