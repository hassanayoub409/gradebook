from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    """Admin-only routes: approving/rejecting/directly-creating gated-role accounts."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper