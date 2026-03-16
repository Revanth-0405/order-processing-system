import pytest
import uuid
import requests
from lambdas.process_order.handler import handler as process_order_handler
from lambdas.update_inventory.handler import handler as update_inventory_handler
from lambdas.send_webhook.handler import handler as send_webhook_handler

# --- process_order Lambda Tests ---
def test_process_order_ping_success():
    event = {"action": "ping"}
    result = process_order_handler(event, {})
    assert result == {"status": "ok", "message": "pong"}

def test_process_order_missing_order(mocker, app):
    mocker.patch('app.models.order.Order.query', mocker.Mock(get=mocker.Mock(return_value=None)))
    event = {"order_id": str(uuid.uuid4()), "action": "order_created"}
    result = process_order_handler(event, {})
    assert result == {"status": "error", "message": "Order not found"}

# --- update_inventory Lambda Tests ---
def test_update_inventory_missing_order(mocker, app):
    mocker.patch('app.models.order.Order.query', mocker.Mock(get=mocker.Mock(return_value=None)))
    event = {"order_id": str(uuid.uuid4()), "action": "reduce_stock"}
    result = update_inventory_handler(event, {})
    assert result == {"status": "error", "message": "Order not found"}

def test_update_inventory_invalid_action(mocker, app):
    mock_order = mocker.Mock()
    mocker.patch('app.models.order.Order.query', mocker.Mock(get=mocker.Mock(return_value=mock_order)))
    event = {"order_id": str(uuid.uuid4()), "action": "explode_stock"}
    result = update_inventory_handler(event, {})
    assert result.get("status") == "error"

# --- send_webhook Lambda Tests ---
def test_send_webhook_missing_order(mocker, app):
    mocker.patch('app.extensions.db.session.get', return_value=None)
    event = {"order_id": str(uuid.uuid4()), "event_type": "order_created"}
    result = send_webhook_handler(event, {})
    assert result == {"status": "error"}

def test_send_webhook_no_subscribers(mocker, app):
    mock_order = mocker.Mock()
    mock_order.id = uuid.uuid4()
    mock_order.order_number = "ORD-TEST"
    mock_order.status = "pending"
    mock_order.user_id = uuid.uuid4()
    mock_order.total_amount = 100.00
    mock_order.items = []
    
    mocker.patch('app.extensions.db.session.get', return_value=mock_order)
    
    mock_ws_query = mocker.Mock()
    mock_ws_query.filter_by.return_value.all.return_value = []
    mocker.patch('app.models.webhook.WebhookSubscription.query', mock_ws_query)
    
    event = {"order_id": str(uuid.uuid4()), "event_type": "order_created"}
    result = send_webhook_handler(event, {})
    assert result == {"status": "success", "processed": 0, "results": []}

# --- FIX 7: Circuit Breaker Test ---
def test_circuit_breaker_trips(mocker, app):
    from app.models.webhook import WebhookSubscription
    import uuid
    import requests
    
    mocker.patch('app.services.dynamodb_service.DynamoDBService.get_delivery_count_last_hour', return_value=0)
    mocker.patch('app.services.dynamodb_service.DynamoDBService.log_delivery')
    
    mock_order = mocker.Mock()
    mock_order.id = uuid.uuid4()
    mock_order.order_number = "ORD-TEST"
    mock_order.status = "pending"
    mock_order.user_id = uuid.uuid4()
    mock_order.total_amount = 100.00
    mock_order.items = []
    mocker.patch('app.extensions.db.session.get', return_value=mock_order)
    
    mock_sub = WebhookSubscription(id=uuid.uuid4(), user_id=mock_order.user_id, target_url="http://fail.com", event_types=["all"])
    mock_sub.failure_count = 4
    mock_sub.is_active = True
    mock_sub.secret_key = "fake-secret-key-for-testing"
    
    mock_ws_query = mocker.Mock()
    mock_ws_query.filter_by.return_value.all.return_value = [mock_sub]
    mocker.patch('app.models.webhook.WebhookSubscription.query', mock_ws_query)
    
    mocker.patch('requests.post', side_effect=requests.exceptions.RequestException("Connection Timeout"))
    
    event = {"order_id": str(uuid.uuid4()), "event_type": "order_created"}
    with app.app_context():
        send_webhook_handler(event, {})
        
    assert mock_sub.failure_count == 5
    assert mock_sub.is_active is False