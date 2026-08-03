from sqlalchemy.engine import Engine

from banking_intelligence.core.config import Settings
from banking_intelligence.database.engine import create_database_engine


def test_create_database_engine_uses_settings() -> None:
    """Database engine should use the URL built from application settings."""
    settings = Settings(
        _env_file=None,
        postgres_db="test_database",
        postgres_user="test_user",
        postgres_password="test_password",
        postgres_host="test_host",
        postgres_port=6543,
        platform_api_key="test-platform-api-key",
    )

    engine = create_database_engine(settings)

    try:
        assert isinstance(engine, Engine)
        assert engine.url == settings.database_url
    finally:
        engine.dispose()
