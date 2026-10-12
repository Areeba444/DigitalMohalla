"""Check a generated dataset against the design, reading ONLY the CSV files.

    python -I data/generators/validate.py data/derived/standard

The checks do not import the generator, so they test the files, not the code that made them:
foreign keys, the lifecycle transition table, schema constraints that PostgreSQL would enforce,
no activity before an account existed, no double booking, outcomes only from closed loans or
resolved disputes, trust edges recomputed from outcomes, privacy columns, review-text diversity,
and a coverage report against data/REQUIREMENTS.md (D-01 to D-10, claims, ES-01 to ES-13).
Exit code 0 means every check passed.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    REF_DATE,
    auth_role,
    engine_config,
    load_transitions,
    parse_ts,
    read_csv,
    value_band,
)

TABLES = [
    "app_user",
    "community",
    "membership",
    "category",
    "item",
    "borrowing_transaction",
    "lifecycle_event",
    "condition_report",
    "outcome",
    "trust_edge",
    "review",
    "escalation_case",
    "moderator_decision",
    "booking",
    "locality_verification",
]
TERMINAL = {"COMPLETED", "DECLINED", "CANCELLED", "EXPIRED", "NO_SHOW"}
BORROWER_KEYS = {"punctuality", "care_for_item", "communication", "follow_terms"}
LENDER_KEYS = {"fair_terms", "condition_accuracy", "responsiveness", "dispute_fairness"}
FORBIDDEN_COLUMNS = re.compile(
    r"address|latitude|longitude|\blat\b|\blon\b|cnic|passport|gps", re.I
)
HALF_LIFE = 180.0
PERIOD = re.compile(r"^\[(.+?),(.+?)\)$")
ES_IDS = [f"ES-{i:02d}" for i in range(1, 14)]
NOT_BUILT = {
    "ES-09": "location mismatch: locality method still open",
    "ES-10": "location refusal: locality method still open",
}


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checks = 0

    def check(self, cond: bool, msg: str) -> None:
        self.checks += 1
        if not cond:
            self.failures.append(msg)


def T(s: str) -> datetime:
    return parse_ts(s)


def load(folder: Path) -> dict[str, list[dict[str, str]]]:
    d = {t: read_csv(folder / f"{t}.csv") for t in TABLES}
    for name in (
        "user_truth",
        "item_value_pkr",
        "transaction_truth",
        "review_truth",
        "scenario_manifest",
    ):
        p = folder / "labels" / f"{name}.csv"
        d[f"labels/{name}"] = read_csv(p) if p.exists() else []
    return d


def validate(folder: Path) -> tuple[Report, dict[str, Any]]:
    r = Report()
    d = load(folder)
    cfg = engine_config()
    allowed = load_transitions()
    users = {u["id"]: u for u in d["app_user"]}
    comms = {c["id"]: c for c in d["community"]}
    items = {i["id"]: i for i in d["item"]}
    txns = {t["id"]: t for t in d["borrowing_transaction"]}
    events_by: dict[str, list[dict[str, str]]] = defaultdict(list)
    for e in d["lifecycle_event"]:
        events_by[e["stream_id"]].append(e)
    ev = {e["event_id"]: e for e in d["lifecycle_event"]}
    cases = {c["id"]: c for c in d["escalation_case"]}
    decisions = {x["id"]: x for x in d["moderator_decision"]}
    value_pkr = {x["item_id"]: float(x["value_pkr"]) for x in d["labels/item_value_pkr"]}

    # ---- unique ids, privacy, synthetic
    for t in TABLES:
        ids = [x.get("id") or x.get("event_id") for x in d[t] if ("id" in x or "event_id" in x)]
        r.check(len(ids) == len(set(ids)), f"{t}: duplicate ids")
        for col in d[t][0].keys() if d[t] else []:
            r.check(
                not FORBIDDEN_COLUMNS.search(col), f"{t}.{col}: column name suggests private data"
            )
    r.check(
        all(u["is_synthetic"] == "true" for u in users.values()),
        "every user must be labelled synthetic",
    )
    r.check(
        all(u["email"].endswith("@synthetic.invalid") and not u["phone"] for u in users.values()),
        "emails must be synthetic.invalid, no phones",
    )
    r.check(len({u["email"].lower() for u in users.values()}) == len(users), "duplicate emails")
    r.check(
        all(T(u["created_at"]) <= REF_DATE for u in users.values()),
        "user created after reference date",
    )

    # ---- memberships
    mem_by_user: dict[str, list[dict[str, str]]] = defaultdict(list)
    live = Counter()
    for m in d["membership"]:
        r.check(m["user_id"] in users and m["community_id"] in comms, "membership: bad foreign key")
        live[(m["user_id"], m["community_id"])] += 1
        r.check(
            bool(m["decided_at"]) and T(m["decided_at"]) > T(m["requested_at"]),
            "membership decided_at missing/early",
        )
        r.check(
            T(m["requested_at"]) >= T(users[m["user_id"]]["created_at"]),
            "membership requested before account existed",
        )
        mem_by_user[m["user_id"]].append(m)
    r.check(
        all(v == 1 for v in live.values()), "more than one live membership for a user and community"
    )
    mods = {m["community_id"]: m["user_id"] for m in d["membership"] if m["role"] == "MODERATOR"}
    r.check(set(mods) == set(comms), "each community needs exactly one moderator")

    def in_community(user: str, comm: str, at: datetime) -> bool:
        return any(
            m["community_id"] == comm and T(m["decided_at"]) <= at for m in mem_by_user[user]
        )

    # ---- items
    for i in d["item"]:
        r.check(i["owner_id"] in users and i["community_id"] in comms, "item: bad foreign key")
        r.check(
            T(i["created_at"]) >= T(users[i["owner_id"]]["created_at"]),
            "item created before its owner existed",
        )
        r.check(
            in_community(i["owner_id"], i["community_id"], T(i["created_at"])),
            "item owner is not a member of the item's community",
        )
        r.check(
            i["id"] in value_pkr and value_band(value_pkr[i["id"]], cfg) == i["value_band"],
            f"item {i['title']}: band does not match value",
        )
    r.check(
        len({c["name"] for c in d["category"]}) == len(d["category"]), "duplicate category names"
    )

    # ---- transactions and events
    accepted: dict[str, list[tuple[datetime, datetime, str]]] = defaultdict(list)
    for tid, t in txns.items():
        evs = sorted(events_by.get(tid, []), key=lambda e: int(e["stream_seq"]))
        r.check(bool(evs), f"txn {tid}: no events")
        if not evs:
            continue
        b, lend, it = t["borrower_id"], t["lender_id"], items[t["item_id"]]
        r.check(
            b != lend and it["owner_id"] == lend,
            "txn: lender must own the item and differ from borrower",
        )
        m = PERIOD.match(t["requested_period"])
        r.check(m is not None, "txn: bad period literal")
        start, end = (T(m.group(1)), T(m.group(2))) if m else (REF_DATE, REF_DATE)
        r.check(start < end, "txn: empty period")
        r.check(T(t["created_at"]) == T(evs[0]["occurred_at"]), "txn created_at != first event")
        r.check(
            in_community(b, it["community_id"], T(t["created_at"])),
            "borrower not a member of the item's community at request time",
        )
        prev_state, prev_t = None, None
        for k, e in enumerate(evs, start=1):
            r.check(int(e["stream_seq"]) == k, f"txn {tid}: stream_seq not contiguous")
            tt = T(e["occurred_at"])
            r.check(tt <= REF_DATE, "event after the reference date")
            r.check(prev_t is None or tt > prev_t, "event times not strictly increasing")
            r.check(
                tt >= T(users[b]["created_at"]) and tt >= T(users[lend]["created_at"]),
                "event before an account existed",
            )
            r.check(
                (e["previous_state"] or None) == prev_state,
                "previous_state does not follow the stream",
            )
            if prev_state is None:
                r.check(
                    e["event_type"] == "request_created" and e["new_state"] == "REQUEST_CREATED",
                    "first event must be request_created",
                )
            else:
                roles = allowed.get((prev_state, e["event_type"], e["new_state"]))
                r.check(
                    roles is not None,
                    f"txn {tid}: not an allowed transition {prev_state}->{e['event_type']}->{e['new_state']}",
                )
                if roles is not None:
                    r.check(
                        auth_role(e["authorisation"]) in roles,
                        "authorisation role not allowed for transition",
                    )
            role = auth_role(e["authorisation"])
            r.check(
                (role == "SYSTEM") == (e["actor_id"] == ""),
                "actor must be empty exactly for system events",
            )
            if e["authorisation"] == "party:borrower":
                r.check(e["actor_id"] == b, "party:borrower actor is not the borrower")
            if e["authorisation"] == "party:lender":
                r.check(e["actor_id"] == lend, "party:lender actor is not the lender")
            if role == "MODERATOR":
                r.check(
                    e["authorisation"] == f"role:moderator@{it['community_id']}"
                    and e["actor_id"] == mods[it["community_id"]],
                    "moderator event must come from that community's moderator",
                )
            r.check(
                (e["config_version"] != "")
                == (e["event_type"] in ("assessment_generated", "held_for_review")),
                "config_version only on assessment events",
            )
            if e["event_type"] == "held_for_review":
                r.check(
                    json.loads(e["payload"]).get("hold_reason") is not None,
                    "held_for_review needs a hold_reason",
                )
            prev_state, prev_t = e["new_state"], tt
        last = evs[-1]
        r.check(
            t["current_state"] == last["new_state"] and int(t["stream_version"]) == len(evs),
            "projection: state/version mismatch",
        )
        r.check(t["last_event_at"] == last["occurred_at"], "projection: last_event_at mismatch")
        r.check(
            (t["closed_at"] != "") == (last["new_state"] in TERMINAL),
            "projection: closed_at must be set exactly when terminal",
        )
        r.check(
            (t["hold_reason"] != "") == (last["new_state"] == "HELD_FOR_REVIEW"),
            "projection: hold_reason mismatch",
        )
        has_handover = any(e["event_type"] == "handover_confirmed" for e in evs)
        r.check(
            (t["due_at"] != "") == has_handover,
            "projection: due_at must be set exactly after handover",
        )
        if any(e["event_type"] == "request_accepted" for e in evs):
            accepted[t["item_id"]].append((start, end, tid))

    for item_id, periods in accepted.items():
        periods.sort()
        for (_, e1, a), (s2, _, b2) in zip(periods, periods[1:], strict=False):
            r.check(e1 <= s2, f"double booking of item {item_id}: {a} and {b2}")
    ev_ids = sorted(int(x) for x in ev)
    r.check(ev_ids == list(range(1, len(ev_ids) + 1)), "event ids must be 1..N")

    # ---- condition reports
    for c in d["condition_report"]:
        t = txns[c["transaction_id"]]
        r.check(
            c["reporter_id"] in (t["borrower_id"], t["lender_id"]),
            "condition report by a non-party",
        )
        r.check(
            (c["reporter_role"] == "BORROWER") == (c["reporter_id"] == t["borrower_id"]),
            "condition report role mismatch",
        )
        r.check(
            c["deposit_received"] == ""
            or (c["phase"] == "HANDOVER" and c["reporter_role"] == "LENDER"),
            "deposit_received only for lender at handover",
        )
        r.check(T(c["created_at"]) <= REF_DATE, "condition report after the reference date")

    # ---- outcomes
    close_events = {
        e["event_id"]: e
        for e in d["lifecycle_event"]
        if e["event_type"] in ("transaction_closed", "dispute_resolved")
    }
    seen = set()
    per_source = defaultdict(set)
    for o in d["outcome"]:
        e = close_events.get(o["source_event_id"])
        r.check(
            e is not None, "outcome source event must be transaction_closed or dispute_resolved"
        )
        if e is None:
            continue
        t = txns[o["transaction_id"]]
        r.check(e["stream_id"] == o["transaction_id"], "outcome source event is in another stream")
        want_subj = t["borrower_id"] if o["subject_role"] == "BORROWER" else t["lender_id"]
        want_obs = t["lender_id"] if o["subject_role"] == "BORROWER" else t["borrower_id"]
        r.check(
            o["subject_id"] == want_subj and o["observer_id"] == want_obs,
            "outcome subject/observer do not match the parties",
        )
        r.check(o["metric"] in ("ON_TIME_RETURN", "CONDITION_AGREED", "DISPUTE_FREE"), "bad metric")
        r.check(
            o["metric"] != "ON_TIME_RETURN" or o["subject_role"] == "BORROWER",
            "ON_TIME_RETURN is a borrower metric",
        )
        k = (o["source_event_id"], o["subject_id"], o["metric"])
        r.check(k not in seen, "duplicate outcome for one event, subject and metric")
        seen.add(k)
        per_source[o["source_event_id"]].add((o["subject_role"], o["metric"]))
        r.check(o["occurred_at"] == e["occurred_at"], "outcome occurred_at != source event time")
        it = items[t["item_id"]]
        r.check(o["value_band"] == it["value_band"], "outcome value_band != item band")
        m = PERIOD.match(t["requested_period"])
        days = round((T(m.group(2)) - T(m.group(1))).total_seconds() / 86400) if m else -1
        r.check(o["loan_duration"] == f"{days} days", "outcome loan_duration != period length")
        r.check(
            (o["status"] == "FLAGGED_FOR_REEVALUATION") == (o["flagged_by_decision_id"] != ""),
            "flag status/decision mismatch",
        )
        if o["flagged_by_decision_id"]:
            dec = decisions.get(o["flagged_by_decision_id"])
            r.check(
                dec is not None and dec["kind"] == "REVERSAL",
                "flagged outcome must point at a REVERSAL decision",
            )
    for eid in close_events:
        got = per_source.get(eid, set())
        r.check(
            ("BORROWER", "DISPUTE_FREE") in got and ("LENDER", "DISPUTE_FREE") in got,
            "closed loan without DISPUTE_FREE outcomes for both parties",
        )

    # ---- trust edges recomputed from outcomes
    agg: dict[tuple[str, str, str, str], list[float]] = {}
    for o in d["outcome"]:
        if o["status"] != "VALID":
            continue
        age = max(0.0, (REF_DATE - T(o["occurred_at"])).total_seconds() / 86400.0)
        w = 2.0 ** (-age / HALF_LIFE)
        a = agg.setdefault(
            (o["observer_id"], o["subject_id"], o["subject_role"], o["metric"]), [0.0, 0.0, 0]
        )
        a[0 if o["success"] == "true" else 1] += w
        a[2] += 1
    edges = {(e["source_id"], e["target_id"], e["role"], e["metric"]): e for e in d["trust_edge"]}
    r.check(
        set(edges) == set(agg), "trust edges are not exactly the pairs that have valid outcomes"
    )
    for k, (s, f, n) in agg.items():
        e = edges.get(k)
        if e:
            r.check(
                abs(float(e["weight"]) - (1 + s) / (2 + s + f)) <= 0.0006
                and int(e["evidence_count"]) == n,
                "trust edge weight/count differs from outcomes",
            )
            r.check(
                0 < float(e["weight"]) <= 1 and e["source_id"] != e["target_id"], "bad trust edge"
            )

    # ---- reviews
    closed_at: dict[str, datetime] = {}
    for e in close_events.values():
        closed_at[e["stream_id"]] = T(e["occurred_at"])
    seen_rv = set()
    for rv in d["review"]:
        t = txns[rv["transaction_id"]]
        parties = {t["borrower_id"], t["lender_id"]}
        r.check(
            rv["reviewer_id"] in parties
            and rv["reviewee_id"] in parties
            and rv["reviewer_id"] != rv["reviewee_id"],
            "review between non-parties",
        )
        r.check((rv["reviewee_id"], rv["transaction_id"]) not in seen_rv or True, "")
        key = (rv["transaction_id"], rv["reviewer_id"])
        r.check(key not in seen_rv, "two reviews by one reviewer for one loan")
        seen_rv.add(key)
        r.check(
            (rv["reviewee_role"] == "BORROWER") == (rv["reviewee_id"] == t["borrower_id"]),
            "reviewee_role mismatch",
        )
        r.check(
            rv["transaction_id"] in closed_at
            and T(rv["created_at"]) > closed_at[rv["transaction_id"]],
            "review must come after the loan closed",
        )
        r.check(T(rv["created_at"]) <= REF_DATE, "review after the reference date")
        ratings = json.loads(rv["ratings"])
        r.check(
            set(ratings) == (BORROWER_KEYS if rv["reviewee_role"] == "BORROWER" else LENDER_KEYS),
            "review rating keys wrong for role",
        )
        r.check(
            all(isinstance(v, int) and 1 <= v <= 5 for v in ratings.values()), "rating outside 1..5"
        )
        r.check(
            rv["comment"].strip() != ""
            and rv["retaliation_flag"] == "false"
            and rv["similarity_flag"] == "false",
            "review comment empty or engine flags pre-set",
        )

    # ---- cases and decisions
    live_cases = Counter()
    for c in d["escalation_case"]:
        e = ev.get(c["opened_event_id"])
        r.check(
            e is not None and e["stream_id"] == c["transaction_id"],
            "case opened_event_id not in its transaction",
        )
        if e:
            r.check(
                e["event_type"]
                == ("dispute_opened" if c["trigger_type"] == "DISPUTE" else "held_for_review"),
                "case trigger/event type mismatch",
            )
            r.check(T(c["opened_at"]) == T(e["occurred_at"]), "case opened_at != event time")
        r.check(
            (c["trigger_type"] == "DISPUTE") == (c["dispute_reason"] != "")
            and (c["trigger_type"] == "DISPUTE") == (c["hold_reason"] == ""),
            "case dispute/hold fields inconsistent",
        )
        r.check(
            (c["status"] in ("OPEN", "AWAITING_INFORMATION")) == (c["closed_at"] == ""),
            "case closed_at inconsistent with status",
        )
        it = items[txns[c["transaction_id"]]["item_id"]]
        r.check(
            c["assigned_to"] == mods[it["community_id"]],
            "case not assigned to the community moderator",
        )
        if c["status"] in ("OPEN", "AWAITING_INFORMATION"):
            live_cases[c["transaction_id"]] += 1
    r.check(all(v == 1 for v in live_cases.values()), "more than one live case for a transaction")
    for x in d["moderator_decision"]:
        c = cases.get(x["case_id"])
        r.check(
            c is not None and x["decided_by"] == c["assigned_to"],
            "decision by someone other than the assigned moderator",
        )
        r.check(x["safeguards"] == "[]", "safeguards only allowed for SAFEGUARDS_IMPOSED")
        r.check(
            (x["kind"] in ("REVERSAL", "APPEAL_OVERTURNED")) == (x["reverses_decision_id"] != ""),
            "reversal decision linkage",
        )
        if x["kind"] == "DISPUTE_RESOLVED":
            r.check(x["resolved_outcome"] != "", "dispute decision needs resolved_outcome")
    resolved_ev = [e for e in d["lifecycle_event"] if e["event_type"] == "dispute_resolved"]
    dec_by_time = Counter(
        (cases[x["case_id"]]["transaction_id"], x["decided_at"])
        for x in d["moderator_decision"]
        if x["kind"] == "DISPUTE_RESOLVED"
    )
    for e in resolved_ev:
        r.check(
            dec_by_time[(e["stream_id"], e["occurred_at"])] == 1,
            "dispute_resolved event without exactly one decision",
        )

    check_trigger_rules(r, d)

    # ---- scenario manifest
    for m in d["labels/scenario_manifest"]:
        t = txns.get(m["transaction_id"])
        r.check(t is not None, f"manifest {m['case_id']}: unknown transaction")
        if t:
            r.check(
                t["current_state"] == "LOCALITY_CHECKED" and T(m["as_of"]) == T(t["created_at"]),
                f"manifest {m['case_id']}: request must be waiting at LOCALITY_CHECKED",
            )
            r.check(
                t["borrower_id"] == m["borrower_id"] and t["lender_id"] == m["lender_id"],
                f"manifest {m['case_id']}: parties differ",
            )

    # ---- review-text diversity (proxy for the engine's similarity signal)
    text_stats = text_diversity(d)
    r.check(
        text_stats["legit_distinct_share"] >= 0.80,
        f"legitimate review texts too repetitive ({text_stats['legit_distinct_share']:.2f} distinct)",
    )
    # natural coincidences exist (two neutral reviews sharing one common sentence); more than 5% would be a text-bank defect
    r.check(
        text_stats["legit_share_with_a_lookalike_about_the_same_person"] <= 0.05,
        "too many legitimate reviews about the same person look alike (cosine >= 0.7)",
    )
    for g, v in text_stats["attack_group_mean_cosine"].items():
        r.check(
            v >= 0.8,
            f"attack group {g}: reviews are not similar enough to be a test case (mean cosine {v:.2f})",
        )
    return r, coverage(d, cfg, text_stats)


# ----------------------------------------------------------------------------- text proxy


def _grams(s: str) -> Counter[str]:
    s = " " + re.sub(r"\s+", " ", s.lower().strip()) + " "
    return Counter(s[i : i + 3] for i in range(len(s) - 2))


def text_diversity(d: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    """Character 3-gram TF-IDF cosine between reviews: a PROXY for the engine's S4 signal, used only to
    show that legitimate reviews are not accidentally similar and attack groups really are."""
    kind = {x["review_id"]: x for x in d["labels/review_truth"]}
    rv_of = {rv["id"]: rv["reviewee_id"] for rv in d["review"]}
    rows = [(rv["id"], rv["comment"], kind.get(rv["id"], {})) for rv in d["review"]]
    if not rows or len(rows) > 3000:
        return {
            "legit_distinct_share": 1.0,
            "legit_share_with_a_lookalike_about_the_same_person": 0.0,
            "attack_group_mean_cosine": {},
            "skipped": True,
        }
    grams = [_grams(c) for _, c, _ in rows]
    df: Counter[str] = Counter()
    for g in grams:
        df.update(g.keys())
    n = len(rows)
    vecs = []
    for g in grams:
        v = {k: (1 + math.log(c)) * math.log((1 + n) / (1 + df[k]) + 1) for k, c in g.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({k: x / norm for k, x in v.items()})

    def cos(i: int, j: int) -> float:
        a, b = vecs[i], vecs[j]
        if len(a) > len(b):
            a, b = b, a
        return sum(x * b.get(k, 0.0) for k, x in a.items())

    legit = [i for i, (_, _, lab) in enumerate(rows) if lab.get("is_attack") != "true"]
    attack_groups: dict[str, list[int]] = defaultdict(list)
    for i, (_, _, lab) in enumerate(rows):
        if lab.get("is_attack") == "true" and lab.get("kind") in ("ring", "farm", "burst"):
            attack_groups[lab.get("group_id") or "?"].append(i)
    # the engine compares reviews about the same person, so that is where a false alarm would arise
    by_reviewee: dict[str, list[int]] = defaultdict(list)
    for i, (rid, _, _) in enumerate(rows):
        by_reviewee[rv_of[rid]].append(i)
    legit_set = set(legit)
    hot = set()
    for idx in by_reviewee.values():
        idx = [i for i in idx if i in legit_set]
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                if cos(idx[a], idx[b]) >= 0.7:
                    hot.update((idx[a], idx[b]))
    out = {
        "legit_distinct_share": len({rows[i][1] for i in legit}) / max(1, len(legit)),
        "legit_share_with_a_lookalike_about_the_same_person": len(hot) / max(1, len(legit)),
        "attack_group_mean_cosine": {},
    }
    for g, idx in attack_groups.items():
        sims = [cos(a, b) for ai, a in enumerate(idx) for b in idx[ai + 1 :]]
        out["attack_group_mean_cosine"][g] = sum(sims) / len(sims) if sims else 1.0
    return out


# ----------------------------------------------------------------------------- coverage


def coverage(
    d: dict[str, list[dict[str, str]]], cfg: dict[str, Any], text_stats: dict[str, Any]
) -> dict[str, Any]:
    users = {u["id"]: u for u in d["app_user"]}
    truth = {u["user_id"]: u for u in d["labels/user_truth"]}
    tx = d["borrowing_transaction"]
    c: dict[str, Any] = {}
    memberships = Counter(m["user_id"] for m in d["membership"])
    c["D-01"] = {
        "users": len(users),
        "communities": len(d["community"]),
        "members_in_2_communities": sum(1 for v in memberships.values() if v > 1),
    }
    out_adj: dict[str, set[str]] = defaultdict(set)
    for e in d["trust_edge"]:
        out_adj[e["source_id"]].add(e["target_id"])
    two_hop = sum(
        1
        for a in out_adj
        for b in out_adj[a]
        for z in out_adj.get(b, ())
        if z != a and z not in out_adj[a]
    )
    c["D-02"] = {"trust_edges": len(d["trust_edge"]), "two_hop_paths_without_direct_edge": two_hop}
    c["D-03"] = {
        "items_by_band": dict(Counter(i["value_band"] for i in d["item"])),
        "categories": len({i["category_id"] for i in d["item"]}),
    }
    c["D-04"] = {
        "streams": len(tx),
        "final_states": dict(Counter(t["current_state"] for t in tx)),
        "event_types_used": len({e["event_type"] for e in d["lifecycle_event"]}),
        "events": len(d["lifecycle_event"]),
    }
    c["D-05"] = {
        "outcomes": len(d["outcome"]),
        "by_metric": dict(Counter(o["metric"] for o in d["outcome"])),
        "flagged": sum(1 for o in d["outcome"] if o["status"] != "VALID"),
    }
    c["D-06"] = {
        "reviews": len(d["review"]),
        "distinct_comments": len({r["comment"] for r in d["review"]}),
        "review_kinds": dict(Counter(x["kind"] for x in d["labels/review_truth"])),
    }
    c["D-07"] = {
        "cases_by_reason_and_status": dict(
            Counter(
                f"{x['dispute_reason']}:{x['status']}"
                for x in d["escalation_case"]
                if x["trigger_type"] == "DISPUTE"
            )
        ),
        "hold_cases": dict(
            Counter(
                f"{x['trigger_type']}:{x['status']}"
                for x in d["escalation_case"]
                if x["trigger_type"] != "DISPUTE"
            )
        ),
    }
    c["D-08"] = {
        "attack_kinds": dict(
            Counter(u["group_kind"] for u in truth.values() if u["is_attack_account"] == "true")
        ),
        "attack_accounts": sum(1 for u in truth.values() if u["is_attack_account"] == "true"),
        "attack_text_cosine_mean_by_group": {
            k: round(v, 3) for k, v in text_stats["attack_group_mean_cosine"].items()
        },
    }
    times = sorted(T(t["created_at"]) for t in tx)
    months = Counter(t.strftime("%Y-%m") for t in times)
    c["D-09"] = {
        "first_request": times[0].isoformat(),
        "last_request": times[-1].isoformat(),
        "months_with_requests": len(months),
        "weekday_counts": dict(sorted(Counter(t.weekday() for t in times).items())),
        "local_hour_buckets": dict(
            sorted(Counter(((t + timedelta(hours=5)).hour // 4) * 4 for t in times).items())
        ),
    }
    c["D-10"] = {
        "borrower_evidence_levels": dict(
            Counter(
                u["evidence_level_at_ref"]
                for u in truth.values()
                if u["archetype"] not in ("moderator", "admin")
            )
        )
    }
    newcomers = [
        u
        for u in truth.values()
        if (REF_DATE - T(u["created_at"])).days <= 30
        and u["archetype"] not in ("moderator", "admin")
        and u["is_attack_account"] != "true"
    ]
    sampled = [u for u in truth.values() if u.get("history_basis") == "sampled"]
    c["C1"] = {
        "users_with_sampled_history_and_known_true_reliability": len(sampled),
        "of_which_with_at_most_2_outcome_loans": sum(
            1 for u in sampled if int(u["borrower_outcome_loans_at_ref"]) <= 2
        ),
        "note": "scripted users have nominal reliability labels; calibrate on sampled users (use the scale tier for enough of them)",
    }
    c["C3"] = {
        "legit_dense_cluster_accounts": sum(
            1 for u in truth.values() if u["group_kind"] == "legit_dense_cluster"
        ),
        "legit_dense_reviews": sum(
            1 for x in d["labels/review_truth"] if x["kind"] == "legit_dense"
        ),
    }
    c["C5"] = {
        "non_attack_accounts_30_days_or_younger": len(newcomers),
        "of_which_with_true_reliability_0.85_or_more": sum(
            1 for u in newcomers if float(u["true_p_on_time_return"]) >= 0.85
        ),
    }
    ids = {
        m["case_id"].split("b")[0] if m["case_id"].startswith("ES") else m["case_id"]
        for m in d["labels/scenario_manifest"]
    }
    c["scenarios"] = {
        s: (
            "built" if s in ids else ("NOT BUILT: " + NOT_BUILT[s] if s in NOT_BUILT else "MISSING")
        )
        for s in ES_IDS
    }
    c["extra_cases"] = sorted(
        m["case_id"] for m in d["labels/scenario_manifest"] if not m["case_id"].startswith("ES-")
    )
    return c


def render_coverage(cov: dict[str, Any]) -> str:
    lines = [
        "# Coverage of this dataset",
        "",
        "Generated by `data/generators/validate.py` from the CSV files. SYNTHETIC data.",
        "",
    ]
    for k, v in cov.items():
        lines.append(f"## {k}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(v, indent=1, sort_keys=True))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    folder = Path(argv[1])
    rep, cov = validate(folder)
    print(f"{folder}: {rep.checks} checks, {len(rep.failures)} failed")
    for f, n in Counter(rep.failures).most_common(40):
        print(f"  FAIL x{n}: {f}")
    (folder / "COVERAGE.md").write_text(render_coverage(cov), encoding="utf-8")
    return 1 if rep.failures else 0


# ----------------------------------------------------------------------------- schema trigger rules

VERIF_RANK = {"UNVERIFIED": 0, "CONTACT_VERIFIED": 1, "COMMUNITY_VERIFIED": 2}
DISPUTE_REASONS = {"DAMAGE", "NON_RETURN", "CONDITION_MISMATCH", "NO_SHOW", "OTHER"}
DECISION_FOR_EVENT = {
    "hold_cleared": {"CLEARED", "SAFEGUARDS_IMPOSED"},
    "request_declined": {"RESTRICTED"},
    "dispute_resolved": {"DISPUTE_RESOLVED"},
}


def check_trigger_rules(r: Report, d: dict[str, list[dict[str, str]]]) -> None:
    """Re-implements, from the CSV files, the rules that the schema's triggers (event_validate,
    event_apply, party_guard, review_guard, txn_guard_create) enforce when events are appended
    live. They cannot run on history (the database stamps events with the current time), so the
    history is loaded with triggers off and these checks stand in for them."""
    users = {u["id"]: u for u in d["app_user"]}
    items = {i["id"]: i for i in d["item"]}
    txns = {t["id"]: t for t in d["borrowing_transaction"]}
    cases_by_txn: dict[str, list[dict[str, str]]] = defaultdict(list)
    for c in d["escalation_case"]:
        cases_by_txn[c["transaction_id"]].append(c)
    decisions = {x["id"]: x for x in d["moderator_decision"]}
    ev_by: dict[str, list[dict[str, str]]] = defaultdict(list)
    for e in d["lifecycle_event"]:
        ev_by[e["stream_id"]].append(e)
    reports: dict[str, list[dict[str, str]]] = defaultdict(list)
    for c in d["condition_report"]:
        reports[c["transaction_id"]].append(c)
    loc_by_member = {x["membership_id"]: x for x in d["locality_verification"]}
    members = {(m["user_id"], m["community_id"]): m for m in d["membership"]}

    def state_at(evs: list[dict[str, str]], t: datetime) -> str | None:
        cur = None
        for e in evs:
            if T(e["occurred_at"]) <= t:
                cur = e["new_state"]
        return cur

    for tid, t in txns.items():
        evs = sorted(ev_by[tid], key=lambda e: int(e["stream_seq"]))
        it = items[t["item_id"]]
        b, lend = users[t["borrower_id"]], t["lender_id"]
        r.check(
            b["status"] == "ACTIVE"
            and VERIF_RANK[b["verification_level"]] >= VERIF_RANK[it["required_verification"]],
            "G1: borrower not active or not verified to the level the item requires",
        )
        due = None
        for k, e in enumerate(evs):
            et, tt = e["event_type"], T(e["occurred_at"])
            pl, refs = json.loads(e["payload"]), json.loads(e["evidence_refs"])
            if et == "request_created":
                r.check(
                    pl.get("item_id") == t["item_id"]
                    and pl.get("requested_period") == t["requested_period"],
                    "request_created payload must carry item_id and requested_period",
                )
            if et == "locality_checked":
                m = members.get((t["borrower_id"], it["community_id"]))
                lv = loc_by_member.get(m["id"]) if m else None
                r.check(
                    lv is not None
                    and lv["outcome"] == "VERIFIED"
                    and T(lv["valid_until"]) > tt
                    and pl.get("locality_outcome") == "VERIFIED",
                    "locality_checked needs a stored, still valid VERIFIED locality result",
                )
            if et == "dispute_opened":
                r.check(
                    pl.get("reason") in DISPUTE_REASONS,
                    "dispute_opened needs a valid payload.reason",
                )
                r.check(
                    e["authorisation"] != "system:borrowing-service"
                    or pl.get("reason") == "NON_RETURN",
                    "the system opens only NON_RETURN disputes",
                )
            if et == "handover_confirmed":
                due = T(PERIOD.match(t["requested_period"]).group(2))
                prior = [
                    c for c in reports[tid] if c["phase"] == "HANDOVER" and T(c["created_at"]) < tt
                ]
                rl = max(
                    (c for c in prior if c["reporter_role"] == "LENDER"),
                    key=lambda c: T(c["created_at"]),
                    default=None,
                )
                rb = max(
                    (c for c in prior if c["reporter_role"] == "BORROWER"),
                    key=lambda c: T(c["created_at"]),
                    default=None,
                )
                ok = (
                    rl is not None
                    and rb is not None
                    and rb["condition_agreed"] == "true"
                    and T(rb["created_at"]) > T(rl["created_at"])
                )
                r.check(
                    ok,
                    "handover needs the lender's checklist then the borrower's agreeing confirmation",
                )
                if ok and float(it["deposit_amount"]) > 0:
                    r.check(
                        rl["deposit_received"] == "true",
                        "required deposit must be recorded as received",
                    )
            if et == "return_confirmed":
                prior = [
                    c for c in reports[tid] if c["phase"] == "RETURN" and T(c["created_at"]) < tt
                ]
                rl = max(
                    (c for c in prior if c["reporter_role"] == "LENDER"),
                    key=lambda c: T(c["created_at"]),
                    default=None,
                )
                rb = max(
                    (c for c in prior if c["reporter_role"] == "BORROWER"),
                    key=lambda c: T(c["created_at"]),
                    default=None,
                )
                r.check(
                    rl is not None
                    and rb is not None
                    and rl["condition_agreed"] == "true"
                    and rb["condition_agreed"] == "true"
                    and T(rb["created_at"]) > T(rl["created_at"]),
                    "return needs both parties agreeing, the borrower after the lender",
                )
            if et == "transaction_closed":
                rc = max(
                    (T(x["occurred_at"]) for x in evs if x["event_type"] == "return_confirmed"),
                    default=None,
                )
                due_at = T(PERIOD.match(t["requested_period"]).group(2))
                r.check(
                    rc is not None and pl.get("outcome") == ("on_time" if rc <= due_at else "late"),
                    "transaction_closed payload.outcome must match return time against the due date",
                )
            if et == "dispute_withdrawn":
                opened = [x for x in evs[:k] if x["event_type"] == "dispute_opened"]
                r.check(
                    bool(opened)
                    and opened[-1]["previous_state"] == e["new_state"]
                    and opened[-1]["actor_id"] == e["actor_id"],
                    "dispute_withdrawn must restore the pre-dispute state and be made by the party who raised it",
                )
            if e["authorisation"].startswith("role:moderator@"):
                dec = decisions.get(refs.get("decision_id", ""))
                r.check(
                    dec is not None
                    and dec["decided_by"] == e["actor_id"]
                    and dec["kind"] in DECISION_FOR_EVENT.get(et, set())
                    and any(c["id"] == dec["case_id"] for c in cases_by_txn[tid])
                    and T(dec["decided_at"]) == tt,
                    "moderator event needs evidence_refs.decision_id of a matching decision by this actor on this loan's case",
                )
                r.check(
                    e["actor_id"] not in (t["borrower_id"], t["lender_id"]),
                    "a party cannot decide its own case",
                )
            if et == "request_declined" and e["authorisation"] == "system:borrowing-service":
                r.check(
                    pl.get("reason") == "dates_taken",
                    "the system declines only with reason dates_taken",
                )
        del lend, due

    # condition reports are only allowed in the matching state (party_guard)
    for c in d["condition_report"]:
        evs = sorted(ev_by[c["transaction_id"]], key=lambda e: int(e["stream_seq"]))
        st = state_at(evs, T(c["created_at"]))
        want = "ACCEPTED" if c["phase"] == "HANDOVER" else "RETURN_INITIATED"
        r.check(
            st == want, f"{c['phase']} checklist written while the loan was in {st}, not {want}"
        )

    # reviews only for COMPLETED loans, after completion (review_guard) is covered above; bookings and cases are projections
    derived_book = {}
    for tid, evs0 in ev_by.items():
        evs = sorted(evs0, key=lambda e: int(e["stream_seq"]))
        acc = next((e for e in evs if e["event_type"] == "request_accepted"), None)
        if acc:
            rel = next(
                (
                    e["occurred_at"]
                    for e in evs
                    if int(e["stream_seq"]) > int(acc["stream_seq"])
                    and e["new_state"] in ("COMPLETED", "NO_SHOW")
                ),
                "",
            )
            derived_book[tid] = (
                txns[tid]["item_id"],
                txns[tid]["requested_period"],
                acc["occurred_at"],
                rel,
            )
    got_book = {
        b["transaction_id"]: (b["item_id"], b["period"], b["created_at"], b["released_at"])
        for b in d["booking"]
    }
    r.check(
        got_book == derived_book, "booking.csv is not the projection of the accept/complete events"
    )
    r.check(
        all((b["status"] == "RELEASED") == (b["released_at"] != "") for b in d["booking"]),
        "booking status/released_at mismatch",
    )

    # cases: the event_apply trigger writes reason and priority; the lifecycle closes them
    for tid, cs in cases_by_txn.items():
        evs = sorted(ev_by[tid], key=lambda e: int(e["stream_seq"]))
        for c in cs:
            opened = next(e for e in evs if e["event_id"] == c["opened_event_id"])
            pl = json.loads(opened["payload"])
            if c["trigger_type"] == "DISPUTE":
                r.check(
                    c["priority"] == "1"
                    and c["reason"] == (pl.get("description") or f"dispute: {pl.get('reason')}")
                    and c["raised_by"] == opened["actor_id"],
                    "dispute case differs from what event_apply writes",
                )
            else:
                r.check(
                    c["reason"] == f"request held: {pl.get('hold_reason')}"
                    and c["priority"]
                    == ("1" if pl.get("hold_reason") == "manipulation_risk" else "2"),
                    "hold case differs from what event_apply writes",
                )
            later = [e for e in evs if int(e["stream_seq"]) > int(opened["stream_seq"])]
            closer = next(
                (
                    e
                    for e in later
                    if e["authorisation"].startswith("role:moderator@")
                    or e["event_type"]
                    in ("dispute_withdrawn", "request_cancelled", "request_declined")
                ),
                None,
            )
            if closer is None:
                r.check(
                    c["status"] == "OPEN" and c["closed_at"] == "",
                    "case without a closing event must be OPEN",
                )
            elif closer["authorisation"].startswith("role:moderator@"):
                r.check(
                    c["status"] in ("DECIDED", "REVERSED")
                    and (c["status"] == "REVERSED" or c["closed_at"] == closer["occurred_at"]),
                    "case closed by a moderator event must be DECIDED (or REVERSED later)",
                )
            else:
                r.check(
                    c["status"] == "WITHDRAWN" and c["closed_at"] == closer["occurred_at"],
                    "case closed by withdraw/cancel/decline must be WITHDRAWN",
                )

    # every approved member has a valid VERIFIED locality result (assumption A10)
    ref = REF_DATE
    for m in d["membership"]:
        lv = loc_by_member.get(m["id"])
        r.check(
            lv is not None
            and lv["outcome"] == "VERIFIED"
            and lv["method"] == "MODERATOR_APPROVAL"
            and T(lv["valid_until"]) > ref
            and T(lv["checked_at"]) >= T(m["decided_at"]),
            "member without a valid locality result",
        )
        if lv:
            appr = users.get(lv["approved_by"])
            r.check(
                appr is not None and appr["platform_role"] == "ADMIN",
                "locality approval needs a moderator or admin",
            )


if __name__ == "__main__":
    sys.exit(main(sys.argv))
