import os
import pickle
import threading
import webbrowser

import sys
import keyring
if hasattr(sys, "frozen"):
    if sys.platform.startswith("win"):
        import keyring.backends.Windows
        keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())
    elif sys.platform.startswith("darwin"):
        import keyring.backends.OS_X
        keyring.set_keyring(keyring.backends.OS_X.Keyring())

from flask import render_template, Blueprint, redirect
from flask_wtf import FlaskForm
from wtforms.fields import SubmitField, TextField
from collections import defaultdict


import db_playmate.constants as constants

import toml

config = Blueprint("config", __name__)

global forms
forms = {}


class ConfigForm(FlaskForm):
    box_client_id = TextField("Box Client ID (Required)")
    box_client_secret = TextField("Box Client Secret (Required)")
    box_redirect_uri = TextField(
        "Box Redirect URI (only change if needed)", default="http://localhost:5000"
    )

    kobo_base_url = TextField(
        "Kobo URI (only change if needed)", default="https://kf.kobotoolbox.org"
    )
    kobo_auth_token = TextField("Kobo Authentication Token (Required)")

    databrary_username = TextField("Databrary Username (Required)")
    databrary_password = TextField(
        "Databrary Password (Required, will be stored to keychain for secure access only)"
    )

    submit_button = SubmitField("Submit")


def create_forms():
    config_form = ConfigForm()
    forms = {"config_form": config_form}

    return forms


@config.route("/", methods=["GET", "POST"])
def config_page():
    global forms
    forms = create_forms()
    return render_template("config.html", forms=forms)


@config.route("/submit", methods=["GET", "POST"])
def submit():
    global forms
    config_form = ConfigForm()

    box_client_id = config_form.box_client_id.data
    box_client_secret = config_form.box_client_secret.data
    box_redirect_uri = config_form.box_redirect_uri.data

    kobo_base_url = config_form.kobo_base_url.data
    kobo_auth_token = config_form.kobo_auth_token.data

    databrary_username = config_form.databrary_username.data
    databrary_password = config_form.databrary_password.data

    keyring.set_password(
        "db_playmate_databrary", databrary_username, databrary_password
    )
    keyring.set_password("db_playmate_box", box_client_id, box_client_secret)
    keyring.set_password("db_playmate_kobo", kobo_base_url, kobo_auth_token)

    with open(constants.USER_DATA_DIR + "/config.toml", "w") as handle:
        cfg = defaultdict(dict)
        cfg["databrary"]["username"] = databrary_username
        cfg["kobo"]["base_url"] = kobo_base_url
        cfg["box"]["client_id"] = box_client_id
        cfg["box"]["redirect_uri"] = box_redirect_uri
        toml.dump(cfg, handle)

    return redirect("http://localhost:5000")


def get_creds():
    with open(constants.USER_DATA_DIR + "/config.toml") as handle:
        cfg = toml.load(handle)

    #  db_password = keyring.get_password("db_playmate_databrary", cfg['databrary']['username'])
    kobo_auth_token = keyring.get_password("db_playmate_kobo", cfg["kobo"]["base_url"])
    box_client_secret = keyring.get_password("db_playmate_box", cfg["box"]["client_id"])

    return kobo_auth_token, box_client_secret
