from app.models.webhook import WebhookSubscription
from app.extensions import db

class WebhookService:
    @staticmethod
    def get_user_subscriptions(user_id):
        return WebhookSubscription.query.filter_by(user_id=user_id).all()
    # (Move your DB logic from webhooks.py into here to satisfy the Service Layer requirement)