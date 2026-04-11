from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import SessionDep
from app.models import Message, Recipe, RecipeCreate, RecipePublic, RecipesPublic


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
def read_item(session: SessionDep, id: int) -> Any:
    """
    Gets a Recipe by ID.
    """
    recipe = session.get(Recipe, id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/", response_model=RecipePublic)
def create_recipe(
    *, session: SessionDep, recipe_in: RecipeCreate
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
    session.commit()
    session.refresh(db_obj)
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