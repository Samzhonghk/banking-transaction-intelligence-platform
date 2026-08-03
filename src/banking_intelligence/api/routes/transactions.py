from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.engine import Engine

from banking_intelligence.api.dependencies import get_database_engine
from banking_intelligence.api.schemas.transactions import (
    TransactionListResponse,
)
from banking_intelligence.api.security import require_api_key
from banking_intelligence.services.transaction_queries import fetch_transactions

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
    dependencies=[Depends(require_api_key)],
)


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="Retrieve a list of transactions",
)
def list_transactions(
    engine: Annotated[
        Engine,
        Depends(get_database_engine),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TransactionListResponse:
    """Return one authenticated page of trusted transactions."""

    with engine.connect() as conn:
        items, total = fetch_transactions(
            connection=conn,
            limit=limit,
            offset=offset,
        )

    return TransactionListResponse(
        items=list(items),
        total=total,
        limit=limit,
        offset=offset,
    )
