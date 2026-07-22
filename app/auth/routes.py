from flask import render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from app.auth import auth_bp
from app.auth.forms import SignupForm, LoginForm, CompleteProfileForm
from app.extensions import db, bcrypt, oauth
from app.models.user import User, RoleEnum, ApprovalStatusEnum
from app.models.course import PendingEnrollment, Enrollment


def _convert_pending_enrollments(user):
    """Shared by local signup and Google complete-profile: converts any
    PendingEnrollment rows matching this user's email into real Enrollments.
    Returns the count converted."""
    pending_rows = PendingEnrollment.query.filter_by(email=user.email).all()
    converted = 0
    for pending in pending_rows:
        db.session.add(Enrollment(course_id=pending.course_id, student_id=user.id))
        db.session.delete(pending)
        converted += 1
    return converted


def _attempt_login(user, remember=False):
    """Single shared gate for logging a user in. Every login path (local,
    and Google OAuth) must route through here rather than calling
    login_user() directly, per §7.3."""
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
            db.session.flush()

            converted = _convert_pending_enrollments(user)

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


@auth_bp.route("/login/google")
def login_google():
    if current_user.is_authenticated:
        return redirect(url_for("main.landing"))
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/login/google/callback")
def google_callback():
    if current_user.is_authenticated:
        return redirect(url_for("main.landing"))

    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")
    if not userinfo:
        flash("Google login failed — no profile info returned.", "danger")
        return redirect(url_for("auth.login"))

    google_id = userinfo["sub"]
    email = userinfo["email"]
    full_name = userinfo.get("name", email)
    avatar_url = userinfo.get("picture")

    # 1. Look up by google_id first (returning Google user).
    user = User.query.filter_by(google_id=google_id).first()

    # 2. Fall back to email, to link an existing local account.
    if user is None:
        user = User.query.filter_by(email=email).first()
        if user is not None:
            user.google_id = google_id
            if not user.avatar_url:
                user.avatar_url = avatar_url
            db.session.commit()

    # 3. Neither found — brand-new Google user, needs to pick a role first.
    if user is None:
        session["google_pending"] = {
            "google_id": google_id,
            "email": email,
            "full_name": full_name,
            "avatar_url": avatar_url,
        }
        return redirect(url_for("auth.complete_profile"))

    if _attempt_login(user):
        flash(f"Welcome back, {user.full_name}!", "success")
        return redirect(url_for("main.landing"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/complete-profile", methods=["GET", "POST"])
def complete_profile():
    pending_data = session.get("google_pending")
    if not pending_data:
        flash("No pending Google signup found. Please try logging in with Google again.", "warning")
        return redirect(url_for("auth.login"))

    form = CompleteProfileForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("That username is already taken.", "danger")
            return render_template("auth/complete_profile.html", form=form, email=pending_data["email"])

        role = RoleEnum(form.role.data)
        user = User(
            username=form.username.data,
            email=pending_data["email"],
            full_name=pending_data["full_name"],
            google_id=pending_data["google_id"],
            avatar_url=pending_data["avatar_url"],
            role=role,
            password_hash=None,  # Google-only account
        )

        if role == RoleEnum.STUDENT:
            user.approval_status = None
            db.session.add(user)
            db.session.flush()

            converted = _convert_pending_enrollments(user)

            db.session.commit()
            session.pop("google_pending", None)
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
            session.pop("google_pending", None)
            return render_template("auth/pending_approval.html", role=role.value)

    return render_template("auth/complete_profile.html", form=form, email=pending_data["email"])