from flask import (
    Blueprint, 
    render_template)

from lib.utils import (
    get_user_role, 
    get_order_data,
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
    orders = get_order_data(lambda_client, order_mgr_lambda, session['username'])
    logger.info(orders)

    return render_template('orders.html',
            user_role=get_user_role(cognito_client, session['access_token'], lambda_client, session['username']), 
            orders=orders)