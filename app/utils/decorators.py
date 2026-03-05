from functools import wraps
from flask import request, jsonify

def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Placeholder: Implement your Level 1 JWT extraction here later
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        # Mocking user context for now
        request.user = {'id': 'mock-uuid', 'is_admin': False}
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Placeholder: Verify admin status based on the JWT token
        # For testing Phase 1 quickly, we'll bypass the strict check
        # In production, check if request.user['is_admin'] is True
        token = request.headers.get('Authorization')
        if token != "Bearer admin-token": # Simple mock check for testing
            return jsonify({'message': 'Admin privileges required!'}), 403
            
        return f(*args, **kwargs)
    return decorated_function