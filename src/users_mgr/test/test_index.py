import unittest
from unittest.mock import patch, MagicMock
from src.index import handler
from src.get import get_all_users, BadRequestException
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


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
        """Test the handler function for handling DynamoDB query exceptions"""

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


class TestGetAllUsers(unittest.TestCase):

    @patch('boto3.resource')
    def test_get_all_users_success(self, mock_boto3_resource):
        # Mock event and table
        mock_event = {'body': {'restaurant_id': 'mock_restaurant_id'}}
        mock_table = MagicMock()

        # Mock DynamoDB response
        mock_table.query.return_value = {'Items': [{'users': ['user1', 'user2']}]}

        # Call the function
        result = get_all_users(mock_event, mock_table)

        # Assert that the function behaves as expected
        expected_result = {
            'statusCode': 200,
            'body': {
                'items': ['user1', 'user2']
            }
        }
        self.assertEqual(result, expected_result)

        # Optionally, assert that DynamoDB query method was called with the expected parameters
        mock_table.query.assert_called_once_with(
            KeyConditionExpression=Key('pk').eq('mock_restaurant_id') & Key('type').eq('users')
        )

    @patch('boto3.resource')
    def test_get_all_users_not_found(self, mock_boto3_resource):
        # Mock event and table
        mock_event = {'body': {'restaurant_id': 'nonexistent'}}
        mock_table = MagicMock()

        # Mock DynamoDB response for user not found
        mock_table.query.return_value = {'Items': []}

        # Call the function
        result = get_all_users(mock_event, mock_table)

        # Assert the function behaves as expected
        expected_result = {
            'statusCode': 404,
            'body': 'User not found.'
        }
        self.assertEqual(result, expected_result)

    @patch('boto3.resource')
    def test_get_all_users_bad_request(self, mock_boto3_resource):
        # Mock event and table with missing 'restaurant_id' in 'body'
        mock_event = {'body': {}}
        mock_table = MagicMock()

        # Call the function and expect a BadRequestException
        with self.assertRaises(BadRequestException):
            get_all_users(mock_event, mock_table)

    @patch('boto3.resource')
    def test_get_all_users_internal_error(self, mock_boto3_resource):
        # Mock event and table
        mock_event = {'body': {'restaurant_id': 'house'}}
        mock_table = MagicMock()

        # Mock DynamoDB response for internal error
        mock_table.side_effect = Exception("An error occurred (InternalError) while calling the operation_name operation: Unknown error")

        # Call the function
        result = get_all_users(mock_event, mock_table)

        # Assert the function behaves as expected
        expected_result = {
            'statusCode': 500,
            'body': 'Error accessing DynamoDB: An error occurred (InternalError) while calling the operation_name operation: Unknown error'
        }
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()