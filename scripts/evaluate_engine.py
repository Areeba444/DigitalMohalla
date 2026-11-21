"""Evaluation harness for the assurance engine (build item M7; Evaluation Protocol v0, DA-18).

    cd backend
    uv run python ../scripts/evaluate_engine.py ../data/derived/standard            # development run
    uv run python ../scripts/evaluate_engine.py ../data/interim/scale --protocol-frozen 1.0

Predicts "the borrower returns this loan on time" for every test loan from the history before a
cutoff T only (time-ordered holdout, DM06), with four baselines (B0 global rate, B1 role rate, B2
recency-weighted rate, B3 direct-only Beta) and the full engine (F: the posterior mean from
`AssuranceEngine.assess`, recency- and similarity-weighted). Reports Brier score, log loss, calibration
and 90% interval coverage, each with a 95% bootstrap interval, for all test loans and for the
unseen-pair subset. The hidden truth (`labels/user_truth.csv`) is read only in the scoring step.

Not measured here (and not claimed): decision quality (false trust rate etc., protocol section 6.2),
because the engine's context (disputes, reviews, trust graph) is not replayed at T. Indirect evidence
changes the assurance state, not the posterior mean (Algorithm doc D-1), so F and B3 differ only
through similarity weighting. Without `--protocol-frozen` the output is labelled a DEVELOPMENT RUN:
the protocol says to freeze it before any result is read, so the reported run is made once, with the
frozen version, on the `scale` tier. All data is SYNTHETIC.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config.engine_config import load_engine_config  # noqa: E402
from app.domain.assurance.engine import AssuranceEngine, OutcomeSnapshot  # noqa: E402
from app.domain.assurance.estimation.posterior import (  # noqa: E402
    EstimatorParams,
    WeightedOutcome,
    estimate,
)
from app.domain.lifecycle.ports import AssessmentRequest  # noqa: E402
from app.evaluation.metrics import (  # noqa: E402
    b0_global,
    b2_recency,
    b3_beta_mean,
    bootstrap_ci,
    brier,
    calibration,
    coverage,
    log_loss,
)

OUT = ROOT / "docs" / "design" / "14_testing" / "results"
CUTOFF_PERCENTILE = 0.70  # E2 (proposed)
PROTOCOL_DRAFT = "0.1 draft"
METHODS = ("B0", "B1", "B2", "B3", "F")


def read(folder: Path, name: str) -> list[dict[str, str]]:
    with (folder / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def when(s: str) -> datetime:
    return datetime.fromisoformat(s)


def days(s: str) -> float:
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*day", s)
    return float(m.group(1)) if m else 1.0


class FrozenSource:
    """EvidenceSource frozen at T: the training outcomes only, no graph, no disputes, no reviews."""

    def __init__(self, by_borrower: dict[str, list[OutcomeSnapshot]]) -> None:
        self.by = by_borrower

    def borrower_outcomes(self, borrower_id: UUID) -> list[OutcomeSnapshot]:
        return self.by.get(str(borrower_id), [])

    def trust_graph(self) -> dict[str, dict[str, float]]:
        return {}

    def open_dispute(self, borrower_id: UUID) -> bool:
        return False

    def resolved_disputes_since(self, borrower_id: UUID, since: datetime) -> int:
        return 0

    def verification_ok(self, borrower_id: UUID, item_id: UUID) -> bool:
        return True

    def display_names(self, user_ids: list[str]) -> dict[str, str]:
        return {}

    def reviews_since(self, since: datetime) -> list[Any]:
        return []

    def complaints_by(self, user_id: UUID, since: datetime) -> list[Any]:
        return []

    def account_context(self, user_id: UUID, since: datetime) -> tuple[None, None]:
        return None, None


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
    except OSError:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("folder", type=Path)
    ap.add_argument("--protocol-frozen", default="", help="frozen protocol version, e.g. 1.0")
    ap.add_argument("--resamples", type=int, default=1000)
    ap.add_argument("--out", type=Path, default=OUT, help="where the results files are written")
    a = ap.parse_args()
    cfg = load_engine_config()
    params = EstimatorParams.from_config(cfg.section("trust_estimation_alg1"))
    half = params.half_life_days
    thresholds = cfg.section("decision_policy_alg4")["thresholds"]
    n_min = float(next(v for k, v in thresholds.items() if k.startswith("n_min")))

    outcomes = [
        o
        for o in read(a.folder, "outcome.csv")
        if o["subject_role"] == "BORROWER"
        and o["metric"] == "ON_TIME_RETURN"
        and o["status"] == "VALID"
    ]
    txns = {t["id"]: t for t in read(a.folder, "borrowing_transaction.csv")}
    times = sorted(when(o["occurred_at"]) for o in outcomes)
    cutoff = times[int(CUTOFF_PERCENTILE * len(times))]

    training = [o for o in outcomes if when(o["occurred_at"]) < cutoff]
    by_borrower: dict[str, list[OutcomeSnapshot]] = defaultdict(list)
    history: dict[str, list[tuple[datetime, bool]]] = defaultdict(list)
    for o in training:
        ok = o["success"] == "true"
        by_borrower[o["subject_id"]].append(
            OutcomeSnapshot(
                when(o["occurred_at"]),
                ok,
                "VALID",
                int(o["category_id"]),
                o["value_band"],
                days(o["loan_duration"]),
                o["observer_id"] or None,
            )
        )
        history[o["subject_id"]].append((when(o["occurred_at"]), ok))
    seen_pairs = {
        (t["borrower_id"], t["lender_id"]) for t in txns.values() if when(t["created_at"]) < cutoff
    }
    tests = [
        o
        for o in outcomes
        if o["transaction_id"] in txns and when(txns[o["transaction_id"]]["created_at"]) > cutoff
    ]
    truth = {
        r["user_id"]: float(r["true_p_on_time_return"])
        for r in read(a.folder, "labels/user_truth.csv")
    }  # scoring only
    engine = AssuranceEngine(FrozenSource(by_borrower), cfg, clock=lambda: cutoff)
    b0 = b0_global([o["success"] == "true" for o in training])

    y: list[int] = []
    preds: dict[str, list[float]] = {m: [] for m in METHODS}
    unseen: list[bool] = []
    first_for: dict[str, int] = {}
    f_int: list[tuple[float, float]] = []
    b3_int: list[tuple[float, float]] = []
    n_eff_of: list[float] = []
    for i, o in enumerate(tests):
        t = txns[o["transaction_id"]]
        b = o["subject_id"]
        h = history.get(b, [])
        y.append(1 if o["success"] == "true" else 0)
        unseen.append((b, t["lender_id"]) not in seen_pairs)
        preds["B0"].append(b0)
        preds["B1"].append(b0)
        preds["B2"].append(b2_recency(h, cutoff, half, b0))
        preds["B3"].append(b3_beta_mean(h, cutoff, half))
        r = engine.assess(
            AssessmentRequest(
                uuid4(),
                UUID(b),
                UUID(t["lender_id"]),
                UUID(t["item_id"]),
                o["value_band"],
                int(o["category_id"]),
                cfg.config_version,
                days(o["loan_duration"]),
            )
        )
        preds["F"].append(float(r.posterior_mean))
        first_for.setdefault(b, i)
        f_int.append((float(r.ci90_low), float(r.ci90_high)))
        e3 = estimate([WeightedOutcome(w, ok) for w, ok in h], params, cutoff)
        b3_int.append((e3.lower_90, e3.upper_90))
        n_eff_of.append(e3.n_eff)

    def table(idx: list[int]) -> dict[str, dict[str, Any]]:
        yy = [y[i] for i in idx]
        res: dict[str, dict[str, Any]] = {}
        for m, p_all in preds.items():
            p = [p_all[i] for i in idx]
            lo, hi = bootstrap_ci(
                lambda s, p=p, yy=yy: brier([p[k] for k in s], [yy[k] for k in s]),
                len(idx),
                a.resamples,
            )
            bins, ece = calibration(p, yy)
            res[m] = {
                "brier": round(brier(p, yy), 4),
                "brier_ci95": [round(lo, 4), round(hi, 4)],
                "log_loss": round(log_loss(p, yy), 4),
                "ece": round(ece, 4),
                "calibration_bins": [b.__dict__ for b in bins],
            }
            if m != "B0":
                p0 = [preds["B0"][i] for i in idx]
                dlo, dhi = bootstrap_ci(
                    lambda s, p=p, p0=p0, yy=yy: (
                        brier([p[k] for k in s], [yy[k] for k in s])
                        - brier([p0[k] for k in s], [yy[k] for k in s])
                    ),
                    len(idx),
                    a.resamples,
                )
                res[m]["brier_minus_B0_ci95"] = [round(dlo, 4), round(dhi, 4)]
        return res

    everyone = list(range(len(tests)))
    only_unseen = [i for i in everyone if unseen[i]]
    firsts = sorted(first_for.values())
    cov: dict[str, dict[str, Any]] = {}
    for name, ints in (("B3", b3_int), ("F", f_int)):
        for label, keep in (
            ("n_eff below n_min", [i for i in firsts if n_eff_of[i] < n_min]),
            ("n_eff at least n_min", [i for i in firsts if n_eff_of[i] >= n_min]),
        ):
            sel = [i for i in keep if tests[i]["subject_id"] in truth]
            value = (
                round(
                    coverage([ints[i] for i in sel], [truth[tests[i]["subject_id"]] for i in sel]),
                    3,
                )
                if sel
                else None
            )
            cov[f"{name}: {label}"] = {"borrowers": len(sel), "coverage": value}

    manifest = a.folder / "MANIFEST.json"
    frozen = bool(a.protocol_frozen)
    label = "SYNTHETIC DATA. " + (
        "Measured run."
        if frozen
        else "DEVELOPMENT RUN: protocol not frozen, not a reported result."
    )
    result: dict[str, Any] = {
        "label": label,
        "protocol_version": a.protocol_frozen or PROTOCOL_DRAFT,
        "config_version": cfg.config_version,
        "commit": git_commit(),
        "run_date": datetime.now(UTC).date().isoformat(),
        "tier_folder": a.folder.name,
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()
        if manifest.exists()
        else None,
        "cutoff_T": cutoff.isoformat(),
        "cutoff_percentile": CUTOFF_PERCENTILE,
        "training_outcomes": len(training),
        "test_loans": len(tests),
        "test_loans_unseen_pair": len(only_unseen),
        "global_on_time_rate_B0": round(b0, 4),
        "all_test_loans": table(everyone),
        "unseen_pair_subset": table(only_unseen)
        if len(only_unseen) >= 20
        else "fewer than 20 loans: not reported",
        "interval_coverage": cov,
    }
    a.out.mkdir(parents=True, exist_ok=True)
    stem = f"evaluation_{a.folder.name}_{'frozen' if frozen else 'dev'}_{result['run_date']}"
    (a.out / f"{stem}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# Engine evaluation, {a.folder.name} tier ({label})",
        "",
        f"Protocol {result['protocol_version']}; config {result['config_version']}; "
        f"commit {result['commit']}; run {result['run_date']}; cutoff T = {result['cutoff_T']} "
        "(70th percentile of outcome times).",
        f"Training outcomes {len(training)}; test loans {len(tests)} (unseen pair: "
        f"{len(only_unseen)}); B0 = {result['global_on_time_rate_B0']}.",
        "",
        "Brier score (lower is better) with 95% bootstrap interval, and the paired difference to "
        "B0 (negative = better than B0):",
        "",
        "| Method | Brier | 95% interval | vs B0, 95% interval | Log loss | ECE |",
        "| :--- | ---: | :--- | :--- | ---: | ---: |",
    ]
    for m, row in result["all_test_loans"].items():
        lines.append(
            f"| {m} | {row['brier']} | {row['brier_ci95']} | "
            f"{row.get('brier_minus_B0_ci95', '-')} | {row['log_loss']} | {row['ece']} |"
        )
    lines += ["", "90% interval coverage of the hidden true probability (target near 0.90):", ""]
    lines += [f"- {k}: {v['coverage']} over {v['borrowers']} borrowers" for k, v in cov.items()]
    lines += [
        "",
        "Decision metrics (protocol section 6.2) are not measured in this run. "
        "Full numbers: the JSON file of the same name.",
    ]
    (a.out / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
