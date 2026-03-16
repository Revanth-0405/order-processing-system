from app.extensions import db
from datetime import datetime, timezone
import uuid

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    idempotency_key = db.Column(db.String(100), unique=True, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00) # <--- CRITICAL FIX 1
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    product = db.relationship('Product', backref='order_items') 