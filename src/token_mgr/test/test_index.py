import unittest
from unittest.mock import patch, MagicMock
from src.index import handler
from src.post import validate_token
from src.patch import set_token
from src.custom_exceptions import BadRequestException


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


class TestValidateTokenLambda(unittest.TestCase):

    def setUp(self):
        self.event = {
            'body': {
                'restaurant_id': 'example_restaurant',
                'request_token': 'example_token'
            }
        }
        self.table = MagicMock()

    def test_valid_token(self):
        # Mocking DynamoDB response with a valid token that has not expired
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

        response = validate_token(self.event, self.table)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body']['object_id'], 'example_id')
        self.assertEqual(response['body']['id_type'], 'example_type')

    def test_expired_token(self):
        # Mocking DynamoDB response with an expired token
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'tokens',
                'tokens': [
                    {'token': 'example_token', 'expiry_date': 1, 'object_id': 'example_id', 'id_type': 'example_type'}
                ]
            }
        }

        response = validate_token(self.event, self.table)

        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Invalid token', response['body'])

    def test_invalid_token(self):
        # Mocking DynamoDB response with no matching token
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

        response = validate_token(self.event, self.table)

        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Invalid token', response['body'])


class TestSetTokenFunction(unittest.TestCase):
    def test_set_token_with_expected_parameters(self):
        event = {'body': {'restaurant_id': 'example_restaurant', 'id_type': 'order', 'object_id': 'example_id'}}
        self.table = MagicMock()
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

        response = set_token(event, self.table)

        self.assertEqual(response['statusCode'], 200)

    def test_invalid_event_format(self):
        event = {'example': 'example'}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            set_token(event, self.table)
        self.assertEqual(str(context.exception), 'No request body exists.')


if __name__ == '__main__':
    unittest.main()
