# -*- coding: utf-8 -*-
import os
from betterme.extensions import db

from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from datetime import datetime
from flask_avatars import Identicon

roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer,
                                       db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer,
                                       db.ForeignKey('permission.id')),
                             )

tagging = db.Table('tagging',
                   db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                   db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                   )


class Follow(db.Model):
    follower_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    follower = db.relationship('User', foreign_keys=[
                               follower_id], back_populates='following', lazy='joined')
    followed = db.relationship('User', foreign_keys=[
                               followed_id], back_populates='followers', lazy='joined')

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

    l_avatar = db.Column(db.String(64))
    m_avatar = db.Column(db.String(64))
    s_avatar = db.Column(db.String(64))

    confirmed = db.Column(db.Boolean, default=False)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates='users')

    posts = db.relationship('Post', back_populates='user')
    photos = db.relationship('Photo', back_populates='user')

    comments = db.relationship('Comment', back_populates='user')
    collections = db.relationship(
        'Collect', back_populates='collector', cascade='all')

    following = db.relationship('Follow', foreign_keys=[Follow.follower_id], back_populates='follower', lazy='dynamic', cascade='all')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], back_populates='followed', lazy='dynamic', cascade='all')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.set_role()
        self.follow(self)
        self.generate_avatar()

    def set_role(self):
        if self.role is None:
            if self.email == current_app.config['ADMIN_EMAIL']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(name='User').first()
            db.session.commit()

    def generate_avatar(self):
        identicon = Identicon()
        filename = identicon.generate(text=self.email)
        self.l_avatar = filename[2]
        self.m_avatar = filename[1]
        self.s_avatar = filename[0]
        db.session.commit()

    def collect(self, post):
        if not self.collection(post):
            collect = Collect(collector=self, collected=post)
            db.session.add(collect)
            db.session.commit()

    def uncollect(self, photo):
        collect = Collect.query.with_parent(
            self).filter_by(collected_id=photo.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()

    def collection(self, post):
        c = Collect.query.with_parent(self).filter_by(
            collected_id=post.id).first()
        if c is None:
            return False
        return True

    def is_follow(self, user):
        if user.id is None:
            return False
        return self.following.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_follow(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()
    def unfollow(self, user):
        if self.is_follow(user):
            follow = self.following.filter_by(followed_id=user.id).first()
            db.session.delete(follow)
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
    permissions = db.relationship(
        'Permission', secondary=roles_permissions, back_populates='roles')
    users = db.relationship('User', back_populates='role')

    @staticmethod
    def init_role():
        roles_permission_map = {
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
                permission = Permission.query.filter_by(
                    name=permission_name).first()
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
                    user.role = Role.query.filter_by(
                        name='Administrator').first()
                else:
                    user.role = Role.query.filter_by(name='User').first()
            db.session.add(user)
        db.session.commit()


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    roles = db.relationship(
        'Role', secondary=roles_permissions, back_populates='permissions')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(144))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    can_comment = db.Column(db.Boolean, default=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='posts')

    photos = db.relationship('Photo', back_populates='post', cascade='all')
    tags = db.relationship('Tag', secondary=tagging, back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', cascade='all')
    collectors = db.relationship(
        'Collect', back_populates='collected', cascade='all')


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)

    posts = db.relationship('Post', secondary=tagging, back_populates='tags')


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


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(144))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    flag = db.Column(db.Integer, default=0)

    replied_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    post = db.relationship('Post', back_populates='comments')
    user = db.relationship('User', back_populates='comments')
    replied = db.relationship(
        'Comment', back_populates='replies', remote_side=[id])
    replies = db.relationship(
        'Comment', back_populates='replied', cascade='all')


@db.event.listens_for(Photo, 'after_delete', named=True)
def delete_photos(**kwargs):
    target = kwargs['target']
    for filename in [target.filename, target.s_filename, target.m_filename]:
        user_path = os.path.join(
            current_app.config['UPLOAD_PATH'], current_user.name, filename)
        if os.path.exists(user_path):  # not every filename map a unique file
            os.remove(path)


class Collect(db.Model):
    collector_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), primary_key=True)
    collected_id = db.Column(
        db.Integer, db.ForeignKey('post.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    collector = db.relationship(
        'User', back_populates='collections', lazy='joined')
    collected = db.relationship(
        'Post', back_populates='collectors', lazy='joined')



