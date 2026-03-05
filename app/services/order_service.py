import datetime
import random
import string
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.product import Product

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
            return new_order
            
        except Exception as e:
            db.session.rollback() # Roll back everything if any step fails
            raise e