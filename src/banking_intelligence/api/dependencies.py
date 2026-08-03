from fastapi import Request
from sqlalchemy.engine import Engine

from banking_intelligence.core.config import Settings


def get_database_engine(request: Request) -> Engine:
    """Return the database engine owned by the FastAPI application."""

    return request.app.state.database_engine


def get_settings(request: Request) -> Settings:
    """Return the settings owned by the FastAPI application."""
    return request.app.state.settings
