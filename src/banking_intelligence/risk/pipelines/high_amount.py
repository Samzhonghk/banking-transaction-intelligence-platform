from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection, RowMapping

from banking_intelligence.database.models import (
    RiskAlert,
    RiskRule,
    Transaction,
    TransactionRiskResult,
)
from banking_intelligence.risk.evaluators.high_amount import evaluate_high_amount


def fetch_transaction_batch(
    connection: Connection,
    after_transaction_id: int,
    batch_size: int,
) -> Sequence[RowMapping]:
    """Return the next trusted transaction batch using keyset pagination."""
    if batch_size <= 0:
        raise ValueError("Batch size must be greater than zero")

    query = (
        select(
            Transaction.id,
            Transaction.amount,
        )
        .where(Transaction.id > after_transaction_id)
        .order_by(Transaction.id.asc())
        .limit(batch_size)
    )

    return connection.execute(query).mappings().all()


def build_risk_result_rows(
    transactions: Sequence[RowMapping],
    risk_rule_id: int,
    threshold: Decimal,
) -> list[dict[str, object]]:
    """Build persistence rows for one transaction risk-evaluation batch."""
    rows: list[dict[str, object]] = []
    for t in transactions:
        matched, risk_score, evidence = evaluate_high_amount(
            amount=t["amount"],
            threshold=threshold,
        )

        rows.append(
            {
                "transaction_id": t["id"],
                "risk_rule_id": risk_rule_id,
                "matched": matched,
                "risk_score": risk_score,
                "evidence": evidence,
            }
        )

    return rows


def insert_risk_results(
    connection: Connection,
    rows: Sequence[dict[str, object]],
) -> Sequence[RowMapping]:
    """Insert new risk results idempotently and return inserted outcomes."""
    if not rows:
        return []

    statement = (
        insert(TransactionRiskResult)
        .values(list(rows))
        .on_conflict_do_nothing(
            constraint="uq_transaction_risk_results_transaction_rule",
        )
        .returning(
            TransactionRiskResult.id,
            TransactionRiskResult.matched,
        )
    )

    return connection.execute(statement).mappings().all()


def build_risk_alert_rows(
    inserted_results: Sequence[RowMapping],
) -> list[dict[str, object]]:
    """Build alert rows only for newly inserted matched risk results."""
    return [
        {"transaction_risk_result_id": result["id"]}
        for result in inserted_results
        if result["matched"]
    ]


def insert_risk_alerts(
    connection: Connection,
    rows: Sequence[dict[str, object]],
) -> int:
    """Insert new investigation alerts idempotently."""
    if not rows:
        return 0

    statement = (
        insert(RiskAlert)
        .values(list(rows))
        .on_conflict_do_nothing(
            constraint="uq_risk_alerts_transaction_risk_result",
        )
        .returning(RiskAlert.id)
    )

    inserted_ids = connection.execute(statement).scalars().all()
    return len(inserted_ids)


def fetch_high_amount_rule(
    connection: Connection,
    risk_rule_id: int,
) -> RowMapping:
    """Return one active and executable high-amount rule."""
    query = select(
        RiskRule.id,
        RiskRule.threshold,
    ).where(
        RiskRule.id == risk_rule_id,
        RiskRule.is_active.is_(True),
        RiskRule.rule_type == "high_amount",
        RiskRule.threshold.is_not(None),
    )

    rule = connection.execute(query).mappings().one_or_none()

    if rule is None:
        raise ValueError(f"Active high-amount risk rule {risk_rule_id} was not found.")

    return rule


def run_high_amount_risk_pipeline(
    connection: Connection,
    risk_rule_id: int,
    batch_size: int = 1000,
) -> dict[str, int]:
    """Evaluate trusted transactions and persist results and alerts."""
    if batch_size <= 0:
        raise ValueError("Batch size must be greater than zero.")

    rule = fetch_high_amount_rule(
        connection=connection,
        risk_rule_id=risk_rule_id,
    )

    threshold = rule["threshold"]
    after_transaction_id = 0
    evaluated_count = 0
    inserted_result_count = 0
    inserted_alert_count = 0

    while True:
        transactions = fetch_transaction_batch(
            connection=connection,
            after_transaction_id=after_transaction_id,
            batch_size=batch_size,
        )

        if not transactions:
            break

        result_rows = build_risk_result_rows(
            transactions=transactions,
            risk_rule_id=risk_rule_id,
            threshold=threshold,
        )

        inserted_results = insert_risk_results(
            connection=connection,
            rows=result_rows,
        )

        alert_rows = build_risk_alert_rows(inserted_results=inserted_results)

        inserted_alert_count += insert_risk_alerts(
            connection=connection,
            rows=alert_rows,
        )

        evaluated_count += len(transactions)
        inserted_result_count += len(inserted_results)
        after_transaction_id = transactions[-1]["id"]

    return {
        "evaluated_count": evaluated_count,
        "inserted_result_count": inserted_result_count,
        "inserted_alert_count": inserted_alert_count,
    }
