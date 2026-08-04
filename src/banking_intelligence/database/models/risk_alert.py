from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from banking_intelligence.database.base import Base


class RiskAlert(Base):
    """Represent one investigation workflow for a matched risk result."""

    __tablename__ = "risk_alerts"
    __table_args__ = (
        UniqueConstraint(
            "transaction_risk_result_id",
            name="uq_risk_alerts_transaction_risk_result",
        ),
        CheckConstraint(
            "status IN ('open', 'investigating', 'resolved', 'dismissed')",
            name="ck_risk_alerts_status",
        ),
        CheckConstraint(
            "resolution_outcome IS NULL OR resolution_outcome "
            "IN ('confirmed_risk', 'false_positive', 'no_action')",
            name="ck_risk_alerts_resolution_outcome",
        ),
        CheckConstraint(
            "((status IN ('open', 'investigating') AND resolved_at IS NULL) OR "
            "(status IN ('resolved', 'dismissed') AND resolved_at IS NOT NULL))",
            name="ck_risk_alerts_resolution_timestamp",
        ),
        {"schema": "risk"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_risk_result_id: Mapped[int] = mapped_column(
        ForeignKey(
            "risk.transaction_risk_results.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        server_default="open",
        index=True,
    )
    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
    )
    resolution_outcome: Mapped[str | None] = mapped_column(String(30))
    resolution_note: Mapped[str | None] = mapped_column(Text)
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
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
