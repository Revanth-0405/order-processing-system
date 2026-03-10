import logging
from app.extensions import db
from app.models.order import Order
from app.models.product import Product
from app.services.dynamodb_service import DynamoDBService

logger = logging.getLogger(__name__)

def handler(event, context):
    """
    AWS Lambda Handler for updating inventory.
    Input Event: {"order_id": "uuid", "action": "reduce_stock" | "restore_stock"}
    """
    logger.info(f"Lambda update_inventory invoked with event: {event}")
    
    order_id = event.get('order_id')
    action = event.get('action')
    
    if not order_id or action not in ['reduce_stock', 'restore_stock']:
        return {"status": "error", "message": "Invalid event payload"}

    order = Order.query.get(order_id)
    if not order:
        return {"status": "error", "message": "Order not found"}

    inventory_changes = []

    try:
        for item in order.items:
            # ROW-LEVEL LOCKING: .with_for_update() prevents other transactions 
            # from modifying this product row until this transaction commits.
            product = Product.query.with_for_update().get(item.product_id)
            
            if not product:
                continue

            before_stock = product.stock_quantity

            if action == 'reduce_stock':
                product.stock_quantity -= item.quantity
            elif action == 'restore_stock':
                product.stock_quantity += item.quantity

            after_stock = product.stock_quantity

            inventory_changes.append({
                "product_id": str(product.id),
                "sku": product.sku,
                "quantity_changed": item.quantity,
                "before": before_stock,
                "after": after_stock
            })

        # Commit the transaction to release the row locks
        db.session.commit()

        # Log the inventory update to DynamoDB
        DynamoDBService.put_event(
            order_id=order_id,
            event_type="inventory_updated",
            payload={"action": action, "changes": inventory_changes},
            processed_by="update_inventory_lambda"
        )

        return {
            "status": "success",
            "message": f"Inventory {action} completed successfully"
        }

    except Exception as e:
        db.session.rollback() # Release locks if something fails
        logger.error(f"Error updating inventory: {str(e)}")
        
        DynamoDBService.put_event(
            order_id=order_id,
            event_type="inventory_update_failed",
            payload={"action": action, "error": str(e)},
            processed_by="update_inventory_lambda"
        )
        return {"status": "error", "message": str(e)}