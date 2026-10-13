"""k-hop search over the trust graph of the synthetic `mini` dataset in PostgreSQL (suite 7, ES-13).

ES-13: borrower v has borrowed from a and b, who both borrowed from lender u; v never borrowed
from u. ES-13b: same amount of history, but through lenders with no link to u. Runs in its own
scratch database (`dm_khop_test`).
"""

from __future__ import annotations

import csv
import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import Engine, create_engine, make_url, text

from app.config.engine_config import load_engine_config
from app.domain.assurance.indirect.khop import KHopParams
from app.infra.db.session import make_engine
from app.infra.db.trust_graph import indirect_for, load_graph

ROOT = Path(__file__).resolve().parents[3]
MINI = ROOT / "data" / "derived" / "mini"
DB_NAME = "dm_khop_test"
P = KHopParams.from_config(load_engine_config().section("indirect_trust_alg2"))


def _loader() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "load_dataset", ROOT / "scripts" / "load_dataset.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ids() -> dict[str, str]:
    with (MINI / "labels" / "user_truth.csv").open(encoding="utf-8") as f:
        return {r["alias"]: r["user_id"] for r in csv.DictReader(f)}


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


def test_es13_community_paths_support_the_borrower(engine: Engine) -> None:
    u = ids()
    with engine.connect() as c:
        r = indirect_for(c, u["es13.u"], u["es13.v"], P, target_mean=0.73)
    assert r.first_hops == sorted([u["es13.a"], u["es13.b"]])
    assert [p.hops for p in r.paths] == [2, 2]
    assert r.reliability >= 0.3  # rho_sup: enough for rule R9 (ADR-0008)
    assert r.reliability <= P.rho_max


def test_es13b_without_a_path_there_is_no_indirect_support(engine: Engine) -> None:
    u = ids()
    with engine.connect() as c:
        r = indirect_for(c, u["es13.u"], u["es13.v_nopath"], P, target_mean=0.73)
    assert (r.paths, r.reliability) == ([], 0.0)


def test_graph_is_read_per_role_and_metric(engine: Engine) -> None:
    with engine.connect() as c:
        g = load_graph(c, "BORROWER", "ON_TIME_RETURN")
        n = c.execute(
            text(
                "SELECT count(*) FROM trust_edge WHERE role = 'BORROWER' AND metric = 'ON_TIME_RETURN'"
            )
        ).scalar_one()
    assert sum(len(nb) for nb in g.values()) == n
    assert all(0 < w <= 1 for nb in g.values() for w in nb.values())
