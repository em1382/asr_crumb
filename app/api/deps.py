import secrets
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlmodel import Session

from app.core.config import get_settings
from app.core.db import engine

_api_key_header = APIKeyHeader(name="X-API-Key")


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def verify_api_key(
    api_key: Annotated[str, Security(_api_key_header)],
) -> None:
    expected = get_settings().api_key
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
ApiKeyAuthDep = Annotated[None, Depends(verify_api_key)]