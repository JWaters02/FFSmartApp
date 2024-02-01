from flask import (
    Blueprint,
    json,
    jsonify, 
    flash,
    make_response,
    request,
    render_template)

from lib.utils import (
    get_user_role,
    is_user_signed_in,
    create_user,
    make_lambda_request,
    get_email_by_username,
    delete_user_by_username
)
from lib.globals import (
    users_mgr_lambda,
    lambda_client,
    user_pool_id,
    cognito_client,
    flask_session as session
)

user_route = Blueprint('user', __name__)


@user_route.route('/logout/')
def logout():
    session.clear()
    return jsonify({'status': '200'})


@user_route.route('/register-restaurant', methods=['GET', 'POST'])
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


@user_route.route('/update-credentials', methods=['POST'])
def update_credentials():
    session['access_token'] = request.form.get('accessToken')
    session['user_data'] = request.form.get('userData')
    session['username'] = request.form.get('username')
    return make_response('', 200)


@user_route.route('/new-password', methods=['GET', 'POST'])
def new_password():
    print(request.method)
    if request.method == 'POST':
        pass

    elif request.method == 'GET':
        return render_template('new-password.html')

    else:
        return make_response('', 400)


@user_route.route('/verify', methods=['GET', 'POST'])
def verify():
    return render_template('verification.html')


@user_route.route('/register-user', methods=['POST'])
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


@user_route.route('/remove-user', methods=['DELETE'])
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


@user_route.route('/users')
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


@user_route.route('/edit-user', methods=['POST', 'GET'])
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