import os
import boto3
import json
from boto3.dynamodb.conditions import Key
from datetime import datetime
import logging
from .utils import unix_to_readable, get_health_and_safety_email, get_filtered_items, send_email_with_attachment, create_csv_content

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    response = None

    try:
        master_db_name = os.environ.get('MASTER_DB')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(master_db_name)
        logger.info(f"Using database: {master_db_name}")

        body = event['body']
        restaurant_name = body['restaurant_name']
        start_date = int(datetime.strptime(body['startDate'], '%Y-%m-%d').timestamp())
        end_date = int(datetime.strptime(body['endDate'], '%Y-%m-%d').timestamp())
        logger.info(f"Querying for restaurant: {restaurant_name}, Start Date: {start_date}, End Date: {end_date}")
        
        email = get_health_and_safety_email(table, restaurant_name)
        if not email:
            raise ValueError("Health and safety email not found for the restaurant.")
            
        filtered_items = get_filtered_items(table, restaurant_name, start_date, end_date)
        csv_content = create_csv_content(filtered_items)
        send_email_with_attachment(email, restaurant_name, body['startDate'], body['endDate'], filtered_items)

        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Health and Safety Report Sent!',
                'csv_data': csv_content
            })
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        response = {
            'statusCode': 500,
            'body': json.dumps({'details': str(e)})
        }

    return response
