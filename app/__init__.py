from flask import Flask
from flask_cors import CORS

from app.config import load_configurations, configure_logging
from .api import api_blueprint
from .webhook import webhook_blueprint


def create_app():
    app = Flask(__name__)

    # Load configurations and logging settings
    load_configurations(app)
    configure_logging()
    CORS(app)
    # Import and register blueprints, if any
    app.register_blueprint(webhook_blueprint, url_prefix="/webhook")
    app.register_blueprint(api_blueprint, url_prefix="/api")

    app.config['SECRET_KEY'] = 'secret!'

    return app
