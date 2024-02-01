from .utils import generate_delivery_email_body, generate_and_send_email, get_cognito_user_email, \
    generate_expired_items_email_body, generate_low_stock_email_body


def send_low_stocks_email(ses_client, restaurant, emails, low_stock):
    """
    Sends the low stock email.

    :param ses_client: SES Client.
    :param restaurant: The restaurant setting to the restaurant of interest.
    :param emails: Emails for head chefs and restaurant admin account.
    :param low_stock: List of items with low stock.
    :return: None
    """
    destination = emails
    sender = 'no-reply@ffsmart.benlewisjones.com'
    subject = 'LOW STOCK WARNING'
    body = generate_low_stock_email_body(restaurant, low_stock)

    generate_and_send_email(ses_client, subject, body, destination, sender)


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


def send_expired_items(ses_client, restaurant, emails, expires_items, going_to_expire_items):
    """
    Sends an email to the restaurant showing the expired items.
    :param ses_client: Client for SES.
    :param restaurant: The restaurant of interest.
    :param emails: Emails to send to.
    :param expires_items: List containing all the expired items.
    :param going_to_expire_items: A list of items that are going to expire.
    :return: None
    """
    destination = emails
    sender = 'no-reply@ffsmart.benlewisjones.com'
    subject = 'Food expiration in your fridge'
    body = generate_expired_items_email_body(restaurant, expires_items, going_to_expire_items)

    generate_and_send_email(ses_client, subject, body, destination, sender)

