"""
Authentication middleware for protecting API endpoints.
"""
from functools import wraps
from flask import jsonify
from flask_login import current_user


def require_auth(f):
    """
    Decorator to require authentication for an endpoint.
    
    Returns 401 if user is not authenticated.
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            return {'data': 'secret'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication is required to access this resource',
                    'details': {}
                }
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def optional_auth(f):
    """
    Decorator for endpoints that work with or without authentication.
    
    Sets current_user but doesn't require authentication.
    
    Usage:
        @app.route('/public-or-private')
        @optional_auth
        def flexible_route():
            if current_user.is_authenticated:
                return {'data': 'personalized'}
            return {'data': 'public'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # current_user is automatically available via Flask-Login
        return f(*args, **kwargs)
    return decorated_function
