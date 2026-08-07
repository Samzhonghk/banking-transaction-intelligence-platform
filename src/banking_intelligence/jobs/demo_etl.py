import subprocess
from pathlib import Path

from sqlalchemy.engine import Engine

from banking_intelligence.bootstrap import bootstrap_demo_configuration
from banking_intelligence.core.config import Settings
from banking_intelligence.database.engine import create_database_engine
from banking_intelligence.ingestion.pipelines import run_csv_transaction_pipeline
from banking_intelligence.risk.pipelines.high_amount import (
    run_high_amount_risk_pipeline,
)

DEFAULT_CSV_PATH = Path("/app/data/samples/demo_transactions.csv")
DEFAULT_WAREHOUSE_PATH = Path("/app/warehouse")


def run_demo_etl_job(
    *,
    engine: Engine,
    csv_path: Path = DEFAULT_CSV_PATH,
    warehouse_path: Path = DEFAULT_WAREHOUSE_PATH,
) -> dict[str, int]:
    """Run the deterministic cloud demonstration workflow from start to finish."""
    with engine.begin() as connection:
        identifiers = bootstrap_demo_configuration(connection)

    etl_run_id = run_csv_transaction_pipeline(
        engine=engine,
        file_path=csv_path,
        source_system_id=identifiers["source_system_id"],
        pipeline_name="azure-container-apps-job-demo",
    )

    with engine.begin() as connection:
        risk_metrics = run_high_amount_risk_pipeline(
            connection=connection,
            risk_rule_id=identifiers["risk_rule_id"],
            batch_size=1000,
        )

    subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            str(warehouse_path),
            "--profiles-dir",
            str(warehouse_path),
        ],
        check=True,
    )

    return {
        "etl_run_id": etl_run_id,
        "risk_rule_id": identifiers["risk_rule_id"],
        "evaluated_count": risk_metrics["evaluated_count"],
        "inserted_result_count": risk_metrics["inserted_result_count"],
        "inserted_alert_count": risk_metrics["inserted_alert_count"],
    }


def main() -> int:
    """Run the demo ETL job using environment-based cloud configuration."""
    engine = create_database_engine(Settings())

    try:
        metrics = run_demo_etl_job(engine=engine)
    finally:
        engine.dispose()

    print(
        "Demo ETL job completed: "
        f"etl_run_id={metrics['etl_run_id']}, "
        f"risk_rule_id={metrics['risk_rule_id']}, "
        f"evaluated={metrics['evaluated_count']}, "
        f"inserted_results={metrics['inserted_result_count']}, "
        f"inserted_alerts={metrics['inserted_alert_count']}"
    )
    return 0
