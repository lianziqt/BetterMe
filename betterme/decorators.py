from functools import wraps 
from flask_login import current_user
from flask import Markup, flash, url_for, redirect, abort

def confirm_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.confirmed:
            message = Markup(
                '请先完成邮件认证流程'
                '没收到邮件？'
                '<a class="alert-link" href="%s">点击这里重新发送</a>' %
                url_for('auth.resend_confirm_email'))
            flash(message, 'warning')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)
    return decorated_function

def permission_required(permission_name):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission_name):
                abort(403)
            return func(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required():
    return permission_required('ADMINISTER')(func)