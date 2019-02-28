from flask import url_for
from betterme.models import Notification, Collect
from betterme.extensions import db

def push_follow_notification(follower, receiver):
    message = ' <a href="%s">%s</a> followed you.' % \
                (url_for('user.index', username=follower.username), follower.username)
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()

def push_collect_notification(collector, collected):
    message = ' <a href="%s">%s</a> followed your <a href="%s">post</a>. ' % \
                (url_for('user.index', username=collector.username), collector.username, 
                url_for('main.show_post', post_id=collected.id))
    notification = Notification(message=message, receiver=collected.user)
    db.session.add(notification)
    db.session.commit()

def push_comment_notification(post_id, receiver, page=1):
    message = '<a href="%s#comments">This post</a> has new comment/reply.' % \
              (url_for('main.show_post', post_id=post_id, page=page))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()