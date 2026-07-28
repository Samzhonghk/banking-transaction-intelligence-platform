import argparse
from pathlib import Path

from sqlalchemy import select

from banking_intelligence.core.config import Settings
from banking_intelligence.database.engine import create_database_engine
from banking_intelligence.database.models import SourceSystem
from banking_intelligence.ingestion.pipelines import (
    run_csv_transaction_pipeline,
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
    return parser


def main() -> int:
    """Run the requested command and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args()

    engine = create_database_engine(Settings())

    try:
        with engine.connect() as conn:
            source_system_id = conn.execute(
                select(SourceSystem.id).where(
                    SourceSystem.name == args.source_name,
                    SourceSystem.source_type == "csv",
                    SourceSystem.is_active.is_(True),
                )
            ).scalar_one_or_none()

        if source_system_id is None:
            parser.error(f"Active CSV source system not found: {args.source_name}")
        etl_run_id = run_csv_transaction_pipeline(
            engine=engine,
            file_path=args.file_path,
            source_system_id=source_system_id,
            pipeline_name=args.pipeline_name,
        )
        print(f"ETL run {etl_run_id} completed successfully")
        return 0
    finally:
        engine.dispose()
