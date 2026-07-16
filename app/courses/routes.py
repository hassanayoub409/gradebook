from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.courses import courses_bp
from app.courses.forms import CourseForm
from app.courses.permissions import staff_required, course_staff_required, enrolled_or_staff_required
from app.extensions import db
from app.models.course import Course, CourseStaff


@courses_bp.route("/courses/new", methods=["GET", "POST"])
@login_required
@staff_required
def new_course():
    form = CourseForm()
    if form.validate_on_submit():
        existing = Course.query.filter_by(code=form.code.data, term=form.term.data).first()
        if existing:
            flash("A course with that code already exists for that term.", "danger")
            return render_template("courses/course_form.html", form=form)

        course = Course(
            code=form.code.data,
            title=form.title.data,
            term=form.term.data,
            is_published=form.is_published.data,
            created_by=current_user.id,
        )
        db.session.add(course)
        db.session.flush()  # get course.id before commit

        db.session.add(CourseStaff(course_id=course.id, user_id=current_user.id))
        db.session.commit()

        flash(f"Course {course.code} created.", "success")
        return redirect(url_for("courses.course_detail", course_id=course.id))

    return render_template("courses/course_form.html", form=form)


@courses_bp.route("/courses/<int:course_id>")
@login_required
@enrolled_or_staff_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template("courses/course_detail.html", course=course)


@courses_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
@course_staff_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.code = form.code.data
        course.title = form.title.data
        course.term = form.term.data
        course.is_published = form.is_published.data
        db.session.commit()
        flash("Course updated.", "success")
        return redirect(url_for("courses.course_detail", course_id=course.id))
    return render_template("courses/course_form.html", form=form, course=course)