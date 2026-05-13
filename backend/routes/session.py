"""
Session management routes for saving and restoring user sessions.
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from services.session_manager import SessionManager
from services.auth_service import AuthService


session_bp = Blueprint('session', __name__)


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


@session_bp.route('/restore', methods=['GET'])
@require_auth
def restore_session():
    """
    Restore user's most recent active session.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Response:
        200: {
            "session": {
                "session_id": string,
                "user_id": int,
                "answered_question_ids": array,
                "current_difficulty_level": int,
                "current_performance_score": float,
                "current_question_id": int or null,
                "is_drill_mode": boolean,
                "drill_mode_topics": array,
                "created_at": string (ISO 8601),
                "updated_at": string (ISO 8601),
                "is_active": boolean
            },
            "message": string
        }
        404: {
            "error": {
                "code": "SESSION_NOT_FOUND",
                "message": string
            }
        }
        401: {
            "error": {
                "code": "UNAUTHORIZED" | "INVALID_TOKEN_FORMAT" | "SESSION_EXPIRED",
                "message": string
            }
        }
        500: {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": string
            }
        }
    """
    try:
        # Get user ID from authenticated request
        user_id = request.user_id
        
        # Restore session using SessionManager
        session = SessionManager.restore_session(user_id)
        
        if not session:
            return jsonify({
                'error': {
                    'code': 'SESSION_NOT_FOUND',
                    'message': 'No active session found for user'
                }
            }), 404
        
        return jsonify({
            'session': session.to_dict(),
            'message': 'Session restored successfully'
        }), 200
        
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
                'message': 'An error occurred while restoring session'
            }
        }), 500


@session_bp.route('/new', methods=['POST'])
@require_auth
def new_session():
    """
    Start a new practice session for the authenticated user.
    
    Deactivates any existing active sessions and creates a new one.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Response:
        201: {
            "session": {
                "session_id": string,
                "user_id": int,
                "answered_question_ids": array,
                "current_difficulty_level": int,
                "current_performance_score": float,
                "current_question_id": int or null,
                "is_drill_mode": boolean,
                "drill_mode_topics": array,
                "created_at": string (ISO 8601),
                "updated_at": string (ISO 8601),
                "is_active": boolean
            },
            "message": string
        }
        400: {
            "error": {
                "code": "USER_NOT_FOUND",
                "message": string
            }
        }
        401: {
            "error": {
                "code": "UNAUTHORIZED" | "INVALID_TOKEN_FORMAT" | "SESSION_EXPIRED",
                "message": string
            }
        }
        500: {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": string
            }
        }
    """
    try:
        # Get user ID from authenticated request
        user_id = request.user_id
        
        # Create new session using SessionManager
        session = SessionManager.create_session(user_id)
        
        if not session:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 400
        
        return jsonify({
            'session': session.to_dict(),
            'message': 'New session created successfully'
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
                'message': 'An error occurred while creating session'
            }
        }), 500


@session_bp.route('/save', methods=['POST'])
@require_auth
def save_session():
    """
    Save current session state to database.
    
    Includes retry logic (3 attempts) for reliability.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Request Body:
        {
            "session_id": "string (UUID)",
            "state": {
                "answered_question_ids": array (optional),
                "current_difficulty_level": int (optional),
                "current_performance_score": float (optional),
                "current_question_id": int or null (optional),
                "is_drill_mode": boolean (optional),
                "drill_mode_topics": array (optional)
            }
        }
    
    Response:
        200: {
            "success": true,
            "message": string
        }
        400: {
            "error": {
                "code": "MISSING_FIELDS" | "INVALID_REQUEST" | "VALIDATION_ERROR",
                "message": string
            }
        }
        401: {
            "error": {
                "code": "UNAUTHORIZED" | "INVALID_TOKEN_FORMAT" | "SESSION_EXPIRED",
                "message": string
            }
        }
        500: {
            "error": {
                "code": "SAVE_FAILED" | "INTERNAL_ERROR",
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
        session_id = data.get('session_id')
        state = data.get('state')
        
        # Check for missing fields
        missing_fields = []
        if not session_id:
            missing_fields.append('session_id')
        if not state:
            missing_fields.append('state')
        
        if missing_fields:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'details': {'missing_fields': missing_fields}
                }
            }), 400
        
        # Save session state using SessionManager
        success = SessionManager.save_session_state(session_id, state)
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'SAVE_FAILED',
                    'message': 'Failed to save session state after 3 attempts'
                }
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Session state saved successfully'
        }), 200
        
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
                'message': 'An error occurred while saving session'
            }
        }), 500
