"""Recipe HTTP routes with mocked `Session` (no database)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.agent import AGENT_MODEL_NAME
from app.models import FitStatus, Recipe

NOW = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

MINIMAL_RECIPE_BODY = {
    "recipe_name": "Test Loaf",
    "batch_id": "batch-test-1",
    "status_expectation": "audit",
    "ingredients": [],
}


def _session_for_list(count: int, recipes: list[Recipe]) -> MagicMock:
    session = MagicMock()
    r_count = MagicMock()
    r_count.one.return_value = count
    r_list = MagicMock()
    r_list.all.return_value = recipes
    session.exec.side_effect = [r_count, r_list]
    return session


def test_get_recipes_returns_list(
    client: TestClient,
    override_get_db,
) -> None:
    recipe = Recipe(
        id=1,
        recipe_name="Loaf",
        batch_id="b1",
        status_expectation="ok",
        ingredients=[],
        created_at=NOW,
        updated_at=NOW,
    )
    override_get_db(_session_for_list(1, [recipe]))
    res = client.get("/api/v1/recipes/")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["batch_id"] == "b1"


def test_get_recipe_by_id_not_found(
    client: TestClient,
    override_get_db,
) -> None:
    session = MagicMock()
    session.get.return_value = None
    override_get_db(session)
    res = client.get("/api/v1/recipes/99")
    assert res.status_code == 404


def test_get_recipe_by_id_found(
    client: TestClient,
    override_get_db,
) -> None:
    recipe = Recipe(
        id=2,
        recipe_name="Loaf",
        batch_id="b2",
        status_expectation="ok",
        ingredients=[{"flour": "100g"}],
        created_at=NOW,
        updated_at=NOW,
    )
    session = MagicMock()
    session.get.return_value = recipe
    override_get_db(session)
    res = client.get("/api/v1/recipes/2")
    assert res.status_code == 200
    assert res.json()["id"] == 2


def test_delete_recipe_not_found(
    client: TestClient,
    override_get_db,
) -> None:
    session = MagicMock()
    session.get.return_value = None
    override_get_db(session)
    res = client.delete("/api/v1/recipes/1")
    assert res.status_code == 404


def test_post_recipe_requires_x_api_key(
    client: TestClient,
    override_get_db,
) -> None:
    session = MagicMock()
    override_get_db(session)
    res = client.post("/api/v1/recipes/", json=MINIMAL_RECIPE_BODY)
    # FastAPI's `APIKeyHeader` rejects a missing header before route deps (401).
    assert res.status_code == 401


def test_post_recipe_rejects_wrong_api_key(
    client: TestClient,
    override_get_db,
) -> None:
    session = MagicMock()
    override_get_db(session)
    res = client.post(
        "/api/v1/recipes/",
        json=MINIMAL_RECIPE_BODY,
        headers={"X-API-Key": "wrong"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Invalid API key"


@patch("app.api.routes.recipes.execute_agent_fit_run")
@patch("app.api.routes.recipes.create_pending_fit_run")
def test_post_recipe_success(
    mock_create_run: MagicMock,
    mock_execute: MagicMock,
    client: TestClient,
    override_get_db,
) -> None:
    session = MagicMock()
    dup = MagicMock()
    dup.first.return_value = None
    session.exec.return_value = dup

    def add(obj: Recipe) -> None:
        session._added_recipe = obj

    def flush() -> None:
        r = session._added_recipe
        r.id = 42

    def refresh(obj: Recipe) -> None:
        obj.created_at = NOW
        obj.updated_at = NOW

    session.add = add
    session.flush = flush
    session.refresh = refresh
    override_get_db(session)

    mock_create_run.return_value = MagicMock(
        id=7,
        recipe_id=42,
        run_sequence=1,
        agent_model=AGENT_MODEL_NAME,
        status=FitStatus.pending,
        created_at=NOW,
    )

    res = client.post(
        "/api/v1/recipes/",
        json=MINIMAL_RECIPE_BODY,
        headers={"X-API-Key": "test-secret-key"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 42
    assert data["batch_id"] == MINIMAL_RECIPE_BODY["batch_id"]
    mock_create_run.assert_called_once()
    mock_execute.assert_called_once_with(7)


@patch("app.api.routes.recipes.execute_agent_fit_run")
@patch("app.api.routes.recipes.create_pending_fit_run")
def test_post_recipe_duplicate_batch_id(
    mock_create_run: MagicMock,
    mock_execute: MagicMock,
    client: TestClient,
    override_get_db,
) -> None:
    session = MagicMock()
    existing = Recipe(
        id=1,
        recipe_name="Old",
        batch_id=MINIMAL_RECIPE_BODY["batch_id"],
        status_expectation="x",
        ingredients=[],
        created_at=NOW,
        updated_at=NOW,
    )
    dup = MagicMock()
    dup.first.return_value = existing
    session.exec.return_value = dup
    override_get_db(session)

    res = client.post(
        "/api/v1/recipes/",
        json=MINIMAL_RECIPE_BODY,
        headers={"X-API-Key": "test-secret-key"},
    )
    assert res.status_code == 409
    mock_create_run.assert_not_called()
    mock_execute.assert_not_called()


def test_list_fit_runs_recipe_not_found(
    client: TestClient,
    override_get_db,
) -> None:
    session = MagicMock()
    session.get.return_value = None
    override_get_db(session)
    res = client.get("/api/v1/recipes/1/fit-runs")
    assert res.status_code == 404
