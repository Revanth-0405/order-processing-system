from flask import Blueprint, jsonify
from app.extensions import db
from sqlalchemy import text
from app.services.lambda_invoker import LambdaInvoker

health_bp = Blueprint('health', __name__)

@health_bp.route('', methods=['GET'])
def health_check():
    status = {
        "status": "healthy", 
        "flask": "ok", 
        "postgres": "unknown", 
        "dynamodb": "unknown",
        "lambda_system": "unknown"
    }
    
    # 1. Check PostgreSQL
    try:
        db.session.execute(text('SELECT 1'))
        status["postgres"] = "connected"
    except Exception:
        status["postgres"] = "disconnected"
        status["status"] = "unhealthy"

    # 2. Check DynamoDB
    try:
        from lambdas.shared.dynamo_utils import get_dynamodb_resource
        dynamodb = get_dynamodb_resource()
        dynamodb.meta.client.list_tables(Limit=1)
        status["dynamodb"] = "connected"
    except Exception as e:
        print(f"DynamoDB Health Check Error: {e}")
        status["dynamodb"] = "disconnected"
        status["status"] = "unhealthy"

    # 3. Check Lambda Availability (No-Op Ping)
    try:
        ping_response = LambdaInvoker.invoke('process_order', {'action': 'ping'})
        if ping_response and ping_response.get('status') == 'ok':
            status["lambda_system"] = "connected"
        else:
            status["lambda_system"] = "unexpected_response"
            status["status"] = "unhealthy"
    except Exception as e:
        print(f"Lambda Health Check Error: {e}")
        status["lambda_system"] = "disconnected"
        status["status"] = "unhealthy"

    return jsonify(status), 200 if status["status"] == "healthy" else 503