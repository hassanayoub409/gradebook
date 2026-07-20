from flask import send_file
from flask_login import login_required, current_user

from app.exports import exports_bp
from app.exports.excel import build_course_workbook, build_multi_course_workbook, build_roster_workbook
from app.courses.permissions import get_course_or_404, course_staff_required
from app.models.course import Course, Enrollment
from app.models.user import User


@exports_bp.route("/courses/<int:course_id>/export")
@login_required
def export_course(course_id):
    course = get_course_or_404(course_id)

    if not current_user.role.value == "student":
        # Staff export of a whole course's roster is a different shape
        # (multi-student, not multi-course) — out of scope for this stage,
        # keep this route student-only for now.
        from flask import abort
        abort(403)

    if not course.has_student(current_user) or not course.is_published:
        from flask import abort
        abort(403)

    workbook = build_course_workbook(course, current_user)
    filename = f"{course.code}_{course.term}_results.xlsx".replace(" ", "_")

    return send_file(
        workbook,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@exports_bp.route("/export/all")
@login_required
def export_all():
    if not current_user.role.value == "student":
        from flask import abort
        abort(403)

    courses = (
        Course.query.join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == current_user.id, Course.is_published.is_(True))
        .all()
    )

    workbook = build_multi_course_workbook(courses, current_user)

    return send_file(
        workbook,
        as_attachment=True,
        download_name="my_results.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

@exports_bp.route("/courses/<int:course_id>/export/roster")
@login_required
@course_staff_required
def export_roster(course_id):
    course = get_course_or_404(course_id)

    students = (
        User.query.join(Enrollment, Enrollment.student_id == User.id)
        .filter(Enrollment.course_id == course.id)
        .order_by(User.full_name.asc())
        .all()
    )

    workbook = build_roster_workbook(course, students)
    filename = f"{course.code}_{course.term}_roster.xlsx".replace(" ", "_")

    return send_file(
        workbook,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )