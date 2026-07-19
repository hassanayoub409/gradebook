from flask import render_template, redirect, url_for
from flask_login import login_required, current_user

from app.main import main_bp
from app.models.course import Course, CourseStaff, Enrollment


@main_bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_approved:
        return render_template("auth/pending_approval.html", role=current_user.role.value)

    if current_user.is_staff:
        courses = (
            Course.query.join(CourseStaff, CourseStaff.course_id == Course.id)
            .filter(CourseStaff.user_id == current_user.id)
            .all()
        )
        return render_template("dashboard/staff_dashboard.html", courses=courses)

    if current_user.is_admin:
        return redirect(url_for("admin.requests_list"))
        # return render_template("dashboard/staff_dashboard.html", courses=[])

    courses = (
        Course.query.join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == current_user.id, Course.is_published.is_(True))
        .all()
    )
    return render_template("dashboard/student_dashboard.html", courses=courses)