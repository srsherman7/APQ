"""
Drill mode routes for focused practice on weak areas.
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from services.analytics_engine import AnalyticsEngine
from services.session_manager import SessionManager
from services.auth_service import AuthService
from models.session import Session
from extensions import db


drill_bp = Blueprint('drill', __name__)


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


@drill_bp.route('/activate', methods=['POST'])
@require_auth
def activate_drill_mode():
    """
    Activate drill mode for weak area practice.
    
    Drill mode filters questions to topics where the user has <70% performance
    and at least 5 attempts. Uses AnalyticsEngine to identify weak areas.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Response:
        200: {
            "session": {
                "session_id": string,
                "user_id": int,
                "is_drill_mode": boolean,
                "drill_mode_topics": array,
                "current_difficulty_level": int,
                ...
            },
            "message": string,
            "weak_areas": array
        }
        404: {
            "error": {
                "code": "NO_WEAK_AREAS",
                "message": string
            }
        }
        401: {
            "error": {
                "code": "AUTHENTICATION_REQUIRED",
                "message": string
            }
        }
        500: {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": string
            }
        }
    
    Requirements: 9.8, 6.1, 6.2, 6.3, 6.4
    """
    try:
        # Get user ID from authenticated request
        user_id = request.user_id
        
        # Use AnalyticsEngine to identify weak areas
        analytics = AnalyticsEngine()
        weak_areas = analytics.identify_weak_areas(user_id)
        
        # Check if user has any weak areas
        if not weak_areas:
            return jsonify({
                'error': {
                    'code': 'NO_WEAK_AREAS',
                    'message': 'No weak areas found. All areas are proficient (≥70% or <5 attempts).'
                }
            }), 404
        
        # Extract topic names from weak areas
        weak_topics = [area['topic'] for area in weak_areas]
        
        # Get or create active session for user
        session = Session.query.filter_by(
            user_id=user_id,
            is_active=True
        ).first()
        
        if not session:
            # Create new session if none exists
            session = SessionManager.create_session(user_id)
            if not session:
                return jsonify({
                    'error': {
                        'code': 'SESSION_CREATION_FAILED',
                        'message': 'Failed to create session'
                    }
                }), 500
        
        # Activate drill mode on the session
        session.is_drill_mode = True
        session.drill_mode_topics = weak_topics
        db.session.commit()
        
        return jsonify({
            'session': session.to_dict(),
            'message': f'Drill mode activated for {len(weak_topics)} weak area(s)',
            'weak_areas': weak_areas
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
                'message': 'An error occurred while activating drill mode'
            }
        }), 500


@drill_bp.route('/deactivate', methods=['POST'])
@require_auth
def deactivate_drill_mode():
    """
    Deactivate drill mode and return to normal practice.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Response:
        200: {
            "session": {
                "session_id": string,
                "user_id": int,
                "is_drill_mode": boolean,
                "drill_mode_topics": array,
                ...
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
                "code": "AUTHENTICATION_REQUIRED",
                "message": string
            }
        }
        500: {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": string
            }
        }
    
    Requirements: 9.9, 6.9
    """
    try:
        # Get user ID from authenticated request
        user_id = request.user_id
        
        # Get active session for user
        session = Session.query.filter_by(
            user_id=user_id,
            is_active=True
        ).first()
        
        if not session:
            return jsonify({
                'error': {
                    'code': 'SESSION_NOT_FOUND',
                    'message': 'No active session found for user'
                }
            }), 404
        
        # Deactivate drill mode
        session.is_drill_mode = False
        session.drill_mode_topics = []
        db.session.commit()
        
        return jsonify({
            'session': session.to_dict(),
            'message': 'Drill mode deactivated. Returned to normal practice mode.'
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
                'message': 'An error occurred while deactivating drill mode'
            }
        }), 500
