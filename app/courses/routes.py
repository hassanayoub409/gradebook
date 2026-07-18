from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.courses import courses_bp
from app.courses.forms import CourseForm, SectionForm, ActivityForm
from app.courses.permissions import staff_required, course_staff_required, enrolled_or_staff_required
from app.extensions import db
from app.models.course import Course, CourseStaff, Enrollment
from app.models.academic import Section, Activity, ActivityTypeEnum, Mark
from app.models.user import User
from app.utils.validators import validate_obtained_marks
from app.utils.grades import student_activity_mark, section_summary, course_total


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
        db.session.flush()

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

    student_view_data = None
    if not current_user.is_staff and not current_user.is_admin:
        activity_marks = {}
        for section in course.sections:
            for activity in section.activities:
                activity_marks[activity.id] = student_activity_mark(current_user.id, activity)

        section_summaries = {s.id: section_summary(current_user.id, s) for s in course.sections}
        overall = course_total(current_user.id, course)

        student_view_data = {
            "activity_marks": activity_marks,
            "section_summaries": section_summaries,
            "overall": overall,
        }

    return render_template("courses/course_detail.html", course=course, student_view_data=student_view_data)


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
    db.session.delete(section)
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
            return render_template(
                "courses/activity_form.html", form=form, course=course, section=section, activity=activity
            )

        activity.name = form.name.data
        activity.activity_type = ActivityTypeEnum(form.activity_type.data)
        activity.total_marks = form.total_marks.data
        db.session.commit()
        flash("Activity updated.", "success")
        return redirect(url_for("courses.course_detail", course_id=course.id))

    return render_template(
        "courses/activity_form.html", form=form, course=course, section=section, activity=activity
    )


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
    db.session.delete(activity)
    db.session.commit()
    flash(f"Activity '{activity.name}' deleted.", "info")
    return redirect(url_for("courses.course_detail", course_id=course.id))


@courses_bp.route("/courses/<int:course_id>/activities/<int:activity_id>/marks", methods=["GET", "POST"])
@login_required
@course_staff_required
def enter_marks(course_id, activity_id):
    course = Course.query.get_or_404(course_id)
    activity = (
        Activity.query.join(Section)
        .filter(Activity.id == activity_id, Section.course_id == course.id)
        .first_or_404()
    )

    students = (
        db.session.query(User)
        .join(Enrollment, Enrollment.student_id == User.id)
        .filter(Enrollment.course_id == course.id)
        .order_by(User.full_name.asc())
        .all()
    )

    existing_marks = {m.student_id: m for m in activity.marks}

    if request.method == "POST":
        errors = []
        for student in students:
            raw_value = request.form.get(f"mark_{student.id}", "").strip()
            if raw_value == "":
                continue  # leave ungraded, don't touch existing mark either way

            try:
                obtained = float(raw_value)
                validate_obtained_marks(obtained, activity.total_marks)
            except ValueError as e:
                errors.append(f"{student.full_name}: {e}")
                continue

            mark = existing_marks.get(student.id)
            if mark:
                mark.obtained_marks = obtained
                mark.entered_by = current_user.id
            else:
                mark = Mark(
                    activity_id=activity.id,
                    student_id=student.id,
                    obtained_marks=obtained,
                    entered_by=current_user.id,
                )
                db.session.add(mark)

        if errors:
            db.session.rollback()
            for e in errors:
                flash(e, "danger")
        else:
            db.session.commit()
            flash("Marks saved.", "success")

        return redirect(url_for("courses.enter_marks", course_id=course.id, activity_id=activity.id))

    return render_template(
        "courses/marks_entry.html",
        course=course,
        activity=activity,
        students=students,
        existing_marks=existing_marks,
    )