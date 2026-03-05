from app.extensions import db
from app.models.product import Product

class ProductService:
    @staticmethod
    def get_all_products(page=1, per_page=10, search=None):
        query = Product.query.filter_by(is_active=True)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
            
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_product_by_id(product_id):
        return Product.query.filter_by(id=product_id, is_active=True).first()

    @staticmethod
    def create_product(data):
        new_product = Product(
            name=data['name'],
            description=data.get('description'),
            sku=data['sku'],
            price=data['price'],
            stock_quantity=data.get('stock_quantity', 0)
        )
        db.session.add(new_product)
        db.session.commit()
        return new_product

    @staticmethod
    def update_product(product, data):
        if 'name' in data: product.name = data['name']
        if 'description' in data: product.description = data['description']
        if 'sku' in data: product.sku = data['sku']
        if 'price' in data: product.price = data['price']
        if 'stock_quantity' in data: product.stock_quantity = data['stock_quantity']
        
        db.session.commit()
        return product

    @staticmethod
    def soft_delete_product(product):
        product.is_active = False
        db.session.commit()
        return product