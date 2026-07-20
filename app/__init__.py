import os
from flask import Flask

from app.config import config_map
from app.extensions import db, migrate, login_manager, bcrypt, csrf, oauth


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)

    login_manager.login_view = "auth.login"

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.main import main_bp
    app.register_blueprint(main_bp)

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.cli import register_cli
    register_cli(app)

    from app.admin import admin_bp
    app.register_blueprint(admin_bp)

    from app.courses import courses_bp
    app.register_blueprint(courses_bp)

    from app.exports import exports_bp
    app.register_blueprint(exports_bp)

    return app