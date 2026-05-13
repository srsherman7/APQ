"""
Feedback System service for generating immediate feedback with explanations and memory techniques.

This service provides comprehensive feedback after each answer submission, including:
- Correctness indicator
- Correct answer
- Explanation of why the correct answer is correct
- Explanation of why the user's answer was incorrect (if applicable)
- Memory techniques and mnemonic devices
- IT professional context mapping to traditional technologies
"""
from dataclasses import dataclass
from typing import Optional
from models.question import Question


@dataclass
class FeedbackResponse:
    """
    Data transfer object for feedback responses.
    
    Attributes:
        is_correct: Whether the user's answer was correct
        correct_answer: The correct answer to the question
        explanation: Explanation of why the correct answer is correct
        incorrect_explanation: Explanation of why the user's answer was incorrect (None if correct)
        memory_technique: Mnemonic device or memory aid for retention
        it_context_mapping: Traditional IT equivalents for AWS concepts (optional)
        next_question: The next question to present (optional, handled by Question Engine)
    """
    is_correct: bool
    correct_answer: str
    explanation: str
    incorrect_explanation: Optional[str]
    memory_technique: str
    it_context_mapping: Optional[str]
    next_question: Optional[dict] = None
    
    def to_dict(self):
        """Convert FeedbackResponse to dictionary for JSON serialization."""
        return {
            'is_correct': self.is_correct,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'incorrect_explanation': self.incorrect_explanation,
            'memory_technique': self.memory_technique,
            'it_context_mapping': self.it_context_mapping,
            'next_question': self.next_question,
        }


class FeedbackService:
    """
    Service for generating immediate feedback after answer submission.
    
    Responsibilities:
    - Generate comprehensive feedback for answer submissions
    - Retrieve explanations for correct answers
    - Retrieve memory techniques and mnemonic devices
    - Retrieve IT professional context mappings
    - Include incorrect explanations when answer is wrong
    """
    
    def generate_feedback(self, question_id: int, user_answer: str, correct_answer: str) -> FeedbackResponse:
        """
        Generates comprehensive feedback for an answer submission.
        
        Args:
            question_id: The ID of the question being answered
            user_answer: The answer provided by the user
            correct_answer: The correct answer to the question
        
        Returns:
            FeedbackResponse with correctness, explanations, and memory techniques
        
        Raises:
            ValueError: If question_id is not found in the database
        """
        # Retrieve the question from the database
        question = Question.query.filter_by(question_id=question_id, is_active=True).first()
        
        if not question:
            raise ValueError(f"Question with ID {question_id} not found or is inactive")
        
        # Determine if the answer is correct
        is_correct = user_answer.strip() == correct_answer.strip()
        
        # Get explanation
        explanation = self.get_explanation(question_id)
        
        # Get incorrect explanation if answer is wrong
        incorrect_explanation = None
        if not is_correct:
            incorrect_explanation = self.get_incorrect_explanation(question_id)
        
        # Get memory technique
        memory_technique = self.get_memory_technique(question_id)
        
        # Get IT context mapping
        it_context_mapping = self.get_it_context_mapping(question_id)
        
        return FeedbackResponse(
            is_correct=is_correct,
            correct_answer=correct_answer,
            explanation=explanation,
            incorrect_explanation=incorrect_explanation,
            memory_technique=memory_technique,
            it_context_mapping=it_context_mapping,
        )
    
    def get_explanation(self, question_id: int) -> str:
        """
        Retrieves the explanation text for a question.
        
        Args:
            question_id: The ID of the question
        
        Returns:
            Explanation text describing why the correct answer is correct
        
        Raises:
            ValueError: If question_id is not found in the database
        """
        question = Question.query.filter_by(question_id=question_id, is_active=True).first()
        
        if not question:
            raise ValueError(f"Question with ID {question_id} not found or is inactive")
        
        return question.explanation
    
    def get_incorrect_explanation(self, question_id: int) -> Optional[str]:
        """
        Retrieves the incorrect explanation text for a question.
        
        Args:
            question_id: The ID of the question
        
        Returns:
            Explanation text describing why incorrect answers are wrong, or None if not available
        
        Raises:
            ValueError: If question_id is not found in the database
        """
        question = Question.query.filter_by(question_id=question_id, is_active=True).first()
        
        if not question:
            raise ValueError(f"Question with ID {question_id} not found or is inactive")
        
        return question.incorrect_explanation
    
    def get_memory_technique(self, question_id: int) -> str:
        """
        Retrieves the mnemonic device or memory technique for a question.
        
        Args:
            question_id: The ID of the question
        
        Returns:
            Memory technique text to aid retention
        
        Raises:
            ValueError: If question_id is not found in the database
        """
        question = Question.query.filter_by(question_id=question_id, is_active=True).first()
        
        if not question:
            raise ValueError(f"Question with ID {question_id} not found or is inactive")
        
        return question.memory_technique
    
    def get_it_context_mapping(self, question_id: int) -> Optional[str]:
        """
        Retrieves traditional IT equivalents for AWS concepts.
        
        Args:
            question_id: The ID of the question
        
        Returns:
            IT context mapping text describing traditional IT equivalents, or None if not available
        
        Raises:
            ValueError: If question_id is not found in the database
        """
        question = Question.query.filter_by(question_id=question_id, is_active=True).first()
        
        if not question:
            raise ValueError(f"Question with ID {question_id} not found or is inactive")
        
        return question.it_context_mapping
