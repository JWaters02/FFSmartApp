import unittest
import time
from unittest.mock import patch, MagicMock
from src.orders_mgr.src.index import handler
from src.orders_mgr.src.delete import delete_order, ClientError
from src.orders_mgr.src.post import create_order, NotFoundException, order_check
from src.orders_mgr.src.get import get_all_orders, get_order
from src.orders_mgr.src.custom_exceptions import BadRequestException
from src.orders_mgr.src.utils import (generate_order_id, is_order_id_valid, get_expired_item_quantity_fridge, get_item_quantity_fridge,
                       get_item_quantity_orders, get_total_item_quantity)



#This call is testing the delete order lambda by mocking the data
class TestDeleteOrderLambda(unittest.TestCase):
    # Mocking up data that will be used over the various tests below
    def setUp(self):
        self.event = {
            'body': {
                'restaurant_id': 'example_restaurant',
                'order_id': 'example_order'
            }
        }
        #creating the mocked table
        self.table = MagicMock()

    # Testing if what happens when a successful order is deleted and how the program handles this
    def test_delete_order_successful(self):
        #This is creating the dynamoDB response and mocking it
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'orders',
                'orders': [{'id': 'existing_order'}, {'id': 'example_order'}]
            }
        }

        #This will return the status code from running the mocked table against the response in setup
        response = delete_order(self.event, self.table)

        #This will pass the test if the status code is 200 and its ran once
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(self.table.update_item.call_count, 1)

    #Testing what happens when the function does not find the order when deleted
    def test_delete_order_not_found(self):
        # This is mocking a response for a resturant that does not exist
        self.table.get_item.return_value = {}

        #This will return the status code from running the mocked table against the response in setup
        response = delete_order(self.event, self.table)

        #This will pass the test if the status code is 404 and the body contains a error
        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Restaurant does not exist', response['body'])

    #This is testing when deleting a order what the function does when the ID is malformed
    def test_delete_order_invalid_order_id(self):
        # Mocking a Dynamodb response with a incorrect ID
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'orders',
                'orders': [{'id': 'another_order'}, {'id': 'yet_another_order'}]
            }
        }

        #This will return the status code from running the mocked table against the response in setup
        response = delete_order(self.event, self.table)

        #This will pass the test if the status code is 404 and the body contains a error
        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Order does not exist', response['body'])

    # Testing what happens if the dynamoDb encounters a failure during a delete
    def test_dynamodb_error(self):
        # This mocks a dynamodb error without using the database
        self.table.get_item.side_effect = ClientError({'Error': {'Code': 'TestException'}},
                                                      'operation_name')

        #This will return the status code from running the mocked table against the response in setup
        response = delete_order(self.event, self.table)

        #This will pass the test if the status code is 500 and the body contains a error
        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error accessing DynamoDB', response['body'])


#Testing the create order function with mocking data and responses
class TestCreateOrderFunction(unittest.TestCase):
    # This is the mocked setup of all data we will use for these tests
    def setUp(self):
        self.dynamodb_client = MagicMock()
        self.table = MagicMock()
        self.restaurant_name = 'example_restaurant'
        self.order_items = [{'item_id': 'item1', 'quantity': 2}, {'item_id': 'item2', 'quantity': 3}]
        self.expired_items = [{'item_id': 'expired_item', 'quantity': 1}]
        self.table_name = 'example_table'

    #Testing the response when an order is created successfully
    def test_create_order_successful(self):
        # Here we are modifying the generate order function to isolate the behaviour of this method
        with patch('src.orders_mgr.src.post.generate_order_id', return_value='example_order_id'):
            #Creating the response from all the mocked data into the function
            response = create_order(self.dynamodb_client, self.table, self.restaurant_name, self.order_items,
                                    self.expired_items, self.table_name)

        #This will only pass the test with the correct status code and an successful order creation along with mocked expiry date of an item
        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(response['body']['order_id'], 'example_order_id')
        self.assertEqual(response['body']['expired_items'], self.expired_items)

        #This verifyies that the update item method on the mocked client has been called only once based on teh parameters chosen
        self.dynamodb_client.update_item.assert_called_once_with(
            TableName='example_table',
            Key={
                'pk': {'S': 'example_restaurant'},
                'type': {'S': 'orders'}
            },
            UpdateExpression="SET #ord = list_append(#ord, :new_order)",
            ExpressionAttributeNames={
                '#ord': 'orders'
            },
            ExpressionAttributeValues={
                ':new_order': {
                    'L': [
                        {
                            'M': {
                                'id': {'S': 'example_order_id'},
                                'delivery_date': {'N': str(int(time.time()) + 86400)},
                                'date_ordered': {'N': str(int(time.time()))},
                                'items': {'L': self.order_items}
                            }
                        }
                    ]
                },
            },
        )

    #Testing what happens when an creating an order cannot be found
    def test_create_order_not_found_exception(self):
        # Here we are modifying the generate order function to isolate the behaviour of this method
        with patch('src.orders_mgr.src.post.generate_order_id', return_value='example_order_id'):
            #Creating the response from all the mocked data into the function
            self.table.update_item.side_effect = NotFoundException('Restaurant does not exist')
            response = create_order(self.dynamodb_client, self.table, self.restaurant_name, self.order_items,
                                    self.expired_items, self.table_name)

        #This will only pass the test with the correct status code
        self.assertEqual(response['statusCode'], 201)

    #This is testing what happens when mocking a client error during a order creation
    def test_create_order_client_error_exception(self):
        # Here we are modifying the generate order function to isolate the behaviour of this method
        with patch('src.orders_mgr.src.post.generate_order_id', return_value='example_order_id'):
            #Creating the response from all the mocked data into the function
            self.table.update_item.side_effect = ClientError({'Error': {'Code': 'TestException'}}, 'operation_name')
            response = create_order(self.dynamodb_client, self.table, self.restaurant_name, self.order_items,
                                    self.expired_items, self.table_name)

        #This will only pass the test with the correct status code
        self.assertEqual(response['statusCode'], 201)

#Testing the checking for the fridge based on given ID of the resturant
class TestOrderCheck(unittest.TestCase):

    # Replacing the boto resource function with a mock object
    @patch('src.orders_mgr.src.post.get_total_item_quantity')
    @patch('src.orders_mgr.src.post.get_expired_item_quantity_fridge')
    @patch('src.orders_mgr.src.post.create_order')
    # This test mocks the dynamodb table with a resturant ID and checks against it that it cant find the fridge and orders response
    def test_order_needed(self, mock_create_order, mock_expired_quantity, mock_total_quantity):
        def test_order_needed(self, mock_create_order, mock_expired_quantity, mock_total_quantity):
            mock_table = MagicMock()
            # Mocking fridge information
            mock_dynamodb_client = MagicMock()
            mock_event = {'body': {'restaurant_id': 'restaurant_id'}}
            mock_table_name = 'your_table_name'

            # Mocking the fridge response
            fridge_response = {
                'Items': [
                    {'item_name': 'item1', 'desired_quantity': 10,
                     'items': [{'expiry_date': '2024-01-01', 'current_quantity': 5}]}
                ]
            }

            # Mocking the orders response
            orders_response = {
                'Items': [
                    {'item_name': 'item1', 'orders': [{'expiry_date': '2024-01-01', 'quantity': 2}]}
                ]
            }

            mock_table.query.side_effect = [fridge_response, orders_response]

            # Running the function against the mocked information
            result = order_check(mock_dynamodb_client, mock_event, mock_table, mock_table_name)

            # Ensuring that the mock total quantity is only called once
            mock_total_quantity.assert_called_once_with(
                {'item_name': 'item1', 'desired_quantity': 10,
                 'items': [{'expiry_date': '2024-01-01', 'current_quantity': 5}]},
                [{'item_name': 'item1', 'orders': [{'expiry_date': '2024-01-01', 'quantity': 2}]}]
            )
            # ensuring that the mocked expired quantity is only called once
            mock_expired_quantity.assert_called_once_with(
                {'item_name': 'item1', 'desired_quantity': 10,
                 'items': [{'expiry_date': '2024-01-01', 'current_quantity': 5}]}
            )
            # Ensuring that the create order is called exactly once with specific arguments
            mock_create_order.assert_called_once_with(
                mock_dynamodb_client, mock_table,
                'restaurant_id', [{'M': {'item_name': {'S': 'item1'}, 'quantity': {'N': '3'}}}], [], mock_table_name
            )

            # This will only pass the test with the correct status code
            self.assertEqual(result['statusCode'], 201)


class TestGetAllOrdersFunction(unittest.TestCase):
    # test the function can run when given the expected parameters
    def test_normal_parameters(self):
        event = {'body': {'restaurant_id': 'example_restaurant'}}
        self.table = MagicMock()

        response = get_all_orders(event, self.table)

        self.assertEqual(response['statusCode'], 200)

    # test the function returns an appropriate error message when there is a key error
    def test_key_error(self):
        event = {'body': {'restaurant_id': 'example_restaurant'}}
        self.table = MagicMock()
        self.table.query.side_effect = KeyError()

        response = get_all_orders(event, self.table)

        self.assertEqual(response['statusCode'], 404)

    # test the function returns an appropriate error message when there is a client error
    def test_client_error(self):
        event = {'body': {'restaurant_id': 'example_restaurant'}}
        self.table = MagicMock()
        self.table.query.side_effect = ClientError(error_response={'Error': {'Code': 'TestException'}},
                                                   operation_name='query')

        response = get_all_orders(event, self.table)

        self.assertEqual(response['statusCode'], 500)


class TestGetOrderFunction(unittest.TestCase):
    # test the function can run when given the expected parameters
    def test_normal_parameters(self):
        event = {'body': {'restaurant_id': 'example_restaurant', 'order_id': 'example_id'}}
        self.table = MagicMock()

        response = get_order(event, self.table)

        self.assertEqual(response['statusCode'], 200)

    # test the function returns an appropriate error message when the event body is missing
    def test_event_missing_body(self):
        event = {'example': 'example'}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            get_order(event, self.table)
        self.assertEqual(str(context.exception), 'Bad request restaurant_id not found in body.')

    # test the function returns an appropriate error message when the restaurant id is missing
    def test_event_missing_restaurant_id(self):
        event = {'body': {'order_id': 'example_id'}}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            get_order(event, self.table)
        self.assertEqual(str(context.exception), 'Bad request restaurant_id not found in body.')

    # test the function returns an appropriate error message when the order id is missing
    def test_event_missing_order_id(self):
        event = {'body': {'restaurant_id': 'example_restaurant'}}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            get_order(event, self.table)
        self.assertEqual(str(context.exception), 'Bad request order_id not found in body.')

    # test the function returns an appropriate error message when there is a key error
    def test_key_error(self):
        event = {'body': {'restaurant_id': 'example_restaurant', 'order_id': 'example_id'}}
        self.table = MagicMock()
        self.table.query.side_effect = KeyError()

        response = get_order(event, self.table)

        self.assertEqual(response['statusCode'], 404)

    # test the function returns an appropriate error message when there is a client error
    def test_client_error(self):
        event = {'body': {'restaurant_id': 'example_restaurant', 'order_id': 'example_id'}}
        self.table = MagicMock()
        self.table.query.side_effect = ClientError(error_response={'Error': {'Code': 'TestException'}},
                                                   operation_name='query')

        response = get_order(event, self.table)

        self.assertEqual(response['statusCode'], 500)


class TestGenerateOrderIdFunction(unittest.TestCase):
    # tests the function returns the correct id
    @patch('src.orders_mgr.src.utils.secrets')
    def test_normal_parameters(self, mock_secrets):
        self.table = MagicMock()
        restaurant_id = 'example_restaurant'
        mock_secrets.randbits.return_value = 1234567890123456

        response = generate_order_id(self.table, restaurant_id)

        self.assertEqual(response, '1234567890123456')

    # tests the function returns the correct error message when there is no restaurant id
    def test_missing_restaurant_id(self):
        self.table = MagicMock()
        restaurant_id = 'example_restaurant'
        self.table.get_item.return_value = {'example': 'example'}

        with self.assertRaises(NotFoundException) as context:
            generate_order_id(self.table, restaurant_id)
        self.assertEqual(str(context.exception), 'Restaurant does not exist.')


class TestIsOrderIdValidFunction(unittest.TestCase):
    # tests the function returns true if there is no matching ids
    def test_id_valid(self):
        order_id = 1234567890123456
        self.item = MagicMock()

        response = is_order_id_valid(order_id, self.item)

        self.assertEqual(response, True)

    # tests the function returns false if there is a matching id
    def test_id_invalid(self):
        order_id = 1234567890123456
        self.item = {'orders': [{'id': 1234567890123456}]}

        response = is_order_id_valid(order_id, self.item)

        self.assertEqual(response, False)


class TestGetExpiredItemQuantityFridgeFunction(unittest.TestCase):
    # tests the function returns the correct quantity
    def test_normal_parameters(self):
        mock_time = time.time()-999999
        self.fridge_item = {'item_list': [{'expiry_date': mock_time, 'current_quantity': 10}]}

        response = get_expired_item_quantity_fridge(self.fridge_item, mock_time)

        self.assertEqual(response, 10)

    # tests the function returns 0 when there is no matching items
    def test_zero_expired_item_quantity(self):
        mock_time = time.time() - 999999
        self.fridge_item = {'item_list': [{'expiry_date': mock_time+999999, 'current_quantity': 10}]}

        response = get_expired_item_quantity_fridge(self.fridge_item, mock_time)

        self.assertEqual(response, 0)

    def test_multiple_expired_item_quantity(self):
        mock_time = time.time() - 999999
        self.fridge_item = {'item_list': [{'expiry_date': mock_time, 'current_quantity': 10},
                                          {'expiry_date': mock_time, 'current_quantity': 15},
                                          {'expiry_date': mock_time+999999, 'current_quantity': 1}]}

        response = get_expired_item_quantity_fridge(self.fridge_item, mock_time)

        self.assertEqual(response, 25)

class TestGetItemQuantityFridgeFunction(unittest.TestCase):
    # tests the function returns the correct quantity
    def test_normal_parameters(self):
        self.fridge_item = {'item_list': [{'expiry_date': time.time(), 'current_quantity': 10}]}

        response = get_item_quantity_fridge(self.fridge_item)

        self.assertEqual(response, 10)

    # tests the function returns 0 when there is no matching items
    def test_zero_item_quantity(self):
        self.fridge_item = {'item_list': [{'expiry_date': time.time() - 999999, 'current_quantity': 10}]}

        response = get_item_quantity_fridge(self.fridge_item)

        self.assertEqual(response, 0)


class TestGetItemQuantityOrdersFunction(unittest.TestCase):
    # tests the function returns the correct quantity
    def test_normal_parameters(self):
        order_items = [{'item_name': 'example_name', 'quantity': 10}]
        item_name = 'example_name'

        response = get_item_quantity_orders(order_items, item_name)

        self.assertEqual(response, 10)

    # tests the function returns 0 when there is no matching items
    def test_no_matching_item_name(self):
        order_items = [{'item_name': 'another_example_name', 'quantity': 10}]
        item_name = 'example_name'

        response = get_item_quantity_orders(order_items, item_name)

        self.assertEqual(response, 0)


class TestGetTotalItemQuantityFunction(unittest.TestCase):  # depends on previous two functions
    # tests the function returns the correct quantity
    def test_normal_parameters(self):
        fridge_item = {'item_list': [{'expiry_date': time.time(), 'current_quantity': 5}], 'item_name': 'example_name'}
        orders = [{'items': [{'item_name': 'example_name', 'quantity': 10}]}]

        response = get_total_item_quantity(fridge_item, orders)

        self.assertEqual(response, 15)

    # tests the function returns the correct quantity when there are no matching items in the order
    def test_only_fridge_item(self):
        fridge_item = {'item_list': [{'expiry_date': time.time(), 'current_quantity': 5}], 'item_name': 'example_name'}
        orders = [{'items': [{'item_name': 'another_example_name', 'quantity': 10}]}]

        response = get_total_item_quantity(fridge_item, orders)

        self.assertEqual(response, 5)


if __name__ == '__main__':
    unittest.main()
