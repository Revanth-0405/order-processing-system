import requests
import hmac
import hashlib
import json
import time
from app.utils.logger import setup_logger
from app.models.webhook import WebhookSubscription, WebhookDLQ
from app.models.order import Order
from app.services.dynamodb_service import DynamoDBService
from app.extensions import db

logger = setup_logger(__name__, service_name="lambda_send_webhook")

def handler(event, context):
    request_id = event.get('request_id', 'N/A')
    logger.info(f"Lambda send_webhook invoked for order {event.get('order_id')}", extra={'request_id': request_id})
    
    order_id = event.get('order_id')
    event_type = event.get('event_type')
    payload = event.get('payload', {})

    order = Order.query.get(order_id)
    if not order: return {"status": "error"}

    subscriptions = WebhookSubscription.query.filter_by(user_id=order.user_id, is_active=True).filter(
        (WebhookSubscription.event_type == event_type) | (WebhookSubscription.event_type == 'all')
    ).all()

    results = []
    
    # Standardized Payload
    delivery_payload = {"event": event_type, "order_id": str(order_id), "data": payload}
    payload_bytes = json.dumps(delivery_payload, separators=(',', ':')).encode('utf-8')

    for sub in subscriptions:
        # RATE LIMITING LOGIC
        delivery_count = DynamoDBService.get_delivery_count_last_hour(sub.id)
        if delivery_count >= 100:
            logger.warning(f"RATE LIMIT EXCEEDED: Webhook {sub.id} has {delivery_count} deliveries in the last hour. Skipping.", extra={'request_id': request_id})
            continue # Skip to the next subscriber!

        signature = hmac.new(sub.secret_key.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        headers = {'Content-Type': 'application/json', 'X-Webhook-Signature': signature}
        
        max_retries = 3
        success = False
        status_code = None
        error_msg = None
        
        # Exponential backoff retry loop
        for attempt in range(max_retries):
            try:
                resp = requests.post(sub.target_url, data=payload_bytes, headers=headers, timeout=5)
                status_code = resp.status_code
                if resp.ok:
                    success = True
                    break 
                error_msg = f"HTTP {status_code}"
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt) 
        
        # --- BONUS: CIRCUIT BREAKER LOGIC ---
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
                # In a real app, you would queue an email to the user here.
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