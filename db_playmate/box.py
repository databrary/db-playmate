import argparse
import toml
import logging as log
import os
import time
import webbrowser
from collections import deque
from threading import Thread
from boxsdk.object.collaboration import CollaborationRole
import db_playmate.constants as constants
import traceback
from db_playmate import app

import boxsdk as bx
import sys
import keyring

if hasattr(sys, "frozen"):
    if sys.platform.startswith("win"):
        import keyring.backends.Windows

        keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())
    elif sys.platform.startswith("darwin"):
        import keyring.backends.OS_X

        keyring.set_keyring(keyring.backends.OS_X.Keyring())
from flask import Flask
from flask import request

boxapp = Flask(__name__)

server = None
_access_code = None


@boxapp.route("/")
def handle_redirect():
    global _access_code
    _access_code = request.args.get("code")
    log.info(_access_code)
    if _access_code and len(_access_code) > 0:
        return "Success! You can now close this window."
    else:
        _access_code = "denied"  # prevents box initialization hang
        return "Error: Access code was not obtained"


def authenticate(oauth, access_code):
    access_token, refresh_token = oauth.authenticate(access_code)
    return access_token, refresh_token


# From: https://stackoverflow.com/questions/29595255/working-with-the-box-com-sdk-for-python
def read_tokens():
    """Reads authorisation tokens from keyring"""

    # Use keyring to read the tokens
    auth_token = keyring.get_password("Box_Auth", "play_box")
    refresh_token = keyring.get_password("Box_Refresh", "play_box")
    return auth_token, refresh_token


def store_tokens(access_token, refresh_token):
    """Callback function when Box SDK refreshes tokens"""

    # Use keyring to store the tokens
    keyring.set_password("Box_Auth", "play_box", access_token)
    keyring.set_password("Box_Refresh", "play_box", refresh_token)


class Box:
    def __init__(self, client_id, client_secret, redirect_url="http://localhost:5001"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_url = redirect_url
        self._login()

    def _login(self):
        # access_token, refresh_token = read_tokens()

        # if access_token is None or refresh_token is None:
        oauth = bx.OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            store_tokens=store_tokens,
        )
        self.auth_url, csrf_token = oauth.get_authorization_url(self.redirect_url)
        webbrowser.open(self.auth_url)
        global _access_code
        while _access_code is None:
            log.debug(_access_code)
            time.sleep(1)

        if _access_code == "denied":
            raise PermissionError("Failed to authenticate to Box.")

        access_token, refresh_token = authenticate(oauth, _access_code)

        oauth = bx.OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=access_token,
            refresh_token=refresh_token,
            store_tokens=store_tokens,
        )
        self._client = bx.Client(oauth)

    def get_root(self):
        return self._client.root_folder()

    def list_folder(self, directory):
        items = directory.get_items()
        return items

    def create_folder(self, base_folder, new_folder_name):
        """
        base_folder: Dir to create a folder in
        new_folder_name: Name of the new dir
        returns: New folder handle if successful, None if not
        """
        base = self.get_folder(base_folder)
        if base is not None:
            try:
                return base.create_subfolder(new_folder_name)
            except:
                pass
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
        curfolder = self.get_root()
        for name in path:
            if len(curname) > 0:
                curname = os.sep.join([curname, name])
            else:
                curname = name
            log.debug(curname)
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
            if p.endswith(os.sep):
                p = p[:-1]
            for item in curdir.get_items():
                if item.name == p:
                    curdir = item
                    break
            if curdir == rootdir or curdir.name != p:
                return None
        if curdir.name == target_dir:
            return curdir
        raise Exception("Could not find directory {} in Box".format(path))
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

    def download_file(self, box_file, local_path, local_filename=None):
        """
        Downloads a file from box to the local path
        """
        if type(box_file) == str:
            box_file = self.get_file(box_file)

        if local_filename is not None:
            local_path = local_path + os.sep + local_filename
        else:
            local_path = local_path + os.sep + box_file.get().name

        with open(local_path, "wb") as handle:
            return self.download_file_stream(box_file, handle)

    def download_file_stream(self, box_file, output_stream):
        """
        Returns a file stream instead of a file object.
        Downloads the file to an already created output stream (e.g., to Databrary)
        """
        return box_file.download_to(output_stream)

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

    def upload_file(self, local_filepath, dest_folder, makedirs=False, new_name=None):
        """
        Main upload file function. Will call upload_large_file if the file
        is over 200MB so that the upload can be chunked or resumed.
        local_filepath: Location of the file to upload on the local computer
        dest_folder: Destination folder of the file (string)
        new_name: assign a new name to the file (optional)
        """
        if self.get_folder(dest_folder) is None:
            self.create_folders(dest_folder)
        if self.get_file(dest_folder + os.sep + local_filepath.split(os.sep)[-1]):
            self.delete(dest_folder + os.sep + local_filepath.split(os.sep)[-1])
            # TODO Remove this
        filesize = os.path.getsize(local_filepath) / 1000 / 1000
        upload_folder = self.get_folder(dest_folder)
        if upload_folder is None and makedirs is True:
            upload_folder = self.create_folders(dest_folder)
        if filesize > 200:  # MB
            return self.upload_large_file(local_filepath, dest_folder, new_name)
        else:
            app.logger.info("UPLOADING", new_name, local_filepath, dest_folder)
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
            uploaded_file = uploader.start()
        except:
            # Try to resume the download if we've already started
            uploaded_file = uploader.resume()
        return uploaded_file

    def upload_file_stream(self, stream, dest_folder, total_size, filename):
        dest = self.get_folder(dest_folder)
        if total_size > 200:
            upload_session = dest.create_upload_session(total_size, filename)
            uploader = upload_session.get_chunked_uploader_for_stream(
                stream, total_size
            )
            try:
                uploaded_file = uploader.start()
            except:
                uploaded_file = uploader.resume()
        else:
            uploaded_file = dest.upload_stream(stream, filename)
        return uploaded_file

    def add_collab_viewer(self, item, email_address):
        """
        item: The Box File or Folder to add a collaborator to
        email_address: String form of the email address to collab
        """
        try:
            item.collaborate_with_login(email_address, CollaborationRole.VIEWER)
            return True
        except Exception as e:
            app.logger.error("Error: could not add user", e)
        return False

    def add_collab_editor(self, item, email_address):
        """
        item: The Box File or Folder to add a collaborator to
        email_address: String form of the email address to collab
        """
        try:
            item.collaborate_with_login(email_address, CollaborationRole.EDITOR)
            return True
        except Exception as e:
            app.logger.error("Error: could not add user", e)
        return False

    def add_collab_write_only(self, item, email_address):
        """
        item: The Box File or Folder to add a collaborator to
        email_address: String form of the email address to collab
        """
        try:
            item.collaborate_with_login(
                email_address, CollaborationRole.PREVIEWER_UPLOADER
            )
            return True
        except Exception as e:
            app.logger.error("Error: could not add user", e)
        return False

    def remove_collab_viewer(self, item, email_address):
        """
        item: The Box File or Folder to remove collab from
        email_address: String form of the email address to collab
        returns True if the collab was successfully removed,
                False if the collab could not be found.
        """
        collabs = item.get_collaborations()
        for c in collabs:
            target = c.accessible_by
            if target is not None:
                app.logger.info(target.login)

            if (
                target is not None and target.login == email_address
            ) or c.invite_email == email_address:
                c.delete()
                return True
        return False

    def list_collabs(self, item):
        collabs = item.get_collaborations()
        # Put it into a pandas dataframe or similar object?
        class BoxCollab:
            def __init__(self, c):
                self.email = (
                    c.accessible_by.login
                    if c.accessible_by is not None
                    else c.invite_email
                )
                self.status = c.status
                self.name = c.accessible_by.name if c.accessible_by is not None else ""

        return [BoxCollab(c) for c in collabs]

    def update_coded_videos(self, datastore):
        # For each uncoded video in the datastore, check to see if it has been coded yet
        # Pri coding check
        passes = ["loc", "obj", "com", "emo", "tra"]
        for sub in datastore.get_submissions():
            app.logger.info("Checking", sub.play_filename, sub.coding_filename_prefix + ".opf")
            # Check for PRI files
            for p in passes:
                if getattr(sub, "assigned_coding_site_{}".format(p)) and not getattr(
                    sub, "primary_coding_finished_{}".format(p)
                ):
                    lab = getattr(sub, "assigned_coding_site_{}".format(p))
                    # Check for file
                    pri_folder_name = constants.PRI_CODED_DIR.format(p, lab)
                    app.logger.info(pri_folder_name)
                    pri_file_name = "{}/{}_{}.opf".format(
                        pri_folder_name, sub.coding_filename_prefix, p
                    )
                    app.logger.info("Checking folder", pri_file_name)
                    pri_file = self.get_file(pri_file_name)
                    app.logger.info(pri_file)
                    if pri_file is not None:
                        setattr(sub, "primary_coding_finished_{}".format(p), True)
                        app.logger.info("Found, setting to true")

    def set_permissions_read(self, folder, emails):
        self.set_permissions(folder, emails, CollaborationRole.VIEWER)

    def set_permissions_readwrite(self, folder, emails):
        self.set_permissions(folder, emails, CollaborationRole.VIEWER_UPLOADER)

    def set_permissions_write(self, folder, emails):
        self.set_permissions(folder, emails, CollaborationRole.PREVIEWER_UPLOADER)

    def set_permissions(self, folder, emails, role):
        f = get_folder(folder)
        for e in emails:
            f.collaborate_with_login(e, role)

    def get_finished_opf_files(self, asset):
        filenames = []
        # if we cant find the file then get the primary, it is silver
        for p in ["tra", "loc", "emo", "com", "obj"]:
            try:  # TODO remove this
                filepath = "/".join(
                    [
                        constants.SILVER_FINAL_DIR,
                        getattr(asset, "assigned_coding_site_" + p),
                        asset.coding_filename_prefix + p,
                    ]
                )
                if self.get_file(filepath):
                    filenames.append(
                        self.download_file(filepath, constants.TMP_DATA_DIR,)
                    )
                else:
                    filepath = "/".join(
                        [
                            constants.PRI_CODED_DIR,
                            getattr(asset, "assigned_coding_site_" + p),
                            asset.coding_filename_prefix + p,
                        ]
                    )
                    filenames.append(
                        self.download_file(filepath, constants.TMP_DATA_DIR,)
                    )
            except:
                pass

        return filenames

    def get_files_in_folder(self, folder):
        files = []
        dirs = []
        for x in folder.get_items():
            if type(x) is bx.object.folder.Folder:
                dirs.append(x)
            else:
                files.append(x)
        return dirs, files

    def get_file_tree(self, directory):
        return self._get_file_tree(directory, [])

    def _get_file_tree(self, directory, files, dirpath=""):
        app.logger.info(directory)
        if directory.endswith("/"):
            directory = directory[:-1]
        dirpath += directory + "/"
        app.logger.info(directory, dirpath, dirpath[:-1])
        dirs, files_in_folder = self.get_files_in_folder(self.get_folder(dirpath[:-1]))
        app.logger.info(dirs, files_in_folder)
        files += [dirpath + f.get().name for f in files_in_folder]
        for d in dirs:
            self._get_file_tree(d.name, files, dirpath)
        return files

    def sync_datastore_to_box(self, datastore):
        qa_dir = constants.QA_CODING_DIR
        app.logger.info(qa_dir)
        app.logger.info("QA TEMP SYNC")
        for path in self.get_file_tree(qa_dir):
            app.logger.info(path)
            if path.endswith(".opf"):
                filename = path.split("/")[-1]
                app.logger.info(path, filename)
                _, site, subj_number = filename.replace(".opf", "").split("_")
                if site != "SITID" and subj_number != "PPP":
                    app.logger.info('Site', site)
                    app.logger.info('Subject Number', subj_number)
                    # app.logger.info(datastore.sites[site].submissions)
                    try:
                        submission = datastore.find_submission_by_site_subj(
                            site, subj_number
                        )
                        submission.ready_for_qa = True
                    except KeyError:
                        continue
                    except ValueError:
                        continue

        # Check QA files
        qa_dir = "/".join(constants.QA_CODED_DIR.split("/")[0:3])
        app.logger.info(qa_dir)
        app.logger.info("QA SYNC")
        app.logger.info(self.get_file_tree(qa_dir))
        for path in self.get_file_tree(qa_dir):
            app.logger.info(path)
            if path.endswith(".opf"):
                app.logger.info(path)
                filename = path.split("/")[-1]
                try:
                    _, site, subj_number = filename.replace(".opf", "").split("_")
                except ValueError:
                    _, site, subj_number, hqa = filename.replace(".opf", "").split("_")
                try:
                    submission = datastore.find_submission_by_site_subj(
                        site, subj_number
                    )
                    submission.ready_for_qa = True
                    submission.ready_for_coding = True
                except KeyError:
                    continue

        coding_dir = "/".join(constants.PRI_CODING_DIR.split("/")[0:3])
        app.logger.info("PRIMARY CODING SYNC", coding_dir)
        files = self.get_file_tree(coding_dir)
        # These are the paths to all of the files in the dir, parse them
        app.logger.info(files)
        for path in files:
            app.logger.info(path)
            if path.endswith(".opf"):
                try:
                    app.logger.info(path)
                    _, _, _, coding_pass, lab_folder, status, filename = path.split("/")
                    coding_pass = coding_pass[-3:]
                    lab_code = "_".join(lab_folder.split("_")[2:])
                    status = status[0]
                    app.logger.info(coding_pass, lab_code, status)

                    # Update the file based on the information we just saw
                    submission = datastore.find_submission_by_name(filename)
                    setattr(submission, "assigned_coding_site_" + coding_pass, lab_code)
                    app.logger.info(
                        "PRIMARY SYNC", submission.play_filename, coding_pass, lab_code
                    )
                    submission.ready_for_qa = True
                    submission.ready_for_coding = True
                    if status == "3":
                        setattr(
                            submission, "primary_coding_finished_" + coding_pass, True
                        )
                except KeyError as e:
                    app.logger.error(traceback.format_exc())
                    continue
                except AttributeError as e:
                    app.logger.error("Not found", traceback.format_exc())
                    continue
                except ValueError as e:
                    app.logger.error(traceback.format_exc())
                    continue

        coding_dir = "/".join(constants.REL_CODING_DIR.split("/")[0:3])
        app.logger.info("REL CODING SYNC", coding_dir)
        files = self.get_file_tree(coding_dir)
        # These are the paths to all of the files in the dir, parse them
        for path in files:
            if path.endswith(".opf"):
                app.logger.info(path)
                try:
                    _, _, _, coding_pass, lab_folder, filename = path.split("/")
                    coding_pass = coding_pass[-3:]
                    lab_code = lab_folder.split("_")[1]

                    # Update the file based on the information we just saw
                    submission = datastore.find_submission_by_name(filename)
                    setattr(submission, "ready_for_rel_" + coding_pass, True)
                    setattr(submission, "assigned_coding_site_" + coding_pass, lab_code)
                    submission.ready_for_qa = True
                    submission.ready_for_coding = True
                except KeyError:
                    app.logger.error(traceback.format_exc())
                    continue
                except AttributeError:
                    app.logger.error(traceback.format_exc())
                    continue
                except ValueError:
                    app.logger.error(traceback.format_exc())
                    continue
                except IndexError:
                    app.logger.error(traceback.format_exc())
                    continue

        silver_dir = constants.SILVER_FINAL_DIR
        # TODO Check silver dir

        gold_dir = constants.GOLD_FINAL_DIR
        # TODO Check gold dir

    def update_permissions(self, datastore):
        admin_emails = datastore.labs["PLAYT_1"].coders
        app.logger.info("ADMIN EMAILS", admin_emails)
        for lab in datastore.labs:
            # Generate each of the folders we need to check
            app.logger.info(lab)
            lab = datastore.labs[lab]
            for coding_pass in ["loc", "emo", "com", "tra", "obj"]:
                if getattr(lab, "code_" + coding_pass):
                    coding_dir = constants.PRI_CODING_DIR.format(
                        coding_pass, lab.lab_code
                    )
                    coded_dir = constants.PRI_CODED_DIR.format(
                        coding_pass, lab.lab_code
                    )
                    work_dir = constants.PRI_WORK_DIR.format(coding_pass, lab.lab_code)
                    #  rel_dir = constants.REL_CODING_DIR.format(coding_pass, lab.name)
                    #  rel_coded_dir = constants.REL_CODED_DIR.format(
                    #  coding_pass, lab.name
                    #  )
                    coding_folder = self.get_folder(coding_dir)
                    coded_folder = self.get_folder(coded_dir)
                    work_folder = self.get_folder(work_dir)
                    if not coding_folder:
                        coding_folder = self.create_folders(coding_dir)
                    if not coded_folder:
                        coded_folder = self.create_folders(coded_dir)
                    if not work_folder:
                        work_folder = self.create_folders(work_dir)

                    # Confirm file permissions
                    collabs = self.list_collabs(coding_folder)
                    current_emails = [x.email for x in collabs]
                    app.logger.info("Authorized collabs", collabs)
                    app.logger.info("Current emails", current_emails)
                    for email in lab.coders:
                        if email not in current_emails:
                            app.logger.info("ADDING", email, "TO", coding_dir)
                            #  self.add_collab_write_only(coded_folder, email)
                            #  self.add_collab_viewer(coding_folder, email)
                            #  self.add_collab_editor(work_folder, email)
                    for email in current_emails:
                        if email not in lab.coders and email not in admin_emails:
                            app.logger.info("REMOVING", email, "FROM", coding_dir)
                            #  self.remove_collab_viewer(coded_folder, email)
                            #  self.remove_collab_viewer(coding_folder, email)
                            #  self.remove_collab_viewer(work_folder, email)

                    # Confirm video permissions
                    for asset in lab.assigned_videos:
                        video_file = self.get_file(
                            constants.VIDEO_DIR + "/" + asset.play_filename
                        )
                        for email in lab.coders:
                            if email not in current_emails:
                                app.logger.info("ADDING", email, "TO", asset.play_filename)
                                #  self.add_collab_viewer(video_file, email)
                        for email in current_emails:
                            if email not in lab.coders and email not in admin_emails:
                                app.logger.info("REMOVING", email, "FROM", asset.play_filename)
                                #  self.remove_collab_viewer(video_file, email)


def get_client(client_id, client_secret):
    global server
    if server is None:
        server = Thread(target=boxapp.run, daemon=True, kwargs=dict(port="5001"))
        server.start()

    return Box(client_id, client_secret)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config-file",
        default=constants.USER_DATA_DIR + "/config.toml",
        required=False,
        help="json file with box credentials",
    )
    args = parser.parse_args()

    with open(args.config_file) as config:
        cfg = toml.load(config)
        clid = cfg["box"]["client_id"]
        clsec = cfg["box"]["client_secret"]

    box = get_client(clid, clsec)
