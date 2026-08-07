from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.engine import Connection

from banking_intelligence.bootstrap.demo_config import (
    DEMO_RISK_RULE_CODE,
    DEMO_RISK_RULE_VERSION,
    DEMO_SOURCE_NAME,
    bootstrap_demo_configuration,
)
from banking_intelligence.database.models import RiskRule, SourceSystem


def test_bootstrap_demo_configuration_is_idempotent(
    database_connection: Connection,
) -> None:
    """Repeated bootstraps should refresh one configuration pair in place."""
    first_identifiers = bootstrap_demo_configuration(database_connection)
    second_identifiers = bootstrap_demo_configuration(database_connection)

    assert second_identifiers == first_identifiers

    source_system = database_connection.execute(
        select(
            SourceSystem.id,
            SourceSystem.source_type,
            SourceSystem.is_active,
        ).where(SourceSystem.name == DEMO_SOURCE_NAME)
    ).mappings().one()
    assert source_system["id"] == first_identifiers["source_system_id"]
    assert source_system["source_type"] == "csv"
    assert source_system["is_active"] is True

    risk_rule = database_connection.execute(
        select(
            RiskRule.id,
            RiskRule.rule_type,
            RiskRule.severity,
            RiskRule.threshold,
            RiskRule.is_active,
        ).where(
            RiskRule.code == DEMO_RISK_RULE_CODE,
            RiskRule.version == DEMO_RISK_RULE_VERSION,
        )
    ).mappings().one()
    assert risk_rule["id"] == first_identifiers["risk_rule_id"]
    assert risk_rule["rule_type"] == "high_amount"
    assert risk_rule["severity"] == "high"
    assert risk_rule["threshold"] == Decimal("1000.00")
    assert risk_rule["is_active"] is True
