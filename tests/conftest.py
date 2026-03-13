import os
import pytest
from app.extensions import db
from app.config import config_by_name

# 1. Create a dedicated Testing Configuration class
class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-secret-key"
    LAMBDA_MODE = "local"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# 2. Inject this testing config into your app's configuration dictionary!
config_by_name['testing'] = TestingConfig

# 3. Import create_app AFTER we've injected the config
from app import create_app

@pytest.fixture
def app():
    # Now create_app('testing') will work perfectly and natively!
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()