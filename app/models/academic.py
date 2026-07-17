import enum
from datetime import datetime

from app.extensions import db


class ActivityTypeEnum(str, enum.Enum):
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    MIDTERM = "midterm"
    FINAL = "final"
    CUSTOM = "custom"


class Section(db.Model):
    __tablename__ = "sections"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False, default=0.0)  # % of course grade
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    course = db.relationship("Course", backref=db.backref("sections", cascade="all, delete-orphan"))
    activities = db.relationship("Activity", back_populates="section", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("course_id", "name", name="uq_section_name_per_course"),
    )

    def __repr__(self):
        return f"<Section {self.name} ({self.weight}%)>"


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    activity_type = db.Column(db.Enum(ActivityTypeEnum), nullable=False, default=ActivityTypeEnum.CUSTOM)
    total_marks = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    section = db.relationship("Section", back_populates="activities")

    __table_args__ = (
        db.UniqueConstraint("section_id", "name", name="uq_activity_name_per_section"),
    )

    def __repr__(self):
        return f"<Activity {self.name} /{self.total_marks}>"