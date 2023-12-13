from flask import Flask, render_template, session, jsonify, request, flash
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

@app.route('/home')
def home():
    return render_template('home.html', user_role=get_user_role())

@app.route('/inventory')
def inventory():
    items = [
        {'name': 'Apple', 'expiry_date': '12th January 2024', 'quantity': 25, 'desired_quantity': 29, 'image': 'apple.png'},
        {'name': 'Orange', 'expiry_date': '9th January 2024', 'quantity': 6, 'desired_quantity': 15, 'image': 'orange.png'},
        {'name': 'Banana', 'expiry_date': '8th January 2024', 'quantity': 12, 'desired_quantity': 10, 'image': 'banana.png'},
        {'name': 'Pear', 'expiry_date': '7th January 2024', 'quantity': 3, 'desired_quantity': 10, 'image': 'pear.png'},
        {'name': 'Pineapple', 'expiry_date': '6th January 2024', 'quantity': 1, 'desired_quantity': 5, 'image': 'pineapple.png'},
        {'name': 'Watermelon', 'expiry_date': '5th January 2024', 'quantity': 0, 'desired_quantity': 10, 'image': 'watermelon.png'},
        {'name': 'Strawberry', 'expiry_date': '4th January 2024', 'quantity': 0, 'desired_quantity': 10, 'image': 'strawberry.png'},
        {'name': 'Raspberry', 'expiry_date': '3rd January 2024', 'quantity': 0, 'desired_quantity': 10, 'image': 'raspberry.png'},
        {'name': 'Blueberry', 'expiry_date': '2nd January 2024', 'quantity': 0, 'desired_quantity': 10, 'image': 'blueberry.png'},
        {'name': 'Blackberry', 'expiry_date': '1st January 2024', 'quantity': 0, 'desired_quantity': 10, 'image': 'blackberry.png'},
    ]
    return render_template('inventory.html', user_role=get_user_role(), items=items)

@app.route('/orders')
def orders():
    return render_template('orders.html', user_role=get_user_role())

@app.route('/health')
def health_report():
    return render_template('health-report.html', user_role=get_user_role())

@app.route('/delivery')
def delivery():
    return render_template('delivery.html', user_role=get_user_role())

@app.route('/users')
def manage_users():
    # example users
    users = [
        {'name': 'Dan Jones', 'email': 'DanJones@yahoo.com', 'role': 'Head chef'},
        {'name': 'Larry Jones', 'email': 'LarryJones@gmail.com', 'role': 'Chef'},
        {'name': 'Bob Jones', 'email': 'BobJones@yahoo.com', 'role': 'Chef'},
        {'name': 'Sally Jones', 'email': 'SallyJones@gmail.com', 'role': 'Chef'},
        {'name': 'Ben Jones', 'email': 'BenJones@yahoo.com', 'role': 'Chef'},
        {'name': 'BigBen Jones', 'email': 'BigBenJones@gmail.com', 'role': 'Chef'},
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
    role = 'admin'
    return role

# run
if __name__ == '__main__':
    app.run(debug=True)
