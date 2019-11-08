import json
import logging as log

import db_playmate as dbp
from db_playmate import Box
from db_playmate import Kobo
from db_playmate import __version__


def test_version():
    assert __version__ == "0.1.0"


def test_box(configs):
    box_cfg = configs["box"]
    dbp.box.main(box_cfg["client_id"], box_cfg["client_secret"])


def test_kobo(configs):
    burl = configs["kobo"]["base_url"]
    token = configs["kobo"]["auth_token"]
    log.info(burl)
    log.info(token)
    r = Kobo(base_url=burl, token=token)
    log.info(f"\n{len(r.forms)}")
    for form in r.forms:
        log.info("\n" + json.dumps(form.json, indent=2))
