from flask import Flask, render_template, session, jsonify, request, flash, redirect, url_for
from flask_session import Session
import boto3
import os

# init app
app = Flask(__name__)

# Get environment variables
dynamodb_session_table = os.environ.get('DYNAMODB_TABLE')
fridge_mgr_lambda = os.environ.get('FRIDGE_MGR_ARN')
order_mgr_lambda = os.environ.get('ORDER_MGR_ARN')
users_mgr_lambda = os.environ.get('USERS_MGR_ARN')
health_report_mgr_lambda = os.environ.get('HEALTH_REPORT_MGR_ARN')
token_mgr_lambda = os.environ.get('TOKEN_MGR_ARN')

# config
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_DYNAMODB'] = boto3.resource('dynamodb', region_name='eu-west-1')
app.config['SESSION_DYNAMODB_TABLE'] = dynamodb_session_table
app.config['SESSION_PERMANENT'] = False

# create lambda clients
fridge_mgr_client = boto3.client('lambda', region_name='eu-west-1')
order_mgr_client = boto3.client('lambda', region_name='eu-west-1')
users_mgr_client = boto3.client('lambda', region_name='eu-west-1')
health_report_mgr_client = boto3.client('lambda', region_name='eu-west-1')
token_mgr_client = boto3.client('lambda', region_name='eu-west-1')

# init session
Session(app)

# session
@app.route('/logout/')
def logout():
    session.clear()
    # print a session variable
    print(session.get('username'))
    return jsonify({'status': '200'})

# pages
@app.route('/',  methods=['GET', 'POST'])
def index():
    if 'username' in session: # whatever the auth is for if they are logged in or not
        return render_template('home.html')
    else:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            # however the call to the lamba function is done, I think it's something like this
            response = token_mgr_client.invoke(
                FunctionName=token_mgr_lambda,
                InvocationType='RequestResponse',
                Payload='{"username": "' + username + '", "password": "' + password + '"}'
            )

            response_payload = response['Payload'].read()
            response_payload = response_payload.decode('utf-8')
            response_payload = eval(response_payload)

            if response_payload['status'] == '200':
                session['username'] = username
                return render_template('home.html')
            else:
                flash('Invalid username or password', 'error')
                return render_template('login.html', error=response_payload['message'])
        return render_template('login.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # however the call to the lamba function is done, I think it's something like this
        response = users_mgr_client.invoke(
            FunctionName=users_mgr_lambda,
            InvocationType='RequestResponse',
            Payload='{"username": "' + username + '", "password": "' + password + '"}'
        )

        response_payload = response['Payload'].read()
        response_payload = response_payload.decode('utf-8')
        response_payload = eval(response_payload)

        if response_payload['status'] == '200':
            session['username'] = username
            return render_template('home.html')
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html', error=response_payload['message'])
    return render_template('register.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    return render_template('verification.html')

@app.route('/home')
def home():
    return render_template('home.html', user_role=get_user_role())

@app.route('/404')
def error_404():
    return render_template('404.html')

@app.route('/inventory')
def inventory():
    items = [
        {'name': 'Apple', 'expiry_date': '12th January 2024', 'quantity': 25, 'desired_quantity': 29},
        {'name': 'Orange', 'expiry_date': '9th January 2024', 'quantity': 6, 'desired_quantity': 15},
        {'name': 'Banana', 'expiry_date': '8th January 2024', 'quantity': 12, 'desired_quantity': 10},
        {'name': 'Pear', 'expiry_date': '7th January 2024', 'quantity': 3, 'desired_quantity': 10},
        {'name': 'Pineapple', 'expiry_date': '6th January 2024', 'quantity': 1, 'desired_quantity': 5},
    ]
    return render_template('inventory.html', user_role=get_user_role(), items=items)

@app.route('/orders')
def orders():
    # example orders
    orders = [
        {'id': 1, 'name': 'Order 1'},
        {'id': 2, 'name': 'Order 2'},
    ]

    return render_template('orders.html', user_role=get_user_role(), orders=orders)

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
    return render_template('health-report.html', user_role=get_user_role())

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

@app.route('/users')
def manage_users():
    # example users
    users = [
        {'name': 'Dan Jones', 'email': 'DanJones@yahoo.com', 'role': 'Head chef'},
        {'name': 'Larry Jones', 'email': 'LarryJones@gmail.com', 'role': 'Chef'},
        {'name': 'Bob Jones', 'email': 'BobJones@yahoo.com', 'role': 'Chef'},
        {'name': 'Sally Jones', 'email': 'SallyJones@gmail.com', 'role': 'Chef'},
        {'name': 'Ben Jones', 'email': 'BenJones@yahoo.com', 'role': 'Chef'},
    ]

    return render_template('users.html', user_role=get_user_role(), users=users)

@app.route('/admin')
def admin_settings():
    if get_user_role() != 'admin': # replace with cognito stuff
        return render_template('404.html')
    return render_template('admin-settings.html', user_role=get_user_role())

def get_user_role():
    # some shit involving cognito to get the user role here
    # then return the user's role
    role = 'headchef' # this shows everything, good for testing
    return role

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
