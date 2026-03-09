"""
Flask extensions initialization.
Centralizes extension setup for clean dependency management.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions (will be bound to app in create_app)
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://"
)


def init_extensions(app):
    """Initialize all Flask extensions with app instance."""
    from config import settings
    
    # Database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # CORS
    cors.init_app(
        app,
        origins=settings.get_cors_origins_list(),
        supports_credentials=True
    )
    
    # Rate limiting
    if settings.RATE_LIMIT_ENABLED:
        limiter.init_app(app)
