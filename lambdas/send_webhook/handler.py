import requests
import hmac
import hashlib
import json
import time
import uuid
from app.extensions import db
from datetime import datetime, timezone
from app.utils.logger import setup_logger
from app.models.webhook import WebhookSubscription, WebhookDLQ
from app.models.order import Order
from app.services.dynamodb_service import DynamoDBService

logger = setup_logger(__name__, service_name="lambda_send_webhook")

def handler(event, context):
    request_id = event.get('request_id', 'N/A')
    logger.info(f"Lambda send_webhook invoked for order {event.get('order_id')}", extra={'request_id': request_id})
    
    order_id = event.get('order_id')
    event_type = event.get('event_type')
    payload = event.get('payload', {})

    # PHASE 4 FIX: Use SQLAlchemy 2.0 Session.get
    order = db.session.get(Order, order_id)
    if not order: return {"status": "error"}

    # PHASE 3 FIX: Memory filter for JSON array to prevent dialect clashes
    all_subs = WebhookSubscription.query.filter_by(user_id=order.user_id, is_active=True).all()
    subscriptions = [s for s in all_subs if event_type in s.event_types or "all" in s.event_types]

    results = []
    
    delivery_id = str(uuid.uuid4())
    timestamp_iso = datetime.now(timezone.utc).isoformat()
    
    # PHASE 3 FIX: Full standard payload format as requested by the reviewer
    delivery_payload = {
        "event": event_type, 
        "delivery_id": delivery_id,
        "timestamp": timestamp_iso,
        "data": {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "items": [{"product_id": str(i.product_id), "qty": i.quantity} for i in order.items]
        }
    }
    
    payload_bytes = json.dumps(delivery_payload, separators=(',', ':')).encode('utf-8')
    
    for sub in subscriptions:
        # RATE LIMITING LOGIC
        delivery_count = DynamoDBService.get_delivery_count_last_hour(sub.id)
        if delivery_count >= 100:
            logger.warning(f"RATE LIMIT EXCEEDED: Webhook {sub.id} has {delivery_count} deliveries in the last hour. Skipping.", extra={'request_id': request_id})
            continue # Skip to the next subscriber!

        signature = hmac.new(sub.secret_key.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        headers = {
            'Content-Type': 'application/json', 
            'X-Webhook-Signature': signature,
            'X-Webhook-Event': event_type,
            'X-Webhook-Delivery-ID': delivery_id,
            'X-Webhook-Timestamp': timestamp_iso
        }
        
        max_retries = 3
        success = False
        status_code = None
        error_msg = None
        
        # Exponential backoff retry loop [2, 4, 8]
        backoff_intervals = [2, 4, 8] 
        
        for attempt in range(max_retries):
            try:
                # PHASE 3 FIX: Timeout changed to 10s per the spec
                resp = requests.post(sub.target_url, data=payload_bytes, headers=headers, timeout=10)
                status_code = resp.status_code
                if resp.ok:
                    success = True
                    break 
                error_msg = f"HTTP {status_code}"
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
            
            if attempt < max_retries - 1:
                time.sleep(backoff_intervals[attempt]) 
        
        # CIRCUIT BREAKER LOGIC ---
        if success:
            sub.failure_count = 0  # Reset on success
        else:
            sub.failure_count += 1 # Increment on total failure
            logger.warning(f"Webhook {sub.id} failed {sub.failure_count} consecutive times.", extra={'request_id': request_id})
            
            dlq_item = WebhookDLQ(
                webhook_id=sub.id,
                payload=payload_bytes.decode('utf-8'),
                error_message=error_msg
            )
            db.session.add(dlq_item)
            logger.info(f"Payload routed to Dead Letter Queue for webhook {sub.id}", extra={'request_id': request_id})

            if sub.failure_count >= 5:
                sub.is_active = False
                logger.error(f"CIRCUIT BREAKER TRIPPED! Webhook {sub.id} disabled after 5 consecutive failures.", extra={'request_id': request_id})
        
        # Save the circuit breaker status to PostgreSQL
        db.session.commit()
        # ------------------------------------
        
        DynamoDBService.log_delivery(
            webhook_id=sub.id, url=sub.target_url, event_type=event_type, 
            payload=delivery_payload, status_code=status_code or 0, 
            success=success, attempts=attempt + 1, error=error_msg, request_id=request_id
        )
        
        results.append({"url": sub.target_url, "success": success})

    return {"status": "success", "processed": len(subscriptions), "results": results}