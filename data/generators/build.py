"""Build the synthetic dataset: python -I data/generators/build.py --tier mini|standard|scale

Tiers
  mini      the scenario cast and the development attack set only (fast CI tests, committed)
  standard  mini plus ordinary background life; 50-100 users scale of the plan (committed)
  scale     background life only, thousands of users, for latency and k-hop tests (NOT committed;
            written under data/interim/)

Output is CSV in the shapes of docs/design/06_data_model/schema.sql (NULL = empty field, booleans
true/false, jsonb as JSON text), plus labels/ with the hidden ground truth. Everything is SYNTHETIC.
The same seed and reference date give byte-identical files.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import texts  # noqa: E402
from attacks_dev import build_dev_attacks  # noqa: E402
from common import (  # noqa: E402
    BASE_SEED,
    DERIVED,
    GENERATOR_VERSION,
    INTERIM,
    REF_DATE,
    WINDOW_START,
    load_public_stats,
    range_literal,
    rng_for,
    sha256_file,
    uid,
    write_csv,
)
from population import build_background, run_background  # noqa: E402
from scenarios import build_scenarios  # noqa: E402
from world import CATEGORIES, TERMINAL, World, set_good_star_weights  # noqa: E402

TIERS: dict[str, dict[str, Any]] = {
    "mini": dict(communities=["g7", "f10"], bg_users=0, bg_loans=0, cast=True),
    "standard": dict(communities=["g7", "f10", "e7"], bg_users=26, bg_loans=100, cast=True),
    "scale": dict(communities=None, bg_users=2000, bg_loans=12000, cast=False),
}
COMMUNITY_NAMES = {
    "g7": "Sector G-7 (synthetic)",
    "f10": "Sector F-10 (synthetic)",
    "e7": "Sector E-7 (synthetic)",
}
ATTACK_KINDS = {
    "rating_ring",
    "new_account_burst",
    "similar_reviews",
    "trivial_exchanges",
    "false_damage_claims",
}


def build_world(
    tier: str, seed: int = BASE_SEED, users: int | None = None, loans: int | None = None
) -> World:
    spec = TIERS[tier]
    stats = load_public_stats()
    set_good_star_weights(stats["epinions_ratings"]["star_share"])
    w = World(tier, seed)
    n_users = users if users is not None else spec["bg_users"]
    n_loans = loans if loans is not None else spec["bg_loans"]
    comms = spec["communities"] or [f"s{i:02d}" for i in range(1, max(3, n_users // 80) + 1)]
    for c in comms:
        w.add_community(
            c,
            COMMUNITY_NAMES.get(c, f"Sector {c.upper()} (synthetic)"),
            WINDOW_START - timedelta(days=4),
        )
        w.add_user(
            f"mod.{c}",
            c,
            WINDOW_START + timedelta(hours=9),
            archetype="moderator",
            is_moderator=True,
            p_on_time=1.0,
            p_cond=1.0,
        )
    w.add_user(
        "admin.1", comms[0], WINDOW_START + timedelta(hours=8), archetype="admin", is_admin=True
    )
    bg: list[str] = []
    if n_users:
        bg = build_background(w, comms, n_users, n_loans, stats)
    lenders: list[str] = []
    if spec["cast"]:
        build_scenarios(w, comms[0], comms[1])
        lenders = [f"cast.L{i}" for i in range(1, 6)]
        build_dev_attacks(w, comms[0], lenders)
    if bg:
        run_background(w, bg, n_loans, stats, extra_lenders=lenders)
    return w


# ----------------------------------------------------------------------------- tables


def _evidence_level(w: World, alias: str) -> tuple[str, int]:
    times = sorted(w.history.get((alias, "BORROWER"), []))
    n = len(times)
    if n == 0:
        return "none", 0
    if (REF_DATE - times[-1]).days > 270:
        return "old", n
    return ("sparse" if n <= 2 else "moderate" if n <= 7 else "rich"), n


def write_tables(w: World, out: Path) -> dict[str, int]:
    out.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    # ---- event ids: global order by time, then stream, then sequence
    events = [e for t in w.txns.values() for e in t.events]
    events.sort(key=lambda e: (e["t"], e["txn"], e["seq"]))
    ev_id = {(e["txn"], e["seq"]): i for i, e in enumerate(events, start=1)}

    def U(a: str) -> str:
        return uid("user", a)

    # ---- people and places
    counts["app_user"] = write_csv(
        out / "app_user.csv",
        [
            "id",
            "display_name",
            "email",
            "phone",
            "password_hash",
            "verification_level",
            "platform_role",
            "status",
            "is_synthetic",
            "created_at",
        ],
        (
            {
                "id": u.id,
                "display_name": u.name,
                "email": f"{u.alias.replace('.', '-')}@synthetic.invalid",
                "phone": None,
                "password_hash": None,
                "verification_level": u.verification,
                "platform_role": "ADMIN" if u.is_admin else "MEMBER",
                "status": "ACTIVE",
                "is_synthetic": True,
                "created_at": u.created_at,
            }
            for u in w.users.values()
        ),
    )
    counts["community"] = write_csv(
        out / "community.csv",
        ["id", "name", "join_code", "rules", "boundary_polygon", "is_active", "created_at"],
        (
            {
                "id": uid("community", c["alias"]),
                "name": c["name"],
                "join_code": c["join_code"],
                "rules": "Synthetic community for testing. Not a real housing society.",
                "boundary_polygon": None,
                "is_active": True,
                "created_at": c["created_at"],
            }
            for c in w.communities.values()
        ),
    )
    mem = []
    for u in w.users.values():
        if u.is_admin:
            continue
        for k, c in enumerate([u.community, *u.extra_communities]):
            req = u.created_at + (timedelta(minutes=5) if k == 0 else timedelta(days=3))
            mem.append(
                {
                    "id": uid("membership", f"{u.alias}:{c}"),
                    "user_id": u.id,
                    "community_id": uid("community", c),
                    "role": "MODERATOR" if u.is_moderator else "MEMBER",
                    "status": "APPROVED",
                    "requested_at": req,
                    "decided_at": req + timedelta(hours=2),
                }
            )
    counts["membership"] = write_csv(
        out / "membership.csv",
        ["id", "user_id", "community_id", "role", "status", "requested_at", "decided_at"],
        mem,
    )
    cat_id = {c: i for i, c in enumerate(CATEGORIES, start=1)}
    counts["category"] = write_csv(
        out / "category.csv",
        ["id", "name", "is_restricted", "min_verification"],
        (
            {"id": i, "name": c, "is_restricted": False, "min_verification": "COMMUNITY_VERIFIED"}
            for c, i in cat_id.items()
        ),
    )
    counts["item"] = write_csv(
        out / "item.csv",
        [
            "id",
            "owner_id",
            "community_id",
            "category_id",
            "title",
            "description",
            "value_band",
            "deposit_amount",
            "required_verification",
            "status",
            "created_at",
        ],
        (
            {
                "id": it.id,
                "owner_id": U(it.owner),
                "community_id": uid("community", it.community),
                "category_id": cat_id[it.category],
                "title": it.title,
                "description": None,
                "value_band": it.band,
                "deposit_amount": it.deposit,
                "required_verification": "COMMUNITY_VERIFIED",
                "status": "PUBLISHED",
                "created_at": it.created_at,
            }
            for it in w.items.values()
        ),
    )

    # ---- loans and events
    trows = []
    for t in w.txns.values():
        p, evs = t.plan, t.events
        last = evs[-1]
        state = last["new"]
        handover = next((e for e in evs if e["type"] == "handover_confirmed"), None)
        msg = texts.request_message(rng_for(w.seed, f"msg:{t.alias}")) or None
        trows.append(
            {
                "id": t.id,
                "item_id": w.items[p.item].id,
                "borrower_id": U(p.borrower),
                "lender_id": U(p.lender),
                "requested_period": range_literal(t.start, t.end),
                "message": msg,
                "created_at": evs[0]["t"],
                "current_state": state,
                "stream_version": len(evs),
                "hold_reason": last["payload"].get("hold_reason")
                if state == "HELD_FOR_REVIEW"
                else None,
                "due_at": t.end if handover else None,
                "last_event_at": last["t"],
                "closed_at": last["t"] if state in TERMINAL else None,
            }
        )
    counts["borrowing_transaction"] = write_csv(
        out / "borrowing_transaction.csv",
        [
            "id",
            "item_id",
            "borrower_id",
            "lender_id",
            "requested_period",
            "message",
            "created_at",
            "current_state",
            "stream_version",
            "hold_reason",
            "due_at",
            "last_event_at",
            "closed_at",
        ],
        trows,
    )
    counts["lifecycle_event"] = write_csv(
        out / "lifecycle_event.csv",
        [
            "event_id",
            "stream_id",
            "stream_seq",
            "event_type",
            "schema_version",
            "actor_id",
            "occurred_at",
            "previous_state",
            "new_state",
            "evidence_refs",
            "authorisation",
            "config_version",
            "payload",
        ],
        (
            {
                "event_id": ev_id[(e["txn"], e["seq"])],
                "stream_id": w.txns[e["txn"]].id,
                "stream_seq": e["seq"],
                "event_type": e["type"],
                "schema_version": 1,
                "actor_id": U(e["actor"]) if e["actor"] else None,
                "occurred_at": e["t"],
                "previous_state": e["prev"],
                "new_state": e["new"],
                "evidence_refs": e["evidence_refs"],
                "authorisation": e["auth"],
                "config_version": e["config_version"],
                "payload": e["payload"],
            }
            for e in events
        ),
    )
    counts["condition_report"] = write_csv(
        out / "condition_report.csv",
        [
            "id",
            "transaction_id",
            "phase",
            "reporter_id",
            "reporter_role",
            "checklist",
            "condition_agreed",
            "deposit_received",
            "reduced_evidence",
            "notes",
            "created_at",
        ],
        (
            {
                "id": uid("condition", f"{r['txn']}:{r['phase']}:{r['role']}:{i}"),
                "transaction_id": w.txns[r["txn"]].id,
                "phase": r["phase"],
                "reporter_id": U(r["reporter"]),
                "reporter_role": r["role"],
                "checklist": {},
                "condition_agreed": r["agreed"],
                "deposit_received": r["deposit"],
                "reduced_evidence": r["reduced"],
                "notes": r["notes"],
                "created_at": r["created_at"],
            }
            for i, r in enumerate(w.cond_reports)
        ),
    )

    # ---- projections the database trigger event_apply would write
    counts["booking"] = write_csv(
        out / "booking.csv",
        ["id", "transaction_id", "item_id", "period", "status", "created_at", "released_at"],
        (
            {
                "id": uid("booking", k["txn"]),
                "transaction_id": w.txns[k["txn"]].id,
                "item_id": w.items[k["item"]].id,
                "period": range_literal(k["start"], k["end"]),
                "status": "RELEASED" if k["released_at"] else "HELD",
                "created_at": k["created_at"],
                "released_at": k["released_at"],
            }
            for k in w.bookings
        ),
    )
    admin = next(u for u in w.users.values() if u.is_admin)
    counts["locality_verification"] = write_csv(
        out / "locality_verification.csv",
        [
            "id",
            "membership_id",
            "method",
            "outcome",
            "geofence_signal",
            "invitation_id",
            "permission_refused",
            "mock_provider_detected",
            "duplicate_suspected",
            "approved_by",
            "checked_at",
            "valid_until",
        ],
        (
            {
                "id": uid("locality", m["id"]),
                "membership_id": m["id"],
                "method": "MODERATOR_APPROVAL",
                "outcome": "VERIFIED",
                "geofence_signal": None,
                "invitation_id": None,
                "permission_refused": False,
                "mock_provider_detected": False,
                "duplicate_suspected": False,
                "approved_by": admin.id,
                "checked_at": m["decided_at"],
                # still valid at the reference date, so a fresh request is not held as locality_inconclusive
                "valid_until": max(
                    m["decided_at"] + timedelta(days=365), REF_DATE + timedelta(days=120)
                ),
            }
            for m in mem
        ),
    )

    # ---- evidence
    counts["outcome"] = write_csv(
        out / "outcome.csv",
        [
            "id",
            "transaction_id",
            "source_event_id",
            "subject_id",
            "observer_id",
            "subject_role",
            "metric",
            "success",
            "occurred_at",
            "category_id",
            "value_band",
            "loan_duration",
            "status",
            "flagged_by_decision_id",
        ],
        (
            {
                "id": uid("outcome", f"{o['txn']}:{o['ev'][1]}:{o['subject']}:{o['metric']}"),
                "transaction_id": w.txns[o["txn"]].id,
                "source_event_id": ev_id[o["ev"]],
                "subject_id": U(o["subject"]),
                "observer_id": U(o["observer"]),
                "subject_role": o["role"],
                "metric": o["metric"],
                "success": o["success"],
                "occurred_at": o["occurred_at"],
                "category_id": cat_id[o["category"]],
                "value_band": o["band"],
                "loan_duration": f"{o['duration_days']} days",
                "status": o["status"],
                "flagged_by_decision_id": uid("decision", o["flagged_by"])
                if o["flagged_by"]
                else None,
            }
            for o in w.outcomes
        ),
    )
    counts["trust_edge"] = write_csv(
        out / "trust_edge.csv",
        ["source_id", "target_id", "role", "metric", "weight", "evidence_count", "updated_at"],
        (
            {
                "source_id": U(e["source"]),
                "target_id": U(e["target"]),
                "role": e["role"],
                "metric": e["metric"],
                "weight": e["weight"],
                "evidence_count": e["evidence_count"],
                "updated_at": e["updated_at"],
            }
            for e in w.trust_edges()
        ),
    )
    counts["review"] = write_csv(
        out / "review.csv",
        [
            "id",
            "transaction_id",
            "reviewer_id",
            "reviewee_id",
            "reviewee_role",
            "ratings",
            "comment",
            "retaliation_flag",
            "similarity_flag",
            "created_at",
        ],
        (
            {
                "id": uid("review", r["alias"]),
                "transaction_id": w.txns[r["txn"]].id,
                "reviewer_id": U(r["reviewer"]),
                "reviewee_id": U(r["reviewee"]),
                "reviewee_role": r["role"],
                "ratings": r["ratings"],
                "comment": r["comment"],
                "retaliation_flag": False,
                "similarity_flag": False,
                "created_at": r["created_at"],
            }
            for r in w.reviews
        ),
    )
    counts["escalation_case"] = write_csv(
        out / "escalation_case.csv",
        [
            "id",
            "transaction_id",
            "opened_event_id",
            "trigger_type",
            "hold_reason",
            "dispute_reason",
            "raised_by",
            "status",
            "priority",
            "reason",
            "assigned_to",
            "info_deadline",
            "opened_at",
            "closed_at",
        ],
        (
            {
                "id": uid("case", c["alias"]),
                "transaction_id": w.txns[c["txn"]].id,
                "opened_event_id": ev_id[c["ev"]],
                "trigger_type": c["trigger"],
                "hold_reason": c["hold_reason"],
                "dispute_reason": c["dispute_reason"],
                "raised_by": U(c["raised_by"]) if c["raised_by"] else None,
                "status": c["status"],
                "priority": c["priority"],
                "reason": c["reason"],
                "assigned_to": U(c["assigned_to"]),
                "info_deadline": None,
                "opened_at": c["opened_at"],
                "closed_at": c["closed_at"],
            }
            for c in w.cases
        ),
    )
    counts["moderator_decision"] = write_csv(
        out / "moderator_decision.csv",
        [
            "id",
            "case_id",
            "decided_by",
            "decider_role",
            "kind",
            "reason",
            "safeguards",
            "resolved_outcome",
            "reverses_decision_id",
            "decided_at",
        ],
        (
            {
                "id": uid("decision", d["alias"]),
                "case_id": uid("case", d["case"]),
                "decided_by": U(d["decided_by"]),
                "decider_role": "MODERATOR",
                "kind": d["kind"],
                "reason": d["reason"],
                "safeguards": [],
                "resolved_outcome": d["resolved_outcome"],
                "reverses_decision_id": uid("decision", d["reverses"]) if d["reverses"] else None,
                "decided_at": d["decided_at"],
            }
            for d in w.decisions
        ),
    )

    # ---- labels (ground truth; not part of the schema)
    lab = out / "labels"
    rows = []
    for u in w.users.values():
        level, n = _evidence_level(w, u.alias)
        rows.append(
            {
                "user_id": u.id,
                "alias": u.alias,
                "display_name": u.name,
                "community": u.community,
                "archetype": u.archetype,
                "created_at": u.created_at,
                "true_p_on_time_return": u.p_on_time,
                "true_p_condition_agreed": u.p_cond,
                "true_p_lender_condition_ok": u.p_lender_cond,
                "borrower_outcome_loans_at_ref": n,
                "evidence_level_at_ref": level,
                "history_basis": "sampled" if u.alias.startswith("bg.") else "scripted",
                "group_id": u.group,
                "group_kind": u.group_kind,
                "group_role": u.group_role,
                "is_attack_account": bool(
                    u.group_kind in ATTACK_KINDS and u.group_role != "target"
                ),
                "split": u.split,
            }
        )
    counts["labels/user_truth"] = write_csv(lab / "user_truth.csv", list(rows[0]), rows)
    counts["labels/item_value_pkr"] = write_csv(
        lab / "item_value_pkr.csv",
        ["item_id", "alias", "value_pkr", "value_band"],
        (
            {"item_id": it.id, "alias": it.alias, "value_pkr": it.value_pkr, "value_band": it.band}
            for it in w.items.values()
        ),
    )
    counts["labels/transaction_truth"] = write_csv(
        lab / "transaction_truth.csv",
        [
            "transaction_id",
            "alias",
            "tags",
            "path",
            "final_state",
            "group_id",
            "is_attack",
            "disputed",
            "fault_found",
            "request_under_test",
        ],
        (
            {
                "transaction_id": t.id,
                "alias": t.alias,
                "tags": "|".join(t.plan.tags),
                "path": t.plan.path,
                "final_state": t.events[-1]["new"],
                "group_id": t.plan.group,
                "is_attack": t.plan.is_attack,
                "disputed": bool(t.facts.get("disputed")),
                "fault_found": t.facts.get("fault") or None,
                "request_under_test": "request_under_test" in t.plan.tags,
            }
            for t in w.txns.values()
        ),
    )
    byalias = {r["alias"]: r for r in w.reviews}
    counts["labels/review_truth"] = write_csv(
        lab / "review_truth.csv",
        ["review_id", "alias", "kind", "group_id", "is_attack"],
        (
            {
                "review_id": uid("review", rt["alias"]),
                "alias": rt["alias"],
                "kind": rt["kind"],
                "group_id": rt["group"] or None,
                "is_attack": rt["is_attack"],
            }
            for rt in w.review_truth
            if rt["alias"] in byalias
        ),
    )
    mf = sorted(w.manifest, key=lambda m: m["case_id"])
    counts["labels/scenario_manifest"] = (
        write_csv(
            lab / "scenario_manifest.csv",
            [
                "case_id",
                "scenario",
                "requirements",
                "transaction",
                "transaction_id",
                "borrower_id",
                "lender_id",
                "item_id",
                "as_of",
                "expected_state",
                "expected_rule",
                "expected_decision",
                "expected_lifecycle",
                "must_not_rule",
                "expected_source",
                "notes",
                "split",
                "group",
            ],
            mf,
        )
        if mf
        else 0
    )
    return counts


def write_manifest(out: Path, tier: str, seed: int, counts: dict[str, int]) -> None:
    files = {}
    for f in sorted(out.rglob("*.csv")):
        rel = f.relative_to(out).as_posix()
        files[rel] = {"rows": counts.get(rel[:-4], None), "sha256": sha256_file(f)}
    man = {
        "synthetic": True,
        "about": "SYNTHETIC data for testing Digital Mohalla. No real person, address or identifier. Not real fraud data.",
        "generator_version": GENERATOR_VERSION,
        "tier": tier,
        "seed": seed,
        "reference_date": REF_DATE.isoformat(),
        "files": files,
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(man, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--tier", choices=list(TIERS), required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output folder (default: data/derived/<tier>, scale: data/interim/scale)",
    )
    ap.add_argument("--seed", type=int, default=BASE_SEED)
    ap.add_argument("--users", type=int, default=None, help="background users (scale tier)")
    ap.add_argument("--loans", type=int, default=None, help="target background loans (scale tier)")
    a = ap.parse_args(argv)
    out = a.out or ((INTERIM if a.tier == "scale" else DERIVED) / a.tier)
    w = build_world(a.tier, a.seed, a.users, a.loans)
    counts = write_tables(w, out)
    write_manifest(out, a.tier, a.seed, counts)
    print(
        f"{a.tier}: {len(w.users)} users, {len(w.txns)} transactions, {sum(len(t.events) for t in w.txns.values())} events, "
        f"{len(w.outcomes)} outcomes, {len(w.reviews)} reviews, {len(w.cases)} cases -> {out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
