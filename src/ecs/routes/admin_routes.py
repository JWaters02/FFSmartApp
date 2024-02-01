from flask import (
    Blueprint, 
    redirect, 
    url_for, 
    json,
    flash,
    request,
    render_template)

from lib.utils import (
    make_lambda_request,
    get_user_role,
    get_admin_settings
)
from lib.globals import (
    users_mgr_lambda,
    lambda_client,
    cognito_client,
    logger,
    flask_session as session
)

admin_route = Blueprint('admin', __name__)

@admin_route.before_request
def before_request():
    if not session.get('access_token'):
        return redirect(url_for('index'))
    
    if get_user_role(cognito_client, session['access_token'], lambda_client, session['username']) != 'Admin':
        return redirect(url_for('error_404'))

@admin_route.route('/admin', methods=['POST', 'GET'])
def admin_settings():
    user_role = get_user_role(cognito_client, session['access_token'], lambda_client, session['username'])

    if user_role != 'Admin':
        return render_template('404.html')
    
    if request.method == 'GET':
        response = get_admin_settings(session['username'], lambda_client, users_mgr_lambda)

        logger.info(f"Response: {response}")

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
        
        response = make_lambda_request(lambda_client, payload, users_mgr_lambda)
        if response['statusCode'] == 200:
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('admin.admin_settings'))
        else:
            flash('Failed to update settings.', 'danger')
            return redirect(url_for('admin.admin_settings'))