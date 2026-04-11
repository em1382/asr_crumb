"""drop fit_run.summary

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-04-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("fit_run", "summary")


def downgrade() -> None:
    op.add_column(
        "fit_run",
        sa.Column(
            "summary",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )
