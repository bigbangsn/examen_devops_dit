import os

class Config:
    """Base configuration class with common settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mysecret')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database connection pooling configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30))
    }

    # Add logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Session configuration
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('SESSION_LIFETIME', 1800))  # 30 minutes in seconds
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_REFRESH_EACH_REQUEST = True

    # Security configuration
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'False').lower() == 'true'

    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL', 'sqlite:///../instance/data.db')

    @classmethod
    def init_app(cls, app):
        """Initialize application with development configuration."""
        Config.init_app(app)

        # Configure logging for development
        import logging
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        app.logger.addHandler(handler)

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing

    @classmethod
    def init_app(cls, app):
        """Initialize application with testing configuration."""
        Config.init_app(app)

class ProductionConfig(Config):
    """Production configuration."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///../instance/data.db')
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        """Initialize application with production configuration."""
        Config.init_app(app)

        # Configure logging for production
        import logging
        from logging.handlers import RotatingFileHandler

        # Create logs directory if it doesn't exist
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

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
