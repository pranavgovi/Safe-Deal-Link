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
