"""add fit run and fit recommendation

Revision ID: f8a9b0c1d2e3
Revises: c79ab6ebbafd
Create Date: 2026-04-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, Sequence[str], None] = "c79ab6ebbafd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fit_run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("agent_model", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("passed", "failed", "needs_review", name="fitstatus"),
            nullable=False,
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("violations", sa.JSON(), nullable=True),
        sa.Column("normalized_recipe", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipe.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fit_run_recipe_id"), "fit_run", ["recipe_id"], unique=False
    )
    op.create_index(op.f("ix_fit_run_status"), "fit_run", ["status"], unique=False)

    op.create_table(
        "fit_recommendation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fit_run_id", sa.Integer(), nullable=False),
        sa.Column(
            "severity",
            sa.Enum("info", "warning", "error", name="recommendationseverity"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("suggested_change", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["fit_run_id"], ["fit_run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fit_recommendation_fit_run_id"),
        "fit_recommendation",
        ["fit_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fit_recommendation_severity"),
        "fit_recommendation",
        ["severity"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_fit_recommendation_severity"), table_name="fit_recommendation"
    )
    op.drop_index(
        op.f("ix_fit_recommendation_fit_run_id"), table_name="fit_recommendation"
    )
    op.drop_table("fit_recommendation")

    op.drop_index(op.f("ix_fit_run_status"), table_name="fit_run")
    op.drop_index(op.f("ix_fit_run_recipe_id"), table_name="fit_run")
    op.drop_table("fit_run")

    sa.Enum(name="fitstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="recommendationseverity").drop(op.get_bind(), checkfirst=True)
