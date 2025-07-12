from flask_cors import CORS

from app.api import api_blueprint
from app.conf.config import load_configurations, configure_logging
from app.conf.db_conf import db
from flask import Flask

from app.services.cache import load_menu_cache, load_extra_ingr_cache
from app.socketio import socketio
from app.webhook import webhook_blueprint


def create_app():
    app = Flask(__name__)

    load_configurations(app)
    configure_logging()
    CORS(app)
    socketio.init_app(app)

    # Import and register blueprints, if any
    app.register_blueprint(webhook_blueprint, url_prefix="/webhook")
    app.register_blueprint(api_blueprint, url_prefix="/api")

    app.config['SECRET_KEY'] = 'secret!'
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://icposdb_user:Sdm7Z4zflKeMY1Aqb6gXOtidTbZtBlJH@dpg-d1j5bd2li9vc739dg45g-a/icposdb"
    # app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://icposdb_user:Sdm7Z4zflKeMY1Aqb6gXOtidTbZtBlJH@dpg-d1j5bd2li9vc739dg45g-a.frankfurt-postgres.render.com/icposdb"
    db.init_app(app)

    with app.app_context():
        load_menu_cache()
        load_extra_ingr_cache()
    return app