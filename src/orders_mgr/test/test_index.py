import unittest
import time
from unittest.mock import patch, MagicMock
from src.index import handler
from src.delete import delete_order, ClientError
from src.post import create_order, NotFoundException, order_check
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


class TestDeleteOrderLambda(unittest.TestCase):

    def setUp(self):
        self.event = {
            'body': {
                'restaurant_id': 'example_restaurant',
                'order_id': 'example_order'
            }
        }
        self.table = MagicMock()

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

    def test_delete_order_not_found(self):
        # Mocking DynamoDB response for non-existent restaurant
        self.table.get_item.return_value = {}

        response = delete_order(self.event, self.table)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Restaurant does not exist', response['body'])

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

    def test_dynamodb_error(self):
        # Mocking DynamoDB ClientError
        self.table.get_item.side_effect = ClientError({'Error': {'Code': 'TestException'}},
                                                      'operation_name')

        response = delete_order(self.event, self.table)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error accessing DynamoDB', response['body'])


class TestCreateOrderFunction(unittest.TestCase):

    def setUp(self):
        self.dynamodb_client = MagicMock()
        self.table = MagicMock()
        self.restaurant_name = 'example_restaurant'
        self.order_items = [{'item_id': 'item1', 'quantity': 2}, {'item_id': 'item2', 'quantity': 3}]
        self.expired_items = [{'item_id': 'expired_item', 'quantity': 1}]
        self.table_name = 'example_table'

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

    def test_create_order_not_found_exception(self):
        with patch('src.post.generate_order_id', return_value='example_order_id'):
            self.table.update_item.side_effect = NotFoundException('Restaurant does not exist')
            response = create_order(self.dynamodb_client, self.table, self.restaurant_name, self.order_items,
                                    self.expired_items, self.table_name)

        self.assertEqual(response['statusCode'], 404)

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


if __name__ == '__main__':
    unittest.main()