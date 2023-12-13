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
    return render_template('home.html', username=session.get('username'))


# run
if __name__ == '__main__':
    app.run(debug=True)
