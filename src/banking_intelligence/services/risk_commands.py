from sqlalchemy import func, select, update
from sqlalchemy.engine import Connection, RowMapping

from banking_intelligence.database.models import RiskAlert
from banking_intelligence.risk.workflows.alerts import validate_alert_transition


def transition_risk_alert(
    connection: Connection,
    alert_id: int,
    target_status: str,
    assigned_to: str | None = None,
    resolution_outcome: str | None = None,
    resolution_note: str | None = None,
) -> RowMapping | None:
    """Transition one risk alert and return its updated database record."""
    current_status = connection.execute(
        select(RiskAlert.status).where(RiskAlert.id == alert_id).with_for_update()
    ).scalar_one_or_none()

    if current_status is None:
        return None

    validate_alert_transition(
        current_status=current_status,
        target_status=target_status,
    )

    update_values: dict[str, object] = {
        "status": target_status,
        "assigned_to": assigned_to,
        "resolution_outcome": resolution_outcome,
        "resolution_note": resolution_note,
        "updated_at": func.now(),
        "resolved_at": (
            func.now() if target_status in {"resolved", "dismissed"} else None
        ),
    }

    statement = (
        update(RiskAlert)
        .where(RiskAlert.id == alert_id)
        .values(**update_values)
        .returning(
            RiskAlert.id.label("alert_id"),
            RiskAlert.status,
            RiskAlert.assigned_to,
            RiskAlert.resolution_outcome,
            RiskAlert.resolution_note,
            RiskAlert.updated_at,
            RiskAlert.resolved_at,
        )
    )

    return connection.execute(statement).mappings().one()
