from uuid import uuid4

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.engine import Connection

from banking_intelligence.database.models import (
    EtlRun,
    RawTransaction,
    RejectedRecord,
    SourceSystem,
)
from banking_intelligence.ingestion.loaders.raw_transactions import (
    load_raw_transactions,
)
from banking_intelligence.ingestion.loaders.rejected_records import (
    load_rejected_records,
)


def test_load_rejected_records_persists_jsonb_reasons(
    database_connection: Connection,
) -> None:
    source_system_id = database_connection.execute(
        insert(SourceSystem)
        .values(
            name=f"rejected-loader-{uuid4()}",
            source_type="csv",
        )
        .returning(SourceSystem.id)
    ).scalar_one()

    etl_run_id = database_connection.execute(
        insert(EtlRun)
        .values(
            source_system_id=source_system_id,
            pipeline_name="rejected-loader-integration-test",
        )
        .returning(EtlRun.id)
    ).scalar_one()

    raw_df = pd.DataFrame(
        [
            {
                "transaction_id": "TX001",
                "amount": "100.50",
            },
            {
                "transaction_id": "TX002",
                "amount": "-5.00",
            },
        ]
    )

    raw_loaded_count = load_raw_transactions(
        connection=database_connection,
        dataframe=raw_df,
        etl_run_id=etl_run_id,
    )

    assert raw_loaded_count == 2

    rejected_df = pd.DataFrame(
        [
            {
                "rejection_reason": ("invalid_amount;manual_review_required"),
            }
        ],
        index=[1],
    )

    rejected_loaded_count = load_rejected_records(
        connection=database_connection,
        rejected_dataframe=rejected_df,
        etl_run_id=etl_run_id,
    )

    stored_rejection = (
        database_connection.execute(
            select(
                RawTransaction.source_row_number,
                RejectedRecord.rejection_reasons,
            )
            .join(
                RejectedRecord,
                RejectedRecord.raw_transaction_id == RawTransaction.id,
            )
            .where(RawTransaction.etl_run_id == etl_run_id)
        )
        .mappings()
        .one()
    )

    assert rejected_loaded_count == 1
    assert stored_rejection["source_row_number"] == 2
    assert stored_rejection["rejection_reasons"] == [
        "invalid_amount",
        "manual_review_required",
    ]
