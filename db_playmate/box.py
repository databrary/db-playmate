import logging as log
import argparse

from boxsdk import JWTAuth
import boxsdk as bx
import keyring
import json

from flask import Flask
from flask import request
from threading import Thread
import webbrowser
import time
from collections import deque

import os

app = Flask(__name__)

access_code = None


@app.route("/")
def handle_redirect():
    global access_code
    access_code = request.args.get("code")
    log.info(access_code)
    if len(access_code) > 0:
        return "Success! You can now close this window."
    else:
        return "Error: Access code was not obtained"


class Box:
    def __init__(self, client_id, client_secret, redirect_url="http://localhost:5000"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_url = redirect_url
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

    def get_root(self):
        return self.client.root_folder()

    def list_folder(self, directory):
        items = directory.get_items()
        for i in items:
            print("{0} {1} is named {2}".format(i.type.capitalize(), i.id, i.name))

    def create_folder(self, base_folder, new_folder_name):
        """
        base_folder: Dir to create a folder in
        new_folder_name: Name of the new dir
        returns: New folder handle if successful, None if not
        """
        base = self.get_folder(base_folder)
        if base is not None:
            return base.create_subfolder(new_folder_name)
        return None

    def create_folders(self, path):
        """
        Recursively creates a path of folders. If the folder already exists,
        do nothing.
        path: The path of folders we want to create starting from the root
        returns: The created folder at the end of the path
        """
        path = path.split(os.sep)
        curname = ""
        parent = None
        curfolder = self.get_root()
        for name in path:
            if len(curname) > 0:
                curname = os.sep.join([curname, name])
            else:
                curname = name
            print(curname)
            parent = curfolder
            curfolder = self.get_folder(curname)
            if curfolder is None:
                curfolder = parent.create_subfolder(name)
        return curfolder

    def get_folder(self, path):
        """
        Path: the full path based from the root directory in Box
        returns: The folder object if found, None if not found
        """
        if path == "":
            return self.get_root()
        path = path.split(os.sep)
        target_dir = path[-1]
        path = deque(path)
        rootdir = self.get_root()
        curdir = rootdir
        while len(path) > 0:
            p = path.popleft()
            for item in curdir.get_items():
                if item.name == p:
                    curdir = item
                    break
            if curdir == rootdir or curdir.name != p:
                return None
        if curdir.name == target_dir:
            return curdir
        return None

    def get_file(self, path):
        """
        Path: full path based from the root directory
        returns: File object if found, None if not found
        """
        path = path.split(os.sep)
        filename = path[-1]
        filepath = os.sep.join(path[:-1])
        folder = self.get_folder(filepath)
        if folder is not None:
            for item in folder.get_items():
                if item.name == filename:
                    return item
        return None

    def move(self, src, dst, new_name=None):
        """
        src: Full path to file/folder we want to move
        dst: Directory to move the file/folder to
        new_name: Change the name of the file (optional)
        returns: Handle to the moved file or None if the file or dst
            could not be found
        """
        file_to_move = self.get_file(src)
        dst_folder = self.get_folder(dst)
        if dst_folder is not None and file_to_move is not None:
            return file_to_move.move(dst_folder, new_name)
        return None

    def copy(self, src, dst, new_name=None):
        """
        src: Full path to file/folder we want to copy
        dst: Directory to copy the file to
        new_name: Change the name of the file (optional)
        returns: Handle to the copied file or None if the file or dst
            could not be found
        """
        source_file = self.get_file(src)
        dest_dir = self.get_folder(dst)
        if source_file is not None and dest_dir is not None:
            return source_file.copy(dest_dir, new_name)
        return None

    def delete(self, src):
        """
        Delete the src file/folder
        src: Full path to the file to delete
        returns True if success, False if not
        """
        file_to_del = self.get_file(src)
        if file_to_del is not None:
            return file_to_del.delete()
        else:
            return False

    def upload_file(self, local_filepath, dest_folder, new_name=None):
        """
        Main upload file function. Will call upload_large_file if the file
        is over 100MB so that the upload can be chunked or resumed.
        local_filepath: Location of the file to upload on the local computer
        dest_folder: Destination folder of the file (string)
        new_name: assign a new name to the file (optional)
        """
        filesize = os.path.getsize(local_filepath) / 1000 / 1000
        if filesize > 100:  # MB
            return self.upload_large_file(local_filepath, dest_folder, new_name)
        else:
            upload_folder = self.get_folder(dest_folder)
            uploaded_file = upload_folder.upload(local_filepath, file_name=new_name)
            return uploaded_file

    def upload_large_file(self, local_filepath, dest_folder, new_name=None):
        """
        local_filepath: Location of the file to upload on the local computer
        dest_folder: Destination folder of the file (string)
        new_name: assign a new name to the file (optional)
        """
        dest = self.get_folder(dest_folder)
        uploader = dest.get_chunked_uploader(local_filepath)
        try:
            uploaded_file = chunked_uploader.start()
        except:
            # Try to resume the download if we've already started
            uploaded_file = chunked_uploader.resume()
        return uploaded_file


def main(client_id, client_secret):

    # Delete the stored keys for debugging
    # try:
    #     keyring.delete_password("Box_Auth", "play_box")
    #     keyring.delete_password("Box_Refresh", "play_box")
    # except:
    #     pass

    server = Thread(target=app.run, daemon=True)
    server.start()
    box = Box(client_id, client_secret)

    return box


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config-file",
        default="config.json",
        required=False,
        help="json file with box credentials",
    )
    args = parser.parse_args()

    with open(args.config_file) as config:
        cfg = json.load(config)
        clid = cfg["client_id"]
        clsec = cfg["client_secret"]

    main(clid, clsec)
