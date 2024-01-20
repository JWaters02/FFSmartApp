from .utils import generate_token_email_body, generate_and_send_email, get_cognito_user_email, generate_email_body


def send_delivery_email(ses_client, restaurant, token):
    destination = [restaurant['delivery_company_email']]
    sender = 'no-reply@ffsmart.benlewisjones.com'
    subject = 'Your delivery link'
    body = generate_token_email_body(restaurant, token)

    generate_and_send_email(ses_client, subject, body, destination, sender)


def send_expired_items(ses_client, restaurant, expires_items):
    email = get_cognito_user_email(restaurant['pk'])
    if email is None:
        return

    destination = [email]
    sender = 'no-reply@ffsmart.benlewisjones.com'
    subject = 'Food has expired with your fridge'
    body = generate_email_body(restaurant, expires_items)

    generate_and_send_email(ses_client, subject, body, destination, sender)

