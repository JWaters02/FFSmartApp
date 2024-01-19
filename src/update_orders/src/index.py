import os
import boto3
from .utils import make_lambda_request, list_of_all_pks_and_delivery_emails, generate_and_send_email, \
    generate_email_body


def handler(event, data):
    __token_mgr_arn__ = os.environ.get('TOKEN_MGR_ARN')
    __master_db_name__ = os.environ.get('MASTER_DB')

    ses_client = boto3.client('ses')
    lambda_client = boto3.client('lambda', region_name='eu-west-1')
    dynamodb_resource = boto3.resource('dynamodb')
    table = dynamodb_resource.Table(__master_db_name__)

    all_items = list_of_all_pks_and_delivery_emails(table)

    for restaurant in all_items:

        # 1. Create new orders
        # TODO: create new orders

        # 2. get a token
        payload = {
            'httpMethod': 'PATCH',
            'action': 'set_token',
            'body': {
                'restaurant_id': restaurant['pk']
            }
        }

        lambda_response = make_lambda_request(lambda_client, payload, __token_mgr_arn__)

        if lambda_response['statusCode'] != 200:
            # Nothing we can do
            continue

        token = lambda_response['body']['token']

        # 3. generate body of email
        body = generate_email_body(restaurant, token)

        # 4. send email
        destination = [restaurant['delivery_company_email']]
        sender = 'no-reply@ffsmart.benlewisjones.com'
        subject = 'Your delivery link'

        generate_and_send_email(ses_client, subject, body, destination, sender)

        # 5. old tokens must be removed
        payload = {
            'httpMethod': 'DELETE',
            'action': 'clean_up_old_tokens',
            'body': {
                'restaurant_id': restaurant['pk']
            }
        }

        lambda_response = make_lambda_request(lambda_client, payload, __token_mgr_arn__)

    response = {
        'statusCode': 200,
    }

    return response
