import logging
import requests
from app.models.webhook import WebhookSubscription
from app.models.order import Order

logger = logging.getLogger(__name__)

def handler(event, context):
    """
    AWS Lambda Handler for sending out webhooks.
    Input Event: {
        "order_id": "uuid-string",
        "event_type": "order_confirmed",
        "payload": {...}
    }
    """
    logger.info(f"Lambda send_webhook invoked with event: {event}")
    
    order_id = event.get('order_id')
    event_type = event.get('event_type')
    payload = event.get('payload', {})

    if not order_id or not event_type:
        return {"status": "error", "message": "Missing order_id or event_type"}

    # We need the user_id to find their specific webhooks.
    # Since the event payload might not have it, we look it up via the order.
    order = Order.query.get(order_id)
    if not order:
        return {"status": "error", "message": "Order not found"}

    user_id = order.user_id

    # Find matching active subscriptions for this user
    # We match the specific event_type OR the catch-all 'all'
    subscriptions = WebhookSubscription.query.filter_by(user_id=user_id, is_active=True).filter(
        (WebhookSubscription.event_type == event_type) | (WebhookSubscription.event_type == 'all')
    ).all()

    if not subscriptions:
        return {"status": "success", "message": "No active webhooks to trigger"}

    results = []
    
    # Send the HTTP POST requests
    for sub in subscriptions:
        try:
            response = requests.post(
                sub.target_url,
                json={
                    "event": event_type,
                    "order_id": str(order_id),
                    "data": payload
                },
                timeout=5 # 5-second timeout so a bad server doesn't hang our Lambda
            )
            
            results.append({
                "url": sub.target_url,
                "status_code": response.status_code,
                "success": response.ok
            })
            logger.info(f"Webhook sent to {sub.target_url} - Status: {response.status_code}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook to {sub.target_url}: {str(e)}")
            results.append({
                "url": sub.target_url,
                "error": str(e),
                "success": False
            })

    return {
        "status": "success",
        "processed": len(subscriptions),
        "results": results
    }