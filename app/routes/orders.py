from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.models.order import Order
from app.services.order_service import OrderService
from app.schemas.order import order_input_schema, order_output_schema, orders_output_schema
from app.utils.decorators import jwt_required
from app.services.dynamodb_service import DynamoDBService
from app.utils.decorators import admin_required
from app.services.lambda_invoker import LambdaInvoker

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('', methods=['POST'])
@jwt_required
def place_order():
    json_data = request.get_json()
    
    # 1. Validate incoming JSON payload
    try:
        data = order_input_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
        
    # 2. Extract user ID from JWT
    user_id = get_jwt_identity()
    
    # 3. Process the order
    try:
        new_order = OrderService.create_order(user_id, data)
        return jsonify(order_output_schema.dump(new_order)), 201
    except ValueError as ve:
        # Catch our custom validation errors (like insufficient stock)
        return jsonify({'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'message': 'An error occurred while placing the order.'}), 500
    

@orders_bp.route('', methods=['GET'])
@jwt_required
def get_orders():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status') # Optional filter

    pagination = OrderService.get_user_orders(user_id, page, per_page, status)
    
    return jsonify({
        'items': orders_output_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200

@orders_bp.route('/<uuid:order_id>/events', methods=['GET'])
@jwt_required
def get_order_events(order_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    is_admin = claims.get('is_admin', False)

    order = OrderService.get_order_by_id(order_id, user_id)
    if not order and not is_admin:
        return jsonify({'message': 'Order not found or access denied'}), 404

    events = DynamoDBService.get_events_by_order(order_id)
    return jsonify({'items': events, 'total': len(events)}), 200

@orders_bp.route('/<uuid:order_id>/cancel', methods=['PUT'])
@jwt_required
def cancel_order(order_id):
    user_id = get_jwt_identity()
    order = OrderService.get_order_by_id(order_id, user_id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
        
    try:
        updated_order = OrderService.cancel_order(order)
        return jsonify(order_output_schema.dump(updated_order)), 200
    except ValueError as ve:
        return jsonify({'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'message': 'An error occurred while cancelling the order.'}), 500
    
@orders_bp.route('/<uuid:order_id>/events', methods=['GET'])
@jwt_required
def get_order_events(order_id):
    # Verify the user owns this order first (or is admin)
    user_id = request.user['id']
    order = OrderService.get_order_by_id(order_id, user_id)
    if not order and not request.user.get('is_admin'):
        return jsonify({'message': 'Order not found or access denied'}), 404

    events = DynamoDBService.get_events_by_order(order_id)
    return jsonify({'items': events, 'total': len(events)}), 200

@orders_bp.route('/<uuid:order_id>/process', methods=['POST'])
@admin_required
def manually_process_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    payload = {
        "order_id": str(order.id),
        "action": "manual_process_trigger",
        "user_id": str(order.user_id)
    }
    
    try:
        result = LambdaInvoker.invoke('process_order', payload)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'message': f"Failed to invoke lambda: {str(e)}"}), 500