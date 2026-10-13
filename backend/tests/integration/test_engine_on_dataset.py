"""The real engine on the synthetic `mini` dataset in PostgreSQL (suites 9 and 11; TC-71).

Each labelled case in data/derived/mini/labels/scenario_manifest.csv names a probe request, the time
it is assessed (`as_of`) and the expected state and rule. The engine reads the borrower's outcomes,
the trust graph, disputes and verification through PostgresEvidenceSource, exactly as the API does.
Runs in its own scratch database (`dm_engine_test`). All data is SYNTHETIC.
"""

from __future__ import annotations

import csv
import importlib.util
import os
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from types import ModuleType
from uuid import UUID

import pytest
from sqlalchemy import Engine, create_engine, make_url, text

from app.config.engine_config import load_engine_config
from app.domain.assurance.engine import AssuranceEngine
from app.domain.lifecycle.ports import AssessmentRequest, AssessmentResult
from app.infra.db.evidence import PostgresEvidenceSource
from app.infra.db.session import make_engine

ROOT = Path(__file__).resolve().parents[3]
MINI = ROOT / "data" / "derived" / "mini"
DB_NAME = "dm_engine_test"
CFG = load_engine_config()
# Known gaps, each strict (an unexpected pass fails, so the mark is removed when the gap closes):
KNOWN = {
    # manipulation detection arrives in Slice C; until then the risk level is 1 and R2 cannot fire
    "ES-04": "R2 needs corroborated manipulation signals (Slice C)",
    # the generator's casts predate the similarity weighting (D17) and are thinner than their
    # fixtures; the engine matches the fixtures themselves (tests/unit/test_assurance_engine.py)
    "ES-02": "mini cast: mixed categories and bands, n_eff 4.1 after similarity (fixture 9.5); B5",
    "ES-05": "mini cast: 5 loans, newest 79 days old, n_eff 2.9 before similarity (fixture 6.6); B5",
}


def _loader() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "load_dataset", ROOT / "scripts" / "load_dataset.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cases() -> list[dict[str, str]]:
    with (MINI / "labels" / "scenario_manifest.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["expected_state"] or r["expected_rule"] or r["must_not_rule"]]


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


def assess(eng: Engine, case: dict[str, str]) -> AssessmentResult:
    with eng.connect() as c:
        row = (
            c.execute(
                text(
                    "SELECT i.value_band::text AS band, i.category_id AS cat, "
                    "EXTRACT(EPOCH FROM upper(t.requested_period) - lower(t.requested_period)) "
                    "/ 86400.0 AS days FROM borrowing_transaction t JOIN item i ON i.id = t.item_id "
                    "WHERE t.id = :t"
                ),
                {"t": case["transaction_id"]},
            )
            .mappings()
            .one()
        )
    as_of = datetime.fromisoformat(case["as_of"])
    engine = AssuranceEngine(PostgresEvidenceSource(lambda: eng), CFG, clock=lambda: as_of)
    return engine.assess(
        AssessmentRequest(
            transaction_id=UUID(case["transaction_id"]),
            borrower_id=UUID(case["borrower_id"]),
            lender_id=UUID(case["lender_id"]),
            item_id=UUID(case["item_id"]),
            value_band=row["band"],
            category_id=row["cat"],
            config_version=CFG.config_version,
            duration_days=float(row["days"]),
        )
    )


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            c,
            id=c["case_id"],
            marks=[pytest.mark.xfail(reason=KNOWN[c["case_id"]], strict=True)]
            if c["case_id"] in KNOWN
            else [],
        )
        for c in cases()
    ],
)
def test_labelled_case_gets_its_expected_state_and_rule(
    engine: Engine, case: dict[str, str]
) -> None:
    r = assess(engine, case)
    if case["expected_state"]:
        assert r.assurance_state == case["expected_state"], r.explanation
    if case["expected_rule"]:
        assert r.rule_fired == case["expected_rule"], r.explanation
    if case["must_not_rule"]:
        assert r.rule_fired != case["must_not_rule"]
    assert r.config_version == CFG.config_version  # TC-71
    assert r.explanation.endswith("Decision support, not a guarantee.")
