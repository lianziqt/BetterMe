from flask import url_for
from betterme.models import Notification, Collect
from betterme.extensions import db

def push_follow_notification(follower, receiver):
    message = '用户 <a href="%s">%s</a> 关注了你' % \
                (url_for('user.index', username=follower.username), follower.username)
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()

def push_collect_notification(collector, collected):
    message = '用户 <a href="%s">%s</a> 收藏了<a href="%s">您的微博</a>. ' % \
                (url_for('user.index', username=collector.username), collector.username, 
                url_for('main.show_post', post_id=collected.id))
    notification = Notification(message=message, receiver=collected.user)
    db.session.add(notification)
    db.session.commit()

def push_comment_notification(post_id, receiver, page=1):
    message = '<a href="%s#comments">您的微博</a>有了新的评论' % \
              (url_for('main.show_post', post_id=post_id, page=page))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()