"""`fit_run_service` helpers with mocked `Session` only."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.agent import AGENT_MODEL_NAME
from app.fit_run_service import create_pending_fit_run
from app.models import FitRun, FitStatus


def test_create_pending_fit_run_first_sequence() -> None:
    session = MagicMock()
    r = MagicMock()
    r.first.return_value = None
    session.exec.return_value = r

    row = create_pending_fit_run(session, recipe_id=3)

    assert isinstance(row, FitRun)
    assert row.recipe_id == 3
    assert row.run_sequence == 1
    assert row.status == FitStatus.pending
    assert row.agent_model == AGENT_MODEL_NAME
    session.add.assert_called_once()
    session.flush.assert_called()
    session.refresh.assert_called_once()


def test_create_pending_fit_run_increments_sequence() -> None:
    session = MagicMock()
    r = MagicMock()
    r.first.return_value = 4
    session.exec.return_value = r

    row = create_pending_fit_run(session, recipe_id=1)

    assert row.run_sequence == 5
