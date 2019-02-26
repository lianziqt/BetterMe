# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, request, \
    current_app, Blueprint, abort, make_response, send_from_directory
from flask_login import current_user, login_required

from betterme.decorators import permission_required, confirm_required
from betterme.forms.main import PostForm, TagForm, CommentForm
from betterme.models import User, Post, Photo, Comment, Tag
from betterme.extensions import db
from betterme.utils import rename_image, resize_image, flash_errors

ajax_bp = Blueprint('ajax', __name__)

@ajax_bp.route('/profile/<int:user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('main/profile_popup.html', user=user)