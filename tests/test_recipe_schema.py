"""Pydantic / SQLModel schema validation (no HTTP, no DB)."""

import pytest
from pydantic import ValidationError

from app.models import RecipeCreate


def test_recipe_create_accepts_minimal_payload() -> None:
    r = RecipeCreate(
        recipe_name="Bread",
        batch_id="b-1",
        status_expectation="audit",
        ingredients=[],
    )
    assert r.batch_id == "b-1"


def test_recipe_create_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError) as exc:
        RecipeCreate(
            recipe_name="Bread",
            batch_id="b-1",
            status_expectation="audit",
            ingredients=[],
            unexpected_field="nope",
        )
    assert "extra" in str(exc.value).lower() or "forbidden" in str(exc.value).lower()
