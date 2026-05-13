"""
Question and answer routes for retrieving questions and submitting answers.
"""
import time
from flask import Blueprint, request, jsonify
from functools import wraps
from services.auth_service import AuthService
from services.question_engine import QuestionEngine
from services.feedback_service import FeedbackService
from services.adaptive_system import AdaptiveSystem
from services.question_parser import QuestionParser, ValidationError, JSONParseError
from models.session import Session
from models.question import Question
from models.question_attempt import QuestionAttempt
from extensions import db

question_bp = Blueprint('question', __name__)


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


@question_bp.route('/next', methods=['GET'])
@require_auth
def get_next_question():
    """
    Get the next question based on session state and difficulty.
    
    Query Parameters:
        session_id: UUID of the current session (required)
        difficulty: Target difficulty level 1-5 (optional, uses session's current difficulty if not provided)
    
    Response:
        200: {
            "question": {
                "question_id": int,
                "question_text": string,
                "options": array,
                "topic_area": string,
                "difficulty_level": int
            }
        }
        400: {
            "error": {
                "code": "MISSING_FIELDS",
                "message": string
            }
        }
        404: {
            "error": {
                "code": "NO_QUESTIONS_AVAILABLE",
                "message": string
            }
        }
    
    Performance: <200ms under load of up to 100 concurrent users
    Requirements: 9.2, 15.1
    """
    start_time = time.time()
    
    try:
        # Get query parameters
        session_id = request.args.get('session_id')
        difficulty = request.args.get('difficulty')
        
        # Validate required parameters
        if not session_id:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Missing required parameter: session_id'
                }
            }), 400
        
        # Get session to determine difficulty
        session = Session.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({
                'error': {
                    'code': 'SESSION_NOT_FOUND',
                    'message': f'Session {session_id} not found'
                }
            }), 404
        
        # Use provided difficulty or session's current difficulty
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
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DIFFICULTY',
                        'message': 'Difficulty must be an integer'
                    }
                }), 400
        else:
            difficulty_level = session.current_difficulty_level
        
        # Get next question using QuestionEngine
        question_engine = QuestionEngine()
        question = question_engine.get_next_question(session_id, difficulty_level)
        
        if not question:
            return jsonify({
                'error': {
                    'code': 'NO_QUESTIONS_AVAILABLE',
                    'message': 'No questions available at the requested difficulty level'
                }
            }), 404
        
        # Update session's current question
        session.current_question_id = question.question_id
        db.session.commit()
        
        # Check response time (should be <200ms)
        elapsed_time = (time.time() - start_time) * 1000
        
        return jsonify({
            'question': question.to_dict(include_answer=False),
            '_response_time_ms': round(elapsed_time, 2)
        }), 200
        
    except Exception as e:
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred while retrieving the next question'
            }
        }), 500


@question_bp.route('/answer', methods=['POST'])
@require_auth
def submit_answer():
    """
    Submit an answer and receive immediate feedback with next question.
    
    Request Body:
        {
            "session_id": "string (UUID)",
            "question_id": int,
            "answer": "string"
        }
    
    Response:
        200: {
            "feedback": {
                "is_correct": bool,
                "correct_answer": string,
                "explanation": string,
                "incorrect_explanation": string | null,
                "memory_technique": string,
                "it_context_mapping": string | null
            },
            "next_question": {
                "question_id": int,
                "question_text": string,
                "options": array,
                "topic_area": string,
                "difficulty_level": int
            } | null
        }
        400: {
            "error": {
                "code": "MISSING_FIELDS" | "VALIDATION_ERROR",
                "message": string
            }
        }
        404: {
            "error": {
                "code": "NOT_FOUND",
                "message": string
            }
        }
    
    Performance: <300ms under load of up to 100 concurrent users
    Requirements: 9.3, 1.1-1.9, 3.1-3.7, 15.2
    """
    start_time = time.time()
    
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
        
        # Extract and validate required fields
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        user_answer = data.get('answer')
        
        missing_fields = []
        if not session_id:
            missing_fields.append('session_id')
        if question_id is None:
            missing_fields.append('question_id')
        if not user_answer:
            missing_fields.append('answer')
        
        if missing_fields:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'details': {'missing_fields': missing_fields}
                }
            }), 400
        
        # Get session
        session = Session.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({
                'error': {
                    'code': 'SESSION_NOT_FOUND',
                    'message': f'Session {session_id} not found'
                }
            }), 404
        
        # Get question
        question = Question.query.filter_by(question_id=question_id, is_active=True).first()
        if not question:
            return jsonify({
                'error': {
                    'code': 'QUESTION_NOT_FOUND',
                    'message': f'Question {question_id} not found or is inactive'
                }
            }), 404
        
        # Record the question attempt
        is_correct = user_answer.strip() == question.correct_answer.strip()
        
        attempt = QuestionAttempt(
            session_id=session_id,
            question_id=question_id,
            user_id=session.user_id,
            user_answer=user_answer,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
            difficulty_at_attempt=session.current_difficulty_level
        )
        db.session.add(attempt)
        
        # Mark question as answered in session
        question_engine = QuestionEngine()
        question_engine.mark_question_answered(session_id, question_id)
        
        # Adjust difficulty for next question
        adaptive_system = AdaptiveSystem()
        new_difficulty = adaptive_system.adjust_difficulty(
            session.current_difficulty_level,
            is_correct
        )
        session.current_difficulty_level = new_difficulty
        
        # Update session performance score
        total_attempts = QuestionAttempt.query.filter_by(session_id=session_id).count()
        correct_attempts = QuestionAttempt.query.filter_by(
            session_id=session_id,
            is_correct=True
        ).count()
        
        if total_attempts > 0:
            session.current_performance_score = round((correct_attempts / total_attempts) * 100, 1)
        
        db.session.commit()
        
        # Generate feedback using FeedbackService
        feedback_service = FeedbackService()
        feedback = feedback_service.generate_feedback(
            question_id,
            user_answer,
            question.correct_answer
        )
        
        # Get next question at new difficulty level
        next_question = question_engine.get_next_question(session_id, new_difficulty)
        
        # Update session's current question if next question exists
        if next_question:
            session.current_question_id = next_question.question_id
            db.session.commit()
        
        # Check response time (should be <300ms)
        elapsed_time = (time.time() - start_time) * 1000
        
        response_data = {
            'feedback': feedback.to_dict(),
            'next_question': next_question.to_dict(include_answer=False) if next_question else None,
            '_response_time_ms': round(elapsed_time, 2)
        }
        
        return jsonify(response_data), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        # Rollback on error
        db.session.rollback()
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred while processing the answer'
            }
        }), 500


@question_bp.route('/import', methods=['POST'])
@require_auth
def import_questions():
    """
    Batch import questions from JSON array.
    
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
                "code": "MISSING_FIELDS" | "VALIDATION_ERROR" | "JSON_PARSE_ERROR",
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
        
        # Extract questions array
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
        
        # Parse and validate questions using QuestionParser
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
        
        # Batch import using QuestionParser
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
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred while importing questions'
            }
        }), 500


@question_bp.route('/filter', methods=['GET'])
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
        # Get query parameters
        topic = request.args.get('topic')
        difficulty = request.args.get('difficulty')
        
        # Build query
        query = Question.query.filter_by(is_active=True)
        
        # Apply topic filter if provided
        if topic:
            query = query.filter_by(topic_area=topic)
        
        # Apply difficulty filter if provided
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
        
        # Execute query
        questions = query.all()
        
        # Convert to dict with full details (include_answer=True)
        questions_data = [q.to_dict(include_answer=True) for q in questions]
        
        return jsonify({
            'questions': questions_data,
            'count': len(questions_data)
        }), 200
        
    except Exception as e:
        # Log error in production
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred while filtering questions'
            }
        }), 500


@question_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint - no authentication required.
    
    Response:
        200: {
            "status": "ok"
        }
    
    Requirements: 13.1
    """
    return jsonify({
        'status': 'ok'
    }), 200
