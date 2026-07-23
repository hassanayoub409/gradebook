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

@click.command("seed-demo")
@with_appcontext
def seed_demo():
    """Wipe and repopulate the database with demo data: admin, staff,
    students, two courses with sections/activities/marks, and a couple of
    pending requests. Safe to re-run — it clears existing data first."""
    from datetime import datetime
    from app.models.user import User, RoleEnum, ApprovalStatusEnum
    from app.models.course import Course, CourseStaff, Enrollment, PendingEnrollment
    from app.models.academic import Section, Activity, ActivityTypeEnum, Mark

    if not click.confirm("This will DELETE all existing data and reseed. Continue?"):
        click.echo("Aborted.")
        return

    # Wipe in FK-safe order
    Mark.query.delete()
    Activity.query.delete()
    Section.query.delete()
    PendingEnrollment.query.delete()
    Enrollment.query.delete()
    CourseStaff.query.delete()
    Course.query.delete()
    User.query.delete()
    db.session.commit()

    def make_user(username, email, full_name, role, approval_status=None, password="password123"):
        u = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            role=role,
            approval_status=approval_status,
        )
        db.session.add(u)
        return u

    admin = make_user("admin", "admin@gradebook.demo", "Ada Admin", RoleEnum.ADMIN, ApprovalStatusEnum.APPROVED)
    db.session.flush()
    admin.reviewed_by = admin.id
    admin.reviewed_at = datetime.utcnow()

    instructor = make_user("instructor1", "instructor1@gradebook.demo", "Ibrahim Instructor", RoleEnum.INSTRUCTOR, ApprovalStatusEnum.APPROVED)
    ta = make_user("ta1", "ta1@gradebook.demo", "Tara TA", RoleEnum.TA, ApprovalStatusEnum.APPROVED)
    db.session.flush()
    for u in (instructor, ta):
        u.reviewed_by = admin.id
        u.reviewed_at = datetime.utcnow()

    pending_instructor = make_user("pending_instructor", "pending.instructor@gradebook.demo", "Pat Pending", RoleEnum.INSTRUCTOR, ApprovalStatusEnum.PENDING)
    pending_ta = make_user("pending_ta", "pending.ta@gradebook.demo", "Terry TA-Hopeful", RoleEnum.TA, ApprovalStatusEnum.PENDING)

    students = []
    for i in range(1, 6):
        s = make_user(f"student{i}", f"student{i}@gradebook.demo", f"Student {i}", RoleEnum.STUDENT)
        students.append(s)

    db.session.flush()

    course1 = Course(code="CS101", title="Intro to Computer Science", term="Fall 2026", is_published=True, created_by=instructor.id)
    course2 = Course(code="CS201", title="Data Structures", term="Fall 2026", is_published=False, created_by=ta.id)
    db.session.add_all([course1, course2])
    db.session.flush()

    db.session.add(CourseStaff(course_id=course1.id, user_id=instructor.id))
    db.session.add(CourseStaff(course_id=course1.id, user_id=ta.id))
    db.session.add(CourseStaff(course_id=course2.id, user_id=ta.id))

    for s in students[:4]:
        db.session.add(Enrollment(course_id=course1.id, student_id=s.id))
    db.session.add(PendingEnrollment(course_id=course1.id, email="not.registered.yet@gradebook.demo"))

    quizzes = Section(course_id=course1.id, name="Quizzes", weight=30)
    midterm = Section(course_id=course1.id, name="Midterm", weight=30)
    final = Section(course_id=course1.id, name="Final", weight=40)
    db.session.add_all([quizzes, midterm, final])
    db.session.flush()

    quiz1 = Activity(section_id=quizzes.id, name="Quiz 1", activity_type=ActivityTypeEnum.QUIZ, total_marks=20)
    quiz2 = Activity(section_id=quizzes.id, name="Quiz 2", activity_type=ActivityTypeEnum.QUIZ, total_marks=20)
    midterm_exam = Activity(section_id=midterm.id, name="Midterm Exam", activity_type=ActivityTypeEnum.MIDTERM, total_marks=100)
    db.session.add_all([quiz1, quiz2, midterm_exam])
    db.session.flush()

    demo_scores = {
        0: {quiz1: 18, quiz2: 17, midterm_exam: 82},
        1: {quiz1: 15, quiz2: 19, midterm_exam: 74},
        2: {quiz1: 20, quiz2: 20, midterm_exam: 95},
        # students[3] intentionally left fully ungraded to demo the "0%" empty state
    }
    for idx, marks in demo_scores.items():
        student = students[idx]
        for activity, obtained in marks.items():
            db.session.add(Mark(
                activity_id=activity.id,
                student_id=student.id,
                obtained_marks=obtained,
                entered_by=instructor.id,
            ))

    db.session.commit()

    click.echo("Demo data seeded:")
    click.echo("  Admin:      admin / password123")
    click.echo("  Instructor: instructor1 / password123")
    click.echo("  TA:         ta1 / password123")
    click.echo("  Students:   student1..student5 / password123")
    click.echo("  Pending:    pending_instructor, pending_ta (awaiting approval)")


def register_cli(app):
    app.cli.add_command(create_admin)
    app.cli.add_command(seed_demo)