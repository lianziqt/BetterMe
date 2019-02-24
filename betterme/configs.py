# -*- coding: utf-8 -*-

import os
import sys

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# sql
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'my secret string')

    PHOTO_PER_PAGE = 12
    COMMENT_PER_PAGE = 15
    NOTIFICATION_PER_PAGE = 20
    USER_PER_PAGE = 20
    MANAGE_PHOTO_PER_PAGE = 20
    MANAGE_USER_PER_PAGE = 30
    MANAGE_TAG_PER_PAGE = 50
    MANAGE_COMMENT_PER_PAGE = 30
    SEARCH_RESULT_PER_PAGE = 20
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # file size exceed to 3 Mb will return a 413 error response.

    ADMIN_EMAIL = os.getenv('BM_ADMIN','659733166@qq.com')
    MAIL_SUBJECT_PREFIX = '[BetterMe]'
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('BetterMe Admin', MAIL_USERNAME)


    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = \
        prefix + os.path.join(basedir, 'data-dev.db')
    REDIS_URL = "redis://localhost"

class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'

class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = \
        os.getenv('DATABASE_URI', prefix + os.path.join(basedir))

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}

class Operations: 
    CONFIRM = 'confirm' 
    RESET_PASSWORD = 'reset-password' 
    CHANGE_EMAIL = 'change-email'