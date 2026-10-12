"""The synthetic-data generator (data/generators) and the files it produces.

These tests run the generator as a separate process, exactly as a person would, so the generator's
module names do not leak into this test session. All data is synthetic and uses fixed seeds.

What is checked:
  * mini and standard build and pass every check in validate.py (foreign keys, lifecycle transition
    table, schema constraints, no activity before accounts existed, no double booking, outcomes only
    from closed loans, trust edges recomputed from outcomes, privacy columns, review-text diversity);
  * building twice gives byte-identical files (same seed, same reference date);
  * the committed files in data/derived/ are what the generator produces now;
  * a small `scale` build works at another size;
  * the validator really fails on broken data (so a pass means something).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GEN = ROOT / "data" / "generators"
DERIVED = ROOT / "data" / "derived"


def run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(GEN / script), *args],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=ROOT,
    )


def lf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    out = {}
    for tier in ("mini", "standard"):
        folder = tmp_path_factory.mktemp(tier)
        r = run("build.py", "--tier", tier, "--out", str(folder))
        assert r.returncode == 0, r.stderr + r.stdout
        out[tier] = folder
    return out


@pytest.mark.parametrize("tier", ["mini", "standard"])
def test_generated_data_passes_every_check(built: dict[str, Path], tier: str) -> None:
    r = run("validate.py", str(built[tier]))
    assert r.returncode == 0, r.stdout
    assert " 0 failed" in r.stdout


@pytest.mark.parametrize("tier", ["mini", "standard"])
def test_committed_files_are_what_the_generator_produces(built: dict[str, Path], tier: str) -> None:
    committed = DERIVED / tier
    assert (committed / "MANIFEST.json").exists(), (
        f"run build.py --tier {tier} and commit the result"
    )
    man = json.loads((committed / "MANIFEST.json").read_text(encoding="utf-8"))
    fresh = json.loads((built[tier] / "MANIFEST.json").read_text(encoding="utf-8"))
    assert fresh["files"] == man["files"], (
        "generator output changed: rebuild data/derived and review the diff"
    )
    for rel in man["files"]:
        assert lf((committed / rel).read_bytes()) == (built[tier] / rel).read_bytes(), rel


def test_build_is_deterministic(built: dict[str, Path], tmp_path: Path) -> None:
    again = tmp_path / "again"
    assert run("build.py", "--tier", "mini", "--out", str(again)).returncode == 0
    for f in sorted([*built["mini"].rglob("*.csv"), built["mini"] / "MANIFEST.json"]):
        assert f.read_bytes() == (again / f.relative_to(built["mini"])).read_bytes(), f.name


def test_everything_is_labelled_synthetic(built: dict[str, Path]) -> None:
    man = json.loads((built["standard"] / "MANIFEST.json").read_text(encoding="utf-8"))
    assert man["synthetic"] is True
    users = (built["standard"] / "app_user.csv").read_text(encoding="utf-8").splitlines()[1:]
    assert users and all(",true," in u + "," and "@synthetic.invalid" in u for u in users)


def test_scenario_manifest_covers_the_scenarios(built: dict[str, Path]) -> None:
    rows = (built["standard"] / "labels" / "scenario_manifest.csv").read_text(encoding="utf-8")
    for sid in (
        "ES-01",
        "ES-02",
        "ES-03",
        "ES-04",
        "ES-05",
        "ES-06",
        "ES-07",
        "ES-08",
        "ES-11",
        "ES-12",
        "ES-13",
        "C3",
        "C5",
    ):
        assert f"\n{sid}," in "\n" + rows, sid
    assert (
        "ES-09" not in rows and "ES-10" not in rows
    )  # locality method is still open: not built on purpose


def test_small_scale_build_validates(tmp_path: Path) -> None:
    out = tmp_path / "scale"
    r = run("build.py", "--tier", "scale", "--users", "120", "--loans", "500", "--out", str(out))
    assert r.returncode == 0, r.stderr + r.stdout
    v = run("validate.py", str(out))
    assert v.returncode == 0, v.stdout


def test_validator_fails_on_broken_data(built: dict[str, Path], tmp_path: Path) -> None:
    # 1. an illegal lifecycle jump
    bad = tmp_path / "illegal_transition"
    shutil.copytree(built["mini"], bad)
    f = bad / "lifecycle_event.csv"
    lines = f.read_text(encoding="utf-8").splitlines()
    k = next(i for i, ln in enumerate(lines) if ",handover_confirmed," in ln)
    lines[k] = lines[k].replace(",ACTIVE,", ",COMPLETED,")
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = run("validate.py", str(bad))
    assert r.returncode == 1 and "FAIL" in r.stdout

    # 2. a private column sneaking in
    bad2 = tmp_path / "private_column"
    shutil.copytree(built["mini"], bad2)
    f = bad2 / "item.csv"
    text = f.read_text(encoding="utf-8").splitlines()
    text[0] += ",home_address"
    text[1:] = [ln + ",House 1" for ln in text[1:]]
    f.write_text("\n".join(text) + "\n", encoding="utf-8")
    r = run("validate.py", str(bad2))
    assert r.returncode == 1 and "private data" in r.stdout

    # 3. a duplicated outcome
    bad3 = tmp_path / "duplicate_outcome"
    shutil.copytree(built["mini"], bad3)
    f = bad3 / "outcome.csv"
    lines = f.read_text(encoding="utf-8").splitlines()
    lines.append(
        lines[1].replace(lines[1].split(",")[0], "00000000-0000-0000-0000-000000000000", 1)
    )
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = run("validate.py", str(bad3))
    assert r.returncode == 1 and "duplicate outcome" in r.stdout
