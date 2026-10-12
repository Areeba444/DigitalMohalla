"""The synthetic dataset (data/derived/mini) loaded into a real PostgreSQL 16.

Each test builds a throwaway database `dm_dataset_load_test` next to the test database, loads the
dataset with scripts/load_dataset.py and checks it, so the other integration tests are untouched.
Skipped without TEST_DATABASE_URL (the user must be allowed to CREATE DATABASE).

What this proves: the generated files satisfy the schema's own constraints (foreign keys, CHECKs,
the booking exclusion constraint), the hash chain of every stream verifies, the database's
replay_state() and the backend's Python replay agree with the stored state, and a request made
through the real lifecycle service on top of the loaded data runs end to end under the live triggers.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import psycopg
import pytest
from sqlalchemy import Engine, create_engine, make_url, text

from app.domain.lifecycle.service import Actor
from app.infra.db.session import make_engine
from tests.integration.conftest import period
from tests.integration.test_borrowing_service import make_service

ROOT = Path(__file__).resolve().parents[3]
MINI = ROOT / "data" / "derived" / "mini"
DB_NAME = "dm_dataset_load_test"


def _loader() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "load_dataset", ROOT / "scripts" / "load_dataset.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:  # overrides the session fixture: this module has its own database
    base = os.environ.get("TEST_DATABASE_URL")
    if not base:
        pytest.skip("TEST_DATABASE_URL is not set")
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as c:
            c.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)"))
            c.execute(text(f"CREATE DATABASE {DB_NAME}"))
    except Exception as exc:  # no CREATE DATABASE right
        pytest.skip(f"cannot create a scratch database: {exc}")
    url = make_url(base).set(database=DB_NAME).render_as_string(hide_password=False)
    eng = make_engine(url)
    yield eng
    eng.dispose()
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)"))
    admin.dispose()


@pytest.fixture(scope="module")
def loaded(engine: Engine) -> dict[str, int]:
    mod = _loader()
    mod.reset_schema(engine)
    counts = mod.load(engine, MINI)
    assert not mod.verify(engine, MINI)
    return counts  # type: ignore[no-any-return]


def test_mini_loads_and_every_check_passes(engine: Engine, loaded: dict[str, int]) -> None:
    mod = _loader()
    assert mod.verify(engine, MINI) == []
    assert loaded["lifecycle_event"] > 1000 and loaded["outcome"] > 500


def test_user_triggers_are_back_on_after_the_load(engine: Engine, loaded: dict[str, int]) -> None:
    with engine.connect() as c:
        off = c.execute(
            text(
                "SELECT count(*) FROM pg_trigger g JOIN pg_class k ON k.oid = g.tgrelid "
                "JOIN pg_namespace n ON n.oid = k.relnamespace "
                "WHERE n.nspname = 'dm' AND NOT g.tgisinternal AND g.tgenabled <> 'O'"
            )
        ).scalar_one()
    assert off == 0


def test_loaded_events_cannot_be_changed(engine: Engine, loaded: dict[str, int]) -> None:
    with engine.begin() as c, pytest.raises(Exception, match="append-only"):
        c.execute(text("UPDATE lifecycle_event SET payload = '{}' WHERE event_id = 1"))


def test_a_real_request_runs_end_to_end_on_the_loaded_data(
    engine: Engine, loaded: dict[str, int]
) -> None:
    """Live triggers, locality check, booking and checklists, on top of the loaded history."""
    with engine.connect() as conn:
        outer = conn.begin()
        try:
            row = conn.execute(
                text(
                    "SELECT i.id, i.owner_id, m.user_id FROM item i "
                    "JOIN membership m ON m.community_id = i.community_id AND m.status = 'APPROVED' "
                    "JOIN app_user b ON b.id = m.user_id AND b.platform_role = 'MEMBER' "
                    "WHERE i.value_band = 'LOW' AND i.deposit_amount = 0 AND i.status = 'PUBLISHED' "
                    "  AND m.user_id <> i.owner_id AND m.role = 'MEMBER' "
                    "  AND NOT EXISTS (SELECT 1 FROM booking k WHERE k.item_id = i.id AND k.status = 'HELD') "
                    "ORDER BY i.id LIMIT 1"
                )
            ).one()
            item, lender_id, borrower_id = row
            svc = make_service(conn, engine)
            created = svc.create_request(
                Actor(borrower_id), item, period(1, 3), "synthetic smoke test"
            )
            assert created.state in ("ASSESSED", "HELD_FOR_REVIEW")
            assert created.state == "ASSESSED"
            txn = created.transaction_id
            assert svc.accept(Actor(lender_id), txn).state == "ACCEPTED"
            svc.record_handover_checklist(Actor(lender_id), txn, checklist={"note": "synthetic"})
            assert svc.confirm_handover(Actor(borrower_id), txn).state == "ACTIVE"
            assert svc.initiate_return(Actor(borrower_id), txn).state == "RETURN_INITIATED"
            svc.confirm_return(Actor(lender_id), txn)
            assert svc.confirm_return(Actor(borrower_id), txn).state == "COMPLETED"
        finally:
            outer.rollback()


def test_a_broken_dataset_is_caught(engine: Engine, tmp_path: Path) -> None:
    mod = _loader()
    # 1. a foreign key that points nowhere is refused while loading
    bad_fk = tmp_path / "bad_fk"
    shutil.copytree(MINI, bad_fk)
    f = bad_fk / "outcome.csv"
    lines = f.read_text(encoding="utf-8").splitlines()
    head = lines[0].split(",")
    cols = lines[1].split(",")
    cols[head.index("subject_id")] = "00000000-0000-0000-0000-000000000001"
    lines[1] = ",".join(cols)
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mod.reset_schema(engine)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        mod.load(engine, bad_fk)

    # 2. a stored state that the events do not support loads fine but fails verification
    bad_state = tmp_path / "bad_state"
    shutil.copytree(MINI, bad_state)
    f = bad_state / "borrowing_transaction.csv"
    lines = f.read_text(encoding="utf-8").splitlines()
    k = next(i for i, ln in enumerate(lines) if ",LOCALITY_CHECKED," in ln)
    lines[k] = lines[k].replace(",LOCALITY_CHECKED,", ",ASSESSED,")
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mod.reset_schema(engine)
    mod.load(engine, bad_state)
    problems = mod.verify(engine, bad_state)
    assert any("replay_state" in p for p in problems), problems
