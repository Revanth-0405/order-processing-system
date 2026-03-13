import random
import logging
from app.extensions import db
from app.models.order import Order
from app.services.dynamodb_service import DynamoDBService

logger = logging.getLogger(__name__)

def handler(event, context):

    if event.get('action') == 'ping':
        return {"status": "ok", "message": "pong"}
    
    """
    AWS Lambda Handler for processing orders.
    Input Event: {"order_id": "uuid", "action": "order_created", "user_id": "uuid"}
    """
    logger.info(f"Lambda process_order invoked with event: {event}")
    
    order_id = event.get('order_id')
    user_id = event.get('user_id')
    
    if not order_id:
        return {"status": "error", "message": "Missing order_id"}

    # 1. Log the initial 'order_created' event
    DynamoDBService.put_event(
        order_id=order_id,
        event_type="order_created",
        payload=event,
        processed_by="process_order_lambda"
    )

    # 2. Fetch the order from PostgreSQL
    order = Order.query.get(order_id)
    if not order:
        return {"status": "error", "message": "Order not found"}

    # 3. Simulate Payment Processing (80% chance of success)
    payment_successful = random.random() < 0.8
    
    if payment_successful:
        # Payment Success Flow
        DynamoDBService.put_event(
            order_id=order_id,
            event_type="payment_success",
            payload={"transaction_id": f"txn_{random.randint(1000, 9999)}"},
            processed_by="process_order_lambda"
        )
        
        order.status = 'confirmed'
        db.session.commit()
        
        DynamoDBService.put_event(
            order_id=order_id,
            event_type="order_confirmed",
            payload={"status": "confirmed"},
            processed_by="process_order_lambda"
        )
        
        # This return payload is what Flask will use to chain the next Lambdas
        return {
            "status": "success",
            "event_type": "order_confirmed",
            "order_id": order_id,
            "payload": {"order_number": order.order_number, "total_amount": str(order.total_amount)}
        }
        
    else:
        # Payment Failure Flow
        DynamoDBService.put_event(
            order_id=order_id,
            event_type="payment_failed",
            payload={"error": "Insufficient funds or card declined"},
            processed_by="process_order_lambda"
        )
        
        order.status = 'cancelled'
        db.session.commit()
        
        DynamoDBService.put_event(
            order_id=order_id,
            event_type="order_cancelled",
            payload={"reason": "payment_failed"},
            processed_by="process_order_lambda"
        )
        
        return {
            "status": "failure",
            "event_type": "order_cancelled",
            "order_id": order_id,
            "payload": {"reason": "payment_failed"}
        }