from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import ConfigDict
from sqlmodel import Field, Column, DateTime, JSON, SQLModel


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