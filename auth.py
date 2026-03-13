from kiteconnect import KiteConnect
import config

def get_kite_client():
    """
    Initializes and returns an authenticated KiteConnect client.
    """
    kite = KiteConnect(api_key=config.API_KEY)
    if config.ACCESS_TOKEN:
        kite.set_access_token(config.ACCESS_TOKEN)
    return kite

def generate_session(request_token):
    """
    Exchanges a request_token for an access_token.
    """
    kite = KiteConnect(api_key=config.API_KEY)
    data = kite.generate_session(request_token, api_secret=config.API_SECRET)
    return data["access_token"]

def get_login_url():
    """
    Returns the login URL for user authentication.
    """
    kite = KiteConnect(api_key=config.API_KEY)
    return kite.login_url()
