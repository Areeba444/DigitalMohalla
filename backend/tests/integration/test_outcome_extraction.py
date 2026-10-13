"""Outcome extraction against the synthetic `mini` dataset in a real PostgreSQL (TC-76, TC-23, FR-B-15).

The dataset's outcomes were written by the data generator from its own copy of decision D11, so it
is an independent oracle: every closing event's outcomes, recomputed from the events alone by the
backend, must equal what the dataset holds. Runs in its own scratch database (`dm_outcome_test`).
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import Engine, create_engine, make_url, text

from app.infra.db.outcomes import outcomes_for_event, record_pending_outcomes
from app.infra.db.session import make_engine

ROOT = Path(__file__).resolve().parents[3]
MINI = ROOT / "data" / "derived" / "mini"
DB_NAME = "dm_outcome_test"
ROW = (
    "SELECT source_event_id, subject_id::text, subject_role::text, metric::text, success, occurred_at, "
    "category_id, value_band::text, loan_duration FROM outcome"
)


def _loader() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "load_dataset", ROOT / "scripts" / "load_dataset.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:  # this module has its own database
    base = os.environ.get("TEST_DATABASE_URL")
    if not base:
        pytest.skip("TEST_DATABASE_URL is not set")
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as c:
            c.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)"))
            c.execute(text(f"CREATE DATABASE {DB_NAME}"))
    except Exception as exc:
        pytest.skip(f"cannot create a scratch database: {exc}")
    eng = make_engine(make_url(base).set(database=DB_NAME).render_as_string(hide_password=False))
    mod = _loader()
    mod.reset_schema(eng)
    mod.load(eng, MINI)
    yield eng
    eng.dispose()
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)"))
    admin.dispose()


@pytest.fixture(scope="module")
def stored(engine: Engine) -> set[tuple[Any, ...]]:
    """The dataset's outcomes as loaded, before any test changes the table."""
    with engine.connect() as c:
        return {tuple(r) for r in c.execute(text(ROW)).all()}


def test_every_closing_event_gives_the_dataset_outcomes(
    engine: Engine, stored: set[tuple[Any, ...]]
) -> None:
    expected: dict[int, set[tuple[str, str, bool]]] = {}
    for eid, _subj, role, metric, ok, *_ in stored:
        expected.setdefault(eid, set()).add((role, metric, ok))
    with engine.connect() as c:
        closing = (
            c.execute(
                text(
                    "SELECT event_id FROM lifecycle_event "
                    "WHERE event_type IN ('transaction_closed', 'dispute_resolved') ORDER BY event_id"
                )
            )
            .scalars()
            .all()
        )
        assert len(closing) > 100
        for eid in closing:
            got = {(r.subject_role, r.metric, r.success) for r in outcomes_for_event(c, eid)}
            assert got == expected.get(eid, set()), f"event {eid}"


def test_open_loans_and_open_disputes_have_no_outcomes(engine: Engine) -> None:
    with engine.connect() as c:
        n = c.execute(
            text(
                "SELECT count(*) FROM outcome o JOIN borrowing_transaction t ON t.id = o.transaction_id "
                "WHERE t.current_state NOT IN ('COMPLETED')"
            )
        ).scalar_one()
        disputed = c.execute(
            text("SELECT count(*) FROM borrowing_transaction WHERE current_state = 'DISPUTED'")
        ).scalar_one()
    assert disputed >= 1  # the dataset has open disputes (ES-03b, ES-07, ES-08)
    assert n == 0


def test_all_outcomes_can_be_rebuilt_from_the_events_alone(
    engine: Engine, stored: set[tuple[Any, ...]]
) -> None:
    with engine.begin() as c:
        c.execute(text("TRUNCATE outcome"))
        assert c.execute(text("SELECT count(*) FROM v_pending_outcomes")).scalar_one() > 100
        inserted = record_pending_outcomes(c)
        rebuilt = {tuple(r) for r in c.execute(text(ROW)).all()}
        statuses = set(c.execute(text("SELECT DISTINCT status::text FROM outcome")).scalars().all())
    assert inserted == len(stored)
    assert rebuilt == stored
    # outcomes are written as VALID; flagging for re-evaluation (ES-11) is a later moderator action
    assert statuses == {"VALID"}


def test_rebuilding_twice_adds_nothing(engine: Engine) -> None:
    with engine.begin() as c:
        before = c.execute(text("SELECT count(*) FROM outcome")).scalar_one()
        assert record_pending_outcomes(c) == 0
        assert c.execute(text("SELECT count(*) FROM outcome")).scalar_one() == before
        assert c.execute(text("SELECT count(*) FROM v_pending_outcomes")).scalar_one() == 0
