import pytest

from app import create_app
from app.extensions import db as _db
from app.models.user import RoleEnum, ApprovalStatusEnum
from tests.helpers import make_user


@pytest.fixture
def app():
    flask_app = create_app("testing")
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def seed_users(db):
    """One approved Admin (created the same way `create-admin` would), one
    pending instructor, one pending admin request — per §14."""
    admin = make_user(db, "admin1", "admin1@test.com", "Admin One", RoleEnum.ADMIN, ApprovalStatusEnum.APPROVED)
    pending_instructor = make_user(
        db, "pend_inst", "pend_inst@test.com", "Pending Instructor", RoleEnum.INSTRUCTOR, ApprovalStatusEnum.PENDING
    )
    pending_admin = make_user(
        db, "pend_admin", "pend_admin@test.com", "Pending Admin", RoleEnum.ADMIN, ApprovalStatusEnum.PENDING
    )
    return {"admin": admin, "pending_instructor": pending_instructor, "pending_admin": pending_admin}