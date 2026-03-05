import uuid
from datetime import datetime, timezone
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # Added for Phase 1 admin checks
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    orders = db.relationship('Order', backref='user', lazy=True)