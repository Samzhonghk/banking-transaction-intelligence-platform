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


def create_transaction_test_app() -> tuple[FastAPI, Connection]:
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


def test_list_transactions_requires_api_key() -> None:
    """The transaction collection should reject unauthenticated requests."""
    application, _ = create_transaction_test_app()

    with TestClient(application) as client:
        response = client.get("/transactions")

    assert response.status_code == 401


def test_list_transactions_returns_paginated_response() -> None:
    """The transaction collection should expose its documented page contract."""
    application, connection = create_transaction_test_app()
    transaction_timestamp = datetime(2026, 7, 28, 10, 15, tzinfo=UTC)
    query_result = [
        {
            "id": 10,
            "account_id": 20,
            "external_transaction_id": "TX-001",
            "amount": Decimal("100.50"),
            "currency_code": "NZD",
            "description": "Test payment",
            "transaction_timestamp": transaction_timestamp,
        }
    ]

    with patch(
        "banking_intelligence.api.routes.transactions.fetch_transactions",
        return_value=(query_result, 1),
    ) as fetch_transactions:
        with TestClient(application) as client:
            response = client.get(
                "/transactions?limit=25&offset=5",
                headers={"X-API-Key": "expected-api-key"},
            )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 10,
                "account_id": 20,
                "external_transaction_id": "TX-001",
                "amount": "100.50",
                "currency_code": "NZD",
                "description": "Test payment",
                "transaction_timestamp": "2026-07-28T10:15:00Z",
            }
        ],
        "total": 1,
        "limit": 25,
        "offset": 5,
    }
    fetch_transactions.assert_called_once_with(
        connection=connection,
        limit=25,
        offset=5,
    )
