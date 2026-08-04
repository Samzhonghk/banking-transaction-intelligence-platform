from collections.abc import Sequence
from datetime import date

from sqlalchemy import (
    Date,
    Integer,
    Numeric,
    String,
    column,
    func,
    select,
    table,
)
from sqlalchemy.engine import Connection, RowMapping

daily_transaction_summary = table(
    "mart_daily_transaction_summary",
    column("transaction_date", Date),
    column("currency_code", String(3)),
    column("transaction_count", Integer),
    column("active_account_count", Integer),
    column("total_amount", Numeric),
    column("average_amount", Numeric),
    column("minimum_amount", Numeric),
    column("maximum_amount", Numeric),
    schema="analytics",
)


def fetch_daily_transaction_summaries(
    connection: Connection,
    limit: int,
    offset: int,
    start_date: date | None = None,
    end_date: date | None = None,
    currency_code: str | None = None,
) -> tuple[Sequence[RowMapping], int]:
    """Return one filtered page of daily analytical transaction metrics."""
    filters = []
    if start_date is not None:
        filters.append(daily_transaction_summary.c.transaction_date >= start_date)

    if end_date is not None:
        filters.append(daily_transaction_summary.c.transaction_date <= end_date)

    if currency_code is not None:
        filters.append(daily_transaction_summary.c.currency_code == currency_code)

    total = connection.execute(
        select(func.count()).select_from(daily_transaction_summary).where(*filters)
    ).scalar_one()

    query = (
        select(*daily_transaction_summary.c)
        .where(*filters)
        .order_by(
            daily_transaction_summary.c.transaction_date.desc(),
            daily_transaction_summary.c.currency_code.asc(),
        )
        .limit(limit)
        .offset(offset)
    )

    items = connection.execute(query).mappings().all()
    return items, total
