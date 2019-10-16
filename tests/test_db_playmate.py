from db_playmate import __version__
from db_playmate import Kobo, Box
import os
from pathlib import Path
import pytest
import logging as log
import toml
import json
import requests


@pytest.fixture
def config_file():
    """Fetch config file"""
    base_dir = Path(__file__).resolve().parent.parent
    try:
        return open(base_dir.joinpath('env', 'config.toml'))
    except FileNotFoundError:
        return open(base_dir.joinpath('config.toml'))


@pytest.fixture
def configs(config_file):
    """Read configuration file"""

    with config_file:
        config = toml.load(config_file)
        return config


def test_version():
    assert __version__ == '0.1.0'


def test_box(configs):
    clid = configs["box"]["client_id"]
    clsec = configs["box"]["client_secret"]
    log.info(clid)
    log.info(clsec)


def test_kobo(configs):
    burl = configs["kobo"]["base_url"]
    token = configs["kobo"]["auth_token"]
    r = Kobo().get_forms(url=burl, token=token)
    log.info("\n" + json.dumps(r, indent=2)[:300])
