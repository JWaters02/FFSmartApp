import unittest
from unittest.mock import patch, MagicMock
from src.get import get_all_users, BadRequestException, get_user
from src.post import create_new_restaurant_dynamodb_entries, BadRequestException
from src.delete import delete_user
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key




#This class is testing the function get all users
class TestGetAllUsers(unittest.TestCase):

    # Replacing the boto resource function with a mock object
    @patch('boto3.resource')
    #Testing the response if the application cannot find all users
    def test_get_all_users_not_found(self, mock_boto3_resource):
        #Creating the mock data and tables
        mock_event = {'body': {'restaurant_id': 'nonexistent'}}
        mock_table = MagicMock()
        # Filling the tables with void data
        mock_table.query.return_value = {'Items': []}
        #Running the function with our mock data
        result = get_all_users(mock_event, mock_table)
        #Expectation when a user is not found
        expected_result = {
            'statusCode': 404,
            'body': 'User not found.'
        }
        #this will test the output with an actual and expected result
        self.assertEqual(result, expected_result)

    # Replacing the boto resource function with a mock object
    @patch('boto3.resource')
    #Testing the response if the application has an internal error whilst testing the function
    def test_get_all_users_internal_error(self, mock_boto3_resource):
        #Creating the mock data and tables
        mock_event = {'body': {'restaurant_id': 'house'}}
        mock_table = MagicMock()

        #When the query method is called it will raise a client error
        mock_table.query.side_effect = ClientError(
            error_response={'Error': {'Code': 'InternalError', 'Message': 'Unknown error'}},
            operation_name='operation_name'
        )
        #Running the function with our mock data
        result = get_all_users(mock_event, mock_table)
        #Expectation when an internal error occurs
        expected_result = {
            'statusCode': 500,
            'body': 'Error accessing DynamoDB: An error occurred (InternalError) when calling the operation_name operation: Unknown error'
        }
        #this will test the output with an actual and expected result
        self.assertEqual(result, expected_result)

    # Replacing the boto resource function with a mock object
    @patch('boto3.resource')
    #Testing the function if the request is an empty body
    def test_get_all_users_bad_request(self, mock_boto3_resource):
        #Creating the mock data and tables
        mock_event = {'body': {}}
        mock_table = MagicMock()

        #Creating the assertion and running the get all users function
        with self.assertRaises(BadRequestException):
            get_all_users(mock_event, mock_table)

#This class is now testing the get_user function
class TestGetUserFunction(unittest.TestCase):
    # Replacing the boto resource function with a mock object
    @patch('boto3.resource')
    @patch('botocore.exceptions.ClientError')
    # Testing the function when the function finds a user and returns a success status
    def test_get_user_success(self, key_mock, client_error_mock):
        #Creating the mock data and tables
        table_mock = MagicMock()
        table_mock.query.return_value = {
            'Items': [
                {'users': [{'username': 'john_doe', 'other_field': 'value'}]}
            ]
        }
        #Creating the mock event which is what will be ran against the function
        event = {'body': {'restaurant_id': 'example_restaurant', 'username': 'john_doe'}}

        #Running the function
        result = get_user(event, table_mock)

        #Creating the mock event which is what will be ran against the function
        expected_result = {'statusCode': 200, 'body': {'username': 'john_doe', 'other_field': 'value'}}
        self.assertEqual(result, expected_result)

    # Replacing the boto resource function with a mock object
    @patch('boto3.resource')
    @patch('botocore.exceptions.ClientError')
    #Testing the response if the application cannot find the specific user
    def test_get_user_not_found(self, key_mock, client_error_mock):
        #Creating the mock data and tables
        table_mock = MagicMock()
        table_mock.query.return_value = {'Items': []}

        #This is the dummy data what will be ran against the function
        event = {'body': {'restaurant_id': 'example_restaurant', 'username': 'nonexistent_user'}}

        #This is running the function with the mock data
        result = get_user(event, table_mock)

        #Expected result that should appear when a user is not found
        expected_result = {'statusCode': 404, 'body': 'User not found.'}
        #Checking the response between the test data and the actual response
        self.assertEqual(result, expected_result)

    # Replacing the boto resource function with a mock object
    @patch('boto3.resource')
    # Testing the response of the application when the resturant ID is missing from the body
    def test_get_user_bad_request_missing_restaurant_id(self, key_mock):
        event = {'body': {'username': 'john_doe'}}

        # This tests whether the block raises an exception and if it does it passes if not the test will fail
        with self.assertRaises(BadRequestException):
            get_user(event, MagicMock())

    # Replacing the boto resource function with a mock object
    @patch('boto3.resource')
    # Testing the response of the application when the username is missing from the body
    def test_get_user_bad_request_missing_username(self, key_mock):
        event = {'body': {'restaurant_id': 'example_restaurant'}}

        # This tests whether the block raises an exception and if it does it passes if not the test will fail
        with self.assertRaises(BadRequestException):
            get_user(event, MagicMock())

    # Replacing the boto resource function with a mock object
    @patch('boto3.resource')
    @patch('botocore.exceptions.ClientError')
    # Testing the get user function if the user does not exists
    def test_get_user_not_found(self, key_mock, client_error_mock):
        #Creating the mock data and tables
        table_mock = MagicMock()
        table_mock.query.return_value = {'Items': []}

        #Dummy data
        event = {'body': {'restaurant_id': 'example_restaurant', 'username': 'nonexistent_user'}}

        #Running the mocked test data against the function
        result = get_user(event, table_mock)

        #Expected result when the application cannot find the user
        expected_result = {'statusCode': 404, 'body': 'User not found.'}
        #Comparing the actual and expected result
        self.assertEqual(result, expected_result)


#This class is testing the create_new_resturant against the dynamoDB
class TestCreateNewRestaurantDynamoDBEntries(unittest.TestCase):

    # Replacing the boto resource function with a mock object
    @patch('boto3.client')
    # Testing the results when a resturant is created
    def test_create_new_restaurant_success(self, client_mock):

        #This is assinging the mock object to the dynamo client mock as if it were an actual dynamodb client
        dynamodb_client_mock = client_mock.return_value

        #as we are simulating a success here the dictory will be empty as it is simulating a successful transaction
        dynamodb_client_mock.transact_write_items.return_value = {}

        #Dummy data
        event = {'body': {'restaurant_name': 'new_restaurant'}}

        #Running this with the event data on our table
        result = create_new_restaurant_dynamodb_entries(dynamodb_client_mock, event, 'FfSmartAppTheOneWeAreWorkingOnStackAnalysisAndDesignStorageStackC668B19C-analysisanddesigncourseworkmasterdynamodbtable3462106D-1IU8LQL1LND18')

        #Expected result on a success
        expected_result = {'statusCode': 200}
        #Comparing this with the actual result
        self.assertEqual(result, expected_result)

    # Replacing the boto resource function with a mock object
    @patch('boto3.client')
    # Testing the function if theres a conflict in data already in the table
    def test_create_new_restaurant_conflict(self, client_mock):
        #This is assinging the mock object to the dynamo client mock as if it were an actual dynamodb client
        dynamodb_client_mock = client_mock.return_value

        #This will raises a client error with the error response.
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

        #This is the test data we'll be using again
        event = {'body': {'restaurant_name': 'existing_restaurant'}}

        #Calling the function with our parameters
        try:
            create_new_restaurant_dynamodb_entries(
                dynamodb_client_mock,
                event,
                'FfSmartAppTheOneWeAreWorkingOnStackAnalysisAndDesignStorageStackC668B19C-analysisanddesigncourseworkmasterdynamodbtable3462106D-1IU8LQL1LND18'
            )
        #Catching the exceptions and if a specfic type is catch then the actions below ensures it has expected propterties
        except Exception as e:
            self.assertIsInstance(e, ClientError)
            self.assertEqual(e.response['Error']['Code'], 'TransactionCanceledException')
            self.assertEqual(e.response['Error']['Message'], 'The conditional request failed')
            self.assertEqual(e.response['ResponseMetadata']['HTTPStatusCode'], 500)







#This is testing deleting a user from the table
class TestDeleteUserLambda(unittest.TestCase):
    # Mocking up data that will be used over the various tests below
    def setUp(self):
        self.event = {
            'body': {
                'restaurant_id': 'example_restaurant',
                'username': 'example_user'
            }
        }
        #creating the mocked table
        self.table = MagicMock()

    #Testing if a succesful user deletion and the response it will return
    def test_delete_user_successful(self):
        #This simulates the behaviour of retirving an item from dynamodb with example data
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'users',
                'users': [{'username': 'existing_user'}, {'username': 'example_user'}]
            }
        }
        # Testing the delete user function with the the data that is about to be deleted and the mocked dynamodb table
        response = delete_user(self.event, self.table)

        #if both of these assertions pass with a status code of 200 and teh update_item method is called the expected number of times it will pass
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(self.table.update_item.call_count, 1)

    #Testing whether the delete user function can handle if a user is not found
    def test_delete_user_not_found(self):
        self.table.get_item.return_value = {}

        #once again this tests the delete_user function with the event and mocked data in teh table
        response = delete_user(self.event, self.table)

        #This will check that a 404 is displayed along with the resturant is not found error code
        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Restaurant does not exist', response['body'])

    #This tests the delete_user function when there is a dynamodb error
    def test_delete_user_dynamodb_error(self):
        self.table.get_item.side_effect = ClientError({'Error': {'Code': 'TestException'}}, 'operation_name')

        response = delete_user(self.event, self.table)
        print (response, "response")
        #This ensures that when running this and simulating a error it responds accordingly
        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error accessing DynamoDB', response['body'])


if __name__ == '__main__':
    unittest.main()