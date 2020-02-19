from box import get_client
import toml
from box import Box
from databrary import Databrary
from kobo import Kobo

"""
This is the bridge between Box and Kobo/Databrary.
Used to transfer files between the three systems.
"""

class Bridge:
    def __init__(self, db_username, kobo_base_url, kobo_token, box_session):
        self.box = box_session
        self.kobo = Kobo(kobo_base_url, kobo_token)
        self.db = Databrary(db_username)

    def transfer_box_to_databrary(self, box_path, db_volume, db_container, rename_file=None):
        """
        Rename file is optional, if so specify the filename to use on databrary)
        """
        # First, get the file from box
        # This returns a box file object, not the download
        box_file = self.box.get_file(box_path)

        # Now open an output stream into databrary
        # TODO

    def transfer_databrary_to_box(self, db_volume, db_container, db_asset, box_path):
        """
        Transfer a file from databrary to Box
        """
        # TODO expose the file name changing part of the download function 
        file_stream, total_size, filename = self.db.download_asset_stream(db_volume, db_container, db_asset)
        self.box.upload_file_stream(file_stream, box_path, total_size, filename)

    def transfer_kobo_to_box(self):
        pass


if __name__ == "__main__":

    with open("env/config.toml") as config:
        cfg = toml.load(config)
        clid = cfg["box"]["client_id"]
        clsec = cfg["box"]["client_secret"]
        databrary_username = cfg["databrary"]["username"]
        kobo_base_url = cfg['kobo']['base_url']
        kobo_token = cfg['kobo']['auth_token']

    box = get_client(clid, clsec)
    bridge = Bridge(databrary_username, kobo_base_url, kobo_token, box)
