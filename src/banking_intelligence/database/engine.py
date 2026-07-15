from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from banking_intelligence.core.config import Settings


def create_database_engine(settings: Settings) -> Engine:
    """Create the application's SQLAlchemy database engine."""
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )
