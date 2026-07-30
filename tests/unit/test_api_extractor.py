from unittest.mock import Mock

import pytest
import requests

from banking_intelligence.ingestion.extractors.api import (
    RETRYABLE_STATUS_CODES,
    build_retry_session,
    extract_api_transactions,
    fetch_transaction_page,
)


def test_build_retry_session_configures_transient_get_retries() -> None:
    """The session should retry only safe GET requests and transient failures."""
    session = build_retry_session(
        total_retries=4,
        backoff_factor=1.0,
    )

    try:
        retry_strategy = session.get_adapter("https://").max_retries

        assert retry_strategy.total == 4
        assert retry_strategy.allowed_methods == frozenset({"GET"})
        assert retry_strategy.status_forcelist == RETRYABLE_STATUS_CODES
        assert retry_strategy.backoff_factor == 1.0
        assert retry_strategy.respect_retry_after_header is True
    finally:
        session.close()


def test_fetch_transaction_page_sends_pagination_and_timeout() -> None:
    """One page request should use explicit pagination and timeout values."""
    session = Mock(spec=requests.Session)
    response = Mock(spec=requests.Response)
    response.json.return_value = {
        "data": [{"transaction_id": "TX001"}],
        "pagination": {
            "page": 2,
            "total_pages": 3,
        },
    }
    session.get.return_value = response

    payload = fetch_transaction_page(
        session=session,
        url="https://example.test/transactions",
        page=2,
        page_size=50,
        timeout=(2.0, 15.0),
    )

    session.get.assert_called_once_with(
        "https://example.test/transactions",
        params={
            "page": 2,
            "page_size": 50,
        },
        timeout=(2.0, 15.0),
    )
    response.raise_for_status.assert_called_once_with()
    assert payload["data"] == [{"transaction_id": "TX001"}]


def test_fetch_transaction_page_rejects_non_object_records() -> None:
    """Every item in the API data list must be a transaction object."""
    session = Mock(spec=requests.Session)
    response = Mock(spec=requests.Response)
    response.json.return_value = {
        "data": ["not-an-object"],
        "pagination": {
            "page": 1,
            "total_pages": 1,
        },
    }
    session.get.return_value = response

    with pytest.raises(
        ValueError,
        match="Every transaction API record must be a JSON object",
    ):
        fetch_transaction_page(
            session=session,
            url="https://example.test/transactions",
            page=1,
        )


def test_extract_api_transactions_combines_every_page() -> None:
    """Paginated API records should be returned as one ordered DataFrame."""
    session = Mock(spec=requests.Session)
    first_response = Mock(spec=requests.Response)
    first_response.json.return_value = {
        "data": [{"transaction_id": "TX001"}],
        "pagination": {
            "page": 1,
            "total_pages": 2,
        },
    }
    second_response = Mock(spec=requests.Response)
    second_response.json.return_value = {
        "data": [{"transaction_id": "TX002"}],
        "pagination": {
            "page": 2,
            "total_pages": 2,
        },
    }
    session.get.side_effect = [
        first_response,
        second_response,
    ]

    dataframe = extract_api_transactions(
        url="https://example.test/transactions",
        session=session,
        page_size=25,
    )

    assert dataframe.to_dict(orient="records") == [
        {"transaction_id": "TX001"},
        {"transaction_id": "TX002"},
    ]
    assert session.get.call_count == 2


def test_extract_api_transactions_rejects_unexpected_page() -> None:
    """The extractor should reject a response for a page it did not request."""
    session = Mock(spec=requests.Session)
    response = Mock(spec=requests.Response)
    response.json.return_value = {
        "data": [{"transaction_id": "TX001"}],
        "pagination": {
            "page": 2,
            "total_pages": 2,
        },
    }
    session.get.return_value = response

    with pytest.raises(
        ValueError,
        match="unexpected page number",
    ):
        extract_api_transactions(
            url="https://example.test/transactions",
            session=session,
        )
