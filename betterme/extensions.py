# -*- coding: utf-8 -*-

from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_mail import mail
from flask_sqlalchemy import SQLAlchemy

bootstrap = Bootstrap()
moment = Moment()
mail = Mail()
db = SQLAlchemy()