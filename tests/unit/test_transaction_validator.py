import pandas as pd

from banking_intelligence.ingestion.validators.transactions import split_transactions


def test_split_transactions_records_rejection_reasons() -> None:
    """Invalid rows should be separated with explicit failure reasons."""

    timestamp = pd.Timestamp("2026-07-15T00:00:00Z")

    dataframe = pd.DataFrame(
        [
            {
                "transaction_id": "TX001",
                "account_id": "A001",
                "amount": 100.00,
                "currency": "NZD",
                "transaction_timestamp": timestamp,
            },
            {
                "transaction_id": "",
                "account_id": "",
                "amount": float("nan"),
                "currency": "CAD",
                "transaction_timestamp": pd.NaT,
            },
        ]
    )

    accepted, rejected = split_transactions(dataframe)

    assert accepted["transaction_id"].tolist() == ["TX001"]
    assert rejected.index.tolist() == [1]
    assert rejected.loc[1, "rejection_reason"] == (
        "missing_transaction_id;"
        "missing_account_id;"
        "invalid_amount;"
        "unsupported_currency;"
        "invalid_timestamp"
    )
