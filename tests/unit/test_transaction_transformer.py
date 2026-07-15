import pandas as pd

from banking_intelligence.ingestion.transformers.transactions import (
    transform_transactions,
)


def test_transform_transactions_standardises_values() -> None:
    """Transaction fields should be cleaned without changing raw data."""

    raw = pd.DataFrame(
        [
            {
                "transaction_id": " TX001 ",
                "account_id": " 00123 ",
                "description": " Grocery store ",
                "currency": " nzd ",
                "amount": "100.50",
                "transaction_timestamp": "2026-07-15T10:00:00+12:00",
            }
        ]
    )

    transformed = transform_transactions(raw)
    assert transformed.loc[0, "transaction_id"] == "TX001"
    assert transformed.loc[0, "account_id"] == "00123"
    assert transformed.loc[0, "description"] == "Grocery store"
    assert transformed.loc[0, "currency"] == "NZD"
    assert transformed.loc[0, "amount"] == 100.50
    assert transformed.loc[0, "transaction_timestamp"] == pd.Timestamp(
        "2026-07-14T22:00:00Z"
    )

    assert raw.loc[0, "currency"] == " nzd "
    assert raw.loc[0, "amount"] == "100.50"
