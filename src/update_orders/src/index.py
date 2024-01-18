import os
import boto3
from .utils import make_lambda_request, list_of_all_pks_and_delivery_emails, generate_and_send_email


def handler(event, data):
    __token_mgr_arn__ = os.environ.get('TOKEN_MGR_ARN')
    __master_db_name__ = os.environ.get('MASTER_DB')

    ses_client = boto3.client('ses')
    lambda_client = boto3.client('lambda', region_name='eu-west-1')
    dynamodb_resource = boto3.resource('dynamodb')
    dynamodb_client = boto3.client('dynamodb')
    table = dynamodb_resource.Table(__master_db_name__)

    '''
    1. get all the PKs /
     
    2. for each restaurant get delivery_company_email & send email
        a. get delivery_company_email /
        b. get orders
        c. generate a tokenized link (next)
        d. send email /
    '''

    all_items = list_of_all_pks_and_delivery_emails(table)
    # TODO: remove the following two lines
    all_items.clear()
    all_items.append({
        'pk': 'house',
        'delivery_company_email': 'lewisjonesben@yahoo.com'
    })

    for restaurant in all_items:
        destination = [restaurant['delivery_company_email']]
        sender = 'info@ffsmart.benlewisjones.com'
        subject = 'Your delivery link'
        body = '''
        https://www.google.com/
        '''

        generate_and_send_email(ses_client, subject, body, destination, sender)

    response = {
        'statusCode': 200,
        'body': {
            'details': 'function works',
        }
    }

    return response
