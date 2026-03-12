import logging
import requests
import hmac
import hashlib
import json
import time
from app.models.webhook import WebhookSubscription
from app.models.order import Order
from app.services.dynamodb_service import DynamoDBService

logger = logging.getLogger(__name__)

def handler(event, context):
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
        # 1. HMAC-SHA256 SIGNING
        signature = hmac.new(sub.secret_key.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        headers = {'Content-Type': 'application/json', 'X-Webhook-Signature': signature}
        
        # 2. EXPONENTIAL BACKOFF RETRY LOGIC (Max 3 attempts: 0s, 2s, 4s)
        max_retries = 3
        success = False
        status_code = None
        error_msg = None
        
        for attempt in range(max_retries):
            try:
                resp = requests.post(sub.target_url, data=payload_bytes, headers=headers, timeout=5)
                status_code = resp.status_code
                if resp.ok:
                    success = True
                    break # Success! Exit the retry loop
                error_msg = f"HTTP {status_code}"
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
            
            # If not successful and not the last attempt, backoff and retry
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt) # Waits 1s, then 2s
        
        # 3. DYNAMODB LOGGING
        DynamoDBService.log_delivery(
            webhook_id=sub.id, url=sub.target_url, event_type=event_type, 
            payload=delivery_payload, status_code=status_code or 0, 
            success=success, attempts=attempt + 1, error=error_msg
        )
        
        results.append({"url": sub.target_url, "success": success})

    return {"status": "success", "processed": len(subscriptions), "results": results}