from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import get_jwt_identity
from app.extensions import db
from app.models.order import Order
from app.services.order_service import OrderService
from app.schemas.order import order_schema, orders_schema
from app.utils.decorators import jwt_required, current_user_is_admin
from app.services.dynamodb_service import DynamoDBService

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['POST'])
@jwt_required
def create_order():
    user_id = get_jwt_identity()
    data = request.get_json()
    idem_key = request.headers.get('Idempotency-Key') # Get from header
    
    try:
        # CRITICAL FIX: Actually pass the idempotency key to the service!
        new_order = OrderService.create_order(user_id, data, idempotency_key=idem_key)
        return jsonify({"message": "Order placed", "order_id": new_order.id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('', methods=['GET'])
@jwt_required
def get_orders():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': orders_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200

@products_bp.route('/<uuid:id>', methods=['GET'])
@jwt_required
def get_order(id):
    order = db.session.get(Order, id)
    if not order:
        return jsonify({"message": "Order not found"}), 404
        
    # PHASE 1 FIX: Allow admin to view any order
    if str(order.user_id) != str(get_jwt_identity()) and not current_user_is_admin():
        return jsonify({"error": "Unauthorized"}), 403
        
    return jsonify(order_schema.dump(order)), 200

@products_bp.route('/<uuid:id>/cancel', methods=['PUT'])
@jwt_required
def cancel_order(id):
    order = db.session.get(Order, id)
    if not order:
        return jsonify({"message": "Order not found"}), 404
        
    if str(order.user_id) != str(get_jwt_identity()) and not current_user_is_admin():
        return jsonify({"error": "Unauthorized"}), 403

    if order.status in ['cancelled', 'shipped', 'delivered']:
        return jsonify({"error": f"Cannot cancel order in {order.status} status"}), 400

    order.status = 'cancelled'
    db.session.commit()
    
    # PHASE 1 FIX: Log cancellation to DynamoDB
    try:
        DynamoDBService.put_event(order.id, 'order_cancelled', {"reason": "User requested"})
    except Exception as e:
        print(f"Failed to log cancel event: {e}")

    return jsonify({"message": "Order cancelled successfully"}), 200