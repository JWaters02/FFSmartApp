from flask import (
    Blueprint, 
    redirect, 
    url_for, 
    json,
    jsonify, 
    flash, 
    request,
    render_template)
from datetime import datetime
import time

from lib.utils import (
    get_user_role, 
    get_restaurant_id,
    get_order_data
)
from lib.globals import (
    order_mgr_lambda,
    lambda_client, 
    cognito_client,
    logger,
    flask_session as session
)

orders_route = Blueprint('orders', __name__)

@orders_route.route('/orders')
def orders():
    # example orders
    orders = [
        {'id': 1, 'name': 'Order 1'},
        {'id': 2, 'name': 'Order 2'},
    ]

    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])

    return render_template('orders.html', user_role=user_role, orders=orders)


@orders_route.route('/api/order-items/<int:order_id>')
def order_items(order_id):
    # example data
    order_items_data = {
        1: [
            {'name': 'Apple', 'quantity': 5, 'date_ordered': '12th January 2024'},
            {'name': 'Orange', 'quantity': 2, 'date_ordered': '9th January 2024'},
            {'name': 'Banana', 'quantity': 1, 'date_ordered': '8th January 2024'},
        ],
        2: [
            {'name': 'Cherry', 'quantity': 20, 'date_ordered': '12th January 2024'},
            {'name': 'Pinapple', 'quantity': 5, 'date_ordered': '9th January 2024'},
            {'name': 'Peach', 'quantity': 7, 'date_ordered': '8th January 2024'},
        ],
    }
    items = order_items_data.get(order_id, [])
    return jsonify(items=items)


@orders_route.route('/api/complete-order', methods=['POST'])
def complete_order():
    data = request.get_json()
    items = data['items']
    return jsonify({'status': 'success', 'message': 'Order completed successfully!'})