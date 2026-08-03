from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.engine import Connection, RowMapping

from banking_intelligence.database.models import Transaction


def fetch_transactions(
    connection: Connection,
    limit: int,
    offset: int,
) -> tuple[Sequence[RowMapping], int]:
    """Return one transaction page and the total available row count."""
    total = connection.execute(
        select(func.count()).select_from(Transaction)
    ).scalar_one()

    query = (
        select(
            Transaction.id,
            Transaction.account_id,
            Transaction.external_transaction_id,
            Transaction.amount,
            Transaction.currency_code,
            Transaction.description,
            Transaction.transaction_timestamp,
        )
        .order_by(
            Transaction.transaction_timestamp.desc(),
            Transaction.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    items = connection.execute(query).mappings().all()
    return items, total
