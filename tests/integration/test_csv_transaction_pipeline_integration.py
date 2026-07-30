from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest
import requests
from sqlalchemy import delete, func, insert, select
from sqlalchemy.engine import Engine

from banking_intelligence.core.config import Settings
from banking_intelligence.database.engine import create_database_engine
from banking_intelligence.database.models import (
    Account,
    EtlRun,
    RawTransaction,
    RejectedRecord,
    SourceSystem,
    Transaction,
)
from banking_intelligence.ingestion.pipelines import (
    run_api_transaction_pipeline,
    run_csv_transaction_pipeline,
)


@pytest.fixture
def database_engine() -> Engine:
    """Provide an engine for a pipeline that manages its own transactions."""
    engine = create_database_engine(Settings())
    try:
        yield engine
    finally:
        engine.dispose()


def test_csv_transaction_pipeline_persists_all_outcomes(
    database_engine: Engine,
    tmp_path: Path,
) -> None:
    """A successful batch should persist raw, accepted, and rejected outcomes."""
    source_name = f"pipeline-success-{uuid4()}"
    with database_engine.begin() as connection:
        source_system_id = connection.execute(
            insert(SourceSystem)
            .values(name=source_name, source_type="csv")
            .returning(SourceSystem.id)
        ).scalar_one()

    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "transaction_id,account_id,amount,currency,description,"
        "transaction_timestamp\n"
        "TX001,ACC001,100.50,NZD,Salary,2026-07-28T09:00:00Z\n"
        "TX002,ACC001,-5.00,NZD,Invalid,2026-07-28T09:05:00Z\n"
        "TX003,ACC001,25.25,NZD,Coffee,2026-07-28T09:10:00Z\n",
        encoding="utf-8",
    )

    try:
        etl_run_id = run_csv_transaction_pipeline(
            engine=database_engine,
            file_path=csv_path,
            source_system_id=source_system_id,
        )

        with database_engine.connect() as connection:
            etl_run = connection.execute(
                select(
                    EtlRun.status,
                    EtlRun.extracted_count,
                    EtlRun.accepted_count,
                    EtlRun.rejected_count,
                    EtlRun.finished_at,
                ).where(EtlRun.id == etl_run_id)
            ).one()

            raw_count = connection.scalar(
                select(func.count())
                .select_from(RawTransaction)
                .where(RawTransaction.etl_run_id == etl_run_id)
            )
            accepted_count = connection.scalar(
                select(func.count())
                .select_from(Transaction)
                .join(
                    RawTransaction,
                    RawTransaction.id == Transaction.raw_transaction_id,
                )
                .where(RawTransaction.etl_run_id == etl_run_id)
            )
            rejected_count = connection.scalar(
                select(func.count())
                .select_from(RejectedRecord)
                .join(
                    RawTransaction,
                    RawTransaction.id == RejectedRecord.raw_transaction_id,
                )
                .where(RawTransaction.etl_run_id == etl_run_id)
            )

        assert etl_run.status == "succeeded"
        assert etl_run.extracted_count == 3
        assert etl_run.accepted_count == 2
        assert etl_run.rejected_count == 1
        assert etl_run.finished_at is not None
        assert raw_count == 3
        assert accepted_count == 2
        assert rejected_count == 1
    finally:
        with database_engine.begin() as connection:
            account_ids = select(Account.id).where(
                Account.source_system_id == source_system_id
            )
            connection.execute(
                delete(Transaction).where(Transaction.account_id.in_(account_ids))
            )
            connection.execute(
                delete(Account).where(Account.source_system_id == source_system_id)
            )
            connection.execute(
                delete(EtlRun).where(EtlRun.source_system_id == source_system_id)
            )
            connection.execute(
                delete(SourceSystem).where(SourceSystem.id == source_system_id)
            )


def test_csv_transaction_pipeline_records_failure(
    database_engine: Engine,
    tmp_path: Path,
) -> None:
    """A failed extraction should remain visible in ETL run history."""
    with database_engine.begin() as connection:
        source_system_id = connection.execute(
            insert(SourceSystem)
            .values(
                name=f"pipeline-failure-{uuid4()}",
                source_type="csv",
            )
            .returning(SourceSystem.id)
        ).scalar_one()

    missing_path = tmp_path / "missing.csv"

    try:
        with pytest.raises(FileNotFoundError):
            run_csv_transaction_pipeline(
                engine=database_engine,
                file_path=missing_path,
                source_system_id=source_system_id,
            )

        with database_engine.connect() as connection:
            failed_run = connection.execute(
                select(
                    EtlRun.status,
                    EtlRun.finished_at,
                    EtlRun.error_message,
                ).where(EtlRun.source_system_id == source_system_id)
            ).one()

        assert failed_run.status == "failed"
        assert failed_run.finished_at is not None
        assert "No such file or directory" in failed_run.error_message
        assert missing_path.name in failed_run.error_message
    finally:
        with database_engine.begin() as connection:
            connection.execute(
                delete(EtlRun).where(EtlRun.source_system_id == source_system_id)
            )
            connection.execute(
                delete(SourceSystem).where(SourceSystem.id == source_system_id)
            )


def test_api_transaction_pipeline_persists_paginated_outcomes(
    database_engine: Engine,
) -> None:
    """Paginated HTTP records should use the shared PostgreSQL pipeline."""
    with database_engine.begin() as connection:
        source_system_id = connection.execute(
            insert(SourceSystem)
            .values(
                name=f"pipeline-api-{uuid4()}",
                source_type="api",
                base_url="https://example.test/transactions",
            )
            .returning(SourceSystem.id)
        ).scalar_one()

    session = Mock(spec=requests.Session)
    first_response = Mock(spec=requests.Response)
    first_response.json.return_value = {
        "data": [
            {
                "transaction_id": "API-TX001",
                "account_id": "API-ACC001",
                "amount": "80.50",
                "currency": "nzd",
                "description": "API payment",
                "transaction_timestamp": "2026-07-30T09:00:00Z",
            },
            {
                "transaction_id": "API-TX002",
                "account_id": "API-ACC002",
                "amount": "-5.00",
                "currency": "NZD",
                "description": "Invalid API payment",
                "transaction_timestamp": "2026-07-30T09:05:00Z",
            },
        ],
        "pagination": {
            "page": 1,
            "total_pages": 2,
        },
    }
    second_response = Mock(spec=requests.Response)
    second_response.json.return_value = {
        "data": [
            {
                "transaction_id": "API-TX003",
                "account_id": "API-ACC003",
                "amount": "25.25",
                "currency": "AUD",
                "description": "Second page",
                "transaction_timestamp": "2026-07-30T09:10:00Z",
            }
        ],
        "pagination": {
            "page": 2,
            "total_pages": 2,
        },
    }
    session.get.side_effect = [
        first_response,
        second_response,
    ]

    try:
        etl_run_id = run_api_transaction_pipeline(
            engine=database_engine,
            url="https://example.test/transactions",
            source_system_id=source_system_id,
            session=session,
            page_size=2,
        )

        with database_engine.connect() as connection:
            etl_run = connection.execute(
                select(
                    EtlRun.status,
                    EtlRun.extracted_count,
                    EtlRun.accepted_count,
                    EtlRun.rejected_count,
                ).where(EtlRun.id == etl_run_id)
            ).one()
            raw_count = connection.scalar(
                select(func.count())
                .select_from(RawTransaction)
                .where(RawTransaction.etl_run_id == etl_run_id)
            )

        assert etl_run.status == "succeeded"
        assert etl_run.extracted_count == 3
        assert etl_run.accepted_count == 2
        assert etl_run.rejected_count == 1
        assert raw_count == 3
        assert session.get.call_count == 2
    finally:
        with database_engine.begin() as connection:
            account_ids = select(Account.id).where(
                Account.source_system_id == source_system_id
            )
            connection.execute(
                delete(Transaction).where(Transaction.account_id.in_(account_ids))
            )
            connection.execute(
                delete(Account).where(Account.source_system_id == source_system_id)
            )
            connection.execute(
                delete(EtlRun).where(EtlRun.source_system_id == source_system_id)
            )
            connection.execute(
                delete(SourceSystem).where(SourceSystem.id == source_system_id)
            )
