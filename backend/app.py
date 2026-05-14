"""
Flask application factory for AWS Cloud Practitioner Exam Practice Application.
"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from extensions import db, login_manager


def create_app(config_class=Config):
    """
    Create and configure the Flask application.
    """
    # Resolve the Angular production build directory
    frontend_dist = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'frontend', 'dist', 'frontend', 'browser'
    )

    app = Flask(
        __name__,
        static_folder=frontend_dist,
        static_url_path=''
    )
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.session_protection = 'strong'
    login_manager.login_view = None

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

    # Register API blueprints
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

    # Serve Angular app for all non-API routes (SPA fallback)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        # Serve the file if it exists (JS, CSS, assets, etc.)
        if path and os.path.exists(os.path.join(frontend_dist, path)):
            return send_from_directory(frontend_dist, path)
        # Fall back to index.html for all Angular client-side routes
        return send_from_directory(frontend_dist, 'index.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=4201)
