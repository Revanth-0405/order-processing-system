import pytest
import json
from app.models.product import Product
from app.extensions import db

def test_health_endpoint(client):
    """Integration Test 1: Verifies the health check endpoint returns correctly"""
    response = client.get('/api/v1/health')
    assert response.status_code in [200, 503]
    assert b"postgres" in response.data

def test_user_registration_flow(client, app):
    """Integration Test 2: Tests the database write for a new user"""
    response = client.post('/api/v1/auth/register', 
                           json={"username": "testuser", "email": "test@user.com", "password": "password123"})
    assert response.status_code == 201
    assert b"User registered successfully" in response.data

def test_order_idempotency_flow(client, app):
    """Integration Test 3: Tests order placement success path and idempotency replay"""
    
    # 1. Register and Login to get the JWT
    client.post('/api/v1/auth/register', json={"username": "buyer", "email": "buyer@test.com", "password": "pass"})
    login_resp = client.post('/api/v1/auth/login', json={"username": "buyer", "password": "pass"})
    token = json.loads(login_resp.data)['access_token']
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Idempotency-Key': 'test-idem-key-999'
    }
    
    # 2. Create a valid product in the test database so we can actually buy it!
    with app.app_context():
        p = Product(name="Test Keyboard", sku="KB-999", price=100.0, stock_quantity=10, is_active=True)
        db.session.add(p)
        db.session.commit()
        product_id = str(p.id)

    # 3. Create a valid, successful order payload
    valid_payload = {
        "items": [{"product_id": product_id, "quantity": 1}],
        "shipping_address": "123 Test Ave"
    }
    
    # 4. First attempt (Should successfully create the order)
    resp1 = client.post('/api/v1/orders', json=valid_payload, headers=headers)
    # FIX: If this fails, it will now print the exact error message to your terminal!
    assert resp1.status_code == 201, f"Order failed! Error: {resp1.data}" 
    
    # 5. Second attempt with the exact same Idempotency-Key
    # The server should catch the duplicate key and return the cached 200 OK response
    resp2 = client.post('/api/v1/orders', json=valid_payload, headers=headers)
    assert resp2.status_code == 200, f"Idempotency replay failed! Error: {resp2.data}"