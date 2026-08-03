from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from banking_intelligence.api.app import create_app
from banking_intelligence.api.dependencies import get_database_engine


def test_readiness_check_returns_ready() -> None:
    """The readiness endpoint should succeed when PostgreSQL responds."""
    engine = MagicMock(spec=Engine)
    application = create_app()
    application.dependency_overrides[get_database_engine] = lambda: engine

    with TestClient(application) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    engine.connect.assert_called_once()


def test_readiness_check_returns_503_when_database_is_unavailable() -> None:
    """The readiness endpoint should fail safely when PostgreSQL is unavailable."""
    engine = MagicMock(spec=Engine)
    engine.connect.side_effect = SQLAlchemyError("internal database failure")

    app = create_app()
    app.dependency_overrides[get_database_engine] = lambda: engine

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}
    assert "internal database failure" not in response.text
