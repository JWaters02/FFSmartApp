import json
import os
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError, BotoCoreError


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


def list_of_all_pks_and_delivery_emails(table):
    """
    Gets all the PKs and corresponding delivery emails from the master table.
    :param table: The resource of the master dynamo table.
    :return: A list containing a dict with each pk and corresponding delivery email.
    """
    all_pks = []

    # for large responses from dynamo it can page the responses
    next_page_exists = True

    # dynamo will return the last key, this can be used to get the next page
    last_evaluated_key = None

    while next_page_exists:
        # use the last key to get the next page if it exists
        if last_evaluated_key:
            dynamo_response = table.scan(
                FilterExpression=Attr('type').eq('admin_settings'),
                ExclusiveStartKey=last_evaluated_key

            )
        else:
            dynamo_response = table.scan(
                FilterExpression=Attr('type').eq('admin_settings'),
            )

        if 'Items' in dynamo_response:
            all_pks.extend(dynamo_response['Items'])

        last_evaluated_key = dynamo_response.get('LastEvaluatedKey')
        next_page_exists = last_evaluated_key is not None

    return all_pks


def generate_and_send_email(ses_client, subject, body, destinations, sender):
    """
    Generates and then sends an email to destination.

    :param ses_client: Client of the ses.
    :param subject: The emails subject.
    :param body: The emails body.
    :param destinations: The an array of destination email addresses.
    :param sender: The sender email address, this must be a verified email address.
    :return: True if email was sent.
    """

    try:
        ses_client.send_email(
            Destination={
                'ToAddresses': destinations,
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': body,
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject,
                },
            },
            Source=sender
        )

        return True

    except ClientError as ignore:
        # Handle email not being sent
        return False


def generate_delivery_email_body(restaurant_admin_settings, token):
    """
    Creates the body of the email sent to the delivery driver.

    :param restaurant_admin_settings: The restaurant settings.
    :param token: Token for the email.
    :return: The emails body.
    """
    delivery_link = f'http://0.0.0.0:80/delivery/{restaurant_admin_settings["pk"]}/{token}'

    return f'''
    Hello Driver,
    
    You have a delivery for {restaurant_admin_settings['restaurant_details']['restaurant_name']}.
    
    Delivery link: {delivery_link}
    
    Address:
    {restaurant_admin_settings['restaurant_details']['location']['city']}
    {restaurant_admin_settings['restaurant_details']['location']['postcode']}
    {restaurant_admin_settings['restaurant_details']['location']['street_address_1']}
    {restaurant_admin_settings['restaurant_details']['location']['street_address_2']}
    {restaurant_admin_settings['restaurant_details']['location']['street_address_3']}
    
    Good luck!
    This link will self-destruct in 3 days.
    '''


def generate_expired_items_email_body(restaurant_admin_settings, expired_items):
    """
    Creates the body of the email sent to the restaurant showing all the expired items.

    :param restaurant_admin_settings: The restaurant settings.
    :param expired_items: A list of all the expired items.
    :return: The emails body.
    """
    list_of_items = ''

    for item in expired_items:
        list_of_items += f"{item['item_name']}: {item['quantity']}\r\t"

    return f"""
    Hello {restaurant_admin_settings['restaurant_details']['restaurant_name']},
    
    The following items have expired:
    {list_of_items}
    
    This has been reported as a part of your health report.
    
    Thanks
    """


def get_cognito_user_email(username):
    """
    Gets the email address for a cognito user.

    :param username: Username of the cognito user.
    :return: The emails body.
    """
    __user_pool_id__ = os.environ.get('USER_POOL_ID')
    cognito_client = boto3.client('cognito-idp')

    try:
        cognito_response = cognito_client.admin_get_user(
            UserPoolId=__user_pool_id__,
            Username=username
        )

        for attribute in cognito_response['UserAttributes']:
            if attribute['Name'] == 'email':
                return attribute['Value']

    except ClientError as ignore:
        return None

    except BotoCoreError as ignore:
        return None