#We have paypal client ID and secret
# To hit Paypal APIs , we need an access token
# paypal does not want us to send client id and secret in every single call
# so we exchange client id and secret for an access token

import time, requests
from config import PAYPAL_BASE_URL, PAYPAL_CLIENT_ID, PAYPAL_SECRET

_access_token, _expiration_time= None, 0


def get_access_token():
    global _access_token, _expiration_time
    if _access_token and time.time() < _expiration_time:
        return _access_token
    else:
        response = requests.post(
        f"{PAYPAL_BASE_URL}/v1/oauth2/token",
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"}, #there are 2 options to either pass using json= or data=, paypal expects data
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
        timeout= 30
        )
        response.raise_for_status() #for status codes 4xx, 5xx raises an error
        data = response.json()
        _access_token= data["access_token"]
        _expiration_time = time.time() + data["expires_in"] - 60 #always better to refresh 60 seconds early beacause a request might potentially miss out if it is sent in the last second
        return _access_token

def auth_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_access_token()}",
    }


def create_order(amount: float, payee_email: str, deal_id: str):
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders",
        headers=auth_headers(),
        json={
            "intent": "AUTHORIZE",
            "purchase_units": [
                {
                    "custom_id": deal_id,
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{amount:.2f}",
                    },
                    "payee": {
                        "email_address": payee_email,
                    },
                }
            ],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "return_url": "https://example.com/return",
                        "cancel_url": "https://example.com/cancel",
                    }
                }
            },
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

#buyer confirms to proceed with authorising the deal via paypal popup
def authorize_order(order_id: str): 
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/authorize",
        headers=auth_headers(),
        json={},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

#used to fetch the authorisation's current status - created/captured/voided
def get_authorization(auth_id: str):
    response = requests.get(
        f"{PAYPAL_BASE_URL}/v2/payments/authorizations/{auth_id}",
        headers=auth_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def capture_authorization(auth_id: str, amount: float, deal_id: str, final: bool = True):
    headers = auth_headers()
    headers["PayPal-Request-Id"] = f"capture-{deal_id}"
    #adding this header will help us prevent idempotent transactions that is paypal charging the client twice
    
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/payments/authorizations/{auth_id}/capture",
        headers=headers,
        json={
            "amount": {
                "currency_code": "USD",
                "value": f"{amount:.2f}",
            },
            "final_capture": final,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def void_authorization(auth_id: str):
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/payments/authorizations/{auth_id}/void",
        headers=auth_headers(),
        timeout=30,
    )
    response.raise_for_status()
    # PayPal returns 204 No Content on a successful void
    return response.json() if response.content else None


def reauthorize(auth_id: str, amount: float):
    headers = auth_headers()
    headers["PayPal-Request-Id"] = f"reauthorize-{auth_id}"
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/payments/authorizations/{auth_id}/reauthorize",
        headers=headers,
        json={
            "amount": {
                "currency_code": "USD",
                "value": f"{amount:.2f}",
            }
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def refund_capture(capture_id: str, amount: float = None):
    headers = auth_headers()
    headers["PayPal-Request-Id"] = f"refund-{capture_id}"
    body = {}
    if amount is not None:
        body["amount"] = {
            "currency_code": "USD",
            "value": f"{amount:.2f}",
        }
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/payments/captures/{capture_id}/refund",
        headers=headers,
        json=body,
        timeout=30,
    )
    response.raise_for_status()
    return response.json() if response.content else None


def add_tracking(order_id: str, capture_id: str, carrier: str, number: str):
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/track",
        headers=auth_headers(),
        json={
            "capture_id": capture_id,
            "tracking_number": number,
            "carrier": carrier,
            "status": "SHIPPED",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    get_access_token()
