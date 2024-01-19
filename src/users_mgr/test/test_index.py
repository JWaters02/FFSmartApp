import unittest
from unittest.mock import patch, MagicMock
from src.index import handler
from src.get import get_all_users, BadRequestException, get_user
from src.post import create_new_restaurant_dynamodb_entries, BadRequestException
from src.delete import delete_user
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
    def test_get_all_users_internal_error(self, mock_boto3_resource):
        # Mock event and table
        mock_event = {'body': {'restaurant_id': 'house'}}
        mock_table = MagicMock()

        # Mock DynamoDB response for internal error
        mock_table.query.side_effect = ClientError(
            error_response={'Error': {'Code': 'InternalError', 'Message': 'Unknown error'}},
            operation_name='operation_name'
        )

        # Call the function
        result = get_all_users(mock_event, mock_table)

        # Assert that the function returns the expected response for an internal error
        expected_result = {
            'statusCode': 500,
            'body': 'Error accessing DynamoDB: An error occurred (InternalError) when calling the operation_name operation: Unknown error'
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
class TestGetUserFunction(unittest.TestCase):

    @patch('boto3.resource')  # Replace 'your_module' with the actual module name
    @patch('botocore.exceptions.ClientError')
    def test_get_user_success(self, key_mock, client_error_mock):
        # Mocking the DynamoDB table response
        table_mock = MagicMock()
        table_mock.query.return_value = {
            'Items': [
                {'users': [{'username': 'john_doe', 'other_field': 'value'}]}
            ]
        }

        # Creating a sample event
        event = {'body': {'restaurant_id': 'example_restaurant', 'username': 'john_doe'}}

        # Calling the function
        result = get_user(event, table_mock)

        # Asserting the result
        expected_result = {'statusCode': 200, 'body': {'username': 'john_doe', 'other_field': 'value'}}
        self.assertEqual(result, expected_result)

    @patch('boto3.resource')  # Replace 'your_module' with the actual module name
    @patch('botocore.exceptions.ClientError')
    def test_get_user_not_found(self, key_mock, client_error_mock):
        # Mocking the DynamoDB table response with no items
        table_mock = MagicMock()
        table_mock.query.return_value = {'Items': []}

        # Creating a sample event
        event = {'body': {'restaurant_id': 'example_restaurant', 'username': 'nonexistent_user'}}

        # Calling the function
        result = get_user(event, table_mock)

        # Asserting the result
        expected_result = {'statusCode': 404, 'body': 'User not found.'}
        self.assertEqual(result, expected_result)

    @patch('boto3.resource')  # Replace 'your_module' with the actual module name
    def test_get_user_bad_request_missing_restaurant_id(self, key_mock):
        # Creating a sample event with missing restaurant_id
        event = {'body': {'username': 'john_doe'}}

        # Calling the function and expecting a BadRequestException
        with self.assertRaises(BadRequestException):
            get_user(event, MagicMock())

    @patch('boto3.resource')  # Replace 'your_module' with the actual module name
    def test_get_user_bad_request_missing_username(self, key_mock):
        # Creating a sample event with missing username
        event = {'body': {'restaurant_id': 'example_restaurant'}}

        # Calling the function and expecting a BadRequestException
        with self.assertRaises(BadRequestException):
            get_user(event, MagicMock())

    @patch('boto3.resource')  # Replace 'your_module' with the actual module name
    @patch('botocore.exceptions.ClientError')
    def test_get_user_not_found(self, key_mock, client_error_mock):
        # Mocking the DynamoDB table response with no items
        table_mock = MagicMock()
        table_mock.query.return_value = {'Items': []}

        # Creating a sample event
        event = {'body': {'restaurant_id': 'example_restaurant', 'username': 'nonexistent_user'}}

        # Calling the function
        result = get_user(event, table_mock)

        # Asserting the result
        expected_result = {'statusCode': 404, 'body': 'User not found.'}
        self.assertEqual(result, expected_result)











class TestCreateNewRestaurantDynamoDBEntries(unittest.TestCase):

    @patch('boto3.client')  # Replace 'your_module' with the actual module name
    def test_create_new_restaurant_success(self, client_mock):
        # Mocking DynamoDB client
        dynamodb_client_mock = client_mock.return_value

        # Mocking DynamoDB transact_write_items
        dynamodb_client_mock.transact_write_items.return_value = {}

        # Creating a sample event
        event = {'body': {'restaurant_name': 'new_restaurant'}}

        # Calling the function
        result = create_new_restaurant_dynamodb_entries(dynamodb_client_mock, event, 'FfSmartAppTheOneWeAreWorkingOnStackAnalysisAndDesignStorageStackC668B19C-analysisanddesigncourseworkmasterdynamodbtable3462106D-1IU8LQL1LND18')

        # Asserting the result
        expected_result = {'statusCode': 200}
        self.assertEqual(result, expected_result)

    @patch('boto3.client')  # Replace 'your_module' with the actual module name
    def test_create_new_restaurant_conflict(self, client_mock):
        # Mocking DynamoDB client
        dynamodb_client_mock = client_mock.return_value

        # Mocking DynamoDB transact_write_items with ConditionalCheckFailedException
        dynamodb_client_mock.transact_write_items.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'TransactionCanceledException',
                    'Message': 'The conditional request failed',
                    'CancellationReasons': [
                        {
                            'Code': 'ConditionalCheckFailed',
                            'Message': 'The conditional request failed'
                        }
                    ]
                }
            },
            'transact_write_items'
        )

        # Creating a sample event
        event = {'body': {'restaurant_name': 'existing_restaurant'}}

        try:
            # Calling the function
            create_new_restaurant_dynamodb_entries(
                dynamodb_client_mock,
                event,
                'FfSmartAppTheOneWeAreWorkingOnStackAnalysisAndDesignStorageStackC668B19C-analysisanddesigncourseworkmasterdynamodbtable3462106D-1IU8LQL1LND18'
            )
        except Exception as e:
            # Asserting that the caught exception is an instance of ClientError
            self.assertIsInstance(e, ClientError)
            # Further assertions on the exception if needed
            self.assertEqual(e.response['Error']['Code'], 'TransactionCanceledException')
            self.assertEqual(e.response['Error']['Message'], 'The conditional request failed')
            self.assertEqual(e.response['ResponseMetadata']['HTTPStatusCode'], 500)








class TestDeleteUserLambda(unittest.TestCase):

    def setUp(self):
        self.event = {
            'body': {
                'restaurant_id': 'example_restaurant',
                'username': 'example_user'
            }
        }
        self.table = MagicMock()

    def test_delete_user_successful(self):
        # Mocking DynamoDB response
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'users',
                'users': [{'username': 'existing_user'}, {'username': 'example_user'}]
            }
        }

        response = delete_user(self.event, self.table)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(self.table.update_item.call_count, 1)

    def test_delete_user_not_found(self):
        # Mocking DynamoDB response for non-existent restaurant
        self.table.get_item.return_value = {}

        response = delete_user(self.event, self.table)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Restaurant does not exist', response['body'])

    def test_delete_user_dynamodb_error(self):
        # Mocking DynamoDB ClientError
        self.table.get_item.side_effect = ClientError({'Error': {'Code': 'TestException'}}, 'operation_name')

        response = delete_user(self.event, self.table)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error accessing DynamoDB', response['body'])


if __name__ == '__main__':
    unittest.main()