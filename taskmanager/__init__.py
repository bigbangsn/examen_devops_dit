from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from taskmanager.session_utils import regenerate_session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import logging
from logging.handlers import RotatingFileHandler
import os
import time
from datetime import datetime, timedelta

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
talisman = Talisman()

def create_app(config_name='development'):
    """
    Application factory function that creates and configures the Flask application.

    Args:
        config_name (str): The configuration to use (development, testing, production)

    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Load configuration based on environment
    if config_name == 'development':
        app.config.from_object('taskmanager.config.DevelopmentConfig')
    elif config_name == 'testing':
        app.config.from_object('taskmanager.config.TestingConfig')
    elif config_name == 'production':
        app.config.from_object('taskmanager.config.ProductionConfig')
    else:
        app.config.from_object('taskmanager.config.DevelopmentConfig')

    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Configure security headers with Talisman
    csp = {
        'default-src': ['\'self\''],
        'script-src': ['\'self\'', '\'unsafe-inline\'', 'cdn.jsdelivr.net'],
        'style-src': ['\'self\'', '\'unsafe-inline\'', 'fonts.googleapis.com', 'cdn.jsdelivr.net'],
        'font-src': ['\'self\'', 'fonts.gstatic.com', 'cdn.jsdelivr.net'],
        'img-src': ['\'self\'', 'data:'],
        'frame-ancestors': ['\'none\'']
    }

    talisman.init_app(
        app,
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        feature_policy={
            'geolocation': '\'none\'',
            'camera': '\'none\'',
            'microphone': '\'none\'',
            'payment': '\'none\''
        },
        force_https=app.config.get('FORCE_HTTPS', False),  # Only force HTTPS in production
        session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', False),
        strict_transport_security=True,
        strict_transport_security_preload=True,
        referrer_policy='strict-origin-when-cross-origin'
    )

    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/taskmanager.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('TaskManager startup')

    # Session validation middleware
    @app.before_request
    def validate_session():
        """Check if session is valid and not expired."""
        # Skip for static files and login/register routes
        if request.path.startswith('/static') or \
           request.endpoint in ['auth.connexion', 'auth.enregistrer', None]:
            return

        # Check if user is logged in
        if 'personne_id' in session:
            # Check if session has a login time
            if 'login_time' not in session:
                # For existing sessions without login_time, add it now
                session['login_time'] = datetime.utcnow().timestamp()

            # Check if session has expired
            login_time = session.get('login_time')
            if login_time:
                # Get session lifetime from config (default 30 minutes)
                lifetime = app.config.get('PERMANENT_SESSION_LIFETIME', 1800)
                current_time = datetime.utcnow().timestamp()

                # If session has expired, log out the user
                if current_time - login_time > lifetime:
                    app.logger.info(f"Session expired for user {session.get('personne_id')}")
                    session.clear()
                    flash("Votre session a expiré. Veuillez vous reconnecter.", "warning")
                    return redirect(url_for('auth.connexion'))

                # Periodically regenerate session ID for long-lived sessions
                if current_time - login_time > 600:  # Every 10 minutes
                    regenerate_session()
                    session['login_time'] = current_time

    # Register blueprints
    from taskmanager.auth import auth_bp
    from taskmanager.tasks import tasks_bp
    from taskmanager.categories import categories_bp
    from taskmanager.users import users_bp
    from taskmanager.health import health_bp
    from taskmanager.models import Personne

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(health_bp)

    # Add context processor to make current_user available in templates
    @app.context_processor
    def inject_current_user():
        """Make current_user available in templates."""
        class UserWrapper:
            """Wrapper class to provide Flask-Login like interface."""
            def __init__(self, user=None):
                self.user = user
                self.is_authenticated = user is not None

            def __getattr__(self, name):
                if self.user is None:
                    return None
                return getattr(self.user, name)

        if 'personne_id' in session:
            user = Personne.query.get(session['personne_id'])
            if user:
                return {'current_user': UserWrapper(user)}
        return {'current_user': UserWrapper()}

    # Import custom exceptions
    from taskmanager.exceptions import (
        TaskManagerException, 
        AuthenticationError, 
        AuthorizationError, 
        ResourceNotFoundError, 
        ValidationError, 
        DatabaseError
    )

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Server Error: {e}")
        return render_template('errors/500.html'), 500

    @app.errorhandler(TaskManagerException)
    def handle_task_manager_exception(e):
        app.logger.error(f"TaskManager Exception: {e.message}")
        return render_template('errors/error.html', error=e.message), 400

    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(e):
        app.logger.warning(f"Authentication Error: {e.message}")
        return render_template('errors/error.html', error=e.message), 401

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(e):
        app.logger.warning(f"Authorization Error: {e.message}")
        return render_template('errors/error.html', error=e.message), 403

    @app.errorhandler(ResourceNotFoundError)
    def handle_resource_not_found_error(e):
        app.logger.info(f"Resource Not Found: {e.message}")
        return render_template('errors/404.html', error=e.message), 404

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        app.logger.info(f"Validation Error: {e.message}")
        return render_template('errors/error.html', error=e.message), 422

    @app.errorhandler(DatabaseError)
    def handle_database_error(e):
        app.logger.error(f"Database Error: {e.message}")
        return render_template('errors/error.html', error=e.message), 500

    return app
