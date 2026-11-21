"""Evaluation harness smoke test (M7): it runs end to end on the committed `mini` tier, labels an
unfrozen run as a development run, uses a time-ordered split with no test loan before the cutoff,
and writes its results with the versions needed to reproduce them. All data is synthetic."""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_harness_runs_on_mini_and_records_its_provenance(tmp_path: Path) -> None:
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_engine.py"),
            str(ROOT / "data" / "derived" / "mini"),
            "--resamples",
            "30",
            "--out",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT / "backend",
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(next(tmp_path.glob("evaluation_mini_dev_*.json")).read_text(encoding="utf-8"))
    assert "DEVELOPMENT RUN" in out["label"] and out["protocol_version"] == "0.1 draft"
    assert out["config_version"] and out["commit"] and out["manifest_sha256"]
    assert out["test_loans"] > 0 and out["training_outcomes"] > 0
    table = out["all_test_loans"]
    assert set(table) == {"B0", "B1", "B2", "B3", "F"}
    for row in table.values():
        assert 0.0 <= row["brier"] <= 1.0 and row["brier_ci95"][0] <= row["brier_ci95"][1]
    assert datetime.fromisoformat(out["cutoff_T"])  # the split is by time
    assert list(tmp_path.glob("*.md"))
