from tests.helpers import make_user, login
from app.models.user import RoleEnum, ApprovalStatusEnum
from app.models.course import Course, CourseStaff, Enrollment


def test_student_can_export_own_published_course(client, db):
    instructor = make_user(db, "exp_instr", "exp_instr@test.com", "Exp Instr", RoleEnum.INSTRUCTOR, ApprovalStatusEnum.APPROVED)
    course = Course(code="EXP101", title="Export Test", term="Fall 2026", is_published=True, created_by=instructor.id)
    db.session.add(course)
    db.session.commit()

    student = make_user(db, "exp_stud", "exp_stud@test.com", "Exp Student", RoleEnum.STUDENT, None)
    db.session.add(Enrollment(course_id=course.id, student_id=student.id))
    db.session.commit()

    login(client, "exp_stud")
    resp = client.get(f"/courses/{course.id}/export")
    assert resp.status_code == 200
    assert resp.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_staff_cannot_use_student_export_route(client, db):
    instructor = make_user(db, "exp_instr2", "exp_instr2@test.com", "Exp Instr2", RoleEnum.INSTRUCTOR, ApprovalStatusEnum.APPROVED)
    course = Course(code="EXP102", title="Export Test2", term="Fall 2026", is_published=True, created_by=instructor.id)
    db.session.add(course)
    db.session.flush()  # assigns course.id before we reference it below
    db.session.add(CourseStaff(course_id=course.id, user_id=instructor.id))
    db.session.commit()

    login(client, "exp_instr2")
    assert client.get(f"/courses/{course.id}/export").status_code == 403


def test_staff_roster_export_works_for_course_staff(client, db):
    instructor = make_user(db, "exp_instr3", "exp_instr3@test.com", "Exp Instr3", RoleEnum.INSTRUCTOR, ApprovalStatusEnum.APPROVED)
    course = Course(code="EXP103", title="Export Test3", term="Fall 2026", is_published=True, created_by=instructor.id)
    db.session.add(course)
    db.session.flush()  # assigns course.id before we reference it below
    db.session.add(CourseStaff(course_id=course.id, user_id=instructor.id))
    db.session.commit()

    login(client, "exp_instr3")
    resp = client.get(f"/courses/{course.id}/export/roster")
    assert resp.status_code == 200


def test_non_staff_cannot_export_roster(client, db):
    instructor = make_user(db, "exp_instr4", "exp_instr4@test.com", "Exp Instr4", RoleEnum.INSTRUCTOR, ApprovalStatusEnum.APPROVED)
    course = Course(code="EXP104", title="Export Test4", term="Fall 2026", is_published=True, created_by=instructor.id)
    db.session.add(course)
    db.session.commit()

    student = make_user(db, "exp_stud4", "exp_stud4@test.com", "Exp Student4", RoleEnum.STUDENT, None)
    db.session.add(Enrollment(course_id=course.id, student_id=student.id))
    db.session.commit()

    login(client, "exp_stud4")
    assert client.get(f"/courses/{course.id}/export/roster").status_code == 403