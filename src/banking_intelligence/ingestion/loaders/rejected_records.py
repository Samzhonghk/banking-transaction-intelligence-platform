import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.engine import Connection

from banking_intelligence.database.models import RawTransaction, RejectedRecord


def load_rejected_records(
    connection: Connection,
    rejected_dataframe: pd.DataFrame,
    etl_run_id: int,
) -> int:
    """Persist validation failures linked to their raw transactions."""
    if rejected_dataframe.empty:
        return 0

    source_row_numbers = [int(index) + 1 for index in rejected_dataframe.index]

    raw_transactions = connection.execute(
        select(
            RawTransaction.id,
            RawTransaction.source_row_number,
        ).where(
            RawTransaction.etl_run_id == etl_run_id,
            RawTransaction.source_row_number.in_(source_row_numbers),
        )
    ).all()

    raw_id_by_source_row = {row.source_row_number: row.id for row in raw_transactions}

    missing_source_rows = sorted(set(source_row_numbers) - raw_id_by_source_row.keys())

    if missing_source_rows:
        raise ValueError(
            f"Raw transactions not found for source rows: {missing_source_rows}"
        )

    rows = []
    for index, rejected_record in rejected_dataframe.iterrows():
        source_row_number = int(index) + 1

        rejection_reasons = [
            reason
            for reason in str(rejected_record["rejection_reason"]).split(";")
            if reason
        ]

        rows.append(
            {
                "raw_transaction_id": raw_id_by_source_row[source_row_number],
                "rejection_reasons": rejection_reasons,
            }
        )

    connection.execute(
        insert(RejectedRecord),
        rows,
    )

    return len(rows)
