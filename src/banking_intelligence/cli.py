import argparse
from pathlib import Path

from sqlalchemy import select

from banking_intelligence.core.config import Settings
from banking_intelligence.database.engine import create_database_engine
from banking_intelligence.database.models import SourceSystem
from banking_intelligence.ingestion.extractors import build_retry_session
from banking_intelligence.ingestion.pipelines import (
    run_api_transaction_pipeline,
    run_csv_transaction_pipeline,
)
from banking_intelligence.risk.pipelines.high_amount import (
    run_high_amount_risk_pipeline,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for ingestion operations."""
    parser = argparse.ArgumentParser(
        prog="banking-intelligence",
        description="Run banking transaction intelligence workflows",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    ingest_parser = subparsers.add_parser(
        "ingest-csv",
        help="Ingest one transaction CSV file.",
    )

    ingest_parser.add_argument(
        "--source-name",
        required=True,
        help="Registered source-system name",
    )

    ingest_parser.add_argument(
        "--pipeline-name",
        default="csv-transaction-ingestion",
        help="Name recorded in ETL run history",
    )

    ingest_parser.add_argument(
        "file_path",
        type=Path,
        help="Path to the transaction CSV file",
    )

    api_parser = subparsers.add_parser(
        "ingest-api",
        help="Ingest transactions from a paginated API",
    )

    api_parser.add_argument(
        "--source-name",
        required=True,
        help="Registered API source-system name",
    )

    api_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of transaction records requested per page.",
    )

    api_parser.add_argument(
        "--pipeline-name",
        default="api-transaction-ingestion",
        help="Name recorded in ETL run history",
    )

    risk_parser = subparsers.add_parser(
        "evaluate-risk",
        help="Evaluate trusted transactions with a risk rule.",
    )

    risk_parser.add_argument(
        "--rule-id",
        type=int,
        required=True,
        help="Active high-amount risk-rule ID.",
    )

    risk_parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of trusted transactions evaluated per batch.",
    )
    return parser


def main() -> int:
    """Run the requested command and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args()

    settings = Settings()
    engine = create_database_engine(settings)

    try:
        if args.command == "evaluate-risk":
            with engine.begin() as connection:
                metrics = run_high_amount_risk_pipeline(
                    connection=connection,
                    risk_rule_id=args.rule_id,
                    batch_size=args.batch_size,
                )

            print(
                "Risk evaluation completed: "
                f"evaluated={metrics['evaluated_count']}, "
                f"inserted_results={metrics['inserted_result_count']}, "
                f"inserted_alerts={metrics['inserted_alert_count']}"
            )
            return 0

        source_type = "csv" if args.command == "ingest-csv" else "api"
        with engine.connect() as conn:
            source_system = conn.execute(
                select(SourceSystem.id, SourceSystem.base_url).where(
                    SourceSystem.name == args.source_name,
                    SourceSystem.source_type == source_type,
                    SourceSystem.is_active.is_(True),
                )
            ).one_or_none()

        if source_system is None:
            parser.error(
                f"Active {source_type.upper()} source system not found: "
                f"{args.source_name}"
            )

        if args.command == "ingest-csv":
            etl_run_id = run_csv_transaction_pipeline(
                engine=engine,
                file_path=args.file_path,
                source_system_id=source_system.id,
                pipeline_name=args.pipeline_name,
            )
        else:
            if not source_system.base_url:
                parser.error(f"API source system has no base URL: {args.source_name}")

            session = build_retry_session()

            try:
                if settings.transaction_api_token is not None:
                    token = settings.transaction_api_token.get_secret_value().strip()

                    if token:
                        session.headers["Authorization"] = f"Bearer {token}"

                etl_run_id = run_api_transaction_pipeline(
                    engine=engine,
                    url=source_system.base_url,
                    source_system_id=source_system.id,
                    session=session,
                    page_size=args.page_size,
                    pipeline_name=args.pipeline_name,
                )
            finally:
                session.close()

        print(f"ETL run {etl_run_id} completed successfully")
        return 0
    finally:
        engine.dispose()
