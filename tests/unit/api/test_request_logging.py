from uuid import UUID

from fastapi.testclient import TestClient

from banking_intelligence.api.app import create_app


def test_request_logging_generates_request_id() -> None:

    with TestClient(create_app()) as client:
        response = client.get("/health")
        request_id = response.headers["X-Request-ID"]
        assert response.status_code == 200
        assert UUID(request_id)


def test_request_logging_preserves_existing_request_id() -> None:
    """An upstream request ID should be returned unchanged."""
    request_id = "gateway-request-123"
    with TestClient(create_app()) as client:
        response = client.get(
            "/health",
            headers={"X-Request-ID": request_id},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
