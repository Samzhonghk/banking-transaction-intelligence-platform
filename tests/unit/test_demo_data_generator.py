import pytest

from banking_intelligence.demo_data import (
    CURRENCIES,
    apply_invalid_case,
    generate_transaction_rows,
)


def test_generate_transaction_rows_is_reproducible() -> None:
    """The same row count and seed should always produce identical data."""
    first_run = list(generate_transaction_rows(row_count=20, seed=42))
    second_run = list(generate_transaction_rows(row_count=20, seed=42))

    assert first_run == second_run
    assert len(first_run) == 20
    assert first_run[0]["transaction_id"] == "TX-GEN-00000001"


def test_generated_accounts_keep_one_currency() -> None:
    """Every valid account should retain one currency across all transactions."""
    currency_by_account: dict[str, str] = {}

    for row in generate_transaction_rows(row_count=5_000, seed=42):
        account_id = row["account_id"]
        currency = row["currency"]

        if not account_id or currency not in CURRENCIES:
            continue

        previous_currency = currency_by_account.setdefault(account_id, currency)
        assert currency == previous_currency


def test_apply_invalid_case_rejects_unknown_rule() -> None:
    """Unknown invalid-data rules should fail instead of silently doing nothing."""
    row = {
        "transaction_id": "TX001",
        "account_id": "ACC001",
        "amount": "100.00",
        "currency": "NZD",
        "description": "Test transaction",
        "transaction_timestamp": "2026-01-01T00:00:00Z",
    }

    with pytest.raises(ValueError, match="Unsupported invalid case"):
        apply_invalid_case(row, "unknown-rule")
