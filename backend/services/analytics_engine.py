"""
Analytics Engine service for performance tracking and weak area identification.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy import func, and_
from extensions import db
from models.question_attempt import QuestionAttempt
from models.user_profile import UserProfile
from models.session import Session
from models.question import Question


class AnalyticsEngine:
    """
    Analytics Engine service for calculating performance scores and identifying weak areas.
    
    Methods:
        calculate_performance_score: Calculate session performance as (correct/total) × 100
        calculate_topic_score: Calculate topic-specific performance for a user
        identify_weak_areas: Identify topics with <70% performance and ≥5 attempts
        update_user_profile: Update user profile metrics after question attempt
        get_session_history: Retrieve recent session data for a user
    """
    
    def calculate_performance_score(self, session_id: str) -> float:
        """
        Calculate performance score for a session.
        
        Args:
            session_id: The session ID to calculate score for
        
        Returns:
            Performance score as percentage (0.0-100.0) rounded to 1 decimal place
        
        Requirements: 5.1
        """
        # Query all attempts for this session
        attempts = QuestionAttempt.query.filter_by(session_id=session_id).all()
        
        if not attempts:
            return 0.0
        
        total = len(attempts)
        correct = sum(1 for attempt in attempts if attempt.is_correct)
        
        score = (correct / total) * 100
        return round(score, 1)
    
    def calculate_topic_score(self, user_id: int, topic_area: str) -> Tuple[float, int, int]:
        """
        Calculate topic-specific performance for a user.
        
        Args:
            user_id: The user ID
            topic_area: The topic area to calculate score for
        
        Returns:
            Tuple of (score, correct_count, total_count)
            Score is percentage (0.0-100.0) rounded to 1 decimal place
        
        Requirements: 5.5
        """
        # Query all attempts for this user and topic
        attempts = db.session.query(QuestionAttempt).join(
            Question, QuestionAttempt.question_id == Question.question_id
        ).filter(
            and_(
                QuestionAttempt.user_id == user_id,
                Question.topic_area == topic_area
            )
        ).all()
        
        if not attempts:
            return 0.0, 0, 0
        
        total = len(attempts)
        correct = sum(1 for attempt in attempts if attempt.is_correct)
        
        score = (correct / total) * 100
        return round(score, 1), correct, total
    
    def identify_weak_areas(self, user_id: int) -> List[Dict]:
        """
        Identify topics needing improvement.
        
        Args:
            user_id: The user ID
        
        Returns:
            List of weak areas with topic, score, and attempt count
            Format: [{"topic": str, "score": float, "attempt_count": int}]
            Only includes topics with <70% score and ≥5 attempts
        
        Requirements: 5.6, 6.2
        """
        # Get all unique topics the user has attempted
        topics = db.session.query(Question.topic_area).join(
            QuestionAttempt, Question.question_id == QuestionAttempt.question_id
        ).filter(
            QuestionAttempt.user_id == user_id
        ).distinct().all()
        
        weak_areas = []
        
        for (topic,) in topics:
            score, correct, total = self.calculate_topic_score(user_id, topic)
            
            # Check if this is a weak area: <70% score and ≥5 attempts
            if total >= 5 and score < 70.0:
                weak_areas.append({
                    'topic': topic,
                    'score': score,
                    'attempt_count': total,
                    'correct_count': correct
                })
        
        # Sort by score (lowest first) for prioritization
        weak_areas.sort(key=lambda x: x['score'])
        
        return weak_areas
    
    def update_user_profile(self, user_id: int, question_attempt: QuestionAttempt) -> UserProfile:
        """
        Update user profile metrics after a question attempt.
        
        Args:
            user_id: The user ID
            question_attempt: The question attempt that was just completed
        
        Returns:
            Updated UserProfile object
        
        Requirements: 5.7
        """
        from sqlalchemy.orm.attributes import flag_modified
        
        # Get or create user profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
        
        # Get the question to find its topic
        question = Question.query.get(question_attempt.question_id)
        
        if not question:
            # If question not found, just update total count
            profile.total_questions_answered += 1
            profile.last_updated = datetime.utcnow()
            db.session.commit()
            return profile
        
        # Update total questions answered
        profile.total_questions_answered += 1
        
        # Update topic scores
        topic_scores = profile.topic_scores or {}
        topic = question.topic_area
        
        if topic not in topic_scores:
            topic_scores[topic] = {'correct': 0, 'total': 0, 'score': 0.0}
        
        topic_scores[topic]['total'] += 1
        if question_attempt.is_correct:
            topic_scores[topic]['correct'] += 1
        
        # Recalculate topic score
        correct = topic_scores[topic]['correct']
        total = topic_scores[topic]['total']
        topic_scores[topic]['score'] = round((correct / total) * 100, 1)
        
        profile.topic_scores = topic_scores
        flag_modified(profile, 'topic_scores')  # Mark JSON field as modified
        
        # Recalculate overall performance score
        all_attempts = QuestionAttempt.query.filter_by(user_id=user_id).all()
        if all_attempts:
            total_correct = sum(1 for a in all_attempts if a.is_correct)
            total_attempts = len(all_attempts)
            profile.overall_performance_score = round((total_correct / total_attempts) * 100, 1)
        
        # Update weak areas
        profile.weak_areas = self.identify_weak_areas(user_id)
        flag_modified(profile, 'weak_areas')  # Mark JSON field as modified
        
        # Update timestamp
        profile.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return profile
    
    def get_session_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """
        Retrieve recent session data for a user.
        
        Args:
            user_id: The user ID
            limit: Maximum number of sessions to retrieve (default 20)
        
        Returns:
            List of session dictionaries with date, score, and question count
            Format: [{"session_id": str, "date": str, "score": float, "questions_answered": int}]
            Ordered by most recent first
        
        Requirements: 5.8
        """
        # Query recent sessions for this user
        sessions = Session.query.filter_by(user_id=user_id).order_by(
            Session.created_at.desc()
        ).limit(limit).all()
        
        history = []
        
        for session in sessions:
            # Count attempts in this session
            attempt_count = QuestionAttempt.query.filter_by(session_id=session.session_id).count()
            
            # Calculate session score
            score = self.calculate_performance_score(session.session_id)
            
            history.append({
                'session_id': session.session_id,
                'date': session.created_at.isoformat() if session.created_at else None,
                'score': score,
                'questions_answered': attempt_count,
                'is_drill_mode': session.is_drill_mode,
                'is_active': session.is_active
            })
        
        return history
    
    def get_user_analytics(self, user_id: int) -> Dict:
        """
        Get comprehensive analytics for a user.
        
        Args:
            user_id: The user ID
        
        Returns:
            Dictionary with overall stats, topic breakdown, weak areas, and session history
        
        Requirements: 5.1-5.10
        """
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            # Create default profile if none exists
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            db.session.commit()
        
        # Get session history
        history = self.get_session_history(user_id)
        
        return {
            'overall_performance_score': profile.overall_performance_score,
            'total_questions_answered': profile.total_questions_answered,
            'topic_scores': profile.topic_scores or {},
            'weak_areas': profile.weak_areas or [],
            'session_history': history,
            'last_updated': profile.last_updated.isoformat() if profile.last_updated else None
        }
