"""Trust-edge projection against the synthetic `mini` dataset in PostgreSQL (ADR-0006, suite 7).

The dataset's edges were computed by the data generator from its own copy of ADR-0006, as of its
reference date. Rebuilding every edge from the outcomes alone, as of that date, must give the same
rows. Runs in its own scratch database (`dm_trust_edge_test`).
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import Engine, create_engine, make_url, text

from app.infra.db.session import make_engine
from app.infra.db.trust_edges import refresh_trust_edges

ROOT = Path(__file__).resolve().parents[3]
MINI = ROOT / "data" / "derived" / "mini"
DB_NAME = "dm_trust_edge_test"
REF = datetime(
    2026, 10, 1, 8, 0, tzinfo=UTC
)  # the dataset's reference date (data/generators/common.py)
ROWS = (
    "SELECT source_id::text, target_id::text, role::text, metric::text, weight, evidence_count, "
    "updated_at FROM trust_edge"
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
    with engine.connect() as c:
        return {tuple(r) for r in c.execute(text(ROWS)).all()}


def test_every_edge_can_be_rebuilt_from_the_outcomes(
    engine: Engine, stored: set[tuple[Any, ...]]
) -> None:
    assert len(stored) > 300
    with engine.begin() as c:
        written = refresh_trust_edges(c, REF)
        rebuilt = {tuple(r) for r in c.execute(text(ROWS)).all()}
    assert written == len(stored)
    assert rebuilt == stored


def test_refreshing_one_pair_touches_only_that_pair(engine: Engine) -> None:
    with engine.begin() as c:
        src, dst = c.execute(
            text("SELECT source_id::text, target_id::text FROM trust_edge LIMIT 1")
        ).one()
        before = {tuple(r) for r in c.execute(text(ROWS)).all()}
        later = datetime(2027, 4, 1, 8, 0, tzinfo=UTC)  # half a year on: weights have decayed
        n = refresh_trust_edges(c, later, [(src, dst)])
        after = {tuple(r) for r in c.execute(text(ROWS)).all()}
        c.rollback()
    changed = before ^ after
    assert n >= 1
    assert changed and all((r[0], r[1]) == (src, dst) for r in changed)
    assert all(r[6] == later for r in after if (r[0], r[1]) == (src, dst))


def test_an_edge_needs_a_valid_outcome(engine: Engine) -> None:
    with engine.connect() as c:
        orphan = c.execute(
            text(
                "SELECT count(*) FROM trust_edge e WHERE NOT EXISTS (SELECT 1 FROM outcome o "
                "WHERE o.observer_id = e.source_id AND o.subject_id = e.target_id "
                "AND o.subject_role = e.role AND o.metric = e.metric AND o.status = 'VALID')"
            )
        ).scalar_one()
    assert orphan == 0
