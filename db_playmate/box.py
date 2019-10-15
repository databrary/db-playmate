import keyring
import json
import boxsdk as bx
from boxsdk import OAuth2, Client
import toml

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


def get_auth(client_id, client_secret, dev_token):
    """Return OAuth2"""
    return bx.OAuth2(
        client_id=client_id, client_secret=client_secret, access_token=dev_token
    )


def main(config, dev_token=None):
    clid = box_config["client_id"]
    clsec = box_config["client_secret"]
    print(clid, clsec)


# print(clid, clsec, dev_token)
# auth = get_auth(clid, clsec, dev_token)
# client = bx.Client(auth)
# me = client.user().get()
# print(f"My user ID is {me.id}")


if __name__ == "__main__":
    try:
        cf = open("../env/config.toml")
    except:
        cf = open("../config.toml")

    with cf:
        config = toml.load(cf)
        box_config = config["box"]

    main(config=box_config, dev_token=None)
