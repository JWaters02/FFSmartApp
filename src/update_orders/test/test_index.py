import unittest
import os
from unittest.mock import patch, MagicMock
from src.index import handler
from src.emails import send_delivery_email, send_expired_items
from src.utils import get_cognito_user_email, list_of_all_pks_and_delivery_emails

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


if __name__ == '__main__':
    unittest.main()