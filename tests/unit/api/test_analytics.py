from datetime import date
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


def create_analytics_test_app() -> tuple[FastAPI, Connection]:
    """Create an application with isolated settings and database dependencies."""
    application = create_app()

    settings = MagicMock(spec=Settings)
    settings.platform_api_key = SecretStr("expected-api-key")

    engine = MagicMock(spec=Engine)
    connection = MagicMock(spec=Connection)
    engine.connect.return_value.__enter__.return_value = connection

    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[get_database_engine] = lambda: engine

    return application, connection


def test_daily_summary_requires_api_key() -> None:
    """The analytics endpoint should reject unauthenticated requests."""
    application, _ = create_analytics_test_app()

    with TestClient(application) as client:
        response = client.get("/analytics/daily-summary")

    assert response.status_code == 401


def test_daily_summary_returns_filtered_paginated_response() -> None:
    """The endpoint should normalize filters and expose its page contract."""
    application, connection = create_analytics_test_app()
    query_result = [
        {
            "transaction_date": date(2026, 7, 28),
            "currency_code": "NZD",
            "transaction_count": 2,
            "active_account_count": 1,
            "total_amount": Decimal("1293.40"),
            "average_amount": Decimal("646.70"),
            "minimum_amount": Decimal("42.90"),
            "maximum_amount": Decimal("1250.50"),
        }
    ]

    with patch(
        "banking_intelligence.api.routes.analytics.fetch_daily_transaction_summaries",
        return_value=(query_result, 1),
    ) as fetch_summaries:
        with TestClient(application) as client:
            response = client.get(
                "/analytics/daily-summary"
                "?start_date=2026-07-01&end_date=2026-07-31"
                "&currency_code=nzd&limit=25&offset=5",
                headers={"X-API-Key": "expected-api-key"},
            )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "transaction_date": "2026-07-28",
                "currency_code": "NZD",
                "transaction_count": 2,
                "active_account_count": 1,
                "total_amount": "1293.40",
                "average_amount": "646.70",
                "minimum_amount": "42.90",
                "maximum_amount": "1250.50",
            }
        ],
        "total": 1,
        "limit": 25,
        "offset": 5,
    }
    fetch_summaries.assert_called_once_with(
        connection=connection,
        limit=25,
        offset=5,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
        currency_code="NZD",
    )


def test_daily_summary_rejects_reversed_date_range() -> None:
    """An invalid date range should fail before querying PostgreSQL."""
    application, _ = create_analytics_test_app()

    with patch(
        "banking_intelligence.api.routes.analytics.fetch_daily_transaction_summaries"
    ) as fetch_summaries:
        with TestClient(application) as client:
            response = client.get(
                "/analytics/daily-summary?start_date=2026-08-01&end_date=2026-07-01",
                headers={"X-API-Key": "expected-api-key"},
            )

    assert response.status_code == 422
    assert response.json()["detail"] == "start_date must not be after end_date."
    fetch_summaries.assert_not_called()
