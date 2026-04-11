"""initial_schema

Revision ID: c79ab6ebbafd
Revises:
Create Date: 2026-04-11 09:23:23.356428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c79ab6ebbafd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "recipe",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Text(), nullable=False),
        sa.Column("recipe_name", sa.Text(), nullable=False),
        sa.Column("status_expectation", sa.Text(), nullable=False),
        sa.Column("ingredients", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("recipe")
