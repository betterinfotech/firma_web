from flask import Flask
from app.api.auth import auth_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config")

    app.register_blueprint(auth_bp)

    return app
