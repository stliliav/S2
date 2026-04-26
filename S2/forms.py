from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms import StringField, PasswordField, SubmitField, FileField, IntegerField
from wtforms.validators import DataRequired, EqualTo, ValidationError

from extensions import db
from models import User

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    age = StringField('Age', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat the password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Sign up')

    def validate_username(self, field):
        stmt = select(User).where(User.username == field.data)
        if db.session.execute(stmt).scalar_one_or_none():
            raise ValidationError('Username already exists')

class SignInForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign in')

    def validate_username(self, field):
        stmt = select(User).where(User.username == field.data)

class MovieForm(FlaskForm):
    title = StringField('Movie name', validators=[DataRequired()])
    genres = StringField('Genres', validators=[DataRequired()])
    year = IntegerField('Year of publishing', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    img = FileField('Image')
    submit = SubmitField('Save movie')

class CommentForm(FlaskForm):
    text = StringField('Input your comment', validators=[DataRequired()])
    submit = SubmitField('Post')

class UsernameForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Set new username')

    def validate_username(self, field):
        stmt = select(User).where(User.username == field.data)
        if db.session.execute(stmt).scalar_one_or_none():
            raise ValidationError('Username already exists')


class UserEmailForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Set new email')
    def validate_email(self, field):
        if db.session.execute(select(User).where(User.email == field.data)).scalar_one_or_none():
            raise ValidationError('Email already exists')

class PasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat your password', validators=[DataRequired(), EqualTo('password', message = 'Passwords must match')])
    submit = SubmitField('Change password')