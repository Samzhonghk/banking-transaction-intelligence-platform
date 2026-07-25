from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import insert, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from banking_intelligence.database.models import (
    Account,
    EtlRun,
    RawTransaction,
    SourceSystem,
    Transaction,
)


def test_core_transaction_preserves_lineage_and_constraints(
    database_connection: Connection,
) -> None:
    """Trusted transactions should retain precise values and raw lineage."""
    source_system_id = database_connection.execute(
        insert(SourceSystem)
        .values(
            name=f"core-model-{uuid4()}",
            source_type="csv",
        )
        .returning(SourceSystem.id)
    ).scalar_one()

    etl_run_id = database_connection.execute(
        insert(EtlRun)
        .values(
            source_system_id=source_system_id,
            pipeline_name="core-model-integration-test",
        )
        .returning(EtlRun.id)
    ).scalar_one()

    raw_transaction_id = database_connection.execute(
        insert(RawTransaction)
        .values(
            etl_run_id=etl_run_id,
            source_row_number=1,
            raw_payload={
                "transaction_id": "TX001",
                "account_id": "ACC001",
                "amount": "100.50",
                "currency": "NZD",
            },
            record_fingerprint="a" * 64,
        )
        .returning(RawTransaction.id)
    ).scalar_one()

    account_id = database_connection.execute(
        insert(Account)
        .values(
            source_system_id=source_system_id,
            external_account_id="ACC001",
            currency_code="NZD",
        )
        .returning(Account.id)
    ).scalar_one()

    transaction_id = database_connection.execute(
        insert(Transaction)
        .values(
            raw_transaction_id=raw_transaction_id,
            account_id=account_id,
            external_transaction_id="TX001",
            amount=Decimal("100.50"),
            currency_code="NZD",
            description="Integration test transaction",
            transaction_timestamp=datetime(
                2026,
                7,
                26,
                10,
                30,
                tzinfo=UTC,
            ),
        )
        .returning(Transaction.id)
    ).scalar_one()

    stored_transaction = (
        database_connection.execute(
            select(
                Transaction.amount,
                Transaction.currency_code,
                Account.external_account_id,
                RawTransaction.source_row_number,
            )
            .join(Account, Account.id == Transaction.account_id)
            .join(
                RawTransaction,
                RawTransaction.id == Transaction.raw_transaction_id,
            )
            .where(Transaction.id == transaction_id)
        )
        .mappings()
        .one()
    )

    assert stored_transaction["amount"] == Decimal("100.50")
    assert stored_transaction["currency_code"] == "NZD"
    assert stored_transaction["external_account_id"] == "ACC001"
    assert stored_transaction["source_row_number"] == 1

    invalid_raw_transaction_id = database_connection.execute(
        insert(RawTransaction)
        .values(
            etl_run_id=etl_run_id,
            source_row_number=2,
            raw_payload={
                "transaction_id": "TX002",
                "account_id": "ACC001",
                "amount": "-1.00",
                "currency": "NZD",
            },
            record_fingerprint="b" * 64,
        )
        .returning(RawTransaction.id)
    ).scalar_one()

    savepoint = database_connection.begin_nested()
    with pytest.raises(IntegrityError):
        database_connection.execute(
            insert(Transaction).values(
                raw_transaction_id=invalid_raw_transaction_id,
                account_id=account_id,
                external_transaction_id="TX002",
                amount=Decimal("-1.00"),
                currency_code="NZD",
                transaction_timestamp=datetime.now(UTC),
            )
        )
    savepoint.rollback()
