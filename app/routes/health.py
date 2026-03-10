from flask import Blueprint, jsonify
from app.extensions import db
from shared.dynamo_utils import get_dynamodb_resource
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

    # Check DynamoDB
    try:
        dynamodb = get_dynamodb_resource()
        dynamodb.meta.client.list_tables(Limit=1)
        status["dynamodb"] = "connected"
    except Exception:
        status["dynamodb"] = "disconnected"
        status["status"] = "unhealthy"

    return jsonify(status), 200 if status["status"] == "healthy" else 503