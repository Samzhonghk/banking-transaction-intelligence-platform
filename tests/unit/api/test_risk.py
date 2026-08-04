from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.engine import Connection, Engine

from banking_intelligence.api.app import create_app
from banking_intelligence.api.dependencies import (
    get_database_engine,
    get_settings,
)
from banking_intelligence.core.config import Settings


def create_risk_test_app() -> tuple[FastAPI, Connection]:
    """Create an application with isolated risk-route dependencies."""
    application = create_app()
    settings = MagicMock(spec=Settings)
    settings.platform_api_key = SecretStr("expected-api-key")

    engine = MagicMock(spec=Engine)
    connection = MagicMock(spec=Connection)
    engine.connect.return_value.__enter__.return_value = connection
    engine.begin.return_value.__enter__.return_value = connection

    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[get_database_engine] = lambda: engine
    return application, connection


def test_list_risk_alerts_requires_api_key() -> None:
    """The investigation queue should reject unauthenticated requests."""
    application, _ = create_risk_test_app()

    with TestClient(application) as client:
        response = client.get("/risk/alerts")

    assert response.status_code == 401


def test_list_risk_alerts_returns_filtered_paginated_response() -> None:
    """The endpoint should expose joined risk context and page metadata."""
    application, connection = create_risk_test_app()
    timestamp = datetime(2026, 8, 4, 10, 0, tzinfo=UTC)
    query_result = [
        {
            "alert_id": 301,
            "status": "open",
            "assigned_to": None,
            "created_at": timestamp,
            "risk_result_id": 201,
            "risk_score": Decimal("87.50"),
            "evidence": {"threshold": "1000.00"},
            "transaction_id": 101,
            "external_transaction_id": "TX-RISK-001",
            "amount": Decimal("1750.00"),
            "currency_code": "NZD",
            "transaction_timestamp": timestamp,
            "risk_rule_id": 9,
            "rule_code": "HIGH_AMOUNT_DEMO",
            "rule_name": "High amount demo rule",
            "rule_version": 1,
            "severity": "high",
        }
    ]

    with patch(
        "banking_intelligence.api.routes.risk.fetch_risk_alerts",
        return_value=(query_result, 1),
    ) as fetch_alerts:
        with TestClient(application) as client:
            response = client.get(
                "/risk/alerts?status=open&severity=high"
                "&min_score=75.00&limit=25&offset=5",
                headers={"X-API-Key": "expected-api-key"},
            )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "alert_id": 301,
                "status": "open",
                "assigned_to": None,
                "created_at": "2026-08-04T10:00:00Z",
                "risk_result_id": 201,
                "risk_score": "87.50",
                "evidence": {"threshold": "1000.00"},
                "transaction_id": 101,
                "external_transaction_id": "TX-RISK-001",
                "amount": "1750.00",
                "currency_code": "NZD",
                "transaction_timestamp": "2026-08-04T10:00:00Z",
                "risk_rule_id": 9,
                "rule_code": "HIGH_AMOUNT_DEMO",
                "rule_name": "High amount demo rule",
                "rule_version": 1,
                "severity": "high",
            }
        ],
        "total": 1,
        "limit": 25,
        "offset": 5,
    }
    fetch_alerts.assert_called_once_with(
        connection=connection,
        limit=25,
        offset=5,
        alert_status="open",
        severity="high",
        min_score=Decimal("75.00"),
    )


def test_list_risk_alerts_rejects_invalid_filters() -> None:
    """Invalid enums and score bounds should fail before querying PostgreSQL."""
    application, _ = create_risk_test_app()

    with patch("banking_intelligence.api.routes.risk.fetch_risk_alerts") as fetch:
        with TestClient(application) as client:
            response = client.get(
                "/risk/alerts?status=unknown&min_score=101",
                headers={"X-API-Key": "expected-api-key"},
            )

    assert response.status_code == 422
    fetch.assert_not_called()


def test_transition_risk_alert_requires_api_key() -> None:
    application, _ = create_risk_test_app()

    with TestClient(application) as client:
        response = client.patch(
            "/risk/alerts/301",
            json={"status": "investigating", "assigned_to": "analyst"},
        )

    assert response.status_code == 401


def test_transition_risk_alert_returns_updated_workflow_state() -> None:
    application, connection = create_risk_test_app()
    timestamp = datetime(2026, 8, 5, 10, 0, tzinfo=UTC)
    updated_alert = {
        "alert_id": 301,
        "status": "investigating",
        "assigned_to": "analyst@example.com",
        "resolution_outcome": None,
        "resolution_note": None,
        "updated_at": timestamp,
        "resolved_at": None,
    }

    with patch(
        "banking_intelligence.api.routes.risk.transition_risk_alert",
        return_value=updated_alert,
    ) as transition:
        with TestClient(application) as client:
            response = client.patch(
                "/risk/alerts/301",
                headers={"X-API-Key": "expected-api-key"},
                json={
                    "status": "investigating",
                    "assigned_to": "analyst@example.com",
                },
            )

    assert response.status_code == 200
    assert response.json() == {
        "alert_id": 301,
        "status": "investigating",
        "assigned_to": "analyst@example.com",
        "resolution_outcome": None,
        "resolution_note": None,
        "updated_at": "2026-08-05T10:00:00Z",
        "resolved_at": None,
    }
    transition.assert_called_once_with(
        connection=connection,
        alert_id=301,
        target_status="investigating",
        assigned_to="analyst@example.com",
        resolution_outcome=None,
        resolution_note=None,
    )


def test_transition_risk_alert_returns_not_found() -> None:
    application, _ = create_risk_test_app()

    with patch(
        "banking_intelligence.api.routes.risk.transition_risk_alert",
        return_value=None,
    ):
        with TestClient(application) as client:
            response = client.patch(
                "/risk/alerts/404",
                headers={"X-API-Key": "expected-api-key"},
                json={"status": "investigating", "assigned_to": "analyst"},
            )

    assert response.status_code == 404
    assert response.json() == {"detail": "Risk alert not found"}


def test_transition_risk_alert_returns_conflict() -> None:
    application, _ = create_risk_test_app()

    with patch(
        "banking_intelligence.api.routes.risk.transition_risk_alert",
        side_effect=ValueError(
            "Cannot transition risk alert from 'resolved' to 'open'."
        ),
    ):
        with TestClient(application) as client:
            response = client.patch(
                "/risk/alerts/301",
                headers={"X-API-Key": "expected-api-key"},
                json={"status": "open"},
            )

    assert response.status_code == 409
    assert "Cannot transition risk alert" in response.json()["detail"]


def test_transition_risk_alert_rejects_incomplete_workflow_fields() -> None:
    application, _ = create_risk_test_app()

    with patch(
        "banking_intelligence.api.routes.risk.transition_risk_alert"
    ) as transition:
        with TestClient(application) as client:
            response = client.patch(
                "/risk/alerts/301",
                headers={"X-API-Key": "expected-api-key"},
                json={"status": "resolved"},
            )

    assert response.status_code == 422
    transition.assert_not_called()
