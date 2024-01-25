from flask import (
    Blueprint, 
    render_template,
    redirect,
    url_for
)

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

@orders_route.before_request
def before_request():
    if not session.get('access_token'):
        return redirect(url_for('index'))
    
    if get_user_role(cognito_client, session['access_token'], lambda_client, session['username']) == 'None':
        return redirect(url_for('error_404'))

@orders_route.route('/orders')
def orders():
    orders = get_order_data(lambda_client, order_mgr_lambda, session['username'])
    logger.info(orders)

    return render_template('orders.html',
            user_role=get_user_role(cognito_client, session['access_token'], lambda_client, session['username']), 
            orders=orders)