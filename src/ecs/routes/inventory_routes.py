from datetime import datetime
import time

from flask import (
    Blueprint, 
    redirect, 
    url_for, 
    json,
    flash, 
    request,
    render_template)

from lib.utils import (
    get_user_role, 
    get_restaurant_id
)
from lib.globals import (
    fridge_mgr_lambda,
    lambda_client, 
    cognito_client,
    logger,
    flask_session as session
)

inventory_route = Blueprint('inventory', __name__)

@inventory_route.route('/inventory')
def inventory():
    try:
        restaurant_name = get_restaurant_id(cognito_client, session['access_token'])
        
        lambda_payload = {
            "httpMethod": "POST",
            "action": "view_inventory",
            "body": {
                "restaurant_name": restaurant_name
            }
        }
        
        response = lambda_client.invoke(
            FunctionName=fridge_mgr_lambda,
            InvocationType='RequestResponse',
            Payload=json.dumps(lambda_payload)
        )

        response_payload = json.loads(response['Payload'].read())
        if response_payload['statusCode'] == 200:
            items = response_payload['body']['additional_details']['items']
            is_front_door_open = response_payload['body']['additional_details']['is_front_door_open']
            
            for item in items:
                for detail in item['item_list']:
                    detail['expiry_date'] = datetime.fromtimestamp(detail['expiry_date']).strftime('%Y-%m-%d')
                    
            return render_template('inventory.html', 
                    user_role=get_user_role(cognito_client, session['access_token'], lambda_client, session['username']), 
                    items=items, 
                    is_front_door_open=is_front_door_open)
        else:
            logger.error(f"Lambda function error: {response_payload}")
            flash('Error fetching inventory data', 'error')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash('Error fetching inventory data', 'error')

    return render_template('inventory.html', 
            user_role=get_user_role(cognito_client, session['access_token'], lambda_client, session['username']), 
            items=[])


@inventory_route.route('/add-item', methods=['POST'])
def add_item():    
    item_name = request.form.get('item_name')
    quantity_change = request.form.get('quantity_change', 0)
    desired_quantity = request.form.get('desired_quantity', 0)

    try:
        expiry_date_str = request.form.get('expiry_date')
        expiry_date = int(time.mktime(datetime.strptime(expiry_date_str, '%Y-%m-%d').timetuple()))
        restaurant_name = get_restaurant_id(cognito_client, session['access_token'])

        lambda_payload = {
            "httpMethod": "POST",
            "action": "add_item",
            "body": {
                "restaurant_name": restaurant_name,
                "item_name": item_name,
                "quantity_change": int(quantity_change),
                "expiry_date": int(expiry_date),
                "desired_quantity": int(desired_quantity) if desired_quantity else None
            }
        }

        response = lambda_client.invoke(
            FunctionName=fridge_mgr_lambda,
            InvocationType='RequestResponse',
            Payload=json.dumps(lambda_payload)
        )

        response_payload = json.loads(response['Payload'].read())
        if response_payload['statusCode'] == 200:
            flash('Item added successfully!', 'success')
        else:
            flash(f"Failed to add item: {response_payload['body']['details']}", 'error')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash('Error adding item', 'error')

    return redirect(url_for('inventory.inventory'))


@inventory_route.route('/delete-item', methods=['POST'])
def delete_item():
    item_name = request.form.get('item_name')
    logger.info(f"Received delete request for item: {item_name}")

    try:
        expiry_date_str = request.form.get('expiry_date')
        expiry_date = int(time.mktime(datetime.strptime(expiry_date_str, '%Y-%m-%d').timetuple()))
        quantity_change = int(request.form.get('quantity_change'))
        logger.info(f"Request details - Item name: {item_name}, Expiry Date: {expiry_date_str}, Quantity Change: {quantity_change}")
        restaurant_name = get_restaurant_id(cognito_client, session['access_token'])

        lambda_payload = {
            "httpMethod": "POST",
            "action": "delete_item",
            "body": {
                "restaurant_name": restaurant_name,
                "item_name": item_name,
                "quantity_change": quantity_change,
                "expiry_date": expiry_date
            }
        }

        response = lambda_client.invoke(
            FunctionName=fridge_mgr_lambda,
            InvocationType='RequestResponse',
            Payload=json.dumps(lambda_payload)
        )

        response_payload = json.loads(response['Payload'].read())
        logger.info(f"Lambda response: {response_payload}")

        if response_payload['statusCode'] == 200:
            flash('Item deleted successfully!', 'success')
        else:
            flash(f"Failed to delete item: {response_payload['body']['details']}", 'error')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash('Error deleting item', 'error')

    return redirect(url_for('inventory.inventory'))


@inventory_route.route('/update-item', methods=['POST'])
def update_item():
    item_name = request.form.get('item_name')
    expiry_date_str = request.form.get('expiry_date')
    quantity_change = int(request.form.get('quantity_change'))
    logger.info(f"Received update request for item: {item_name}, Expiry Date: {expiry_date_str}, Quantity Change: {quantity_change}")
    restaurant_name = get_restaurant_id(cognito_client, session['access_token'])

    try:
        expiry_date = int(time.mktime(datetime.strptime(expiry_date_str, '%Y-%m-%d').timetuple()))

        lambda_payload = {
            "httpMethod": "POST",
            "action": "update_item",
            "body": {
                "restaurant_name": restaurant_name,
                "item_name": item_name,
                "quantity_change": quantity_change,
                "expiry_date": expiry_date
            }
        }

        logger.info(f"Lambda payload: {lambda_payload}")

        response = lambda_client.invoke(
            FunctionName=fridge_mgr_lambda,
            InvocationType='RequestResponse',
            Payload=json.dumps(lambda_payload)
        )

        response_payload = json.loads(response['Payload'].read())
        logger.info(f"Lambda response: {response_payload}")

        if response_payload['statusCode'] == 200:
            flash('Item updated successfully!', 'success')
        else:
            flash(f"Failed to update item: {response_payload['body']['details']}", 'error')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash('Error updating item', 'error')

    return redirect(url_for('inventory.inventory'))


@inventory_route.route('/open_door', methods=['POST'])
def open_door():
    
    restaurant_name = get_restaurant_id(cognito_client, session['access_token'])

    lambda_payload = {
        "httpMethod": "POST",
        "action": "open_door",
        "body": {
            "restaurant_name": restaurant_name,
            "is_front_door_open": True,
            "is_back_door_open": False
        }
    }
    response = lambda_client.invoke(
        FunctionName=fridge_mgr_lambda,
        InvocationType='RequestResponse',
        Payload=json.dumps(lambda_payload)
    )
    return redirect(url_for('inventory.inventory'))


@inventory_route.route('/close_door', methods=['POST'])
def close_door():
    
    restaurant_name = get_restaurant_id(cognito_client, session['access_token'])
    
    lambda_payload = {
        "httpMethod": "POST",
        "action": "close_door",
        "body": {
            "restaurant_name": restaurant_name
        }
    }
    response = lambda_client.invoke(
        FunctionName=fridge_mgr_lambda,
        InvocationType='RequestResponse',
        Payload=json.dumps(lambda_payload)
    )
    return redirect(url_for('inventory.inventory'))