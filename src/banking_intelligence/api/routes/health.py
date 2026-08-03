from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Represent the API liveness response."""

    status: Literal["ok"]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API liveness",
)
def health_check() -> HealthResponse:
    """Return the API process liveness status."""
    return HealthResponse(status="ok")
