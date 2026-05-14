"""
Flask application factory for AWS Cloud Practitioner Exam Practice Application.
"""
from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db, login_manager


def create_app(config_class=Config):
    """
    Create and configure the Flask application.
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.session_protection = 'strong'
    login_manager.login_view = None  # API doesn't redirect, returns 401
    
    # Configure user_loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.session import session_bp
    from routes.question import question_bp
    from routes.analytics import analytics_bp
    from routes.drill import drill_bp
    from routes.study import study_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(session_bp, url_prefix='/api/session')
    app.register_blueprint(question_bp, url_prefix='/api/question')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(drill_bp, url_prefix='/api/drill')
    app.register_blueprint(study_bp, url_prefix='/api/study')
    app.register_blueprint(admin_bp, url_prefix='/api/questions')
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=4201)
