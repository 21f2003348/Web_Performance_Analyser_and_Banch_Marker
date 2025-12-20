from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired, Email

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    qualification = StringField('Qualification', render_kw={"data-error": "Optional field."})
    dob = DateField('Date of Birth', format='%Y-%m-%d', render_kw={"data-error": "Please enter a valid date."})
    submit = SubmitField('Register', render_kw={"data-error": "Please fill out this field."})

class LoginForm(FlaskForm):
    username = StringField('Username (Email)', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
