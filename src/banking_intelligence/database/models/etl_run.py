from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from banking_intelligence.database.base import Base


class EtlRun(Base):
    """Represent one execution of an ingestion pipeline."""

    __tablename__ = "etl_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed')",
            name="ck_etl_runs_status",
        ),
        CheckConstraint(
            "extracted_count >= 0 AND accepted_count >= 0 AND rejected_count >= 0",
            name="ck_etl_runs_non_negative_counts",
        ),
        {"schema": "ingestion"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_system_id: Mapped[int] = mapped_column(
        ForeignKey(
            "ingestion.source_systems.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    pipeline_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    extracted_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    accepted_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    rejected_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    error_message: Mapped[str | None] = mapped_column(Text)
