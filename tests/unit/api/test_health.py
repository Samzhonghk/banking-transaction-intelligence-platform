from fastapi.testclient import TestClient

from banking_intelligence.api.app import create_app


def test_health_check_returns_ok() -> None:
    """The liveness endpoint should return the documented response."""
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
