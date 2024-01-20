from .utils import make_lambda_request


def create_new_order(lambda_client, lambda_arn, restaurant):
    """
    Creates a new order.

    :param lambda_client: Client of the lambda.
    :param lambda_arn: Arn of order mgr.
    :param restaurant: Admin settings of the restaurant.
    :return: The lambda's response.
    """
    orders_payload = {
        'httpMethod': 'POST',
        'action': 'create_order',
        'body': {
            'restaurant_id': restaurant['pk']
        }
    }

    return make_lambda_request(lambda_client, orders_payload, lambda_arn)


def create_an_order_token(lambda_client, lambda_arn, restaurant, order_id):
    """
    Creates a new token.

    :param lambda_client: Client of the lambda.
    :param lambda_arn: Arn of token mgr.
    :param restaurant: Admin settings of the restaurant.
    :param order_id: The order's id.
    :return: The lambda's body.
    """
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
    """
    Removes the old tokens.

    :param lambda_client: Client of the lambda.
    :param lambda_arn: Arn of token mgr.
    :param restaurant: Admin settings of the restaurant.
    :return: List containing all the removed objects.
    """
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
    """
    Removes old objects from the other entries.

    :param lambda_client: Client of the lambda.
    :param order_lambda_arn: Arn of order mgr.
    :param restaurant: Admin settings of the restaurant.
    :param old_tokens: List of the old tokens.
    :return: None
    """
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