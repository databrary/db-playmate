import logging as log

from boxsdk import JWTAuth
import boxsdk as bx
import keyring
import json

from flask import Flask
from flask import request
from threading import Thread
import webbrowser
import time

app = Flask(__name__)

access_code = None


@app.route("/")
def handle_redirect():
    global access_code
    access_code = request.args.get("code")
    print(access_code)
    if len(access_code) > 0:
        return "Success! You can now close this window."
    else:
        return "Error: Access code was not obtained"


class Box:
    def __init__(self):
        with open("config.json") as config:
            cfg = json.load(config)

        self.client_id = cfg["client_id"]
        self.client_secret = cfg["client_secret"]
        self.redirect_url = "http://localhost:5000"

        self.login()

    def authenticate(self, oauth, access_code):
        access_token, refresh_token = oauth.authenticate(access_code)

    def login(self):
        access_token, refresh_token = self.read_tokens()

        if access_token is None or refresh_token is None:
            oauth = bx.OAuth2(
                client_id=self.client_id,
                client_secret=self.client_secret,
                store_tokens=self.store_tokens,
            )
            self.auth_url, csrf_token = oauth.get_authorization_url(self.redirect_url)
            webbrowser.open(self.auth_url)
            global access_code
            while access_code is None:
                print(access_code)
                time.sleep(1)
            self.authenticate(oauth, access_code)
            access_token, refresh_token = self.read_tokens()

        oauth = bx.OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        self.client = bx.Client(oauth)

    def list_dir(self, directory):
        items = directory.get_items()
        for i in items:
            print("{0} {1} is named {2}".format(i.type.capitalize(), i.id, i.name))

    def create_dir(self, base_dir, new_dir_name):
        pass

    # Finds a file by a full path given, will return the file or folder at the end
    # of the path
    def find_by_path(self, path):
        items = self.client.root_folder().get_items()
        path = path.split("/")
        # Explore the search function

    # From: https://stackoverflow.com/questions/29595255/working-with-the-box-com-sdk-for-python
    def read_tokens(self):
        """Reads authorisation tokens from keyring"""
        # Use keyring to read the tokens
        auth_token = keyring.get_password("Box_Auth", "play_box")
        refresh_token = keyring.get_password("Box_Refresh", "play_box")
        return auth_token, refresh_token

    def store_tokens(self, access_token, refresh_token):
        """Callback function when Box SDK refreshes tokens"""
        # Use keyring to store the tokens
        keyring.set_password("Box_Auth", "play_box", access_token)
        keyring.set_password("Box_Refresh", "play_box", refresh_token)

    def get_auth(self, client_id, client_secret, dev_token):
        """Return OAuth2"""
        return bx.OAuth2(
            client_id=client_id, client_secret=client_secret, access_token=dev_token
        )

    def get_folder(self):
        pass

    def copy_file(self, src, dst):
        pass


if __name__ == "__main__":
    # Delete the stored keys for debugging
    try:
        keyring.delete_password("Box_Auth", "play_box")
        keyring.delete_password("Box_Refresh", "play_box")
    except:
        pass

    server = Thread(target=app.run, daemon=True)
    server.start()
    box = Box()  # cid is hardcoded for now
    box.list_dir(box.client.root_folder())
    print("Finished!")
