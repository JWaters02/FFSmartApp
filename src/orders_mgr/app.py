import json
import logging
import os
import time
from datetime import datetime

import boto3
from flask import Flask, jsonify, make_response, flash, redirect, url_for, request, render_template, session
from flask_session import Session

from lib.utils import (create_user, delete_user_by_username, get_email_by_username,
                       get_restaurant_id, get_user_role, is_user_signed_in, make_lambda_request)

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


@app.route('/orders')
def orders():
    payload = json.dumps({
        "httpMethod": "GET",
        "action": "get_all_orders",
        "body": {
            "restaurant_id": session['username']
        }
    })

    response = make_lambda_request(lambda_client, payload, order_mgr_lambda)

    if response['statusCode'] == 404:
        return make_response(response['body'], response['statusCode'])
    elif response['statusCode'] == 500:
        return make_response('', response['statusCode'])

    orders = response['body']['items']
    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])

    return render_template('orders.html', user_role=user_role, orders=orders)


@app.route('/api/order-items/<int:order_id>')
def order_items(order_id):
    payload = json.dumps({
        "httpMethod": "GET",
        "action": "get_order",
        "body": {
            "restaurant_id": session['username'],
            "order_id": order_id
        }
    })

    response = make_lambda_request(lambda_client, payload, order_mgr_lambda)

    if response['statusCode'] == 404:
        return make_response(response['body'], response['statusCode'])
    elif response['statusCode'] == 500:
        return make_response('', response['statusCode'])

    items = response['body']['items']

    return jsonify(items=items)