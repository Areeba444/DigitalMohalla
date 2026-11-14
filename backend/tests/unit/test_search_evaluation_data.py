"""Search evaluation data and agreement (suite 30, data part; DA-25; plan item M9).

The committed catalogue and queries are what the generator produces (so nobody edits them by hand
before they are frozen); the catalogue keeps DA-25's shape; and the agreement script gives the
textbook kappa values. TC-295 to TC-298.
"""

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "data" / "derived" / "search"


def load(name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, REPO / "data" / "generators" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lf(path: Path) -> bytes:
    """File bytes with Windows line endings undone (git may check text files out as CRLF)."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def test_tc295_committed_files_match_their_checksums_and_the_generator(tmp_path: Path) -> None:
    manifest = json.loads((OUT / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, digest in manifest["sha256"].items():
        assert hashlib.sha256(lf(OUT / name)).hexdigest() == digest, name
    gen = load("search_catalogue")
    gen.OUT = tmp_path
    gen.main()
    for name in manifest["sha256"]:
        assert lf(tmp_path / name) == lf(OUT / name), name


def test_tc296_catalogue_shape() -> None:
    """DA-25 section 2: about 150 items, 20 decoys, a third with a Roman Urdu name, new and
    established lenders, no location or person fields, all synthetic."""
    with (OUT / "catalogue.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    items = [r for r in rows if r["decoy"] == "NONE"]
    assert len(items) == 150 and len(rows) - len(items) == 20
    assert 40 <= sum(bool(r["search_terms"]) for r in items) <= 60
    assert {r["lender_has_history"] for r in items} == {"True", "False"}
    assert all(r["synthetic"] == "True" for r in rows)
    assert not {"lat", "lng", "address", "email", "phone"} & set(rows[0])
    with (OUT / "queries.csv").open(encoding="utf-8") as fh:
        types = [r["type"] for r in csv.DictReader(fh)]
    assert 20 <= len(types) <= 30 and set(types) == {
        "exact",
        "need",
        "roman_urdu",
        "misspelling",
        "category",
        "no_answer",
    }


def test_tc297_kappa_matches_hand_worked_values() -> None:
    """Perfect agreement gives 1; a known 2x2 case (a = [0,0,1,1], b = [0,1,1,1]) gives exact 0.75
    and kappa 0.5; quadratic kappa treats 0-vs-2 as worse than 0-vs-1."""
    agree = load("search_agreement")
    assert agree.kappa([0, 1, 2, 2], [0, 1, 2, 2]) == 1.0
    assert agree.kappa([0, 0, 1, 1], [0, 1, 1, 1]) == pytest.approx(0.5)
    near = agree.kappa([0, 1, 2, 0, 1, 2], [1, 1, 2, 0, 1, 2], "quadratic")
    far = agree.kappa([0, 1, 2, 0, 1, 2], [2, 1, 2, 0, 1, 2], "quadratic")
    assert near > far


def test_tc298_agreement_script_runs_on_two_files(tmp_path: Path) -> None:
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text(
        "query_id,item_key,label\nQ01,C001,2\nQ01,C004,1\nQ02,C013,2\nQ02,C001,0\n",
        encoding="utf-8",
    )
    b.write_text(
        "query_id,item_key,label\nQ01,C001,2\nQ01,C004,2\nQ02,C013,2\nQ02,C001,0\nQ03,C002,1\n",
        encoding="utf-8",
    )
    out = subprocess.run(
        [
            sys.executable,
            "-I",
            str(REPO / "data" / "generators" / "search_agreement.py"),
            str(a),
            str(b),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "pairs: 4" in out and "only_one_labeller: 1" in out and "exact_agreement: 0.750" in out
