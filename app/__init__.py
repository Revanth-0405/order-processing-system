import uuid
import logging
from flask import request, g
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt
from app.utils.error_handlers import register_error_handlers

# Import the JSON formatter for structured logging
from pythonjsonlogger import jsonlogger

def create_app(config_name='dev'):
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config_by_name[config_name])

    # PHASE 4 FIX: Configure application-wide JSON Logging
    logger = logging.getLogger()
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logHandler = logging.StreamHandler()
    # Format the logs as JSON containing the timestamp, level, and message
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)

    # Initialize extensions with the app
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Register error handlers
    register_error_handlers(app)

    from lambdas.shared.dynamo_utils import create_order_events_table
    create_order_events_table()
    
    # Initialize Webhook Deliveries Table
    from app.services.dynamodb_service import DynamoDBService
    DynamoDBService.create_webhook_deliveries_table()

    # import models here
    from app.models.user import User
    from app.models.product import Product
    from app.models.order import Order, OrderItem
    
    # REQUEST TRACING MIDDLEWARE 
    @app.before_request
    def before_request():
        # Generate a unique request ID for tracing
        g.request_id = str(uuid.uuid4())

    @app.after_request
    def after_request(response):
        # Attach the request ID to the response headers
        if hasattr(g, 'request_id'):
            response.headers['X-Request-Id'] = g.request_id
        return response

    # our blueprints
    from app.routes.products import products_bp
    from app.routes.orders import orders_bp
    from app.routes.auth import auth_bp
    from app.routes.health import health_bp
    from app.routes.events import events_bp
    from app.routes.webhooks import webhooks_bp, webhook_receiver_bp

    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    app.register_blueprint(orders_bp, url_prefix='/api/v1/orders')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(health_bp, url_prefix='/api/v1/health')
    app.register_blueprint(events_bp, url_prefix='/api/v1/events')
    app.register_blueprint(webhooks_bp, url_prefix='/api/v1/webhooks')
    app.register_blueprint(webhook_receiver_bp, url_prefix='/api/v1/webhook-receiver')

    return app