from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, FloatField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Email
from flask_wtf.file import FileField, FileAllowed, FileRequired


class CourseForm(FlaskForm):
    code = StringField("Course code", validators=[DataRequired(), Length(max=20)])
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    term = StringField("Term", validators=[DataRequired(), Length(max=40)])
    is_published = BooleanField("Published (visible to enrolled students)")


class SectionForm(FlaskForm):
    name = StringField("Section name", validators=[DataRequired(), Length(max=100)])
    weight = FloatField(
        "Weight (% of course grade)",
        validators=[DataRequired(), NumberRange(min=0, max=100)],
    )

class ActivityForm(FlaskForm):
    name = StringField("Activity name", validators=[DataRequired(), Length(max=100)])
    activity_type = SelectField(
        "Type",
        choices=[
            ("quiz", "Quiz"),
            ("assignment", "Assignment"),
            ("midterm", "Midterm"),
            ("final", "Final"),
            ("custom", "Custom"),
        ],
        validators=[DataRequired()],
    )
    total_marks = FloatField(
        "Total marks",
        validators=[DataRequired(), NumberRange(min=0.01, message="Total marks must be greater than 0.")],
    )

class EnrollForm(FlaskForm):
    emails = TextAreaField(
        "Student emails",
        validators=[DataRequired()],
        description="One email per line. Unregistered emails will be invited "
        "and enrolled automatically once that person signs up as a student.",
    )


class MarksImportForm(FlaskForm):
    csv_file = FileField(
        "CSV file",
        validators=[FileRequired(), FileAllowed(["csv"], "CSV files only.")],
    )

class AddCourseStaffForm(FlaskForm):
    email = StringField(
        "Instructor or TA email",
        validators=[DataRequired(), Email(), Length(max=120)],
        description="Must be an existing, approved instructor or TA account.",
    )