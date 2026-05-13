"""
Authentication service for user registration, login, and session management.
"""
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.exc import IntegrityError
from extensions import db
from models.user import User


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class RateLimitError(AuthenticationError):
    """Exception raised when rate limit is exceeded."""
    pass


class AuthService:
    """
    Service class for handling user authentication operations.
    
    Provides methods for:
    - User registration with password hashing
    - Login with credential verification
    - Session token management
    - Rate limiting for failed login attempts
    - Logout with session invalidation
    """
    
    # Session token storage (in-memory for now, should use Redis in production)
    _session_tokens: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password as a string
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    
    @staticmethod
    def generate_session_token() -> str:
        """
        Generate a secure random session token.
        
        Returns:
            Random session token string (32 bytes hex)
        """
        return secrets.token_hex(32)
    
    @classmethod
    def register_user(cls, username: str, email: str, password: str) -> Tuple[User, str]:
        """
        Register a new user account.
        
        Args:
            username: Unique username (3-30 characters)
            email: Unique email address
            password: Plain text password (will be hashed)
            
        Returns:
            Tuple of (User object, error message or None)
            
        Raises:
            ValueError: If validation fails
            IntegrityError: If username or email already exists
        """
        # Validate username length (additional validation beyond DB constraint)
        if not username or len(username) < 3 or len(username) > 30:
            raise ValueError("Username must be between 3 and 30 characters")
        
        # Validate email format (basic check)
        if not email or '@' not in email:
            raise ValueError("Invalid email format")
        
        # Validate password length
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Check username uniqueness
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            raise ValueError("Username already in use")
        
        # Check email uniqueness
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            raise ValueError("Email already in use")
        
        # Hash password
        password_hash = cls.hash_password(password)
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            failed_login_attempts=0
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return new_user, None
        except IntegrityError as e:
            db.session.rollback()
            # Handle race condition where user was created between check and insert
            if 'username' in str(e.orig):
                raise ValueError("Username already in use")
            elif 'email' in str(e.orig):
                raise ValueError("Email already in use")
            else:
                raise
    
    @classmethod
    def _check_rate_limit(cls, user: User) -> None:
        """
        Check if user has exceeded failed login attempt rate limit.
        
        Args:
            user: User object to check
            
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        # Rate limit: 5 attempts per 15-minute window
        max_attempts = 5
        window_duration = timedelta(minutes=15)
        
        # If no failed attempts, allow login
        if user.failed_login_attempts == 0:
            return
        
        # Check if we're still within the rate limit window
        if user.failed_login_window_start:
            window_end = user.failed_login_window_start + window_duration
            now = datetime.utcnow()
            
            # If window has expired, reset the counter
            if now > window_end:
                user.failed_login_attempts = 0
                user.failed_login_window_start = None
                db.session.commit()
                return
            
            # If within window and at/over limit, raise error
            if user.failed_login_attempts >= max_attempts:
                time_remaining = (window_end - now).total_seconds()
                minutes_remaining = int(time_remaining / 60) + 1
                raise RateLimitError(
                    f"Too many failed login attempts. Please try again in {minutes_remaining} minute(s)."
                )
    
    @classmethod
    def _record_failed_login(cls, user: User) -> None:
        """
        Record a failed login attempt for rate limiting.
        
        Args:
            user: User object to update
        """
        now = datetime.utcnow()
        
        # If this is the first failed attempt or window has expired, start new window
        if user.failed_login_attempts == 0 or not user.failed_login_window_start:
            user.failed_login_window_start = now
            user.failed_login_attempts = 1
        else:
            # Check if window has expired
            window_duration = timedelta(minutes=15)
            window_end = user.failed_login_window_start + window_duration
            
            if now > window_end:
                # Start new window
                user.failed_login_window_start = now
                user.failed_login_attempts = 1
            else:
                # Increment counter within existing window
                user.failed_login_attempts += 1
        
        db.session.commit()
    
    @classmethod
    def _reset_failed_login_attempts(cls, user: User) -> None:
        """
        Reset failed login attempts after successful login.
        
        Args:
            user: User object to update
        """
        user.failed_login_attempts = 0
        user.failed_login_window_start = None
        db.session.commit()
    
    @classmethod
    def login(cls, username_or_email: str, password: str) -> Tuple[Optional[str], Optional[User], Optional[str]]:
        """
        Authenticate user and create session token.
        
        Args:
            username_or_email: Username or email address
            password: Plain text password
            
        Returns:
            Tuple of (session_token, User object, error message)
            Returns (None, None, error) on failure
            Returns (token, user, None) on success
            
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        # Generic error message to avoid revealing whether username exists
        generic_error = "Invalid credentials"
        
        if not user:
            return None, None, generic_error
        
        # Check rate limit before attempting authentication
        try:
            cls._check_rate_limit(user)
        except RateLimitError as e:
            return None, None, str(e)
        
        # Verify password
        if not cls.verify_password(password, user.password_hash):
            cls._record_failed_login(user)
            return None, None, generic_error
        
        # Reset failed login attempts on successful login
        cls._reset_failed_login_attempts(user)
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate session token
        session_token = cls.generate_session_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Store session token (in-memory for now)
        cls._session_tokens[session_token] = {
            'user_id': user.user_id,
            'username': user.username,
            'expires_at': expires_at
        }
        
        return session_token, user, None
    
    @classmethod
    def validate_session_token(cls, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token and return session data.
        
        Args:
            session_token: Session token to validate
            
        Returns:
            Session data dictionary if valid, None if invalid or expired
        """
        if not session_token or session_token not in cls._session_tokens:
            return None
        
        session_data = cls._session_tokens[session_token]
        
        # Check if token has expired
        if datetime.utcnow() > session_data['expires_at']:
            # Remove expired token
            del cls._session_tokens[session_token]
            return None
        
        return session_data
    
    @classmethod
    def logout(cls, session_token: str) -> bool:
        """
        Invalidate a session token.
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if token was found and removed, False otherwise
        """
        if session_token in cls._session_tokens:
            del cls._session_tokens[session_token]
            return True
        return False
    
    @classmethod
    def get_user_by_token(cls, session_token: str) -> Optional[User]:
        """
        Get user object from session token.
        
        Args:
            session_token: Session token
            
        Returns:
            User object if token is valid, None otherwise
        """
        session_data = cls.validate_session_token(session_token)
        if not session_data:
            return None
        
        return User.query.get(session_data['user_id'])
    
    @classmethod
    def clear_all_sessions(cls) -> None:
        """
        Clear all session tokens (for testing purposes).
        """
        cls._session_tokens.clear()
