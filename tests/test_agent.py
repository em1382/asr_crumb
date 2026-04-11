"""Unit tests for `app.agent` (mocked chain / settings; no Gemini calls)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

import app.agent as agent
from app.core.config import Settings
from app.models import FitRecommendationAgentOutput, RecommendationSeverity


def test_escape_langchain_literal_braces() -> None:
    assert agent._escape_langchain_literal_braces("a{b}c") == "a{{b}}c"
    assert agent._escape_langchain_literal_braces("{}") == "{{}}"


def test_configure_raises_when_google_api_key_missing() -> None:
    settings = Settings(
        api_v1_str="/api/v1",
        cors_allowed_origins="http://localhost",
        api_key="k",
        google_api_key=None,
    )
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        agent.configure(settings)


def test_get_recipe_recommendations_raises_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(agent, "chain", None)
    with pytest.raises(RuntimeError, match="not configured"):
        agent.get_recipe_recommendations(
            {"ingredients": [], "recipe_name": "plain"},
        )


def test_get_recipe_recommendations_invokes_chain_with_expected_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_chain = MagicMock()
    expected = FitRecommendationAgentOutput(
        severity=RecommendationSeverity.info,
        message="ok",
        reasoning=None,
        recommendations=None,
    )
    mock_chain.invoke.return_value = expected
    monkeypatch.setattr(agent, "chain", mock_chain)

    recipe = {
        "ingredients": [{"id": "flour", "amount": 500, "unit": "grams"}],
        "recipe_name": "Whole wheat",
    }
    result = agent.get_recipe_recommendations(recipe)

    assert result is expected
    mock_chain.invoke.assert_called_once_with(
        {
            "ingredients": json.dumps(recipe["ingredients"]),
            "bread_type": recipe["recipe_name"],
        }
    )
