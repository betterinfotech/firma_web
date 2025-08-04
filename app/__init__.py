from flask import Flask
from app.api.auth import auth_bp
from datadog import initialize

from app.config import DATADOG_OPTIONS


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config")

    initialize(**DATADOG_OPTIONS)
    app.register_blueprint(auth_bp)

    return app
