from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.services.product_service import ProductService
from app.schemas.product import product_schema, products_schema
from app.utils.decorators import admin_required

products_bp = Blueprint('products', __name__, url_prefix='/api/products')

@products_bp.route('', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')

    pagination = ProductService.get_all_products(page, per_page, search)
    
    return jsonify({
        'items': products_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }), 200

@products_bp.route('/<uuid:product_id>', methods=['GET'])
def get_product(product_id):
    product = ProductService.get_product_by_id(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    return jsonify(product_schema.dump(product)), 200

@products_bp.route('', methods=['POST'])
@admin_required
def create_product():
    json_data = request.get_json()
    try:
        data = product_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
        
    try:
        new_product = ProductService.create_product(data)
        return jsonify(product_schema.dump(new_product)), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@products_bp.route('/<uuid:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    product = ProductService.get_product_by_id(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
        
    json_data = request.get_json()
    try:
        # Partial validation for updates
        data = product_schema.load(json_data, partial=True) 
    except ValidationError as err:
        return jsonify(err.messages), 400
        
    updated_product = ProductService.update_product(product, data)
    return jsonify(product_schema.dump(updated_product)), 200

@products_bp.route('/<uuid:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    product = ProductService.get_product_by_id(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
        
    ProductService.soft_delete_product(product)
    return jsonify({'message': 'Product deleted successfully'}), 200