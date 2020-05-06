import stripe
from lander_backend.constants import *

stripe.api_key = 'sk_test_EmD8xVEImHu3sw12IcdGURXd00nwsGEVDc'

def create_stripe_session_for_payment(website_details, u, log_identifier):
    print(log_identifier+"Creating a new stripe session for website transaction with uuid: {}".format(u))
    try:
        amount = STANDARD_WEBSITE_PRICE_IN_DOLLARS * 100
        success_url = PAYMENT_SUCCESS_REDIRECTION_URL + '?session_id={CHECKOUT_SESSION_ID}' + '&website_uuid=' + u
        failure_url = PAYMENT_FAILURE_REDIRECTION_URL + '?website_uuid=' + u
        description = "Creating a brand new website " + LANDER_WEBSITE_HOST + website_details["website_name"]

        stripe_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'name': 'Create Website',
                'description': description,
                'amount': amount,
                'currency': 'usd',
                'quantity': 1,
            }],
            success_url=success_url,
            cancel_url=failure_url,
        )
        return stripe_session
    except Exception as e:
        raise e