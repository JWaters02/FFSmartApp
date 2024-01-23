from datetime import datetime
import time
from flask import (
    Blueprint, 
    redirect, 
    url_for, 
    json,
    jsonify, 
    flash,
    make_response,
    request,
    render_template)

from lib.utils import (
    get_order_data,
    validate_token,
    make_lambda_request
)
from lib.globals import (
    fridge_mgr_lambda,
    order_mgr_lambda,
    token_mgr_lambda,
    lambda_client,
    flask_session as session
)

delivery_route = Blueprint('delivery', __name__)

@delivery_route.route('/delivery/<restaurant_id>/<token>/', methods=['GET', 'POST', 'PATCH'])
def delivery(restaurant_id, token):
    if not validate_token(token, lambda_client, restaurant_id, token_mgr_lambda): return redirect(url_for('error_404'))
    
    order_data = get_order_data(lambda_client, order_mgr_lambda, restaurant_id)
    print(order_data)

    if request.method == 'PATCH':
        door_data = request.json
        if door_data['is_back_door_open']:
            open_door(restaurant_id)
        else:
            close_door(restaurant_id)
        return make_response(jsonify({'success': True}), 200)

    return render_template('delivery.html', 
            order_data=order_data, 
            restaurant_id=restaurant_id, 
            token=token,
            is_back_door_open=session.get('is_back_door_open', False))


@delivery_route.route('/delivery/complete_order/<restaurant_id>/<token>/', methods=['POST'])
def complete_order(restaurant_id, token):
    if not validate_token(token, lambda_client, restaurant_id, token_mgr_lambda): return redirect(url_for('error_404'))
    
    submitted_data = request.json['items']
    print(submitted_data)

    # If any order expiry dates are before tomorrow or don't exist, don't complete
    for item in submitted_data:
        if item['expiry_date'] is None:
            return jsonify({'success': False, 'message': 'Expiry date must be specified'}), 400
        if item['expiry_date'] < int(time.time()):
            return jsonify({'success': False, 'message': 'Expiry date cannot be for the past'}), 400

    order_data = get_order_data(lambda_client, order_mgr_lambda, restaurant_id)
    print(order_data)

    success, discrepancies = compare_order_data(order_data, submitted_data)

    if not success:
        return jsonify({'success': False, 'message': discrepancies}), 400

    # If all items match, add the item to the inventory
    if not add_items(restaurant_id, submitted_data):
        return jsonify({'success': False, 'message': 'Failed to add items to inventory'}), 400

    # And delete the orders
    order_ids = [order['id'] for order in order_data]
    if not delete_orders(restaurant_id, order_ids):
        return jsonify({'success': False, 'message': 'Failed to delete orders'}), 400
    
    # And close the door
    close_door(restaurant_id)

    return jsonify({'success': True, 'message': 'Order completed successfully'})

@delivery_route.route('/delivery/end_delivery/<restaurant_id>/<token>/', methods=['POST'])
def delete_token(restaurant_id, token):
    payload = {
        "httpMethod": "DELETE",
        "action": "delete_token",
        "body": {
            "restaurant_id": restaurant_id,
            "request_token": token
        }
    }

    response = make_lambda_request(lambda_client, payload, token_mgr_lambda)
    if response['statusCode'] != 200:
        flash(f"Failed to delete token: {response}", 'error')
        return redirect(url_for('delivery.delivery', restaurant_id=restaurant_id, token=token))
    return redirect(url_for('error_404'))


def compare_order_data(expected, submitted):
    discrepancies = []
    success = True

    for item in submitted:
        item['quantity'] = int(item['quantity'])

    submitted_dict = {}
    for item in submitted:
        if item['order_id'] in submitted_dict:
            submitted_dict[item['order_id']].append(item)
        else:
            submitted_dict[item['order_id']] = [item]

    for order in expected:
        order_id = order['id']
        if order_id not in submitted_dict:
            discrepancies.append(f"Order ID not found: {order_id}")
            success = False
            continue

        submitted_items = {item['item_name']: item for item in submitted_dict[order_id]}
        for expected_item in order['items']:
            if expected_item['item_name'] not in submitted_items:
                discrepancies.append(f"Missing item: ({order_id}, {expected_item['item_name']})")
                success = False
            elif submitted_items[expected_item['item_name']]['quantity'] != expected_item['quantity']:
                discrepancies.append(f"Quantity mismatch for ({order_id}, {expected_item['item_name']}): Expected {expected_item['quantity']}, got {submitted_items[expected_item['item_name']]['quantity']}")
                success = False

    return success, discrepancies


def add_items(restaurant_id, items):
    for item in items:
        item['quantity'] = int(item['quantity'])
        item['restaurant_name'] = restaurant_id

        payload = {
            "httpMethod": "POST",
            "action": "add_item",
            "body": item
        }

        response = make_lambda_request(lambda_client, payload, fridge_mgr_lambda)
        if response['statusCode'] != 200:
            flash(f"Failed to add item: {response}", 'error')
            return False
    return True


def delete_orders(restaurant_id, order_ids):
    for order_id in order_ids:
        payload = {
            "httpMethod": "DELETE",
            "action": "delete_order",
            "body": {
                "restaurant_id": restaurant_id,
                "order_id": order_id
            }
        }

        response = make_lambda_request(lambda_client, payload, order_mgr_lambda)
        if response['statusCode'] != 200:
            flash(f"Failed to delete order: {response}", 'error')
            return False
    return True


def open_door(restaurant_id):
    payload = {
        "httpMethod": "POST",
        "action": "open_door",
        "body": {
            "restaurant_name": restaurant_id,
            "is_back_door_open": True
        }
    }

    response = make_lambda_request(lambda_client, payload, fridge_mgr_lambda)
    if response['statusCode'] == 200:
        session['is_back_door_open'] = True
    else:
        flash(f"Failed to open door: {response['body']['details']}", 'error')


def close_door(restaurant_id):
    payload = {
        "httpMethod": "POST",
        "action": "close_door",
        "body": {
            "restaurant_name": restaurant_id
        }
    }

    response = make_lambda_request(lambda_client, payload, fridge_mgr_lambda)
    if response['statusCode'] == 200:
        session['is_back_door_open'] = False
    else:
        flash(f"Failed to close door: {response['body']['details']}", 'error')