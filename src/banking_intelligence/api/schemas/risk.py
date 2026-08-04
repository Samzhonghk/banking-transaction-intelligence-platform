from datetime import datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

AlertStatus = Literal["open", "investigating", "resolved", "dismissed"]
RiskSeverity = Literal["low", "medium", "high", "critical"]
ResolutionOutcome = Literal[
    "confirmed_risk",
    "false_positive",
    "no_action",
]


class RiskAlertResponse(BaseModel):
    """Public representation of one transaction investigation alert."""

    alert_id: int
    status: AlertStatus
    assigned_to: str | None
    created_at: datetime

    risk_result_id: int
    risk_score: Decimal
    evidence: dict[str, object]

    transaction_id: int
    external_transaction_id: str
    amount: Decimal
    currency_code: str
    transaction_timestamp: datetime

    risk_rule_id: int
    rule_code: str
    rule_name: str
    rule_version: int
    severity: RiskSeverity


class RiskAlertListResponse(BaseModel):
    """Paginated collection of transaction investigation alerts."""

    items: list[RiskAlertResponse]
    total: int
    limit: int
    offset: int


class RiskAlertTransitionRequest(BaseModel):
    """Requested investigation workflow change for one risk alert."""

    status: AlertStatus
    assigned_to: str | None = Field(
        default=None,
        max_length=100,
    )

    resolution_outcome: ResolutionOutcome | None = None
    resolution_note: str | None = Field(
        default=None,
        max_length=2000,
    )

    @model_validator(mode="after")
    def validate_required_workflow_fields(self) -> Self:
        """Validate fields required by the requested workflow state."""

        if self.status == "investigating" and (
            self.assigned_to is None or not self.assigned_to.strip()
        ):
            raise ValueError("assigned_to is required when investigating an alert.")

        if self.status in {"resolved", "dismissed"} and self.resolution_outcome is None:
            raise ValueError("resolution_outcome is required for a terminal alert.")

        return self


class RiskAlertTransitionResponse(BaseModel):
    """Updated investigation workflow state returned to an API caller."""

    alert_id: int
    status: AlertStatus
    assigned_to: str | None
    resolution_outcome: ResolutionOutcome | None
    resolution_note: str | None
    updated_at: datetime
    resolved_at: datetime | None
