import uuid
import secrets
from datetime import datetime, timezone
from app.extensions import db

class WebhookSubscription(db.Model):
    __tablename__ = 'webhook_subscriptions'

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    target_url = db.Column(db.String(512), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    
    # NEW: Secure key for HMAC-SHA256 signing
    secret_key = db.Column(db.String(64), default=lambda: secrets.token_hex(32), nullable=False) 
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    failure_count = db.Column(db.Integer, default=0, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'target_url', 'event_type', name='uq_user_url_event'),
    )