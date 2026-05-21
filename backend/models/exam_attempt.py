"""
ExamAttempt model for timed practice exams (65 questions, 90 minutes).
"""
from datetime import datetime
from extensions import db


class ExamAttempt(db.Model):
    """
    Represents a single timed exam attempt by a user.

    Attributes:
        exam_id: Primary key
        user_id: The user taking the exam
        started_at: When the exam was started
        completed_at: When the exam was submitted (null if in progress)
        time_limit_seconds: Time limit (default 5400 = 90 minutes)
        question_ids: JSON array of 65 question IDs in order
        answers: JSON object mapping question_id -> user's answer (null if unanswered)
        results: JSON object mapping question_id -> is_correct (populated on completion)
        score: Percentage score (0-100, null if in progress)
        total_correct: Number of correct answers (null if in progress)
        total_questions: Number of questions (65)
        passed: Whether the user passed (score >= 70, null if in progress)
        is_completed: Whether the exam has been submitted
    """
    __tablename__ = 'exam_attempts'

    exam_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    time_limit_seconds = db.Column(db.Integer, nullable=False, default=5400)
    question_ids = db.Column(db.JSON, nullable=False)
    answers = db.Column(db.JSON, nullable=False, default=dict)
    results = db.Column(db.JSON)
    score = db.Column(db.Float)
    total_correct = db.Column(db.Integer)
    total_questions = db.Column(db.Integer, nullable=False, default=65)
    passed = db.Column(db.Boolean)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'<ExamAttempt {self.exam_id} user={self.user_id} score={self.score}>'

    def to_dict(self, include_results=False):
        data = {
            'exam_id': self.exam_id,
            'user_id': self.user_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'time_limit_seconds': self.time_limit_seconds,
            'total_questions': self.total_questions,
            'is_completed': self.is_completed,
            'score': self.score,
            'total_correct': self.total_correct,
            'passed': self.passed,
        }
        if include_results:
            data['question_ids'] = self.question_ids
            data['answers'] = self.answers
            data['results'] = self.results
        return data
