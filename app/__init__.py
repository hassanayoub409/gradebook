import os
from flask import Flask

from app.config import config_map
from app.extensions import db, migrate, login_manager, bcrypt, csrf, oauth


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # db.init_app(app)
    # migrate.init_app(app, db)
    # login_manager.init_app(app)
    # bcrypt.init_app(app)
    # csrf.init_app(app)
    # oauth.init_app(app)

    # login_manager.login_view = "auth.login"

    from app.main import main_bp
    app.register_blueprint(main_bp)

    return app