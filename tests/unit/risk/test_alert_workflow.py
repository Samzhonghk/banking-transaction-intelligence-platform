import pytest

from banking_intelligence.risk.workflows.alerts import validate_alert_transition


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    [
        ("open", "investigating"),
        ("open", "dismissed"),
        ("investigating", "resolved"),
        ("investigating", "dismissed"),
        ("open", "open"),
        ("resolved", "resolved"),
    ],
)
def test_validate_alert_transition_accepts_allowed_transitions(
    current_status: str,
    target_status: str,
) -> None:
    validate_alert_transition(current_status, target_status)


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    [
        ("open", "resolved"),
        ("investigating", "open"),
        ("resolved", "open"),
        ("dismissed", "investigating"),
        ("unknown", "open"),
        ("unknown", "unknown"),
        ("open", "unknown"),
    ],
)
def test_validate_alert_transition_rejects_invalid_transitions(
    current_status: str,
    target_status: str,
) -> None:
    with pytest.raises(ValueError, match="Cannot transition risk alert"):
        validate_alert_transition(current_status, target_status)
