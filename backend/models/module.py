"""
Module model — represents a certification or course module.
Each module has its own question pool, exam format, topic areas, and progress tracking.
"""
from datetime import datetime
from extensions import db


class Module(db.Model):
    """
    A learning module (e.g., AWS Cloud Practitioner, Solutions Architect, etc.)

    Attributes:
        module_id: Primary key
        slug: URL-friendly identifier (e.g., 'cloud-practitioner')
        name: Display name (e.g., 'AWS Cloud Practitioner')
        description: Short description of the module
        icon: Material icon name for the UI
        exam_question_count: Number of questions in a timed exam (e.g., 65)
        exam_time_limit_seconds: Time limit for timed exam (e.g., 5400 = 90 min)
        exam_passing_score: Passing percentage (e.g., 70.0)
        topic_areas: JSON array of topic area names for this module
        is_active: Whether the module is available to users
        created_at: When the module was created
    """
    __tablename__ = 'modules'

    module_id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='school')
    exam_question_count = db.Column(db.Integer, nullable=False, default=65)
    exam_time_limit_seconds = db.Column(db.Integer, nullable=False, default=5400)
    exam_passing_score = db.Column(db.Float, nullable=False, default=70.0)
    topic_areas = db.Column(db.JSON, nullable=False, default=list)
    study_content = db.Column(db.JSON, default=dict)  # Per-module study guides and cheatsheets
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    questions = db.relationship('Question', backref='module', lazy='dynamic')
    sessions = db.relationship('Session', backref='module', lazy='dynamic')
    exam_attempts = db.relationship('ExamAttempt', backref='module', lazy='dynamic')

    def __repr__(self):
        return f'<Module {self.slug}: {self.name}>'

    def to_dict(self):
        return {
            'module_id': self.module_id,
            'slug': self.slug,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'exam_question_count': self.exam_question_count,
            'exam_time_limit_seconds': self.exam_time_limit_seconds,
            'exam_passing_score': self.exam_passing_score,
            'topic_areas': self.topic_areas,
            'is_active': self.is_active,
            'question_count': self.questions.filter_by(is_active=True).count() if self.questions else 0,
        }
