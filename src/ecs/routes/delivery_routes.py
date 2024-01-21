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
    get_order_data
)
from lib.globals import (
    order_mgr_lambda,
    lambda_client,
    user_pool_id,
    cognito_client,
    logger,
    flask_session as session
)

delivery_route = Blueprint('delivery', __name__)

@delivery_route.route('/delivery/<token>', methods=['GET'])
def delivery(token):
    # TODO: needs updating
    order_data = get_order_data(token)
    if not order_data:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('error_404'))

    return render_template('delivery.html', order_data=order_data)