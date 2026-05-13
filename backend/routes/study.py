"""
Study materials routes for study guides and cheatsheets.
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from services.study_guide_generator import StudyGuideGenerator, TimeoutError
from services.auth_service import AuthService


study_bp = Blueprint('study', __name__)


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


@study_bp.route('/guide/<topic>', methods=['GET'])
@require_auth
def get_study_guide(topic):
    """
    Generate study guide for specified topic area.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Path Parameters:
        topic: Topic area (Cloud Concepts, Security and Compliance, Technology, Billing and Pricing)
    
    Response:
        200: {
            "study_guide": {
                "topic_area": string,
                "sections": {
                    "service_definitions": {
                        "heading": string,
                        "content": array
                    },
                    "use_cases": {
                        "heading": string,
                        "content": array
                    },
                    "exam_scenarios": {
                        "heading": string,
                        "content": array
                    },
                    "comparison_table": {
                        "heading": string,
                        "content": array
                    }
                }
            }
        }
        400: {
            "error": {
                "code": "INVALID_TOPIC",
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
                "code": "GENERATION_TIMEOUT" | "INTERNAL_ERROR",
                "message": string
            }
        }
    """
    try:
        # Initialize generator
        generator = StudyGuideGenerator()
        
        # Generate study guide (30-second timeout enforced by service)
        study_guide = generator.generate_study_guide(topic)
        
        # Format the content
        formatted_content = generator.format_study_content(study_guide)
        
        return jsonify({
            'study_guide': formatted_content
        }), 200
        
    except ValueError as e:
        # Invalid topic area
        return jsonify({
            'error': {
                'code': 'INVALID_TOPIC',
                'message': str(e)
            }
        }), 400
    except TimeoutError as e:
        # Generation exceeded 30 seconds
        return jsonify({
            'error': {
                'code': 'GENERATION_TIMEOUT',
                'message': str(e)
            }
        }), 500
    except Exception as e:
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred while generating study guide'
            }
        }), 500


@study_bp.route('/cheatsheets', methods=['GET'])
@require_auth
def get_cheatsheets():
    """
    List available pre-generated cheatsheets.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Response:
        200: {
            "cheatsheets": [
                {
                    "id": string,
                    "title": string,
                    "topic_area": string,
                    "description": string
                }
            ]
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
        # Initialize generator
        generator = StudyGuideGenerator()
        
        # Get pre-generated cheatsheets
        cheatsheets = generator.get_pregenerated_cheatsheets()
        
        # Convert to dict format
        cheatsheets_data = [
            {
                'id': cs.id,
                'title': cs.title,
                'topic_area': cs.topic_area,
                'description': cs.description
            }
            for cs in cheatsheets
        ]
        
        return jsonify({
            'cheatsheets': cheatsheets_data
        }), 200
        
    except Exception as e:
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred while retrieving cheatsheets'
            }
        }), 500
