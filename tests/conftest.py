from pathlib import Path

import pytest
import toml


@pytest.fixture
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


@pytest.fixture
def configs(config_files):
    """Read configuration file"""

    config = {}
    for cf in config_files:
        with cf:
            config.update(toml.load(cf))

    return config
