import unittest
from unittest.mock import patch, MagicMock
from src.index import handler

class TestDynamoDBHandler(unittest.TestCase):

    @patch('boto3.resource')
    def test_view_inventory_success(self, mock_boto3_resource):
        """
        Test the 'view_inventory' action of the handler function.
        """

        # Setup mock DynamoDB
        mock_dynamodb_resource = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb_resource
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': {'pk': 'restaurant_1', 'type': 'fridge', 'items': []}}

        # Define handler input for 'view_inventory' action
        mock_event = {
            'body': json.dumps({'restaurant_name': 'restaurant_1'}),
            'action': 'view_inventory'
        }
        mock_context = {}

        # Execute handler function
        response = handler(mock_event, mock_context)

        # Verify DynamoDB get_item was called correctly
        mock_table.get_item.assert_called_with(Key={'pk': 'restaurant_1', 'type': 'fridge'})

        # Define expected response
        expected_response = {
            'statusCode': 200,
            'body': {'details': 'Inventory retrieved successfully', 'additional_details': {'pk': 'restaurant_1', 'type': 'fridge', 'items': []}}
        }

        # Assert response matches expected
        self.assertEqual(response, expected_response)

    # Additional test cases go here, for different actions and scenarios

if __name__ == '__main__':
    unittest.main()

