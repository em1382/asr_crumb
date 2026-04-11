"""rename suggested_change to recommendations; drop fit_run JSON columns

Revision ID: a1b2c3d4e5f6
Revises: 559e6298f3eb
Create Date: 2026-04-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "559e6298f3eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("fit_run", "violations")
    op.drop_column("fit_run", "normalized_recipe")
    op.alter_column(
        "fit_recommendation",
        "suggested_change",
        new_column_name="recommendations",
        existing_type=sa.JSON(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "fit_recommendation",
        "recommendations",
        new_column_name="suggested_change",
        existing_type=sa.JSON(),
        existing_nullable=True,
    )
    op.add_column(
        "fit_run",
        sa.Column("violations", sa.JSON(), nullable=True),
    )
    op.add_column(
        "fit_run",
        sa.Column("normalized_recipe", sa.JSON(), nullable=True),
    )
