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

#Testing hte function modify door state - when opening the door or closing
class TestModifyDoorStateFunction(unittest.TestCase):
    #Mocking a test response making sure that if the door is closed it can be open
    def test_open_door_action(self):
        item = {'is_front_door_open': False, 'is_back_door_open': False}
        body = {'is_front_door_open': True, 'is_back_door_open': False}
        action = "open_door"

        #Opening the door with the mocked data from above
        modify_door_state(item, body, action)

        #Ensuring that the response shows the door being open
        self.assertTrue(item['is_front_door_open'])
        self.assertFalse(item['is_back_door_open'])


    #Testing the behaviour when the door is being closed
    def test_close_door_action(self):
        item = {'is_front_door_open': True, 'is_back_door_open': True}
        body = {}
        action = "close_door"

        modify_door_state(item, body, action)

        self.assertFalse(item['is_front_door_open'])
        self.assertFalse(item['is_back_door_open'])

    #This tests the initial door state and thedesired state from the request body and modified accorindly
    def test_close_door_action_with_existing_values(self):
        item = {'is_front_door_open': True, 'is_back_door_open': True}
        body = {'is_front_door_open': False, 'is_back_door_open': True}
        action = "close_door"

        modify_door_state(item, body, action)

        self.assertFalse(item['is_front_door_open'])
        self.assertFalse(item['is_back_door_open'])

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

class TestDeleteEntireItem(unittest.TestCase):
    # The test is desgined to validate the functionality of the delete_entire_item function 
    # test the deletion of an entire existing item from the list.
    def test_delete_entire_item_existing(self):
        #test set up
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

    # test the behavior of the function when attempting to delete an item that does not exist in the inventory.
    def test_delete_entire_item_non_existing(self):
        #test set up
        item = {'items': []}
        body = {'item_name': 'Milk', 'quantity_change': 10, 'expiry_date': '2024-01-01'}
        delete_entire_item(item, body)
        self.assertEqual(len(item['items']), 0)

    # test the function's ability to partially delete an item.
    def test_delete_partial_item(self):
        #test set up
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

    # verify the function's behavior when the deletion request is for an item with a specific expiry date that does not exist in the inventory
    def test_delete_item_not_in_list(self):
        #test set up
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

    #  test the function's response when attempting to delete an item name that does not exist in the inventory.
    def test_delete_nonexistent_item_name(self):
        #test set up
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

    # test no changes are made if the parameter is the wrong format
    def test_wrong_input(self):
        test_item = {'test_key': 'test_value'}

        delete_zero_quantity_items(test_item)

        self.assertEqual(test_item, {'test_key': 'test_value'})


class TestModifyItemsFunction(unittest.TestCase):
    # test if the function can update an existing item
    @patch('src.inventory_utils.get_current_time_gmt')
    def test_update_existing_item(self, mock_get_current_time):
        item = {'items': [{'item_name': 'apple', 'desired_quantity': 5,
                           'item_list': [{'current_quantity': 3, 'expiry_date': '2024-02-01',
                                          'date_added': 1643424000, 'date_removed': 0}]}]}
        body = {'item_name': 'apple', 'quantity_change': 2, 'expiry_date': '2024-02-01'}
        action = ""
        mock_get_current_time.return_value = 1643424000  # mock the current time

        modify_items(item, body, action, mock_get_current_time())

        self.assertEqual(item['items'], [{'item_name': 'apple', 'desired_quantity': 5,
                                          'item_list': [{'current_quantity': 5, 'expiry_date': '2024-02-01',
                                                         'date_added': 1643424000, 'date_removed': 0}]}])

    # test if the function can create a new item
    @patch('src.inventory_utils.get_current_time_gmt')
    def test_create_new_item(self, mock_get_current_time):
        item = {'items': []}
        body = {'item_name': 'apple', 'quantity_change': 5, 'expiry_date': '2024-02-01'}
        action = ""
        mock_get_current_time.return_value = 1643491200  # mock the current time

        modify_items(item, body, action, mock_get_current_time())

        self.assertEqual(item['items'], [{'item_name': 'apple', 'desired_quantity': 5,
                                          'item_list': [{'current_quantity': 5, 'expiry_date': '2024-02-01',
                                                         'date_added': 1643491200, 'date_removed': 0}]}])

    # test if the function can create a new item where the desired quantity is different to the current quantity
    @patch('src.inventory_utils.get_current_time_gmt')
    def test_create_new_item_with_desired_quantity(self, mock_get_current_time):
        item = {'items': []}
        body = {'item_name': 'apple', 'quantity_change': 5, 'expiry_date': '2024-02-01', 'desired_quantity': 10}
        action = ""
        mock_get_current_time.return_value = 1643491200  # mock the current time

        modify_items(item, body, action, mock_get_current_time())

        self.assertEqual(item['items'], [{'item_name': 'apple', 'desired_quantity': 10,
                                          'item_list': [{'current_quantity': 5, 'expiry_date': '2024-02-01',
                                                         'date_added': 1643491200, 'date_removed': 0}]}])

    # test the function can update an existing item with a different expiry
    @patch('src.inventory_utils.get_current_time_gmt')
    def test_update_existing_item_with_different_expiry(self, mock_get_current_time):
        item = {'items': [{'item_name': 'apple', 'desired_quantity': 5,
                           'item_list': [{'current_quantity': 3, 'expiry_date': '2024-02-01',
                                          'date_added': 1643424000, 'date_removed': 0}]}]}
        body = {'item_name': 'apple', 'quantity_change': 2, 'expiry_date': '2024-03-01'}
        action = ""
        mock_get_current_time.return_value = 1643424000  # mock the current time

        modify_items(item, body, action, mock_get_current_time())

        self.assertEqual(item['items'], [{'item_name': 'apple', 'desired_quantity': 5,
                                          'item_list': [{'current_quantity': 3, 'expiry_date': '2024-02-01',
                                                         'date_added': 1643424000, 'date_removed': 0},
                                                        {'current_quantity': 2, 'expiry_date': '2024-03-01',
                                                         'date_added': 1643424000, 'date_removed': 0}]}])


if __name__ == '__main__':
    unittest.main()


