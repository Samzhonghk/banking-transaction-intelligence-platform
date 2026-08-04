ALLOWED_ALERT_TRANSITIONS = {
    "open": frozenset({"investigating", "dismissed"}),
    "investigating": frozenset({"resolved", "dismissed"}),
    "resolved": frozenset(),
    "dismissed": frozenset(),
}


def validate_alert_transition(
    current_status: str,
    target_status: str,
) -> None:
    """Reject an invalid investigation workflow transition."""
    if (
        current_status not in ALLOWED_ALERT_TRANSITIONS
        or target_status not in ALLOWED_ALERT_TRANSITIONS
    ):
        raise ValueError(
            f"Cannot transition risk alert from "
            f"{current_status!r} to {target_status!r}."
        )

    if current_status == target_status:
        return

    allowed_targets = ALLOWED_ALERT_TRANSITIONS[current_status]

    if target_status not in allowed_targets:
        raise ValueError(
            f"Cannot transition risk alert from "
            f"{current_status!r} to {target_status!r}."
        )
