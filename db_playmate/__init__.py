from flask import Flask
from db_playmate.configure import config

app = Flask(__name__)
app.config["SECRET_KEY"] = "you-will-never-guess"
app.register_blueprint(config, url_prefix="/config")


