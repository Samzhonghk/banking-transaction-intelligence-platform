from collections.abc import Callable
from pathlib import Path

import pandas as pd
import requests
from sqlalchemy import func, insert, update
from sqlalchemy.engine import Engine

from banking_intelligence.database.models import EtlRun
from banking_intelligence.ingestion.extractors.api import (
    extract_api_transactions,
)
from banking_intelligence.ingestion.extractors.csv import extract_csv
from banking_intelligence.ingestion.loaders import (
    load_accepted_transactions,
    load_raw_transactions,
    load_rejected_records,
)
from banking_intelligence.ingestion.transformers.transactions import (
    transform_transactions,
)
from banking_intelligence.ingestion.validators.transactions import (
    split_transactions,
)


def _run_transaction_pipeline(
    engine: Engine,
    extractor: Callable[[], pd.DataFrame],
    source_system_id: int,
    pipeline_name: str,
) -> int:
    """Run shared transaction processing for one source-specific extractor."""
    with engine.begin() as conn:
        etl_run_id = conn.execute(
            insert(EtlRun)
            .values(
                source_system_id=source_system_id,
                pipeline_name=pipeline_name,
                status="running",
            )
            .returning(EtlRun.id)
        ).scalar_one()

    try:
        raw_df = extractor()
        transformed_df = transform_transactions(raw_df)
        accepted_df, rejected_df = split_transactions(transformed_df)

        with engine.begin() as conn:
            extracted_count = load_raw_transactions(
                connection=conn,
                dataframe=raw_df,
                etl_run_id=etl_run_id,
            )

            accepted_count = load_accepted_transactions(
                connection=conn,
                accepted_df=accepted_df,
                etl_run_id=etl_run_id,
            )

            rejected_count = load_rejected_records(
                connection=conn,
                rejected_dataframe=rejected_df,
                etl_run_id=etl_run_id,
            )

            conn.execute(
                update(EtlRun)
                .where(EtlRun.id == etl_run_id)
                .values(
                    status="succeeded",
                    finished_at=func.now(),
                    extracted_count=extracted_count,
                    accepted_count=accepted_count,
                    rejected_count=rejected_count,
                    error_message=None,
                )
            )

    except Exception as exc:
        with engine.begin() as conn:
            conn.execute(
                update(EtlRun)
                .where(EtlRun.id == etl_run_id)
                .values(
                    status="failed",
                    finished_at=func.now(),
                    error_message=str(exc),
                )
            )
        raise

    return etl_run_id


def run_csv_transaction_pipeline(
    engine: Engine,
    file_path: Path,
    source_system_id: int,
    pipeline_name: str = "csv-transaction-ingestion",
) -> int:
    """Run one CSV ingestion batch and return its ETL run ID."""
    return _run_transaction_pipeline(
        engine=engine,
        extractor=lambda: extract_csv(file_path),
        source_system_id=source_system_id,
        pipeline_name=pipeline_name,
    )


def run_api_transaction_pipeline(
    engine: Engine,
    url: str,
    source_system_id: int,
    session: requests.Session | None = None,
    page_size: int = 100,
    timeout: tuple[float, float] = (3.05, 30.0),
    max_pages: int = 1000,
    pipeline_name: str = "api-transaction-ingestion",
) -> int:
    """Run one paginated API ingestion batch and return its ETL run ID."""
    return _run_transaction_pipeline(
        engine=engine,
        extractor=lambda: extract_api_transactions(
            url=url,
            session=session,
            page_size=page_size,
            timeout=timeout,
            max_pages=max_pages,
        ),
        source_system_id=source_system_id,
        pipeline_name=pipeline_name,
    )
