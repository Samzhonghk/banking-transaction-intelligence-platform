from datetime import timedelta

import pendulum
from airflow.sdk import dag, task


@dag(
    dag_id="banking_intelligence_daily",
    schedule="0 2 * * *",
    start_date=pendulum.datetime(
        2026,
        1,
        1,
        tz="Pacific/Auckland",
    ),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "data-engineering",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=[
        "banking-intelligence",
        "data-engineering",
    ],
)
def banking_intelligence_daily() -> None:
    """Define the scheduled banking intelligence workflow."""

    @task.bash
    def ingest_csv_transactions() -> str:
        """Run the existing CSV transaction ingestion CLI."""
        return (
            "/opt/airflow/project-venv/bin/banking-intelligence ingest-csv "
            "/opt/airflow/project/data/samples/demo_transactions.csv "
            "--source-name demo-csv "
            "--pipeline-name airflow-daily-csv"
        )

    @task.bash
    def evaluate_transaction_risk() -> str:
        """Evaluate trusted transactions using the configured risk rule."""
        return (
            "/opt/airflow/project-venv/bin/banking-intelligence evaluate-risk "
            "--rule-id ${RISK_RULE_ID} "
            "--batch-size 1000"
        )

    @task.bash
    def build_analytics_warehouse() -> str:
        """Build and test the dbt analytics warehouse."""
        return (
            "/opt/airflow/project-venv/bin/dbt build "
            "--project-dir /opt/airflow/project/warehouse "
            "--profiles-dir /opt/airflow/project/warehouse"
        )

    ingest_task = ingest_csv_transactions()
    evaluate_task = evaluate_transaction_risk()
    dbt_task = build_analytics_warehouse()
    ingest_task >> evaluate_task >> dbt_task


banking_intelligence_daily()
