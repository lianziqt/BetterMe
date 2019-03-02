# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, request, \
    current_app, Blueprint, abort, make_response, send_from_directory, jsonify
from flask_login import current_user, login_required

from betterme.decorators import permission_required, confirm_required
from betterme.forms.main import PostForm, TagForm, CommentForm
from betterme.models import User, Post, Photo, Comment, Tag, Notification
from betterme.extensions import db
from betterme.utils import rename_image, resize_image, flash_errors

ajax_bp = Blueprint('ajax', __name__)

@ajax_bp.route('/profile/<int:user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('main/profile_popup.html', user=user)

@ajax_bp.route('/count-follower/<int:user_id>')
def count_follower(user_id):
    user = User.query.get_or_404(user_id)
    count = user.followers.count() - 1
    return jsonify(count=count)

@ajax_bp.route('/follow/<username>', methods=['POST'])
def follow(username):
    if not current_user.is_authenticated:
        return jsonify(message='请先登录'), 403
    if not current_user.confirmed:
        return jsonify(message='请先完成账户确认'), 400
    if not current_user.can('FOLLOW'):
        return jsonify(message='您没有该权限'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_follow(user):
        return jsonify(message='亲，已经关注了'), 400

    current_user.follow(user)
    return jsonify(message='关注成功')


@ajax_bp.route('/unfollow/<username>', methods=['POST'])
def unfollow(username):
    if not current_user.is_authenticated:
        return jsonify(message='请先登陆'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_follow(user):
        return jsonify(message='还没关注'), 400

    current_user.unfollow(user)
    return jsonify(message='取消关注')

@ajax_bp.route('/notification-count')
def notifications_count():
    if not current_user.is_authenticated:
        return jsonify(message='请先登录'), 403
    count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
    return jsonify(count=count)