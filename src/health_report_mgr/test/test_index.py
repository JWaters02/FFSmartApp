import unittest
from unittest.mock import patch, MagicMock
from src.index import handler
from src.utils import send_email_with_attachment
from ..src.index import handler
import json
from boto3.dynamodb.conditions import Key

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
