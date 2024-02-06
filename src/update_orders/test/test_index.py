import unittest
import os
from unittest import mock
from unittest.mock import patch, MagicMock, Mock
from .src.emails import send_delivery_email, send_expired_items
from .src.utils import get_cognito_user_email, list_of_all_pks_and_delivery_emails, generate_delivery_email_body, generate_expired_items_email_body, make_lambda_request, generate_and_send_email,ClientError
from .src.lambda_requests import create_an_order_token, remove_old_tokens, remove_old_objects, create_new_order
from unittest.mock import patch



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
    @patch('boto3.client')
    @patch('src.emails.generate_expired_items_email_body')
    @patch('src.emails.generate_and_send_email')
    # This is testing sending the email whe an item has expired
    def test_send_expired_items(self, mock_generate_and_send_email, mock_generate_expired_items_email_body,
                                mock_boto3_client):
        # This is mocking a SES client which is Amazons Simple email service
        ses_client = MagicMock()

        # This is mocking the behaviour of the boto resource to return the client
        mock_boto3_client.return_value = ses_client

        # This is a mock of an email body we can use
        mock_generate_expired_items_email_body.return_value = 'example_body'

        # This is the test data we will be using
        restaurant = {'pk': 'example_pk'}
        emails = ['user@example.com']
        expires_items = ['item1', 'item2']
        going_to_expire_items = ['item3', 'item4']

        # Running the function with our test data and information
        send_expired_items(ses_client, restaurant, emails, expires_items, going_to_expire_items)

        # Assertions that will need to pass before the test is passed
        mock_generate_expired_items_email_body.assert_called_once_with(restaurant, expires_items, going_to_expire_items)
        mock_generate_and_send_email.assert_called_once_with(
            ses_client,
            'Food expiration in your fridge',
            'example_body',
            emails,
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
    # This function tests getting a user but if theres no email information
    def test_get_cognito_user_email_no_email_attribute(self, mock_boto3_client):
        # Mocking a cognito client
        mock_cognito_client = MagicMock()
        mock_boto3_client.return_value = mock_cognito_client

        # Test information we can use
        username = 'test_user'
        user_attributes = [{'Name': 'some_other_attribute', 'Value': 'some_value'}]

        # Accessing the environment variables called User Pool ID which is used for AWS Congnito testing
        os.environ['USER_POOL_ID'] = 'your_user_pool_id'

        mock_cognito_client.admin_get_user.return_value = {'UserAttributes': user_attributes}

        # This is running the function along with the username test data
        result = get_cognito_user_email(username)

        # This is used to interact with AWS Cognito, this checks whether he boto client was called exactly once ensuring that its created for Cognito Identity provider
        mock_boto3_client.assert_called_once_with('cognito-idp')
        mock_cognito_client.admin_get_user.assert_called_once_with(UserPoolId='your_user_pool_id', Username='test_user')

        # Deleting the environment variable
        del os.environ['USER_POOL_ID']

        # This will only pass if it returns our test username
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
    # Tests the create_new_order function to ensure it behaves as expected when it successfully creates a new order.
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



# This is testing the function which generates the delivery email
class TestGenerateDeliveryEmailBody(unittest.TestCase):
    # This function is testing the body of the email
    def test_generate_delivery_email_body(self):
        # This is mocoking a test resturant
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

        # This is the expected response from the email
        expected_email_body = f'''
                   Hello Driver,
    
    You have a delivery for {mock_restaurant_admin_settings['restaurant_details']['restaurant_name']}.
    
    Delivery link: http://FfSmar-Analy-3HyxSmNqsx3Z-1763585782.eu-west-1.elb.amazonaws.com/delivery/{mock_restaurant_admin_settings['pk']}/{mock_token}
    
    Address:
    {mock_restaurant_admin_settings['restaurant_details']['location']['city']}
    {mock_restaurant_admin_settings['restaurant_details']['location']['postcode']}
    {mock_restaurant_admin_settings['restaurant_details']['location']['street_address_1']}
    {mock_restaurant_admin_settings['restaurant_details']['location']['street_address_2']}
    {mock_restaurant_admin_settings['restaurant_details']['location']['street_address_3']}
    
    Good luck!
    This link will self-destruct in 3 days.
               '''
        # This is running the function with our mocked information and token
        result = generate_delivery_email_body(mock_restaurant_admin_settings, mock_token)

        # This will pass if the expected result is the same as whats generated
        self.assertEqual(result.strip(), expected_email_body.strip())

# This is testing the generating of an email if the items are expired
class TestGenerateExpiredItemsEmailBody(unittest.TestCase):
    def test_generate_expired_items_email_body(self):
        # This is the test data that we will be using
        restaurant_admin_settings = {
            'restaurant_details': {
                'restaurant_name': 'Test Restaurant'
            }
        }
        # This is mocked expired items
        expired_items = [{'item_name': 'Expired Item 1', 'quantity': 2}]
        going_to_expire_items = [{'item_name': 'Expiring Item 1', 'quantity': 3}]

        # This is running the data with the test items we have created
        result = generate_expired_items_email_body(restaurant_admin_settings, expired_items, going_to_expire_items)

        # expected result that the email will say
        expected_result = """
        Hello Test Restaurant,
    
    The following items have expired:
    Expired Item 1: 2\r\t
    
    The following items are about to expire:
    Expiring Item 1: 3\r\t
    
    This has been reported as a part of your health report.
    
    Thanks
        """
        # This will pass if the expected email is matching the actual result
        self.assertEqual(result.strip(), expected_result.strip())

class TestMakeLambdaRequest(unittest.TestCase):
    #this test is for the MakeLambda request
    # the line below is used to mock the json dumps function.

    @patch('src.utils.json.dumps')
    def test_make_lambda_request(self, mock_json_dumps):
        # Set up mock objects
        mock_lambda_client = Mock()
        mock_response = {
            'Payload': Mock(read=Mock(return_value=b'{"key": "value"}'))
        }
        mock_lambda_client.invoke.return_value = mock_response
        mock_json_dumps.return_value = '{"test": "data"}'

        # tests the function and the payload 
        test_payload = {'test': 'data'}
        test_function_name = 'testFunction'


        response = make_lambda_request(mock_lambda_client, test_payload, test_function_name)
        #ensures the test is called with the expected parameters 

        mock_lambda_client.invoke.assert_called_once_with(
            FunctionName='testFunction',
            InvocationType='RequestResponse',
            Payload='{"test": "data"}'
        )
        # asserts that the response from make_lambda_request matches the expected response
        mock_json_dumps.assert_called_once_with(test_payload)
        self.assertEqual(response, {'key': 'value'})

class TestGenerateAndSendEmail(unittest.TestCase):
#test the GenerateAndSendEmail function to ensure it performs as expected 
    @patch('src.utils.boto3.client')
    #test is used to check whether the GenerateAndSendEmail function performs is successfully
    def test_generate_and_send_email_success(self, mock_boto3_client):
        #mock set up for boto3 
        mock_ses_client = Mock()
        mock_ses_client.send_email.return_value = {'MessageId': '12345'}
        mock_boto3_client.return_value = mock_ses_client

        # test data that is used
        subject = 'Test Subject'
        body = 'Test Body'
        destinations = ['test@example.com']
        sender = 'sender@example.com'

        result = generate_and_send_email(mock_ses_client, subject, body, destinations, sender)

        self.assertTrue(result)
         #ensures the function returns the expected values to determine if it's a success 
        mock_ses_client.send_email.assert_called_once_with(
            Destination={'ToAddresses': destinations},
            Message={
                'Body': {'Text': {'Charset': 'UTF-8', 'Data': body}},
                'Subject': {'Charset': 'UTF-8', 'Data': subject}
            },
            Source=sender
        )
     #test for checking whether there is error handling in place to deal with a failure for generate_and_send_email
    @patch('src.utils.boto3.client')
    def test_generate_and_send_email_failure(self, mock_boto3_client):
        #mock set up for boto3 
        mock_ses_client = Mock()
        #test data used for the mock scenario
        error_response = {'Error': {'Code': 'TestException', 'Message': 'Test Message'}}
        mock_ses_client.send_email.side_effect = ClientError(error_response, 'send_email')
        mock_boto3_client.return_value = mock_ses_client

        #some fields are missing on purpose to ensure the error handling is in place to deal with missing data and parameters.
        result = generate_and_send_email(mock_ses_client, 'subject', 'body', ['test@example.com'], 'sender@example.com')

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()