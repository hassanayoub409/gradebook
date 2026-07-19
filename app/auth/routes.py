from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.auth import auth_bp
from app.auth.forms import SignupForm, LoginForm
from app.extensions import db, bcrypt
from app.models.user import User, RoleEnum, ApprovalStatusEnum

from app.models.course import PendingEnrollment, Enrollment


def _attempt_login(user, remember=False):
    """
    Single shared gate for logging a user in. Every login path (local,
    and later Google OAuth) must route through here rather than calling
    login_user() directly, per §7.3.
    """
    if not user.is_approved:
        if user.approval_status == ApprovalStatusEnum.PENDING:
            flash("Your account is awaiting admin review.", "warning")
        elif user.approval_status == ApprovalStatusEnum.REJECTED:
            flash("Your signup request was not approved.", "danger")
        return False
    login_user(user, remember=remember)
    return True


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.landing"))

    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("That username is already taken.", "danger")
            return render_template("auth/signup.html", form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash("That email is already registered.", "danger")
            return render_template("auth/signup.html", form=form)

        role = RoleEnum(form.role.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            password_hash=bcrypt.generate_password_hash(form.password.data).decode("utf-8"),
            role=role,
        )

        if user.role == RoleEnum.STUDENT:
            user.approval_status = None
            db.session.add(user)
            db.session.flush()  # need user.id before converting pending enrollments

            pending_rows = PendingEnrollment.query.filter_by(email=user.email).all()
            converted = 0
            for pending in pending_rows:
                db.session.add(Enrollment(course_id=pending.course_id, student_id=user.id))
                db.session.delete(pending)
                converted += 1

            db.session.commit()
            login_user(user)

            if converted:
                flash(f"Welcome! You've been enrolled in {converted} course(s) waiting for you.", "success")
            else:
                flash("Welcome! Your account is ready.", "success")
            return redirect(url_for("main.landing"))
        else:
            user.approval_status = ApprovalStatusEnum.PENDING
            db.session.add(user)
            db.session.commit()
            return render_template("auth/pending_approval.html", role=role.value)

    return render_template("auth/signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.landing"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user is None or user.password_hash is None or not bcrypt.check_password_hash(
            user.password_hash, form.password.data
        ):
            flash("Invalid username/email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if _attempt_login(user):
            flash(f"Welcome back, {user.full_name}!", "success")
            return redirect(url_for("main.landing"))
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("main.landing"))