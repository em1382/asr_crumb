from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlmodel import Field, Column, JSON, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FitStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    needs_review = "needs_review"


class RecommendationSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class Recipe(SQLModel, table=True):
    __tablename__ = "recipe"

    id: int | None = Field(default=None, primary_key=True)
    batch_id: str = Field(unique=True)
    recipe_name: str
    # This is for audit purposes only
    status_expectation: str
    ingredients: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    fit_runs: list["FitRun"] = Relationship(
        back_populates="recipe",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class FitRun(SQLModel, table=True):
    __tablename__ = "fit_run"

    id: int | None = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    agent_model: str | None = None
    status: FitStatus = Field(default=FitStatus.needs_review, index=True)
    summary: str | None = None
    violations: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))
    normalized_recipe: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON)
    )

    recipe: Recipe | None = Relationship(back_populates="fit_runs")
    recommendations: list["FitRecommendation"] = Relationship(
        back_populates="fit_run",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class FitRecommendation(SQLModel, table=True):
    __tablename__ = "fit_recommendation"

    id: int | None = Field(default=None, primary_key=True)
    fit_run_id: int = Field(foreign_key="fit_run.id", index=True)
    severity: RecommendationSeverity = Field(
        default=RecommendationSeverity.info, index=True
    )
    message: str
    reasoning: str | None = None
    suggested_change: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON)
    )

    fit_run: FitRun | None = Relationship(back_populates="recommendations")
