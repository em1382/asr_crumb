"""add fitstatus pending

Revision ID: 2a3b4c5d6e7f
Revises: f8a9b0c1d2e3
Create Date: 2026-04-11 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "2a3b4c5d6e7f"
down_revision: Union[str, Sequence[str], None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL 11+ allows ADD VALUE inside a transaction.
    op.execute("ALTER TYPE fitstatus ADD VALUE 'pending'")


def downgrade() -> None:
    # Dropping a label from a PostgreSQL enum requires recreating the type;
    # omitting destructive downgrade for this additive change.
    pass
