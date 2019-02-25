# -*- coding: utf-8 -*-

from betterme.extensions import db

from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from datetime import datetime
from flask_avatars import Identicon

roles_permissions = db.Table('roles_permissions', 
                    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id')),
                )

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, index=True)
    email = db.Column(db.String(32), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(20))
    website = db.Column(db.String(255))
    bio = db.Column(db.String(120))
    location = db.Column(db.String(120))
    member_since = db.Column(db.DateTime, default=datetime.utcnow)

    large_avatar = db.Column(db.String(64))
    medium_avatar = db.Column(db.String(64))
    small_avatar = db.Column(db.String(64))

    confirmed = db.Column(db.Boolean, default=False)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates='users')

    posts = db.relationship('Post', back_populates='user')
    photos = db.relationship('Photo', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.set_role()
        self.generate_avatar()

    def set_role(self):
        if self.role is  None:
            if self.email == current_app.config['ADMIN_EMAIL']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(name='User').first()
            db.session.commit()
    
    def generate_avatar(self):
        identicon = Identicon()
        filename = identicon.generate(text=self.email)
        self.large_avatar = filename[2]
        self.medium_avatar = filename[1]
        self.small_avatar = filename[0]
        db.session.commit()

    @property
    def admin(self):
        return self.role.name == 'Administrator'
    
    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permissions

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    permissions = db.relationship('Permission', secondary=roles_permissions, back_populates='roles')
    users = db.relationship('User', back_populates='role')

    @staticmethod
    def init_role():
        roles_permission_map={
            'Locked': ['FOLLOW', 'COLLECT'],
            'User': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD'],
            'Moderator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE'],
            'Administrator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE', 'ADMINISTER']
        }
        for role_name in roles_permission_map:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
            role.permissions = []
            for permission_name in roles_permission_map[role_name]:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permissions.append(permission)
        db.session.commit()

    @staticmethod
    def init_role_permission():
        for user in User.query.all():
            if user.role is None:
                if user.email == current_user.config['ADMIN_EMAIL']:
                    user.role = Role.query.filter_by(name='Administrator').first()
                else:
                    user.role = Role.query.filter_by(name='User').first()
            db.session.add(user)
        db.session.commit()

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    roles = db.relationship('Role', secondary=roles_permissions, back_populates='permissions')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(144))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    can_comment = db.Column(db.Boolean, default=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='posts')

    photos = db.relationship('Photo', back_populates='post', cascade='all')

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64), unique=True, index=True)
    s_filename = db.Column(db.String(66))
    m_filename = db.Column(db.String(66))
    connected = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='photos')

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', back_populates='photos')


