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
    user_pool_id,
    cognito_client,
    logger,
    flask_session as session
)

delivery_route = Blueprint('delivery', __name__)

@delivery_route.route('/delivery/<restaurant_id>/<token>/', methods=['GET', 'POST'])
def delivery(restaurant_id, token):
    # if not validate_token(token, lambda_client, restaurant_id, token_mgr_lambda):
    #     flash('Invalid or expired token.', 'danger')
    #     return redirect(url_for('error_404'))
    
    order_data = get_order_data(lambda_client, order_mgr_lambda, restaurant_id)
    logger.info(order_data)

    if request.method == 'POST':
        try:
            item_name = request.form.get('item_name')
            quantity = request.form.get('quantity', 0)
            expiry_date_str = request.form.get('expiry_date')
            
            if not item_name or not quantity or not expiry_date_str:
                flash('Please fill in all fields', 'error')
                return render_template('delivery.html', 
                        order_data=order_data, 
                        restaurant_id=restaurant_id, 
                        token=token,
                        is_back_door_open=session.get('is_back_door_open', False))
            
            expiry_date = int(time.mktime(datetime.strptime(expiry_date_str, '%Y-%m-%d').timetuple()))
            restaurant_name = restaurant_id

            payload = {
                "httpMethod": "POST",
                "action": "add_item",
                "body": {
                    "restaurant_name": restaurant_name,
                    "item_name": item_name,
                    "quantity_change": int(quantity),
                    "expiry_date": expiry_date
                }
            }

            response = make_lambda_request(lambda_client, payload, fridge_mgr_lambda)
            if response['statusCode'] == 200:
                flash('Item added successfully!', 'success')
            else:
                flash(f"Failed to add item: {response['body']['details']}", 'error')

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            flash('Error adding item', 'error')

    return render_template('delivery.html', 
            order_data=order_data, 
            restaurant_id=restaurant_id, 
            token=token,
            is_back_door_open=session.get('is_back_door_open', False))

@delivery_route.route('/delivery/open_door/<restaurant_id>/<token>/', methods=['POST'])
def open_door(restaurant_id, token):
    # if not validate_token(token, lambda_client, restaurant_id, token_mgr_lambda):
    #     flash('Invalid or expired token.', 'danger')
    #     return redirect(url_for('error_404'))
    
    payload = {
        "httpMethod": "POST",
        "action": "open_door",
        "body": {
            "restaurant_name": restaurant_id,
            "is_front_door_open": False,
            "is_back_door_open": True
        }
    }

    response = make_lambda_request(lambda_client, payload, fridge_mgr_lambda)
    if response['statusCode'] == 200:
        session['is_back_door_open'] = True
        return jsonify({'success': True, 'is_back_door_open': True})
    else:
        flash(f"Failed to open door: {response['body']['details']}", 'error')
        return jsonify({'success': False, 'is_back_door_open': False})


@delivery_route.route('/delivery/close_door/<restaurant_id>/<token>/', methods=['POST'])
def close_door(restaurant_id, token):
    # if not validate_token(token, lambda_client, restaurant_id, token_mgr_lambda):
    #     flash('Invalid or expired token.', 'danger')
    #     return redirect(url_for('error_404'))
    
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
        return jsonify({'success': True, 'is_back_door_open': False})
    else:
        flash(f"Failed to close door: {response['body']['details']}", 'error')
        return jsonify({'success': False, 'is_back_door_open': True})