import json
import logging
import os
import io
import time
import csv
from datetime import datetime

import boto3
from flask import Flask, jsonify, make_response, flash, redirect, url_for, request, render_template, session
from flask_session import Session
from lib.utils import create_user, make_lambda_request, get_email_by_username, delete_user_by_username, is_user_signed_in, get_user_role, get_admin_settings, get_restaurant_id

# init app
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dynamodb_session_table = os.environ.get('DYNAMODB_TABLE')
fridge_mgr_lambda = os.environ.get('FRIDGE_MGR_NAME')
order_mgr_lambda = os.environ.get('ORDERS_MGR_NAME')
users_mgr_lambda = os.environ.get('USERS_MGR_NAME')
health_report_mgr_lambda = os.environ.get('HEALTH_REPORT_MGR_NAME')
token_mgr_lambda = os.environ.get('TOKEN_MGR_NAME')

# set these variables above to the hardcoded values
dynamodb_session_table = 'analysis-and-design-ecs-session-table'
fridge_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignFridgeM-JGnzKOPDBYoi'
order_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignOrdersM-Q5wAIRISq5SD'
users_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignUsersMg-AzDLX5oyzz1y'
health_report_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignHealthR-Fhf8nl7TD4Dl'
token_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignTokenMg-Iw77qKeVW3Yn'

# config
region = 'eu-west-1' #needs to be eu-west-1
user_pool_id = 'eu-west-1_BGeP1szQM'
client_id = '3368pjmkt1q1nlqg48duhbikgn'

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_DYNAMODB'] = boto3.resource('dynamodb', region_name=region)
app.config['SESSION_DYNAMODB_TABLE'] = dynamodb_session_table
app.config['SESSION_PERMANENT'] = False

# create lambda client
lambda_client = boto3.client('lambda', region_name=region)
cognito_client = boto3.client('cognito-idp')

# init session
Session(app)


# session
@app.route('/logout/')
def logout():
    session.clear()
    return jsonify({'status': '200'})


@app.route('/config')
def config():
    return jsonify(user_pool_id=user_pool_id, client_id=client_id, region=region)


# flash
@app.route('/flash', methods=['POST'])
def flash_message():
    parameters = request.get_json()
    message = parameters['message']
    category = parameters['category']
    flash(message, category)
    return jsonify({'status': '200'})


# pages
@app.route('/', methods=['GET'])
def index():
    return render_template('login.html')

@app.route('/send-health-report', methods=['POST'])
def send_health_report():
    restaurant_name = get_restaurant_id(cognito_client, session['access_token'])
    start_date = request.form.get('startDate')
    end_date = request.form.get('endDate')

    lambda_payload = {
        "httpMethod": "POST",
        "action": "send_health_report",
        "body": {
            "restaurant_name": restaurant_name,
            "startDate": start_date,
            "endDate": end_date
        }
    }
    response = lambda_client.invoke(
        FunctionName=health_report_mgr_lambda,
        InvocationType='RequestResponse',
        Payload=json.dumps(lambda_payload)
    )
    
    response_payload = json.loads(response['Payload'].read())
    if response_payload.get('statusCode') == 200:
        flash('Email sent successfully!', 'success')
        body = json.loads(response_payload['body'])
        csv_data = body['csv_data']
        csv_reader = csv.reader(io.StringIO(csv_data), delimiter=',')
        headers = next(csv_reader)
        csv_list = [dict(zip(headers, row)) for row in csv_reader]
        
        return render_template('health-report.html', csv_list=csv_list, start_date=start_date, end_date=end_date)
    else:
        flash('Failed to send email.', 'error')
    
    return redirect(url_for('health_report'))

@app.route('/register-restaurant', methods=['GET', 'POST'])
def register_restaurant():
    if request.method == 'POST':
        username = request.form.get('username')  # the username is the restaurant name

        payload = {
            'httpMethod': 'POST',
            'action': 'create_new_restaurant_dynamodb_entries',
            'body': {
                'restaurant_name': username
            }
        }

        response = lambda_client.invoke(
            FunctionName=users_mgr_lambda,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        response_payload = response['Payload'].read()
        response_payload = response_payload.decode('utf-8')
        response_payload = eval(response_payload)

        if response_payload['statusCode'] != 200:
            flash('Failed to create the account correctly', 'error')
            # TODO: delete the entries made for the account
            # TODO: delete the account in cognito

        return make_response('', response_payload['statusCode'])

    elif request.method == 'GET':
        return render_template('register-restaurant.html')

    else:
        return {
            'statusCode': 400
        }


@app.route('/update-credentials', methods=['POST'])
def update_credentials():
    session['access_token'] = request.form.get('accessToken')
    session['user_data'] = request.form.get('userData')
    session['username'] = request.form.get('username')
    return make_response('', 200)


@app.route('/new-password', methods=['GET', 'POST'])
def new_password():
    print(request.method)
    if request.method == 'POST':
        pass

    elif request.method == 'GET':
        return render_template('new-password.html')

    else:
        return make_response('', 400)


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    return render_template('verification.html')


@app.route('/home')
def home():
    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])

    return render_template('home.html', user_role=user_role)


@app.route('/404')
def error_404():
    return render_template('404.html')

@app.route('/open_door', methods=['POST'])
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
    return redirect(url_for('inventory'))

@app.route('/close_door', methods=['POST'])
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
    return redirect(url_for('inventory'))


@app.route('/inventory')
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


@app.route('/add-item', methods=['POST'])
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

    return redirect(url_for('inventory'))

@app.route('/delete-item', methods=['POST'])
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

    return redirect(url_for('inventory'))

@app.route('/update-item', methods=['POST'])
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

    return redirect(url_for('inventory'))

@app.route('/orders')
def orders():
    # example orders
    orders = [
        {'id': 1, 'name': 'Order 1'},
        {'id': 2, 'name': 'Order 2'},
    ]

    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])

    return render_template('orders.html', user_role=user_role, orders=orders)


@app.route('/api/order-items/<int:order_id>')
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


@app.route('/health')
def health_report():
    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])
    return render_template('health-report.html', user_role=user_role)


@app.route('/api/health-report/<int:date_after>/<int:date_before>')
def health_report_api(date_after, date_before):
    # example data
    items = [
        {'name': 'Apple', 'date_added': 219827349871, 'date_removed': 23740173847, 'expiry_date': 27949012840},
        {'name': 'Orange', 'date_added': 219827349871, 'expiry_date': 27949012840},
    ]
    return jsonify(items=items)


@app.route('/delivery/<token>', methods=['GET'])
def delivery(token):
    # TODO: needs updating
    order_data = get_order_data(token)
    if not order_data:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('error_404'))

    return render_template('delivery.html', order_data=order_data)


def get_order_data(token):
    if not verify_token(token):
        flash('Invalid or expired token.', 'danger')
        return None
    # example order data
    order_data = [
        {'name': 'Apple'},
        {'name': 'Orange'},
    ]
    return order_data


@app.route('/api/complete-order', methods=['POST'])
def complete_order():
    data = request.get_json()
    items = data['items']
    return jsonify({'status': 'success', 'message': 'Order completed successfully!'})


@app.route('/register-user', methods=['POST'])
def register_user():
    if request.method == 'POST':
        response = None

        username = request.form.get('username')
        email = request.form.get('email')
        restaurant_id = request.form.get('restaurant_id')
        role = request.form.get('role')
        access_token = request.form.get('accessToken')

        if not is_user_signed_in(cognito_client, access_token, session['username']):
            return make_response('', 401)

        if create_user(cognito_client, username, email, restaurant_id, user_pool_id):
            payload = {
                'httpMethod': 'POST',
                'action': 'create_user',
                'body': {
                    'restaurant_id': restaurant_id,
                    'username': username,
                    'role': role
                }
            }

            lambda_response = lambda_client.invoke(
                FunctionName=users_mgr_lambda,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            response_payload = lambda_response['Payload'].read()
            response_payload = response_payload.decode('utf-8')
            response_payload = eval(response_payload)

            print(response_payload)

            response = make_response('', 200)
        else:
            body = jsonify({
                'details': 'failed to create user'
            })
            response = make_response(body, 500)

        return response

    else:
        return make_response('', 400)


@app.route('/remove-user', methods=['DELETE'])
def remove_user():
    username_to_delete = request.form.get('usernameToDelete')
    access_token = request.form.get('accessToken')

    if not is_user_signed_in(cognito_client, access_token, session['username']):
        return make_response('', 401)

    payload = json.dumps({
        "httpMethod": "DELETE",
        "action": "delete_user",
        "body": {
            "restaurant_id": session['username'],
            "username": username_to_delete
        }
    })

    response = make_lambda_request(lambda_client, payload, users_mgr_lambda)

    if response['statusCode'] == 404:
        return make_response(response['body'], response['statusCode'])
    elif response['statusCode'] == 500:
        return make_response('', response['statusCode'])

    username = request.form.get('username')
    status_code = delete_user_by_username(cognito_client, user_pool_id, username_to_delete)

    return make_response('', status_code)


@app.route('/users')
def manage_users():

    payload = json.dumps({
        "httpMethod": "GET",
        "action": "get_all_users",
        "body": {
            "restaurant_id": session['username']
        }
    })

    response = make_lambda_request(lambda_client, payload, users_mgr_lambda)

    users = []

    if response['statusCode'] == 200:
        users = [{
            'name': user['username'],
            'email': get_email_by_username(cognito_client, user_pool_id, user['username']),
            'role': user['role']
        } for user in response['body']['items']]

    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])

    return render_template('users.html', user_role=user_role, users=users)


@app.route('/edit-user', methods=['POST', 'GET'])
def edit_user():
    if request.method == 'GET':
        user = {
            'username': request.args.get('username'),
            'email': request.args.get('email'),
            'job_role': request.args.get('jobRole')
        }

        user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])

        return render_template('edit-user.html', user_role=user_role, user=user)

    elif request.method == 'POST':

        if not is_user_signed_in(cognito_client, request.form.get('accessToken'), session['username']):
            return make_response('', 401)

        payload = json.dumps({
            "httpMethod": "POST",
            "action": "update_user",
            "body": {
                "restaurant_id": session['username'],
                "username": request.form.get('username'),
                "new_role": request.form.get('newRole')
            }
        })

        response = make_lambda_request(lambda_client, payload, users_mgr_lambda)

        return make_response('', response['statusCode'])


@app.route('/admin', methods=['POST', 'GET'])
def admin_settings():
    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])

    if user_role != 'Admin':
        return render_template('404.html')
    
    if request.method == 'GET':
        response = get_admin_settings(session['username'], lambda_client, users_mgr_lambda)

        if response['statusCode'] == 200:
            return render_template('admin-settings.html', user_role=user_role, settings=response['body']['admin_settings'])
        else:
            return render_template('admin-settings.html', user_role=user_role, settings={})

    if request.method == 'POST':
        payload = json.dumps({
            "httpMethod": "POST",
            "action": "update_admin_settings",
            "body": {
                "restaurant_id": session['username'],
                "delivery_company_email": request.form.get('DeliveryCompanyEmail'),
                "health_and_safety_email": request.form.get('HealthAndSafetyEmail'),
                "restaurant_details": {
                    "location": {
                        "city": request.form.get('City'),
                        "postcode": request.form.get('Postcode'),
                        "street_address_1": request.form.get('StreetAddress1'),
                        "street_address_2": request.form.get('StreetAddress2'),
                        "street_address_3": request.form.get('StreetAddress3')
                    },
                    "restaurant_name": request.form.get('RestaurantName'),
                }
            }
        })
        print(payload)
        
        response = make_lambda_request(lambda_client, payload, users_mgr_lambda)
        print(response)
        if response['statusCode'] == 200:
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('admin_settings'))
        else:
            flash('Failed to update settings.', 'danger')
            return redirect(url_for('admin_settings'))


@app.route('/password/<token>', methods=['GET', 'POST'])
def update_password(token):
    user = verify_token(token)
    if not user:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('error_404'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('update_password', token=token))

        flash('Your password has been updated!', 'success')
        return redirect(url_for('index'))

    return render_template('update-password.html', token=token)


def verify_token(token):
    # token verification logic
    return False


# run
if __name__ == '__main__':
    app.run(debug=True)
