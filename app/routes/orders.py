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