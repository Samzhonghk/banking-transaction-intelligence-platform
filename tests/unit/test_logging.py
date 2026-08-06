import json
import logging

import pytest

from banking_intelligence.core.logging import JsonFormatter, configure_logging


def test_json_formatter_emits_structured_fields() -> None:
    record = logging.LogRecord(
        name="banking.test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="loaded %s rows",
        args=(23,),
        exc_info=None,
    )

    record.request_id = "request-123"
    record.status_code = 200
    record.secret = "must-not-be-logged"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "banking.test"
    assert payload["message"] == "loaded 23 rows"
    assert payload["timestamp"].endswith("+00:00")
    assert payload["request_id"] == "request-123"
    assert payload["status_code"] == 200
    assert "secret" not in payload


def test_configure_logging_rejects_unknown_level() -> None:
    """Unknown logging levels should fail during application startup."""
    with pytest.raises(ValueError, match="Invalid log level"):
        configure_logging("verbose")
