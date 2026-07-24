from collections.abc import Iterator

import pytest
from sqlalchemy.engine import Connection

from banking_intelligence.core.config import Settings
from banking_intelligence.database.engine import create_database_engine


@pytest.fixture
def database_connection() -> Iterator[Connection]:
    """Provide a real database connection rolled back after each test."""

    engine = create_database_engine(Settings())

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            yield connection
        finally:
            transaction.rollback()

    engine.dispose()
