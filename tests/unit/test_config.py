import pytest

from banking_intelligence.core.config import Settings


def test_settings_loads_values_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings should load and validate PostgreSQL environment variables."""

    monkeypatch.setenv("POSTGRES_DB", "test_database")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password")
    monkeypatch.setenv("POSTGRES_HOST", "test_host")
    monkeypatch.setenv("POSTGRES_PORT", "6543")

    settings = Settings(_env_file=None)

    assert settings.postgres_db == "test_database"
    assert settings.postgres_user == "test_user"
    assert settings.postgres_password.get_secret_value() == "test_password"
    assert settings.postgres_host == "test_host"
    assert settings.postgres_port == 6543


def test_database_url_contains_expected_components() -> None:
    """Database URL should contain all configured PostgreSQL components."""

    settings = Settings(
        _env_file=None,
        postgres_db="test_database",
        postgres_user="test_user",
        postgres_password="test_password",
        postgres_host="test_host",
        postgres_port=6543,
    )

    database_url = settings.database_url

    assert database_url.drivername == "postgresql+psycopg"
    assert database_url.username == "test_user"
    assert database_url.password == "test_password"
    assert database_url.host == "test_host"
    assert database_url.port == 6543
    assert database_url.database == "test_database"
