from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from banking_intelligence.database.base import Base


class Transaction(Base):
    """Represent one validated transaction in the trusted core layer."""

    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "raw_transaction_id",
            name="uq_transactions_raw_transaction",
        ),
        UniqueConstraint(
            "account_id",
            "external_transaction_id",
            name="uq_transactions_account_external_id",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_transactions_positive_amount",
        ),
        CheckConstraint(
            "currency_code ~ '^[A-Z]{3}$'",
            name="ck_transactions_currency_code_format",
        ),
        {"schema": "core"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_transaction_id: Mapped[int] = mapped_column(
        ForeignKey(
            "ingestion.raw_transactions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey(
            "core.accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    external_transaction_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text)
    transaction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
