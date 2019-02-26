# -*- coding: utf-8 -*-
import os
from flask import render_template, flash, redirect, url_for, request, \
    current_app, Blueprint, abort, make_response, send_from_directory
from flask_login import current_user, login_required

from betterme.decorators import permission_required, confirm_required
from betterme.forms.main import PostForm, TagForm, CommentForm
from betterme.models import User, Post, Photo, Comment, Tag
from betterme.extensions import db
from betterme.utils import rename_image, resize_image, flash_errors


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


@main_bp.route('/uploads/images/<path:filename>/<int:user_id>')
def get_image(filename, user_id):
    user = User.query.get_or_404(user_id)
    user_path = os.path.join(current_app.config['UPLOAD_PATH'], user.name)
    return send_from_directory(user_path, filename)


@main_bp.route('/get/<int:post_id>')
def get_first_image(post_id):
    post = Post.query.get_or_404(post_id)
    
    photos = post.photos

    filename = photos[0].s_filename
    print(filename)
    user_path = os.path.join(current_app.config['UPLOAD_PATH'], post.user.name)
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
        path = os.path.join(
            current_app.config['UPLOAD_PATH'], current_user.name)
        if not os.path.exists(path):
            os.makedirs(path)
        f.save(os.path.join(
            current_app.config['UPLOAD_PATH'], current_user.name, filename))
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


@main_bp.route('/post/<int:post_id>')
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MANAGE_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(post).order_by(
        Comment.timestamp.desc()).paginate(page, per_page)
    comments = pagination.items

    comment_form = CommentForm()
    post_form = PostForm()
    tag_form = TagForm()

    post_form.body.data = post.body
    return render_template('main/post.html', post=post, comment_form=comment_form,
                           post_form=post_form, tag_form=tag_form,
                           pagination=pagination, comments=comments)


@main_bp.route('/post/next/<int:post_id>')
def next_post(post_id):
    post = Post.query.get_or_404(post_id)
    next_post = Post.query.with_parent(post.user).filter(
        Post.id < post_id).order_by(Post.id.desc()).first()

    if next_post is None:
        flash('This is already the last one.', 'info')
        return redirect(url_for('.show_post', post_id=post_id))
    return redirect(url_for('.show_post', post_id=next_post.id))


@main_bp.route('/post/prev/<int:post_id>')
def previous_post(post_id):
    post = Post.query.get_or_404(post_id)
    previous_post = Post.query.with_parent(post.user).filter(
        Post.id > post_id).order_by(Post.id.asc()).first()

    if previous_post is None:
        flash('This is already the first one.', 'info')
        return redirect(url_for('.show_post', post_id=post_id))
    return redirect(url_for('.show_post', post_id=previous_post.id))


@main_bp.route('/post/<int:post_id>/edit_post', methods=['POST'])
@login_required
def edit_post(post_id):
    postform = PostForm()
    post = Post.query.get_or_404(post_id)

    if current_user != post.user:
        abort(403)
    if postform.validate_on_submit():
        post.body = postform.body.data
        db.session.commit()
        flash('Post updated.', 'success')

    flash_errors(postform)
    return redirect(url_for('.show_post', post_id=post_id))


@main_bp.route('/post/<int:post_id>/comment/new', methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_comment(post_id):
    post = Post.query.get_or_404(post_id)
    page = request.args.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        user = current_user._get_current_object()
        comment = Comment(body=body, user=user, post=post)

        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
        db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')
    flash_errors(form)
    return redirect(url_for('.show_post', post_id=post_id, page=page))


@main_bp.route('/post/<int:post_id>/tag/new', methods=['POST'])
@login_required
def new_tag(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.user:
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.name.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in post.tags:
                post.tags.append(tag)
                db.session.commit()
            flash('Tag added.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_post', post_id=post_id))


@main_bp.route('/set-comment/<int:post_id>', methods=['GET', 'POST'])
@login_required
def set_comment(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.user:
        abort(403)

    if post.can_comment:
        post.can_comment = False
    else:
        post.can_comment = True
    flash('Comment setted', 'info')
    db.session.commit()
    return redirect(url_for('.show_post', post_id=post_id))


@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_post', post_id=comment.post_id, reply=comment_id,
                user=comment.user.name) + '#comment-form')


@main_bp.route('/delete/post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')

    next_post = Post.query.with_parent(post.user).filter(
        Post.id < post_id).order_by(Post.id.desc()).first()
    if next_p is None:
        next_post = Post.query.with_parent(post.user).filter(
            Post.id > post_id).order_by(Post.id.asc()).first()
        if next_post is None:
            return redirect(url_for('user.index', username=post.user.username))
        return redirect(url_for('.show_post', post_id=next_post.id))
    return redirect(url_for('.show_post', post_id=next_post.id))


@main_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.post.user and current_user != comment.user:
        abort(403)

    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted', 'info')
    return redirect(url_for('.show_post', post_id=comment.post_id))

@main_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/tag/<int:tag_id>/<order>')
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MANAGE_COMMENT_PER_PAGE']
    order_rule = 'time'
    pagination = Post.query.with_parent(tag).order_by(Post.timestamp.desc()).paginate(page, per_page)
    posts = pagination.items()

    if order == 'by_collects':
        posts.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    return render_template('main/tag.html', tag=tag, pagination=pagination, posts=posts, order_rule=order_rule)

@main_bp.route('/delete/tag/<int:post_id>/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(post_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    post = Post.query.get_or_404(post_id)
    if current_user != ppost.author:
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()

    if not tag.photos:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))
