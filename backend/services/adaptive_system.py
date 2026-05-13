"""
Adaptive System service for adjusting question difficulty based on user performance.

This service implements the adaptive difficulty algorithm that adjusts question
difficulty levels (1-5) based on whether users answer correctly or incorrectly.
"""
from typing import Optional
from models.session import Session
from models.question_attempt import QuestionAttempt
from extensions import db


class AdaptiveSystem:
    """
    Service for managing adaptive difficulty adjustments.
    
    The adaptive system adjusts difficulty levels based on user performance:
    - Correct answer: increase difficulty by 1 (max 5)
    - Incorrect answer: decrease difficulty by 1 (min 1)
    - Starting difficulty: 2
    """
    
    @staticmethod
    def get_starting_difficulty() -> int:
        """
        Returns the initial difficulty level for new sessions.
        
        Returns:
            int: Starting difficulty level (always 2)
        """
        return 2
    
    @staticmethod
    def adjust_difficulty(current_level: int, is_correct: bool) -> int:
        """
        Adjusts difficulty level based on answer correctness.
        
        Args:
            current_level: Current difficulty level (1-5)
            is_correct: Whether the user answered correctly
            
        Returns:
            int: New difficulty level (1-5)
            
        Examples:
            >>> AdaptiveSystem.adjust_difficulty(3, True)
            4
            >>> AdaptiveSystem.adjust_difficulty(3, False)
            2
            >>> AdaptiveSystem.adjust_difficulty(5, True)
            5
            >>> AdaptiveSystem.adjust_difficulty(1, False)
            1
        """
        if is_correct:
            # Increase difficulty by 1, max 5
            return min(current_level + 1, 5)
        else:
            # Decrease difficulty by 1, min 1
            return max(current_level - 1, 1)
    
    @staticmethod
    def calculate_next_difficulty(session_id: str) -> int:
        """
        Determines difficulty for next question based on last answer in session.
        
        This method looks at the most recent question attempt in the session
        and adjusts the current difficulty level accordingly.
        
        Args:
            session_id: UUID string identifier for the session
            
        Returns:
            int: Difficulty level for next question (1-5)
            
        Raises:
            ValueError: If session not found
        """
        # Get the session
        session = Session.query.filter_by(session_id=session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get the most recent attempt for this session
        last_attempt = QuestionAttempt.query.filter_by(
            session_id=session_id
        ).order_by(
            QuestionAttempt.timestamp.desc()
        ).first()
        
        # If no attempts yet, return starting difficulty
        if not last_attempt:
            return AdaptiveSystem.get_starting_difficulty()
        
        # Adjust difficulty based on last attempt
        new_difficulty = AdaptiveSystem.adjust_difficulty(
            session.current_difficulty_level,
            last_attempt.is_correct
        )
        
        # Update session with new difficulty
        session.current_difficulty_level = new_difficulty
        db.session.commit()
        
        return new_difficulty
