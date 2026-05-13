"""
Question model for exam questions and metadata.
"""
from datetime import datetime
from extensions import db


class Question(db.Model):
    """
    Question model representing exam practice questions.
    
    Attributes:
        question_id: Primary key, unique identifier for the question
        question_text: The question text (max 1000 characters)
        options: JSON array of answer options (2-6 strings, max 500 chars each)
        correct_answer: The correct answer (must match one option)
        explanation: Explanation of why the correct answer is correct (max 2000 chars)
        incorrect_explanation: Optional explanation for incorrect answers
        memory_technique: Mnemonic device or memory aid (max 500 chars)
        topic_area: Exam topic area (Cloud Concepts, Security, Technology, Billing)
        difficulty_level: Question difficulty (1-5 scale)
        it_context_mapping: Traditional IT equivalents for AWS concepts
        created_date: Timestamp when question was created
        modified_date: Timestamp when question was last modified
        is_active: Whether question is active in the question pool
    """
    __tablename__ = 'questions'
    
    question_id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)  # Array of strings
    correct_answer = db.Column(db.String(500), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    incorrect_explanation = db.Column(db.Text)
    memory_technique = db.Column(db.Text, nullable=False)
    topic_area = db.Column(db.String(100), nullable=False, index=True)
    difficulty_level = db.Column(db.Integer, nullable=False, index=True)
    it_context_mapping = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    modified_date = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    attempts = db.relationship('QuestionAttempt', backref='question', lazy='dynamic')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('difficulty_level >= 1 AND difficulty_level <= 5', name='check_difficulty_level_range'),
        db.CheckConstraint('length(question_text) > 0 AND length(question_text) <= 1000', name='check_question_text_length'),
        db.CheckConstraint('length(explanation) >= 50 AND length(explanation) <= 2000', name='check_explanation_length'),
        db.CheckConstraint('length(memory_technique) > 0 AND length(memory_technique) <= 500', name='check_memory_technique_length'),
        db.CheckConstraint('length(correct_answer) > 0 AND length(correct_answer) <= 500', name='check_correct_answer_length'),
        db.Index('idx_topic_difficulty', 'topic_area', 'difficulty_level'),
        db.Index('idx_active_difficulty', 'is_active', 'difficulty_level'),
    )
    
    def __repr__(self):
        return f'<Question {self.question_id}: {self.question_text[:50]}...>'
    
    def to_dict(self, include_answer=False):
        """
        Convert question to dictionary representation.
        
        Args:
            include_answer: Whether to include the correct answer (default False)
        
        Returns:
            Dictionary representation of the question
        """
        data = {
            'question_id': self.question_id,
            'question_text': self.question_text,
            'options': self.options,
            'topic_area': self.topic_area,
            'difficulty_level': self.difficulty_level,
        }
        
        if include_answer:
            data.update({
                'correct_answer': self.correct_answer,
                'explanation': self.explanation,
                'incorrect_explanation': self.incorrect_explanation,
                'memory_technique': self.memory_technique,
                'it_context_mapping': self.it_context_mapping,
                'is_active': self.is_active,
            })
        
        return data
