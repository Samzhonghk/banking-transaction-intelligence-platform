from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.engine import Engine

from banking_intelligence.api.dependencies import get_database_engine
from banking_intelligence.api.schemas.risk import (
    AlertStatus,
    RiskAlertListResponse,
    RiskAlertTransitionRequest,
    RiskAlertTransitionResponse,
    RiskSeverity,
)
from banking_intelligence.api.security import require_api_key
from banking_intelligence.services.risk_commands import transition_risk_alert
from banking_intelligence.services.risk_queries import fetch_risk_alerts

router = APIRouter(
    prefix="/risk",
    tags=["risk"],
    dependencies=[Depends(require_api_key)],
)


@router.get(
    "/alerts",
    response_model=RiskAlertListResponse,
    summary="List transaction risk alerts",
)
def list_risk_alerts(
    engine: Annotated[Engine, Depends(get_database_engine)],
    alert_status: Annotated[AlertStatus | None, Query(alias="status")] = None,
    severity: RiskSeverity | None = None,
    min_score: Annotated[Decimal | None, Query(ge=0, le=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RiskAlertListResponse:
    """Return one authenticated and filtered investigation queue page."""
    with engine.connect() as connection:
        items, total = fetch_risk_alerts(
            connection=connection,
            limit=limit,
            offset=offset,
            alert_status=alert_status,
            severity=severity,
            min_score=min_score,
        )

    return RiskAlertListResponse(
        items=list(items),
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/alerts/{alert_id}",
    response_model=RiskAlertTransitionResponse,
    summary="Transition a risk alert",
)
def transition_alert(
    alert_id: int,
    payload: RiskAlertTransitionRequest,
    engine: Annotated[Engine, Depends(get_database_engine)],
) -> RiskAlertTransitionResponse:
    """Apply one authenticated investigation workflow transition."""
    try:
        with engine.begin() as connection:
            updated_alert = transition_risk_alert(
                connection=connection,
                alert_id=alert_id,
                target_status=payload.status,
                assigned_to=payload.assigned_to,
                resolution_outcome=payload.resolution_outcome,
                resolution_note=payload.resolution_note,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if updated_alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk alert not found",
        )

    return RiskAlertTransitionResponse.model_validate(updated_alert)
