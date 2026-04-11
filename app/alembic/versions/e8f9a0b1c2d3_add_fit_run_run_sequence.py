"""add fit_run.run_sequence per recipe

Revision ID: e8f9a0b1c2d3
Revises: c7d8e9f0a1b2
Create Date: 2026-04-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fit_run",
        sa.Column("run_sequence", sa.Integer(), nullable=True),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE fit_run
            SET run_sequence = (
                SELECT COUNT(*)
                FROM fit_run AS f2
                WHERE f2.recipe_id = fit_run.recipe_id
                  AND f2.id <= fit_run.id
            )
            """
        )
    )
    op.alter_column("fit_run", "run_sequence", nullable=False)
    op.create_unique_constraint(
        "uq_fit_run_recipe_run_sequence",
        "fit_run",
        ["recipe_id", "run_sequence"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_fit_run_recipe_run_sequence",
        "fit_run",
        type_="unique",
    )
    op.drop_column("fit_run", "run_sequence")
