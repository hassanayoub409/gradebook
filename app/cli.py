import click
from flask.cli import with_appcontext

from app.extensions import db, bcrypt
from app.models.user import User, RoleEnum, ApprovalStatusEnum


@click.command("create-admin")
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.option("--full-name", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_admin(username, email, full_name, password):
    """
    Create an Admin account directly, bypassing signup and review entirely.
    """
    if User.query.filter_by(username=username).first():
        click.echo(f"Username '{username}' already exists.")
        return
    if User.query.filter_by(email=email).first():
        click.echo(f"Email '{email}' already exists.")
        return

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        role=RoleEnum.ADMIN,
        approval_status=ApprovalStatusEnum.APPROVED,
    )
    db.session.add(user)
    db.session.commit()
    # reviewed_by stays null for the bootstrap admin — there's no reviewer yet.
    click.echo(f"Admin '{username}' created.")


def register_cli(app):
    app.cli.add_command(create_admin)