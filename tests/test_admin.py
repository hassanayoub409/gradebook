from tests.helpers import make_user, login
from app.models.user import User, RoleEnum, ApprovalStatusEnum


def test_non_admin_cannot_access_admin_routes(client, db):
    make_user(db, "student_x", "student_x@test.com", "Student X", RoleEnum.STUDENT, None)
    login(client, "student_x")
    assert client.get("/admin/requests").status_code == 403
    assert client.get("/admin/users").status_code == 403
    assert client.get("/admin/users/new").status_code == 403


def test_admin_can_approve_pending_instructor(client, db, seed_users):
    pending = seed_users["pending_instructor"]
    login(client, "admin1")
    client.post(f"/admin/requests/{pending.id}/approve", follow_redirects=True)

    refreshed = User.query.get(pending.id)
    assert refreshed.approval_status == ApprovalStatusEnum.APPROVED
    assert refreshed.reviewed_by is not None

    client.post("/logout")
    resp = login(client, "pend_inst")
    assert b"awaiting admin review" not in resp.data


def test_admin_can_reject_pending_ta(client, db, seed_users):
    ta = make_user(db, "pend_ta", "pend_ta@test.com", "Pending TA", RoleEnum.TA, ApprovalStatusEnum.PENDING)
    login(client, "admin1")
    client.post(f"/admin/requests/{ta.id}/reject", follow_redirects=True)

    client.post("/logout")
    resp = login(client, "pend_ta")
    assert b"not approved" in resp.data


def test_admin_direct_create_logs_in_immediately_no_pending(client, db, seed_users):
    login(client, "admin1")
    resp = client.post(
        "/admin/users/new",
        data={
            "username": "direct_ta",
            "email": "direct_ta@test.com",
            "full_name": "Direct TA",
            "role": "ta",
            "password": "directpass123",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    user = User.query.filter_by(username="direct_ta").first()
    assert user.approval_status == ApprovalStatusEnum.APPROVED
    assert user.reviewed_by is not None

    client.post("/logout")
    resp = client.post(
        "/login", data={"identifier": "direct_ta", "password": "directpass123"}, follow_redirects=True
    )
    assert b"awaiting admin review" not in resp.data


def test_cannot_remove_last_remaining_admin(client, db, seed_users):
    admin = seed_users["admin"]
    login(client, "admin1")
    resp = client.post(f"/admin/users/{admin.id}/remove", follow_redirects=True)
    assert b"Cannot remove the last remaining admin" in resp.data

    refreshed = User.query.get(admin.id)
    assert refreshed.is_active_flag is True


def test_can_remove_admin_when_another_remains(client, db, seed_users):
    admin1 = seed_users["admin"]
    admin2 = make_user(db, "admin2", "admin2@test.com", "Admin Two", RoleEnum.ADMIN, ApprovalStatusEnum.APPROVED)

    login(client, "admin1")
    resp = client.post(f"/admin/users/{admin2.id}/remove", follow_redirects=True)
    assert b"Cannot remove the last remaining admin" not in resp.data

    refreshed = User.query.get(admin2.id)
    assert refreshed.is_active_flag is False
    assert admin1  # still exists, unaffected