from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RETRYABLE_STATUS_CODES = frozenset(
    {
        429,
        500,
        502,
        503,
        504,
    }
)


def build_retry_session(
    total_retries: int = 3,
    backoff_factor: float = 0.5,
) -> requests.Session:
    """Build an HTTP session that retries transient GET failures."""
    retry_strategy = Retry(
        total=total_retries,
        connect=total_retries,
        read=total_retries,
        status=total_retries,
        allowed_methods=frozenset({"GET"}),
        status_forcelist=RETRYABLE_STATUS_CODES,
        backoff_factor=backoff_factor,
        respect_retry_after_header=True,
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def fetch_transaction_page(
    session: requests.Session,
    url: str,
    page: int,
    page_size: int = 100,
    timeout: tuple[float, float] = (3.05, 30.0),
) -> dict[str, Any]:
    """Fetch and validate one page of transaction API records."""
    response = session.get(
        url,
        params={
            "page": page,
            "page_size": page_size,
        },
        timeout=timeout,
    )

    response.raise_for_status()

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise ValueError("Transaction API returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("Transaction API response must be a JSON object")

    records = payload.get("data")
    pagination = payload.get("pagination")

    if not isinstance(records, list):
        raise ValueError("Transaction API response must contain a data list")

    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Every transaction API record must be a JSON object.")

    if not isinstance(pagination, dict):
        raise ValueError("Transaction API response must contain pagination metadata.")
    return payload


def extract_api_transactions(
    url: str,
    session: requests.Session | None = None,
    page_size: int = 100,
    timeout: tuple[float, float] = (3.05, 30.0),
    max_pages: int = 1000,
) -> pd.DataFrame:
    """Fetch every transaction API page into one DataFrame."""
    if page_size <= 0:
        raise ValueError("page size must be greater than 0")
    if max_pages <= 0:
        raise ValueError("max pages must be greater than 0")

    owns_session = session is None
    active_session = session or build_retry_session()

    records: list[dict[str, Any]] = []
    requested_page = 1

    try:
        while True:
            payload = fetch_transaction_page(
                session=active_session,
                url=url,
                page=requested_page,
                page_size=page_size,
                timeout=timeout,
            )

            pagination = payload["pagination"]
            response_page = pagination.get("page")
            total_pages = pagination.get("total_pages")

            if not isinstance(response_page, int):
                raise ValueError("pagination page must be an integer")

            if not isinstance(total_pages, int) or total_pages < 1:
                raise ValueError(
                    "pagination total page must be a positive integer number"
                )

            if response_page != requested_page:
                raise ValueError("Transaction API returned an unexpected page number.")

            if response_page > total_pages:
                raise ValueError(
                    "pagination page can not exceed pagination total pages"
                )

            records.extend(payload["data"])

            if requested_page >= total_pages:
                break

            if requested_page >= max_pages:
                raise ValueError(f"Transaction API exceed max_pages={max_pages}")

            requested_page += 1

    finally:
        if owns_session:
            active_session.close()
    return pd.DataFrame.from_records(records)
