from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate

def create_app(config_name='dev'):
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # We will register our blueprints (routes) here later
    
    # A simple health check route to verify the app is running
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Flask API is running'}, 200

    return app