from pathlib import Path
from unittest.mock import MagicMock, Mock, call

from sqlalchemy.engine import Connection, Engine

from banking_intelligence.jobs import demo_etl


def test_run_demo_etl_job_runs_each_stage_in_order(monkeypatch) -> None:
    """The job should compose existing pipelines and pass bootstrap IDs onward."""
    engine = MagicMock(spec=Engine)
    connection = MagicMock(spec=Connection)
    engine.begin.return_value.__enter__.return_value = connection
    events: list[str] = []

    bootstrap = Mock(
        side_effect=lambda _: (
            events.append("bootstrap")
            or {"source_system_id": 17, "risk_rule_id": 23}
        )
    )
    ingest = Mock(side_effect=lambda **_: events.append("ingest") or 31)
    risk = Mock(
        side_effect=lambda **_: events.append("risk")
        or {
            "evaluated_count": 11,
            "inserted_result_count": 11,
            "inserted_alert_count": 2,
        }
    )
    dbt_run = Mock(side_effect=lambda *_, **__: events.append("dbt"))

    monkeypatch.setattr(demo_etl, "bootstrap_demo_configuration", bootstrap)
    monkeypatch.setattr(demo_etl, "run_csv_transaction_pipeline", ingest)
    monkeypatch.setattr(demo_etl, "run_high_amount_risk_pipeline", risk)
    monkeypatch.setattr(demo_etl.subprocess, "run", dbt_run)

    metrics = demo_etl.run_demo_etl_job(
        engine=engine,
        csv_path=Path("demo.csv"),
        warehouse_path=Path("warehouse"),
    )

    assert events == ["bootstrap", "ingest", "risk", "dbt"]
    assert metrics == {
        "etl_run_id": 31,
        "risk_rule_id": 23,
        "evaluated_count": 11,
        "inserted_result_count": 11,
        "inserted_alert_count": 2,
    }
    assert engine.begin.call_args_list == [call(), call()]
    bootstrap.assert_called_once_with(connection)
    ingest.assert_called_once_with(
        engine=engine,
        file_path=Path("demo.csv"),
        source_system_id=17,
        pipeline_name="azure-container-apps-job-demo",
    )
    risk.assert_called_once_with(
        connection=connection,
        risk_rule_id=23,
        batch_size=1000,
    )
    dbt_run.assert_called_once_with(
        [
            "dbt",
            "build",
            "--project-dir",
            "warehouse",
            "--profiles-dir",
            "warehouse",
        ],
        check=True,
    )
