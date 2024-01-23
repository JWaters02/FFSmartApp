import json
import unittest
from unittest.mock import patch, MagicMock
from src.inventory_utils import modify_door_state, generate_response, delete_entire_item
from src.inventory_utils import delete_zero_quantity_items, modify_items
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

class TestModifyDoorStateFunction(unittest.TestCase):

    def test_open_door_action(self):
        item = {'is_front_door_open': False, 'is_back_door_open': False}
        body = {'is_front_door_open': True, 'is_back_door_open': False}
        action = "open_door"

        modify_door_state(item, body, action)

        self.assertTrue(item['is_front_door_open'])
        self.assertFalse(item['is_back_door_open'])

    def test_open_door_action_with_default_values(self):
        item = {'is_front_door_open': False, 'is_back_door_open': False}
        body = {}
        action = "open_door"

        modify_door_state(item, body, action)

        self.assertFalse(item['is_front_door_open'])  # Default value should be False
        self.assertFalse(item['is_back_door_open'])   # Default value should be False

    def test_close_door_action(self):
        item = {'is_front_door_open': True, 'is_back_door_open': True}
        body = {}
        action = "close_door"

        modify_door_state(item, body, action)

        self.assertFalse(item['is_front_door_open'])
        self.assertFalse(item['is_back_door_open'])

    def test_close_door_action_with_existing_values(self):
        item = {'is_front_door_open': True, 'is_back_door_open': True}
        body = {'is_front_door_open': False, 'is_back_door_open': True}
        action = "close_door"

        modify_door_state(item, body, action)

        self.assertFalse(item['is_front_door_open'])
        self.assertFalse(item['is_back_door_open'])

class TestGenerateResponse(unittest.TestCase):

    def test_generate_response_with_additional_details(self):
        status_code = 200
        message = "Success"
        additional_details = {'key': 'value'}
        response = generate_response(status_code, message, additional_details)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body']['details'], "Success")
        self.assertEqual(response['body']['additional_details'], {'key': 'value'})

    def test_generate_response_without_additional_details(self):
        status_code = 500
        message = "Error"
        response = generate_response(status_code, message)
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body']['details'], "Error")
        self.assertNotIn('additional_details', response['body'])

class TestDeleteEntireItem(unittest.TestCase):

    def test_delete_entire_item_existing(self):
        item = {
            'items': [
                {
                    'item_name': 'Milk',
                    'item_list': [
                        {'expiry_date': '2024-01-01', 'current_quantity': 10}
                    ]
                }
            ]
        }
        body = {'item_name': 'Milk', 'quantity_change': 10, 'expiry_date': '2024-01-01'}
        delete_entire_item(item, body)
        self.assertEqual(len(item['items']), 0)

    def test_delete_entire_item_non_existing(self):
        item = {'items': []}
        body = {'item_name': 'Milk', 'quantity_change': 10, 'expiry_date': '2024-01-01'}
        delete_entire_item(item, body)
        self.assertEqual(len(item['items']), 0)

    def test_delete_partial_item(self):
        item = {
            'items': [
                {
                    'item_name': 'Juice',
                    'item_list': [
                        {'expiry_date': '2024-02-01', 'current_quantity': 20},
                        {'expiry_date': '2024-03-01', 'current_quantity': 15}
                    ]
                }
            ]
        }
        body = {'item_name': 'Juice', 'quantity_change': 20, 'expiry_date': '2024-02-01'}
        delete_entire_item(item, body)
        self.assertEqual(len(item['items'][0]['item_list']), 1)
        self.assertNotIn({'expiry_date': '2024-02-01', 'current_quantity': 20}, item['items'][0]['item_list'])

    def test_delete_item_not_in_list(self):
        item = {
            'items': [
                {
                    'item_name': 'Water',
                    'item_list': [
                        {'expiry_date': '2024-04-01', 'current_quantity': 30}
                    ]
                }
            ]
        }
        body = {'item_name': 'Water', 'quantity_change': 15, 'expiry_date': '2024-05-01'}
        delete_entire_item(item, body)
        self.assertEqual(len(item['items'][0]['item_list']), 1)
        self.assertIn({'expiry_date': '2024-04-01', 'current_quantity': 30}, item['items'][0]['item_list'])

    def test_delete_nonexistent_item_name(self):
        item = {
            'items': [
                {
                    'item_name': 'Tea',
                    'item_list': [
                        {'expiry_date': '2024-06-01', 'current_quantity': 25}
                    ]
                }
            ]
        }
        body = {'item_name': 'Coffee', 'quantity_change': 25, 'expiry_date': '2024-06-01'}
        delete_entire_item(item, body)
        self.assertEqual(len(item['items']), 1)
        self.assertEqual(item['items'][0]['item_name'], 'Tea')

class TestDeleteZeroQuantityItemsFunction(unittest.TestCase):

    def test_remove_empty_items(self):
        # Create input parameters for function
        test_item = {'items':[{'item_list':[{'current_quantity': 5}]},{'item_list': []}]}

        # Execute function
        delete_zero_quantity_items(test_item)

        # Verify response
        self.assertEqual(test_item['items'],[{'item_list':[{'current_quantity': 5}]}])

    def test_remove_zero_quantity_item(self):
        # Create input parameters for function
        test_item = {'items':[{'item_list':[{'current_quantity':5}]},{'item_list':[{'current_quantity':0}]},{'item_list':[{'current_quantity':5}]}]}

        # Execute function
        delete_zero_quantity_items(test_item)

        # Verify response
        self.assertEqual(test_item['items'],[{'item_list':[{'current_quantity':5}]},{'item_list':[{'current_quantity':5}]}])


    def test_keep_non_zero_quantity_item(self):
        # Create input parameters for function
        test_item = {'items':[{'item_list':[{'current_quantity':5}]},{'item_list':[{'current_quantity':5}]},{'item_list':[{'current_quantity':5}]}]}

        # Execute function
        delete_zero_quantity_items(test_item)

        # Verify response
        self.assertEqual(test_item['items'],[{'item_list':[{'current_quantity':5}]},{'item_list':[{'current_quantity':5}]},{'item_list':[{'current_quantity':5}]}])

    def test_wrong_input(self):
        # Create input parameters for function
        test_item = {'test_key':'test_value'}

        # Execute function
        delete_zero_quantity_items(test_item)

        # Verify response
        self.assertEqual(test_item, {'test_key':'test_value'})

class TestModifyItemsFunction(unittest.TestCase):

    @patch('src.inventory_utils.get_current_time_gmt')
    def test_update_existing_item(self, mock_get_current_time):

        # Create input parameters for function
        item = {'items': [{ 'item_name': 'apple', 'desired_quantity': 5, 'item_list': [ {  'current_quantity': 3, 'expiry_date': '2024-02-01', 'date_added': 1643424000, 'date_removed': 0}]}]}
        body = {'item_name': 'apple', 'quantity_change': 2, 'expiry_date': '2024-02-01'}
        action = ""
        mock_get_current_time.return_value = 1643424000  # Mock current time

        # Execute function
        modify_items(item, body, action, mock_get_current_time())

        # Verify response
        self.assertEqual(item['items'], [{'item_name': 'apple','desired_quantity': 5,'item_list': [{'current_quantity': 5,'expiry_date': '2024-02-01','date_added': 1643424000,'date_removed': 0}]}])

    @patch('src.inventory_utils.get_current_time_gmt')
    def test_create_new_item(self, mock_get_current_time):

        # Create input parameters for function
        item = {'items': []}
        body = {'item_name': 'apple', 'quantity_change': 5, 'expiry_date': '2024-02-01'}
        action = ""
        mock_get_current_time.return_value = 1643491200  # Mock current time

        # Execute function
        modify_items(item, body, action, mock_get_current_time())

        # Verify response
        self.assertEqual(item['items'], [{'item_name': 'apple','desired_quantity': 5,'item_list': [{'current_quantity': 5,'expiry_date': '2024-02-01','date_added': 1643491200,'date_removed': 0}]}])

    @patch('src.inventory_utils.get_current_time_gmt')
    def test_create_new_item_with_desired_quantity(self, mock_get_current_time):

        # Create input parameters for function
        item = {'items': []}
        body = {'item_name': 'apple', 'quantity_change': 5, 'expiry_date': '2024-02-01', 'desired_quantity': 10}
        action = ""
        mock_get_current_time.return_value = 1643491200  # Mock current time

        # Execute function
        modify_items(item, body, action, mock_get_current_time())

        # Verify response
        self.assertEqual(item['items'], [{'item_name': 'apple','desired_quantity': 10,'item_list': [{'current_quantity': 5,'expiry_date': '2024-02-01','date_added': 1643491200,'date_removed': 0}]}])

    @patch('src.inventory_utils.get_current_time_gmt')
    def test_update_existing_item_with_different_expiry(self, mock_get_current_time):

        # Create input parameters for function
        item = {'items': [{ 'item_name': 'apple', 'desired_quantity': 5, 'item_list': [ {  'current_quantity': 3, 'expiry_date': '2024-02-01', 'date_added': 1643424000, 'date_removed': 0}]}]}
        body = {'item_name': 'apple', 'quantity_change': 2, 'expiry_date': '2024-03-01'}
        action = ""
        mock_get_current_time.return_value = 1643424000  # Mock current time

        # Execute function
        modify_items(item, body, action, mock_get_current_time())

        # Verify response
        self.assertEqual(item['items'], [{'item_name': 'apple','desired_quantity': 5,'item_list': [{'current_quantity': 3,'expiry_date': '2024-02-01','date_added': 1643424000,'date_removed': 0},{'current_quantity': 2,'expiry_date': '2024-03-01','date_added': 1643424000,'date_removed': 0}]}])


if __name__ == '__main__':
    unittest.main()


