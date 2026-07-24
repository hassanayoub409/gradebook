from tests.helpers import make_user, login
from app.models.user import User, RoleEnum, ApprovalStatusEnum


def test_student_signup_immediate_login(client):
    resp = client.post(
        "/signup",
        data={
            "username": "stud1",
            "email": "stud1@test.com",
            "full_name": "Student One",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "role": "student",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    user = User.query.filter_by(username="stud1").first()
    assert user is not None
    assert user.approval_status is None


def test_instructor_signup_is_pending_not_logged_in(client):
    resp = client.post(
        "/signup",
        data={
            "username": "inst1",
            "email": "inst1@test.com",
            "full_name": "Instructor One",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "role": "instructor",
        },
        follow_redirects=True,
    )
    user = User.query.filter_by(username="inst1").first()
    assert user.approval_status == ApprovalStatusEnum.PENDING
    assert b"awaiting admin review" in resp.data


def test_login_blocked_for_pending_account(client, db):
    make_user(db, "pendu", "pendu@test.com", "Pending User", RoleEnum.TA, ApprovalStatusEnum.PENDING)
    resp = login(client, "pendu")
    assert b"awaiting admin review" in resp.data


def test_login_blocked_for_rejected_account(client, db):
    make_user(db, "rejectedu", "rejectedu@test.com", "Rejected User", RoleEnum.TA, ApprovalStatusEnum.REJECTED)
    resp = login(client, "rejectedu")
    assert b"not approved" in resp.data


def test_login_succeeds_for_approved_student(client, db):
    make_user(db, "okstud", "okstud@test.com", "OK Student", RoleEnum.STUDENT, None)
    resp = login(client, "okstud")
    assert resp.status_code == 200
    assert b"awaiting admin review" not in resp.data


def test_login_wrong_password_rejected(client, db):
    make_user(db, "wrongpw", "wrongpw@test.com", "Wrong PW", RoleEnum.STUDENT, None, password="correcthorse")
    resp = client.post(
        "/login", data={"identifier": "wrongpw", "password": "notthepassword"}, follow_redirects=True
    )
    assert b"Invalid username/email or password" in resp.data