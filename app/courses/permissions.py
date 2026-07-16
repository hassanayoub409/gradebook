from functools import wraps
from flask import abort
from flask_login import current_user

from app.models.course import Course


def admin_required(f):
    """Admin-only routes: approving/rejecting/directly-creating gated-role accounts."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper

def staff_required(f):
    """Any approved instructor/TA — not scoped to a specific course."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff or not current_user.is_approved:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def get_course_or_404(course_id):
    return Course.query.get_or_404(course_id)


def course_staff_required(f):
    """Checks the current_user is instructor/TA on THIS specific course (course_id from route kwargs)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        course = get_course_or_404(kwargs["course_id"])
        if not current_user.is_authenticated or not current_user.is_staff or not current_user.is_approved:
            abort(403)
        if not course.has_staff(current_user):
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def enrolled_or_staff_required(f):
    """Student must be enrolled; staff must be assigned to the course. Used for viewing course detail."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_approved:
            abort(403)
        course = get_course_or_404(kwargs["course_id"])
        if current_user.is_staff:
            if not course.has_staff(current_user):
                abort(403)
        elif current_user.role.value == "student":
            if not course.has_student(current_user):
                abort(403)
        else:
            abort(403)
        return f(*args, **kwargs)
    return wrapper