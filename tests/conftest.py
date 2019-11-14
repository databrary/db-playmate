from pathlib import Path

import pytest
import toml
import db_playmate as dbp



@pytest.fixture(scope="session", autouse=True)
def config_files():
    """Fetch config file. Load root toml and overwrite with env toml."""
    base_dir = Path(__file__).resolve().parent.parent
    files = []
    f = open(base_dir.joinpath("config.toml"))
    if f is not None:
        files.append(f)

    f = open(base_dir.joinpath("env", "config.toml"))
    if f is not None:
        files.append(f)

    return files

@pytest.fixture(scope="session", autouse=True)
def configs(config_files):
    """Read configuration file"""

    config = {}
    for cf in config_files:
        with cf:
            config.update(toml.load(cf))

    return config

@pytest.fixture(scope="session", autouse=True)
def box_client(configs):
    box_cfg = configs["box"]
    bx = dbp.box.main(box_cfg["client_id"], box_cfg["client_secret"])
    try:
        bx.delete("testdir")
    except:
        pass
    yield bx
