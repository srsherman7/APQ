"""
QuestionAttempt model for tracking user answers and performance.
"""
from datetime import datetime
from extensions import db


class QuestionAttempt(db.Model):
    """
    QuestionAttempt model representing a single question answer attempt.
    
    Attributes:
        attempt_id: Primary key, unique identifier for the attempt
        session_id: Foreign key to sessions table
        question_id: Foreign key to questions table
        user_id: Foreign key to users table
        user_answer: The answer selected by the user
        correct_answer: The correct answer for the question
        is_correct: Whether the user's answer was correct
        difficulty_at_attempt: The difficulty level when question was attempted
        timestamp: Timestamp when the attempt was made
    """
    __tablename__ = 'question_attempts'
    
    attempt_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('sessions.session_id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    user_answer = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    difficulty_at_attempt = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Constraints and Indexes for performance
    __table_args__ = (
        db.CheckConstraint('difficulty_at_attempt >= 1 AND difficulty_at_attempt <= 5', name='check_attempt_difficulty_range'),
        db.Index('idx_user_topic_performance', 'user_id', 'timestamp'),
        db.Index('idx_session_attempts', 'session_id', 'timestamp'),
        db.Index('idx_user_question', 'user_id', 'question_id'),
    )
    
    def __repr__(self):
        return f'<QuestionAttempt {self.attempt_id}: User {self.user_id}, Question {self.question_id}, Correct: {self.is_correct}>'
    
    def to_dict(self):
        """Convert question attempt to dictionary representation."""
        return {
            'attempt_id': self.attempt_id,
            'session_id': self.session_id,
            'question_id': self.question_id,
            'user_id': self.user_id,
            'user_answer': self.user_answer,
            'correct_answer': self.correct_answer,
            'is_correct': self.is_correct,
            'difficulty_at_attempt': self.difficulty_at_attempt,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
