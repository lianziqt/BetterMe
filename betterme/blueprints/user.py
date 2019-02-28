# -*- coding: utf-8 -*-

from flask import render_template, Blueprint, current_app,request, redirect,url_for, flash
from betterme.models import User, Post, Photo, Collect, Follow
from flask_login import login_required, current_user
from betterme.decorators import confirm_required, permission_required
from betterme.notifications import push_follow_notification


user_bp = Blueprint('user', __name__)

@user_bp.route('/<username>')
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POST_PER_PAGE']
    pagination = Post.query.with_parent(user).order_by(Post.timestamp.desc()).paginate(page, per_page)
    posts = pagination.items
    return render_template('user/index.html', user=user, pagination=pagination, posts=posts)

@user_bp.route('/<username>/collections')
def show_collections(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POST_PER_PAGE']
    pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.desc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('user/collections.html', user=user, pagination=pagination, collects=collects)

@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
@confirm_required
@permission_required('FOLLOW')
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_follow(user):
        flash('You have already followed this user', 'info')
        return redirect(url_for('.index', username=username))
    
    current_user.follow(user)
    flash('Follow successful', 'info')
    if current_user != user:
        push_follow_notification(current_user._get_current_object(), user)
    return redirect(url_for('.index', username=username))

@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
@confirm_required
@permission_required('FOLLOW')
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_follow(user):
        flash('Not follow', 'info')
        return redirect(url_for('.index', username=username))
    
    current_user.unfollow(user)
    flash('Unfollow successful', 'info')
    return redirect(url_for('.index', username=username))

@user_bp.route('/<username>/followers')
def show_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['USER_PER_PAGE']
    pagination = user.followers.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/followers.html', user=user, pagination=pagination, follows=follows)


@user_bp.route('/<username>/following')
def show_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['USER_PER_PAGE']
    pagination = user.following.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/following.html', user=user, pagination=pagination, follows=follows)