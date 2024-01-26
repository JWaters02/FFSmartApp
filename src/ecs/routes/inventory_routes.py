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
    get_restaurant_id,
    make_lambda_request
)
from lib.globals import (
    fridge_mgr_lambda,
    lambda_client, 
    cognito_client,
    logger,
    flask_session as session
)

inventory_route = Blueprint('inventory', __name__)

@inventory_route.before_request
def before_request():
    if not session.get('access_token'):
        return redirect(url_for('index'))
    
    if get_user_role(cognito_client, session['access_token'], lambda_client, session['username']) == 'None':
        return redirect(url_for('error_404'))

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

        response = make_lambda_request(lambda_client, lambda_payload, fridge_mgr_lambda)
        if response['statusCode'] == 200:
            items = response['body']['additional_details']['items']
            is_front_door_open = response['body']['additional_details']['is_front_door_open']
            today = datetime.now().date()

            for item in items:
                # Convert expiry_date from timestamp to date object for comparison
                for detail in item['item_list']:
                    expiry_date = datetime.fromtimestamp(detail['expiry_date']).date()
                    detail['is_expired'] = expiry_date < today
                    detail['expiry_date_formatted'] = expiry_date.strftime('%Y-%m-%d')
                
                # Calculate the total non-expired quantity
                item['total_non_expired_quantity'] = sum(
                    detail['current_quantity'] for detail in item['item_list']
                    if not detail['is_expired']
                )

                # Determine if an order is needed for non-expired items
                item['is_order_needed'] = item['total_non_expired_quantity'] < item['desired_quantity']

                for detail in item['item_list']:
                    # Show quantity buttons if the current quantity is greater than 0
                    detail['show_quantity_buttons'] = detail['current_quantity'] > 0

                    # Determine if no order is required for expired items
                    detail['no_order_required'] = detail['is_expired'] and item['total_non_expired_quantity'] >= item['desired_quantity']

            return render_template('inventory.html', 
                    user_role=get_user_role(cognito_client, session['access_token'], lambda_client, session['username']), 
                    items=items, 
                    is_front_door_open=is_front_door_open)
        else:
            logger.error(f"Lambda function error: {response}")
            flash('Error fetching inventory data', 'error')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash('Error fetching inventory data', 'error')

    return render_template('inventory.html', 
            user_role=get_user_role(cognito_client, session['access_token'], lambda_client, session['username']), 
            items=[])


@inventory_route.route('/delete-item', methods=['POST'])
def delete_item():
    item_name = request.form.get('item_name')

    try:
        expiry_date = int(request.form.get('expiry_date'))
        current_quantity = int(request.form.get('current_quantity'))
        restaurant_name = get_restaurant_id(cognito_client, session['access_token'])

        lambda_payload = {
            "httpMethod": "POST",
            "action": "delete_item",
            "body": {
                "restaurant_name": restaurant_name,
                "item_name": item_name,
                "current_quantity": current_quantity,
                "expiry_date": expiry_date
            }
        }

        response = make_lambda_request(lambda_client, lambda_payload, fridge_mgr_lambda)
        if response['statusCode'] == 200:
            flash('Item deleted successfully!', 'success')
        else:
            flash(f"Failed to delete item: {response['body']['details']}", 'error')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash('Error deleting item', 'error')

    return redirect(url_for('inventory.inventory'))


@inventory_route.route('/update-item', methods=['POST'])
def update_item():
    item_name = request.form.get('item_name')
    expiry_date = int(request.form.get('expiry_date'))
    quantity_change = int(request.form.get('quantity_change'))
    restaurant_name = get_restaurant_id(cognito_client, session['access_token'])

    try:
        lambda_payload = {
            "httpMethod": "POST",
            "action": "update_item_quantity",
            "body": {
                "restaurant_name": restaurant_name,
                "item_name": item_name,
                "quantity_change": quantity_change,
                "expiry_date": expiry_date
            }
        }

        response = make_lambda_request(lambda_client, lambda_payload, fridge_mgr_lambda)
        if response['statusCode'] == 200:
            flash('Item updated successfully!', 'success')
        else:
            flash(f"Failed to update item: {response['body']['details']}", 'error')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash('Error updating item', 'error')

    return redirect(url_for('inventory.inventory'))


@inventory_route.route('/update-desired-quantity', methods=['POST'])
def update_desired_quantity():
    item_name = request.form.get('item_name')
    desired_quantity = int(request.form.get('desired_quantity'))
    logger.info(f"Received update desired quantity request for item: {item_name}, Desired Quantity: {desired_quantity}")

    if not validate_inputs(item_name, desired_quantity):
        return redirect(url_for('inventory.inventory'))

    restaurant_name = get_restaurant_id(cognito_client, session['access_token'])
    try:
        lambda_payload = {
            "httpMethod": "POST",
            "action": "update_desired_quantity",
            "body": {
                "restaurant_name": restaurant_name,
                "item_name": item_name,
                "desired_quantity": desired_quantity
            }
        }

        logger.info(f"Lambda payload: {lambda_payload}")

        response = make_lambda_request(lambda_client, lambda_payload, fridge_mgr_lambda)
        logger.info(f"Lambda response: {response}")

        if response['statusCode'] == 200:
            flash('Desired quantity updated successfully!', 'success')
        else:
            flash(f"Failed to update desired quantity: {response['body']['details']}", 'error')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash('Error updating desired quantity', 'error')

    return redirect(url_for('inventory.inventory'))


@inventory_route.route('/add-item', methods=['POST'])
def add_item():
    item_name = request.form.get('add_item_name')
    expiry_date_str = datetime.now().strftime('%Y-%m-%d')
    desired_quantity = int(request.form.get('add_desired_quantity'))

    if not validate_inputs(item_name, desired_quantity):
        return redirect(url_for('inventory.inventory'))

    restaurant_name = get_restaurant_id(cognito_client, session['access_token'])

    try:
        expiry_date = int(time.mktime(datetime.strptime(expiry_date_str, '%Y-%m-%d').timetuple()))

        lambda_payload = {
            "httpMethod": "POST",
            "action": "add_new_item",
            "body": {
                "restaurant_name": restaurant_name,
                "item_name": item_name,
                "expiry_date": expiry_date,
                "desired_quantity": desired_quantity
            }
        }

        response = make_lambda_request(lambda_client, lambda_payload, fridge_mgr_lambda)
        if response['statusCode'] == 200:
            flash('Item added successfully! Your item will show in the next order.', 'success')
        elif response['statusCode'] == 409:
            flash('Item already exists', 'warning')
        else:
            flash(f"Failed to add item: {response['body']['details']}", 'error')

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash('Error adding item', 'error')

    return redirect(url_for('inventory.inventory'))


@inventory_route.route('/open_door', methods=['POST'])
def open_door():
    restaurant_name = get_restaurant_id(cognito_client, session['access_token'])

    lambda_payload = {
        "httpMethod": "POST",
        "action": "open_front_door",
        "body": {
            "restaurant_name": restaurant_name
        }
    }

    response = make_lambda_request(lambda_client, lambda_payload, fridge_mgr_lambda)
    if response['statusCode'] != 200:
        flash(f"Failed to open door: {response['body']['details']}", 'error')
    return redirect(url_for('inventory.inventory'))


@inventory_route.route('/close_door', methods=['POST'])
def close_door():
    restaurant_name = get_restaurant_id(cognito_client, session['access_token'])
    
    lambda_payload = {
        "httpMethod": "POST",
        "action": "close_front_door",
        "body": {
            "restaurant_name": restaurant_name
        }
    }
    response = make_lambda_request(lambda_client, lambda_payload, fridge_mgr_lambda)
    print(response)
    if response['statusCode'] != 200:
        flash(f"Failed to close door: {response['body']['details']}", 'error')
    return redirect(url_for('inventory.inventory'))


def validate_inputs(item_name, desired_quantity):
    if not item_name or item_name == '':
        flash('Item name must be specified', 'error')
        return False
    if len(item_name) > 20:
        flash('Item name must 20 characters or less', 'error')
        return False
    if not desired_quantity:
        flash('Desired quantity must be specified', 'error')
        return False
    if desired_quantity < 1:
        flash('Desired quantity must be greater than 0', 'error')
        return False
    return True