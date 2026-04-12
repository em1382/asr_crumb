from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field as PydanticField
from sqlalchemy import Column, Enum as SAEnum, UniqueConstraint
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


class FitRunBase(SQLModel):
    """
    Shared scalar fields for the persisted `FitRun` row and API schemas
    (e.g. `FitRunPublic`). Subclass with `table=True` for the ORM model.
    """

    recipe_id: int = Field(foreign_key="recipe.id", index=True)
    run_sequence: int
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


class FitRun(FitRunBase, table=True):
    """One agent/fit pass for a recipe (e.g. recommendations toward fit-to-standard)."""

    __tablename__ = "fit_run"
    __table_args__ = (
        UniqueConstraint(
            "recipe_id",
            "run_sequence",
            name="uq_fit_run_recipe_run_sequence",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore[arg-type]
    )


class FitRecommendationAgentOutput(BaseModel):
    """
    Pydantic schema for LangChain structured LLM output. Matches the agent-filled
    columns on `fit_recommendation` (severity, message, reasoning, recommendations).
    """

    model_config = ConfigDict(extra="forbid")

    severity: RecommendationSeverity
    message: str
    reasoning: str | None = None
    recommendations: list[str] | None = PydanticField(
        default=None,
        description=(
            "List of plain-text sentences (each item one string). "
            "Not nested JSON or key-value objects."
        ),
    )


class FitRecommendationBase(SQLModel):
    """
    Shared fields for `FitRecommendation` rows and `FitRecommendationPublic`.
    """

    severity: RecommendationSeverity | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(
                RecommendationSeverity,
                name="recommendationseverity",
                native_enum=True,
                create_type=False,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=True,
        ),
    )
    message: str
    reasoning: str | None = None
    recommendations: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )


class FitRecommendation(FitRecommendationBase, table=True):
    """Structured recommendation line items for a fit run."""

    __tablename__ = "fit_recommendation"

    id: int | None = Field(default=None, primary_key=True)
    fit_run_id: int = Field(foreign_key="fit_run.id", index=True)


class FitRecommendationPublic(FitRecommendationBase):
    """API shape for a stored recommendation (agent output lives here)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fit_run_id: int


class FitRunPublic(FitRunBase):
    """API shape for a fit run row (poll until status leaves `pending`)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class FitRunWithRecommendationsPublic(FitRunPublic):
    """Fit run with recommendation rows for list/detail views."""

    recommendations: list[FitRecommendationPublic]


class FitRunsForRecipePublic(SQLModel):
    data: list[FitRunWithRecommendationsPublic]