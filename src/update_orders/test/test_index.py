import unittest
import os
from unittest import mock
from unittest.mock import patch, MagicMock, Mock
from src.index import handler
from src.emails import send_delivery_email, send_expired_items
from src.utils import get_cognito_user_email, list_of_all_pks_and_delivery_emails
from src.lambda_requests import create_an_order_token, remove_old_tokens, remove_old_objects, create_new_order

class TestPost(unittest.TestCase):

    def test_example(self):
        mock_event = {}
        mock_context = {}

        response = handler(mock_event, mock_context)

        expected_response = {
            'statusCode': 200,
            'body': {
                'details': 'function works',
            }
        }

        self.assertEqual(response, expected_response)


class TestEmailFunctions(unittest.TestCase):
    # Explaination here for what the test is actually doing in general
    @patch('src.emails.generate_delivery_email_body')
    @patch('src.emails.generate_and_send_email')
    def test_send_delivery_email(self, mock_generate_and_send_email, mock_generate_delivery_email_body):
        ses_client = MagicMock()
        restaurant = {'delivery_company_email': 'delivery@example.com'}
        token = 'example_token'

        mock_generate_delivery_email_body.return_value = 'example_body'

        send_delivery_email(ses_client, restaurant, token)

        mock_generate_delivery_email_body.assert_called_once_with(restaurant, token)
        mock_generate_and_send_email.assert_called_once_with(
            ses_client,
            'Your delivery link',
            'example_body',
            ['delivery@example.com'],
            'no-reply@ffsmart.benlewisjones.com'
        )

    @patch('src.emails.get_cognito_user_email')
    @patch('src.emails.generate_expired_items_email_body')
    @patch('src.emails.generate_and_send_email')
    # Explaination here for what the test is actually doing in general
    def test_send_expired_items(self, mock_generate_and_send_email, mock_generate_expired_items_email_body,
                                mock_get_cognito_user_email):
        ses_client = MagicMock()
        restaurant = {'pk': 'example_pk'}
        expired_items = ['item1', 'item2']

        mock_get_cognito_user_email.return_value = 'user@example.com'
        mock_generate_expired_items_email_body.return_value = 'example_body'

        send_expired_items(ses_client, restaurant, expired_items)

        mock_get_cognito_user_email.assert_called_once_with('example_pk')
        mock_generate_expired_items_email_body.assert_called_once_with(restaurant, expired_items)
        mock_generate_and_send_email.assert_called_once_with(
            ses_client,
            'Food has expired with your fridge',
            'example_body',
            ['user@example.com'],
            'no-reply@ffsmart.benlewisjones.com'
        )





class TestGetCognitoUserEmail(unittest.TestCase):
    # Explaination here for what the test is actually doing in general
    @patch('src.utils.boto3.client')
    def test_get_cognito_user_email(self, mock_boto3_client):
        mock_cognito_client = MagicMock()
        mock_boto3_client.return_value = mock_cognito_client

        username = 'test_user'
        user_attributes = [{'Name': 'email', 'Value': 'user@example.com'}]

        os.environ['USER_POOL_ID'] = 'your_user_pool_id'

        mock_cognito_client.admin_get_user.return_value = {'UserAttributes': user_attributes}

        result = get_cognito_user_email(username)

        mock_boto3_client.assert_called_once_with('cognito-idp')
        mock_cognito_client.admin_get_user.assert_called_once_with(UserPoolId='your_user_pool_id', Username='test_user')

        del os.environ['USER_POOL_ID']

        self.assertEqual(result, 'user@example.com')
        # Explaination here for what the test is actually doing in general
    @patch('src.utils.boto3.client')
    def test_get_cognito_user_email_no_email_attribute(self, mock_boto3_client):
        mock_cognito_client = MagicMock()
        mock_boto3_client.return_value = mock_cognito_client

        username = 'test_user'
        user_attributes = [{'Name': 'some_other_attribute', 'Value': 'some_value'}]

        os.environ['USER_POOL_ID'] = 'your_user_pool_id'

        mock_cognito_client.admin_get_user.return_value = {'UserAttributes': user_attributes}

        result = get_cognito_user_email(username)

        mock_boto3_client.assert_called_once_with('cognito-idp')
        mock_cognito_client.admin_get_user.assert_called_once_with(UserPoolId='your_user_pool_id', Username='test_user')

        del os.environ['USER_POOL_ID']

        self.assertIsNone(result)
class TestCreateOrderToken(unittest.TestCase):
    # Explaination here for what the test is actually doing in general
    @patch('src.lambda_requests.make_lambda_request')
    def test_create_an_order_token_success(self, mock_make_lambda_request):

        mock_response = {
            'statusCode': 200,
            'body': {
                'token': 'your_token_here'
            }
        }
        mock_make_lambda_request.return_value = mock_response


        lambda_client = Mock()
        lambda_arn = 'your_lambda_arn'
        restaurant = {'pk': 'your_restaurant_id'}
        order_id = 'your_order_id'


        result = create_an_order_token(lambda_client, lambda_arn, restaurant, order_id)


        self.assertEqual(result, 'your_token_here')
        mock_make_lambda_request.assert_called_once_with(
            lambda_client,
            {
                'httpMethod': 'PATCH',
                'action': 'set_token',
                'body': {
                    'restaurant_id': restaurant['pk'],
                    'id_type': 'order',
                    'object_id': order_id
                }
            },
            lambda_arn
        )

    @patch('src.lambda_requests.make_lambda_request')
    # Explaination here for what the test is actually doing in general
    def test_create_an_order_token_failure(self, mock_make_lambda_request):
        # Mock the lambda response for a failed call
        mock_response = {
            'statusCode': 500,
            'body': 'Internal Server Error'
        }
        mock_make_lambda_request.return_value = mock_response


        lambda_client = Mock()
        lambda_arn = 'your_lambda_arn'
        restaurant = {'pk': 'your_restaurant_id'}
        order_id = 'your_order_id'
        result = create_an_order_token(lambda_client, lambda_arn, restaurant, order_id)


        self.assertIsNone(result)
        mock_make_lambda_request.assert_called_once_with(
            lambda_client,
            {
                'httpMethod': 'PATCH',
                'action': 'set_token',
                'body': {
                    'restaurant_id': restaurant['pk'],
                    'id_type': 'order',
                    'object_id': order_id
                }
            },
            lambda_arn
        )
class TestRemoveOldTokens(unittest.TestCase):
    # Explaination here for what the test is actually doing in general
    @patch('src.lambda_requests.make_lambda_request')
    def test_remove_old_tokens_success(self, mock_make_lambda_request):
        mock_response = {
            'statusCode': 200,
            'body': {
                'objects_removed': [{'id_type': 'order', 'object_id': 'order_id_1'}, {'id_type': 'order', 'object_id': 'order_id_2'}]
            }
        }
        mock_make_lambda_request.return_value = mock_response

        lambda_client = Mock()
        lambda_arn = 'your_lambda_arn'
        restaurant = {'pk': 'your_restaurant_id'}

        result = remove_old_tokens(lambda_client, lambda_arn, restaurant)

        self.assertEqual(result, [{'id_type': 'order', 'object_id': 'order_id_1'}, {'id_type': 'order', 'object_id': 'order_id_2'}])
        mock_make_lambda_request.assert_called_once_with(
            lambda_client,
            {
                'httpMethod': 'DELETE',
                'action': 'clean_up_old_tokens',
                'body': {
                    'restaurant_id': restaurant['pk']
                }
            },
            lambda_arn
        )

    @patch('src.lambda_requests.make_lambda_request')
    def test_remove_old_tokens_failure(self, mock_make_lambda_request):
        # Explaination here for what the test is actually doing in general
        mock_response = {
            'statusCode': 500,
            'body': 'Internal Server Error'
        }
        mock_make_lambda_request.return_value = mock_response

        lambda_client = Mock()
        lambda_arn = 'your_lambda_arn'
        restaurant = {'pk': 'your_restaurant_id'}

        result = remove_old_tokens(lambda_client, lambda_arn, restaurant)

        self.assertEqual(result, [])
        mock_make_lambda_request.assert_called_once_with(
            lambda_client,
            {
                'httpMethod': 'DELETE',
                'action': 'clean_up_old_tokens',
                'body': {
                    'restaurant_id': restaurant['pk']
                }
            },
            lambda_arn
        )
class TestRemoveOldObjects(unittest.TestCase):
    @patch('src.lambda_requests.make_lambda_request')
    # Explaination here for what the test is actually doing in general
    def test_remove_old_objects(self, mock_make_lambda_request):
        mock_response = {
            'statusCode': 200
        }
        mock_make_lambda_request.return_value = mock_response
        lambda_client = Mock()
        order_lambda_arn = 'your_order_lambda_arn'
        restaurant = {'pk': 'your_restaurant_id'}
        old_tokens = [{'id_type': 'order', 'object_id': 'order_id_1'}, {'id_type': 'order', 'object_id': 'order_id_2'}]
        remove_old_objects(lambda_client, order_lambda_arn, restaurant, old_tokens)
        expected_calls = [
            mock.call(
                lambda_client,
                {
                    'httpMethod': 'DELETE',
                    'action': 'delete_order',
                    'body': {
                        'restaurant_id': restaurant['pk'],
                        'order_id': 'order_id_1'
                    }
                },
                order_lambda_arn
            ),
            mock.call(
                lambda_client,
                {
                    'httpMethod': 'DELETE',
                    'action': 'delete_order',
                    'body': {
                        'restaurant_id': restaurant['pk'],
                        'order_id': 'order_id_2'
                    }
                },
                order_lambda_arn
            )
        ]

        mock_make_lambda_request.assert_has_calls(expected_calls)
        
class TestCreateNewOrder(unittest.TestCase):
    @patch('src.lambda_requests.make_lambda_request')
    # Explaination here for what the test is actually doing in general
    def test_create_new_order_success(self, mock_make_lambda_request):
        mock_response = {
            'statusCode': 200,
            'body': {
                'order_id': 'new_order_id'
            }
        }
        mock_make_lambda_request.return_value = mock_response
        lambda_client = Mock()
        lambda_arn = 'your_order_lambda_arn'
        restaurant = {'pk': 'your_restaurant_id'}
        result = create_new_order(lambda_client, lambda_arn, restaurant)

        expected_result = {
            'statusCode': 200,
            'body': {
                'order_id': 'new_order_id'
            }
        }
        self.assertEqual(result, expected_result)

        mock_make_lambda_request.assert_called_once_with(
            lambda_client,
            {
                'httpMethod': 'POST',
                'action': 'create_order',
                'body': {
                    'restaurant_id': restaurant['pk']
                }
            },
            lambda_arn
        )

if __name__ == '__main__':
    unittest.main()