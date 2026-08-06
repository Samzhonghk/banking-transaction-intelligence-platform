import json
import logging
from datetime import UTC, datetime
from logging.config import dictConfig

LOG_CONTEXT_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "etl_run_id",
    "risk_rule_id",
)


class JsonFormatter(logging.Formatter):
    """Format application log records as one-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert one Python log record into a JSON string."""
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field_name in LOG_CONTEXT_FIELDS:
            field_value = getattr(record, field_name, None)

            if field_value is not None:
                payload[field_name] = field_value

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_level: str = "INFO") -> None:
    """Configure process-wide logging for container workloads."""
    normalized_level = log_level.strip().upper()
    if normalized_level not in logging.getLevelNamesMapping():
        raise ValueError(f"Invalid log level: {log_level!r}")
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": normalized_level,
            },
        }
    )
