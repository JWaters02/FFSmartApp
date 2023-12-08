import os
import boto3
from boto3.dynamodb.conditions import Key
# NOTE: if you want to import another file aka src/utils.py, you must put a `.` before its name `import .utils`.
# Not doing this will not error locally but will error on the lambda.


def handler(event, context):
    response = None

    try:
        __master_db_name__ = os.environ.get('MASTER_DB')

        # Init DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(__master_db_name__)

        # Read from event example
        data = event.get('data')
        partition_key_value = event.get('pk')
        sort_key_value = event.get('type')

        # Write example
        table.put_item(
            Item={
                'pk': partition_key_value,
                'type': sort_key_value,
                'data': data
            }
        )

        # Read example
        database_response = table.query(
            KeyConditionExpression=Key('pk').eq(partition_key_value) & Key('type').eq(sort_key_value)
        )

        response = {
            'statusCode': 200,
            'body': {
                'details': 'function works',
                'db_response': database_response['Items']
            }
        }
    except Exception as e:  # try and use other exception types such as BotoCoreError, with different status codes.
        response = {
            'statusCode': 500,
            'body': {
                'details': str(e)
            }
        }

    return response
