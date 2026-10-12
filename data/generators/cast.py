"""Helpers for hand-designed cast members (scenario people) and their history.

A "cast" member is a synthetic person whose history is written out on purpose, so that a test
knows exactly what evidence exists. Dates are given as "days before the reference date" and
jittered, so scenarios do not all share one timestamp.
"""

from __future__ import annotations

import json
import random
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import texts
from common import REF_DATE, ROOT, WINDOW_START, rng_for, uid
from population import snap_time
from world import (
    BORROWER_METRICS,
    LENDER_METRICS,
    DisputePlan,
    LoanPlan,
    Txn,
    User,
    World,
)

FIXTURES = ROOT / "docs" / "design" / "14_testing" / "scenario_fixtures_iteration1.json"


def fixture_expectations() -> dict[str, dict[str, Any]]:
    d = json.loads(FIXTURES.read_text(encoding="utf-8"))
    return {f["scenario_id"]: f["expected_result"] for f in d["fixtures"]}


def cast_user(w: World, alias: str, community: str, ago_days: float, **kw: Any) -> User:
    rng = rng_for(w.seed, f"cast-user:{alias}")
    created = max(WINDOW_START + timedelta(days=1), REF_DATE - timedelta(days=ago_days))
    created = snap_time(rng, created)
    kw.setdefault("archetype", "cast")
    return w.add_user(alias, community, created, **kw)


def cast_item(w: World, alias: str, owner: str, title: str, value: int, category: str) -> None:
    w.add_item(alias, owner, title, value, category)


def jitter(rng: random.Random, days: float, spread: float = 0.12) -> float:
    return max(0.2, days * (1 + rng.uniform(-spread, spread)))


def hist_loan(
    w: World,
    borrower: str,
    lender: str,
    ago: float,
    *,
    item: str | None = None,
    duration: int | None = None,
    late: float = 0.0,
    dispute: DisputePlan | None = None,
    auto_reviews: bool = True,
    tags: list[str] | None = None,
    group: str | None = None,
    is_attack: bool = False,
    respond_h: float = 5.0,
    path: str = "completed",
    hold: str | None = None,
    hold_result: str = "cleared",
    key: str = "",
) -> Txn:
    """One loan that started `ago` days before the reference date (with jitter)."""
    rng = rng_for(w.seed, f"hist:{borrower}:{lender}:{ago:.2f}:{key}")
    base_t = snap_time(rng, REF_DATE - timedelta(days=jitter(rng, ago)))
    # jitter must not push a loan before the people (or the item) existed
    earliest = max(w.users[borrower].created_at, w.users[lender].created_at) + timedelta(
        days=1, hours=rng.uniform(1, 20)
    )
    if item is not None:
        earliest = max(earliest, w.items[item].created_at + timedelta(days=1))
    dur = duration or rng.choice([1, 2, 3, 4, 5])
    chosen: str | None = None
    t = base_t
    for attempt in range(
        60
    ):  # if every item is busy, move the loan a few days (items cannot double-book)
        t = base_t if attempt == 0 else base_t + timedelta(days=rng.uniform(-7, 7))
        t = min(max(t, earliest), REF_DATE - timedelta(days=1))
        cands = (
            [item]
            if item is not None
            else [
                it.alias
                for it in sorted(w.items_by_owner.get(lender, ()), key=lambda i: i.alias)
                if not (it.band == "HIGH" and hold is None)
            ]
        )
        for cand in cands:
            if w.item_free(cand, t, t + timedelta(days=dur + 3)):
                chosen = cand
                break
        if chosen:
            break
    if chosen is None:
        raise RuntimeError(f"no free item for {lender} around {base_t}")
    item = chosen
    plan = LoanPlan(
        borrower=borrower,
        lender=lender,
        item=item,
        t_request=t,
        duration_days=dur,
        lead_h=rng.uniform(10, 60),
        respond_h=max(0.5, respond_h + rng.uniform(-3, 8)),
        late_days=late,
        dispute=dispute,
        auto_reviews=auto_reviews,
        tags=tags or [],
        group=group,
        is_attack=is_attack,
        path=path,
        hold=hold,
        hold_result=hold_result,
    )
    return w.add_loan(plan)


def request_under_test(
    w: World,
    borrower: str,
    lender: str,
    item: str,
    *,
    tags: list[str] | None = None,
    group: str | None = None,
    is_attack: bool = False,
    key: str = "",
) -> Txn:
    """A request waiting for the engine: created shortly before the reference date, state
    LOCALITY_CHECKED (nothing assessed yet)."""
    rng = rng_for(w.seed, f"rut:{borrower}:{item}:{key}")
    t = REF_DATE - timedelta(hours=rng.uniform(1.5, 6.0), minutes=rng.uniform(0, 59))
    plan = LoanPlan(
        borrower=borrower,
        lender=lender,
        item=item,
        t_request=t,
        path="pending",
        duration_days=rng.choice([2, 3, 4]),
        tags=(tags or []) + ["request_under_test"],
        group=group,
        is_attack=is_attack,
    )
    return w.add_loan(plan)


def ratings_for(rng: random.Random, role: str, stars: int, spread: bool = True) -> dict[str, int]:
    keys = BORROWER_METRICS if role == "BORROWER" else LENDER_METRICS
    out = {}
    for k in keys:
        s = stars
        if spread and stars >= 4 and rng.random() < 0.25:
            s = stars - 1
        out[k] = min(5, max(1, s))
    return out


def manual_review(
    w: World,
    txn: Txn,
    reviewer: str,
    reviewee: str,
    when: datetime,
    stars: int,
    comment: str,
    *,
    kind: str,
    group: str | None = None,
    is_attack: bool = False,
    key: str = "",
    rewrite: Callable[[random.Random], str] | None = None,
) -> None:
    rng = rng_for(w.seed, f"mreview:{txn.alias}:{reviewer}:{key}")
    role = "BORROWER" if reviewee == txn.plan.borrower else "LENDER"
    w.add_review(
        txn,
        reviewer,
        reviewee,
        when,
        ratings_for(rng, role, stars),
        comment,
        kind=kind,
        group=group,
        is_attack=is_attack,
        rewrite=rewrite,
    )


def closed_time(txn: Txn) -> datetime | None:
    for e in txn.events:
        if e["type"] in ("transaction_closed", "dispute_resolved"):
            return e["t"]
    return None


def add_manifest(
    w: World,
    case_id: str,
    scenario: str,
    txn: Txn,
    *,
    requirements: str,
    expected: dict[str, Any] | None,
    source: str,
    notes: str,
    split: str = "",
    group: str = "",
) -> None:
    exp = expected or {}
    w.manifest.append(
        {
            "case_id": case_id,
            "scenario": scenario,
            "requirements": requirements,
            "transaction": txn.alias,
            "transaction_id": txn.id,
            "borrower_id": uid("user", txn.plan.borrower),
            "lender_id": uid("user", txn.plan.lender),
            "item_id": uid("item", txn.plan.item),
            "as_of": txn.plan.t_request,
            "expected_state": exp.get("state", ""),
            "expected_rule": exp.get("rule_fired", ""),
            "expected_decision": exp.get("decision", ""),
            "expected_lifecycle": exp.get("lifecycle_state", ""),
            "must_not_rule": exp.get("must_not_rule", ""),
            "expected_source": source,
            "notes": notes,
            "split": split,
            "group": group,
        }
    )


def good_review_text(rng: random.Random, w: World, txn: Txn) -> str:
    return texts.legit_review(rng, "good", w.items[txn.plan.item].title)
