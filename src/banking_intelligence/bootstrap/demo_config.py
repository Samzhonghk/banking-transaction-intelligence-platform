from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from banking_intelligence.database.models import RiskRule, SourceSystem

DEMO_SOURCE_NAME = "demo-csv"
DEMO_RISK_RULE_CODE = "HIGH_AMOUNT_DEMO"
DEMO_RISK_RULE_VERSION = 1


def bootstrap_demo_configuration(connection: Connection) -> dict[str, int]:
    """Create or refresh the configuration required by the demo ETL workflow.

    The caller owns the surrounding transaction. PostgreSQL upserts make repeated
    deployment runs safe while returning the IDs needed by later job steps.
    """
    source_insert = insert(SourceSystem).values(
        name=DEMO_SOURCE_NAME,
        source_type="csv",
        description="Deterministic CSV source for the cloud ETL demonstration",
        base_url=None,
        is_active=True,
    )
    source_statement = source_insert.on_conflict_do_update(
        index_elements=[SourceSystem.name],
        set_={
            "source_type": source_insert.excluded.source_type,
            "description": source_insert.excluded.description,
            "base_url": source_insert.excluded.base_url,
            "is_active": source_insert.excluded.is_active,
            "updated_at": func.now(),
        },
    ).returning(SourceSystem.id)

    source_system_id = connection.execute(source_statement).scalar_one()

    risk_rule_insert = insert(RiskRule).values(
        code=DEMO_RISK_RULE_CODE,
        name="High amount demo rule",
        description="Flags transactions above NZD 1000 for portfolio demonstration",
        rule_type="high_amount",
        severity="high",
        threshold=Decimal("1000.00"),
        parameters={},
        version=DEMO_RISK_RULE_VERSION,
        is_active=True,
    )
    risk_rule_statement = risk_rule_insert.on_conflict_do_update(
        index_elements=[RiskRule.code, RiskRule.version],
        set_={
            "name": risk_rule_insert.excluded.name,
            "description": risk_rule_insert.excluded.description,
            "rule_type": risk_rule_insert.excluded.rule_type,
            "severity": risk_rule_insert.excluded.severity,
            "threshold": risk_rule_insert.excluded.threshold,
            "parameters": risk_rule_insert.excluded.parameters,
            "is_active": risk_rule_insert.excluded.is_active,
            "updated_at": func.now(),
        },
    ).returning(RiskRule.id)

    risk_rule_id = connection.execute(risk_rule_statement).scalar_one()

    return {
        "source_system_id": source_system_id,
        "risk_rule_id": risk_rule_id,
    }
