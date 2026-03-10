import logging
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt
from app.utils.error_handlers import register_error_handlers

def create_app(config_name='dev'):
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config_by_name[config_name])

    #configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize extensions with the app
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Register error handlers
    register_error_handlers(app)

    #import models here
    from app.models.user import User
    from app.models.product import Product
    from app.models.order import Order, OrderItem

    # our blueprints
    from app.routes.products import products_bp
    from app.routes.orders import orders_bp
    from app.routes.auth import auth_bp
    from app.routes.health import health_bp

    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(health_bp, url_prefix='/api/health')

    return app