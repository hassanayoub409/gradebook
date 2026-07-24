from tests.helpers import make_user, login
from app.models.user import RoleEnum, ApprovalStatusEnum
from app.models.course import Course, CourseStaff, Enrollment
from app.models.academic import Section, Activity, ActivityTypeEnum, Mark


def _make_instructor(db, username="instr1"):
    return make_user(db, username, f"{username}@test.com", "Instructor", RoleEnum.INSTRUCTOR, ApprovalStatusEnum.APPROVED)


def _make_student(db, username="stud_c"):
    return make_user(db, username, f"{username}@test.com", "Student", RoleEnum.STUDENT, None)


def test_staff_can_create_course_and_is_auto_added_as_staff(client, db):
    _make_instructor(db)
    login(client, "instr1")
    client.post("/courses/new", data={"code": "CS100", "title": "Intro", "term": "Fall 2026"}, follow_redirects=True)

    course = Course.query.filter_by(code="CS100").first()
    assert course is not None
    assert CourseStaff.query.filter_by(course_id=course.id, user_id=course.created_by).first() is not None


def test_student_cannot_create_course(client, db):
    _make_student(db)
    login(client, "stud_c")
    assert client.get("/courses/new").status_code == 403


def test_unenrolled_student_cannot_view_course(client, db):
    instructor = _make_instructor(db)
    course = Course(code="CS110", title="X", term="Fall 2026", is_published=True, created_by=instructor.id)
    db.session.add(course)
    db.session.commit()

    _make_student(db, "outsider")
    login(client, "outsider")
    assert client.get(f"/courses/{course.id}").status_code == 403


def test_unpublished_course_hidden_from_enrolled_student(client, db):
    instructor = _make_instructor(db)
    course = Course(code="CS120", title="Y", term="Fall 2026", is_published=False, created_by=instructor.id)
    db.session.add(course)
    db.session.commit()

    student = _make_student(db, "enrolled_hidden")
    db.session.add(Enrollment(course_id=course.id, student_id=student.id))
    db.session.commit()

    login(client, "enrolled_hidden")
    assert client.get(f"/courses/{course.id}").status_code == 403


def test_published_course_visible_to_enrolled_student(client, db):
    instructor = _make_instructor(db)
    course = Course(code="CS121", title="Y2", term="Fall 2026", is_published=True, created_by=instructor.id)
    db.session.add(course)
    db.session.commit()

    student = _make_student(db, "enrolled_visible")
    db.session.add(Enrollment(course_id=course.id, student_id=student.id))
    db.session.commit()

    login(client, "enrolled_visible")
    assert client.get(f"/courses/{course.id}").status_code == 200


def test_non_staff_cannot_add_section(client, db):
    instructor = _make_instructor(db)
    course = Course(code="CS122", title="Z", term="Fall 2026", is_published=True, created_by=instructor.id)
    db.session.add(course)
    db.session.commit()

    _make_student(db, "nonstaff")
    login(client, "nonstaff")
    resp = client.post(f"/courses/{course.id}/sections/new", data={"name": "Quizzes", "weight": 50})
    assert resp.status_code == 403


def test_grade_calculation_zero_for_ungraded_sections():
    """Unit-level test of the pure grading function — no request context needed."""
    from app import create_app
    from app.extensions import db as _db
    from app.utils.grades import course_total

    app = create_app("testing")
    with app.app_context():
        _db.create_all()

        instructor = make_user(_db, "grade_instr", "grade_instr@test.com", "GI", RoleEnum.INSTRUCTOR, ApprovalStatusEnum.APPROVED)
        course = Course(code="CS130", title="Grading", term="Fall 2026", is_published=True, created_by=instructor.id)
        _db.session.add(course)
        _db.session.commit()

        section_a = Section(course_id=course.id, name="A", weight=50)
        section_b = Section(course_id=course.id, name="B", weight=50)
        _db.session.add_all([section_a, section_b])
        _db.session.commit()

        activity_a = Activity(section_id=section_a.id, name="Quiz", activity_type=ActivityTypeEnum.QUIZ, total_marks=20)
        _db.session.add(activity_a)
        _db.session.commit()

        student = make_user(_db, "grade_stud", "grade_stud@test.com", "GS", RoleEnum.STUDENT, None)
        _db.session.add(Enrollment(course_id=course.id, student_id=student.id))
        _db.session.add(Mark(activity_id=activity_a.id, student_id=student.id, obtained_marks=18, entered_by=instructor.id))
        _db.session.commit()

        total = course_total(student.id, course)
        # 18/20 = 90% on section A (50% weight); section B ungraded counts as 0% (50% weight)
        assert round(total["current_percentage"], 1) == 45.0

        _db.session.remove()
        _db.drop_all()