import secrets
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlmodel import Session

from app.core.config import get_settings
from app.core.db import engine

_recipe_create_api_key_header = APIKeyHeader(name="X-API-Key")


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def verify_recipe_create_api_key(
    api_key: Annotated[str, Security(_recipe_create_api_key_header)],
) -> None:
    expected = get_settings().recipe_create_api_key
    try:
        if not secrets.compare_digest(api_key, expected):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        ) from None


SessionDep = Annotated[Session, Depends(get_db)]
RecipeCreateAuthDep = Annotated[None, Depends(verify_recipe_create_api_key)]