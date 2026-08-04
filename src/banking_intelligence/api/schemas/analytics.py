from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DailyTransactionSummaryResponse(BaseModel):
    """Public daily transaction metrics for one currency."""

    transaction_date: date
    currency_code: str
    transaction_count: int
    active_account_count: int
    total_amount: Decimal
    average_amount: Decimal
    minimum_amount: Decimal
    maximum_amount: Decimal


class DailyTransactionSummaryListResponse(BaseModel):
    """Paginated collection of daily transaction metrics."""

    items: list[DailyTransactionSummaryResponse]
    total: int
    limit: int
    offset: int
