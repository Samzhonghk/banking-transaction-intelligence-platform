import pandas as pd
from sqlalchemy import insert
from sqlalchemy.engine import Connection

from banking_intelligence.database.models import RawTransaction
from banking_intelligence.ingestion.fingerprints import build_record_fingerprint


def load_raw_transactions(
    connection: Connection,
    dataframe: pd.DataFrame,
    etl_run_id: int,
) -> int:
    """Bulk-insert raw records within a caller-managed transaction."""
    raw_records = dataframe.to_dict(orient="records")
    rows = []
    for source_row_number, raw_record in enumerate(raw_records, start=1):
        rows.append(
            {
                "etl_run_id": etl_run_id,
                "source_row_number": source_row_number,
                "raw_payload": raw_record,
                "record_fingerprint": build_record_fingerprint(raw_record),
            }
        )

    if not rows:
        return 0

    connection.execute(insert(RawTransaction), rows)
    return len(rows)
