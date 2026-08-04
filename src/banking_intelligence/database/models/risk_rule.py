from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from banking_intelligence.database.base import Base


class RiskRule(Base):
    """Represent one versioned and auditable transaction risk rule."""

    __tablename__ = "risk_rules"
    __table_args__ = (
        UniqueConstraint(
            "code",
            "version",
            name="uq_risk_rules_code_version",
        ),
        CheckConstraint(
            "version > 0",
            name="ck_risk_rules_positive_version",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_risk_rules_severity",
        ),
        CheckConstraint(
            "threshold IS NULL OR threshold > 0",
            name="ck_risk_rules_positive_threshold",
        ),
        CheckConstraint(
            "jsonb_typeof(parameters) = 'object'",
            name="ck_risk_rules_parameters_object",
        ),
        {"schema": "risk"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    parameters: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
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
