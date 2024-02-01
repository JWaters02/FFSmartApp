import json
import unittest
from unittest.mock import patch, MagicMock, ANY
from src.inventory_utils import modify_door_state, generate_response
from src.inventory_utils import delete_zero_quantity_items
from src.index import handler
class TestDynamoDBHandler(unittest.TestCase):

    @patch('boto3.resource')
    def test_view_inventory_success(self, mock_boto3_resource):
        """
        Test the 'view_inventory' action of the handler function.
        """

        mock_dynamodb_resource = MagicMock()
        mock_boto3_resource.return_value = mock_dynamodb_resource
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {'Item': {'pk': 'restaurant_1', 'type': 'fridge', 'items': []}}

        mock_event = {
            'body': json.dumps({'restaurant_name': 'restaurant_1'}),
            'action': 'view_inventory'
        }
        mock_context = {}

        response = handler(mock_event, mock_context)

        mock_table.get_item.assert_called_with(Key={'pk': 'restaurant_1', 'type': 'fridge'})

        expected_response = {
            'statusCode': 200,
            'body': {'details': 'Inventory retrieved successfully', 'additional_details': {'pk': 'restaurant_1', 'type': 'fridge', 'items': []}}
        }

        self.assertEqual(response, expected_response)

#Testing hte function modify door state - when opening the door or closing
class TestModifyDoorStateFunction(unittest.TestCase):

    def test_open_back_door_action(self):
        # Create a MagicMock for the DynamoDB table
        mock_table = MagicMock()

        # Set the return value of get_item() to a dictionary with the expected item
        mock_table.get_item.return_value = {'Item': {'is_front_door_open': False, 'is_back_door_open': True}}

        # Define your test data
        pk = 'test_pk'
        body = {'is_front_door_open': True, 'is_back_door_open': False}
        action = 'open_back_door'

        # Call the function with the mocked data
        response = modify_door_state(mock_table, pk, body, action)

        # Assert the expected behavior
        expected_response = generate_response(200, 'Door state updated successfully', {
            'is_front_door_open': False,
            'is_back_door_open': True
        })
        self.assertEqual(response, expected_response)

    def test_close_front_door_action(self):
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': {'is_front_door_open': True, 'is_back_door_open': True}}

        pk = 'test_pk'
        body = {'is_front_door_open': False, 'is_back_door_open': True}
        action = 'close_front_door'

        response = modify_door_state(mock_table, pk, body, action)

        expected_response = generate_response(200, 'Door state updated successfully', {
            'is_front_door_open': False,
            'is_back_door_open': True
        })
        self.assertEqual(response, expected_response)


class TestGenerateResponse(unittest.TestCase):
    # This test verifies the behavior of the generate_response function when it is called
    def test_generate_response_with_additional_details(self):
        #test parameters
        status_code = 200
        message = "Success"
        additional_details = {'key': 'value'}
        response = generate_response(status_code, message, additional_details)
        #Verifies that the details field in the response body contains the correct message 
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body']['details'], "Success")
        self.assertEqual(response['body']['additional_details'], {'key': 'value'})

    # This test checks the behavior of the generate_response function when it is called without additional details.
    def test_generate_response_without_additional_details(self):
        #test set up
        status_code = 500
        message = "Error"
        response = generate_response(status_code, message)
        # Checks if the details field in the response body correctly contains the error message 
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body']['details'], "Error")
        self.assertNotIn('additional_details', response['body'])


class TestDeleteZeroQuantityItemsFunction(unittest.TestCase):
    # test if the function removes empty items
    def test_remove_empty_item(self):
        mock_item = {'items': [{'item_list': [{'current_quantity': 5}]}, {'item_list': []}]}

        delete_zero_quantity_items(mock_item)

        self.assertEqual(mock_item['items'], [{'item_list': [{'current_quantity': 5}]}])

    # test if the function removes an item where current_quantity = 0
    def test_remove_zero_quantity_item(self):
        mock_item = {'items': [{'item_list': [{'current_quantity': 5}]},
                               {'item_list': [{'current_quantity': 0}]},
                               {'item_list': [{'current_quantity': 5}]}]}

        delete_zero_quantity_items(mock_item)

        self.assertEqual(mock_item['items'], [{'item_list': [{'current_quantity': 5}]},
                                              {'item_list': [{'current_quantity': 5}]}])

    # test if the function makes no changes if no empty or zero quantity items found
    def test_keep_non_zero_quantity_item(self):
        test_item = {'items': [{'item_list': [{'current_quantity': 5}]},
                               {'item_list': [{'current_quantity': 5}]},
                               {'item_list': [{'current_quantity': 5}]}]}

        delete_zero_quantity_items(test_item)

        self.assertEqual(test_item['items'], [{'item_list': [{'current_quantity': 5}]},
                                              {'item_list': [{'current_quantity': 5}]},
                                              {'item_list': [{'current_quantity': 5}]}])

    # test no changes are made if the parameter is the wrong format.
    def test_wrong_input(self):
        test_item = {'test_key': 'test_value'}

        delete_zero_quantity_items(test_item)

        self.assertEqual(test_item, {'test_key': 'test_value'})


if __name__ == '__main__':
    unittest.main()


