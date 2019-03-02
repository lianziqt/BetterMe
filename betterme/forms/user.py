# -*- coding: utf-8 -*-
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, HiddenField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, Regexp

from betterme.models import User


class EditProfileForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired(), Length(1, 30)])
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20),
                                                   Regexp('^[a-zA-Z0-9]*$',
                                                          message='The username should contain only a-z, A-Z and 0-9.')])
    website = StringField('个人网站', validators=[Optional(), Length(0, 255)])
    location = StringField('城市', validators=[Optional(), Length(0, 50)])
    bio = TextAreaField('个人简介', validators=[Optional(), Length(0, 120)])
    submit = SubmitField('提交')

    def validate_username(self, field):
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被占用')


class UploadAvatarForm(FlaskForm):
    image = FileField('上传头像', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], '文件格式应为JPG或PNG格式')
    ])
    submit = SubmitField('上传')


class CropAvatarForm(FlaskForm):
    x = HiddenField()
    y = HiddenField()
    w = HiddenField()
    h = HiddenField()
    submit = SubmitField('裁剪并更新')


class ChangeEmailForm(FlaskForm):
    email = StringField('新邮箱', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField('提交')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('提交')


class NotificationSettingForm(FlaskForm):
    receive_comment_notification = BooleanField('接收新评论提醒')
    receive_follow_notification = BooleanField('接收新粉丝提醒')
    receive_collect_notification = BooleanField('接收新收藏提醒')
    submit = SubmitField('提交')


class PrivacySettingForm(FlaskForm):
    public_collections = BooleanField('公开我的收藏')
    submit = SubmitField('提交')


class DeleteAccountForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField('提交')

    def validate_username(self, field):
        if field.data != current_user.username:
            raise ValidationError('错误的用户名')
