"""Shared fixtures: minimal FastAPI app (no LLM lifespan), env, and DB overrides."""

from __future__ import annotations

import os

# `app.core.db` builds the engine at import time; satisfy Settings before any `app` import.
os.environ.setdefault("API_V1_STR", "/api/v1")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://test.local")
os.environ.setdefault("CRUMB_API_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@127.0.0.1:5432/test")

from collections.abc import Callable, Generator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import deps
from app.api.main import api_router
from app.core.config import get_settings


@pytest.fixture
def app() -> FastAPI:
    """Router only — avoids `app.main` lifespan / `GOOGLE_API_KEY` for LLM setup."""
    application = FastAPI()
    application.include_router(api_router, prefix="/api/v1")
    return application


@pytest.fixture(autouse=True)
def reset_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_V1_STR", "/api/v1")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://test.local")
    monkeypatch.setenv("CRUMB_API_KEY", "test-secret-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@127.0.0.1:5432/test")
    get_settings.cache_clear()


@pytest.fixture
def override_get_db(app: FastAPI) -> Callable[[MagicMock], None]:
    def _apply(session: MagicMock) -> None:
        def _gen() -> Generator[MagicMock, None, None]:
            yield session

        app.dependency_overrides[deps.get_db] = _gen

    yield _apply
    app.dependency_overrides.pop(deps.get_db, None)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
