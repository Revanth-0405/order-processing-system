import uuid
from datetime import datetime, timezone
from app.extensions import db

class WebhookSubscription(db.Model):
    __tablename__ = 'webhook_subscriptions'

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    # The external URL where we will send the HTTP POST request
    target_url = db.Column(db.String(512), nullable=False)
    
    # The specific event to listen for (e.g., 'order_confirmed', 'payment_failed', or 'all')
    event_type = db.Column(db.String(50), nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Prevent a user from subscribing the exact same URL to the exact same event twice
    __table_args__ = (
        db.UniqueConstraint('user_id', 'target_url', 'event_type', name='uq_user_url_event'),
    )