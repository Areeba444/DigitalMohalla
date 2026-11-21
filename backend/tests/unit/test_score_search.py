"""The search scoring script (M11): it refuses to run without labels and scores toy runs. Synthetic."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = str(ROOT / "scripts" / "score_search.py")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


def test_no_labels_no_scores(tmp_path: Path) -> None:
    empty = tmp_path / "labels.csv"
    empty.write_text("query_id,item_key,label\n", encoding="utf-8")
    r = run(
        "--labels",
        str(empty),
        "--keyword",
        str(empty),
        "--hybrid",
        str(empty),
        "--out",
        str(tmp_path),
    )
    assert r.returncode == 2 and "refusing to score" in r.stderr
    assert not list(tmp_path.glob("search_evaluation.json"))


def test_toy_labels_are_scored(tmp_path: Path) -> None:
    (tmp_path / "labels.csv").write_text(
        "query_id,item_key,label\nQ01,C001,2\nQ01,C002,1\nQ01,C003,0\n", encoding="utf-8"
    )
    (tmp_path / "hybrid.csv").write_text(
        "query_id,rank,item_key\nQ01,1,C001\nQ01,2,C002\n", encoding="utf-8"
    )
    (tmp_path / "keyword.csv").write_text(
        "query_id,rank,item_key\nQ01,1,C003\nQ01,2,C001\n", encoding="utf-8"
    )
    r = run(
        "--labels", str(tmp_path / "labels.csv"), "--keyword", str(tmp_path / "keyword.csv"),
        "--hybrid", str(tmp_path / "hybrid.csv"), "--resamples", "20", "--out", str(tmp_path),
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    out = json.loads((tmp_path / "search_evaluation.json").read_text(encoding="utf-8"))
    assert out["queries_scored"] == 1
    assert out["hybrid_minus_keyword"]["ndcg@10"]["mean"] > 0
    assert out["systems"]["hybrid"]["all"]["p@5"]["mean"] == 0.4  # 2 relevant in 5
