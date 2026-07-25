from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from banking_intelligence.database.base import Base


class RejectedRecord(Base):
    """Record the validation failures associated with one raw transaction."""

    __tablename__ = "rejected_records"
    __table_args__ = (
        CheckConstraint(
            "jsonb_array_length(rejection_reasons) > 0",
            name="ck_rejected_records_has_reasons",
        ),
        UniqueConstraint(
            "raw_transaction_id",
            name="uq_rejected_records_raw_transaction",
        ),
        {"schema": "ingestion"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_transaction_id: Mapped[int] = mapped_column(
        ForeignKey(
            "ingestion.raw_transactions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    rejection_reasons: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
    )

    rejected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
