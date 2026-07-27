from unittest.mock import Mock

import pandas as pd
from sqlalchemy.engine import Connection

from banking_intelligence.ingestion.loaders import load_accepted_transactions


def test_load_accepted_transactions_skips_empty_dataframe() -> None:
    """An empty accepted batch should not access PostgreSQL."""
    connection = Mock(spec=Connection)

    loaded_count = load_accepted_transactions(
        connection=connection,
        accepted_df=pd.DataFrame(),
        etl_run_id=42,
    )

    assert loaded_count == 0
    connection.execute.assert_not_called()
