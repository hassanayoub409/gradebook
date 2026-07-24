from app.extensions import bcrypt
from app.models.user import User


def make_user(db, username, email, full_name, role, approval_status=None, password="testpass123"):
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        role=role,
        approval_status=approval_status,
    )
    db.session.add(user)
    db.session.commit()
    return user


def login(client, identifier, password="testpass123"):
    return client.post(
        "/login", data={"identifier": identifier, "password": password}, follow_redirects=True
    )


def logout(client):
    return client.post("/logout", follow_redirects=True)