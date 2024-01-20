from .utils import make_lambda_request


def create_new_order(lambda_client, lambda_arn, restaurant):
    orders_payload = {
        'httpMethod': 'POST',
        'action': 'create_order',
        'body': {
            'restaurant_id': restaurant['pk']
        }
    }

    return make_lambda_request(lambda_client, orders_payload, lambda_arn)


def create_an_order_token(lambda_client, lambda_arn, restaurant, order_id):
    token_payload = {
        'httpMethod': 'PATCH',
        'action': 'set_token',
        'body': {
            'restaurant_id': restaurant['pk'],
            'id_type': 'order',
            'object_id': order_id
        }
    }

    token_lambda_response = make_lambda_request(lambda_client, token_payload, lambda_arn)

    if token_lambda_response['statusCode'] != 200:
        # Nothing we can do
        return None

    return token_lambda_response['body']['token']


def remove_old_tokens(lambda_client, lambda_arn, restaurant):
    token_payload = {
        'httpMethod': 'DELETE',
        'action': 'clean_up_old_tokens',
        'body': {
            'restaurant_id': restaurant['pk']
        }
    }

    token_lambda_response = make_lambda_request(lambda_client, token_payload, lambda_arn)

    result = []

    if token_lambda_response['statusCode'] == 200:
        result = token_lambda_response['body']['objects_removed']

    return result


def remove_old_objects(lambda_client, order_lambda_arn, restaurant, old_tokens):

    for token in old_tokens:
        if token['id_type'] == 'order':
            payload = {
                'httpMethod': 'DELETE',
                'action': 'delete_order',
                'body': {
                    'restaurant_id': restaurant['pk'],
                    'order_id': token['object_id']
                }
            }

            make_lambda_request(lambda_client, payload, order_lambda_arn)