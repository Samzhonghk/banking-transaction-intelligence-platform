import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Add request correlation and structured HTTP access logging."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Log one HTTP request and return its correlated response."""
        request_id = request.headers.get("X-Request-ID")

        if not request_id or len(request_id) > 128:
            request_id = str(uuid4())

        started_at = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            logger.exception(
                "http.request.failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "http.request.completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
