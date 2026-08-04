from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.engine import Connection, RowMapping

from banking_intelligence.database.models import (
    RiskAlert,
    RiskRule,
    Transaction,
    TransactionRiskResult,
)


def fetch_risk_alerts(
    connection: Connection,
    limit: int,
    offset: int,
    alert_status: str | None = None,
    severity: str | None = None,
    min_score: Decimal | None = None,
) -> tuple[Sequence[RowMapping], int]:
    """Return one filtered page of investigation alerts."""
    filters = []
    if alert_status is not None:
        filters.append(RiskAlert.status == alert_status)

    if severity is not None:
        filters.append(RiskRule.severity == severity)

    if min_score is not None:
        filters.append(TransactionRiskResult.risk_score >= min_score)

    total = connection.execute(
        select(func.count())
        .select_from(RiskAlert)
        .join(
            TransactionRiskResult,
            TransactionRiskResult.id == RiskAlert.transaction_risk_result_id,
        )
        .join(
            Transaction,
            Transaction.id == TransactionRiskResult.transaction_id,
        )
        .join(RiskRule, RiskRule.id == TransactionRiskResult.risk_rule_id)
        .where(*filters)
    ).scalar_one()

    query = (
        select(
            RiskAlert.id.label("alert_id"),
            RiskAlert.status,
            RiskAlert.assigned_to,
            RiskAlert.created_at,
            TransactionRiskResult.id.label("risk_result_id"),
            TransactionRiskResult.risk_score,
            TransactionRiskResult.evidence,
            Transaction.id.label("transaction_id"),
            Transaction.external_transaction_id,
            Transaction.amount,
            Transaction.currency_code,
            Transaction.transaction_timestamp,
            RiskRule.id.label("risk_rule_id"),
            RiskRule.code.label("rule_code"),
            RiskRule.name.label("rule_name"),
            RiskRule.version.label("rule_version"),
            RiskRule.severity,
        )
        .join(
            TransactionRiskResult,
            TransactionRiskResult.id == RiskAlert.transaction_risk_result_id,
        )
        .join(Transaction, Transaction.id == TransactionRiskResult.transaction_id)
        .join(
            RiskRule,
            RiskRule.id == TransactionRiskResult.risk_rule_id,
        )
        .where(*filters)
        .order_by(
            RiskAlert.created_at.desc(),
            RiskAlert.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    items = connection.execute(query).mappings().all()

    return items, total
