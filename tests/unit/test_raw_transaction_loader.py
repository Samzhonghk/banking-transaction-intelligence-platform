from unittest.mock import Mock

import pandas as pd
from sqlalchemy.engine import Connection

from banking_intelligence.ingestion.fingerprints import build_record_fingerprint
from banking_intelligence.ingestion.loaders.raw_transactions import (
    load_raw_transactions,
)


def test_load_raw_transaction_builds_bulk_insert_rows() -> None:
    connection = Mock(spec=Connection)
    df = pd.DataFrame(
        [
            {"transaction_id": "TX001", "amount": "100.50"},
            {"transaction_id": "TX002", "amount": "80.00"},
        ]
    )

    loaded_count = load_raw_transactions(
        connection=connection,
        dataframe=df,
        etl_run_id=42,
    )

    assert loaded_count == 2
    connection.execute.assert_called_once()

    insert_statement, rows = connection.execute.call_args.args
    assert insert_statement.table.name == "raw_transactions"

    assert rows[0] == {
        "etl_run_id": 42,
        "source_row_number": 1,
        "raw_payload": {
            "transaction_id": "TX001",
            "amount": "100.50",
        },
        "record_fingerprint": build_record_fingerprint(
            {
                "transaction_id": "TX001",
                "amount": "100.50",
            }
        ),
    }
    assert rows[1]["source_row_number"] == 2


def test_raw_transaction_skip_empty_dataframe() -> None:
    con = Mock(spec=Connection)
    loaded_count = load_raw_transactions(
        connection=con,
        dataframe=pd.DataFrame(),
        etl_run_id=42,
    )
    assert loaded_count == 0
    con.execute.assert_not_called()
