"""Scenario suite (Test Plan suite 11, NFR-Q-01): shared fixtures, config and a scratch database.

Two layers, both on SYNTHETIC data:
- the hand-checked fixtures (docs/design/14_testing/scenario_fixtures_iteration1.json), run through
  the policy and the explanation, and through the real engine where the fixture has raw inputs;
- the same scenarios in the generated `mini` dataset, loaded into PostgreSQL and sent through the
  lifecycle service exactly as a request from the app would be.
The database layer needs TEST_DATABASE_URL and uses its own scratch database (`dm_scenario_test`).
"""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Engine, create_engine, make_url, text

from app.config.engine_config import load_engine_config
from app.infra.db.session import make_engine

ROOT = Path(__file__).resolve().parents[3]
MINI = ROOT / "data" / "derived" / "mini"
DB_NAME = "dm_scenario_test"
CFG = load_engine_config()
FIXTURES: dict[str, dict[str, Any]] = {
    f["scenario_id"]: f
    for f in json.loads(
        (ROOT / "docs" / "design" / "14_testing" / "scenario_fixtures_iteration1.json").read_text(
            encoding="utf-8"
        )
    )["fixtures"]
}
# Words that would turn decision support into a verdict about a person (Overview §5.11)
VERDICT_WORDS = {"score", "unreliable", "untrustworthy", "fraud", "fraudster", "risky", "ai"}


def manifest() -> dict[str, dict[str, str]]:
    with (MINI / "labels" / "scenario_manifest.csv").open(encoding="utf-8") as f:
        return {r["case_id"]: r for r in csv.DictReader(f)}


def assert_no_verdict(explanation: str) -> None:
    """No verdict words about the person, and the decision-support disclaimer at the end."""
    words = set(re.findall(r"[a-z]+", explanation.lower()))
    assert not words & VERDICT_WORDS, words & VERDICT_WORDS
    assert explanation.endswith("Decision support, not a guarantee.")


@pytest.fixture(scope="session")
def mini_db() -> Iterator[Engine]:
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
    spec = importlib.util.spec_from_file_location(
        "load_dataset", ROOT / "scripts" / "load_dataset.py"
    )
    assert spec and spec.loader
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    loader.reset_schema(eng)
    loader.load(eng, MINI)
    yield eng
    eng.dispose()
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)"))
    admin.dispose()
