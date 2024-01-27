import os
import boto3

from .emails import send_delivery_email, send_expired_items, send_low_stocks_email
from .lambda_requests import create_new_order, create_an_order_token, remove_old_tokens, remove_old_objects,\
    get_list_of_low_stock
from .utils import list_of_all_pks_and_delivery_emails


def handler(event, data):
    __token_mgr_arn__ = os.environ.get('TOKEN_MGR_ARN')
    __orders_mgr_arn__ = os.environ.get('ORDERS_MGR_ARN')
    __fridge_mgr_arn__ = os.environ.get('FRIDGE_MGR_ARN')
    __master_db_name__ = os.environ.get('MASTER_DB')

    ses_client = boto3.client('ses')
    lambda_client = boto3.client('lambda', region_name='eu-west-1')
    dynamodb_resource = boto3.resource('dynamodb')
    table = dynamodb_resource.Table(__master_db_name__)

    all_items = list_of_all_pks_and_delivery_emails(table)

    failed_entries = []

    for restaurant in all_items:
        try:
            ##########################
            # Orders
            orders_response = create_new_order(lambda_client, __orders_mgr_arn__, restaurant)

            if 200 > orders_response['statusCode'] > 299:
                continue

            # Email the restaurant with all the expired items
            if orders_response['body']['expired_items']:
                send_expired_items(ses_client, restaurant, orders_response['body']['expired_items'])

            # Order is created, so an email must be sent to the delivery man
            if orders_response['statusCode'] == 201:
                token = create_an_order_token(
                    lambda_client,
                    __token_mgr_arn__,
                    restaurant,
                    orders_response['body']['order_id']
                )
                send_delivery_email(ses_client, restaurant, token)

            ##########################
            # Send email for low stock
            low_stock = get_list_of_low_stock(lambda_client, __fridge_mgr_arn__, restaurant)
            if low_stock:
                send_low_stocks_email(ses_client, restaurant, low_stock)

            ############################
            # Clean up all tokens no matter the type
            old_token_object_ids = remove_old_tokens(lambda_client, __token_mgr_arn__, restaurant)
            remove_old_objects(lambda_client, __orders_mgr_arn__, restaurant, old_token_object_ids)

        except Exception as ignore:
            # If anything goes wrong, this is important for malformed data
            try:
                failed_entries.append(restaurant['pk'])
            except Exception as also_ignored:
                pass

    if failed_entries:
        response = {
            'statusCode': 200,
            'body': {
                'failed_entries': failed_entries
            }
        }
    else:
        response = {
            'statusCode': 200
        }

    return response
