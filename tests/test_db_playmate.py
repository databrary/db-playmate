import db_playmate as dbp
from db_playmate import __version__


def test_version():
    assert __version__ == "0.1.0"


def test_box(configs):
    box_cfg = configs["box"]
    dbp.box.main(box_cfg["client_id"], box_cfg["client_secret"])
