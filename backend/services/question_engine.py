"""
Question Engine service for managing question selection and presentation.

This service handles:
- Question selection based on difficulty level
- Question pool randomization for sessions
- Duplicate prevention within sessions
- Fallback logic when exact difficulty unavailable
"""
import random
from typing import Optional, List
from sqlalchemy import and_
from extensions import db
from models.question import Question
from models.session import Session


class QuestionEngine:
    """
    Manages question selection, randomization, and presentation logic.
    
    Responsibilities:
    - Select next unanswered question at specified difficulty
    - Randomize question order for new sessions
    - Track answered questions to prevent duplicates
    - Find closest difficulty question when exact match unavailable
    """
    
    def get_next_question(self, session_id: str, difficulty_level: int) -> Optional[Question]:
        """
        Returns next unanswered question for session at specified difficulty.
        Scoped to the session's module.
        """
        session = Session.query.get(session_id)
        if not session:
            return None
        
        answered_ids = session.answered_question_ids or []
        module_id = session.module_id
        
        # Query for active questions at target difficulty in this module
        query = Question.query.filter(
            and_(
                Question.is_active == True,
                Question.module_id == module_id,
                Question.difficulty_level == difficulty_level,
                ~Question.question_id.in_(answered_ids) if answered_ids else True
            )
        )
        
        questions = query.all()
        
        if questions:
            return random.choice(questions)
        
        # If no questions at exact difficulty, try fallback
        return self.get_closest_difficulty_question(session_id, difficulty_level)
    
    def randomize_question_pool(self, session_id: str) -> List[int]:
        """
        Creates randomized question order for session.
        
        This method generates a shuffled list of all active question IDs
        that can be used to determine question order for a session.
        
        Args:
            session_id: UUID of the session
        
        Returns:
            List of question IDs in randomized order
        
        Requirements: 1.3
        """
        # Get all active questions
        questions = Question.query.filter_by(is_active=True).all()
        question_ids = [q.question_id for q in questions]
        
        # Shuffle using pseudorandom algorithm
        random.shuffle(question_ids)
        
        return question_ids
    
    def mark_question_answered(self, session_id: str, question_id: int) -> bool:
        """
        Tracks answered questions to prevent duplicates within a session.
        
        Args:
            session_id: UUID of the current session
            question_id: ID of the question that was answered
        
        Returns:
            True if successfully marked, False if session not found
        
        Requirements: 1.4
        """
        session = Session.query.get(session_id)
        if not session:
            return False
        
        # Initialize answered_question_ids if None
        if session.answered_question_ids is None:
            session.answered_question_ids = []
        
        # Add question ID if not already present
        if question_id not in session.answered_question_ids:
            # Create a new list to trigger SQLAlchemy's change detection
            answered_ids = list(session.answered_question_ids)
            answered_ids.append(question_id)
            session.answered_question_ids = answered_ids
            
            try:
                db.session.commit()
                return True
            except Exception as e:
                db.session.rollback()
                raise e
        
        return True
    
    def get_closest_difficulty_question(self, session_id: str, target_difficulty: int) -> Optional[Question]:
        """
        Finds question when exact difficulty unavailable.
        Scoped to the session's module.
        """
        session = Session.query.get(session_id)
        if not session:
            return None
        
        answered_ids = session.answered_question_ids or []
        module_id = session.module_id
        
        for offset in range(1, 5):
            for difficulty in [target_difficulty + offset, target_difficulty - offset]:
                if difficulty < 1 or difficulty > 5:
                    continue
                
                query = Question.query.filter(
                    and_(
                        Question.is_active == True,
                        Question.module_id == module_id,
                        Question.difficulty_level == difficulty,
                        ~Question.question_id.in_(answered_ids) if answered_ids else True
                    )
                )
                
                questions = query.all()
                if questions:
                    return random.choice(questions)
        
        return None
