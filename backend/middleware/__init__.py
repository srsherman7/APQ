"""
Middleware package for authentication and request processing.
"""
from .auth import require_auth, optional_auth

__all__ = ['require_auth', 'optional_auth']
