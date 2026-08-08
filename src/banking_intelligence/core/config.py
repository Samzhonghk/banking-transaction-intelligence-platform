from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    transaction_api_token: SecretStr | None = None
    platform_api_key: SecretStr
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        """Build the SQLAlchemy PostgreSQL connection URL."""

        connection_values = {
            "drivername": "postgresql+psycopg",
            "username": self.postgres_user,
            "password": self.postgres_password.get_secret_value(),
            "database": self.postgres_db,
        }

        if self.postgres_host.startswith("/"):
            return URL.create(
                **connection_values,
                query={
                    "host": self.postgres_host,
                    "port": str(self.postgres_port),
                },
            )

        return URL.create(
            **connection_values,
            host=self.postgres_host,
            port=self.postgres_port,
        )

    postgres_db: str
    postgres_user: str
    postgres_password: SecretStr
    postgres_host: str = "localhost"
    postgres_port: int = 5432
