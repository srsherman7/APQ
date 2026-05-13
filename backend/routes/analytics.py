"""
Analytics routes for performance tracking and user profiles.
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from services.analytics_engine import AnalyticsEngine
from services.auth_service import AuthService


analytics_bp = Blueprint('analytics', __name__)


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


@analytics_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """
    Get user performance profile and analytics.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Response:
        200: {
            "overall_performance_score": float,
            "total_questions_answered": int,
            "topic_scores": dict,
            "weak_areas": array,
            "session_history": array,
            "last_updated": string (ISO 8601)
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
    
    Requirements: 9.4, 5.1-5.10
    """
    try:
        # Get user ID from authenticated request
        user_id = request.user_id
        
        # Get analytics using AnalyticsEngine
        analytics_engine = AnalyticsEngine()
        analytics_data = analytics_engine.get_user_analytics(user_id)
        
        return jsonify(analytics_data), 200
        
    except Exception as e:
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred while retrieving analytics'
            }
        }), 500


@analytics_bp.route('/history', methods=['GET'])
@require_auth
def get_history():
    """
    Get session history for the user.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Query Parameters:
        limit: Maximum number of sessions to retrieve (default 20)
    
    Response:
        200: {
            "sessions": [
                {
                    "session_id": string,
                    "date": string (ISO 8601),
                    "score": float,
                    "questions_answered": int,
                    "is_drill_mode": boolean,
                    "is_active": boolean
                }
            ]
        }
        400: {
            "error": {
                "code": "INVALID_LIMIT",
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
    
    Requirements: 9.4, 5.8
    """
    try:
        # Get user ID from authenticated request
        user_id = request.user_id
        
        # Get limit parameter (default 20)
        limit = request.args.get('limit', 20, type=int)
        
        # Validate limit
        if limit < 1 or limit > 100:
            return jsonify({
                'error': {
                    'code': 'INVALID_LIMIT',
                    'message': 'Limit must be between 1 and 100'
                }
            }), 400
        
        # Get session history using AnalyticsEngine
        analytics_engine = AnalyticsEngine()
        history = analytics_engine.get_session_history(user_id, limit)
        
        return jsonify({
            'sessions': history
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
                'message': 'An error occurred while retrieving session history'
            }
        }), 500
