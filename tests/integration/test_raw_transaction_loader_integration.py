from uuid import uuid4

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.engine import Connection

from banking_intelligence.database.models import (
    EtlRun,
    RawTransaction,
    SourceSystem,
)
from banking_intelligence.ingestion.loaders.raw_transactions import (
    load_raw_transactions,
)


def test_load_raw_transactions_inserts_duplicate_payloads(
    database_connection: Connection,
) -> None:
    """Duplicate payloads from different source rows should be preserved."""
    source_system_id = database_connection.execute(
        insert(SourceSystem)
        .values(
            name=f"integration-csv-{uuid4()}",
            source_type="csv",
        )
        .returning(SourceSystem.id)
    ).scalar_one()

    etl_run_id = database_connection.execute(
        insert(EtlRun)
        .values(
            source_system_id=source_system_id,
            pipeline_name="raw-loader-integration-test",
        )
        .returning(EtlRun.id)
    ).scalar_one()

    duplicate_record = {
        "transaction_id": "TX001",
        "amount": "100.50",
    }
    dataframe = pd.DataFrame([duplicate_record, duplicate_record])
    loaded_count = load_raw_transactions(
        connection=database_connection,
        dataframe=dataframe,
        etl_run_id=etl_run_id,
    )

    stored_rows = (
        database_connection.execute(
            select(
                RawTransaction.source_row_number,
                RawTransaction.raw_payload,
                RawTransaction.record_fingerprint,
            )
            .where(RawTransaction.etl_run_id == etl_run_id)
            .order_by(RawTransaction.source_row_number)
        )
        .mappings()
        .all()
    )

    assert loaded_count == 2
    assert [row["source_row_number"] for row in stored_rows] == [1, 2]
    assert stored_rows[0]["raw_payload"] == duplicate_record
    assert stored_rows[1]["raw_payload"] == duplicate_record

    assert stored_rows[0]["record_fingerprint"] == stored_rows[1]["record_fingerprint"]
