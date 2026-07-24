from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from banking_intelligence.database.base import Base


class RawTransaction(Base):
    """Preserve one source transaction record received by an ETL run."""

    __tablename__ = "raw_transactions"
    __table_args__ = (
        CheckConstraint(
            "source_row_number > 0",
            name="ck_raw_transactions_positive_source_row_number",
        ),
        UniqueConstraint(
            "etl_run_id",
            "source_row_number",
            name="uq_raw_transactions_run_source_row",
        ),
        {"schema": "ingestion"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    etl_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion.etl_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_row_number: Mapped[int] = mapped_column(nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    record_fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
