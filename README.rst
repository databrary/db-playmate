db-playmate
===========

This package is intended to be used as an interface for KoboToolbox and Box
for the Databrary PLAY project.

Set up
******

1. Install poetry::

    curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python3

2. Clone the repo and change to the folder::

    ``git clone git@github.com:sh0sh1n/db-playmate.git && cd db-playmate``

3. Set up Python3 environment if you haven't already activated one:
    a) Create new: ``python3 -m venv .venv``
    b) Activate: ``source .venv/bin/activate``
    c) More info: https://docs.python.org/3/tutorial/venv.html

4. Use poetry to install dependencies: ``poetry install``

5. Copy the ``config.toml`` file to ``env/config.toml`` and fill in your credentials


Configuration
*************

You will need to set up authentication credentials for both Box and KoboToolbox.

KoboToolbox
"""""""""""
1. Log in to KoboToolbox: https://kf.kobotoolbox.org


2. You need to retrieve your API token. Once logged in, go to https://kf.kobotoolbox.org/token/?format=json

3. You should see something like::

    {"token":"c203948098abab0a980ab7986"}

4. Copy the long string in quotes. This will be the value of the ``auth_token`` field inside:
   the ``env/config.toml`` file.
   See `Local configuration file`_.



Box
"""

Local configuration file
""""""""""""""""""""""""

1. The package reads configurations first from the ``config.toml`` file in the root directory and then
a ``env/config.toml`` if it exists. Thus, the ``env/config.toml`` settings will override the root config settings.

2. To add your user-specific configurations, create a folder in the root directory called ``env``
and copy the ``config.toml`` file from the root directory into the ``env`` folder.


3. Open ``env/config.toml`` and replace the default values of parameters with your values.