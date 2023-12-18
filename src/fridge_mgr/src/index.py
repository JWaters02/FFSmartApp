import os
import boto3
import logging
import time

# initialize logger for additional info
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        #sets the initial dynamo table name using the env variables
        master_db_name = os.environ.get('MASTER_DB')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(master_db_name)
        
        #extractss the parameters from the event
        restaurant_name = event.get('restaurant_name')
        action = event.get('action')

        item_name = event.get('item_name')
        quantity_change = event.get('quantity_change', 0)
        expiry_date = event.get('expiry_date')
        
        #completes actions based on the action type by calling function
        if action in ["add_item", "update_item", "delete_item"]:
            response = manage_inventory(table, restaurant_name, item_name, quantity_change, expiry_date, action)
        else:
            #used to raise errors if non-existing action used
            raise ValueError(f"Invalid action specified: {action}")
        
        #returns the response
        return response
    except Exception as e:
        #catches the error and logs it and returns a 500
        logger.error(f"An error occurred: {str(e)}")
        return generate_response(500, f"An error occurred: {str(e)}")

def manage_inventory(table, restaurant_name, item_name, quantity_change, expiry_date, action):
    #function used to complete actions
    try:
        #gets the current UNIX timestamp for date_added
        current_time = int(time.time())
        
        #GETs the current state of the inventory for a given resturant and type
        response = table.get_item(
            Key={
                'restaurant_name': restaurant_name,
                'type': 'fridge'
            }
        )
        item = response.get('Item')
        
        #adds a new item if the item does not exist
        if not item:
            if action == "add_item":
                # initialize the item structure if it doesn't exist
                item = {
                    'restaurant_name': restaurant_name,
                    'type': 'fridge',
                    'items': [{
                        'item_name': item_name,
                        'desired_quantity': quantity_change,
                        'item_list': [{
                            'current_quantity': quantity_change,
                            'expiry_date': expiry_date,
                            'date_added': current_time,
                            'date_removed': 0
                        }]
                    }]
                }
            else:
                return generate_response(404, 'Item not found')
        
        # logic for the update item to update the existing or if the item already exists to update it
        if action in ["add_item", "update_item"]:
            #code searches for an existing inventory item matching the given name and expiry date and updates its quantity, or flags if no such item is found.
            item_found = False
            if 'items' in item:
                for stored_item in item['items']:
                    if stored_item['item_name'] == item_name:
                        for item_detail in stored_item['item_list']:
                            if item_detail['expiry_date'] == expiry_date:
                                item_detail['current_quantity'] += quantity_change
                                item_found = True
                                break
                        if item_found:
                            break
            
            if not item_found:
                # add new item if not found
                new_item_entry = {
                    'current_quantity': quantity_change,
                    'expiry_date': expiry_date,
                    'date_added': current_time,
                    'date_removed': 0
                }
                item['items'].append({
                    'item_name': item_name,
                    'desired_quantity': quantity_change,
                    'item_list': [new_item_entry]
                })
        
        #logic for deleting the items
        elif action == "delete_item":
            # Delete item logic
            for stored_item in item.get('items', []):
                if stored_item['item_name'] == item_name:
                    stored_item['item_list'] = [d for d in stored_item['item_list'] if d['expiry_date'] != expiry_date]
            
            # remove the item entirely if its item_list is empty
            item['items'] = [i for i in item['items'] if i['item_list']]
            
            # check if the items list is empty after deletion
            if not item['items']:
                # Delete the entire DynamoDB record if items list is empty
                table.delete_item(Key={'restaurant_name': restaurant_name, 'type': 'fridge'})
                return generate_response(200, 'Entire record deleted successfully', {})
        
        #updates to put the item in the table
        #boto3 internally converts this json dictionary into the DynamoDB json format
        table.put_item(Item=item)
        return generate_response(200, f'Inventory {action} successful', item)
    except Exception as e:
        #logs and returns any errors during inv management.
        logger.error(f"An error occurred during DynamoDB update: {str(e)}")
        return generate_response(500, f"An error occurred during DynamoDB update: {str(e)}")

def generate_response(status_code, message, additional_details=None):
    #used to create that structured HTTP response
    body = {'details': message}
    if additional_details:
        body['additional_details'] = additional_details
    return {
        'statusCode': status_code,
        'body': body
    }
