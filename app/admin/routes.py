import secrets

from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.admin import admin_bp
from app.admin.forms import DirectCreateUserForm
from app.courses.permissions import admin_required
from app.extensions import db, bcrypt
from app.models.user import User, RoleEnum, ApprovalStatusEnum
from datetime import datetime


@admin_bp.route("/requests")
@login_required
@admin_required
def requests_list():
    pending = User.query.filter(
        User.role.in_([RoleEnum.INSTRUCTOR, RoleEnum.TA, RoleEnum.ADMIN]),
        User.approval_status == ApprovalStatusEnum.PENDING,
    ).order_by(User.created_at.asc()).all()
    return render_template("admin/requests.html", pending=pending)


@admin_bp.route("/requests/<int:user_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_request(user_id):
    user = User.query.get_or_404(user_id)
    if user.approval_status != ApprovalStatusEnum.PENDING:
        flash("That request is no longer pending.", "warning")
        return redirect(url_for("admin.requests_list"))

    user.approval_status = ApprovalStatusEnum.APPROVED
    user.reviewed_by = current_user.id
    user.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash(f"Approved {user.username} as {user.role.value}.", "success")
    return redirect(url_for("admin.requests_list"))


@admin_bp.route("/requests/<int:user_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_request(user_id):
    user = User.query.get_or_404(user_id)
    if user.approval_status != ApprovalStatusEnum.PENDING:
        flash("That request is no longer pending.", "warning")
        return redirect(url_for("admin.requests_list"))

    user.approval_status = ApprovalStatusEnum.REJECTED
    user.reviewed_by = current_user.id
    user.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash(f"Rejected {user.username}'s request.", "info")
    return redirect(url_for("admin.requests_list"))


@admin_bp.route("/users")
@login_required
@admin_required
def users_list():
    users = User.query.filter(
        User.role.in_([RoleEnum.INSTRUCTOR, RoleEnum.TA, RoleEnum.ADMIN]),
        User.approval_status == ApprovalStatusEnum.APPROVED,
    ).order_by(User.full_name.asc()).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_user():
    form = DirectCreateUserForm()
    generated_password = None

    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("That username is already taken.", "danger")
            return render_template("admin/user_form.html", form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash("That email is already registered.", "danger")
            return render_template("admin/user_form.html", form=form)

        password = form.password.data or secrets.token_urlsafe(12)
        if not form.password.data:
            generated_password = password

        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            role=RoleEnum(form.role.data),
            approval_status=ApprovalStatusEnum.APPROVED,
            reviewed_by=current_user.id,
            reviewed_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()

        if generated_password:
            flash(
                f"Created {user.username}. Generated password: {generated_password} "
                "(shown once — copy it now).",
                "success",
            )
        else:
            flash(f"Created {user.username}.", "success")
        return redirect(url_for("admin.users_list"))

    return render_template("admin/user_form.html", form=form)


@admin_bp.route("/users/<int:user_id>/remove", methods=["POST"])
@login_required
@admin_required
def remove_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.role == RoleEnum.ADMIN:
        remaining_admins = User.query.filter(
            User.role == RoleEnum.ADMIN,
            User.approval_status == ApprovalStatusEnum.APPROVED,
            User.is_active_flag.is_(True),
            User.id != user.id,
        ).count()
        if remaining_admins == 0:
            flash("Cannot remove the last remaining admin.", "danger")
            return redirect(url_for("admin.users_list"))

    user.is_active_flag = False
    db.session.commit()
    flash(f"Removed {user.username}.", "info")
    return redirect(url_for("admin.users_list"))