from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, Optional
from wtforms import ValidationError

from betterme.models import User, Post, Photo

class PostForm(FlaskForm):
    body = StringField('微博内容', validators=[DataRequired(), Length(1,144)])
    submit = SubmitField('发布')


class TagForm(FlaskForm):
    tag = StringField('添加标签（空格分隔）', validators=[Optional(), Length(0, 64)])
    submit = SubmitField('添加')


class CommentForm(FlaskForm):
    body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField('发布')
