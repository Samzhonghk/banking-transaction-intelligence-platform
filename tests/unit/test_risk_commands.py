from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection

from banking_intelligence.services.risk_commands import transition_risk_alert


def _compile_sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def test_transition_risk_alert_returns_none_when_alert_is_missing() -> None:
    connection = MagicMock(spec=Connection)
    select_result = MagicMock()
    select_result.scalar_one_or_none.return_value = None
    connection.execute.return_value = select_result

    result = transition_risk_alert(
        connection=connection,
        alert_id=404,
        target_status="investigating",
    )

    select_sql = _compile_sql(connection.execute.call_args.args[0])

    assert result is None
    assert "WHERE risk.risk_alerts.id = 404" in select_sql
    assert "FOR UPDATE" in select_sql
    connection.execute.assert_called_once()


def test_transition_risk_alert_rejects_invalid_transition_before_update() -> None:
    connection = MagicMock(spec=Connection)
    select_result = MagicMock()
    select_result.scalar_one_or_none.return_value = "resolved"
    connection.execute.return_value = select_result

    with pytest.raises(ValueError, match="Cannot transition risk alert"):
        transition_risk_alert(
            connection=connection,
            alert_id=12,
            target_status="open",
        )

    connection.execute.assert_called_once()


def test_transition_risk_alert_updates_terminal_status_and_returns_row() -> None:
    connection = MagicMock(spec=Connection)
    select_result = MagicMock()
    select_result.scalar_one_or_none.return_value = "investigating"
    update_result = MagicMock()
    expected_row = {
        "alert_id": 12,
        "status": "resolved",
        "resolution_outcome": "confirmed_risk",
    }
    update_result.mappings.return_value.one.return_value = expected_row
    connection.execute.side_effect = [select_result, update_result]

    result = transition_risk_alert(
        connection=connection,
        alert_id=12,
        target_status="resolved",
        assigned_to="analyst@example.com",
        resolution_outcome="confirmed_risk",
        resolution_note="Confirmed after investigation.",
    )

    update_sql = _compile_sql(connection.execute.call_args_list[1].args[0])

    assert "UPDATE risk.risk_alerts SET" in update_sql
    assert "status='resolved'" in update_sql
    assert "assigned_to='analyst@example.com'" in update_sql
    assert "resolution_outcome='confirmed_risk'" in update_sql
    assert "resolved_at=now()" in update_sql
    assert "RETURNING risk.risk_alerts.id AS alert_id" in update_sql
    assert result == expected_row
