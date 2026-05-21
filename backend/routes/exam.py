"""
Exam mode routes — timed 65-question practice exams.
"""
import random
from datetime import datetime
from flask import Blueprint, request, jsonify
from functools import wraps
from services.auth_service import AuthService
from models.exam_attempt import ExamAttempt
from models.question import Question
from extensions import db

exam_bp = Blueprint('exam', __name__)


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


@exam_bp.route('/start', methods=['POST'])
@require_auth
def start_exam():
    """
    Start a new timed exam. Selects 65 random questions across all topics
    and difficulty levels, weighted to match the real exam distribution.

    Response 201: { exam: ExamAttempt, questions: [...] }
    """
    try:
        user_id = request.user_id

        # Check for an in-progress exam
        active_exam = ExamAttempt.query.filter_by(
            user_id=user_id, is_completed=False
        ).first()
        if active_exam:
            # Return the existing in-progress exam
            questions = Question.query.filter(
                Question.question_id.in_(active_exam.question_ids)
            ).all()
            # Maintain order
            q_map = {q.question_id: q for q in questions}
            ordered = [q_map[qid] for qid in active_exam.question_ids if qid in q_map]
            return jsonify({
                'exam': active_exam.to_dict(),
                'questions': [q.to_dict(include_answer=False) for q in ordered],
                'message': 'Resumed in-progress exam'
            }), 200

        # Select 65 questions with exam-like distribution:
        # Cloud Concepts ~24%, Security ~30%, Technology ~34%, Billing ~12%
        distribution = {
            'Cloud Concepts': 16,
            'Security and Compliance': 20,
            'Technology': 22,
            'Billing and Pricing': 7,
        }

        selected_ids = []
        for topic, count in distribution.items():
            pool = Question.query.filter_by(
                topic_area=topic, is_active=True
            ).all()
            if len(pool) < count:
                sample = pool
            else:
                sample = random.sample(pool, count)
            selected_ids.extend([q.question_id for q in sample])

        # Shuffle the final selection
        random.shuffle(selected_ids)

        # Create exam attempt
        exam = ExamAttempt(
            user_id=user_id,
            question_ids=selected_ids,
            answers={},
            total_questions=len(selected_ids),
            time_limit_seconds=5400,  # 90 minutes
        )
        db.session.add(exam)
        db.session.commit()

        # Fetch questions in order
        questions = Question.query.filter(
            Question.question_id.in_(selected_ids)
        ).all()
        q_map = {q.question_id: q for q in questions}
        ordered = [q_map[qid] for qid in selected_ids if qid in q_map]

        return jsonify({
            'exam': exam.to_dict(),
            'questions': [q.to_dict(include_answer=False) for q in ordered],
            'message': f'Exam started with {len(selected_ids)} questions. You have 90 minutes.'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500


@exam_bp.route('/answer', methods=['POST'])
@require_auth
def save_answer():
    """
    Save an answer for a question in the current exam.

    Body: { exam_id, question_id, answer }
    Response 200: { message, answers_count }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': {'code': 'INVALID_REQUEST', 'message': 'JSON body required'}}), 400

        exam_id = data.get('exam_id')
        question_id = data.get('question_id')
        answer = data.get('answer')

        if not all([exam_id, question_id, answer]):
            return jsonify({'error': {'code': 'MISSING_FIELDS', 'message': 'exam_id, question_id, and answer are required'}}), 400

        exam = ExamAttempt.query.filter_by(
            exam_id=exam_id, user_id=request.user_id
        ).first()

        if not exam:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Exam not found'}}), 404

        if exam.is_completed:
            return jsonify({'error': {'code': 'EXAM_COMPLETED', 'message': 'This exam has already been submitted'}}), 400

        # Check time limit
        elapsed = (datetime.utcnow() - exam.started_at).total_seconds()
        if elapsed > exam.time_limit_seconds:
            # Auto-complete the exam
            return _complete_exam(exam)

        # Save the answer
        answers = dict(exam.answers or {})
        answers[str(question_id)] = answer
        exam.answers = answers

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(exam, 'answers')
        db.session.commit()

        return jsonify({
            'message': 'Answer saved',
            'answers_count': len(answers),
            'total_questions': exam.total_questions
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500


@exam_bp.route('/submit', methods=['POST'])
@require_auth
def submit_exam():
    """
    Submit the exam for grading.

    Body: { exam_id }
    Response 200: { exam (with results), feedback }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': {'code': 'INVALID_REQUEST', 'message': 'JSON body required'}}), 400

        exam_id = data.get('exam_id')
        if not exam_id:
            return jsonify({'error': {'code': 'MISSING_FIELDS', 'message': 'exam_id is required'}}), 400

        exam = ExamAttempt.query.filter_by(
            exam_id=exam_id, user_id=request.user_id
        ).first()

        if not exam:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Exam not found'}}), 404

        if exam.is_completed:
            return jsonify({
                'exam': exam.to_dict(include_results=True),
                'message': 'Exam already submitted'
            }), 200

        return _complete_exam(exam)

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500


@exam_bp.route('/history', methods=['GET'])
@require_auth
def exam_history():
    """
    Get all completed exam attempts for the current user.

    Response 200: { exams: [...] }
    """
    try:
        exams = ExamAttempt.query.filter_by(
            user_id=request.user_id, is_completed=True
        ).order_by(ExamAttempt.completed_at.desc()).all()

        return jsonify({
            'exams': [e.to_dict() for e in exams]
        }), 200

    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500


@exam_bp.route('/result/<int:exam_id>', methods=['GET'])
@require_auth
def exam_result(exam_id):
    """
    Get detailed results for a specific exam attempt.

    Response 200: { exam (with results), questions_detail: [...] }
    """
    try:
        exam = ExamAttempt.query.filter_by(
            exam_id=exam_id, user_id=request.user_id
        ).first()

        if not exam:
            return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Exam not found'}}), 404

        if not exam.is_completed:
            return jsonify({'error': {'code': 'NOT_COMPLETED', 'message': 'Exam is still in progress'}}), 400

        # Get full question details for review
        questions = Question.query.filter(
            Question.question_id.in_(exam.question_ids)
        ).all()
        q_map = {q.question_id: q for q in questions}

        questions_detail = []
        answers = exam.answers or {}
        results = exam.results or {}

        for qid in exam.question_ids:
            q = q_map.get(qid)
            if not q:
                continue
            questions_detail.append({
                'question_id': qid,
                'question_text': q.question_text,
                'options': q.options,
                'correct_answer': q.correct_answer,
                'user_answer': answers.get(str(qid)),
                'is_correct': results.get(str(qid), False),
                'explanation': q.explanation,
                'memory_technique': q.memory_technique,
                'topic_area': q.topic_area,
            })

        return jsonify({
            'exam': exam.to_dict(include_results=True),
            'questions_detail': questions_detail
        }), 200

    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500


def _complete_exam(exam):
    """Grade and complete an exam."""
    from sqlalchemy.orm.attributes import flag_modified

    answers = exam.answers or {}
    results = {}
    correct_count = 0

    # Grade each question
    for qid in exam.question_ids:
        user_answer = answers.get(str(qid))
        question = Question.query.get(qid)
        if question and user_answer:
            is_correct = user_answer.strip() == question.correct_answer.strip()
        else:
            is_correct = False
        results[str(qid)] = is_correct
        if is_correct:
            correct_count += 1

    # Calculate score
    total = exam.total_questions
    score = round((correct_count / total) * 100, 1) if total > 0 else 0.0

    # Update exam
    exam.results = results
    exam.score = score
    exam.total_correct = correct_count
    exam.passed = score >= 70.0
    exam.is_completed = True
    exam.completed_at = datetime.utcnow()

    flag_modified(exam, 'results')
    flag_modified(exam, 'answers')
    db.session.commit()

    return jsonify({
        'exam': exam.to_dict(include_results=True),
        'message': f'Exam completed. Score: {score}% ({correct_count}/{total}). {"PASSED" if exam.passed else "FAILED"}'
    }), 200
