from datetime import datetime

from app.extensions import db


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)          # e.g. "CS101"
    title = db.Column(db.String(200), nullable=False)
    term = db.Column(db.String(40), nullable=False)          # e.g. "Fall 2026"
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship("User", foreign_keys=[created_by])
    staff = db.relationship("CourseStaff", back_populates="course", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    pending_enrollments = db.relationship(
        "PendingEnrollment", back_populates="course", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint("code", "term", name="uq_course_code_term"),
    )

    def has_staff(self, user):
        return any(cs.user_id == user.id for cs in self.staff)

    def has_student(self, user):
        return any(e.student_id == user.id for e in self.enrollments)

    def __repr__(self):
        return f"<Course {self.code} {self.term}>"


class CourseStaff(db.Model):
    __tablename__ = "course_staff"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    course = db.relationship("Course", back_populates="staff")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("course_id", "user_id", name="uq_course_staff_unique"),
    )


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    course = db.relationship("Course", back_populates="enrollments")
    student = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("course_id", "student_id", name="uq_enrollment_unique"),
    )


class PendingEnrollment(db.Model):
    """A student invited by email before they have an account. Consumed and
    converted into a real Enrollment once that email signs up (wired up in
    the enrollment stage)."""
    __tablename__ = "pending_enrollments"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    invited_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    course = db.relationship("Course", back_populates="pending_enrollments")

    __table_args__ = (
        db.UniqueConstraint("course_id", "email", name="uq_pending_enrollment_unique"),
    )