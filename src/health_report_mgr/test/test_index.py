import unittest
from unittest.mock import patch, MagicMock
from ..src.index import handler
import json
from boto3.dynamodb.conditions import Key
import unittest
from unittest.mock import Mock, patch
from src.utils import get_health_and_safety_email, get_filtered_items, send_email_with_attachment


class TestHandler(unittest.TestCase):

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_handler_function(self, mock_boto_resource, mock_boto_client):  # use highly descriptive function names, not what like this
        """Succeeds"""
        # Mock DynamoDB
        mock_dynamodb_resource = MagicMock()
        mock_boto_resource.return_value = mock_dynamodb_resource
        mock_dynamodb_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_dynamodb_table
        mock_dynamodb_table.query.return_value = {'Items': [{'sample_key': 'sample_value'}]}

        # Mock SES
        mock_ses_client = MagicMock()
        mock_boto_client.return_value = mock_ses_client

        # Handler event and context
        mock_event = {
            'pk': 'example_pk',
            'type': 'example_type'
        }
        mock_context = {}

        # Call the handler
        response = handler(mock_event, mock_context)

        # Verify that DynamoDB query was called correctly
        mock_dynamodb_table.query.assert_called_with(
            KeyConditionExpression=Key('pk').eq('example_pk') & Key('type').eq('example_type')
        )

        # Verify that SES send_email was called
        mock_ses_client.send_email.assert_called_with(
            Source='SENDER_EMAIL',  # TODO: needs to be verified and other stuff
            Destination={'ToAddresses': ['ben@benlewisjones.com']},
            Message={
                'Subject': {'Data': 'DynamoDB Data'},
                'Body': {'Text': {'Data': json.dumps([{'sample_key': 'sample_value'}])}}
            }
        )

        # Assert response
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], json.dumps('Email sent!'))

class TestDynamoDBFunctions(unittest.TestCase):
    # Test the functions related to the DyanmoDB operations

    @patch('src.utils.boto3')
    # Tests the get_health_and_safety_email function to ensure it correctly retrieves a health and safety email address from a DynamoDB table when it exists
    def test_get_health_and_safety_email_found(self, mock_boto3):
        #A mock DynamoDB table is created and configured to return a response containing an email when the get_item method is called
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {'health_and_safety_email': 'test@example.com'}
        }

        email = get_health_and_safety_email(mock_table, 'TestRestaurant')
        # The assertion ensures that the returned email matches the mocked email set up.
        self.assertEqual(email, 'test@example.com')

    @patch('src.utils.boto3')
    #Tests the get_health_and_safety_email function to ensure it returns nothing when the email address is not found in the DynamoDB table
    def test_get_health_and_safety_email_not_found(self, mock_boto3):
        mock_table = Mock()
        mock_table.get_item.return_value = {'Item': {}}
        # The get_health_and_safety_email function is called with the mocked test data

        email = get_health_and_safety_email(mock_table, 'TestRestaurant')
        # Assertion to verify that return is none which shows that no email was found.
        self.assertIsNone(email)

    @patch('src.utils.boto3')
    #Tests the get_filtered_items function to ensure it can retrieve and filter items from a DynamoDB table based on provided date criteria.
    def test_get_filtered_items(self, mock_boto3):
        mock_table = Mock()
        #The mock table is set up to return a list of each item with details
        mock_table.query.return_value = {
            'Items': [
                {
                    'pk': 'TestRestaurant',
                    'type': 'fridge',
                    'items': [
                        {
                            'item_name': 'Milk',
                            'item_list': [
                                {
                                    'date_added': '1609459200',
                                    'date_removed': '1609545600',
                                    'current_quantity': '10',
                                    'expiry_date': '1609824800'
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        start_date, end_date = 1609459200, 1609824800
        items = get_filtered_items(mock_table, 'TestRestaurant', start_date, end_date)
        #Assertion to check that the returned list of items is not empty
        self.assertTrue(len(items) > 0)


class TestSendEmailWithAttachmentFunction (unittest.TestCase):
    # test the function works when given the expected parameters
    @patch('src.utils.boto3.client')
    @patch('src.utils.create_csv_content')
    def test_normal_parameters(self, mock_create_csv_content, mock_boto3_client):
        mock_ses_client = MagicMock()
        mock_boto3_client.return_value = mock_ses_client
        mock_create_csv_content.return_value = 'CSV_CONTENT'

        email = 'example@example.com'
        restaurant_name = 'example_name'
        start_date = '2024-01-01'
        end_date = '2025-01-01'
        filtered_items = [{'example': 'example'}]

        send_email_with_attachment(email, restaurant_name, start_date, end_date, filtered_items)

        mock_boto3_client.assert_called_with('ses')
        mock_ses_client.send_raw_email.assert_called_once()
        mock_create_csv_content.assert_called_with(filtered_items)


if __name__ == '__main__':
    unittest.main()

