"""
Session model for user practice sessions.
"""
from datetime import datetime
from extensions import db


class Session(db.Model):
    """
    Session model representing a user's practice session.
    
    Attributes:
        session_id: Primary key, UUID string identifier
        user_id: Foreign key to users table
        answered_question_ids: JSON array of question IDs answered in this session
        current_difficulty_level: Current adaptive difficulty level (1-5)
        current_performance_score: Current session performance score (0.0-100.0)
        current_question_id: Foreign key to current question being displayed
        is_drill_mode: Whether session is in drill mode
        drill_mode_topics: JSON array of topic areas for drill mode
        created_at: Timestamp when session was created
        updated_at: Timestamp when session was last updated
        is_active: Whether this is the user's active session
    """
    __tablename__ = 'sessions'
    
    session_id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    answered_question_ids = db.Column(db.JSON, default=list, nullable=False)
    current_difficulty_level = db.Column(db.Integer, default=2, nullable=False)
    current_performance_score = db.Column(db.Float, default=0.0, nullable=False)
    current_question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'))
    is_drill_mode = db.Column(db.Boolean, default=False, nullable=False)
    drill_mode_topics = db.Column(db.JSON, default=list, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    attempts = db.relationship('QuestionAttempt', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    current_question = db.relationship('Question', foreign_keys=[current_question_id])
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('current_difficulty_level >= 1 AND current_difficulty_level <= 5', name='check_session_difficulty_range'),
        db.CheckConstraint('current_performance_score >= 0.0 AND current_performance_score <= 100.0', name='check_performance_score_range'),
        db.Index('idx_user_active', 'user_id', 'is_active'),
        db.Index('idx_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Session {self.session_id} for User {self.user_id}>'
    
    def to_dict(self):
        """Convert session to dictionary representation."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'answered_question_ids': self.answered_question_ids,
            'current_difficulty_level': self.current_difficulty_level,
            'current_performance_score': round(self.current_performance_score, 1),
            'current_question_id': self.current_question_id,
            'is_drill_mode': self.is_drill_mode,
            'drill_mode_topics': self.drill_mode_topics,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
