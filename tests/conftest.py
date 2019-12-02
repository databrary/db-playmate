import keyring
import json
import logging as log
from pathlib import Path
import pytest
import toml
from db_playmate import Kobo
import db_playmate as dbp


@pytest.fixture(scope="session", autouse=True)
def test_folder():
    return Path(__file__).resolve().parent


@pytest.fixture(scope="session", autouse=True)
def root_folder():
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def config_files(test_folder):
    """Fetch config file. Load root toml and overwrite with env toml."""
    base_dir = test_folder.parent
    return [base_dir.joinpath("config.toml"), base_dir.joinpath("env", "config.toml")]


def ddm(d1, d2):
    """Deep dictionary merge. Recursively update keys."""
    for k, v in d2.items():
        if isinstance(v, dict) and k in d1.keys() and isinstance(d1[k], dict):
            ddm(d1[k], v)
        else:
            d1[k] = v


@pytest.fixture(scope="session", autouse=True)
def configs(config_files):
    """Read configuration file"""
    config = {}
    for cf in config_files:
        if cf.exists():
            ddm(config, toml.load(cf))

    return config


@pytest.fixture(scope="session")
def kobo(configs):
    log.info(configs)
    burl = configs["kobo"]["base_url"]
    token = configs["kobo"]["auth_token"]
    log.info("Initializing kobo...")
    kobo = Kobo(base_url=burl, token=token)
    return kobo


@pytest.fixture(scope="session")
def examples_folder(test_folder):
    tf = test_folder.joinpath("ex")
    tf.mkdir(parents=True, exist_ok=True)
    return tf


@pytest.fixture(scope="session")
def example_assets(examples_folder):
    """Fetch asset query response."""

    fp = examples_folder.joinpath("assets.json")
    return json.load(open(fp))


@pytest.fixture(scope="session")
def example_form(examples_folder):
    """Fetch form query response."""

    fp = examples_folder.joinpath("form.json")
    return json.load(open(fp))


@pytest.fixture(scope="session")
def example_submissions(examples_folder):
    """Fetch submission query response."""

    fp = examples_folder.joinpath("submissions.json")
    return json.load(open(fp))


@pytest.fixture(scope="session")
def example_form_id():
    return "aGD5Q64T5zTQtakQaS8x55"


@pytest.fixture(scope="session")
def output_folder(test_folder):
    """Output folder to save files to."""

    fp = test_folder.joinpath("tmp_output")
    fp.mkdir(parents=True, exist_ok=True)
    return fp


def clear_box_creds():
    """Clear access and refresh tokens from keyring to avoid auth errors from expired tokens."""
    keyring.delete_password("Box_Auth", "play_box")
    keyring.delete_password("Box_Refresh", "play_box")


@pytest.fixture()
def box_client(configs):
    clear_box_creds()
    box_cfg = configs["box"]
    bx = dbp.box.main(box_cfg["client_id"], box_cfg["client_secret"])
    yield bx
