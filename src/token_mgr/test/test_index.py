import unittest
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
from src.index import handler
from src.post import validate_token
from src.patch import set_token
from src.custom_exceptions import BadRequestException
from src.delete import delete_token, clean_up_old_tokens
from ..src.index import handler


class TestDynamoDBHandler(unittest.TestCase):
    @patch('boto3.resource')
    def test_handler_function(self, mock_boto3_resource):  # use highly descriptive function names, not what like this
        """Basic functionality test"""
        # Mock boto3 setup
        mock_dynamodb_resource = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb_resource

        # Mock dynamodb resource
        mock_dynamodb_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.query.return_value = {'Items': []}

        # Handler inputs
        mock_event = {
            'data': 'example data',
            'pk': 'test_pk',
            'type': 'test_type'
        }
        mock_context = {}

        response = handler(mock_event, mock_context)

        # Assert functions are called correctly
        mock_dynamodb_table.put_item.assert_called_with(Item={
            'pk': 'test_pk',
            'type': 'test_type',
            'data': 'example data'
        })

        # Define the expected response
        expected_response = {
            'statusCode': 200,
            'body': {
                'details': 'function works',
                'db_response': []
            }
        }

        # Assert the response
        self.assertEqual(response, expected_response)

    @patch('boto3.resource')
    def test_handler_query_exception_handling(self, mock_boto3_resource):
        """Test the handler function for handling DynamoDB query exception"""

        mock_dynamodb_resource = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb_resource

        mock_dynamodb_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.query.side_effect = Exception("Query error occurred")

        mock_event = {
            'data': 'example data',
            'pk': 'test_pk',
            'type': 'test_type'
        }
        mock_context = {}

        response = handler(mock_event, mock_context)

        mock_dynamodb_table.put_item.assert_called_with(Item={
            'pk': 'test_pk',
            'type': 'test_type',
            'data': 'example data'
        })

        expected_exception_response = {
            'statusCode': 500,
            'body': {
                'details': 'Query error occurred'
            }
        }

        self.assertEqual(response, expected_exception_response)


# Testing the validate token function with mocked test data
class TestValidateTokenLambda(unittest.TestCase):
    # This is the data we'll be using for this test
    def setUp(self):
        self.event = {
            'body': {
                'restaurant_id': 'example_restaurant',
                'request_token': 'example_token'
            }
        }
        self.table = MagicMock()

    # This is the response we want to use against the dynamoDB
    def test_valid_token(self):
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'tokens',
                'tokens': [
                    {'token': 'example_token', 'expiry_date': 9999999999, 'object_id': 'example_id',
                     'id_type': 'example_type'}
                ]
            }
        }

        # Running the function against the mocked information
        response = validate_token(self.event, self.table)

        # The test will pass if the status code is 200 'success' with the information in the body
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body']['object_id'], 'example_id')
        self.assertEqual(response['body']['id_type'], 'example_type')

    # This is testing what occurs when a token has expired against a resturant
    def test_expired_token(self):
        # Mocked data we'll be running against our mocked db
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'tokens',
                'tokens': [
                    {'token': 'example_token', 'expiry_date': 1, 'object_id': 'example_id', 'id_type': 'example_type'}
                ]
            }
        }

        # Running the validate token with our mocked data
        response = validate_token(self.event, self.table)

        # Test will pass if the response code is a 401 and the body shows the correct error
        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Invalid token', response['body'])

    # Testing what happens if a token is invalid
    def test_invalid_token(self):
        # Test data with an invalid ID
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'tokens',
                'tokens': [
                    {'token': 'another_token', 'expiry_date': 9999999999, 'object_id': 'example_id',
                     'id_type': 'example_type'}
                ]
            }
        }

        # Running the function against the test information
        response = validate_token(self.event, self.table)

        # The test will pass if the status code is a 401 and a error is shown to the user
        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Invalid token', response['body'])


class TestSetTokenFunction(unittest.TestCase):
    # test that function works with expected parameters
    def test_set_token_with_expected_parameters(self):
        event = {'body': {'restaurant_id': 'example_restaurant', 'id_type': 'order', 'object_id': 'example_id'}}
        self.table = MagicMock()
        self.table.get_item.return_value = {'Item': {'pk': 'example_restaurant', 'type': 'tokens', 'tokens':
            [{'token': 'another_token', 'expiry_date': 9999999999, 'object_id': 'example_id', 'id_type': 'example_type'}]}}

        response = set_token(event, self.table)

        self.assertEqual(response['statusCode'], 200)

    # test that function returns error message when given invalid parameters
    def test_invalid_event_format(self):
        event = {'example': 'example'}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            set_token(event, self.table)
        self.assertEqual(str(context.exception), 'No request body exists.')

class TestDeleteToken(unittest.TestCase):
    # The purpose of the test is to view the behaviour of the delete token function in different scenarios.
    #The test method is created by mocking an object that represents the dynamodb table. also creating a valid request event.
    def setUp(self):
        self.table = Mock()
        self.valid_event = {
            'body': {
                'restaurant_id': 'restaurant123',
                'request_token': 'token123'
            }
        }
        self.invalid_event = {
            'body': {}
        }

    # This method is designed to verify the successful deletion of a token
    def test_delete_token_success(self):
        # Mocking DynamoDB response that returns a response that includes a token when the get item method is called.
        self.table.get_item.return_value = {'Item': {'tokens': [{'token': 'token123', 'object_id': 'obj1', 'id_type': 'type1'}]}}
        response = delete_token(self.valid_event, self.table)
        self.assertEqual(response['statusCode'], 200)

    # This test method checks the function's behavior when the token is not found in the database
    def test_delete_token_not_found(self):
    # Sets up a mock response for the get item method of the self table object. The self table object is a mock object that simulates the behavior of a DynamoDB table.
        self.table.get_item.return_value = {'Item': {'tokens': []}}
        #The two arguments
        response = delete_token(self.valid_event, self.table)
        self.assertEqual(response['statusCode'], 404)


class TestCleanUpOldTokens(unittest.TestCase):
    # The purpose of the test is to view the behaviour of the clean up old token function in different scenarios.
    # The set up we will be using a mock object to represent the dynamodb table and valid request events.
    def setUp(self):
        self.table = Mock()
        self.valid_event = {
            'body': {
                'restaurant_id': 'restaurant123'
            }
        }
        self.invalid_event = {
            'body': {}
        }

    # This test method checks the functionality of clean_up_old_tokens when it successfully processes a token
    def test_clean_up_old_tokens_success(self):
        # Mocking DynamoDB response that returns a token response when the get item method is called.
        self.table.get_item.return_value = {'Item': {'tokens': [{'expiry_date': 1643086920, 'object_id': 'obj1', 'id_type': 'type1'}]}}
        response = clean_up_old_tokens(self.valid_event, self.table)
        # The test will use status code 200 to ensure if the test is a success
        self.assertEqual(response['statusCode'], 200)

    #This test method checks the behavior of clean_up_old_tokens when no tokens are found.
    def test_clean_up_old_tokens_not_found(self):
    #Mocking the DynamoDB response to return an empty result set.
        self.table.get_item.return_value = {}
        response = clean_up_old_tokens(self.valid_event, self.table)
        # Response is 404 showsthat no relevant data was found.
        self.assertEqual(response['statusCode'], 404)


if __name__ == '__main__':
    unittest.main()
