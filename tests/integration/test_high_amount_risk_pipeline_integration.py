from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, insert, select
from sqlalchemy.engine import Connection

from banking_intelligence.database.models import (
    Account,
    EtlRun,
    RawTransaction,
    RiskAlert,
    RiskRule,
    SourceSystem,
    Transaction,
    TransactionRiskResult,
)
from banking_intelligence.risk.pipelines.high_amount import (
    build_risk_alert_rows,
    build_risk_result_rows,
    insert_risk_alerts,
    insert_risk_results,
    run_high_amount_risk_pipeline,
)


def test_insert_risk_results_is_idempotent(
    database_connection: Connection,
) -> None:
    """Repeated evaluation should persist one result per rule version."""
    source_system_id = database_connection.execute(
        insert(SourceSystem)
        .values(
            name=f"risk-pipeline-{uuid4()}",
            source_type="csv",
        )
        .returning(SourceSystem.id)
    ).scalar_one()

    etl_run_id = database_connection.execute(
        insert(EtlRun)
        .values(
            source_system_id=source_system_id,
            pipeline_name="risk-pipeline-integration-test",
        )
        .returning(EtlRun.id)
    ).scalar_one()

    raw_transaction_id = database_connection.execute(
        insert(RawTransaction)
        .values(
            etl_run_id=etl_run_id,
            source_row_number=1,
            raw_payload={"transaction_id": "TX-RISK-001", "amount": "150.00"},
            record_fingerprint="c" * 64,
        )
        .returning(RawTransaction.id)
    ).scalar_one()

    account_id = database_connection.execute(
        insert(Account)
        .values(
            source_system_id=source_system_id,
            external_account_id="ACC-RISK-001",
            currency_code="NZD",
        )
        .returning(Account.id)
    ).scalar_one()

    transaction_id = database_connection.execute(
        insert(Transaction)
        .values(
            raw_transaction_id=raw_transaction_id,
            account_id=account_id,
            external_transaction_id="TX-RISK-001",
            amount=Decimal("150.00"),
            currency_code="NZD",
            transaction_timestamp=datetime(2026, 8, 3, 10, 0, tzinfo=UTC),
        )
        .returning(Transaction.id)
    ).scalar_one()

    risk_rule_id = database_connection.execute(
        insert(RiskRule)
        .values(
            code=f"HIGH_AMOUNT_{uuid4()}",
            name="High amount integration rule",
            rule_type="high_amount",
            severity="high",
            threshold=Decimal("100.00"),
        )
        .returning(RiskRule.id)
    ).scalar_one()

    rows = build_risk_result_rows(
        transactions=[{"id": transaction_id, "amount": Decimal("150.00")}],
        risk_rule_id=risk_rule_id,
        threshold=Decimal("100.00"),
    )

    first_insert = insert_risk_results(database_connection, rows)
    second_insert = insert_risk_results(database_connection, rows)

    alert_rows = build_risk_alert_rows(first_insert)
    first_alert_count = insert_risk_alerts(database_connection, alert_rows)
    second_alert_count = insert_risk_alerts(database_connection, alert_rows)

    stored_result = (
        database_connection.execute(
            select(
                TransactionRiskResult.matched,
                TransactionRiskResult.risk_score,
                TransactionRiskResult.evidence,
            ).where(
                TransactionRiskResult.transaction_id == transaction_id,
                TransactionRiskResult.risk_rule_id == risk_rule_id,
            )
        )
        .mappings()
        .one()
    )

    stored_count = database_connection.execute(
        select(func.count())
        .select_from(TransactionRiskResult)
        .where(
            TransactionRiskResult.transaction_id == transaction_id,
            TransactionRiskResult.risk_rule_id == risk_rule_id,
        )
    ).scalar_one()

    stored_alert = (
        database_connection.execute(
            select(
                RiskAlert.transaction_risk_result_id,
                RiskAlert.status,
            ).where(RiskAlert.transaction_risk_result_id == first_insert[0]["id"])
        )
        .mappings()
        .one()
    )

    assert len(first_insert) == 1
    assert second_insert == []
    assert stored_count == 1
    assert stored_result["matched"] is True
    assert stored_result["risk_score"] == Decimal("75.00")
    assert stored_result["evidence"]["threshold"] == "100.00"
    assert first_alert_count == 1
    assert second_alert_count == 0
    assert stored_alert["status"] == "open"


def test_run_high_amount_risk_pipeline_is_idempotent(
    database_connection: Connection,
) -> None:
    """The complete pipeline should evaluate all rows and remain retry-safe."""
    source_system_id = database_connection.execute(
        insert(SourceSystem)
        .values(
            name=f"risk-orchestrator-{uuid4()}",
            source_type="csv",
        )
        .returning(SourceSystem.id)
    ).scalar_one()

    etl_run_id = database_connection.execute(
        insert(EtlRun)
        .values(
            source_system_id=source_system_id,
            pipeline_name="risk-orchestrator-integration-test",
        )
        .returning(EtlRun.id)
    ).scalar_one()

    raw_transaction_id = database_connection.execute(
        insert(RawTransaction)
        .values(
            etl_run_id=etl_run_id,
            source_row_number=1,
            raw_payload={"transaction_id": "TX-ORCHESTRATOR", "amount": "175.00"},
            record_fingerprint="d" * 64,
        )
        .returning(RawTransaction.id)
    ).scalar_one()

    account_id = database_connection.execute(
        insert(Account)
        .values(
            source_system_id=source_system_id,
            external_account_id="ACC-ORCHESTRATOR",
            currency_code="NZD",
        )
        .returning(Account.id)
    ).scalar_one()

    database_connection.execute(
        insert(Transaction).values(
            raw_transaction_id=raw_transaction_id,
            account_id=account_id,
            external_transaction_id="TX-ORCHESTRATOR",
            amount=Decimal("175.00"),
            currency_code="NZD",
            transaction_timestamp=datetime(2026, 8, 4, 10, 0, tzinfo=UTC),
        )
    )

    threshold = Decimal("100.00")
    risk_rule_id = database_connection.execute(
        insert(RiskRule)
        .values(
            code=f"HIGH_AMOUNT_ORCHESTRATOR_{uuid4()}",
            name="High amount orchestrator rule",
            rule_type="high_amount",
            severity="high",
            threshold=threshold,
        )
        .returning(RiskRule.id)
    ).scalar_one()

    transaction_count = database_connection.execute(
        select(func.count()).select_from(Transaction)
    ).scalar_one()
    matched_count = database_connection.execute(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.amount > threshold)
    ).scalar_one()

    first_metrics = run_high_amount_risk_pipeline(
        connection=database_connection,
        risk_rule_id=risk_rule_id,
        batch_size=2000,
    )
    second_metrics = run_high_amount_risk_pipeline(
        connection=database_connection,
        risk_rule_id=risk_rule_id,
        batch_size=2000,
    )

    stored_result_count = database_connection.execute(
        select(func.count())
        .select_from(TransactionRiskResult)
        .where(TransactionRiskResult.risk_rule_id == risk_rule_id)
    ).scalar_one()
    stored_alert_count = database_connection.execute(
        select(func.count())
        .select_from(RiskAlert)
        .join(
            TransactionRiskResult,
            TransactionRiskResult.id == RiskAlert.transaction_risk_result_id,
        )
        .where(TransactionRiskResult.risk_rule_id == risk_rule_id)
    ).scalar_one()

    assert first_metrics == {
        "evaluated_count": transaction_count,
        "inserted_result_count": transaction_count,
        "inserted_alert_count": matched_count,
    }
    assert second_metrics == {
        "evaluated_count": transaction_count,
        "inserted_result_count": 0,
        "inserted_alert_count": 0,
    }
    assert stored_result_count == transaction_count
    assert stored_alert_count == matched_count
