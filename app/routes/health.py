from flask import Blueprint, jsonify
from app.extensions import db
from sqlalchemy import text

health_bp = Blueprint('health', __name__)

@health_bp.route('', methods=['GET'])
def health_check():
    status = {"status": "healthy", "postgres": "unknown", "dynamodb": "unknown"}
    
    # Check PostgreSQL
    try:
        db.session.execute(text('SELECT 1'))
        status["postgres"] = "connected"
    except Exception:
        status["postgres"] = "disconnected"
        status["status"] = "unhealthy"

    # Check DynamoDB (Deferred import to avoid path issues on startup)
    try:
        try:
            # If your folder is in the root directory
            from lambdas.shared.dynamo_utils import get_dynamodb_resource
        except ModuleNotFoundError:
            # If your folder is inside the lambdas/ directory
            from lambdas.shared.dynamo_utils import get_dynamodb_resource
            
        dynamodb = get_dynamodb_resource()
        dynamodb.meta.client.list_tables(Limit=1)
        status["dynamodb"] = "connected"
    except Exception as e:
        print(f"DynamoDB Health Check Error: {e}")
        status["dynamodb"] = "disconnected"
        status["status"] = "unhealthy"

    return jsonify(status), 200 if status["status"] == "healthy" else 503