"""
UserProfile model for user analytics and performance tracking.
"""
from datetime import datetime
from extensions import db


class UserProfile(db.Model):
    """
    UserProfile model representing user performance analytics.
    
    Attributes:
        profile_id: Primary key, unique identifier for the profile
        user_id: Foreign key to users table (unique, one-to-one relationship)
        weak_areas: JSON array of weak areas with topic, score, and attempt count
                   Format: [{"topic": str, "score": float, "attempt_count": int}]
        topic_scores: JSON object mapping topics to performance data
                     Format: {"topic": {"correct": int, "total": int, "score": float}}
        total_questions_answered: Total number of questions answered by user
        overall_performance_score: Overall performance score across all questions (0.0-100.0)
        last_updated: Timestamp when profile was last updated
    """
    __tablename__ = 'user_profiles'
    
    profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True, nullable=False, index=True)
    weak_areas = db.Column(db.JSON, default=list, nullable=False)  # [{"topic": str, "score": float, "attempt_count": int}]
    topic_scores = db.Column(db.JSON, default=dict, nullable=False)  # {"topic": {"correct": int, "total": int, "score": float}}
    total_questions_answered = db.Column(db.Integer, default=0, nullable=False)
    overall_performance_score = db.Column(db.Float, default=0.0, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('total_questions_answered >= 0', name='check_total_questions_positive'),
        db.CheckConstraint('overall_performance_score >= 0.0 AND overall_performance_score <= 100.0', name='check_overall_score_range'),
    )
    
    def __repr__(self):
        return f'<UserProfile for User {self.user_id}>'
    
    def to_dict(self):
        """Convert user profile to dictionary representation."""
        return {
            'profile_id': self.profile_id,
            'user_id': self.user_id,
            'weak_areas': self.weak_areas,
            'topic_scores': self.topic_scores,
            'total_questions_answered': self.total_questions_answered,
            'overall_performance_score': round(self.overall_performance_score, 1),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
