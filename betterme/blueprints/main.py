# -*- coding: utf-8 -*-
import os, random
from flask import render_template, flash, redirect, url_for, request, \
    current_app, Blueprint, abort, make_response, send_from_directory
from flask_login import current_user, login_required
from sqlalchemy.sql.expression import func

from betterme.decorators import permission_required, confirm_required
from betterme.forms.main import PostForm, TagForm, CommentForm
from betterme.models import User, Post, Photo, Comment, Tag, Collect, Notification,Follow
from betterme.extensions import db
from betterme.utils import rename_image, resize_image, flash_errors,redirect_back
from betterme.notifications import push_collect_notification, push_comment_notification


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['POST_PER_PAGE']
        pagination = Post.query\
                .join(Follow, Follow.followed_id == Post.user_id)\
                .filter(Follow.follower_id == current_user.id)\
                .order_by(Post.timestamp.desc())\
                .paginate(page, per_page)
        posts = pagination.items
        photos = None
        tags = Tag.query.join(Tag.posts).group_by(Tag.id).order_by(func.count(Post.id).desc()).limit(8)
    else:
        photos = Photo.query.order_by(func.random()).limit(4)
        posts = None
        pagination = None
        tags = None
    return render_template('main/index.html', posts=posts, photos=photos, pagination=pagination, tags=tags)


@main_bp.route('/explore')
def explore():
    posts = Post.query.order_by(func.random()).limit(12) 
    return render_template('main/explore.html', posts=posts)

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
    filename = photos[0].m_filename
    user_path = os.path.join(current_app.config['UPLOAD_PATH'], post.user.name)
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
        sfname = resize_image(f, filename, current_app.config['PHOTO_SIZE']['small'])
        mfname = resize_image(f, filename, current_app.config['PHOTO_SIZE']['medium'])

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
        flash('已经是最早的微博', 'info')
        return redirect(url_for('.show_post', post_id=post_id))
    return redirect(url_for('.show_post', post_id=next_post.id))


@main_bp.route('/post/prev/<int:post_id>')
def previous_post(post_id):
    post = Post.query.get_or_404(post_id)
    previous_post = Post.query.with_parent(post.user).filter(
        Post.id > post_id).order_by(Post.id.asc()).first()

    if previous_post is None:
        flash('已经是最新的微博', 'info')
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
        flash('微博已编辑', 'success')

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
        flash('评论已提交', 'success')
        if current_user != post.user:
            push_comment_notification(post.id, receiver=post.user, page=page)
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
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in post.tags:
                post.tags.append(tag)
                db.session.commit()
            flash('标签已添加', 'success')

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
        flash('评论已关闭', 'info')
    else:
        post.can_comment = True
        flash('评论已开启','info')
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
    flash('微博已删除', 'info')

    next_post = Post.query.with_parent(post.user).filter(
        Post.id < post_id).order_by(Post.id.desc()).first()
    if next_post is None:
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
    flash('评论已删除', 'info')
    return redirect(url_for('.show_post', post_id=comment.post_id))


@main_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/tag/<int:tag_id>/<order>')
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MANAGE_COMMENT_PER_PAGE']
    order_rule = 'time'
    pagination = Post.query.with_parent(tag).order_by(
        Post.timestamp.desc()).paginate(page, per_page)
    posts = pagination.items

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

    flash('标签已删除', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/collect/<int:post_id>', methods=['POST'])
@login_required
@confirm_required
@permission_required('COLLECT')
def collect_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user.collection(post):
        flash('已在收藏中', 'info')
        return redirect(url_for('.show_post', post_id=post_id))

    current_user.collect(post)
    flash('收藏成功', 'success')
    if current_user != post.user:
        push_collect_notification(current_user._get_current_object(), post)
    return redirect(url_for('.show_post', post_id=post_id))


@main_bp.route('/uncollect/<int:post_id>', methods=['POST'])
@login_required
def uncollect_post(post_id):
    post=Post.query.get_or_404(post_id)
    if not current_user.collection(post):
        flash('你未收藏该微博', 'info')
        return redirect(url_for('.show_post', post_id=post_id))

    current_user.uncollect(post)
    flash('已从收藏中移除', 'success')
    return redirect(url_for('.show_post', post_id=post_id))

@main_bp.route('/photo/<int:post_id>/collectors')
def show_collectors(post_id):
    post=Post.query.get_or_404(post_id)
    page=request.args.get('page', 1, type=int)
    per_page=current_app.config['USER_PER_PAGE']
    pagination=Collect.query.with_parent(post).order_by(
        Collect.timestamp.asc()).paginate(page, per_page)
    collects=pagination.items
    return render_template('main/collectors.html', collects=collects, post=post, pagination=pagination)

@main_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)

    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)

@main_bp.route('/read-notification/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)
    notification.is_read = True
    db.session.commit()
    flash('通知已读', 'success')
    return redirect(url_for('.show_notifications'))

@main_bp.route('/read-all-notifications', methods=['POST'])
@login_required
def read_all_notifications():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash('所有通知已读', 'success')
    return redirect(url_for('.show_notifications'))

@main_bp.route('/search')
def search():
    t= request.args.get('t', '')
    if t == '':
        flash('请输入搜索关键词', 'warning') 
        return redirect_back()
    category = request.args.get('category', 'post')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['SEARCH_RESULT_PER_PAGE']
    try :
        posts = Post.query.whooshee_search(t)
        tags = Tag.query.whooshee_search(t)
        users =  User.query.whooshee_search(t)
        if category == 'post':
            pagination = posts.paginate(page, per_page)
        elif category == 'tag':
            pagination = tags.paginate(page, per_page)
        else:
            pagination = users.paginate(page, per_page)
    except :
        flash('请输入合法搜索关键词', 'warning') 
        return redirect_back()
    results = pagination.items
    return render_template('main/search.html', t=t, results=results, pagination=pagination, category=category, \
                            posts=posts.count(), tags=tags.count(), users=users.count())
