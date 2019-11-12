import json
import logging as log
from pathlib import Path

import pytest
import toml

from db_playmate.kobo import Kobo


@pytest.fixture
def test_folder():
    return Path(__file__).resolve().parent


@pytest.fixture
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


@pytest.fixture
def configs(config_files):
    """Read configuration file"""
    config = {}
    for cf in config_files:
        if cf.exists():
            ddm(config, toml.load(cf))

    return config


@pytest.fixture()
def kobo(configs):
    log.info(configs)
    burl = configs["kobo"]["base_url"]
    token = configs["kobo"]["auth_token"]
    kobo = Kobo(base_url=burl, token=token)
    return kobo


@pytest.fixture()
def examples_folder(test_folder):
    return test_folder.joinpath("ex")


@pytest.fixture
def example_assets(examples_folder):
    """Fetch asset query response."""

    fp = examples_folder.joinpath("assets.json")
    return json.load(open(fp))


@pytest.fixture
def example_submissions(examples_folder):
    """Fetch submission query response."""

    fp = examples_folder.joinpath("submissions.json")
    return json.load(open(fp))
