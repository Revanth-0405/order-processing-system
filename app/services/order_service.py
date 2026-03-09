import datetime
import random
import string
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.lambda_invoker import LambdaInvoker

class OrderService:
    @staticmethod
    def generate_order_number():
        """Generates order number in format: ORD-YYYYMMDD-XXXX"""
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"ORD-{date_str}-{random_str}"

    @staticmethod
    def create_order(user_id, data):
        # The database transaction begins implicitly
        try:
            total_amount = 0
            
            # 1. Create the base Order record
            new_order = Order(
                order_number=OrderService.generate_order_number(),
                user_id=user_id,
                shipping_address=data['shipping_address'],
                notes=data.get('notes')
            )
            db.session.add(new_order)
            db.session.flush() # Flush to get the new_order.id without committing yet

            # 2. Process Order Items and Validate Stock
            for item_data in data['items']:
                product = Product.query.get(item_data['product_id'])
                
                # Validation checks
                if not product or not product.is_active:
                    raise ValueError(f"Product {item_data['product_id']} not found or inactive")
                if product.stock_quantity < item_data['quantity']:
                    raise ValueError(f"Insufficient stock for product: {product.name}")

                # Math
                unit_price = product.price
                subtotal = unit_price * item_data['quantity']
                total_amount += subtotal

                # Create Item record
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=item_data['quantity'],
                    unit_price=unit_price,
                    subtotal=subtotal
                )
                db.session.add(order_item)

            # 3. Finalize Order
            new_order.total_amount = total_amount
            db.session.commit() # Atomic commit for Order + OrderItems
            
            try:
                # 1. Invoke process_order Lambda
                process_payload = {
                    "order_id": str(new_order.id),
                    "action": "order_created",
                    "user_id": str(user_id)
                }
                process_result = LambdaInvoker.invoke('process_order', process_payload)

                # 2. If processing succeeds, chain the inventory update
                if process_result and process_result.get('status') == 'success':
                    inventory_payload = {
                        "order_id": str(new_order.id),
                        "action": "reduce_stock"
                    }
                    LambdaInvoker.invoke('update_inventory', inventory_payload)
                    
                    # Note: We will add the send_webhook invocation here in Phase 3
            except Exception as e:
                # In a real system, we'd use a Dead Letter Queue (DLQ) for failed invocations
                print(f"Failed to invoke async lambdas: {e}")

            return new_order
            
        except Exception as e:
            db.session.rollback() # Roll back everything if any step fails
            raise e
    
    @staticmethod
    def get_user_orders(user_id, page=1, per_page=10, status=None):
        query = Order.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
            
        return query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_order_by_id(order_id, user_id):
        # Ensures a user can only fetch their own orders
        return Order.query.filter_by(id=order_id, user_id=user_id).first()

    @staticmethod
    def cancel_order(order):
        # Rule: cancel only if status is pending or confirmed
        if order.status not in ['pending', 'confirmed']:
            raise ValueError(f"Cannot cancel order with status: {order.status}")
            
        order.status = 'cancelled'
        # we will trigger the update_inventory Lambda here to restore stock
        db.session.commit()
        
        try:
            inventory_payload = {
                "order_id": str(order.id),
                "action": "restore_stock"
            }
            LambdaInvoker.invoke('update_inventory', inventory_payload)
        except Exception as e:
            print(f"Failed to invoke update_inventory lambda: {e}")

        return order