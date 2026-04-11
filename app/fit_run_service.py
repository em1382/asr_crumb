"""Create pending fit runs synchronously; complete agent work in the background."""

from sqlalchemy import func
from sqlmodel import Session, select

from app.agent import AGENT_MODEL_NAME, get_recipe_recommendations
from app.core.db import engine
from app.models import (
    FitRecommendation,
    FitRun,
    FitStatus,
    Recipe,
    RecipePublic,
)


def create_pending_fit_run(session: Session, recipe_id: int) -> FitRun:
    """Insert a `FitRun` in `pending` (call before commit)."""
    max_seq = session.exec(
        select(func.max(FitRun.run_sequence)).where(FitRun.recipe_id == recipe_id)
    ).first()
    next_seq = (max_seq or 0) + 1
    row = FitRun(
        recipe_id=recipe_id,
        run_sequence=next_seq,
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
            fit_run.status = FitStatus.needs_review
            session.add(
                FitRecommendation(
                    fit_run_id=fit_run_id,
                    severity=result.severity,
                    message=result.message,
                    reasoning=result.reasoning,
                    recommendations=result.recommendations,
                )
            )
        except Exception as exc:  # noqa: BLE001 — persist failure for observability
            fit_run.status = FitStatus.failed
            err_msg = str(exc)
            session.add(
                FitRecommendation(
                    fit_run_id=fit_run_id,
                    message=err_msg,
                )
            )

        session.commit()
