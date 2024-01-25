import boto3
from flask import (
    Flask, 
    jsonify,
    flash, 
    redirect, 
    url_for, 
    request, 
    render_template
)
from flask_session import Session

from lib.utils import (
    get_user_role
)
from lib.globals import (
    dynamodb_session_table,
    region, 
    user_pool_id, 
    client_id, 
    lambda_client, 
    cognito_client,
    logger,
    flask_session as session
)

from routes.inventory_routes import inventory_route
from routes.orders_routes import orders_route
from routes.report_routes import report_route
from routes.user_routes import user_route
from routes.delivery_routes import delivery_route
from routes.admin_routes import admin_route

# init app
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_DYNAMODB'] = boto3.resource('dynamodb', region_name=region)
app.config['SESSION_DYNAMODB_TABLE'] = dynamodb_session_table
app.config['SESSION_PERMANENT'] = False

# init session
Session(app)

# register route blueprints
app.register_blueprint(inventory_route)
app.register_blueprint(orders_route)
app.register_blueprint(report_route)
app.register_blueprint(user_route)
app.register_blueprint(delivery_route)
app.register_blueprint(admin_route)


@app.route('/', methods=['GET'])
def index():
    return render_template('login.html')


@app.route('/config')
def config():
    return jsonify(user_pool_id=user_pool_id, client_id=client_id, region=region)


@app.route('/flash', methods=['POST'])
def flash_message():
    parameters = request.get_json()
    message = parameters['message']
    category = parameters['category']
    flash(message, category)
    return jsonify({'status': '200'})


@app.route('/home')
def home():
    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])
    return render_template('home.html', user_role=user_role)


@app.route('/404', methods=['GET', 'PATCH'])
def error_404():
    return render_template('404.html')


@app.route('/404-delivery', methods=['GET', 'PATCH'])
def error_404_delivery():
    return render_template('404-delivery.html')


# run
if __name__ == '__main__':
    app.run(debug=True)
