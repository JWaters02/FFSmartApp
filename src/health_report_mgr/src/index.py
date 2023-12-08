import os
import boto3
import json
from boto3.dynamodb.conditions import Key
# NOTE: if you want to import another file aka src/utils.py, you must put a `.` before its name `import .utils`.
# Not doing this will not error locally but will error on the lambda.


def handler(event, context):
    response = None

    try:
        __master_db_name__ = os.environ.get('MASTER_DB')

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(__master_db_name__)

        partition_key_value = event['pk']
        sort_key_value = event['type']

        # Fetch data from DynamoDB
        database_response = table.query(
            KeyConditionExpression=Key('pk').eq(partition_key_value) & Key('type').eq(sort_key_value)
        )
        data = database_response['Items']

        # Create SES client
        ses = boto3.client('ses')

        # Send email
        ses_response = ses.send_email(
            Source='SENDER_EMAIL',  # TODO: to be verified and other stuff
            Destination={
                'ToAddresses': [
                    'ben@benlewisjones.com',
                ],
            },
            Message={
                'Subject': {
                    'Data': 'DynamoDB Data',
                },
                'Body': {
                    'Text': {
                        'Data': json.dumps(data),
                    },
                }
            }
        )

        response = {
            'statusCode': 200,
            'body': json.dumps('Email sent!')
        }

    except Exception as e:  # try and use other exception types such as BotoCoreError, with different status codes.
        response = {
            'statusCode': 500,
            'body': {
                'details': str(e)
            }
        }

    return response
