from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest
from sqlalchemy.engine import Connection

from banking_intelligence.ingestion.loaders.rejected_records import (
    load_rejected_records,
)


def test_load_rejected_records_skip_empty_dataframe() -> None:
    connection = Mock(spec=Connection)
    rejected_dataframe = pd.DataFrame()

    loaded_count = load_rejected_records(
        connection=connection,
        rejected_dataframe=rejected_dataframe,
        etl_run_id=42,
    )

    assert loaded_count == 0
    connection.execute.assert_not_called()


def test_load_rejected_records_builds_bulk_insert_rows() -> None:
    connection = Mock(spec=Connection)

    select_result = Mock()
    select_result.all.return_value = [
        SimpleNamespace(id=101, source_row_number=1),
        SimpleNamespace(id=103, source_row_number=3),
    ]

    connection.execute.side_effect = [
        select_result,
        Mock(),
    ]

    rejected_dataframe = pd.DataFrame(
        [
            {"rejection_reason": ("invalid_amount;unsupported_currency")},
            {
                "rejection_reason": "invalid_timestamp",
            },
        ],
        index=[0, 2],
    )

    loaded_count = load_rejected_records(
        connection=connection,
        rejected_dataframe=rejected_dataframe,
        etl_run_id=42,
    )

    assert loaded_count == 2
    assert connection.execute.call_count == 2

    inserted_rows = connection.execute.call_args_list[1].args[1]

    assert inserted_rows == [
        {
            "raw_transaction_id": 101,
            "rejection_reasons": [
                "invalid_amount",
                "unsupported_currency",
            ],
        },
        {
            "raw_transaction_id": 103,
            "rejection_reasons": [
                "invalid_timestamp",
            ],
        },
    ]


def test_load_rejected_records_fails_when_raw_record_is_missing() -> None:
    connection = Mock(spec=Connection)
    select_result = Mock()
    select_result.all.return_value = [
        SimpleNamespace(id=101, source_row_number=1),
    ]
    connection.execute.return_value = select_result

    rejected_df = pd.DataFrame(
        [
            {"rejection_reason": "invalid_amount"},
            {"rejection_reason": "invalid_timestamp"},
        ],
        index=[0, 2],
    )

    with pytest.raises(
        ValueError,
        match=r"Raw transactions not found for source rows: \[3\]",
    ):
        load_rejected_records(
            connection=connection,
            rejected_dataframe=rejected_df,
            etl_run_id=42,
        )

    connection.execute.assert_called_once()
