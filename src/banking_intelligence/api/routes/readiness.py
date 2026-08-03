from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from banking_intelligence.api.dependencies import get_database_engine

router = APIRouter(tags=["health"])


class ReadinessResponse(BaseModel):
    """Response returned when the service is ready to receive traffic."""

    status: Literal["ready"]


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Check API readiness",
)
def readiness_check(
    engine: Annotated[Engine, Depends(get_database_engine)],
) -> ReadinessResponse:
    """Check whether the API can communicate with PostgreSQL."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc

    return ReadinessResponse(status="ready")
