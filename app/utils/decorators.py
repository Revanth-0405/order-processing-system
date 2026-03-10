from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # verify_jwt_in_request() automatically checks the Authorization header
        # for a valid Bearer token. If missing or invalid, it returns a 401/422.
        verify_jwt_in_request()
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First, ensure they are logged in
        verify_jwt_in_request()
        
        # Second, grab the additional claims we attached during login
        claims = get_jwt()
        
        # Check if the 'is_admin' claim is True
        if not claims.get('is_admin', False):
            return jsonify({'message': 'Admin privileges required!'}), 403
            
        return f(*args, **kwargs)
    return decorated_function