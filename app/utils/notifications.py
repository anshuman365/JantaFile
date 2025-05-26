from app import db
from flask import current_app
from app.models import Subscription
from pywebpush import webpush, WebPushException
import json
import os

def send_push_notification(title, message, url):
    subscriptions = Subscription.query.all()
    vapid_claims = {
        "sub": "mailto:contact@jantafile.in",
        "public_key": current_app.config['VAPID_PUBLIC_KEY'],
        "private_key": current_app.config['VAPID_PRIVATE_KEY']
    }

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": json.loads(sub.keys)
                },
                data=json.dumps({
                    "title": title,
                    "body": message,
                    "icon": "/static/images/icon-192x192.png",
                    "url": url
                }),
                vapid_private_key=vapid_claims['private_key'],
                vapid_claims=vapid_claims
            )
        except WebPushException as e:
            print("Push failed:", e)
            if e.response.status_code == 410:
                db.session.delete(sub)
                db.session.commit()