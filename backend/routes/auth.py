"""
Authentication routes for user registration, login, and logout.
"""
from flask import Blueprint, request, jsonify
from services.auth_service import AuthService, RateLimitError
from functools import wraps


auth_bp = Blueprint('auth', __name__)


def require_auth(f):
    """
    Decorator to require authentication for API endpoints.
    
    Checks for session token in Authorization header.
    Returns 401 if token is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }), 401
        
        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'error': {
                    'code': 'INVALID_TOKEN_FORMAT',
                    'message': 'Invalid authorization header format. Expected: Bearer <token>'
                }
            }), 401
        
        token = parts[1]
        
        # Validate token
        session_data = AuthService.validate_session_token(token)
        if not session_data:
            return jsonify({
                'error': {
                    'code': 'SESSION_EXPIRED',
                    'message': 'Session has expired. Please login again.'
                }
            }), 401
        
        # Add user info to request context
        request.user_id = session_data['user_id']
        request.username = session_data['username']
        
        return f(*args, **kwargs)
    
    return decorated_function


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    Request Body:
        {
            "username": "string (3-30 chars)",
            "email": "string (valid email)",
            "password": "string (min 8 chars)"
        }
    
    Response:
        200: {
            "user_id": int,
            "username": string,
            "email": string,
            "message": string
        }
        400: {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": string,
                "details": {}
            }
        }
    """
    try:
        # Get request data
        try:
            data = request.get_json()
        except Exception:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body must be valid JSON'
                }
            }), 400
        
        if not data:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body must be JSON'
                }
            }), 400
        
        # Extract fields
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Check for missing fields
        missing_fields = []
        if not username:
            missing_fields.append('username')
        if not email:
            missing_fields.append('email')
        if not password:
            missing_fields.append('password')
        
        if missing_fields:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'details': {'missing_fields': missing_fields}
                }
            }), 400
        
        # Register user
        user, error = AuthService.register_user(username, email, password)
        
        if error:
            return jsonify({
                'error': {
                    'code': 'REGISTRATION_FAILED',
                    'message': error
                }
            }), 400
        
        return jsonify({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'message': 'User registered successfully'
        }), 201
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred during registration'
            }
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and create session.
    
    Request Body:
        {
            "username": "string (username or email)",
            "password": "string"
        }
    
    Response:
        200: {
            "session_token": string,
            "user_id": int,
            "username": string,
            "expires_at": string (ISO 8601),
            "message": string
        }
        400: {
            "error": {
                "code": "MISSING_FIELDS",
                "message": string
            }
        }
        401: {
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": string
            }
        }
        429: {
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": string
            }
        }
    """
    try:
        # Get request data
        try:
            data = request.get_json()
        except Exception:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body must be valid JSON'
                }
            }), 400
        
        if not data:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body must be JSON'
                }
            }), 400
        
        # Extract fields
        username = data.get('username')
        password = data.get('password')
        
        # Check for missing fields
        missing_fields = []
        if not username:
            missing_fields.append('username')
        if not password:
            missing_fields.append('password')
        
        if missing_fields:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'details': {'missing_fields': missing_fields}
                }
            }), 400
        
        # Attempt login
        token, user, error = AuthService.login(username, password)
        
        if error:
            # Check if it's a rate limit error
            if "Too many failed login attempts" in error:
                return jsonify({
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': error
                    }
                }), 429
            else:
                return jsonify({
                    'error': {
                        'code': 'INVALID_CREDENTIALS',
                        'message': error
                    }
                }), 401
        
        # Get session data for expiration time
        session_data = AuthService._session_tokens[token]
        
        return jsonify({
            'session_token': token,
            'user_id': user.user_id,
            'username': user.username,
            'expires_at': session_data['expires_at'].isoformat(),
            'message': 'Login successful'
        }), 200
        
    except Exception as e:
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred during login'
            }
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Invalidate user session.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Response:
        200: {
            "message": string
        }
        401: {
            "error": {
                "code": "UNAUTHORIZED",
                "message": string
            }
        }
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        token = auth_header.split()[1]
        
        # Logout
        success = AuthService.logout(token)
        
        if success:
            return jsonify({
                'message': 'Logout successful'
            }), 200
        else:
            return jsonify({
                'error': {
                    'code': 'LOGOUT_FAILED',
                    'message': 'Session not found'
                }
            }), 400
        
    except Exception as e:
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred during logout'
            }
        }), 500


@auth_bp.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint (no authentication required).
    
    Response:
        200: {
            "status": "ok"
        }
    """
    return jsonify({'status': 'ok'}), 200
