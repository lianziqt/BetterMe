# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email

from betterme.forms.user import EditProfileForm
from betterme.models import User, Role


class EditProfileAdminForm(EditProfileForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 254), Email()])
    role = SelectField('角色', coerce=int)
    active = BooleanField('激活')
    confirmed = BooleanField('确认')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(email=field.data).first():
            raise ValidationError('用户名已被占用')

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被占用')
