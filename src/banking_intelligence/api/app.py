from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from banking_intelligence.api.routes.health import router as health_router
from banking_intelligence.api.routes.readiness import router as readiness_router
from banking_intelligence.api.routes.transactions import router as transactions_router
from banking_intelligence.core.config import Settings
from banking_intelligence.database.engine import create_database_engine


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Create and dispose application-owned resources."""
    settings = Settings()
    application.state.settings = settings
    database_engine = create_database_engine(settings)
    application.state.database_engine = database_engine
    try:
        yield
    finally:
        database_engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Banking Transaction Intelligence Platform",
        description=(
            "Authenticated API for trusted banking transactions "
            "and analytical insights."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(readiness_router)
    app.include_router(transactions_router)
    return app


app = create_app()
