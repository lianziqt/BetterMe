from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError

from betterme.models import User, Post, Photo

class PostForm(FlaskForm):
    body = StringField('Post', validators=[DataRequired(), Length(1,144)])
    submit = SubmitField('')
