import json
import logging as log

from db_playmate import Kobo
from db_playmate import __version__


def test_version():
    assert __version__ == "0.1.0"


def test_box(configs):
    clid = configs["box"]["client_id"]
    clsec = configs["box"]["client_secret"]
    log.info(clid)
    log.info(clsec)


def test_kobo(configs):
    burl = configs["kobo"]["base_url"]
    token = configs["kobo"]["auth_token"]
    log.info(burl)
    log.info(token)
    r = Kobo(base_url=burl, token=token)
    log.info(f"\n{len(r.forms)}")
    for form in r.forms:
        log.info("\n" + json.dumps(form.json, indent=2))
