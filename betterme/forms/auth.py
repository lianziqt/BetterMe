# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError

from betterme.models import User

class RegisterForm(FlaskForm):
    name = StringField('名称', validators=[DataRequired(), Length(1,20)])
    email = StringField('邮箱', validators=[DataRequired(), Length(1,32), Email()])
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20),
                                                Regexp('^[a-zA-Z0-9]*$',
                                                        message='The username should contain only a-z, A-Z and 0-9.')])

    password = PasswordField('密码', validators=[DataRequired(), Length(8,128), EqualTo('password2')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被占用')
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被占用')

class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1,32), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登陆')

class ForgetPasswordForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1,32), Email()])
    SubmitField = SubmitField('提交')

class ResetPasswordForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 254), Email()])
    password = PasswordField('密码', validators=[
        DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('提交')

