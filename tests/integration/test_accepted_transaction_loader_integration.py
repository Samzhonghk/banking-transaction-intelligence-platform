from decimal import Decimal
from uuid import uuid4

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.engine import Connection

from banking_intelligence.database.models import (
    Account,
    EtlRun,
    RawTransaction,
    SourceSystem,
    Transaction,
)
from banking_intelligence.ingestion.loaders import (
    load_accepted_transactions,
    load_raw_transactions,
)
from banking_intelligence.ingestion.transformers.transactions import (
    transform_transactions,
)
from banking_intelligence.ingestion.validators.transactions import (
    split_transactions,
)


def test_load_accepted_transactions_is_idempotent(
    database_connection: Connection,
) -> None:
    """Accepted rows should retain lineage and remain unique across reruns."""
    source_system_id = database_connection.execute(
        insert(SourceSystem)
        .values(
            name=f"accepted-loader-{uuid4()}",
            source_type="csv",
        )
        .returning(SourceSystem.id)
    ).scalar_one()

    etl_run_id = database_connection.execute(
        insert(EtlRun)
        .values(
            source_system_id=source_system_id,
            pipeline_name="accepted-loader-integration-test",
        )
        .returning(EtlRun.id)
    ).scalar_one()

    raw_dataframe = pd.DataFrame(
        [
            {
                "transaction_id": "TX001",
                "account_id": "ACC001",
                "amount": "100.50",
                "currency": "NZD",
                "description": "",
                "transaction_timestamp": "2026-07-27T10:00:00Z",
            },
            {
                "transaction_id": "TX002",
                "account_id": "ACC001",
                "amount": "25.25",
                "currency": "NZD",
                "description": "Coffee",
                "transaction_timestamp": "2026-07-27T10:05:00Z",
            },
        ]
    )

    assert (
        load_raw_transactions(
            connection=database_connection,
            dataframe=raw_dataframe,
            etl_run_id=etl_run_id,
        )
        == 2
    )

    transformed = transform_transactions(raw_dataframe)
    accepted, rejected = split_transactions(transformed)

    assert rejected.empty

    first_loaded_count = load_accepted_transactions(
        connection=database_connection,
        accepted_df=accepted,
        etl_run_id=etl_run_id,
    )
    second_loaded_count = load_accepted_transactions(
        connection=database_connection,
        accepted_df=accepted,
        etl_run_id=etl_run_id,
    )

    stored_accounts = (
        database_connection.execute(
            select(
                Account.external_account_id,
                Account.currency_code,
            ).where(Account.source_system_id == source_system_id)
        )
        .mappings()
        .all()
    )

    stored_transactions = (
        database_connection.execute(
            select(
                Transaction.external_transaction_id,
                Transaction.amount,
                Transaction.description,
                RawTransaction.source_row_number,
            )
            .join(
                RawTransaction,
                RawTransaction.id == Transaction.raw_transaction_id,
            )
            .where(RawTransaction.etl_run_id == etl_run_id)
            .order_by(RawTransaction.source_row_number)
        )
        .mappings()
        .all()
    )

    assert first_loaded_count == 2
    assert second_loaded_count == 0
    assert stored_accounts == [
        {
            "external_account_id": "ACC001",
            "currency_code": "NZD",
        }
    ]
    assert [
        {
            "external_transaction_id": row["external_transaction_id"],
            "amount": row["amount"],
            "description": row["description"],
            "source_row_number": row["source_row_number"],
        }
        for row in stored_transactions
    ] == [
        {
            "external_transaction_id": "TX001",
            "amount": Decimal("100.50"),
            "description": None,
            "source_row_number": 1,
        },
        {
            "external_transaction_id": "TX002",
            "amount": Decimal("25.25"),
            "description": "Coffee",
            "source_row_number": 2,
        },
    ]
