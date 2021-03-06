# -*- coding: utf-8 -*-

import os

import click
from flask import Flask, render_template

from betterme.blueprints.main import main_bp
from betterme.blueprints.user import user_bp
from betterme.blueprints.auth import auth_bp
from betterme.blueprints.ajax import ajax_bp
from betterme.blueprints.admin import admin_bp
from betterme.extensions import bootstrap, db, mail, moment, login_manager, dropzone, csrfprotect, avatars, \
                                whooshee, toolbar, migrate
from betterme.configs import config
from betterme.models import User, Role, Post, Photo, Collect


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('betterme')

    app.config.from_object(config[config_name])

    register_extensions(app)
    register_bluprints(app)
    register_commands(app)
    register_errorhandlers(app)
    register_shell_context(app)
    register_template_context(app)

    return app


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)
    dropzone.init_app(app)
    csrfprotect.init_app(app)
    avatars.init_app(app)
    whooshee.init_app(app)
    migrate.init_app(app, db=db)
    toolbar.init_app(app)

def register_bluprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ajax_bp, url_prefix='/ajax')
    app.register_blueprint(admin_bp, url_prefix='/admin')


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Post=Post, Photo=Photo, Collect=Collect)


def register_template_context(app):
    pass


def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden_request(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Drop and create new database')
    def initdb(drop):
        if drop:
            click.confirm(
                'This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop database')
        db.create_all()
        click.echo('Create new database')

    @app.cli.command()
    def init():
        click.echo('Initializing the database...')
        db.create_all()
        Role.init_role()
        click.echo('Done.')

    @app.cli.command()
    @click.option('--user', default=10, help='Number of user')
    @click.option('--post', default=30, help='Number of post')
    @click.option('--tag', default=20, help='Quantity of tags, default is 500.')
    @click.option('--comment', default=100, help='Quantity of comments, default is 500.')
    def forge(user, post, tag, comment):
        from betterme.fakes import fake_admin, fake_user, fake_post, fake_post, fake_tag, fake_comment
        db.drop_all()
        db.create_all()
        Role.init_role()
        click.echo('Generating the administrator...')
        fake_admin()
        click.echo('Generating %d users...' % user)
        fake_user(user)
        click.echo('Generating the tag...')
        fake_tag(tag)
        click.echo('Generating the post...')
        fake_post(post)
        click.echo('Generating the comment...')
        fake_comment(comment)
        click.echo('Done.')
        pass

