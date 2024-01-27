import unittest
import time
import secrets
from unittest.mock import patch, MagicMock
from src.index import handler
from src.delete import delete_order, ClientError
from src.post import create_order, NotFoundException, order_check
from src.post import create_order, NotFoundException
from src.get import get_all_orders, get_order
from src.custom_exceptions import BadRequestException
from src.utils import (generate_order_id, is_order_id_valid, get_expired_item_quantity_fridge, get_item_quantity_fridge,
                       get_item_quantity_orders, get_total_item_quantity)


class TestDynamoDBHandler(unittest.TestCase):
    @patch('boto3.resource')
    def test_handler_function(self, mock_boto3_resource):
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


class TestDeleteOrderLambda(unittest.TestCase):
    # Explaination here for what the test is actually doing in general
    def setUp(self):
        self.event = {
            'body': {
                'restaurant_id': 'example_restaurant',
                'order_id': 'example_order'
            }
        }
        self.table = MagicMock()

    # Explaination here for what the test is actually doing in general
    def test_delete_order_successful(self):
        # Mocking DynamoDB response
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'orders',
                'orders': [{'id': 'existing_order'}, {'id': 'example_order'}]
            }
        }

        response = delete_order(self.event, self.table)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(self.table.update_item.call_count, 1)

    # Explaination here for what the test is actually doing in general
    def test_delete_order_not_found(self):
        # Mocking DynamoDB response for non-existent restaurant
        self.table.get_item.return_value = {}

        response = delete_order(self.event, self.table)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Restaurant does not exist', response['body'])

    # Explaination here for what the test is actually doing in general
    def test_delete_order_invalid_order_id(self):
        # Mocking DynamoDB response with a different order_id
        self.table.get_item.return_value = {
            'Item': {
                'pk': 'example_restaurant',
                'type': 'orders',
                'orders': [{'id': 'another_order'}, {'id': 'yet_another_order'}]
            }
        }

        response = delete_order(self.event, self.table)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Order does not exist', response['body'])

    # Explaination here for what the test is actually doing in general
    def test_dynamodb_error(self):
        # Mocking DynamoDB ClientError
        self.table.get_item.side_effect = ClientError({'Error': {'Code': 'TestException'}},
                                                      'operation_name')

        response = delete_order(self.event, self.table)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error accessing DynamoDB', response['body'])


class TestCreateOrderFunction(unittest.TestCase):
    # Explaination here for what the test is actually doing in general
    def setUp(self):
        self.dynamodb_client = MagicMock()
        self.table = MagicMock()
        self.restaurant_name = 'example_restaurant'
        self.order_items = [{'item_id': 'item1', 'quantity': 2}, {'item_id': 'item2', 'quantity': 3}]
        self.expired_items = [{'item_id': 'expired_item', 'quantity': 1}]
        self.table_name = 'example_table'

    # Explaination here for what the test is actually doing in general
    def test_create_order_successful(self):
        with patch('src.post.generate_order_id', return_value='example_order_id'):
            response = create_order(self.dynamodb_client, self.table, self.restaurant_name, self.order_items,
                                    self.expired_items, self.table_name)

        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(response['body']['order_id'], 'example_order_id')
        self.assertEqual(response['body']['expired_items'], self.expired_items)

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

    # Explaination here for what the test is actually doing in general
    def test_create_order_not_found_exception(self):
        with patch('src.post.generate_order_id', return_value='example_order_id'):
            self.table.update_item.side_effect = NotFoundException('Restaurant does not exist')
            response = create_order(self.dynamodb_client, self.table, self.restaurant_name, self.order_items,
                                    self.expired_items, self.table_name)

        self.assertEqual(response['statusCode'], 404)

    # Explaination here for what the test is actually doing in general
    def test_create_order_client_error_exception(self):
        with patch('src.post.generate_order_id', return_value='example_order_id'):
            self.table.update_item.side_effect = ClientError({'Error': {'Code': 'TestException'}}, 'operation_name')
            response = create_order(self.dynamodb_client, self.table, self.restaurant_name, self.order_items,
                                    self.expired_items, self.table_name)

        self.assertEqual(response['statusCode'], 500)

class TestOrderCheck(unittest.TestCase):

    @patch('src.post.get_total_item_quantity')
    @patch('src.post.get_expired_item_quantity_fridge')
    @patch('src.post.create_order')
    # Explaination here for what the test is actually doing in general
    def test_order_needed(self, mock_create_order, mock_expired_quantity, mock_total_quantity):
        def test_order_needed(self, mock_create_order, mock_expired_quantity, mock_total_quantity):
            mock_table = MagicMock()
            mock_dynamodb_client = MagicMock()
            mock_event = {'body': {'restaurant_id': 'restaurant_id'}}
            mock_table_name = 'your_table_name'

            fridge_response = {
                'Items': [
                    {'item_name': 'item1', 'desired_quantity': 10,
                     'items': [{'expiry_date': '2024-01-01', 'current_quantity': 5}]}
                ]
            }

            orders_response = {
                'Items': [
                    {'item_name': 'item1', 'orders': [{'expiry_date': '2024-01-01', 'quantity': 2}]}
                ]
            }

            mock_table.query.side_effect = [fridge_response, orders_response]

            result = order_check(mock_dynamodb_client, mock_event, mock_table, mock_table_name)

            mock_total_quantity.assert_called_once_with(
                {'item_name': 'item1', 'desired_quantity': 10,
                 'items': [{'expiry_date': '2024-01-01', 'current_quantity': 5}]},
                [{'item_name': 'item1', 'orders': [{'expiry_date': '2024-01-01', 'quantity': 2}]}]
            )
            mock_expired_quantity.assert_called_once_with(
                {'item_name': 'item1', 'desired_quantity': 10,
                 'items': [{'expiry_date': '2024-01-01', 'current_quantity': 5}]}
            )
            mock_create_order.assert_called_once_with(
                mock_dynamodb_client, mock_table,
                'restaurant_id', [{'M': {'item_name': {'S': 'item1'}, 'quantity': {'N': '3'}}}], [], mock_table_name
            )

            self.assertEqual(result['statusCode'], 201)


class TestGetAllOrdersFunction(unittest.TestCase):
    def test_normal_parameters(self):
        event = {'body': {'restaurant_id': 'example_restaurant'}}
        self.table = MagicMock()

        response = get_all_orders(event, self.table)

        self.assertEqual(response['statusCode'], 200)

    def test_event_missing_body(self):
        event = {'example': 'example'}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            get_all_orders(event, self.table)
        self.assertEqual(str(context.exception), 'Bad request restaurant_id not found in body.')

    def test_event_missing_restaurant_id(self):
        event = {'body': {'example': 'example'}}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            get_all_orders(event, self.table)
        self.assertEqual(str(context.exception), 'Bad request restaurant_id not found in body.')

    def test_key_error(self):
        event = {'body': {'restaurant_id': 'example_restaurant'}}
        self.table = MagicMock()
        self.table.query.side_effect = KeyError()

        response = get_all_orders(event, self.table)

        self.assertEqual(response['statusCode'], 404)

    def test_client_error(self):
        event = {'body': {'restaurant_id': 'example_restaurant'}}
        self.table = MagicMock()
        self.table.query.side_effect = ClientError(error_response={'Error': {'Code': 'TestException'}},
                                                   operation_name='query')

        response = get_all_orders(event, self.table)

        self.assertEqual(response['statusCode'], 500)


class TestGetOrderFunction(unittest.TestCase):
    def test_normal_parameters(self):
        event = {'body': {'restaurant_id': 'example_restaurant', 'order_id': 'example_id'}}
        self.table = MagicMock()

        response = get_order(event, self.table)

        self.assertEqual(response['statusCode'], 200)

    def test_event_missing_body(self):
        event = {'example': 'example'}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            get_order(event, self.table)
        self.assertEqual(str(context.exception), 'Bad request restaurant_id not found in body.')

    def test_event_missing_restaurant_id(self):
        event = {'body': {'order_id': 'example_id'}}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            get_order(event, self.table)
        self.assertEqual(str(context.exception), 'Bad request restaurant_id not found in body.')

    def test_event_missing_order_id(self):
        event = {'body': {'restaurant_id': 'example_restaurant'}}
        self.table = MagicMock()

        with self.assertRaises(BadRequestException) as context:
            get_order(event, self.table)
        self.assertEqual(str(context.exception), 'Bad request order_id not found in body.')

    def test_key_error(self):
        event = {'body': {'restaurant_id': 'example_restaurant', 'order_id': 'example_id'}}
        self.table = MagicMock()
        self.table.query.side_effect = KeyError()

        response = get_order(event, self.table)

        self.assertEqual(response['statusCode'], 404)

    def test_client_error(self):
        event = {'body': {'restaurant_id': 'example_restaurant', 'order_id': 'example_id'}}
        self.table = MagicMock()
        self.table.query.side_effect = ClientError(error_response={'Error': {'Code': 'TestException'}},
                                                   operation_name='query')

        response = get_order(event, self.table)

        self.assertEqual(response['statusCode'], 500)


class TestGenerateOrderIdFunction(unittest.TestCase):
    @patch('src.utils.secrets')
    def test_normal_parameters(self, mock_secrets):
        self.table = MagicMock()
        restaurant_id = 'example_restaurant'
        mock_secrets.randbits.return_value = 1234567890123456

        response = generate_order_id(self.table, restaurant_id)

        self.assertEqual(response, '1234567890123456')

    def test_missing_restaurant_id(self):
        self.table = MagicMock()
        restaurant_id = 'example_restaurant'
        self.table.get_item.return_value = {'example': 'example'}

        with self.assertRaises(NotFoundException) as context:
            generate_order_id(self.table, restaurant_id)
        self.assertEqual(str(context.exception), 'Restaurant does not exist.')


class TestIsOrderIdValidFunction(unittest.TestCase):
    def test_id_valid(self):
        order_id = 1234567890123456
        self.item = MagicMock()

        response = is_order_id_valid(order_id, self.item)

        self.assertEqual(response, True)

    def test_id_invalid(self):
        order_id = 1234567890123456
        self.item = {'orders': [{'id': 1234567890123456}]}

        response = is_order_id_valid(order_id, self.item)

        self.assertEqual(response, False)


class TestGetExpiredItemQuantityFridgeFunction(unittest.TestCase):
    def test_normal_parameters(self):
        self.fridge_item = {'item_list': [{'expiry_date': time.time()-999999, 'current_quantity': 10}]}

        response = get_expired_item_quantity_fridge(self.fridge_item)

        self.assertEqual(response, 10)

    def test_zero_expired_item_quantity(self):
        self.fridge_item = {'item_list': [{'expiry_date': time.time(), 'current_quantity': 10}]}

        response = get_expired_item_quantity_fridge(self.fridge_item)

        self.assertEqual(response, 0)


class TestGetItemQuantityFridgeFunction(unittest.TestCase):
    def test_normal_parameters(self):
        self.fridge_item = {'item_list': [{'expiry_date': time.time(), 'current_quantity': 10}]}

        response = get_item_quantity_fridge(self.fridge_item)

        self.assertEqual(response, 10)

    def test_zero_item_quantity(self):
        self.fridge_item = {'item_list': [{'expiry_date': time.time() - 999999, 'current_quantity': 10}]}

        response = get_item_quantity_fridge(self.fridge_item)

        self.assertEqual(response, 0)


class TestGetItemQuantityOrdersFunction(unittest.TestCase):
    def test_normal_parameters(self):
        order_items = [{'item_name': 'example_name', 'quantity': 10}]
        item_name = 'example_name'

        response = get_item_quantity_orders(order_items, item_name)

        self.assertEqual(response, 10)

    def test_no_matching_item_name(self):
        order_items = [{'item_name': 'another_example_name', 'quantity': 10}]
        item_name = 'example_name'

        response = get_item_quantity_orders(order_items, item_name)

        self.assertEqual(response, 0)


class TestGetTotalItemQuantityFunction(unittest.TestCase):  # depends on previous two functions
    def test_normal_parameters(self):
        fridge_item = {'item_list': [{'expiry_date': time.time(), 'current_quantity': 5}], 'item_name': 'example_name'}
        orders = [{'items': [{'item_name': 'example_name', 'quantity': 10}]}]

        response = get_total_item_quantity(fridge_item, orders)

        self.assertEqual(response, 15)

    def test_only_fridge_item(self):
        fridge_item = {'item_list': [{'expiry_date': time.time(), 'current_quantity': 5}], 'item_name': 'example_name'}
        orders = [{'items': [{'item_name': 'another_example_name', 'quantity': 10}]}]

        response = get_total_item_quantity(fridge_item, orders)

        self.assertEqual(response, 5)


if __name__ == '__main__':
    unittest.main()