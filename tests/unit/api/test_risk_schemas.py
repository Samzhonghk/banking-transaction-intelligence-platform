import pytest
from pydantic import ValidationError

from banking_intelligence.api.schemas.risk import RiskAlertTransitionRequest


def test_transition_request_requires_assignee_for_investigation() -> None:
    with pytest.raises(ValidationError, match="assigned_to is required"):
        RiskAlertTransitionRequest(status="investigating")


@pytest.mark.parametrize("status", ["resolved", "dismissed"])
def test_transition_request_requires_outcome_for_terminal_status(
    status: str,
) -> None:
    with pytest.raises(ValidationError, match="resolution_outcome is required"):
        RiskAlertTransitionRequest.model_validate({"status": status})


def test_transition_request_accepts_complete_investigation() -> None:
    request = RiskAlertTransitionRequest(
        status="investigating",
        assigned_to="analyst@example.com",
    )

    assert request.status == "investigating"
    assert request.assigned_to == "analyst@example.com"


def test_transition_request_accepts_complete_resolution() -> None:
    request = RiskAlertTransitionRequest(
        status="resolved",
        assigned_to="analyst@example.com",
        resolution_outcome="confirmed_risk",
        resolution_note="Customer confirmed fraud.",
    )

    assert request.status == "resolved"
    assert request.resolution_outcome == "confirmed_risk"
