"""Transaction ingestion pipelines."""

from banking_intelligence.ingestion.pipelines.transactions import (
    run_csv_transaction_pipeline,
)

__all__ = ["run_csv_transaction_pipeline"]
