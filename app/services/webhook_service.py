from app.models.webhook import WebhookSubscription
from app.extensions import db

class WebhookService:
    @staticmethod
    def get_all_by_user(user_id):
        return WebhookSubscription.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_user_webhook(webhook_id, user_id):
        return WebhookSubscription.query.filter_by(id=webhook_id, user_id=user_id).first_or_404()

    @staticmethod
    def create_webhook(user_id, target_url, event_types):
        # Check for duplicates
        existing = WebhookSubscription.query.filter_by(user_id=user_id, target_url=target_url).first()
        if existing:
            raise ValueError("Duplicate webhook")
            
        webhook = WebhookSubscription(user_id=user_id, target_url=target_url, event_types=event_types)
        db.session.add(webhook)
        db.session.commit()
        return webhook
        
    @staticmethod
    def update_webhook(webhook, data):
        webhook.target_url = data.get('target_url', webhook.target_url)
        # Safely handle the Phase 3 JSON array upgrade
        webhook.event_types = data.get('event_types', webhook.event_types) 
        webhook.is_active = data.get('is_active', webhook.is_active)
        db.session.commit()
        return webhook

    @staticmethod
    def toggle_webhook(webhook):
        webhook.is_active = not webhook.is_active
        db.session.commit()
        return webhook

    @staticmethod
    def delete_webhook(webhook):
        db.session.delete(webhook)
        db.session.commit()