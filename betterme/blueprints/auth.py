# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, Blueprint
from flask_login import login_user, logout_user, login_required, current_user, login_fresh, confirm_login

from betterme.emails import send_confirm_email, send_reset_password_email
from betterme.extensions import db
from sqlalchemy.sql.expression import func
from betterme.forms.auth import LoginForm, RegisterForm, ForgetPasswordForm, ResetPasswordForm
from betterme.models import User, Photo
from betterme.configs import Operations
from betterme.utils import generate_token, validate_token, redirect_back
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    photos = Photo.query.order_by(func.random()).limit(4)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('Login success.', 'info')
            return redirect_back()
        flash('Invalid email or password.', 'warning')
    return render_template('auth/login.html', form=form, photos=photos)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Success', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    photos = Photo.query.order_by(func.random()).limit(4)
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = form.password.data
        user = User(name=name, email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        token = generate_token(user=user, operation='confirm')
        send_confirm_email(user=user, token=token)
        flash('Confirm email sent, check your inbox.', 'info')
        return redirect(url_for('.login'))
    return render_template('auth/register.html', form=form, photos=photos)

@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return rediect(url_for('main.index'))

    if validate_token(user=current_user, token=token, operation=Operations.CONFIRM):
        flash('邮箱已验证', 'success')
        return redirect(url_for('main.index'))
    else:
        flash('验证连接非法或已过期', 'danger')
        return redirect(url_for('.resend_confirm_email'))

@auth_bp.route('/resend-confirm-email')
@login_required
def resend_confirm_email():
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    token = generate_token(user=current_user, operation=Operations.CONFIRM)
    send_confirm_email(user=current_user, token=token)
    flash('新的验证连接已发送，请检查邮箱', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('forget-password', methods=['GET', 'POST'])
def forget_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ForgetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_token(user=user, operation=Operations.RESET_PASSWORD)
            senf_reset_password_email(user=user, token=token)
            flash('验证连接已发送，请检查邮箱', 'info')
            return redirect(url_for('.login'))
        flash('用户不存在', 'warning')
        return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('用户不存在', 'warning')
            return redirect(url_for('main.index'))
        elif validate_token(user=user, token=token, operation=Operations.RESET_PASSWORD, new_password=form.password.data):
            flash('密码已修改', 'success')
            return redirect(url_for('.login'))
        else:
            flash('链接非法或已过期', 'danger')
            return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)