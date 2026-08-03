from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from banking_intelligence.api.dependencies import get_settings
from banking_intelligence.core.config import Settings

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def require_api_key(
    provided_api_key: Annotated[
        str | None,
        Security(api_key_header),
    ],
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
) -> None:
    """Reject requests that do not contain the configured API key."""
    expected_api_key = settings.platform_api_key.get_secret_value()

    if provided_api_key is None or not compare_digest(
        provided_api_key,
        expected_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
