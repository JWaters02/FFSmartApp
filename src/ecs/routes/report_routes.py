import io
import csv

from flask import (
    Blueprint, 
    redirect, 
    url_for, 
    json,
    jsonify, 
    flash, 
    request,
    render_template)

from lib.utils import (
    get_user_role, 
    get_restaurant_id
)
from lib.globals import (
    health_report_mgr_lambda,
    lambda_client, 
    cognito_client,
    logger,
    flask_session as session
)

report_route = Blueprint('report', __name__)

@report_route.route('/send-health-report', methods=['POST'])
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
        
        user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])
        return render_template('health-report.html', csv_list=csv_list, start_date=start_date, end_date=end_date, user_role=user_role)
    else:
        flash('Failed to send email.', 'error')
    
    return redirect(url_for('report.health_report'))


@report_route.route('/health')
def health_report():
    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])
    return render_template('health-report.html', user_role=user_role)