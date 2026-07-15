"""create application schemas

Revision ID: ca2959e45852
Revises:
Create Date: 2026-07-15 17:48:32.463881

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca2959e45852"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create application-managed PostgreSQL schemas."""
    op.execute(sa.schema.CreateSchema("ingestion"))
    op.execute(sa.schema.CreateSchema("core"))
    op.execute(sa.schema.CreateSchema("risk"))


def downgrade() -> None:
    """Drop application-managed PostgreSQL schemas."""
    op.execute(sa.schema.DropSchema("risk"))
    op.execute(sa.schema.DropSchema("core"))
    op.execute(sa.schema.DropSchema("ingestion"))
