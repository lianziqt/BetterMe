# -*- coding: utf-8 -*-

from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, AnonymousUserMixin
from flask_dropzone import Dropzone
from flask_wtf.csrf import CsrfProtect
from flask_avatars import Avatars
from flask_whooshee import Whooshee
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import Migrate

migrate = Migrate()
bootstrap = Bootstrap()
moment = Moment()
mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
dropzone = Dropzone()
csrfprotect = CsrfProtect()
avatars = Avatars()
whooshee = Whooshee()
toolbar = DebugToolbarExtension()

@login_manager.user_loader
def load_user(user_id):
    from betterme.models import User
    user = User.query.get(int(user_id))
    return user


class Guest(AnonymousUserMixin):
    @property
    def admin(self):
        return False

    def can(self, permission_name):
        return False


login_manager.anonymous_user = Guest
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
