from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from banking_intelligence.database.base import Base


class Account(Base):
    """Represent a trusted banking account used by accepted transactions."""

    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint(
            "source_system_id",
            "external_account_id",
            name="uq_accounts_source_external_id",
        ),
        CheckConstraint(
            "currency_code ~ '^[A-Z]{3}$'",
            name="ck_accounts_currency_code_format",
        ),
        CheckConstraint(
            "status IS NULL OR status IN ('active', 'frozen', 'closed')",
            name="ck_accounts_status",
        ),
        {"schema": "core"},
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
    external_account_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    account_type: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str | None] = mapped_column(String(20))
    opened_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
