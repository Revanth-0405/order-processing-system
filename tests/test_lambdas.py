import pytest
import uuid
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
    # FIX: Matched your exact error message
    assert result == {"status": "error", "message": "Order not found"}

# --- update_inventory Lambda Tests ---
def test_update_inventory_missing_order(mocker, app):
    mocker.patch('app.models.order.Order.query', mocker.Mock(get=mocker.Mock(return_value=None)))
    event = {"order_id": str(uuid.uuid4()), "action": "reduce_stock"}
    result = update_inventory_handler(event, {})
    # FIX: Matched your exact error message
    assert result == {"status": "error", "message": "Order not found"}

def test_update_inventory_invalid_action(mocker, app):
    mock_order = mocker.Mock()
    mocker.patch('app.models.order.Order.query', mocker.Mock(get=mocker.Mock(return_value=mock_order)))
    event = {"order_id": str(uuid.uuid4()), "action": "explode_stock"}
    result = update_inventory_handler(event, {})
    assert result.get("status") == "error"

# --- send_webhook Lambda Tests ---
def test_send_webhook_missing_order(mocker, app):
    mocker.patch('app.models.order.Order.query', mocker.Mock(get=mocker.Mock(return_value=None)))
    event = {"order_id": str(uuid.uuid4()), "event_type": "order_created"}
    result = send_webhook_handler(event, {})
    assert result == {"status": "error"}

def test_send_webhook_no_subscribers(mocker, app):
    mock_order = mocker.Mock()
    mock_order.user_id = uuid.uuid4() 
    mocker.patch('app.models.order.Order.query', mocker.Mock(get=mocker.Mock(return_value=mock_order)))
    
    mock_ws_query = mocker.Mock()
    mock_ws_query.filter_by.return_value.filter.return_value.all.return_value = []
    mocker.patch('app.models.webhook.WebhookSubscription.query', mock_ws_query)
    
    event = {"order_id": str(uuid.uuid4()), "event_type": "order_created"}
    result = send_webhook_handler(event, {})
    assert result == {"status": "success", "processed": 0, "results": []}