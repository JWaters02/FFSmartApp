import unittest
import os
from unittest import mock
from unittest.mock import patch, MagicMock, Mock
from src.index import handler
from src.emails import send_delivery_email, send_expired_items
from src.utils import get_cognito_user_email, list_of_all_pks_and_delivery_emails, generate_delivery_email_body, generate_expired_items_email_body, make_lambda_request, generate_and_send_email,ClientError
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

# This is testing the email functions that we use with our application adn their mocked responses
class TestEmailFunctions(unittest.TestCase):
    # This is patching in a mocked resource
    @patch('src.emails.generate_delivery_email_body')
    @patch('src.emails.generate_and_send_email')

    # This is testing the sending of the delivery email when an order is created
    def test_send_delivery_email(self, mock_generate_and_send_email, mock_generate_delivery_email_body):
        # This is the mocked data
        ses_client = MagicMock()
        restaurant = {'delivery_company_email': 'delivery@example.com'}
        token = 'example_token'

        # This is mocking the body of the email
        mock_generate_delivery_email_body.return_value = 'example_body'

        # Running the function against our mocked data
        send_delivery_email(ses_client, restaurant, token)

        # Ensure that the function is only called once
        mock_generate_delivery_email_body.assert_called_once_with(restaurant, token)
        # Ensure that the function is only called once with this data
        mock_generate_and_send_email.assert_called_once_with(
            ses_client,
            'Your delivery link',
            'example_body',
            ['delivery@example.com'],
            'no-reply@ffsmart.benlewisjones.com'
        )

    # This is patching in a mocked resource
    @patch('src.emails.get_cognito_user_email')
    @patch('src.emails.generate_expired_items_email_body')
    @patch('src.emails.generate_and_send_email')
    # This is sending an email to the chefs based on the expired items that are in the fridge
    def test_send_expired_items(self, mock_generate_and_send_email, mock_generate_expired_items_email_body,
                                mock_get_cognito_user_email):
        # Creating example data
        ses_client = MagicMock()
        restaurant = {'pk': 'example_pk'}
        expired_items = ['item1', 'item2']

        # Setting up the mock behaviour
        mock_get_cognito_user_email.return_value = 'user@example.com'
        mock_generate_expired_items_email_body.return_value = 'example_body'

        # Running the function with the mock data and parameters
        send_expired_items(ses_client, restaurant, expired_items)

        # This assertion is for passing the test, ensureing its all called once with the requested parameters
        mock_get_cognito_user_email.assert_called_once_with('example_pk')
        mock_generate_expired_items_email_body.assert_called_once_with(restaurant, expired_items)
        mock_generate_and_send_email.assert_called_once_with(
            ses_client,
            'Food has expired with your fridge',
            'example_body',
            ['user@example.com'],
            'no-reply@ffsmart.benlewisjones.com'
        )




# This is testing the cognito emails to the user with mocked data and responses
class TestGetCognitoUserEmail(unittest.TestCase):
    # Patching the mocked resources
    @patch('src.utils.boto3.client')
    def test_get_cognito_user_email(self, mock_boto3_client):
        mock_cognito_client = MagicMock()
        mock_boto3_client.return_value = mock_cognito_client

        # Creating the mocked test data
        username = 'test_user'
        user_attributes = [{'Name': 'email', 'Value': 'user@example.com'}]

        # Accessing the environment variables called User Pool ID which is used for AWS Congnito testing
        os.environ['USER_POOL_ID'] = 'your_user_pool_id'

        mock_cognito_client.admin_get_user.return_value = {'UserAttributes': user_attributes}

        # This is running the function along with the username test data
        result = get_cognito_user_email(username)

        # This is used to interact with AWS Cognito, this checks whether he boto client was called exactly once ensuring that its created for Cognito Identity provider
        mock_boto3_client.assert_called_once_with('cognito-idp')
        # This is the mock object retriving information about the user
        mock_cognito_client.admin_get_user.assert_called_once_with(UserPoolId='your_user_pool_id', Username='test_user')

        # Deleting the environment variable
        del os.environ['USER_POOL_ID']

        # Test will pass if result equals the test result
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
    # Test case is designed to verify that create_an_order_token works correctly when the lambda function responds successfully.
    # '@patch' mock the make_lambda_request function. This prevents the actual function from being called and allows us to define a custom response for testing purposes.
    @patch('src.lambda_requests.make_lambda_request')
    # Function is called with a mock Lambda client
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
        # Test assertion ensures the reponse matches the mocked response
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
    # Test validates how create_an_order_token behaves with a failure
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
        #function called with parameters
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
    #  Test function to remove old tokens associated with orders from a restaurant system.
    @patch('src.lambda_requests.make_lambda_request')
    # mock object to the test function
    def test_remove_old_tokens_success(self, mock_make_lambda_request):
        # the mocked reponse represeting items that have been removed.
        mock_response = {
            'statusCode': 200,
            'body': {
                'objects_removed': [{'id_type': 'order', 'object_id': 'order_id_1'}, {'id_type': 'order', 'object_id': 'order_id_2'}]
            }
        }
        mock_make_lambda_request.return_value = mock_response

         #setting up parameters
        lambda_client = Mock()
        lambda_arn = 'your_lambda_arn'
        restaurant = {'pk': 'your_restaurant_id'}


        result = remove_old_tokens(lambda_client, lambda_arn, restaurant)
        #assertion to ensure thefunction call should be equal to the list of objects that were set up in the mock response
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
     # Test behavior of the remove_old_tokens function when it encounters a failure scenario
    def test_remove_old_tokens_failure(self, mock_make_lambda_request):
        mock_response = {
            'statusCode': 500,
            'body': 'Internal Server Error'
        }
        # Sets the mock object to return the mock_response when called. This simulates the scenario where the Lambda function encounters an error.
        mock_make_lambda_request.return_value = mock_response

        #test set up

        lambda_client = Mock()
        lambda_arn = 'your_lambda_arn'
        restaurant = {'pk': 'your_restaurant_id'}

        result = remove_old_tokens(lambda_client, lambda_arn, restaurant)

        # Assertion checks that the remove_old_tokens function returns an empty list when the lambda function fails.
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
    # This test checks whether the remove_old_objects function makes the correct API calls to the AWS lambda function for deleting old objects.
    def test_remove_old_objects(self, mock_make_lambda_request):
        mock_response = {
            'statusCode': 200
        }
        # test parameters
        mock_make_lambda_request.return_value = mock_response
        lambda_client = Mock()
        order_lambda_arn = 'your_order_lambda_arn'
        restaurant = {'pk': 'your_restaurant_id'}
        old_tokens = [{'id_type': 'order', 'object_id': 'order_id_1'}, {'id_type': 'order', 'object_id': 'order_id_2'}]
        #calling the test function
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
         # Assertion checks that the make_lambda_request function was called with the correct parameters for each order in old_tokens
        mock_make_lambda_request.assert_has_calls(expected_calls)
        
class TestCreateNewOrder(unittest.TestCase):
    @patch('src.lambda_requests.make_lambda_request')
    # Tests the create_new_order function to ensure it behaves as expected when it successfully creates a new order
    def test_create_new_order_success(self, mock_make_lambda_request):
        mock_response = {
            'statusCode': 200,
            'body': {
                'order_id': 'new_order_id'
            }
        }
        # Sets up necessary data  which are required to call the create_new_order function.
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
        #The test then asserts that the result returned by create_new_order matches the expected result
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




class TestGenerateDeliveryEmailBody(unittest.TestCase):
    # Explaination here for what the test is actually doing in general

    def test_generate_delivery_email_body(self):
        mock_restaurant_admin_settings = {
            'pk': 'restaurant_id',
            'restaurant_details': {
                'restaurant_name': 'Test Restaurant',
                'location': {
                    'city': 'City',
                    'postcode': '12345',
                    'street_address_1': 'Street 1',
                    'street_address_2': 'Street 2',
                    'street_address_3': 'Street 3'
                }
            }
        }
        mock_token = 'test_token'

        expected_email_body = f'''
                   Hello Driver,
    
    You have a delivery for {mock_restaurant_admin_settings['restaurant_details']['restaurant_name']}.
    
    Delivery link: http://0.0.0.0:80/delivery/{mock_restaurant_admin_settings['pk']}/{mock_token}
    
    Address:
    {mock_restaurant_admin_settings['restaurant_details']['location']['city']}
    {mock_restaurant_admin_settings['restaurant_details']['location']['postcode']}
    {mock_restaurant_admin_settings['restaurant_details']['location']['street_address_1']}
    {mock_restaurant_admin_settings['restaurant_details']['location']['street_address_2']}
    {mock_restaurant_admin_settings['restaurant_details']['location']['street_address_3']}
    
    Good luck!
    This link will self-destruct in 3 days.
               '''

        result = generate_delivery_email_body(mock_restaurant_admin_settings, mock_token)

        self.assertEqual(result.strip(), expected_email_body.strip())


class TestGenerateExpiredItemsEmailBody(unittest.TestCase):
    # Explaination here for what the test is actually doing in general

    def test_generate_expired_items_email_body(self):
        mock_restaurant_admin_settings = {
            'restaurant_details': {
                'restaurant_name': 'Test Restaurant',
                'location': {
                    'city': 'City',
                    'postcode': '12345',
                    'street_address_1': 'Street 1',
                    'street_address_2': 'Street 2',
                    'street_address_3': 'Street 3'
                }
            }
        }
        mock_expired_items = [
            {'item_name': 'Expired Item 1', 'quantity': 5},
            {'item_name': 'Expired Item 2', 'quantity': 10}
        ]

        result = generate_expired_items_email_body(mock_restaurant_admin_settings, mock_expired_items)

        expected_email_body = ('Hello Test Restaurant,\n'
                               '    \n'
                               '    The following items have expired:\n'
                               '    Expired Item 1: 5\r'
                               '\tExpired Item 2: 10\r'
                               '\t\n'
                               '    \n'
                               '    This has been reported as a part of your health report.\n'
                               '    \n'
                               '    Thanks')

        self.assertEqual(result.strip(), expected_email_body.strip())

class TestMakeLambdaRequest(unittest.TestCase):

    @patch('src.utils.json.dumps')
    def test_make_lambda_request(self, mock_json_dumps):
        # Set up mock objects
        mock_lambda_client = Mock()
        mock_response = {
            'Payload': Mock(read=Mock(return_value=b'{"key": "value"}'))
        }
        mock_lambda_client.invoke.return_value = mock_response
        mock_json_dumps.return_value = '{"test": "data"}'


        test_payload = {'test': 'data'}
        test_function_name = 'testFunction'


        response = make_lambda_request(mock_lambda_client, test_payload, test_function_name)


        mock_lambda_client.invoke.assert_called_once_with(
            FunctionName='testFunction',
            InvocationType='RequestResponse',
            Payload='{"test": "data"}'
        )
        mock_json_dumps.assert_called_once_with(test_payload)
        self.assertEqual(response, {'key': 'value'})

class TestGenerateAndSendEmail(unittest.TestCase):

    @patch('src.utils.boto3.client')
    def test_generate_and_send_email_success(self, mock_boto3_client):
        mock_ses_client = Mock()
        mock_ses_client.send_email.return_value = {'MessageId': '12345'}
        mock_boto3_client.return_value = mock_ses_client

        # Define test data
        subject = 'Test Subject'
        body = 'Test Body'
        destinations = ['test@example.com']
        sender = 'sender@example.com'

        result = generate_and_send_email(mock_ses_client, subject, body, destinations, sender)

        self.assertTrue(result)

        mock_ses_client.send_email.assert_called_once_with(
            Destination={'ToAddresses': destinations},
            Message={
                'Body': {'Text': {'Charset': 'UTF-8', 'Data': body}},
                'Subject': {'Charset': 'UTF-8', 'Data': subject}
            },
            Source=sender
        )

    @patch('src.utils.boto3.client')
    def test_generate_and_send_email_failure(self, mock_boto3_client):
        mock_ses_client = Mock()
        error_response = {'Error': {'Code': 'TestException', 'Message': 'Test Message'}}
        mock_ses_client.send_email.side_effect = ClientError(error_response, 'send_email')
        mock_boto3_client.return_value = mock_ses_client

        result = generate_and_send_email(mock_ses_client, 'subject', 'body', ['test@example.com'], 'sender@example.com')

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()