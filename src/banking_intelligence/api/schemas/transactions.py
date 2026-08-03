from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    """Public representation of one trusted transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    external_transaction_id: str
    amount: Decimal
    currency_code: str
    description: str | None
    transaction_timestamp: datetime


class TransactionListResponse(BaseModel):
    """Paginated collection of trusted transactions."""

    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
