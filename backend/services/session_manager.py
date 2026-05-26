"""
Session Manager service for handling session persistence and state management.

This service manages user practice sessions including:
- Creating new sessions
- Saving session state with retry logic
- Restoring user sessions
- Clearing sessions while preserving history
- Ensuring only one active session per user
"""
import uuid
import time
from typing import Optional, Dict, Any
from datetime import datetime
from extensions import db
from models.session import Session
from models.user import User


class SessionManager:
    """
    Manages session persistence, state management, and recovery.
    
    Responsibilities:
    - Initialize new sessions with UUID
    - Save session state with retry logic (3 attempts)
    - Restore most recent active session for user
    - Clear session while preserving history
    - Enforce one active session per user constraint
    """
    
    @staticmethod
    def create_session(user_id: int, module_id: int = 1) -> Optional[Session]:
        """
        Create a new session for the specified user and module.
        
        Deactivates any existing active sessions for the user in this module
        to ensure only one active session exists per module at a time.
        
        Args:
            user_id: The ID of the user to create a session for
            module_id: The module to create the session in (default 1)
            
        Returns:
            Session object if successful, None if user doesn't exist
            
        Raises:
            ValueError: If user_id is invalid
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Deactivate any existing active sessions for this user in this module
        Session.query.filter_by(user_id=user_id, module_id=module_id, is_active=True).update({'is_active': False})
        
        # Create new session with UUID
        session = Session(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            module_id=module_id,
            answered_question_ids=[],
            current_difficulty_level=2,  # Starting difficulty
            current_performance_score=0.0,
            current_question_id=None,
            is_drill_mode=False,
            drill_mode_topics=[],
            is_active=True
        )
        
        db.session.add(session)
        db.session.commit()
        
        return session
    
    @staticmethod
    def save_session_state(session_id: str, state: Dict[str, Any]) -> bool:
        """
        Save session state to database with retry logic.
        
        Attempts to save the session state up to 3 times before failing.
        Updates the session's updated_at timestamp on successful save.
        
        Args:
            session_id: The UUID of the session to save
            state: Dictionary containing session state fields to update
                   Valid keys: answered_question_ids, current_difficulty_level,
                              current_performance_score, current_question_id,
                              is_drill_mode, drill_mode_topics
            
        Returns:
            True if save successful, False after 3 failed attempts
            
        Raises:
            ValueError: If session_id is invalid or state is empty
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")
        
        if not state or not isinstance(state, dict):
            raise ValueError("state must be a non-empty dictionary")
        
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                session = Session.query.get(session_id)
                if not session:
                    return False
                
                # Update session fields from state dictionary
                valid_fields = {
                    'answered_question_ids',
                    'current_difficulty_level',
                    'current_performance_score',
                    'current_question_id',
                    'is_drill_mode',
                    'drill_mode_topics'
                }
                
                for key, value in state.items():
                    if key in valid_fields:
                        setattr(session, key, value)
                
                # Update timestamp
                session.updated_at = datetime.utcnow()
                
                db.session.commit()
                return True
                
            except Exception as e:
                attempt += 1
                db.session.rollback()
                
                if attempt >= max_attempts:
                    # Log error (in production, use proper logging)
                    print(f"Failed to save session {session_id} after {max_attempts} attempts: {str(e)}")
                    return False
                
                # Brief delay before retry (exponential backoff)
                time.sleep(0.1 * (2 ** attempt))
        
        return False
    
    @staticmethod
    def restore_session(user_id: int, module_id: int = None) -> Optional[Session]:
        """
        Restore the most recent active session for the user, optionally scoped to a module.
        
        Args:
            user_id: The ID of the user to restore session for
            module_id: Optional module ID to scope the restore
            
        Returns:
            Session object if found, None if no active session exists
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        
        query = Session.query.filter_by(user_id=user_id, is_active=True)
        if module_id:
            query = query.filter_by(module_id=module_id)
        
        session = query.order_by(Session.updated_at.desc()).first()
        return session
    
    @staticmethod
    def clear_session(session_id: str) -> bool:
        """
        Clear session state while preserving history.
        
        Resets the session to initial state (difficulty level 2, empty answered
        questions, zero score) but preserves the session record and all
        associated question attempts for historical tracking.
        
        Args:
            session_id: The UUID of the session to clear
            
        Returns:
            True if successful, False if session not found
            
        Raises:
            ValueError: If session_id is invalid
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")
        
        try:
            session = Session.query.get(session_id)
            if not session:
                return False
            
            # Reset session state while preserving the record
            session.answered_question_ids = []
            session.current_difficulty_level = 2
            session.current_performance_score = 0.0
            session.current_question_id = None
            session.is_drill_mode = False
            session.drill_mode_topics = []
            session.updated_at = datetime.utcnow()
            
            # Note: We do NOT delete question_attempts - they are preserved for history
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Failed to clear session {session_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: The UUID of the session to retrieve
            
        Returns:
            Session object if found, None otherwise
        """
        if not session_id or not isinstance(session_id, str):
            return None
        
        return Session.query.get(session_id)
    
    @staticmethod
    def deactivate_session(session_id: str) -> bool:
        """
        Deactivate a session (mark as inactive).
        
        Args:
            session_id: The UUID of the session to deactivate
            
        Returns:
            True if successful, False if session not found
        """
        if not session_id or not isinstance(session_id, str):
            return False
        
        try:
            session = Session.query.get(session_id)
            if not session:
                return False
            
            session.is_active = False
            session.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Failed to deactivate session {session_id}: {str(e)}")
            return False
