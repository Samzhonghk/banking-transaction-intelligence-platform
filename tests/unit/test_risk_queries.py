from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection

from banking_intelligence.services.risk_queries import fetch_risk_alerts


def _compile_sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def test_fetch_risk_alerts_applies_filters_to_count_and_page() -> None:
    """Count and page queries should share filters and stable pagination."""
    connection = MagicMock(spec=Connection)
    total_result = MagicMock()
    total_result.scalar_one.return_value = 12
    item_result = MagicMock()
    expected_items = [{"alert_id": 99, "status": "open"}]
    item_result.mappings.return_value.all.return_value = expected_items
    connection.execute.side_effect = [total_result, item_result]

    items, total = fetch_risk_alerts(
        connection=connection,
        limit=25,
        offset=50,
        alert_status="open",
        severity="high",
        min_score=Decimal("75.00"),
    )

    count_sql = _compile_sql(connection.execute.call_args_list[0].args[0])
    page_sql = _compile_sql(connection.execute.call_args_list[1].args[0])

    for sql in (count_sql, page_sql):
        assert "risk.risk_alerts.status = 'open'" in sql
        assert "risk.risk_rules.severity = 'high'" in sql
        assert "risk.transaction_risk_results.risk_score >= 75.00" in sql

    assert "ORDER BY risk.risk_alerts.created_at DESC" in page_sql
    assert "risk.risk_alerts.id DESC" in page_sql
    assert "LIMIT 25 OFFSET 50" in page_sql
    assert items == expected_items
    assert total == 12
