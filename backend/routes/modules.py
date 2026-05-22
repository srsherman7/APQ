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


@modules_bp.route('/create', methods=['POST'])
@require_auth
def create_module():
    """
    Create a new learning module.

    Body: {
        name: string (required),
        slug: string (optional — auto-generated from name if not provided),
        description: string (optional),
        icon: string (optional, default 'school'),
        exam_question_count: int (required),
        exam_time_limit_seconds: int (required),
        exam_passing_score: float (required),
        topic_areas: string[] (required)
    }

    Response 201: { module: {...}, message: string }
    """
    from extensions import db
    import re

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': {'code': 'INVALID_REQUEST', 'message': 'JSON body required'}}), 400

        # Validate required fields
        name = data.get('name')
        topic_areas = data.get('topic_areas')
        exam_question_count = data.get('exam_question_count')
        exam_time_limit_seconds = data.get('exam_time_limit_seconds')
        exam_passing_score = data.get('exam_passing_score')

        if not all([name, topic_areas, exam_question_count, exam_time_limit_seconds, exam_passing_score]):
            return jsonify({'error': {'code': 'MISSING_FIELDS', 'message': 'name, topic_areas, exam_question_count, exam_time_limit_seconds, and exam_passing_score are required'}}), 400

        if not isinstance(topic_areas, list) or len(topic_areas) == 0:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'topic_areas must be a non-empty array'}}), 400

        # Generate slug if not provided
        slug = data.get('slug') or re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

        # Check for duplicate slug
        if Module.query.filter_by(slug=slug).first():
            return jsonify({'error': {'code': 'DUPLICATE', 'message': f'Module with slug "{slug}" already exists'}}), 409

        module = Module(
            slug=slug,
            name=name,
            description=data.get('description', ''),
            icon=data.get('icon', 'school'),
            exam_question_count=int(exam_question_count),
            exam_time_limit_seconds=int(exam_time_limit_seconds),
            exam_passing_score=float(exam_passing_score),
            topic_areas=topic_areas,
        )
        db.session.add(module)
        db.session.commit()

        return jsonify({
            'module': module.to_dict(),
            'message': f'Module "{name}" created successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500


@modules_bp.route('/<slug>/import', methods=['POST'])
@require_auth
def import_module_questions(slug):
    """
    Import questions into a specific module.

    Body: {
        questions: [{question_text, options, correct_answer, explanation,
                     memory_technique, topic_area, difficulty_level, it_context_mapping?}, ...]
    }

    Response 201: { imported_count, skipped_count, message }
    """
    from extensions import db
    from models.question import Question

    try:
        module = Module.query.filter_by(slug=slug).first()
        if not module:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': f'Module "{slug}" not found'}}), 404

        data = request.get_json()
        if not data or 'questions' not in data:
            return jsonify({'error': {'code': 'MISSING_FIELDS', 'message': 'questions array is required'}}), 400

        questions = data['questions']
        if not isinstance(questions, list) or len(questions) == 0:
            return jsonify({'error': {'code': 'VALIDATION_ERROR', 'message': 'questions must be a non-empty array'}}), 400

        imported = 0
        skipped = 0
        errors = []

        for i, q in enumerate(questions):
            # Validate required fields
            required = ['question_text', 'options', 'correct_answer', 'explanation', 'memory_technique', 'topic_area', 'difficulty_level']
            missing = [f for f in required if f not in q or not q[f]]
            if missing:
                errors.append(f'Question {i}: missing {", ".join(missing)}')
                continue

            # Validate options
            if not isinstance(q['options'], list) or len(q['options']) < 2:
                errors.append(f'Question {i}: options must have at least 2 items')
                continue

            # Validate correct_answer is in options
            if q['correct_answer'] not in q['options']:
                errors.append(f'Question {i}: correct_answer must match one of the options')
                continue

            # Validate difficulty
            if not isinstance(q['difficulty_level'], int) or q['difficulty_level'] < 1 or q['difficulty_level'] > 5:
                errors.append(f'Question {i}: difficulty_level must be 1-5')
                continue

            # Validate topic_area is in module's topics
            if q['topic_area'] not in module.topic_areas:
                errors.append(f'Question {i}: topic_area "{q["topic_area"]}" not in module topics {module.topic_areas}')
                continue

            # Skip duplicates
            if Question.query.filter_by(question_text=q['question_text']).first():
                skipped += 1
                continue

            db.session.add(Question(
                module_id=module.module_id,
                question_text=q['question_text'],
                options=q['options'],
                correct_answer=q['correct_answer'],
                explanation=q['explanation'],
                memory_technique=q['memory_technique'],
                topic_area=q['topic_area'],
                difficulty_level=q['difficulty_level'],
                it_context_mapping=q.get('it_context_mapping'),
                is_active=True,
            ))
            imported += 1

        db.session.commit()

        result = {
            'imported_count': imported,
            'skipped_count': skipped,
            'message': f'Imported {imported} questions, skipped {skipped} duplicates.'
        }
        if errors:
            result['errors'] = errors[:20]  # Limit error list
            result['message'] += f' {len(errors)} validation errors.'

        return jsonify(result), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500


@modules_bp.route('/<slug>/export', methods=['GET'])
@require_auth
def export_module_questions(slug):
    """
    Export all questions from a module as JSON.

    Response 200: { module: {...}, questions: [...] }
    """
    from models.question import Question

    try:
        module = Module.query.filter_by(slug=slug).first()
        if not module:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': f'Module "{slug}" not found'}}), 404

        questions = Question.query.filter_by(module_id=module.module_id, is_active=True).all()
        questions_data = [{
            'question_text': q.question_text,
            'options': q.options,
            'correct_answer': q.correct_answer,
            'explanation': q.explanation,
            'memory_technique': q.memory_technique,
            'topic_area': q.topic_area,
            'difficulty_level': q.difficulty_level,
            'it_context_mapping': q.it_context_mapping,
        } for q in questions]

        return jsonify({
            'module': module.to_dict(),
            'questions': questions_data
        }), 200

    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500
