import keyring
import boxsdk as bx


class Box:
    # From: https://stackoverflow.com/questions/29595255/working-with-the-box-com-sdk-for-python
    def read_tokens(self):
        """Reads authorisation tokens from keyring"""
        # Use keyring to read the tokens
        auth_token = keyring.get_password("Box_Auth", "mybox@box.com")
        refresh_token = keyring.get_password("Box_Refresh", "mybox@box.com")
        return auth_token, refresh_token

    def store_tokens(self, access_token, refresh_token):
        """Callback function when Box SDK refreshes tokens"""
        # Use keyring to store the tokens
        keyring.set_password("Box_Auth", "mybox@box.com", access_token)
        keyring.set_password("Box_Refresh", "mybox@box.com", refresh_token)

    def get_auth(self, client_id, client_secret, dev_token):
        """Return OAuth2"""
        return bx.OAuth2(
            client_id=client_id, client_secret=client_secret, access_token=dev_token
        )
