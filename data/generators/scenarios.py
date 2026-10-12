"""Hand-designed scenario cast: one request under test per scenario, with the history it needs.

Every case ends with a request that is waiting for the engine (state LOCALITY_CHECKED). The expected
engine result is NOT computed here. Where a hand-checked fixture exists
(docs/design/14_testing/scenario_fixtures_iteration1.json) its expected result is copied; elsewhere
it is the team's starting position from data/REQUIREMENTS.md, marked unconfirmed. The inputs in the
fixtures are separate, hand-made numbers: they do not depend on this dataset.

ES-09 and ES-10 (location mismatch and refusal) are not built: the locality data would depend on the
locality method, which is still open in the context document.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

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

REQ = "data/REQUIREMENTS.md section 3 (team starting position, unconfirmed)"
FIX = "scenario_fixtures_iteration1.json (hand-checked; inputs differ from this case)"


def _lenders(w: World, c: str) -> list[str]:
    spec = {
        "cast.L1": (
            545,
            [
                ("Power Drill", 3600, "tools"),
                ("Ladder", 4500, "tools"),
                ("Hand Mixer", 1500, "appliances"),
            ],
        ),
        "cast.L2": (
            520,
            [
                ("Rice Cooker", 2100, "appliances"),
                ("Juicer", 1900, "appliances"),
                ("Laptop Charger", 1300, "electronics"),
            ],
        ),
        "cast.L3": (
            540,
            [
                ("Bicycle", 8200, "sports"),
                ("Sewing Machine", 6800, "tools"),
                ("Tent", 4000, "outdoor"),
            ],
        ),
        "cast.L4": (
            500,
            [
                ("Projector", 32000, "electronics"),
                ("Generator", 15000, "tools"),
                ("Extension Cord", 600, "electronics"),
            ],
        ),
        "cast.L5": (
            530,
            [
                ("Wedding Tent Set", 45000, "outdoor"),
                ("Pressure Washer", 18000, "tools"),
                ("Camping Stove", 3000, "outdoor"),
            ],
        ),
    }
    for alias, (ago, items) in spec.items():
        cast_user(
            w,
            alias,
            c,
            ago,
            archetype="cast_lender",
            p_on_time=0.97,
            p_cond=0.97,
            p_lender_cond=0.97,
        )
        for n, (title, value, cat) in enumerate(items, start=1):
            cast_item(w, f"{alias}.i{n}", alias, title, value, cat)
    return list(spec)


def _spread(rng: Any, n: int, lo: float, hi: float) -> list[float]:
    """n distinct 'days ago' values between lo and hi, oldest first."""
    step = (hi - lo) / n
    return sorted((lo + step * (i + rng.uniform(0.1, 0.9)) for i in range(n)), reverse=True)


def _clean_history(
    w: World, rng: Any, borrower: str, n: int, lo: float, hi: float, lenders: list[str], tag: str
) -> None:
    for i, ago in enumerate(_spread(rng, n, lo, hi)):
        hist_loan(w, borrower, lenders[i % len(lenders)], ago, tags=[tag], key=f"{tag}{i}")


def build_scenarios(w: World, c1: str, c2: str) -> None:
    fx = fixture_expectations()
    L = _lenders(w, c1)
    L1, L2, L3, L4, L5 = L

    # ES-01: new user, no history
    cast_user(w, "es01.newcomer", c1, 9, archetype="newcomer_cast", p_on_time=0.9, p_cond=0.95)
    t = request_under_test(w, "es01.newcomer", L1, f"{L1}.i1")
    add_manifest(
        w,
        "ES-01",
        "ES-01",
        t,
        requirements="D-10 cold start; C5",
        expected=fx["ES-01"],
        source=FIX,
        notes="Account 9 days old, zero outcomes. Zero history is INSUFFICIENT_EVIDENCE, not a negative finding.",
    )

    # ES-02: consistently reliable
    rng = rng_for(w.seed, "cast:ES-02")
    cast_user(w, "es02.borrower", c1, 300, archetype="cast_reliable", p_on_time=0.97, p_cond=0.97)
    _clean_history(w, rng, "es02.borrower", 10, 12, 240, [L1, L2, L3, L4], "es02")
    t = request_under_test(w, "es02.borrower", L2, f"{L2}.i1")
    add_manifest(
        w,
        "ES-02",
        "ES-02",
        t,
        requirements="D-10 rich evidence; C1",
        expected=fx["ES-02"],
        source=FIX,
        notes="Ten on-time, condition-agreed loans with four different lenders over eight months.",
    )

    # ES-03: reliable, one recent RESOLVED dispute; ES-03b: the same with the dispute still OPEN
    rng = rng_for(w.seed, "cast:ES-03")
    cast_user(w, "es03.borrower", c1, 300, archetype="cast_reliable", p_on_time=0.95, p_cond=0.95)
    _clean_history(w, rng, "es03.borrower", 9, 40, 250, [L1, L2, L3], "es03")
    hist_loan(
        w,
        "es03.borrower",
        L3,
        27,
        item=f"{L3}.i3",
        duration=2,
        key="dispute",
        dispute=DisputePlan(
            reason="DAMAGE",
            stage="RETURN_INITIATED",
            fault="none",
            conflicting=True,
            open_delay_h=5,
            resolve_after_days=3.0,
        ),
        tags=["es03_dispute"],
    )
    t = request_under_test(w, "es03.borrower", L3, f"{L3}.i2")
    add_manifest(
        w,
        "ES-03",
        "ES-03",
        t,
        requirements="D-07; D-10",
        expected=fx["ES-03"],
        source=FIX,
        notes="Nine clean loans plus one damage dispute about 24 days ago, resolved with no fault found.",
    )

    rng = rng_for(w.seed, "cast:ES-03b")
    cast_user(w, "es03b.borrower", c1, 280, archetype="cast_reliable", p_on_time=0.95, p_cond=0.95)
    _clean_history(w, rng, "es03b.borrower", 8, 30, 230, [L1, L2, L4], "es03b")
    hist_loan(
        w,
        "es03b.borrower",
        L2,
        8,
        item=f"{L2}.i2",
        duration=2,
        key="open",
        dispute=DisputePlan(
            reason="DAMAGE",
            stage="RETURN_INITIATED",
            fault="borrower",
            conflicting=False,
            open_delay_h=6,
            resolve_after_days=None,
        ),
        tags=["es03b_open_dispute"],
    )
    t = request_under_test(w, "es03b.borrower", L1, f"{L1}.i1")
    add_manifest(
        w,
        "ES-03b",
        "ES-03",
        t,
        requirements="D-07 open dispute",
        expected={"state": "ACTIVE_DISPUTE", "rule_fired": "R1", "decision": "ESCALATE"},
        source="data/REQUIREMENTS.md (ES-03: ACTIVE_DISPUTE if still open); rule R1 from schema.sql",
        notes="Same profile as ES-03 but the dispute from a week ago is still open (no outcome row exists for it).",
    )

    # ES-05: retaliatory review after a complaint
    rng = rng_for(w.seed, "cast:ES-05")
    cast_user(w, "es05.borrower", c1, 250, archetype="cast_reliable", p_on_time=0.95, p_cond=0.95)
    cast_user(
        w,
        "es05.lender",
        c1,
        330,
        archetype="cast_lender",
        p_on_time=0.9,
        p_cond=0.9,
        p_lender_cond=0.7,
    )
    cast_item(w, "es05.lender.i1", "es05.lender", "Cricket Kit", 4500, "sports")
    cast_item(w, "es05.lender.i2", "es05.lender", "Badminton Set", 1400, "sports")
    _clean_history(w, rng, "es05.borrower", 4, 120, 200, [L1, L2, L3], "es05")
    t1 = hist_loan(
        w,
        "es05.borrower",
        "es05.lender",
        90,
        item="es05.lender.i1",
        duration=2,
        key="t1",
        auto_reviews=False,
        tags=["es05_confirmed_loan"],
    )
    t2 = hist_loan(
        w,
        "es05.borrower",
        "es05.lender",
        46,
        item="es05.lender.i2",
        duration=3,
        key="t2",
        dispute=DisputePlan(
            reason="CONDITION_MISMATCH",
            stage="ACCEPTED",
            opener="borrower",
            fault="lender",
            resolve_after_days=2.0,
        ),
        auto_reviews=False,
        tags=["es05_complaint"],
    )
    opened = next(e["t"] for e in t2.events if e["type"] == "dispute_opened")
    c1_closed = closed_time(t1)
    assert c1_closed is not None
    rr = rng_for(w.seed, "cast:ES-05:text")
    manual_review(
        w,
        t1,
        "es05.borrower",
        "es05.lender",
        c1_closed + timedelta(hours=9),
        5,
        texts.legit_review(rr, "good", "Cricket Kit"),
        kind="legit",
        key="b2l",
    )
    manual_review(
        w,
        t1,
        "es05.lender",
        "es05.borrower",
        opened + timedelta(days=3, hours=2),
        1,
        texts.retaliation_review(rr, "Cricket Kit"),
        kind="retaliation",
        is_attack=True,
        group="ES-05",
        key="l2b",
    )
    t = request_under_test(w, "es05.borrower", L3, f"{L3}.i2")
    add_manifest(
        w,
        "ES-05",
        "ES-05",
        t,
        requirements="D-06; D-08 (retaliation)",
        expected=fx["ES-05"],
        source=FIX,
        notes="The lender posts a 1-star review of a confirmed on-time, condition-agreed loan three days after the borrower's "
        "upheld complaint. The requirements table lists REVIEW_RECOMMENDED; the fixture expects SUFFICIENT_EVIDENCE "
        "(R8) because the review is down-weighted. Team to confirm which.",
        group="ES-05",
    )

    # ES-06: high-value request with weak evidence; ES-06b: the same request with strong similar evidence
    cast_user(w, "es06.thin", c1, 50, archetype="cast_thin", p_on_time=0.95, p_cond=0.95)
    hist_loan(w, "es06.thin", L1, 31, key="a")
    hist_loan(w, "es06.thin", L2, 13, key="b")
    t = request_under_test(w, "es06.thin", L4, f"{L4}.i1", key="thin")
    add_manifest(
        w,
        "ES-06",
        "ES-06",
        t,
        requirements="D-03 HIGH items",
        expected=fx["ES-06"],
        source=FIX,
        notes="Two outcomes only, request for a 32,000 PKR projector (HIGH band).",
    )
    rng = rng_for(w.seed, "cast:ES-06b")
    cast_user(w, "es06b.strong", c1, 270, archetype="cast_reliable", p_on_time=0.97, p_cond=0.97)
    _clean_history(w, rng, "es06b.strong", 11, 20, 230, [L1, L3, L4], "es06b")
    hist_loan(
        w,
        "es06b.strong",
        L5,
        14,
        item=f"{L5}.i2",
        duration=2,
        key="similar",
        tags=["es06b_similar_high_value"],
    )
    t = request_under_test(w, "es06b.strong", L5, f"{L5}.i2", key="strong")
    add_manifest(
        w,
        "ES-06b",
        "ES-06",
        t,
        requirements="D-03; counter-case",
        expected={
            "state": "SUFFICIENT_EVIDENCE",
            "rule_fired": "R8",
            "decision": "PROCEED_WITH_SAFEGUARDS",
        },
        source="Algorithm_and_Data_Structure_Design.md (strong similar evidence falls through to R8)",
        notes="Twelve clean loans, one of them a similar high-value item. Checks the engine does not hold every HIGH request.",
    )

    # ES-07: conflicting condition reports (open dispute)
    rng = rng_for(w.seed, "cast:ES-07")
    cast_user(w, "es07.borrower", c1, 240, archetype="cast_reliable", p_on_time=0.95, p_cond=0.9)
    _clean_history(w, rng, "es07.borrower", 6, 40, 200, [L1, L2], "es07")
    hist_loan(
        w,
        "es07.borrower",
        L3,
        10,
        item=f"{L3}.i3",
        duration=2,
        key="conflict",
        dispute=DisputePlan(
            reason="CONDITION_MISMATCH",
            stage="RETURN_INITIATED",
            fault="none",
            conflicting=True,
            open_delay_h=4,
            resolve_after_days=None,
        ),
        tags=["es07_conflicting_reports"],
    )
    t = request_under_test(w, "es07.borrower", L2, f"{L2}.i2")
    add_manifest(
        w,
        "ES-07",
        "ES-07",
        t,
        requirements="D-07",
        source=REQ,
        expected={"state": "ACTIVE_DISPUTE", "rule_fired": "R1", "decision": "ESCALATE"},
        notes="At return the borrower reported the item unchanged and the lender reported a difference; the case is open.",
    )

    # ES-08: failure to return
    rng = rng_for(w.seed, "cast:ES-08")
    cast_user(
        w,
        "es08.lender",
        c1,
        300,
        archetype="cast_lender",
        p_on_time=0.9,
        p_cond=0.9,
        p_lender_cond=0.95,
    )
    cast_item(w, "es08.lender.i1", "es08.lender", "Bicycle", 8000, "sports")
    cast_user(w, "es08.borrower", c1, 250, archetype="cast_unreliable", p_on_time=0.5, p_cond=0.7)
    _clean_history(w, rng, "es08.borrower", 5, 50, 200, [L1, L2], "es08")
    hist_loan(
        w,
        "es08.borrower",
        "es08.lender",
        22,
        item="es08.lender.i1",
        duration=5,
        key="overdue",
        dispute=DisputePlan(
            reason="NON_RETURN",
            stage="ACTIVE",
            opener="lender",
            open_delay_h=96,
            resolve_after_days=None,
        ),
        tags=["es08_non_return"],
    )
    t = request_under_test(w, "es08.borrower", L2, f"{L2}.i3")
    add_manifest(
        w,
        "ES-08",
        "ES-08",
        t,
        requirements="D-07",
        source=REQ,
        expected={"state": "ACTIVE_DISPUTE", "rule_fired": "R1", "decision": "ESCALATE"},
        notes="A loan is overdue by about two weeks and the lender has opened a non-return case.",
    )

    # ES-11: moderator reversal
    rng = rng_for(w.seed, "cast:ES-11")
    cast_user(w, "es11.borrower", c1, 290, archetype="cast_reliable", p_on_time=0.93, p_cond=0.9)
    _clean_history(w, rng, "es11.borrower", 6, 150, 240, [L1, L2, L4], "es11")
    hist_loan(
        w,
        "es11.borrower",
        L3,
        100,
        item=f"{L3}.i1",
        duration=3,
        key="reversed",
        dispute=DisputePlan(
            reason="DAMAGE",
            stage="RETURN_INITIATED",
            fault="borrower",
            conflicting=True,
            open_delay_h=5,
            resolve_after_days=3.0,
            reversal_after_days=20.0,
        ),
        tags=["es11_reversed"],
    )
    t = request_under_test(w, "es11.borrower", L3, f"{L3}.i2", key="rev")
    add_manifest(
        w,
        "ES-11",
        "ES-11",
        t,
        requirements="D-07; outcome status FLAGGED_FOR_REEVALUATION",
        source=REQ,
        expected={"state": "REVIEW_RECOMMENDED"},
        notes="A damage finding against the borrower was reversed on appeal; its outcomes are flagged and must be excluded. "
        "The REVERSAL decision kind is an iteration-2 value in the schema.",
    )

    # ES-12: sparse and old history
    cast_user(w, "es12.sparse_old", c1, 520, archetype="cast_sparse", p_on_time=0.9, p_cond=0.9)
    hist_loan(w, "es12.sparse_old", L1, 410, key="a")
    hist_loan(w, "es12.sparse_old", L2, 372, key="b")
    t = request_under_test(w, "es12.sparse_old", L1, f"{L1}.i2")
    add_manifest(
        w,
        "ES-12",
        "ES-12",
        t,
        requirements="D-09; D-10 old evidence",
        source=REQ,
        expected={"state": "INSUFFICIENT_EVIDENCE"},
        notes="Two good outcomes, both more than a year old (recency weight about 0.25 each).",
    )

    # ES-13: history with others, none with this lender, reachable by community paths
    u, a, b, v = "es13.u", "es13.a", "es13.b", "es13.v"
    cast_user(
        w, u, c1, 400, archetype="cast_lender", p_on_time=0.95, p_cond=0.95, p_lender_cond=0.96
    )
    cast_item(w, "es13.u.i1", u, "Mini Projector", 12000, "electronics")
    cast_item(w, "es13.u.i2", u, "Extension Cord", 700, "electronics")
    for who, ago, item in ((a, 350, "Rice Cooker"), (b, 340, "Juicer")):
        cast_user(w, who, c1, ago, archetype="cast_reliable", p_on_time=0.95, p_cond=0.95)
        cast_item(w, f"{who}.i1", who, item, 2000, "appliances")
    for ago in (122, 91, 58, 31):
        hist_loan(w, a, u, ago, item="es13.u.i2", duration=1, key="a")
    for ago in (101, 41, 16):
        hist_loan(w, b, u, ago, item="es13.u.i2", duration=1, key="b")
    cast_user(w, v, c1, 100, archetype="cast_thin", p_on_time=0.95, p_cond=0.95)
    hist_loan(w, v, a, 47, item=f"{a}.i1", duration=2, key="va")
    hist_loan(w, v, b, 21, item=f"{b}.i1", duration=2, key="vb")
    t = request_under_test(w, v, u, "es13.u.i1")
    add_manifest(
        w,
        "ES-13",
        "ES-13",
        t,
        requirements="D-02 community paths; indirect trust",
        expected=fx["ES-13"],
        source=FIX + "; ES-13 expected state is still an open item in the context document",
        notes="v borrowed once from a and once from b; a and b each borrowed from u several times; v never borrowed from u.",
    )
    v2 = "es13.v_nopath"
    for who, ago in (("es13.c", 300), ("es13.d", 290)):
        cast_user(w, who, c1, ago, archetype="cast_reliable", p_on_time=0.95, p_cond=0.95)
        cast_item(w, f"{who}.i1", who, "Folding Chairs (set)", 3200, "furniture")
    cast_user(w, v2, c1, 100, archetype="cast_thin", p_on_time=0.95, p_cond=0.95)
    hist_loan(w, v2, "es13.c", 52, item="es13.c.i1", duration=2, key="vc")
    hist_loan(w, v2, "es13.d", 24, item="es13.d.i1", duration=2, key="vd")
    t = request_under_test(w, v2, u, "es13.u.i1", key="nopath")
    add_manifest(
        w,
        "ES-13b",
        "ES-13",
        t,
        requirements="D-02; counterfactual",
        source=FIX + " (counterfactual_without_paths)",
        expected={
            "state": "INSUFFICIENT_EVIDENCE",
            "rule_fired": "R6_SPARSE",
            "decision": "REQUEST_VERIFICATION",
        },
        notes="Same size of history as v but with lenders who have no link to u: no community path, so no indirect support.",
    )

    # C3: legitimate dense family cluster (must not be flagged)
    rng = rng_for(w.seed, "cast:C3")
    fam = [f"c3.f{i}" for i in range(1, 6)]
    for i, m in enumerate(fam, start=1):
        cast_user(
            w,
            m,
            c2,
            420 - i * 8,
            archetype="cast_family",
            p_on_time=0.97,
            p_cond=0.97,
            p_lender_cond=0.97,
            group="family-1",
            group_kind="legit_dense_cluster",
            group_role="member",
        )
        cast_item(
            w,
            f"{m}.i1",
            m,
            [
                "Rice Cooker",
                "Hand Mixer",
                "Badminton Set",
                "Folding Chairs (set)",
                "Pressure Cooker",
            ][i - 1],
            [2100, 1500, 1400, 3200, 2500][i - 1],
            ["appliances", "appliances", "sports", "furniture", "appliances"][i - 1],
        )
        cast_item(w, f"{m}.i2", m, "Extension Cord", 600, "electronics")
    pairs = [(x, y) for x in fam for y in fam if x != y]
    rng.shuffle(pairs)
    pairs = pairs[:16]
    for k, ago in enumerate(_spread(rng, len(pairs), 6, 82)):
        borrower, lender = pairs[k]
        tx = hist_loan(
            w,
            borrower,
            lender,
            ago,
            duration=rng.choice([1, 2, 3]),
            auto_reviews=False,
            tags=["c3_family"],
            group="family-1",
            key=f"c3{k}",
        )
        tc = closed_time(tx)
        if tc is None:
            continue
        for rv, re_ in ((lender, borrower), (borrower, lender)):
            if rng.random() < 0.95:
                manual_review(
                    w,
                    tx,
                    rv,
                    re_,
                    tc + timedelta(hours=rng.uniform(2, 60)),
                    5 if rng.random() < 0.8 else 4,
                    texts.legit_review(rng, "good", w.items[tx.plan.item].title),
                    kind="legit_dense",
                    group="family-1",
                    key=f"c3{k}",
                    rewrite=lambda r, ti=w.items[tx.plan.item].title: texts.legit_review(
                        r, "good", ti
                    ),
                )
    t = request_under_test(w, "c3.f1", "c3.f2", "c3.f2.i1", tags=["c3_family"], group="family-1")
    add_manifest(
        w,
        "C3",
        "C3",
        t,
        requirements="D-06; claim C3 (false positives)",
        expected={"must_not_rule": "R2"},
        source="data/REQUIREMENTS.md claim C3",
        notes="Five relatives lending to each other 16 times in 80 days with mutual high ratings. Reciprocal clustering is high but "
        "review texts differ, so only one signal is active: the request must not be held for manipulation (not R2).",
        group="family-1",
    )

    # C5: a newcomer who behaves reliably
    cast_user(w, "c5.newcomer", c1, 58, archetype="cast_newcomer", p_on_time=0.97, p_cond=0.97)
    for ago, lender in ((49, L1), (38, L2), (24, L3), (11, L1)):
        hist_loan(w, "c5.newcomer", lender, ago, key=f"c5{ago}", tags=["c5_newcomer"])
    t = request_under_test(w, "c5.newcomer", L3, f"{L3}.i1", key="c5")
    add_manifest(
        w,
        "C5",
        "C5",
        t,
        requirements="D-10; claim C5 (newcomers not excluded)",
        expected={"must_not_rule": "R2"},
        source="data/REQUIREMENTS.md claim C5",
        notes="Account 55 days old with four on-time loans. Replaying the history in time order shows how quickly evidence builds; "
        "no restriction without human review. No expected state is fixed: SUFFICIENT_EVIDENCE thresholds are still open.",
    )
