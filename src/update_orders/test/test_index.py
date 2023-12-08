import unittest
from unittest.mock import patch
from src.index import handler


class TestPost(unittest.TestCase):

    def test_example(self):
        mock_event = {}
        mock_context = {}

        response = handler(mock_event, mock_context)

        expected_response = {
            'statusCode': 200,
            'body': {
                'details': 'function works',
            }
        }

        self.assertEqual(response, expected_response)
