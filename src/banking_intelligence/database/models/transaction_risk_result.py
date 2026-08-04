from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from banking_intelligence.database.base import Base


class TransactionRiskResult(Base):
    """Record one transaction evaluation against one risk-rule version."""

    __tablename__ = "transaction_risk_results"
    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            "risk_rule_id",
            name="uq_transaction_risk_results_transaction_rule",
        ),
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_transaction_risk_results_score_range",
        ),
        CheckConstraint(
            "jsonb_typeof(evidence) = 'object'",
            name="ck_transaction_risk_results_evidence_object",
        ),
        {"schema": "risk"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey(
            "core.transactions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    risk_rule_id: Mapped[int] = mapped_column(
        ForeignKey(
            "risk.risk_rules.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    matched: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    evidence: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
