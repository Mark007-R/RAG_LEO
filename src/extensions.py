from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()

def init_extensions(app):
    from .config import settings

    db.init_app(app)
    migrate.init_app(app, db)

    cors.init_app(
        app,
        origins=settings.get_cors_origins_list(),
        supports_credentials=True
    )
