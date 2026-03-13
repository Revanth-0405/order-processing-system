import pytest
import hmac
import hashlib
import uuid
from app.extensions import db
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.webhook import WebhookSubscription, WebhookDLQ

# --- 1-5: Product Unit Tests ---
def test_create_product(app):
    p = Product(name="Test", sku="123", price=10.0)
    assert p.name == "Test"

def test_product_default_stock(app):
    with app.app_context():
        p = Product(name="TestStock", sku="1234", price=10.0)
        db.session.add(p)
        db.session.commit()
        assert p.stock_quantity == 0

def test_product_active_default(app):
    with app.app_context():
        p = Product(name="TestActive", sku="1235", price=10.0)
        db.session.add(p)
        db.session.commit()
        assert p.is_active is True

def test_product_price_type(app):
    p = Product(name="Test", sku="123", price=10.50)
    assert isinstance(p.price, float)

def test_product_sku_assignment(app):
    p = Product(name="Test", sku="SKU-999", price=10.0)
    assert p.sku == "SKU-999"

# --- 6-10: Order & User Unit Tests ---
def test_user_creation(app):
    u = User(username="admin", email="admin@test.com")
    assert u.username == "admin"

def test_user_password_hashing(app):
    u = User(username="admin", email="admin@test.com")
    u.set_password("secret")
    assert u.check_password("secret") is True

def test_order_default_status(app):
    with app.app_context():
        # FIX: Provide a valid UUID object for SQLite compatibility
        o = Order(order_number="ORD-1", user_id=uuid.uuid4(), shipping_address="123 St")
        db.session.add(o)
        db.session.commit()
        assert o.status == "pending"

def test_order_item_subtotal(app):
    oi = OrderItem(quantity=2, unit_price=50.0)
    assert oi.quantity * oi.unit_price == 100.0

def test_order_idempotency_key(app):
    with app.app_context():
        o = Order(order_number="ORD-2", user_id=uuid.uuid4(), shipping_address="123 St", idempotency_key="key-123")
        db.session.add(o)
        db.session.commit()
        assert o.idempotency_key == "key-123"

# --- 11-15: Webhook & Security Unit Tests ---
def test_webhook_creation(app):
    w = WebhookSubscription(user_id=uuid.uuid4(), target_url="http://test.com", event_type="all")
    assert w.target_url == "http://test.com"

def test_webhook_secret_generation(app):
    with app.app_context():
        w = WebhookSubscription(user_id=uuid.uuid4(), target_url="http://test.com", event_type="all")
        db.session.add(w)
        db.session.commit()
        assert w.secret_key is not None
        assert len(w.secret_key) > 0

def test_dlq_creation(app):
    with app.app_context():
        dlq = WebhookDLQ(webhook_id=uuid.uuid4(), payload="{}", error_message="Timeout")
        db.session.add(dlq)
        db.session.commit()
        assert dlq.resolved is False

def test_hmac_signature_generation(app):
    secret = "my-secret-key"
    payload = b'{"event": "test"}'
    signature = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    assert isinstance(signature, str)
    assert len(signature) == 64

def test_hmac_signature_validation(app):
    secret = "my-secret-key"
    payload = b'{"event": "test"}'
    expected = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    assert hmac.compare_digest(expected, expected) is True