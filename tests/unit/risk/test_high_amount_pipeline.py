from decimal import Decimal
from unittest.mock import MagicMock, call, patch

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection

from banking_intelligence.risk.pipelines.high_amount import (
    build_risk_alert_rows,
    build_risk_result_rows,
    fetch_high_amount_rule,
    fetch_transaction_batch,
    insert_risk_alerts,
    insert_risk_results,
    run_high_amount_risk_pipeline,
)


def test_fetch_transaction_batch_uses_keyset_pagination() -> None:
    """The next batch should be bounded and start after the previous ID."""
    connection = MagicMock(spec=Connection)
    expected_rows = [{"id": 43, "amount": Decimal("100.00")}]
    connection.execute.return_value.mappings.return_value.all.return_value = (
        expected_rows
    )

    rows = fetch_transaction_batch(
        connection=connection,
        after_transaction_id=42,
        batch_size=25,
    )

    statement = connection.execute.call_args.args[0]
    compiled_sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert rows == expected_rows
    assert "WHERE core.transactions.id > 42" in compiled_sql
    assert "ORDER BY core.transactions.id ASC" in compiled_sql
    assert "LIMIT 25" in compiled_sql


def test_fetch_transaction_batch_rejects_non_positive_size() -> None:
    """Invalid batch sizes should fail before querying PostgreSQL."""
    connection = MagicMock(spec=Connection)

    with pytest.raises(ValueError, match="Batch size must be greater than zero"):
        fetch_transaction_batch(
            connection=connection,
            after_transaction_id=0,
            batch_size=0,
        )

    connection.execute.assert_not_called()


def test_build_risk_result_rows_preserves_outcomes_and_evidence() -> None:
    """A transaction batch should become persistence-ready risk rows."""
    transactions = [
        {"id": 101, "amount": Decimal("80.00")},
        {"id": 102, "amount": Decimal("150.00")},
    ]

    rows = build_risk_result_rows(
        transactions=transactions,
        risk_rule_id=7,
        threshold=Decimal("100.00"),
    )

    assert [row["transaction_id"] for row in rows] == [101, 102]
    assert [row["matched"] for row in rows] == [False, True]
    assert [row["risk_score"] for row in rows] == [
        Decimal("0.00"),
        Decimal("75.00"),
    ]
    assert rows[1]["evidence"] == {
        "rule_type": "high_amount",
        "amount": "150.00",
        "threshold": "100.00",
        "excess_amount": "50.00",
    }


def test_insert_risk_results_skips_empty_batch() -> None:
    """An empty evaluation batch should not execute a database statement."""
    connection = MagicMock(spec=Connection)

    inserted_rows = insert_risk_results(connection=connection, rows=[])

    assert inserted_rows == []
    connection.execute.assert_not_called()


def test_build_risk_alert_rows_keeps_only_new_matches() -> None:
    """Only newly inserted matched results should become alerts."""
    inserted_results = [
        {"id": 101, "matched": True},
        {"id": 102, "matched": False},
        {"id": 103, "matched": True},
    ]

    rows = build_risk_alert_rows(inserted_results)

    assert rows == [
        {"transaction_risk_result_id": 101},
        {"transaction_risk_result_id": 103},
    ]


def test_insert_risk_alerts_skips_empty_batch() -> None:
    """An empty matched batch should not execute an alert insert."""
    connection = MagicMock(spec=Connection)

    inserted_count = insert_risk_alerts(connection=connection, rows=[])

    assert inserted_count == 0
    connection.execute.assert_not_called()


def test_fetch_high_amount_rule_returns_executable_rule() -> None:
    """An active high-amount rule with a threshold should be returned."""
    connection = MagicMock(spec=Connection)
    expected_rule = {"id": 7, "threshold": Decimal("100.00")}
    connection.execute.return_value.mappings.return_value.one_or_none.return_value = (
        expected_rule
    )

    rule = fetch_high_amount_rule(connection=connection, risk_rule_id=7)

    assert rule == expected_rule
    connection.execute.assert_called_once()


def test_fetch_high_amount_rule_rejects_missing_rule() -> None:
    """A missing or non-executable rule should fail before batch processing."""
    connection = MagicMock(spec=Connection)
    connection.execute.return_value.mappings.return_value.one_or_none.return_value = (
        None
    )

    with pytest.raises(
        ValueError,
        match="Active high-amount risk rule 99 was not found",
    ):
        fetch_high_amount_rule(connection=connection, risk_rule_id=99)


def test_run_high_amount_risk_pipeline_processes_multiple_batches() -> None:
    """The orchestrator should continue until keyset pagination is exhausted."""
    connection = MagicMock(spec=Connection)
    batches = [
        [
            {"id": 1, "amount": Decimal("150.00")},
            {"id": 2, "amount": Decimal("80.00")},
        ],
        [{"id": 3, "amount": Decimal("250.00")}],
        [],
    ]
    inserted_batches = [
        [
            {"id": 501, "matched": True},
            {"id": 502, "matched": False},
        ],
        [{"id": 503, "matched": True}],
    ]

    with (
        patch(
            "banking_intelligence.risk.pipelines.high_amount.fetch_high_amount_rule",
            return_value={"id": 7, "threshold": Decimal("100.00")},
        ),
        patch(
            "banking_intelligence.risk.pipelines.high_amount.fetch_transaction_batch",
            side_effect=batches,
        ) as fetch_batch,
        patch(
            "banking_intelligence.risk.pipelines.high_amount.insert_risk_results",
            side_effect=inserted_batches,
        ),
        patch(
            "banking_intelligence.risk.pipelines.high_amount.insert_risk_alerts",
            side_effect=[1, 1],
        ),
    ):
        metrics = run_high_amount_risk_pipeline(
            connection=connection,
            risk_rule_id=7,
            batch_size=2,
        )

    assert metrics == {
        "evaluated_count": 3,
        "inserted_result_count": 3,
        "inserted_alert_count": 2,
    }
    assert fetch_batch.call_args_list == [
        call(connection=connection, after_transaction_id=0, batch_size=2),
        call(connection=connection, after_transaction_id=2, batch_size=2),
        call(connection=connection, after_transaction_id=3, batch_size=2),
    ]


def test_run_high_amount_risk_pipeline_rejects_non_positive_batch_size() -> None:
    """Invalid batch size should fail before loading a database rule."""
    connection = MagicMock(spec=Connection)

    with pytest.raises(ValueError, match="Batch size must be greater than zero"):
        run_high_amount_risk_pipeline(
            connection=connection,
            risk_rule_id=7,
            batch_size=0,
        )

    connection.execute.assert_not_called()
