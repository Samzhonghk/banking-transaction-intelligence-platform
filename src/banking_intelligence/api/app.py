import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from banking_intelligence.api.middleware.request_logging import RequestLoggingMiddleware
from banking_intelligence.api.routes.analytics import router as analytics_router
from banking_intelligence.api.routes.health import router as health_router
from banking_intelligence.api.routes.readiness import router as readiness_router
from banking_intelligence.api.routes.risk import router as risk_router
from banking_intelligence.api.routes.transactions import router as transactions_router
from banking_intelligence.core.config import Settings
from banking_intelligence.core.logging import configure_logging
from banking_intelligence.database.engine import create_database_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Create and dispose application-owned resources."""
    settings = Settings()
    configure_logging(settings.log_level)
    logger.info("api.startup")
    application.state.settings = settings
    database_engine = create_database_engine(settings)
    application.state.database_engine = database_engine
    try:
        yield
    finally:
        logger.info("api.shutdown")
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
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(health_router)
    app.include_router(readiness_router)
    app.include_router(transactions_router)
    app.include_router(analytics_router)
    app.include_router(risk_router)

    return app


app = create_app()
