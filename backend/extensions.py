"""
Flask extensions initialization.
This module prevents circular imports by defining extensions separately.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
