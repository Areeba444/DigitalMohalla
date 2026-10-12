"""DEVELOPMENT attack set: controlled manipulation patterns used while building and tuning detection.

Everything here is SYNTHETIC and labelled. Ground truth (which accounts, loans and reviews are part
of an attack) is written to labels/ only; nothing in the schema-shaped files says "attack".

Separation of duties (data/REQUIREMENTS.md section 4): these patterns are the *development* split
(split = "dev"). The attack strategies used for the final evaluation are a different, held-out set
that must be written by someone other than the detectors' author (Student 3), with its own seed
namespace, in its own module, and never imported by tuning code. This file must not be used for the
final evaluation numbers.

Patterns built (threat model in the Overview):
  ring        reciprocal rating ring of four new accounts with near-identical praise (ES-04)
  burst       one new account collecting many quick 5-star reviews from other new accounts
  farm        an established lender collecting near-identical reviews from six new accounts
  padding     two new accounts swapping cheap items to build a record, then a high-value request
  falseclaim  a lender who files damage claims that moderators reject
Not built: shared-device or shared-network linkage (the schema has no device or network column, so
it cannot be expressed without inventing a field) and location spoofing (locality method is open).
"""

from __future__ import annotations

from datetime import timedelta

import texts
from cast import (
    add_manifest,
    cast_item,
    cast_user,
    closed_time,
    fixture_expectations,
    hist_loan,
    manual_review,
    request_under_test,
)
from common import rng_for
from world import DisputePlan, World

SPLIT = "dev"


def _spread(rng, n: int, lo: float, hi: float) -> list[float]:
    step = (hi - lo) / n
    return sorted((lo + step * (i + rng.uniform(0.1, 0.9)) for i in range(n)), reverse=True)


def _clean_victim(w: World, alias: str, c: str, rng, lenders: list[str]) -> None:
    cast_user(w, alias, c, 220, archetype="cast_reliable", p_on_time=0.95, p_cond=0.95, split=SPLIT)
    for i, ago in enumerate(_spread(rng, 5, 30, 190)):
        hist_loan(w, alias, lenders[i % len(lenders)], ago, key=f"{alias}{i}")


def build_dev_attacks(w: World, c1: str, lenders: list[str]) -> None:
    fx = fixture_expectations()

    # ---- ring (ES-04)
    rng = rng_for(w.seed, "attack-dev:ring")
    ring = [f"atk.ring{i}" for i in range(1, 5)]
    for i, m in enumerate(ring):
        cast_user(
            w,
            m,
            c1,
            26 - i,
            archetype="attack_ring",
            p_on_time=0.99,
            p_cond=0.99,
            p_lender_cond=0.99,
            group="ring-1",
            group_kind="rating_ring",
            group_role="participant",
            split=SPLIT,
        )
        cast_item(w, f"{m}.i1", m, "Extension Cord", 600, "electronics")
    cast_item(w, "atk.ring1.i2", "atk.ring1", "Generator (large)", 25000, "tools")
    pairs = [(ring[i], ring[(i + 1) % 4]) for i in range(4)] * 3 + [
        (ring[0], ring[2]),
        (ring[2], ring[0]),
        (ring[1], ring[3]),
        (ring[3], ring[1]),
    ]
    for k, ago in enumerate(_spread(rng, len(pairs), 3, 20)):
        b, lend = pairs[k]
        tx = hist_loan(
            w,
            b,
            lend,
            ago,
            item=f"{lend}.i1",
            duration=1,
            auto_reviews=False,
            tags=["ring"],
            group="ring-1",
            is_attack=True,
            respond_h=1.0,
            key=f"ring{k}",
        )
        tc = closed_time(tx)
        if tc is None:
            continue
        for rv, re_ in ((lend, b), (b, lend)):
            manual_review(
                w,
                tx,
                rv,
                re_,
                tc + timedelta(hours=rng.uniform(0.3, 6)),
                5,
                texts.ring_review(rng),
                kind="ring",
                group="ring-1",
                is_attack=True,
                key=f"ring{k}",
            )
    t = request_under_test(
        w, "atk.ring2", "atk.ring1", "atk.ring1.i2", tags=["ring"], group="ring-1", is_attack=True
    )
    add_manifest(
        w,
        "ES-04",
        "ES-04",
        t,
        requirements="D-08; claim C3 (the true-positive side)",
        expected=fx["ES-04"],
        source="scenario_fixtures_iteration1.json (hand-checked; inputs differ from this case)",
        notes="Four accounts under four weeks old lend cheap items to each other in a closed loop, always on time, "
        "and leave near-identical 5-star praise. Request is for a 25,000 PKR item (HIGH).",
        split=SPLIT,
        group="ring-1",
    )

    # ---- burst
    rng = rng_for(w.seed, "attack-dev:burst")
    hub = "atk.hub"
    cast_user(
        w,
        hub,
        c1,
        3.6,
        archetype="attack_hub",
        p_on_time=0.99,
        p_cond=0.99,
        p_lender_cond=0.99,
        group="burst-1",
        group_kind="new_account_burst",
        group_role="beneficiary",
        split=SPLIT,
    )
    syb = [f"atk.syb{i}" for i in range(1, 9)]
    cheap = [
        ("Extension Cord", 600, "electronics"),
        ("Hand Mixer", 1500, "appliances"),
        ("Laptop Charger", 1200, "electronics"),
        ("Juicer", 1800, "appliances"),
        ("Books (set)", 800, "media"),
        ("Badminton Set", 1400, "sports"),
        ("Rice Cooker", 2000, "appliances"),
        ("Power Drill", 3500, "tools"),
    ]
    for i, (title, val, cat) in enumerate(cheap, start=1):
        cast_item(w, f"atk.hub.i{i}", hub, title, val, cat)
    cast_item(w, "atk.hub.i9", hub, "Sewing Machine", 6500, "tools")
    for i, m in enumerate(syb):
        cast_user(
            w,
            m,
            c1,
            5.5 - 0.15 * i,
            archetype="attack_sybil",
            p_on_time=0.99,
            p_cond=0.99,
            group="burst-1",
            group_kind="new_account_burst",
            group_role="participant",
            split=SPLIT,
        )
    for i, m in enumerate(syb):
        ago = 3.0 - 2.0 * i / 8 - rng.uniform(0, 0.15)
        tx = hist_loan(
            w,
            m,
            hub,
            ago,
            item=f"atk.hub.i{i + 1}",
            duration=1,
            auto_reviews=False,
            tags=["burst"],
            group="burst-1",
            is_attack=True,
            respond_h=0.8,
            key=f"burst{i}",
        )
        tc = closed_time(tx)
        if tc:
            manual_review(
                w,
                tx,
                m,
                hub,
                tc + timedelta(hours=rng.uniform(0.2, 2)),
                5,
                texts.burst_review(rng),
                kind="burst",
                group="burst-1",
                is_attack=True,
                key=f"burst{i}",
            )
    _clean_victim(w, "atk.victim", c1, rng, lenders[:3])
    t = request_under_test(
        w, "atk.victim", hub, "atk.hub.i9", tags=["burst"], group="burst-1", is_attack=True
    )
    add_manifest(
        w,
        "ATK-burst",
        "ES-04 family",
        t,
        requirements="D-08 (new-account burst)",
        expected=None,
        source="none: signals S2 and S3 are scheduled for iteration 2 (ADR-0007); no expected state is fixed",
        notes="Nine accounts under a week old; the hub gets eight 5-star reviews within two days from eight other new accounts.",
        split=SPLIT,
        group="burst-1",
    )

    # ---- similar-review farm
    rng = rng_for(w.seed, "attack-dev:farm")
    farm = "atk.farm"
    cast_user(
        w,
        farm,
        c1,
        240,
        archetype="attack_farm_target",
        p_on_time=0.97,
        p_cond=0.97,
        p_lender_cond=0.97,
        group="farm-1",
        group_kind="similar_reviews",
        group_role="beneficiary",
        split=SPLIT,
    )
    for n, (title, val, cat) in enumerate(
        [
            ("Treadmill", 30000, "sports"),
            ("Tent", 4000, "outdoor"),
            ("Camping Stove", 3000, "outdoor"),
            ("Ladder", 4500, "tools"),
            ("Cricket Kit", 4500, "sports"),
            ("Juicer", 1800, "appliances"),
            ("Bicycle", 8000, "sports"),
        ],
        start=1,
    ):
        cast_item(w, f"atk.farm.i{n}", farm, title, val, cat)
    fr = [f"atk.fr{i}" for i in range(1, 7)]
    for i, m in enumerate(fr):
        cast_user(
            w,
            m,
            c1,
            70 - i,
            archetype="attack_farm_reviewer",
            p_on_time=0.99,
            p_cond=0.99,
            group="farm-1",
            group_kind="similar_reviews",
            group_role="participant",
            split=SPLIT,
        )
    for i, (m, ago) in enumerate(zip(fr, _spread(rng, 6, 18, 44), strict=True)):
        tx = hist_loan(
            w,
            m,
            farm,
            ago,
            item=f"atk.farm.i{i + 2}",
            duration=2,
            auto_reviews=False,
            tags=["farm"],
            group="farm-1",
            is_attack=True,
            key=f"farm{i}",
        )
        tc = closed_time(tx)
        if tc:
            manual_review(
                w,
                tx,
                m,
                farm,
                tc + timedelta(hours=rng.uniform(1, 20)),
                5,
                texts.farm_review(rng),
                kind="farm",
                group="farm-1",
                is_attack=True,
                key=f"farm{i}",
            )
    _clean_victim(w, "atk.victim2", c1, rng, lenders[1:4])
    t = request_under_test(
        w, "atk.victim2", farm, "atk.farm.i1", tags=["farm"], group="farm-1", is_attack=True
    )
    add_manifest(
        w,
        "ATK-farm",
        "ES-04 family",
        t,
        requirements="D-08 (highly similar reviews)",
        expected=None,
        source="none: one signal (review similarity) alone is not corroborated; no expected state is fixed",
        notes="An established lender holds six near-identical 5-star reviews from accounts about ten weeks old. "
        "Request is for a 30,000 PKR item (HIGH).",
        split=SPLIT,
        group="farm-1",
    )

    # ---- padding then a high-value request
    rng = rng_for(w.seed, "attack-dev:padding")
    p, q = "atk.pad1", "atk.pad2"
    for i, m in enumerate((p, q)):
        cast_user(
            w,
            m,
            c1,
            38 - i,
            archetype="attack_padding",
            p_on_time=0.99,
            p_cond=0.99,
            p_lender_cond=0.99,
            group="padding-1",
            group_kind="trivial_exchanges",
            group_role="participant",
            split=SPLIT,
        )
    for m in (p, q):
        cast_item(w, f"{m}.i1", m, "Extension Cord", 600, "electronics")
        cast_item(w, f"{m}.i2", m, "Books (set)", 800, "media")
    order = [(p, q), (q, p)] * 4
    for k, ago in enumerate(_spread(rng, 8, 10, 30)):
        b, lend = order[k]
        tx = hist_loan(
            w,
            b,
            lend,
            ago,
            duration=1,
            auto_reviews=False,
            tags=["padding"],
            group="padding-1",
            is_attack=True,
            key=f"pad{k}",
        )
        tc = closed_time(tx)
        if tc:
            manual_review(
                w,
                tx,
                lend,
                b,
                tc + timedelta(hours=rng.uniform(2, 40)),
                5,
                texts.legit_review(rng, "good", w.items[tx.plan.item].title),
                kind="padding",
                group="padding-1",
                is_attack=True,
                key=f"pad{k}",
                rewrite=lambda r, ti=w.items[tx.plan.item].title: texts.legit_review(r, "good", ti),
            )
    t = request_under_test(
        w, p, lenders[3], f"{lenders[3]}.i1", tags=["padding"], group="padding-1", is_attack=True
    )
    add_manifest(
        w,
        "ATK-padding",
        "ES-06 family",
        t,
        requirements="D-08 (trivial exchanges, sudden high-value request)",
        expected={"state": "REVIEW_RECOMMENDED"},
        source="inferred from Algorithm doc rule R4 (evidence from cheap items is dissimilar to a HIGH request); unconfirmed",
        notes="Two accounts about five weeks old swap cheap items eight times, then one asks for a 32,000 PKR projector.",
        split=SPLIT,
        group="padding-1",
    )

    # ---- false damage claims
    rng = rng_for(w.seed, "attack-dev:falseclaim")
    cl = "atk.claimant"
    cast_user(
        w,
        cl,
        c1,
        330,
        archetype="attack_claimant",
        p_on_time=0.9,
        p_cond=0.9,
        p_lender_cond=0.5,
        group="falseclaim-1",
        group_kind="false_damage_claims",
        group_role="claimant",
        split=SPLIT,
    )
    for n, (title, val, cat) in enumerate(
        [
            ("Bicycle", 8000, "sports"),
            ("Sewing Machine", 6000, "tools"),
            ("Tent", 4000, "outdoor"),
            ("Generator", 14000, "tools"),
        ],
        start=1,
    ):
        cast_item(w, f"{cl}.i{n}", cl, title, val, cat)
    for i, ago in enumerate((95, 62, 31), start=1):
        vic = f"atk.vic{i}"
        cast_user(
            w,
            vic,
            c1,
            250,
            archetype="cast_reliable",
            p_on_time=0.96,
            p_cond=0.96,
            group="falseclaim-1",
            group_kind="false_damage_claims",
            group_role="target",
            split=SPLIT,
        )
        for j, a2 in enumerate(_spread(rng, 4, 120, 230)):
            hist_loan(w, vic, lenders[j % 3], a2, key=f"{vic}{j}")
        hist_loan(
            w,
            vic,
            cl,
            ago,
            item=f"{cl}.i{i}",
            duration=2,
            tags=["falseclaim"],
            group="falseclaim-1",
            is_attack=True,
            key=f"fc{i}",
            dispute=DisputePlan(
                reason="DAMAGE",
                stage="RETURN_INITIATED",
                fault="lender",
                conflicting=True,
                open_delay_h=7,
                resolve_after_days=3.0,
            ),
        )
    _clean_victim(w, "atk.vic4", c1, rng, lenders[:3])
    t = request_under_test(
        w, "atk.vic4", cl, f"{cl}.i4", tags=["falseclaim"], group="falseclaim-1", is_attack=True
    )
    add_manifest(
        w,
        "ATK-falseclaim",
        "threat model: false damage claims",
        t,
        requirements="D-07, D-08",
        expected=None,
        source="none: no engine rule uses a lender's rejected claims yet; no expected state is fixed",
        notes="Three damage claims by one lender against three reliable borrowers were all decided in the borrowers' favour.",
        split=SPLIT,
        group="falseclaim-1",
    )
