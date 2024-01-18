import json
from boto3.dynamodb.conditions import Attr

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
            for item in dynamo_response['Items']:
                all_pks.append({
                    'pk': item['pk'],
                    'delivery_company_email': item['delivery_company_email']
                })

        last_evaluated_key = dynamo_response.get('LastEvaluatedKey')
        next_page_exists = last_evaluated_key is not None

    return all_pks
