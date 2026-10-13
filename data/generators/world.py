"""The simulated neighbourhood: users, items, loans as event streams, outcomes, reviews, disputes.

All data is SYNTHETIC. This module only records what happens; the cast of people and the story
of each scenario are decided elsewhere (population.py, scenarios.py, attacks_dev.py).

Design points (plain language):
  * A loan is a stream of lifecycle events. Every event is checked against the backend's own
    transition table (transition_leaves.csv), so the data can be replayed by the real lifecycle
    code. Nothing after the reference date exists.
  * Outcomes (the evidence the trust engine learns from) are written only when a loan closes
    (transaction_closed) or a dispute is resolved (dispute_resolved). A loan that is still open,
    or a dispute that is still open, has no outcome yet, exactly as the design says.
  * The engine's OWN results (assessments, trust scores) are never written here: they are what
    the engine must compute from this data. Hidden ground truth goes to the labels/ files only.
  * Trust edges are derived from outcomes with the recency-weighted Beta posterior mean of
    ADR-0006 (proposed, not yet signed by Student 2): (1 + s_w) / (2 + s_w + f_w).
"""

from __future__ import annotations

import math
import random
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import texts
from common import (
    REF_DATE,
    SYSTEM_AUTH,
    auth_role,
    engine_config,
    load_transitions,
    range_literal,
    rng_for,
    uid,
    value_band,
)

CATEGORIES = ["tools", "appliances", "electronics", "furniture", "sports", "outdoor", "media"]

# (title, typical value in PKR, category). Values are jittered per item. The first fifteen come from
# the earlier community generator; the rest add the high-value items it lacked (band HIGH > 15,000).
CATALOG = [
    ("Power Drill", 3500, "tools"),
    ("Rice Cooker", 2000, "appliances"),
    ("Laptop Charger", 1200, "electronics"),
    ("Coffee Table", 5000, "furniture"),
    ("Bicycle", 8000, "sports"),
    ("Tent", 4000, "outdoor"),
    ("Books (set)", 800, "media"),
    ("Pressure Cooker", 2500, "appliances"),
    ("Extension Cord", 600, "electronics"),
    ("Camping Stove", 3000, "outdoor"),
    ("Sewing Machine", 6000, "tools"),
    ("Baby Stroller", 9000, "furniture"),
    ("Cricket Kit", 4500, "sports"),
    ("Generator", 15000, "tools"),
    ("Juicer", 1800, "appliances"),
    ("Ladder", 4500, "tools"),
    ("Folding Chairs (set)", 3200, "furniture"),
    ("Hand Mixer", 1500, "appliances"),
    ("Badminton Set", 1400, "sports"),
    ("Pressure Washer", 18000, "tools"),
    ("Projector", 32000, "electronics"),
    ("Wedding Tent Set", 45000, "outdoor"),
    ("Industrial Sewing Machine", 22000, "tools"),
    ("DSLR Camera", 60000, "electronics"),
    ("Treadmill", 30000, "sports"),
    ("Dining Table Set", 28000, "furniture"),
    ("Party Speaker", 16500, "electronics"),
]
LOW_CATALOG = [c for c in CATALOG if c[1] <= 5000]
MID_CATALOG = [c for c in CATALOG if 5000 < c[1] <= 15000]
HIGH_CATALOG = [c for c in CATALOG if c[1] > 15000]

TERMINAL = {"COMPLETED", "DECLINED", "CANCELLED", "EXPIRED", "NO_SHOW"}
BORROWER_METRICS = ["punctuality", "care_for_item", "communication", "follow_terms"]
LENDER_METRICS = ["fair_terms", "condition_accuracy", "responsiveness", "dispute_fairness"]
HALF_LIFE_DAYS = 180.0


@dataclass
class User:
    alias: str
    name: str
    community: str
    created_at: datetime
    verification: str = "COMMUNITY_VERIFIED"
    archetype: str = "steady_average"
    p_on_time: float = 0.85
    p_cond: float = 0.9
    p_lender_cond: float = 0.95
    is_moderator: bool = False
    is_admin: bool = False
    extra_communities: list[str] = field(default_factory=list)
    group: str | None = None
    group_kind: str | None = None
    group_role: str | None = None
    split: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return uid("user", self.alias)


@dataclass
class Item:
    alias: str
    owner: str
    community: str
    category: str
    title: str
    value_pkr: int
    created_at: datetime
    deposit: int = 0
    busy: list[tuple[datetime, datetime]] = field(default_factory=list)

    @property
    def id(self) -> str:
        return uid("item", self.alias)

    @property
    def band(self) -> str:
        return value_band(self.value_pkr)


@dataclass
class DisputePlan:
    reason: str  # DAMAGE | NON_RETURN | CONDITION_MISMATCH | OTHER
    stage: str  # ACCEPTED | ACTIVE | RETURN_INITIATED
    opener: str = "lender"  # borrower | lender
    open_delay_h: float = 6.0
    resolve_after_days: float | None = 4.0  # None: still open at the reference date
    fault: str = "borrower"  # borrower | lender | none
    withdrawn: bool = False
    conflicting: bool = False  # RETURN stage: borrower says "same condition", lender says "not"
    reversal_after_days: float | None = None  # moderator reverses the decision (ES-11)


@dataclass
class LoanPlan:
    borrower: str
    lender: str
    item: str
    t_request: datetime
    path: str = "completed"  # completed|declined|cancelled|expired|no_show|pending
    lead_h: float = 30.0
    duration_days: int = 3
    respond_h: float = 6.0
    late_days: float = 0.0
    hold: str | None = None  # high_value_low_confidence | manipulation_risk
    hold_result: str = "cleared"  # cleared | declined
    dispute: DisputePlan | None = None
    auto_reviews: bool = True
    tags: list[str] = field(default_factory=list)
    group: str | None = None
    is_attack: bool = False
    note: str = ""


@dataclass
class Txn:
    alias: str
    plan: LoanPlan
    start: datetime
    end: datetime
    events: list[dict[str, Any]] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return uid("txn", self.alias)


class World:
    def __init__(self, tier: str, seed: int) -> None:
        self.tier = tier
        self.seed = seed
        self.cfg = engine_config()
        self.config_version = self.cfg["config_metadata"]["config_version"]
        self.allowed = load_transitions()
        self.communities: dict[str, dict[str, Any]] = {}
        self.users: dict[str, User] = {}
        self.items: dict[str, Item] = {}
        self.txns: dict[str, Txn] = {}
        self.cond_reports: list[dict[str, Any]] = []
        self.outcomes: list[dict[str, Any]] = []
        self.reviews: list[dict[str, Any]] = []
        self.cases: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []
        self.review_truth: list[dict[str, Any]] = []
        self.manifest: list[dict[str, Any]] = []
        self._mod_of: dict[str, str] = {}
        self._used_names: set[str] = set()
        self._name_rng = rng_for(seed, "names")
        self._open_case_of_txn: dict[str, dict[str, Any]] = {}
        self.history: dict[tuple[str, str], list[datetime]] = {}
        self.items_by_owner: dict[str, list[Item]] = {}
        self.bookings: list[dict[str, Any]] = []
        self._review_keys: set[tuple[str, str]] = set()
        self._rv_grams: dict[str, list[Counter[str]]] = {}

    # ------------------------------------------------------------------ people and things

    def add_community(self, alias: str, name: str, created_at: datetime) -> None:
        self.communities[alias] = {
            "alias": alias,
            "name": name,
            "created_at": created_at,
            "join_code": f"SYN-{alias.upper()}",
        }

    def fresh_name(self) -> str:
        for _ in range(500):
            n = f"{self._name_rng.choice(texts.FIRST_NAMES)} {self._name_rng.choice(texts.SURNAMES)}"
            if n not in self._used_names:
                self._used_names.add(n)
                return n
        n = f"{self._name_rng.choice(texts.FIRST_NAMES)} {self._name_rng.choice(texts.SURNAMES)} {len(self._used_names)}"
        self._used_names.add(n)
        return n

    def add_user(self, alias: str, community: str, created_at: datetime, **kw: Any) -> User:
        if alias in self.users:
            raise ValueError(f"duplicate user {alias}")
        u = User(
            alias=alias,
            name=kw.pop("name", None) or self.fresh_name(),
            community=community,
            created_at=created_at,
            **kw,
        )
        self.users[alias] = u
        if u.is_moderator:
            self._mod_of[community] = alias
        return u

    def add_item(
        self,
        alias: str,
        owner: str,
        title: str,
        value_pkr: int,
        category: str,
        created_at: datetime | None = None,
    ) -> Item:
        o = self.users[owner]
        created_at = created_at or (o.created_at + timedelta(days=1, hours=3))
        band = value_band(value_pkr, self.cfg)
        dep = 0 if band == "LOW" else int(round(value_pkr * 0.15, -2))
        it = Item(alias, owner, o.community, category, title, value_pkr, created_at, dep)
        self.items[alias] = it
        self.items_by_owner.setdefault(owner, []).append(it)
        return it

    def moderator(self, community: str) -> User:
        return self.users[self._mod_of[community]]

    # ------------------------------------------------------------------ loans

    def item_free(self, item: str, start: datetime, end: datetime) -> bool:
        return all(end <= s or start >= e for s, e in self.items[item].busy)

    def add_loan(self, p: LoanPlan) -> Txn:
        b, lend, it = self.users[p.borrower], self.users[p.lender], self.items[p.item]
        if it.owner != p.lender:
            raise ValueError("lender must own the item")
        if p.borrower == p.lender:
            raise ValueError("self loan")
        if p.t_request < max(b.created_at, lend.created_at, it.created_at) + timedelta(hours=2):
            raise ValueError(f"{p.borrower}/{p.lender} request before accounts/item existed")
        if p.t_request > REF_DATE:
            raise ValueError("request after the reference date")
        alias = f"T{len(self.txns) + 1:04d}"
        rng = rng_for(self.seed, f"loan:{alias}")
        t = _Timeline(self, alias, p, rng)
        txn = t.build()
        self.txns[alias] = txn
        return txn

    # ------------------------------------------------------------------ events

    def commit(self, txn: Txn, drafts: list[dict[str, Any]]) -> None:
        """Validate drafts as one stream, drop everything after the reference date, keep order."""
        prev_state: str | None = None
        last_t: datetime | None = None
        seq = 0
        for d in drafts:
            tt = d["t"]
            if last_t is not None and tt <= last_t:
                tt = last_t + timedelta(seconds=1)
            if tt > REF_DATE:
                break
            key = (prev_state, d["type"], d["new"])
            if prev_state is not None:
                roles = self.allowed.get((prev_state, d["type"], d["new"]))
                if roles is None:
                    raise ValueError(f"{txn.alias}: {key} is not an allowed transition")
                if auth_role(d["auth"]) not in roles:
                    raise ValueError(f"{txn.alias}: {d['auth']} may not do {key}")
            seq += 1
            ev = {
                "txn": txn.alias,
                "seq": seq,
                "type": d["type"],
                "t": tt,
                "actor": d["actor"],
                "auth": d["auth"],
                "prev": prev_state,
                "new": d["new"],
                "payload": d.get("payload") or {},
                "evidence_refs": {},
                "config_version": self.config_version
                if d["type"] in ("assessment_generated", "held_for_review")
                else None,
            }
            txn.events.append(ev)
            if d.get("effect"):
                d["effect"](ev)
            prev_state, last_t = d["new"], tt
        # booking: the database writes it when the lender accepts and releases it when the loan ends
        acc = next((e for e in txn.events if e["type"] == "request_accepted"), None)
        if acc:
            rel = next(
                (
                    e["t"]
                    for e in txn.events
                    if e["seq"] > acc["seq"] and e["new"] in ("COMPLETED", "NO_SHOW")
                ),
                None,
            )
            self.bookings.append(
                {
                    "txn": txn.alias,
                    "item": txn.plan.item,
                    "start": txn.start,
                    "end": txn.end,
                    "created_at": acc["t"],
                    "released_at": rel,
                }
            )

    # ------------------------------------------------------------------ cases, decisions, outcomes

    def open_case(
        self,
        txn: Txn,
        ev: dict[str, Any],
        trigger: str,
        *,
        reason: str,
        dispute_reason: str | None = None,
        hold_reason: str | None = None,
        raised_by: str | None = None,
        priority: int = 2,
    ) -> dict[str, Any]:
        mod = self.moderator(self.items[txn.plan.item].community)
        case = {
            "alias": f"C{len(self.cases) + 1:04d}",
            "txn": txn.alias,
            "ev": (txn.alias, ev["seq"]),
            "trigger": trigger,
            "hold_reason": hold_reason,
            "dispute_reason": dispute_reason,
            "raised_by": raised_by,
            "status": "OPEN",
            "priority": priority,
            "reason": reason,
            "assigned_to": mod.alias,
            "opened_at": ev["t"],
            "closed_at": None,
        }
        self.cases.append(case)
        self._open_case_of_txn[txn.alias] = case
        return case

    def decide(
        self,
        case: dict[str, Any],
        kind: str,
        t: datetime,
        reason: str,
        *,
        resolved_outcome: dict[str, Any] | None = None,
        reverses: dict[str, Any] | None = None,
        status: str = "DECIDED",
    ) -> dict[str, Any]:
        dec = {
            "alias": f"D{len(self.decisions) + 1:04d}",
            "case": case["alias"],
            "decided_by": case["assigned_to"],
            "kind": kind,
            "reason": reason,
            "resolved_outcome": resolved_outcome,
            "reverses": reverses["alias"] if reverses else None,
            "decided_at": t,
        }
        self.decisions.append(dec)
        case["status"], case["closed_at"] = status, t
        return dec

    def emit_outcomes(
        self, txn: Txn, ev: dict[str, Any], results: dict[tuple[str, str], bool]
    ) -> list[dict[str, Any]]:
        """results maps (role, metric) -> success for the party in that role."""
        p, it = txn.plan, self.items[txn.plan.item]
        out = []
        for (role, metric), ok in results.items():
            subj, obs = (p.borrower, p.lender) if role == "BORROWER" else (p.lender, p.borrower)
            row = {
                "txn": txn.alias,
                "ev": (txn.alias, ev["seq"]),
                "subject": subj,
                "observer": obs,
                "role": role,
                "metric": metric,
                "success": ok,
                "occurred_at": ev["t"],
                "category": it.category,
                "band": it.band,
                "duration_days": txn.plan.duration_days,
                "status": "VALID",
                "flagged_by": None,
            }
            self.outcomes.append(row)
            out.append(row)
            if (
                metric == "DISPUTE_FREE"
            ):  # exists for every closed loan: used to count prior evidence
                self.history.setdefault((subj, role), []).append(ev["t"])
        return out

    def prior_count(self, user: str, role: str, before: datetime) -> int:
        return sum(1 for t in self.history.get((user, role), ()) if t < before)

    # ------------------------------------------------------------------ reviews

    def add_review(
        self,
        txn: Txn,
        reviewer: str,
        reviewee: str,
        created_at: datetime,
        ratings: dict[str, int],
        comment: str,
        *,
        kind: str,
        group: str | None = None,
        is_attack: bool = False,
        rewrite: Callable[[random.Random], str] | None = None,
    ) -> None:
        if created_at > REF_DATE:
            return
        if (txn.alias, reviewer) in self._review_keys:
            return
        self._review_keys.add((txn.alias, reviewer))
        if rewrite is not None:
            # keep legitimate reviews about one person from reading alike: draw again if too close to an earlier one
            rng = rng_for(self.seed, f"reroll:{txn.alias}:{reviewer}")
            for _ in range(15):
                g = _grams(comment)
                if all(_cosine(g, h) < 0.5 for h in self._rv_grams.get(reviewee, ())):
                    break
                comment = rewrite(rng)
            self._rv_grams.setdefault(reviewee, []).append(_grams(comment))
        role = "BORROWER" if reviewee == txn.plan.borrower else "LENDER"
        row = {
            "alias": f"R{len(self.reviews) + 1:04d}",
            "txn": txn.alias,
            "reviewer": reviewer,
            "reviewee": reviewee,
            "role": role,
            "ratings": ratings,
            "comment": comment,
            "created_at": created_at,
        }
        self.reviews.append(row)
        self.review_truth.append(
            {"alias": row["alias"], "kind": kind, "group": group or "", "is_attack": is_attack}
        )

    def auto_reviews(self, txn: Txn, t_close: datetime, rng: random.Random) -> None:
        f, p = txn.facts, txn.plan
        it = self.items[p.item]
        for reviewer, reviewee in ((p.lender, p.borrower), (p.borrower, p.lender)):
            prob = 0.85 if f.get("disputed") else 0.7
            if rng.random() > prob:
                continue
            created = t_close + timedelta(
                hours=min(480.0, math.exp(rng.gauss(math.log(20.0), 1.1)))
            )
            if reviewee == p.borrower:
                tiers = [
                    "good" if f["on_time"] else "ok",
                    "good" if f["borrower_cond_ok"] else "bad",
                    "good" if rng.random() < 0.85 else "ok",
                    "good" if f["borrower_cond_ok"] and f["on_time"] else "ok",
                ]
                keys = BORROWER_METRICS
            else:
                resp = "good" if p.respond_h < 8 else "ok"
                tiers = [
                    "good" if rng.random() < 0.85 else "ok",
                    "good" if f["lender_cond_ok"] else "bad",
                    resp,
                    "good" if not f.get("disputed") or f.get("fault") != "lender" else "bad",
                ]
                keys = LENDER_METRICS
            ratings = {k: self.star(rng, tr) for k, tr in zip(keys, tiers, strict=True)}
            worst = "bad" if "bad" in tiers else ("ok" if "ok" in tiers else "good")
            self.add_review(
                txn,
                reviewer,
                reviewee,
                created,
                ratings,
                texts.legit_review(rng, worst, it.title),
                kind="legit",
                rewrite=lambda r, q=worst, ti=it.title: texts.legit_review(r, q, ti),
            )

    def star(self, rng: random.Random, tier: str) -> int:
        order = [5, 4, 3, 2, 1]
        if tier == "good":
            w = _GOOD_STARS
        elif tier == "ok":
            w = [0.06, 0.22, 0.44, 0.19, 0.09]
        else:
            w = [0.02, 0.06, 0.15, 0.35, 0.42]
        return rng.choices(order, weights=w)[0]

    # ------------------------------------------------------------------ derived tables

    def trust_edges(self) -> list[dict[str, Any]]:
        """observer -> subject edges from VALID outcomes (ADR-0006 proposal, weight rounded to 3 dp)."""
        agg: dict[tuple[str, str, str, str], list[Any]] = {}
        for o in self.outcomes:
            if o["status"] != "VALID":
                continue
            k = (o["observer"], o["subject"], o["role"], o["metric"])
            age = max(0.0, (REF_DATE - o["occurred_at"]).total_seconds() / 86400.0)
            w = 2.0 ** (-age / HALF_LIFE_DAYS)
            s, f, n, last = agg.setdefault(k, [0.0, 0.0, 0, o["occurred_at"]])
            if o["success"]:
                agg[k][0] = s + w
            else:
                agg[k][1] = f + w
            agg[k][2] = n + 1
            agg[k][3] = max(last, o["occurred_at"])
        rows = []
        for (src, tgt, role, metric), (s, f, n, _last) in sorted(agg.items()):
            rows.append(
                {
                    "source": src,
                    "target": tgt,
                    "role": role,
                    "metric": metric,
                    "weight": round((1.0 + s) / (2.0 + s + f), 3),
                    "evidence_count": n,
                    "updated_at": REF_DATE,  # when the weight was computed (schema default now())
                }
            )
        return rows


def _grams(s: str) -> Counter[str]:
    s = " " + re.sub(r"\s+", " ", s.lower().strip()) + " "
    return Counter(s[i : i + 3] for i in range(len(s) - 2))


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(c * b.get(k, 0) for k, c in a.items())
    na = math.sqrt(sum(c * c for c in a.values()))
    nb = math.sqrt(sum(c * c for c in b.values()))
    return dot / (na * nb) if na and nb else 0.0


_GOOD_STARS = [0.7695, 0.151, 0.0561, 0.0232, 0.0002]


def set_good_star_weights(star_share: dict[str, float]) -> None:
    """Use the measured Epinions star spread (5,4,3,2,1) as the 'everything went well' spread."""
    global _GOOD_STARS
    _GOOD_STARS = [star_share[k] for k in ("5", "4", "3", "2", "1")]


# ---------------------------------------------------------------------- the timeline of one loan


class _Timeline:
    """Builds the draft events of one loan and commits them. Kept separate to keep World small."""

    def __init__(self, w: World, alias: str, p: LoanPlan, rng: random.Random) -> None:
        self.w, self.alias, self.p, self.rng = w, alias, p, rng
        self.b, self.l = w.users[p.borrower], w.users[p.lender]
        self.it = w.items[p.item]
        self.mod = w.moderator(self.it.community)
        self.drafts: list[dict[str, Any]] = []
        self.txn: Txn  # set in build()

    # -- helpers
    def add(
        self,
        typ: str,
        new: str,
        t: datetime,
        who: str,
        payload: dict[str, Any] | None = None,
        effect: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if who == "borrower":
            actor, auth = self.b.alias, "party:borrower"
        elif who == "lender":
            actor, auth = self.l.alias, "party:lender"
        elif who == "moderator":
            actor, auth = self.mod.alias, f"role:moderator@{uid('community', self.it.community)}"
        else:
            actor, auth = None, SYSTEM_AUTH
        self.drafts.append(
            {
                "type": typ,
                "new": new,
                "t": t,
                "actor": actor,
                "auth": auth,
                "payload": payload or {},
                "effect": effect,
            }
        )

    def report(
        self, t: datetime, phase: str, who: str, agreed: bool, deposit: bool | None = None
    ) -> None:
        if t > REF_DATE:
            return
        u = self.b if who == "borrower" else self.l
        self.w.cond_reports.append(
            {
                "txn": self.alias,
                "phase": phase,
                "reporter": u.alias,
                "role": "BORROWER" if who == "borrower" else "LENDER",
                "agreed": agreed,
                "deposit": deposit,
                "reduced": self.rng.random() < 0.04,
                "notes": texts.condition_note(self.rng, agreed),
                "created_at": t,
            }
        )

    # -- main
    def build(self) -> Txn:
        p, rng = self.p, self.rng
        t0 = p.t_request
        hold_delay = rng.uniform(4, 40) if p.hold else 0.0
        # the lender must be able to answer (after any moderator hold) before the period starts
        lead = max(p.lead_h, hold_delay + p.respond_h + 3.0)
        start = t0 + timedelta(hours=lead)
        end = start + timedelta(days=p.duration_days)
        txn = Txn(self.alias, p, start, end)
        self.txn = txn
        facts = txn.facts
        facts.update(
            on_time=True, borrower_cond_ok=True, lender_cond_ok=True, disputed=False, fault=""
        )

        # schema rule (event_validate): request_created carries the item and the requested period
        self.add(
            "request_created",
            "REQUEST_CREATED",
            t0,
            "borrower",
            {"item_id": self.it.id, "requested_period": range_literal(start, end)},
        )
        self.add(
            "locality_checked",
            "LOCALITY_CHECKED",
            t0 + timedelta(seconds=2),
            "system",
            {"locality_outcome": "VERIFIED"},
        )
        if p.path == "pending":  # a request waiting for the engine: used for the scenario cases
            return self._finish()
        t_assessed = t0 + timedelta(seconds=rng.randint(3, 9))
        if p.hold:
            self.add(
                "held_for_review",
                "HELD_FOR_REVIEW",
                t_assessed,
                "system",
                {"hold_reason": p.hold},
                effect=self._hold_case,
            )
            t_assessed = t0 + timedelta(hours=hold_delay)
            if p.hold_result == "cleared":
                self.add(
                    "hold_cleared",
                    "ASSESSED",
                    t_assessed,
                    "moderator",
                    effect=self._hold_decision("CLEARED"),
                )
            else:
                self.add(
                    "request_declined",
                    "DECLINED",
                    t_assessed,
                    "moderator",
                    {"reason": "hold_declined"},
                    effect=self._hold_decision("RESTRICTED"),
                )
                return self._finish()
        else:
            self.add("assessment_generated", "ASSESSED", t_assessed, "system")

        if p.path == "cancelled":
            self.add(
                "request_cancelled",
                "CANCELLED",
                t_assessed + timedelta(hours=rng.uniform(1, 30)),
                "borrower",
            )
            return self._finish()
        if p.path == "expired":
            self.add("request_expired", "EXPIRED", t_assessed + timedelta(days=7), "system")
            return self._finish()
        t_resp = t_assessed + timedelta(hours=p.respond_h)
        if p.path == "declined":
            self.add(
                "request_declined",
                "DECLINED",
                t_resp,
                "lender",
                {"reason": texts.decline_reason(rng)},
            )
            return self._finish()
        if not self.w.item_free(p.item, start, end):
            # ADR-0001/0002: the dates were taken by an earlier acceptance, so the system declines
            self.add("request_declined", "DECLINED", t_resp, "system", {"reason": "dates_taken"})
            return self._finish()

        self.add("request_accepted", "ACCEPTED", t_resp, "lender")
        self.it.busy.append((start, end))

        if p.path == "no_show":
            self.add("no_show", "NO_SHOW", start + timedelta(hours=26), "system")
            return self._finish()

        dp = p.dispute
        if dp and dp.stage == "ACCEPTED":
            return self._dispute_at_handover(start, dp)

        t_h = start + timedelta(minutes=rng.uniform(-20, 80))
        t_h = max(t_h, t_resp + timedelta(minutes=30))
        self.report(
            t_h - timedelta(minutes=8),
            "HANDOVER",
            "lender",
            True,
            deposit=(self.it.deposit > 0) or None,
        )
        self.report(t_h - timedelta(minutes=3), "HANDOVER", "borrower", True)
        self.add("handover_confirmed", "ACTIVE", t_h, "borrower")
        due = end

        if dp and dp.stage == "ACTIVE":
            return self._dispute_non_return(t_h, due, dp)

        if p.late_days > 0:
            t_ri = due + timedelta(days=p.late_days, hours=rng.uniform(0, 10))
        else:
            t_ri = max(due - timedelta(hours=rng.uniform(6, 30)), t_h + timedelta(hours=1))
        late = p.late_days > 0
        facts["on_time"] = not late
        if dp and dp.stage == "RETURN_INITIATED":
            return self._dispute_at_return(t_ri, due, dp)
        self._return_and_close(t_ri, due, late)
        return self._finish()

    # -- pieces
    def _return_and_close(self, t_ri: datetime, due: datetime, late: bool) -> None:
        rng = self.rng
        self.add("return_initiated", "RETURN_INITIATED", t_ri, "borrower")
        # schema guard (return_confirmed): the borrower confirms AFTER the lender's latest checklist
        t_lr = t_ri + timedelta(minutes=rng.uniform(20, 120))
        t_br = t_lr + timedelta(minutes=rng.uniform(3, 20))
        t_rc = t_br + timedelta(minutes=rng.uniform(1, 10))
        self.report(t_lr, "RETURN", "lender", True)
        self.report(t_br, "RETURN", "borrower", True)
        if (t_rc > due) == (not late):
            raise ValueError(f"{self.alias}: return time does not match the planned lateness")
        self.add("return_confirmed", "RETURNED", t_rc, "borrower")
        t_c = t_rc + timedelta(seconds=rng.randint(1, 4))
        self.add(
            "transaction_closed",
            "COMPLETED",
            t_c,
            "system",
            {"outcome": "late" if late else "on_time"},
            effect=self._closed(late, t_c),
        )

    def _closed(self, late: bool, t_c: datetime) -> Callable[[dict[str, Any]], None]:
        def eff(ev: dict[str, Any]) -> None:
            self.w.emit_outcomes(
                self.txn,
                ev,
                {
                    ("BORROWER", "ON_TIME_RETURN"): not late,
                    ("BORROWER", "CONDITION_AGREED"): True,
                    ("BORROWER", "DISPUTE_FREE"): True,
                    ("LENDER", "CONDITION_AGREED"): True,
                    ("LENDER", "DISPUTE_FREE"): True,
                },
            )
            if self.p.auto_reviews:
                self.w.auto_reviews(self.txn, ev["t"], self.rng)

        return eff

    def _hold_case(self, ev: dict[str, Any]) -> None:
        trig = (
            "HIGH_VALUE_LOW_CONFIDENCE"
            if self.p.hold == "high_value_low_confidence"
            else "MANIPULATION_FLAG"
        )
        # the same reason text and priority the event_apply trigger writes
        self.w.open_case(
            self.txn,
            ev,
            trig,
            reason=f"request held: {self.p.hold}",
            hold_reason=self.p.hold,
            priority=1 if trig == "MANIPULATION_FLAG" else 2,
        )

    def _hold_decision(self, kind: str) -> Callable[[dict[str, Any]], None]:
        def eff(ev: dict[str, Any]) -> None:
            case = self.w._open_case_of_txn[self.alias]
            reason = (
                "Evidence reviewed; request may proceed with safeguards."
                if kind == "CLEARED"
                else "Evidence insufficient for this value; request declined."
            )
            dec = self.w.decide(case, kind, ev["t"], reason)
            ev["evidence_refs"] = {
                "decision_id": uid("decision", dec["alias"])
            }  # schema guard FR-T-11

        return eff

    def _finish(self) -> Txn:
        self.w.commit(self.txn, self.drafts)
        return self.txn

    # -- disputes
    def _open_dispute(self, t: datetime, dp: DisputePlan, from_state: str) -> datetime:
        self.txn.facts["disputed"] = True
        self.txn.facts["fault"] = dp.fault
        who = dp.opener

        desc = texts.dispute_description(
            self.rng, dp.reason, self.it.title, n=max(1, int(self.p.late_days) or 4)
        )

        def eff(ev: dict[str, Any]) -> None:
            raiser = self.b.alias if who == "borrower" else self.l.alias
            # the event_apply trigger opens the case: reason = description, priority 1
            self.w.open_case(
                self.txn,
                ev,
                "DISPUTE",
                reason=desc,
                dispute_reason=dp.reason,
                raised_by=raiser,
                priority=1,
            )

        self.add(
            "dispute_opened",
            "DISPUTED",
            t,
            who,
            {"reason": dp.reason, "description": desc},
            effect=eff,
        )
        return t

    def _resolve(
        self, t_open: datetime, dp: DisputePlan, stage_outcomes: dict[tuple[str, str], bool]
    ) -> None:
        """Moderator resolves (or leaves open). Outcomes follow the fault found."""
        if dp.resolve_after_days is None:
            return
        t_res = t_open + timedelta(days=dp.resolve_after_days, hours=self.rng.uniform(0, 8))

        def eff(ev: dict[str, Any]) -> None:
            w = self.w
            case = w._open_case_of_txn[self.alias]
            res = {"at_fault": dp.fault}
            dec = w.decide(
                case,
                "DISPUTE_RESOLVED",
                ev["t"],
                texts.decision_reason(self.rng, dp.fault),
                resolved_outcome=res,
            )
            ev["evidence_refs"] = {
                "decision_id": uid("decision", dec["alias"])
            }  # schema guard FR-T-11
            results = dict(stage_outcomes)
            borrower_bad = dp.fault == "borrower"
            lender_bad = dp.fault == "lender"
            if dp.stage != "ACCEPTED":
                results[("BORROWER", "CONDITION_AGREED")] = not borrower_bad
            results[("BORROWER", "DISPUTE_FREE")] = not borrower_bad
            results[("LENDER", "CONDITION_AGREED")] = not lender_bad
            results[("LENDER", "DISPUTE_FREE")] = not lender_bad
            rows = w.emit_outcomes(self.txn, ev, results)
            if self.p.auto_reviews:
                w.auto_reviews(self.txn, ev["t"], self.rng)
            if dp.reversal_after_days is not None:
                t_rev = ev["t"] + timedelta(days=dp.reversal_after_days)
                if t_rev <= REF_DATE:
                    rev = w.decide(
                        case,
                        "REVERSAL",
                        t_rev,
                        "Appeal heard; earlier finding reversed, outcomes sent back for re-evaluation.",
                        reverses=dec,
                        status="REVERSED",
                    )
                    for r in rows:
                        r["status"], r["flagged_by"] = "FLAGGED_FOR_REEVALUATION", rev["alias"]

        self.add("dispute_resolved", "COMPLETED", t_res, "moderator", effect=eff)

    def _dispute_at_handover(self, start: datetime, dp: DisputePlan) -> Txn:
        rng = self.rng
        t = start + timedelta(minutes=rng.uniform(10, 50))
        self.report(
            t - timedelta(minutes=6),
            "HANDOVER",
            "lender",
            True,
            deposit=(self.it.deposit > 0) or None,
        )
        self.report(t - timedelta(minutes=2), "HANDOVER", "borrower", False)
        self.txn.facts.update(lender_cond_ok=False, on_time=True)
        t_open = self._open_dispute(t, dp, "ACCEPTED")
        self._resolve(t_open, dp, {})
        return self._finish()

    def _dispute_non_return(self, t_h: datetime, due: datetime, dp: DisputePlan) -> Txn:
        self.txn.facts.update(on_time=False, borrower_cond_ok=dp.fault != "borrower")
        t_open = self._open_dispute(due + timedelta(hours=dp.open_delay_h), dp, "ACTIVE")
        self._resolve(t_open, dp, {("BORROWER", "ON_TIME_RETURN"): False})
        return self._finish()

    def _dispute_at_return(self, t_ri: datetime, due: datetime, dp: DisputePlan) -> Txn:
        rng = self.rng
        late = self.p.late_days > 0
        self.add("return_initiated", "RETURN_INITIATED", t_ri, "borrower")
        t_lr = t_ri + timedelta(minutes=rng.uniform(20, 120))
        t_br = t_lr + timedelta(minutes=rng.uniform(3, 20))
        self.report(t_lr, "RETURN", "lender", False)
        self.report(t_br, "RETURN", "borrower", dp.conflicting)
        self.txn.facts.update(
            borrower_cond_ok=dp.fault != "borrower", lender_cond_ok=dp.fault != "lender"
        )
        t_open = self._open_dispute(t_br + timedelta(hours=dp.open_delay_h), dp, "RETURN_INITIATED")
        if dp.withdrawn:
            t_w = t_open + timedelta(hours=rng.uniform(8, 50))
            self.add(
                "dispute_withdrawn", "RETURN_INITIATED", t_w, dp.opener, effect=self._withdrawn
            )
            # the matter is settled: fresh agreeing checklists, lender first
            t_lr2 = t_w + timedelta(minutes=rng.uniform(30, 120))
            t_br2 = t_lr2 + timedelta(minutes=rng.uniform(3, 20))
            t_rc = t_br2 + timedelta(minutes=rng.uniform(1, 10))
            self.report(t_lr2, "RETURN", "lender", True)
            self.report(t_br2, "RETURN", "borrower", True)
            late_now = t_rc > due
            self.add("return_confirmed", "RETURNED", t_rc, "borrower")
            t_c = t_rc + timedelta(seconds=3)
            self.txn.facts.update(
                borrower_cond_ok=True, lender_cond_ok=True, fault="", on_time=not late_now
            )
            self.add(
                "transaction_closed",
                "COMPLETED",
                t_c,
                "system",
                {"outcome": "late" if late_now else "on_time"},
                effect=self._closed(late_now, t_c),
            )
            return self._finish()
        self._resolve(t_open, dp, {("BORROWER", "ON_TIME_RETURN"): not late})
        return self._finish()

    def _withdrawn(self, ev: dict[str, Any]) -> None:
        case = self.w._open_case_of_txn[self.alias]
        case["status"], case["closed_at"] = "WITHDRAWN", ev["t"]
