"""
Admin routes for question management - batch import, filtering, and reseeding.
"""
import os
import subprocess
import sys
from flask import Blueprint, request, jsonify
from functools import wraps
from services.auth_service import AuthService
from services.question_parser import QuestionParser, ValidationError
from models.question import Question
from extensions import db

admin_bp = Blueprint('admin', __name__)


def require_auth(f):
    """
    Decorator to require authentication for API endpoints.

    Checks for session token in Authorization header.
    Returns 401 if token is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'error': {
                    'code': 'INVALID_TOKEN_FORMAT',
                    'message': 'Invalid authorization header format. Expected: Bearer <token>'
                }
            }), 401

        token = parts[1]

        session_data = AuthService.validate_session_token(token)
        if not session_data:
            return jsonify({
                'error': {
                    'code': 'SESSION_EXPIRED',
                    'message': 'Session has expired. Please login again.'
                }
            }), 401

        request.user_id = session_data['user_id']
        request.username = session_data['username']

        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route('/import', methods=['POST'])
@require_auth
def import_questions():
    """
    Batch import questions from a JSON array.

    Request Body:
        {
            "questions": [
                {
                    "question_text": string,
                    "options": array,
                    "correct_answer": string,
                    "explanation": string,
                    "memory_technique": string,
                    "topic_area": string,
                    "difficulty_level": int,
                    "incorrect_explanation": string (optional),
                    "it_context_mapping": string (optional),
                    "is_active": bool (optional, default true)
                },
                ...
            ]
        }

    Response:
        201: {
            "imported_count": int,
            "message": string
        }
        400: {
            "error": {
                "code": "MISSING_FIELDS" | "VALIDATION_ERROR" | "INVALID_REQUEST",
                "message": string,
                "details": object (optional)
            }
        }
        500: {
            "error": {
                "code": "IMPORT_FAILED" | "INTERNAL_ERROR",
                "message": string
            }
        }

    Requirements: 11.10, 13.1-13.14
    """
    try:
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

        questions_data = data.get('questions')

        if questions_data is None:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Missing required field: questions'
                }
            }), 400

        if not isinstance(questions_data, list):
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'questions must be an array'
                }
            }), 400

        if len(questions_data) == 0:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'questions array cannot be empty'
                }
            }), 400

        parser = QuestionParser()
        validated_questions = []

        for index, question_data in enumerate(questions_data):
            try:
                question = parser._parse_question(question_data, index)
                validated_questions.append(question)
            except ValidationError as e:
                return jsonify({
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': e.format_message(),
                        'details': {
                            'question_index': e.question_index
                        }
                    }
                }), 400

        try:
            imported_count = parser.batch_import(validated_questions)
            return jsonify({
                'imported_count': imported_count,
                'message': f'Successfully imported {imported_count} questions'
            }), 201

        except Exception as e:
            return jsonify({
                'error': {
                    'code': 'IMPORT_FAILED',
                    'message': f'Batch import failed: {str(e)}'
                }
            }), 500

    except Exception as e:
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred while importing questions'
            }
        }), 500


@admin_bp.route('/filter', methods=['GET'])
@require_auth
def filter_questions():
    """
    Retrieve questions filtered by topic area and/or difficulty level.

    Query Parameters:
        topic: Topic area filter (optional)
        difficulty: Difficulty level 1-5 (optional)

    Response:
        200: {
            "questions": [
                {
                    "question_id": int,
                    "question_text": string,
                    "options": array,
                    "correct_answer": string,
                    "explanation": string,
                    "memory_technique": string,
                    "topic_area": string,
                    "difficulty_level": int,
                    "incorrect_explanation": string | null,
                    "it_context_mapping": string | null,
                    "is_active": bool
                },
                ...
            ],
            "count": int
        }
        400: {
            "error": {
                "code": "INVALID_DIFFICULTY",
                "message": string
            }
        }
        500: {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": string
            }
        }

    Requirements: 11.12
    """
    try:
        topic = request.args.get('topic')
        difficulty = request.args.get('difficulty')

        query = Question.query.filter_by(is_active=True)

        if topic:
            query = query.filter_by(topic_area=topic)

        if difficulty:
            try:
                difficulty_level = int(difficulty)
                if difficulty_level < 1 or difficulty_level > 5:
                    return jsonify({
                        'error': {
                            'code': 'INVALID_DIFFICULTY',
                            'message': 'Difficulty must be between 1 and 5'
                        }
                    }), 400
                query = query.filter_by(difficulty_level=difficulty_level)
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DIFFICULTY',
                        'message': 'Difficulty must be an integer'
                    }
                }), 400

        questions = query.all()
        questions_data = [q.to_dict(include_answer=True) for q in questions]

        return jsonify({
            'questions': questions_data,
            'count': len(questions_data)
        }), 200

    except Exception as e:
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred while filtering questions'
            }
        }), 500


@admin_bp.route('/reseed', methods=['POST'])
@require_auth
def reseed_questions():
    """
    Regenerate the question bank from scratch.

    Runs gen.py to produce a fresh questions.json, then deactivates all
    existing questions and imports the new set.

    Response:
        200: {
            "imported_count": int,
            "deactivated_count": int,
            "message": string
        }
        500: {
            "error": { "code": "RESEED_FAILED", "message": string }
        }
    """
    try:
        seed_dir  = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seed_data')
        gen_script = os.path.join(seed_dir, 'gen.py')
        json_path  = os.path.join(seed_dir, 'questions.json')

        # Step 1 — regenerate questions.json
        result = subprocess.run(
            [sys.executable, gen_script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return jsonify({
                'error': {
                    'code': 'RESEED_FAILED',
                    'message': f'gen.py failed: {result.stderr.strip()}'
                }
            }), 500

        # Step 2 — deactivate all existing questions
        deactivated = Question.query.filter_by(is_active=True).count()
        Question.query.update({'is_active': False})
        db.session.commit()

        # Step 3 — import fresh questions
        import json
        with open(json_path, encoding='utf-8') as f:
            questions_data = json.load(f)

        count = 0
        for q in questions_data:
            db.session.add(Question(
                question_text=q['question_text'],
                options=q['options'],
                correct_answer=q['correct_answer'],
                explanation=q['explanation'],
                memory_technique=q['memory_technique'],
                topic_area=q['topic_area'],
                difficulty_level=q['difficulty_level'],
                it_context_mapping=q.get('it_context_mapping'),
                is_active=True
            ))
            count += 1

        db.session.commit()

        return jsonify({
            'imported_count': count,
            'deactivated_count': deactivated,
            'message': f'Question bank refreshed: {deactivated} old questions deactivated, {count} new questions imported.'
        }), 200

    except subprocess.TimeoutExpired:
        return jsonify({
            'error': {'code': 'RESEED_FAILED', 'message': 'gen.py timed out after 30 seconds.'}
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': {'code': 'RESEED_FAILED', 'message': str(e)}
        }), 500


@admin_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint - no authentication required.

    Response:
        200: {
            "status": "healthy"
        }

    Requirements: 14.11
    """
    return jsonify({'status': 'healthy'}), 200
