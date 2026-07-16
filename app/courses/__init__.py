from flask import Blueprint

courses_bp = Blueprint("courses", __name__)

from app.courses import routes  # noqa: E402,F401