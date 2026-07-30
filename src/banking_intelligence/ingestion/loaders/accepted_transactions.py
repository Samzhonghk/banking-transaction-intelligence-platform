from decimal import Decimal

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from banking_intelligence.database.models import (
    Account,
    EtlRun,
    RawTransaction,
    Transaction,
)

TRANSACTION_INSERT_BATCH_SIZE = 5000


def load_accepted_transactions(
    connection: Connection,
    accepted_df: pd.DataFrame,
    etl_run_id: int,
) -> int:
    """Upsert accounts and persist validated transactions with raw lineage."""
    if accepted_df.empty:
        return 0

    source_system_id = connection.execute(
        select(EtlRun.source_system_id).where(EtlRun.id == etl_run_id)
    ).scalar_one()

    source_row_numbers = [int(index) + 1 for index in accepted_df.index]

    raw_transactions = connection.execute(
        select(
            RawTransaction.id,
            RawTransaction.source_row_number,
        ).where(
            RawTransaction.etl_run_id == etl_run_id,
            RawTransaction.source_row_number.in_(source_row_numbers),
        )
    ).all()

    raw_transaction_id_by_source_row = {
        row.source_row_number: row.id for row in raw_transactions
    }

    missing_source_rows = sorted(
        set(source_row_numbers) - set(raw_transaction_id_by_source_row)
    )

    if missing_source_rows:
        raise ValueError(
            f"Raw transactions not found for source rows: {missing_source_rows}"
        )

    currency_counts_by_account = accepted_df.groupby("account_id")["currency"].nunique()

    conflicting_account_ids = (
        currency_counts_by_account[currency_counts_by_account > 1]
        .index.astype(str)
        .tolist()
    )

    if conflicting_account_ids:
        raise ValueError(
            f"Accounts have multiple currencies: {sorted(conflicting_account_ids)}"
        )

    unique_accounts = accepted_df[["account_id", "currency"]].drop_duplicates(
        subset=["account_id"]
    )

    account_rows = [
        {
            "source_system_id": source_system_id,
            "external_account_id": str(account["account_id"]),
            "currency_code": str(account["currency"]),
        }
        for _, account in unique_accounts.iterrows()
    ]

    account_insert = pg_insert(Account).values(account_rows)
    account_upsert = account_insert.on_conflict_do_nothing(
        constraint="uq_accounts_source_external_id"
    )

    connection.execute(account_upsert)

    external_account_ids = [
        str(account_id) for account_id in unique_accounts["account_id"]
    ]

    stored_accounts = connection.execute(
        select(
            Account.id,
            Account.external_account_id,
            Account.currency_code,
        ).where(
            Account.source_system_id == source_system_id,
            Account.external_account_id.in_(external_account_ids),
        )
    ).all()

    account_id_by_external_id = {
        row.external_account_id: row.id for row in stored_accounts
    }

    account_currency_by_external_id = {
        row.external_account_id: row.currency_code for row in stored_accounts
    }

    missing_account_ids = sorted(
        set(external_account_ids) - account_id_by_external_id.keys()
    )

    if missing_account_ids:
        raise ValueError(f"Account not found after upsert: {missing_account_ids}")

    incoming_currency_by_external_id = {
        str(account["account_id"]): str(account["currency"])
        for _, account in unique_accounts.iterrows()
    }

    currency_mismatch_account_ids = sorted(
        external_account_id
        for external_account_id, incoming_currency in (
            incoming_currency_by_external_id.items()
        )
        if account_currency_by_external_id[external_account_id] != incoming_currency
    )

    if currency_mismatch_account_ids:
        raise ValueError(
            "Incoming currencies do not match stored accounts: "
            f"{currency_mismatch_account_ids}"
        )

    transaction_rows = []
    for index, accepted_record in accepted_df.iterrows():
        source_row_number = int(index) + 1
        external_account_id = str(accepted_record["account_id"])

        description = str(accepted_record["description"]).strip() or None

        transaction_rows.append(
            {
                "raw_transaction_id": (
                    raw_transaction_id_by_source_row[source_row_number]
                ),
                "account_id": account_id_by_external_id[external_account_id],
                "external_transaction_id": str(accepted_record["transaction_id"]),
                "amount": Decimal(str(accepted_record["amount"])),
                "currency_code": str(accepted_record["currency"]),
                "description": description,
                "transaction_timestamp": pd.Timestamp(
                    accepted_record["transaction_timestamp"]
                ).to_pydatetime(),
            }
        )

    inserted_count = 0
    for batch_start in range(
        0,
        len(transaction_rows),
        TRANSACTION_INSERT_BATCH_SIZE,
    ):
        transaction_batch = transaction_rows[
            batch_start : batch_start + TRANSACTION_INSERT_BATCH_SIZE
        ]

        transaction_insert = pg_insert(Transaction).values(transaction_batch)

        transaction_load = transaction_insert.on_conflict_do_nothing(
            constraint="uq_transactions_account_external_id"
        ).returning(Transaction.id)

        result = connection.execute(transaction_load)
        inserted_count += len(result.scalars().all())

    return inserted_count
