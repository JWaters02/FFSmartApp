from flask import (
    Blueprint,
    render_template)


forgot_password_route = Blueprint('forgot_password', __name__)


@forgot_password_route.route('/forgot-password', methods=['GET'])
def forgot_password():
    return render_template('forgot-password.html')
