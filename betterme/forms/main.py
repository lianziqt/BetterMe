from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, Optional
from wtforms import ValidationError

from betterme.models import User, Post, Photo

class PostForm(FlaskForm):
    body = StringField('Post', validators=[DataRequired(), Length(1,144)])
    submit = SubmitField('')


class TagForm(FlaskForm):
    tag = StringField('Add Tag (use space to separate)', validators=[Optional(), Length(0, 64)])
    submit = SubmitField()


class CommentForm(FlaskForm):
    body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField()
