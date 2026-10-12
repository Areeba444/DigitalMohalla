"""Background life of the neighbourhood: ordinary members borrowing from each other over 18 months.

What is DERIVED from the public trust networks (see data/derived/public_graph_stats.json):
  * how uneven activity is: a few very active members, many quiet ones (Epinions out-degree shape);
  * how uneven lender popularity is (Epinions in-degree shape);
  * how often a lender later borrows back (Epinions reciprocity, halved: lending is less symmetric
    than trust statements);
  * how loans cluster in time: bursts and long quiet gaps (Bitcoin OTC gap-over-own-median shape).
What is ASSUMED (nothing in our data measures it, so it is a documented choice): the archetype mix,
reliability ranges, month and weekday weights, time of day, loan lengths, review delays.
"""

from __future__ import annotations

import heapq
import math
import random
from datetime import datetime, timedelta
from typing import Any

from common import REF_DATE, WINDOW_START, draw_from_quantiles, rng_for
from world import (
    HIGH_CATALOG,
    LOW_CATALOG,
    MID_CATALOG,
    DisputePlan,
    LoanPlan,
    World,
)

# share of background users, join window (days before the reference date), activity multiplier,
# reliability ranges (on-time return, condition agreed)
ARCHETYPES: dict[str, dict[str, Any]] = {
    "reliable_veteran": dict(
        share=0.24, join=(540, 360), mult=1.4, p_on=(0.90, 0.99), p_cond=(0.92, 0.99)
    ),
    "steady_average": dict(
        share=0.30, join=(500, 120), mult=1.0, p_on=(0.75, 0.92), p_cond=(0.80, 0.95)
    ),
    "unreliable": dict(
        share=0.10, join=(480, 150), mult=0.8, p_on=(0.35, 0.70), p_cond=(0.45, 0.78)
    ),
    "sparse": dict(share=0.14, join=(500, 30), mult=0.0, p_on=(0.70, 0.95), p_cond=(0.80, 0.97)),
    "newcomer_reliable": dict(
        share=0.10, join=(28, 3), mult=0.0, p_on=(0.88, 0.98), p_cond=(0.90, 0.99)
    ),
    "newcomer_unreliable": dict(
        share=0.02, join=(28, 5), mult=0.0, p_on=(0.45, 0.70), p_cond=(0.55, 0.80)
    ),
    "old_inactive": dict(
        share=0.05, join=(545, 470), mult=1.0, p_on=(0.70, 0.95), p_cond=(0.80, 0.97)
    ),
    "lender_only": dict(
        share=0.05, join=(500, 100), mult=0.0, p_on=(0.80, 0.95), p_cond=(0.85, 0.97)
    ),
}
ITEMS_PER = {
    "reliable_veteran": (2, 4),
    "steady_average": (1, 3),
    "unreliable": (0, 1),
    "sparse": (1, 2),
    "newcomer_reliable": (0, 1),
    "newcomer_unreliable": (0, 1),
    "old_inactive": (1, 2),
    "lender_only": (2, 4),
}
HIGH_OWNERS = {"reliable_veteran", "steady_average", "lender_only"}
DURATIONS = [1, 2, 3, 4, 5, 7, 10, 14]
DURATION_W = [0.16, 0.20, 0.20, 0.12, 0.10, 0.10, 0.07, 0.05]
MONTH_W = {
    1: 0.9,
    2: 0.9,
    3: 1.0,
    4: 1.0,
    5: 1.1,
    6: 1.15,
    7: 1.0,
    8: 1.0,
    9: 1.0,
    10: 1.0,
    11: 0.95,
    12: 1.1,
}
DAY_W = {0: 0.8, 1: 0.8, 2: 0.85, 3: 0.9, 4: 1.2, 5: 1.3, 6: 1.3}  # Monday=0 ... Sunday=6


def _largest_remainder(shares: dict[str, float], n: int) -> dict[str, int]:
    raw = {k: v * n for k, v in shares.items()}
    out = {k: int(math.floor(v)) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: (raw[k] - out[k], k), reverse=True)[: n - sum(out.values())]:
        out[k] += 1
    return out


def _poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def snap_time(rng: random.Random, day: datetime) -> datetime:
    """A plausible Pakistan-local time of day on the given date (assumed mix), returned as UTC."""
    r = rng.random()
    if r < 0.25:
        hr = rng.uniform(9, 12)
    elif r < 0.55:
        hr = rng.uniform(12, 17)
    elif r < 0.95:
        hr = rng.uniform(17, 22.5)
    else:
        hr = rng.uniform(6, 9)
    base = day.replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(hours=hr - 5)


def make_times(
    rng: random.Random, n: int, start: datetime, end: datetime, gap_table: dict[str, float]
) -> list[datetime]:
    """n request times in [start, end] with the bursty spacing of the public data."""
    if n <= 0 or end <= start:
        return []
    span = (end - start).total_seconds()
    if n == 1:
        offs = [rng.random() * span]
    else:
        ratios = [min(30.0, max(0.002, draw_from_quantiles(rng, gap_table))) for _ in range(n - 1)]
        scale = 0.8 * span / sum(ratios)
        t = rng.random() * 0.2 * span
        offs = [t]
        for r in ratios:
            t += r * scale
            offs.append(t)
    out = []
    for o in offs:
        d = start + timedelta(seconds=min(o, span))
        # weekday and month weights by rejection: nudge to a neighbouring day if it is a quiet one
        for _ in range(3):
            if rng.random() <= MONTH_W[d.month] * DAY_W[d.weekday()] / (1.15 * 1.3):
                break
            d += timedelta(days=rng.choice((-1, 1)))
        d = min(max(d, start), end)
        out.append(min(snap_time(rng, d), end))
    return sorted(out)


# ----------------------------------------------------------------------------- build the cast


def build_background(
    w: World, communities: list[str], n_users: int, target_loans: int, stats: dict[str, Any]
) -> list[str]:
    """Create background users, items and memberships. Returns the user aliases created."""
    rng = rng_for(w.seed, "background-people")
    counts = _largest_remainder({k: v["share"] for k, v in ARCHETYPES.items()}, n_users)
    plan: list[str] = [a for a in ARCHETYPES for _ in range(counts[a])]
    rng.shuffle(plan)
    aliases = []
    for i, arch in enumerate(plan, start=1):
        spec = ARCHETYPES[arch]
        ago = rng.uniform(spec["join"][1], spec["join"][0])
        created = max(WINDOW_START + timedelta(days=1), REF_DATE - timedelta(days=ago))
        created = snap_time(rng, created)
        comm = communities[i % len(communities)]
        pl = rng.uniform(0.90, 0.99) if rng.random() > 0.12 else rng.uniform(0.60, 0.85)
        # items require COMMUNITY_VERIFIED (schema guard G1), so every member who can borrow has it
        verif = "COMMUNITY_VERIFIED"
        u = w.add_user(
            f"bg.U{i:03d}",
            comm,
            created,
            verification=verif,
            archetype=arch,
            p_on_time=round(rng.uniform(*spec["p_on"]), 3),
            p_cond=round(rng.uniform(*spec["p_cond"]), 3),
            p_lender_cond=round(pl, 3),
        )
        if len(communities) > 1 and rng.random() < 0.08:
            others = [c for c in communities if c != comm]
            u.extra_communities.append(rng.choice(others))
        aliases.append(u.alias)
    n_item = 0
    for a in aliases:
        u = w.users[a]
        lo, hi = ITEMS_PER[u.archetype]
        for _ in range(rng.randint(lo, hi)):
            r = rng.random()
            pool = (
                LOW_CATALOG
                if r < 0.62
                else MID_CATALOG
                if r < 0.89
                else (HIGH_CATALOG if u.archetype in HIGH_OWNERS else MID_CATALOG)
            )
            title, base, cat = rng.choice(pool)
            value = int(round(base * rng.uniform(0.8, 1.25), -2)) or base
            n_item += 1
            w.add_item(f"bg.I{n_item:03d}", a, title, value, cat)
    return aliases


def run_background(
    w: World,
    aliases: list[str],
    target_loans: int,
    stats: dict[str, Any],
    extra_lenders: list[str] | None = None,
) -> int:
    """Chronological simulation of background borrowing. Returns the number of loans made."""
    extra_lenders = extra_lenders or []
    rng = rng_for(w.seed, "background-loans")
    out_tab = stats["epinions_trust"]["positive_edges"]["out_degree_over_mean_quantiles"]
    in_tab = stats["epinions_trust"]["positive_edges"]["in_degree_over_mean_quantiles"]
    gap_tab = stats["bitcoin_otc"]["same_rater_gap_over_own_median_quantiles"]
    recip = 0.5 * stats["epinions_trust"]["reciprocity_positive"]

    act = {a: min(6.0, max(0.1, draw_from_quantiles(rng, out_tab))) for a in aliases}
    pop = {a: min(6.0, max(0.2, draw_from_quantiles(rng, in_tab))) for a in aliases}

    windows: dict[str, tuple[datetime, datetime]] = {}
    for a in aliases:
        u = w.users[a]
        start = max(u.created_at + timedelta(days=1), WINDOW_START)
        end = REF_DATE - timedelta(hours=3)
        if u.archetype == "old_inactive":
            end = u.created_at + timedelta(days=rng.uniform(90, 150))
        windows[a] = (start, end)

    unit = 0.0
    for a in aliases:
        m = ARCHETYPES[w.users[a].archetype]["mult"]
        s, e = windows[a]
        unit += act[a] * m * max(0.0, (e - s).days) / 365.0
    base = 0.86 * target_loans / unit if unit else 0.0

    heap: list[tuple[datetime, int, str, str | None]] = []
    seq = 0
    for a in aliases:
        u = w.users[a]
        arch = u.archetype
        s, e = windows[a]
        lam = base * act[a] * ARCHETYPES[arch]["mult"] * max(0.0, (e - s).days) / 365.0
        if arch == "sparse":
            n = 1 + _poisson(rng, 0.5)
        elif arch == "newcomer_reliable":
            n = _poisson(rng, 0.9)
        elif arch == "newcomer_unreliable":
            n = _poisson(rng, 0.6)
        elif arch == "lender_only":
            n = 0
        else:
            n = _poisson(rng, lam)
        for t in make_times(rng, n, s, e, gap_tab):
            seq += 1
            heapq.heappush(heap, (t, seq, a, None))

    lenders_by_comm: dict[str, list[str]] = {}
    for a in [*aliases, *extra_lenders]:
        if w.items_by_owner.get(a):
            lenders_by_comm.setdefault(w.users[a].community, []).append(a)
            pop.setdefault(a, min(6.0, max(0.2, draw_from_quantiles(rng, in_tab))))
    previous: dict[str, list[str]] = {}
    made = 0
    while heap:
        t, _, b, forced = heapq.heappop(heap)
        if t > REF_DATE - timedelta(
            hours=3
        ):  # a repeat borrowing that would fall after the reference date
            continue
        bu = w.users[b]
        picked = _pick(w, rng, bu, t, forced, lenders_by_comm, pop, previous)
        if picked is None:
            continue
        lender, item, dur = picked
        plan = _make_plan(w, rng, bu, w.users[lender], item, t, dur)
        txn = w.add_loan(plan)
        made += 1
        previous.setdefault(b, []).append(lender)
        closed = [e for e in txn.events if e["type"] == "transaction_closed"]
        if closed and plan.dispute is None and rng.random() < recip and w.items_by_owner.get(b):
            seq += 1
            heapq.heappush(
                heap,
                (
                    closed[0]["t"] + timedelta(days=rng.uniform(5, 60), hours=rng.uniform(0, 12)),
                    seq,
                    lender,
                    b,
                ),
            )
    return made


def _pick(
    w: World,
    rng: random.Random,
    bu: Any,
    t: datetime,
    forced: str | None,
    lenders_by_comm: dict[str, list[str]],
    pop: dict[str, float],
    previous: dict[str, list[str]],
) -> tuple[str, str, int] | None:
    # a second community is joined three days after the account is made (see build.py memberships)
    comms = [
        bu.community,
        *(bu.extra_communities if t >= bu.created_at + timedelta(days=4) else []),
    ]
    for _ in range(10):
        if forced:
            lender = forced
        elif previous.get(bu.alias) and rng.random() < 0.12:
            lender = rng.choice(previous[bu.alias])
        else:
            cands = [
                a
                for c in comms
                for a in lenders_by_comm.get(c, [])
                if a != bu.alias and w.users[a].created_at + timedelta(days=2) <= t
            ]
            cands = [a for a in cands if not _gone(w, a, t)]
            if not cands:
                return None
            lender = rng.choices(cands, weights=[pop[a] for a in cands])[0]
        lu = w.users[lender]
        if lender == bu.alias or lu.created_at + timedelta(days=1) > t or _gone(w, lender, t):
            forced = None
            continue
        if lu.community not in comms:
            forced = None
            continue
        items = [
            i for i in w.items_by_owner.get(lender, ()) if i.created_at + timedelta(hours=2) <= t
        ]
        if not items:
            forced = None
            continue
        weights = [1.0 if i.band == "LOW" else 0.6 if i.band == "MEDIUM" else 0.25 for i in items]
        item = rng.choices(items, weights=weights)[0]
        dur = rng.choices(DURATIONS, weights=DURATION_W)[0]
        if item.band == "HIGH":
            dur = min(dur, 4)
        start_guess = t + timedelta(hours=12)
        if not w.item_free(
            item.alias, start_guess - timedelta(days=1), start_guess + timedelta(days=dur + 2)
        ):
            forced = None
            continue
        return lender, item.alias, dur
    return None


def _gone(w: World, alias: str, t: datetime) -> bool:
    u = w.users[alias]
    return u.archetype == "old_inactive" and t > u.created_at + timedelta(days=150)


def _make_plan(
    w: World, rng: random.Random, b: Any, lend: Any, item_alias: str, t: datetime, dur: int
) -> LoanPlan:
    it = w.items[item_alias]
    prior = w.prior_count(b.alias, "BORROWER", t)
    p = LoanPlan(
        borrower=b.alias,
        lender=lend.alias,
        item=item_alias,
        t_request=t,
        duration_days=dur,
        lead_h=rng.uniform(8, 96),
        respond_h=min(48.0, max(0.5, math.exp(rng.gauss(math.log(6.0), 0.9)))),
    )
    # lifecycle shape
    r = rng.random()
    p_decline = 0.06 + (0.10 if prior == 0 else 0.0) + (0.04 if it.band == "HIGH" else 0.0)
    if it.band == "HIGH" and prior < 3 and rng.random() < 0.9:
        p.hold = "high_value_low_confidence"
        p.hold_result = "cleared" if rng.random() < 0.6 else "declined"
    if r < p_decline:
        p.path = "declined"
        return p
    if r < p_decline + 0.04:
        p.path = "cancelled"
        return p
    if r < p_decline + 0.05:
        p.path = "expired"
        return p
    if r < p_decline + 0.065:
        p.path = "no_show"
        return p
    # how the loan goes
    late = rng.random() > b.p_on_time
    if late:
        p.late_days = round(rng.uniform(0.5, 9.0), 1)
    if rng.random() > lend.p_lender_cond:
        p.dispute = DisputePlan(
            reason="CONDITION_MISMATCH",
            stage="ACCEPTED",
            opener="borrower",
            fault="lender" if rng.random() < 0.7 else "none",
            resolve_after_days=round(rng.uniform(1.5, 10), 1),
        )
        p.late_days = 0.0
    elif b.p_on_time < 0.6 and rng.random() < 0.06:
        p.dispute = DisputePlan(
            reason="NON_RETURN",
            stage="ACTIVE",
            opener="lender",
            open_delay_h=24 * rng.uniform(2, 7),
            fault="borrower" if rng.random() < 0.85 else "none",
            resolve_after_days=round(rng.uniform(3, 14), 1),
        )
        p.late_days = 0.0
    elif rng.random() > b.p_cond:
        fault = rng.choices(["borrower", "lender", "none"], weights=[0.65, 0.15, 0.20])[0]
        p.dispute = DisputePlan(
            reason=rng.choice(["DAMAGE", "DAMAGE", "CONDITION_MISMATCH"]),
            stage="RETURN_INITIATED",
            opener="lender",
            open_delay_h=rng.uniform(2, 30),
            fault=fault,
            conflicting=rng.random() < 0.5,
            withdrawn=rng.random() < 0.10,
            resolve_after_days=round(rng.uniform(1.5, 12), 1),
        )
    return p
