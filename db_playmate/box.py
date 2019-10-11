import keyring
from boxsdk import JWTAuth

# From: https://stackoverflow.com/questions/29595255/working-with-the-box-com-sdk-for-python
def read_tokens():
    """Reads authorisation tokens from keyring"""
    # Use keyring to read the tokens
    auth_token = keyring.get_password("Box_Auth", "mybox@box.com")
    refresh_token = keyring.get_password("Box_Refresh", "mybox@box.com")
    return auth_token, refresh_token


def store_tokens(access_token, refresh_token):
    """Callback function when Box SDK refreshes tokens"""
    # Use keyring to store the tokens
    keyring.set_password("Box_Auth", "mybox@box.com", access_token)
    keyring.set_password("Box_Refresh", "mybox@box.com", refresh_token)


auth = JWTAuth(
    client_id="",
    client_secret="",
    enterprise_id="",
    jwt_key_id="",
    rsa_private_key_file_sys_path="",
    rsa_private_key_passphrase="",
    store_tokens=store_tokens,
)
