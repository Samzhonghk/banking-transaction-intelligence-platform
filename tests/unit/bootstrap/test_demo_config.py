from unittest.mock import MagicMock, Mock

from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection

from banking_intelligence.bootstrap.demo_config import (
    bootstrap_demo_configuration,
)


def test_bootstrap_demo_configuration_upserts_and_returns_ids() -> None:
    """Repeated-safe statements should return IDs required by the ETL job."""
    connection = MagicMock(spec=Connection)
    source_result = Mock()
    source_result.scalar_one.return_value = 17
    rule_result = Mock()
    rule_result.scalar_one.return_value = 23
    connection.execute.side_effect = [source_result, rule_result]

    identifiers = bootstrap_demo_configuration(connection)

    assert identifiers == {
        "source_system_id": 17,
        "risk_rule_id": 23,
    }
    assert connection.execute.call_count == 2

    source_statement = connection.execute.call_args_list[0].args[0]
    source_sql = str(
        source_statement.compile(dialect=postgresql.dialect())
    )
    assert "ON CONFLICT (name) DO UPDATE" in source_sql
    assert "RETURNING ingestion.source_systems.id" in source_sql

    rule_statement = connection.execute.call_args_list[1].args[0]
    rule_sql = str(rule_statement.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (code, version) DO UPDATE" in rule_sql
    assert "RETURNING risk.risk_rules.id" in rule_sql
