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
        
        Args:
            session_id: UUID of the current session
            difficulty_level: Target difficulty level (1-5)
        
        Returns:
            Question object if available, None if no questions available
        
        Requirements: 1.1, 1.3, 1.4, 2.6
        """
        # Get session to access answered questions
        session = Session.query.get(session_id)
        if not session:
            return None
        
        answered_ids = session.answered_question_ids or []
        
        # Query for active questions at target difficulty, excluding answered ones
        query = Question.query.filter(
            and_(
                Question.is_active == True,
                Question.difficulty_level == difficulty_level,
                ~Question.question_id.in_(answered_ids) if answered_ids else True
            )
        )
        
        # Get all matching questions and select randomly
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
        
        Searches for questions at closest available difficulty level by checking
        levels in order: target±1, target±2, etc.
        
        Args:
            session_id: UUID of the current session
            target_difficulty: Target difficulty level (1-5)
        
        Returns:
            Question object at closest available difficulty, None if no questions available
        
        Requirements: 2.6
        """
        session = Session.query.get(session_id)
        if not session:
            return None
        
        answered_ids = session.answered_question_ids or []
        
        # Try difficulty levels in order of proximity: ±1, ±2, ±3, ±4
        for offset in range(1, 5):
            # Try both directions at this offset
            for difficulty in [target_difficulty + offset, target_difficulty - offset]:
                # Skip if out of valid range (1-5)
                if difficulty < 1 or difficulty > 5:
                    continue
                
                # Query for questions at this difficulty
                query = Question.query.filter(
                    and_(
                        Question.is_active == True,
                        Question.difficulty_level == difficulty,
                        ~Question.question_id.in_(answered_ids) if answered_ids else True
                    )
                )
                
                questions = query.all()
                if questions:
                    return random.choice(questions)
        
        # No unanswered questions available at any difficulty
        return None
