import os
import boto3
import logging

from flask import session

# Global variables
dynamodb_session_table = os.environ.get('DYNAMODB_TABLE')
fridge_mgr_lambda = os.environ.get('FRIDGE_MGR_NAME')
order_mgr_lambda = os.environ.get('ORDERS_MGR_NAME')
users_mgr_lambda = os.environ.get('USERS_MGR_NAME')
health_report_mgr_lambda = os.environ.get('HEALTH_REPORT_MGR_NAME')
token_mgr_lambda = os.environ.get('TOKEN_MGR_NAME')

dynamodb_session_table = 'analysis-and-design-ecs-session-table'
fridge_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignFridgeM-JGnzKOPDBYoi'
order_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignOrdersM-Q5wAIRISq5SD'
users_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignUsersMg-AzDLX5oyzz1y'
health_report_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignHealthR-Fhf8nl7TD4Dl'
token_mgr_lambda = 'FfSmartAppTheOneWeAreWork-AnalysisAndDesignTokenMg-Iw77qKeVW3Yn'

region = 'eu-west-1'
user_pool_id = 'eu-west-1_BGeP1szQM'
client_id = '3368pjmkt1q1nlqg48duhbikgn'

lambda_client = boto3.client('lambda', region_name=region)
cognito_client = boto3.client('cognito-idp', region_name=region)
dynamodb_resource = boto3.resource('dynamodb', region_name=region)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flask_session = session