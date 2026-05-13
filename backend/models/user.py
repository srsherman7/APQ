"""
User model for authentication and user management.
"""
from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    """
    User model representing registered users of the application.
    
    Attributes:
        user_id: Primary key, unique identifier for the user
        username: Unique username (3-30 characters)
        email: Unique email address
        password_hash: Hashed password using bcrypt
        created_at: Timestamp when user account was created
        last_login: Timestamp of most recent successful login
        failed_login_attempts: Counter for failed login attempts
        failed_login_window_start: Timestamp when current failed login window started
    """
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    failed_login_window_start = db.Column(db.DateTime)
    
    # Relationships
    sessions = db.relationship('Session', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    attempts = db.relationship('QuestionAttempt', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('length(username) >= 3 AND length(username) <= 30', name='check_username_length'),
        db.CheckConstraint('failed_login_attempts >= 0', name='check_failed_login_attempts_positive'),
    )
    
    def get_id(self):
        """Return the user ID as a string for Flask-Login."""
        return str(self.user_id)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert user to dictionary representation (excluding sensitive data)."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
