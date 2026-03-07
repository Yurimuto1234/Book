from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional, NumberRange, Length
import sqlalchemy as sa
from app import db
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class AddBookForm(FlaskForm):
    title = StringField('Book Title', validators=[DataRequired(), Length(max=200)])
    author = StringField('Author', validators=[DataRequired(), Length(max=200)])
    genre = SelectField('Genre', choices=[
        ('', '— Select a genre —'),
        ('Fiction', 'Fiction'),
        ('Non-Fiction', 'Non-Fiction'),
        ('Science Fiction', 'Science Fiction'),
        ('Fantasy', 'Fantasy'),
        ('Mystery', 'Mystery'),
        ('Thriller', 'Thriller'),
        ('Romance', 'Romance'),
        ('Poetry', 'Poetry'),
        ('Biography', 'Biography'),
        ('History', 'History'),
        ('Self-Help', 'Self-Help'),
        ('Other', 'Other'),
    ], validators=[DataRequired(message='Please select a genre.')])
    year = IntegerField('Year Published', validators=[
        Optional(),
        NumberRange(min=1, max=2100, message='Enter a valid year.')
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    cover = FileField('Book Cover', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only — JPG, PNG or WEBP.'),
    ])
    submit = SubmitField('Add Book')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')