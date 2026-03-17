from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.product import Product
from app.utils.decorators import jwt_required, current_user_is_admin

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    query = Product.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
        
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Safely serialize the products to avoid missing schema imports
    items = [{
        "id": str(p.id), 
        "name": p.name, 
        "sku": p.sku, 
        "price": float(p.price), 
        "stock_quantity": p.stock_quantity
    } for p in paginated.items]
    
    return jsonify({
        "items": items, 
        "total": paginated.total, 
        "pages": paginated.pages,
        "current_page": paginated.page
    }), 200

@products_bp.route('/<uuid:id>', methods=['GET'])
def get_product(id):
    product = db.session.get(Product, id)
    if not product or not product.is_active:
        return jsonify({"error": "Product not found"}), 404
        
    return jsonify({
        "id": str(product.id), 
        "name": product.name, 
        "sku": product.sku, 
        "price": float(product.price), 
        "stock_quantity": product.stock_quantity
    }), 200

@products_bp.route('', methods=['POST'])
@jwt_required
def create_product():
    if not current_user_is_admin():
        return jsonify({"error": "Admin privileges required"}), 403
        
    data = request.get_json()
    
    # Basic validation
    if not data or not data.get('name') or not data.get('sku') or not data.get('price'):
        return jsonify({"error": "Missing required fields (name, sku, price)"}), 400
        
    product = Product(
        name=data['name'], 
        sku=data['sku'], 
        price=data['price'], 
        stock_quantity=data.get('stock_quantity', 0)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({"message": "Product created", "id": str(product.id)}), 201

@products_bp.route('/<uuid:id>', methods=['PUT'])
@jwt_required
def update_product(id):
    if not current_user_is_admin():
        return jsonify({"error": "Admin privileges required"}), 403
        
    product = db.session.get(Product, id)
    if not product or not product.is_active:
        return jsonify({"error": "Product not found"}), 404
    
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.sku = data.get('sku', product.sku)
    product.price = data.get('price', product.price)
    product.stock_quantity = data.get('stock_quantity', product.stock_quantity)
    
    db.session.commit()
    return jsonify({"message": "Product updated"}), 200

@products_bp.route('/<uuid:id>', methods=['DELETE'])
@jwt_required
def delete_product(id):
    if not current_user_is_admin():
        return jsonify({"error": "Admin privileges required"}), 403
        
    product = db.session.get(Product, id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    # Spec requirement: Soft delete
    product.is_active = False 
    db.session.commit()
    
    return jsonify({"message": "Product deleted successfully"}), 200