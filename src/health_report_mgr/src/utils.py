from datetime import datetime
import boto3
import logging
from boto3.dynamodb.conditions import Key, Attr
import io
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def unix_to_readable(timestamp):
    """
    Converts a UNIX timestamp to a readable date-time string.
    :param timestamp: UNIX timestamp.
    :return: Readable date-time string or empty string if timestamp is invalid.
    """
    if timestamp == 0 or timestamp is None:
        return ''
    return datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    
def get_health_and_safety_email(table, restaurant_name):
    """
    Retrieves the health and safety contact email for a given restaurant.
    :param table: DynamoDB table object.
    :param restaurant_name: Name of the restaurant.
    :return: Health and safety email address or None if not found.
    """
    try:
        admin_settings_response = table.get_item(
            Key={
                'pk': restaurant_name, 
                'type': 'admin_settings'
            }
        )
        admin_settings_item = admin_settings_response.get('Item', {})
        email = admin_settings_item.get('health_and_safety_email')
        logger.info(f"Health and Safety Email: {email}")
        return email
    except Exception as e:
        logger.error(f"Error getting health and safety email: {e}")
        return None

def get_filtered_items(table, restaurant_name, start_date, end_date):
    """
    Filters and retrieves items from DynamoDB based on date range and quantity.
    :param table: DynamoDB table object.
    :param restaurant_name: Name of the restaurant.
    :param start_date: Start of the date range (UNIX timestamp).
    :param end_date: End of the date range (UNIX timestamp).
    :return: List of filtered items.
    """
    database_response = table.query(
        KeyConditionExpression=Key('pk').eq(restaurant_name) & Key('type').eq('fridge')
    )
    data = database_response['Items']
    logger.info(f"Database response: {data}")

    filtered_items = []
    for item in data:
        for sub_item in item['items']:
            for detail in sub_item['item_list']:
                date_added = int(detail['date_added'])
                current_quantity = int(detail['current_quantity'])
                if start_date <= date_added <= end_date and current_quantity != 0:
                    filtered_item = {
                        'item_name': sub_item['item_name'],
                        'date_removed': unix_to_readable(detail['date_removed']),
                        'date_added': unix_to_readable(detail['date_added']),
                        'current_quantity': str(current_quantity),
                        'expiry_date': unix_to_readable(detail['expiry_date'])
                    }
                    filtered_items.append(filtered_item)
    return filtered_items


def create_csv_content(filtered_items):
    """
    Creates CSV content from a list of filtered items.
    :param filtered_items: List of items to include in the CSV.
    :return: String containing CSV formatted data.
    """
    logger.info("Creating CSV content from filtered items.")
    csv_output = io.StringIO()
    headers = ['Item Name', 'Date Removed', 'Date Added', 'Quantity', 'Expiry Date']
    writer = csv.writer(csv_output)
    writer.writerow(headers)
    
    for item in filtered_items:
        try:
            writer.writerow([
                item['item_name'],
                item['date_removed'],
                item['date_added'],
                item['current_quantity'],
                item['expiry_date']
            ])
        except Exception as e:
            logger.error(f"Error writing item to CSV: {item}, Error: {e}")
            continue
    
    csv_content = csv_output.getvalue()
    csv_output.close()
    logger.info("CSV content created successfully.")
    return csv_content

def send_email_with_attachment(email, restaurant_name, start_date, end_date, filtered_items):
    """
    Sends an email with the health and safety report as an attachment.
    :param email: Recipient's email address.
    :param restaurant_name: Name of the restaurant.
    :param start_date: Start date of the report.
    :param end_date: End date of the report.
    :param filtered_items: List of items to include in the report.
    """
    ses = boto3.client('ses')
    email_subject = f'Health & Safety Report for Restaurant: {restaurant_name}'
    email_body = f"Please find attached the Health & Safety Report for {restaurant_name} between {start_date} and {end_date}."

    msg = MIMEMultipart()
    msg['Subject'] = email_subject
    msg['From'] = 'no-reply@ffsmart.benlewisjones.com'
    msg['To'] = email

    msg.attach(MIMEText(email_body, 'plain'))

    csv_content = create_csv_content(filtered_items)
    part = MIMEApplication(csv_content, Name='report.csv')
    part['Content-Disposition'] = 'attachment; filename="report.csv"'
    msg.attach(part)

    ses.send_raw_email(
        Source=msg['From'],
        Destinations=[msg['To']],
        RawMessage={'Data': msg.as_string()}
    )
    logger.info("Email with attachment sent successfully")
