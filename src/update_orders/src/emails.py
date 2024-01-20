from .utils import generate_delivery_email_body, generate_and_send_email, get_cognito_user_email, generate_expired_items_email_body


def send_delivery_email(ses_client, restaurant, token):
    """
    Sends the delivery email.
    :param ses_client: Client for SES.
    :param restaurant: The restaurant setting to the restaurant of interest.
    :param token: Token generated for the order.
    :return: None
    """
    destination = [restaurant['delivery_company_email']]
    sender = 'no-reply@ffsmart.benlewisjones.com'
    subject = 'Your delivery link'
    body = generate_delivery_email_body(restaurant, token)

    generate_and_send_email(ses_client, subject, body, destination, sender)


def send_expired_items(ses_client, restaurant, expires_items):
    """
    Sends an email to the restaurant showing the expired items.
    :param ses_client: Client for SES.
    :param restaurant: The restaurant setting to the restaurant of interest.
    :param expires_items: List containing all the expired items.
    :return: None
    """
    email = get_cognito_user_email(restaurant['pk'])
    if email is None:
        return

    destination = [email]
    sender = 'no-reply@ffsmart.benlewisjones.com'
    subject = 'Food has expired with your fridge'
    body = generate_expired_items_email_body(restaurant, expires_items)

    generate_and_send_email(ses_client, subject, body, destination, sender)

