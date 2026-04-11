"""Persist agent output as `FitRun` rows (background / post-commit)."""

from sqlmodel import Session

from app.agent import AGENT_MODEL_NAME, get_recipe_recommendations
from app.core.db import engine
from app.models import FitRun, FitStatus, Recipe, RecipePublic


def _message_content(result: object) -> str:
    content = getattr(result, "content", None)
    if content is not None:
        if isinstance(content, str):
            return content
        return str(content)
    return str(result)


def execute_agent_fit_run(recipe_id: int) -> None:
    """
    Load the recipe, run the LLM, and insert a `FitRun` with the recommendation text.
    """
    with Session(engine) as session:
        recipe = session.get(Recipe, recipe_id)
        if recipe is None:
            return

        recipe_dict = RecipePublic.model_validate(recipe).model_dump()
        try:
            result = get_recipe_recommendations(recipe_dict)
            summary = _message_content(result)
            status = FitStatus.needs_review
        except Exception as exc:  # noqa: BLE001 — persist failure for observability
            summary = str(exc)
            status = FitStatus.failed

        fit_run = FitRun(
            recipe_id=recipe_id,
            agent_model=AGENT_MODEL_NAME,
            status=status,
            summary=summary,
        )
        session.add(fit_run)
        session.commit()
