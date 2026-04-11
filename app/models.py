from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import ConfigDict
from sqlalchemy import Column, Enum as SAEnum
from sqlmodel import Field, DateTime, JSON, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FitStatus(str, Enum):
    pending = "pending"
    passed = "passed"
    failed = "failed"
    needs_review = "needs_review"


class RecommendationSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class RecipeBase(SQLModel):
    """
    Shared scalar fields for the persisted `Recipe` row and API schemas
    (e.g. `RecipePublic`). Subclass with `table=True` for the ORM model or
    without for read/create payloads.
    """

    recipe_name: str
    batch_id: str = Field(index=True, unique=True)
    status_expectation: str  # audit only
    ingredients: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )


class Recipe(RecipeBase, table=True):
    __tablename__ = "recipe"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    updated_at: datetime | None = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )


class RecipeCreate(RecipeBase):
    """Create recipe payload."""

    model_config = ConfigDict(extra="forbid")


class RecipePublic(RecipeBase):
    """Returned recipe shape: base fields plus server-managed columns."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredients: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class RecipesPublic(SQLModel):
    data: list[RecipePublic]
    count: int


class Message(SQLModel):
    """
    Generic message response.
    """
    message: str


class FitRun(SQLModel, table=True):
    """One agent/fit pass for a recipe (e.g. recommendations toward fit-to-standard)."""

    __tablename__ = "fit_run"

    id: int | None = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id", index=True)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )
    agent_model: str | None = None
    status: FitStatus = Field(
        sa_column=Column(
            SAEnum(
                FitStatus,
                name="fitstatus",
                native_enum=True,
                create_type=False,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=False,
        )
    )
    summary: str | None = None
    violations: list[Any] | dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    normalized_recipe: dict[str, Any] | list[Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


class FitRecommendation(SQLModel, table=True):
    """Structured recommendation line items for a fit run."""

    __tablename__ = "fit_recommendation"

    id: int | None = Field(default=None, primary_key=True)
    fit_run_id: int = Field(foreign_key="fit_run.id", index=True)
    severity: RecommendationSeverity = Field(
        sa_column=Column(
            SAEnum(
                RecommendationSeverity,
                name="recommendationseverity",
                native_enum=True,
                create_type=False,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=False,
        )
    )
    message: str
    reasoning: str | None = None
    suggested_change: dict[str, Any] | list[Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


class FitRecommendationPublic(SQLModel):
    """API shape for a stored recommendation (agent output lives here)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fit_run_id: int
    severity: RecommendationSeverity
    message: str
    reasoning: str | None = None
    suggested_change: dict[str, Any] | list[Any] | None = None


class FitRunPublic(SQLModel):
    """API shape for a fit run row (poll until status leaves `pending`)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int
    created_at: datetime
    agent_model: str | None
    status: FitStatus
    summary: str | None
    violations: list[Any] | dict[str, Any] | None
    normalized_recipe: dict[str, Any] | list[Any] | None


class FitRunWithRecommendationsPublic(FitRunPublic):
    """Fit run with recommendation rows for list/detail views."""

    recommendations: list[FitRecommendationPublic]


class FitRunsForRecipePublic(SQLModel):
    data: list[FitRunWithRecommendationsPublic]