from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Length


class CourseForm(FlaskForm):
    code = StringField("Course code", validators=[DataRequired(), Length(max=20)])
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    term = StringField("Term", validators=[DataRequired(), Length(max=40)])
    is_published = BooleanField("Published (visible to enrolled students)")