# -*- coding: utf-8 -*-
import os
from flask import render_template, flash, redirect, url_for, request, current_app, Blueprint, abort, make_response,send_from_directory
from flask_login import current_user, login_required

from betterme.decorators import permission_required, confirm_required
from betterme.forms.main import PostForm
from betterme.models import User, Post, Photo
from betterme.extensions import db
from betterme.utils import rename_image, resize_image


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('main/index.html')


@main_bp.route('/explore')
@permission_required('ADMINISTER')
def explore():
    return render_template('main/explore.html')

@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)

@main_bp.route('/uploads/images/<path:filename>')
def get_image(filename):
    user_path = os.path.join(current_app.config['UPLOAD_PATH'], current_user.name)
    return send_from_directory(user_path, filename)

@main_bp.route('/get/<int:post_id>')
def get_first_image(post_id):
    post = Post.query.filter_by(id=post_id).first()
    print(1)
    photos = post.photos
    filename = photos[0].m_filename
    print(filename)
    user_path = os.path.join(current_app.config['UPLOAD_PATH'], current_user.name)
    print(user_path)
    return send_from_directory(user_path, filename)


@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@confirm_required
@permission_required('UPLOAD')
def upload():
    form = PostForm()

    if request.method == 'POST' and 'file' in request.files:
        f = request.files['file']
        filename = rename_image(f.filename)
        path = os.path.join(current_app.config['UPLOAD_PATH'], current_user.name)
        if not os.path.exists(path):
            os.makedirs(path)
        f.save(os.path.join(current_app.config['UPLOAD_PATH'], current_user.name, filename))
        sfname = resize_image(
            f, filename, current_app.config['PHOTO_SIZE']['small'])
        mfname = resize_image(
            f, filename, current_app.config['PHOTO_SIZE']['medium'])

        p = Photo(
            filename=filename,
            s_filename=sfname,
            m_filename=mfname,
            user=current_user._get_current_object(),
        )
        db.session.add(p)
        db.session.commit()

    if form.validate_on_submit():
        body = form.body.data
        user = current_user._get_current_object()
        post = Post(body=body, user=user)
        db.session.add(post)
        unconnect_photos = Photo.query.filter_by(
            user=user).filter_by(connected=False).all()
        if unconnect_photos is not None:
            for p in unconnect_photos:
                p.connected = True
                p.user = user
                p.post = post
                db.session.add(p)
        db.session.commit()
        return redirect(url_for('.index'))
    return render_template('main/upload.html', form=form)


