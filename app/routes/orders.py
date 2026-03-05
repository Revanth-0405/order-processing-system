from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.services.order_service import OrderService
from app.schemas.order import order_input_schema, order_output_schema
from app.utils.decorators import jwt_required


orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

@orders_bp.route('', methods=['POST'])
@jwt_required
def place_order():
    json_data = request.get_json()
    
    # 1. Validate incoming JSON payload
    try:
        data = order_input_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
        
    # 2. Extract user ID (mocked via decorator for now)
    user_id = request.user['id'] 
    
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
    user_id = request.user['id']
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

@orders_bp.route('/<uuid:order_id>', methods=['GET'])
@jwt_required
def get_order(order_id):
    user_id = request.user['id']
    order = OrderService.get_order_by_id(order_id, user_id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
        
    return jsonify(order_output_schema.dump(order)), 200

@orders_bp.route('/<uuid:order_id>/cancel', methods=['PUT'])
@jwt_required
def cancel_order(order_id):
    user_id = request.user['id']
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