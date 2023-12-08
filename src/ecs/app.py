from flask import Flask, render_template, session, jsonify
from flask_session import Session
import boto3
import os

############################################################
# init app
app = Flask(__name__)

############################################################
# Get environment variables
dynamodb_session_table = os.environ.get('DYNAMODB_TABLE')
fridge_mgr_lambda = os.environ.get('FRIDGE_MGR_ARN')
order_mgr_lambda = os.environ.get('ORDER_MGR_ARN')
users_mgr_lambda = os.environ.get('USERS_MGR_ARN')
health_report_mgr_lambda = os.environ.get('HEALTH_REPORT_MGR_ARN')
token_mgr_lambda = os.environ.get('TOKEN_MGR_ARN')

############################################################
# config
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_DYNAMODB'] = boto3.resource('dynamodb', region_name='eu-west-1')
app.config['SESSION_DYNAMODB_TABLE'] = dynamodb_session_table
app.config['SESSION_PERMANENT'] = False

############################################################
# create lambda clients
fridge_mgr_client = boto3.client('lambda', region_name='eu-west-1')
order_mgr_client = boto3.client('lambda', region_name='eu-west-1')
users_mgr_client = boto3.client('lambda', region_name='eu-west-1')
health_report_mgr_client = boto3.client('lambda', region_name='eu-west-1')
token_mgr_client = boto3.client('lambda', region_name='eu-west-1')

############################################################
# init session
Session(app)

############################################################
# session
@app.route('/logout/')
def logout():
    session.clear()
    # print a session variable
    print(session.get('username'))
    return jsonify({'status': '200'})

############################################################
# pages
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/other-page')
def other_page():
    return render_template('other-page.html')


############################################################
# run
if __name__ == '__main__':
    app.run(debug=True)
