from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.courses import courses_bp
from app.courses.forms import CourseForm, SectionForm, ActivityForm
from app.courses.permissions import staff_required, course_staff_required, enrolled_or_staff_required
from app.extensions import db
from app.models.course import Course, CourseStaff
from app.models.academic import Section, Activity, ActivityTypeEnum


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

@courses_bp.route("/courses/<int:course_id>/sections/new", methods=["GET", "POST"])
@login_required
@course_staff_required
def new_section(course_id):
    course = Course.query.get_or_404(course_id)
    form = SectionForm()
    if form.validate_on_submit():
        if Section.query.filter_by(course_id=course.id, name=form.name.data).first():
            flash("A section with that name already exists in this course.", "danger")
            return render_template("courses/section_form.html", form=form, course=course)

        section = Section(course_id=course.id, name=form.name.data, weight=form.weight.data)
        db.session.add(section)
        db.session.commit()
        flash(f"Section '{section.name}' added.", "success")
        return redirect(url_for("courses.course_detail", course_id=course.id))

    return render_template("courses/section_form.html", form=form, course=course)


@courses_bp.route("/courses/<int:course_id>/sections/<int:section_id>/edit", methods=["GET", "POST"])
@login_required
@course_staff_required
def edit_section(course_id, section_id):
    course = Course.query.get_or_404(course_id)
    section = Section.query.filter_by(id=section_id, course_id=course.id).first_or_404()
    form = SectionForm(obj=section)
    if form.validate_on_submit():
        dup = Section.query.filter(
            Section.course_id == course.id,
            Section.name == form.name.data,
            Section.id != section.id,
        ).first()
        if dup:
            flash("A section with that name already exists in this course.", "danger")
            return render_template("courses/section_form.html", form=form, course=course, section=section)

        section.name = form.name.data
        section.weight = form.weight.data
        db.session.commit()
        flash("Section updated.", "success")
        return redirect(url_for("courses.course_detail", course_id=course.id))

    return render_template("courses/section_form.html", form=form, course=course, section=section)


@courses_bp.route("/courses/<int:course_id>/sections/<int:section_id>/delete", methods=["POST"])
@login_required
@course_staff_required
def delete_section(course_id, section_id):
    course = Course.query.get_or_404(course_id)
    section = Section.query.filter_by(id=section_id, course_id=course.id).first_or_404()
    db.session.delete(section)  # cascades to activities (and their marks, once that model exists)
    db.session.commit()
    flash(f"Section '{section.name}' and its activities were deleted.", "info")
    return redirect(url_for("courses.course_detail", course_id=course.id))


@courses_bp.route("/courses/<int:course_id>/sections/<int:section_id>/activities/new", methods=["GET", "POST"])
@login_required
@course_staff_required
def new_activity(course_id, section_id):
    course = Course.query.get_or_404(course_id)
    section = Section.query.filter_by(id=section_id, course_id=course.id).first_or_404()
    form = ActivityForm()
    if form.validate_on_submit():
        if Activity.query.filter_by(section_id=section.id, name=form.name.data).first():
            flash("An activity with that name already exists in this section.", "danger")
            return render_template("courses/activity_form.html", form=form, course=course, section=section)

        activity = Activity(
            section_id=section.id,
            name=form.name.data,
            activity_type=ActivityTypeEnum(form.activity_type.data),
            total_marks=form.total_marks.data,
        )
        db.session.add(activity)
        db.session.commit()
        flash(f"Activity '{activity.name}' added.", "success")
        return redirect(url_for("courses.course_detail", course_id=course.id))

    return render_template("courses/activity_form.html", form=form, course=course, section=section)


@courses_bp.route(
    "/courses/<int:course_id>/sections/<int:section_id>/activities/<int:activity_id>/edit",
    methods=["GET", "POST"],
)
@login_required
@course_staff_required
def edit_activity(course_id, section_id, activity_id):
    course = Course.query.get_or_404(course_id)
    section = Section.query.filter_by(id=section_id, course_id=course.id).first_or_404()
    activity = Activity.query.filter_by(id=activity_id, section_id=section.id).first_or_404()
    form = ActivityForm(obj=activity)
    if form.validate_on_submit():
        dup = Activity.query.filter(
            Activity.section_id == section.id,
            Activity.name == form.name.data,
            Activity.id != activity.id,
        ).first()
        if dup:
            flash("An activity with that name already exists in this section.", "danger")
            return render_template("courses/activity_form.html", form=form, course=course, section=section, activity=activity)

        activity.name = form.name.data
        activity.activity_type = ActivityTypeEnum(form.activity_type.data)
        activity.total_marks = form.total_marks.data
        db.session.commit()
        flash("Activity updated.", "success")
        return redirect(url_for("courses.course_detail", course_id=course.id))

    return render_template("courses/activity_form.html", form=form, course=course, section=section, activity=activity)


@courses_bp.route(
    "/courses/<int:course_id>/sections/<int:section_id>/activities/<int:activity_id>/delete",
    methods=["POST"],
)
@login_required
@course_staff_required
def delete_activity(course_id, section_id, activity_id):
    course = Course.query.get_or_404(course_id)
    section = Section.query.filter_by(id=section_id, course_id=course.id).first_or_404()
    activity = Activity.query.filter_by(id=activity_id, section_id=section.id).first_or_404()
    db.session.delete(activity)  # cascades to marks, once that model exists
    db.session.commit()
    flash(f"Activity '{activity.name}' deleted.", "info")
    return redirect(url_for("courses.course_detail", course_id=course.id))