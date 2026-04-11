"""Create pending fit runs synchronously; complete agent work in the background."""

from sqlmodel import Session

from app.agent import AGENT_MODEL_NAME, get_recipe_recommendations
from app.core.db import engine
from app.models import (
    FitRecommendation,
    FitRun,
    FitStatus,
    RecommendationSeverity,
    Recipe,
    RecipePublic,
)


def _message_content(result: object) -> str:
    content = getattr(result, "content", None)
    if content is not None:
        if isinstance(content, str):
            return content
        return str(content)
    return str(result)


def create_pending_fit_run(session: Session, recipe_id: int) -> FitRun:
    """Insert a `FitRun` in `pending` (call before commit)."""
    row = FitRun(
        recipe_id=recipe_id,
        agent_model=AGENT_MODEL_NAME,
        status=FitStatus.pending,
    )
    session.add(row)
    session.flush()
    session.refresh(row)
    return row


def execute_agent_fit_run(fit_run_id: int) -> None:
    """
    Load the fit run and recipe, run the LLM, then update the run and attach
    the narrative as a `FitRecommendation`.
    """
    with Session(engine) as session:
        fit_run = session.get(FitRun, fit_run_id)
        if fit_run is None:
            return

        recipe = session.get(Recipe, fit_run.recipe_id)
        if recipe is None:
            fit_run.status = FitStatus.failed
            session.commit()
            return

        recipe_dict = RecipePublic.model_validate(recipe).model_dump()
        try:
            result = get_recipe_recommendations(recipe_dict)
            text = _message_content(result)
            fit_run.status = FitStatus.needs_review
            fit_run.summary = None
            session.add(
                FitRecommendation(
                    fit_run_id=fit_run_id,
                    severity=RecommendationSeverity.info,
                    message=text,
                )
            )
        except Exception as exc:  # noqa: BLE001 — persist failure for observability
            fit_run.status = FitStatus.failed
            fit_run.summary = None
            err_msg = str(exc)
            session.add(
                FitRecommendation(
                    fit_run_id=fit_run_id,
                    severity=RecommendationSeverity.error,
                    message=err_msg,
                )
            )

        session.commit()
