import unittest
from unittest.mock import patch, MagicMock
from unittest.mock import Mock
from src.index import handler
from src.post import validate_token
from src.patch import set_token
from src.custom_exceptions import BadRequestException
from src.delete import delete_token, clean_up_old_tokens


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
    # Explaination here for what the test is actually doing in general
    def setUp(self):
        self.event = {
            'body': {
                'restaurant_id': 'example_restaurant',
                'request_token': 'example_token'
            }
        }
        self.table = MagicMock()

    # Explaination here for what the test is actually doing in general
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

        response = validate_token(self.event, self.table)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body']['object_id'], 'example_id')
        self.assertEqual(response['body']['id_type'], 'example_type')

    # Explaination here for what the test is actually doing in general
    def test_expired_token(self):
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

    # Explaination here for what the test is actually doing in general
    def test_invalid_token(self):
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
    # Explaination here for what the test is actually doing in general
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

    # Explaination here for what the test is actually doing in general
    def test_delete_token_success(self):
        # Mocking DynamoDB response
        self.table.get_item.return_value = {'Item': {'tokens': [{'token': 'token123', 'object_id': 'obj1', 'id_type': 'type1'}]}}
        response = delete_token(self.valid_event, self.table)
        self.assertEqual(response['statusCode'], 200)

    # Explaination here for what the test is actually doing in general
    def test_delete_token_not_found(self):
        self.table.get_item.return_value = {'Item': {'tokens': []}}
        response = delete_token(self.valid_event, self.table)
        self.assertEqual(response['statusCode'], 404)


class TestCleanUpOldTokens(unittest.TestCase):
    # Explaination here for what the test is actually doing in general
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

    # Explaination here for what the test is actually doing in general
    def test_clean_up_old_tokens_success(self):
        # Mocking DynamoDB response
        self.table.get_item.return_value = {'Item': {'tokens': [{'expiry_date': 1643086920, 'object_id': 'obj1', 'id_type': 'type1'}]}}
        response = clean_up_old_tokens(self.valid_event, self.table)
        self.assertEqual(response['statusCode'], 200)

    # Explaination here for what the test is actually doing in general
    def test_clean_up_old_tokens_not_found(self):
        self.table.get_item.return_value = {}
        response = clean_up_old_tokens(self.valid_event, self.table)
        self.assertEqual(response['statusCode'], 404)


if __name__ == '__main__':
    unittest.main()
