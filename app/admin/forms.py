from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional


class DirectCreateUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    role = SelectField(
        "Role",
        choices=[("instructor", "Instructor"), ("ta", "TA"), ("admin", "Admin")],
        validators=[DataRequired()],
    )
    password = PasswordField(
        "Password",
        validators=[Optional(), Length(min=8)],
        description="Leave blank to auto-generate one shown to you once.",
    )