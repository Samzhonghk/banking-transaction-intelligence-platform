from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from banking_intelligence.api.security import require_api_key
from banking_intelligence.core.config import Settings


def protected_endpoint() -> dict[str, str]:
    """Provide a test-only endpoint protected by API-key authentication."""

    return {"status": "allowed"}


def create_security_test_app() -> FastAPI:
    """Create an isolated application for API-key tests."""

    application = FastAPI()
    application.state.settings = Settings(
        _env_file=None,
        postgres_db="test_database",
        postgres_user="test_user",
        postgres_password="test_password",
        platform_api_key="expected-api-key",
    )
    application.get(
        "/protected",
        dependencies=[Depends(require_api_key)],
    )(protected_endpoint)

    return application


def test_api_key_authentication_rejects_missing_key() -> None:
    """A protected endpoint should reject requests without an API key."""

    client = TestClient(create_security_test_app())
    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key.",
    }
    assert response.headers["www-authenticate"] == "ApiKey"


def test_api_key_authentication_rejects_invalid_key() -> None:
    """A protected endpoint should reject an incorrect API key."""

    client = TestClient(create_security_test_app())
    response = client.get(
        "/protected",
        headers={"X-API-Key": "incorrect-api-key"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key.",
    }


def test_api_key_authentication_accepts_valid_key() -> None:
    """A protected endpoint should accept the configured API key."""
    client = TestClient(create_security_test_app())
    response = client.get(
        "/protected",
        headers={"X-API-Key": "expected-api-key"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "allowed"}
