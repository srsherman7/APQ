"""
Module routes — list available learning modules.
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from services.auth_service import AuthService
from models.module import Module

modules_bp = Blueprint('modules', __name__)


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}}), 401
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': {'code': 'INVALID_TOKEN_FORMAT', 'message': 'Invalid authorization header format'}}), 401
        token = parts[1]
        session_data = AuthService.validate_session_token(token)
        if not session_data:
            return jsonify({'error': {'code': 'SESSION_EXPIRED', 'message': 'Session has expired'}}), 401
        request.user_id = session_data['user_id']
        request.username = session_data['username']
        return f(*args, **kwargs)
    return decorated_function


@modules_bp.route('/', methods=['GET'])
@require_auth
def list_modules():
    """
    List all active learning modules.

    Response 200: { modules: [...] }
    """
    try:
        modules = Module.query.filter_by(is_active=True).all()
        return jsonify({
            'modules': [m.to_dict() for m in modules]
        }), 200
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500


@modules_bp.route('/<slug>', methods=['GET'])
@require_auth
def get_module(slug):
    """
    Get details for a specific module by slug.

    Response 200: { module: {...} }
    """
    try:
        module = Module.query.filter_by(slug=slug, is_active=True).first()
        if not module:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': f'Module "{slug}" not found'}}), 404
        return jsonify({'module': module.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500
