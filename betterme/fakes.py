# -*- coding: utf-8 -*-

import os
import random
from PIL import Image
from faker import Faker
from flask import current_app

from betterme.extensions import db
from betterme.models import User, Role, Photo, Post, Tag, Comment

fake = Faker()


def fake_admin():
    admin = User(name='lianziqingtang',
                 username='lzqt',
                 email='659733166@qq.com',
                 bio=fake.sentence(),
                 website='http://www.balthasar.cn',
                 confirmed=True)
    admin.set_password('123456')
    db.session.add(admin)
    db.session.commit()


def fake_user(count=10):
    for i in range(count):
        user = User(name=fake.name(),
                    confirmed=True,
                    username=fake.user_name(),
                    bio=fake.sentence(),
                    location=fake.city(),
                    website=fake.url(),
                    member_since=fake.date_this_decade(),
                    email=fake.email())
        user.set_password('123456')
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

def fake_tag(count=20):
    for i in range(count):
        tag = Tag(name=fake.word())
        db.session.add(tag)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_post(count=30):
    upload_path = current_app.config['UPLOAD_PATH']
    for i in range(count):
        print(i)
        body = fake.sentence()
        filename = 'random_%d.jpg' % i
        r = lambda: random.randint(128, 255)
        img = Image.new(mode='RGB', size=(800, 800), color=(r(), r(), r()))

        user = User.query.get(random.randint(1, User.query.count()))
        upload_path =os.path.join(current_app.config['UPLOAD_PATH'], user.name)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        img.save(os.path.join(upload_path, filename))
        post = Post(
            body=body,
            user=user,
            timestamp=fake.date_time_this_year(),
        )
        for j in range(5):
            tag = Tag.query.get(random.randint(1, Tag.query.count()))
            if tag not in post.tags:
                post.tags.append(tag)
        db.session.add(post)

        photo = Photo(
            filename=filename,
            m_filename=filename,
            s_filename=filename,
            user=user,
            post=post,
            connected=True,
        )
        db.session.add(photo)
    
    db.session.commit()
    


def fake_comment(count=100):
    for i in range(count):
        comment = Comment(
            user=User.query.get(random.randint(1, User.query.count())),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            post=Post.query.get(random.randint(1, Post.query.count()))
        )
        db.session.add(comment)
    db.session.commit()
