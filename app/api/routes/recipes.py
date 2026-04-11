from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import col, func, select

from app.api.deps import SessionDep
from app.fit_run_service import create_pending_fit_run, execute_agent_fit_run
from app.models import (
    FitRecommendation,
    FitRecommendationPublic,
    FitRun,
    FitRunPublic,
    FitRunsForRecipePublic,
    FitRunWithRecommendationsPublic,
    Message,
    Recipe,
    RecipeCreate,
    RecipePublic,
    RecipesPublic,
)


router = APIRouter(prefix="/recipes", tags=["recipes"])


class DuplicateBatchRecipeError(Exception):
    """Raised when a recipe with the same batch_id already exists."""

    def __init__(self, batch_id: str) -> None:
        self.batch_id = batch_id
        super().__init__(f"A recipe with batch_id {batch_id!r} already exists")


@router.get("/", response_model=RecipesPublic)
def read_recipes(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieves all recipes.
    """
    count_statement = select(func.count()).select_from(Recipe)
    count = session.exec(count_statement).one()
    statement = (
        select(Recipe).order_by(col(Recipe.created_at).desc()).offset(skip).limit(limit)
    )
    recipes = session.exec(statement).all()

    recipes_public = [RecipePublic.model_validate(recipe) for recipe in recipes]
    return RecipesPublic(data=recipes_public, count=count)


@router.get("/{id}", response_model=RecipePublic)
def read_recipe(session: SessionDep, id: int) -> Any:
    """
    Gets a Recipe by ID.
    """
    recipe = session.get(Recipe, id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/", response_model=RecipePublic)
def create_recipe(
    *,
    session: SessionDep,
    recipe_in: RecipeCreate,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Creates a new recipe if it doesn't already exist.
    """
    try:
        existing = session.exec(
            select(Recipe).where(Recipe.batch_id == recipe_in.batch_id)
        ).first()
        if existing is not None:
            raise DuplicateBatchRecipeError(recipe_in.batch_id)
    except DuplicateBatchRecipeError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        ) from e

    db_obj = Recipe.model_validate(recipe_in)
    session.add(db_obj)
    session.flush()

    fit_run = create_pending_fit_run(session, db_obj.id)
    session.commit()
    session.refresh(db_obj)

    background_tasks.add_task(execute_agent_fit_run, fit_run.id)

    return db_obj


@router.delete("/{id}")
def delete_item(
    session: SessionDep, id: int
) -> Message:
    """
    Deletes a recipe if it exists.
    """
    recipe = session.get(Recipe, id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    session.delete(recipe)
    session.commit()
    return Message(message=f"Recipe {recipe.batch_id!r} deleted successfully")


@router.get("/{recipe_id}/fit-runs", response_model=FitRunsForRecipePublic)
def list_recipe_fit_runs(session: SessionDep, recipe_id: int) -> Any:
    """
    Fit runs for a recipe (new runs start as `pending`, then fill with recommendations).
    """
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    runs = session.exec(
        select(FitRun)
        .where(FitRun.recipe_id == recipe_id)
        .order_by(col(FitRun.created_at).desc())
    ).all()

    data: list[FitRunWithRecommendationsPublic] = []
    for run in runs:
        recs = session.exec(
            select(FitRecommendation).where(FitRecommendation.fit_run_id == run.id)
        ).all()
        base = FitRunPublic.model_validate(run)
        data.append(
            FitRunWithRecommendationsPublic(
                **base.model_dump(),
                recommendations=[
                    FitRecommendationPublic.model_validate(r) for r in recs
                ],
            )
        )
    return FitRunsForRecipePublic(data=data)