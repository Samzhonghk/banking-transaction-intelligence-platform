from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.engine import Engine

from banking_intelligence.api.dependencies import get_database_engine
from banking_intelligence.api.schemas.analytics import (
    DailyTransactionSummaryListResponse,
)
from banking_intelligence.api.security import require_api_key
from banking_intelligence.services.analytics_queries import (
    fetch_daily_transaction_summaries,
)

router = APIRouter(
    prefix="/analytics", tags=["analytics"], dependencies=[Depends(require_api_key)]
)


@router.get(
    "/daily-summary",
    response_model=DailyTransactionSummaryListResponse,
    summary="List daily transaction metrics",
)
def list_daily_transaction_summaries(
    engine: Annotated[Engine, Depends(get_database_engine)],
    start_date: date | None = None,
    end_date: date | None = None,
    currency_code: Annotated[
        str | None,
        Query(pattern=r"^[A-Za-z]{3}$"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DailyTransactionSummaryListResponse:
    """Return one authenticated page of daily analytical metrics."""
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="start_date must not be after end_date.",
        )

    normalised_currency = currency_code.upper() if currency_code is not None else None

    with engine.connect() as conn:
        items, total = fetch_daily_transaction_summaries(
            connection=conn,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            currency_code=normalised_currency,
        )

    return DailyTransactionSummaryListResponse(
        items=list(items),
        total=total,
        limit=limit,
        offset=offset,
    )
