"""Automated checks for schema.sql v2.3 (Digital Mohalla, design step A6, Student 1).

Each check exercises one rule of the A3 transition table, an ADR or an FR/NFR acceptance criterion
against a real PostgreSQL, and reports PASS/FAIL with its reference. Run:

    pip install psycopg2-binary
    set DM_TEST_DSN=postgresql://postgres@localhost:5499/postgres     (PowerShell: $env:DM_TEST_DSN=...)
    python test_schema.py

The server must provide the contrib extension btree_gist (ADR-0002 exclusion constraint), e.g. the
official postgres Docker image or the EDB binaries. WARNING: drops and recreates schema "dm".
"""
import csv
import datetime as dt
import json
import os
import sys
import threading
import uuid

import psycopg2
from psycopg2.extras import register_uuid

register_uuid()
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
import lifecycle_model as lm  # noqa: E402

NOW = dt.datetime.now(dt.timezone.utc)
CFG = "cfg-2026.10-initial"
RESULTS = []


# ----------------------------------------------------------------------------- infrastructure
def dsn():
    if not os.environ.get("DM_TEST_DSN"):
        sys.exit("Set DM_TEST_DSN to a PostgreSQL 14+ server that has the btree_gist extension.")
    return os.environ["DM_TEST_DSN"]


def day(n, hour=10):
    return (NOW + dt.timedelta(days=n)).replace(hour=hour, minute=0, second=0, microsecond=0)


def rng(a, b):
    return f"[{day(a).isoformat()},{day(b).isoformat()})"


class Expect(Exception):
    pass


def check(name, ref, fn):
    try:
        fn()
        RESULTS.append(("PASS", name, ref, ""))
    except Exception as e:  # noqa: BLE001 - every failure is reported
        RESULTS.append(("FAIL", name, ref, f"{type(e).__name__}: {str(e).strip()[:300]}"))


def run(conn, fn):
    with conn:
        with conn.cursor() as cur:
            return fn(cur)


def expect_error(conn, fragment, fn, sqlstate=None):
    """fn runs in its own DB transaction and must fail with a message containing fragment."""
    try:
        with conn:
            with conn.cursor() as cur:
                fn(cur)
    except psycopg2.Error as e:
        msg = e.pgerror or str(e)
        if fragment.lower() not in msg.lower():
            raise Expect(f"failed for the wrong reason: {msg.strip()[:250]}")
        if sqlstate and e.pgcode != sqlstate:
            raise Expect(f"expected SQLSTATE {sqlstate}, got {e.pgcode}: {msg.strip()[:200]}")
        return
    raise Expect(f'expected an error containing "{fragment}" but the statement succeeded')


def one(cur, sql, args=()):
    cur.execute(sql, args)
    return cur.fetchone()[0]


def eq(a, b, what=""):
    if a != b:
        raise Expect(f"{what}: expected {b!r}, got {a!r}")


# ----------------------------------------------------------------------------- fixtures (synthetic data)
class W:
    pass


def seed(conn):
    w = W()

    def body(cur):
        def user(name, level="COMMUNITY_VERIFIED", role="MEMBER", status="ACTIVE"):
            return one(cur, """INSERT INTO app_user (display_name, email, verification_level, platform_role, status,
                                                     is_synthetic)
                               VALUES (%s, %s, %s, %s, %s, true) RETURNING id""",
                       (name, f"{name.lower()}@example.test", level, role, status))

        def community(name, code):
            return one(cur, "INSERT INTO community (name, join_code) VALUES (%s, %s) RETURNING id", (name, code))

        def member(u, c, role="MEMBER", outcome="VERIFIED", refused=False):
            m = one(cur, """INSERT INTO membership (user_id, community_id, role, status, decided_at)
                            VALUES (%s, %s, %s, 'APPROVED', now()) RETURNING id""", (u, c, role))
            if outcome == "VERIFIED":          # seeded residents: approved by an admin (A11 moderator path)
                cur.execute("""INSERT INTO locality_verification (membership_id, method, outcome, approved_by, valid_until)
                               VALUES (%s, 'MODERATOR_APPROVAL', 'VERIFIED', %s, now() + interval '180 days')""", (m, w.a))
            else:
                signal = "UNAVAILABLE" if refused else "OUTSIDE"
                cur.execute("""INSERT INTO locality_verification (membership_id, method, outcome, geofence_signal,
                                                                  permission_refused, valid_until)
                               VALUES (%s, 'GEOFENCE_INVITATION', %s, %s, %s, now() + interval '180 days')""",
                            (m, outcome, signal, refused))
            return m

        w.c, w.c2 = community("Gulberg Block C", "GBC"), community("Model Town A", "MTA")
        w.b, w.l, w.m, w.a = user("Borrower"), user("Lender"), user("Moderator"), user("Admin", role="ADMIN")
        w.b2, w.b3, w.b4, w.o = user("Borrower2"), user("Borrower3"), user("Borrower4"), user("OtherMod")
        w.x = user("Outsider")
        w.f = user("Conflicted")
        w.i = user("Refuser")
        for u in (w.b, w.l, w.b2, w.b3, w.b4):
            member(u, w.c)
        member(w.m, w.c, role="MODERATOR")
        member(w.o, w.c2, role="MODERATOR")
        member(w.x, w.c2)
        member(w.f, w.c, outcome="CONFLICTING")
        member(w.i, w.c, outcome="INCONCLUSIVE", refused=True)
        w.cat = one(cur, "INSERT INTO category (name) VALUES ('Tools') RETURNING id")

        def item(title, deposit=0):
            return one(cur, """INSERT INTO item (owner_id, community_id, category_id, title, value_band, deposit_amount, status)
                               VALUES (%s, %s, %s, %s, 'LOW', %s, 'PUBLISHED') RETURNING id""",
                       (w.l, w.c, w.cat, title, deposit))
        w.items = [item(f"Item {k}") for k in range(80)]
        w.ladder = item("Ladder", deposit=500)
        cur.execute("INSERT INTO user_block (blocker_id, blocked_id) VALUES (%s, %s)", (w.l, w.b4))
    run(conn, body)
    w.next = 0
    return w


def new_item(w):
    w.next += 1
    return w.items[w.next - 1]


AUTH = {"BORROWER": "party:borrower", "LENDER": "party:lender", "ADMIN": "role:admin", "SYSTEM": "system:test-runner"}


def auth(w, role):
    return f"role:moderator@{w.c}" if role == "MODERATOR" else AUTH[role]


def ev(cur, w, txn, etype, role, actor, new_state, evidence=None, payload=None, config=None, seq=None, prev=None):
    cur.execute("SELECT current_state, stream_version FROM borrowing_transaction WHERE id = %s", (txn,))
    state, version = cur.fetchone()
    cur.execute("""INSERT INTO lifecycle_event (stream_id, stream_seq, event_type, actor_id, previous_state, new_state,
                                                evidence_refs, authorisation, config_version, payload)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING event_id""",
                (txn, seq if seq is not None else version + 1, etype, actor, prev if prev is not None else state,
                 new_state, json.dumps(evidence or {}), auth(w, role), config, json.dumps(payload or {})))
    return cur.fetchone()[0]


def create(cur, w, item, a=2, b=5, borrower=None):
    borrower = borrower or w.b
    txn = one(cur, """INSERT INTO borrowing_transaction (item_id, borrower_id, lender_id, requested_period)
                      VALUES (%s, %s, %s, %s) RETURNING id""", (item, borrower, w.l, rng(a, b)))
    cur.execute("""INSERT INTO lifecycle_event (stream_id, stream_seq, event_type, actor_id, new_state, authorisation, payload)
                   VALUES (%s, 1, 'request_created', %s, 'REQUEST_CREATED', 'party:borrower', %s)""",
                (txn, borrower, json.dumps({"item_id": str(item), "requested_period": rng(a, b)})))
    return txn


def borrower_of(cur, txn):
    return one(cur, "SELECT borrower_id FROM borrowing_transaction WHERE id = %s", (txn,))


# A5 decision table (Algorithm doc §6, ADR-0007, ADR-0008): rule -> (assurance state, policy decision, hold reason)
RULES = {"R1": ("ACTIVE_DISPUTE", "ESCALATE", None), "R2": ("REVIEW_RECOMMENDED", "ESCALATE", "manipulation_risk"),
         "R3": ("INSUFFICIENT_EVIDENCE", "REQUEST_VERIFICATION", None),
         "R4": ("REVIEW_RECOMMENDED", "RESTRICT_HIGH_VALUE", "high_value_low_confidence"),
         "R5": ("REVIEW_RECOMMENDED", "REQUEST_VERIFICATION", None),
         "R6_DISPUTE": ("REVIEW_RECOMMENDED", "PROCEED_WITH_SAFEGUARDS", None),
         "R6_SPARSE": ("INSUFFICIENT_EVIDENCE", "REQUEST_VERIFICATION", None),
         "R7": ("SUFFICIENT_EVIDENCE", "PROCEED", None), "R8": ("SUFFICIENT_EVIDENCE", "PROCEED_WITH_SAFEGUARDS", None),
         "R9": ("REVIEW_RECOMMENDED", "PROCEED_WITH_SAFEGUARDS", None)}


def risk_level(risk, corroborated):
    return 1 if risk < 20 else 2 if risk < 40 else 3 if risk < 60 or not corroborated else 4


def assessment(cur, txn, hold=None, risk=10, state="SUFFICIENT_EVIDENCE", cfg=CFG, rule=None, corroborated=None,
               level=None, decision=None):
    """Insert an assessment; by default the row follows the decision table for the given hold / state."""
    if rule is None:
        rule = {"manipulation_risk": "R2", "high_value_low_confidence": "R4"}.get(hold) or \
            {"SUFFICIENT_EVIDENCE": "R7", "REVIEW_RECOMMENDED": "R9", "INSUFFICIENT_EVIDENCE": "R3",
             "ACTIVE_DISPUTE": "R1"}[state]
    if corroborated is None:
        corroborated = rule == "R2"
    if level is None:
        level = risk_level(risk, corroborated)
    if decision is None:
        decision = RULES[rule][1]
    return one(cur, """INSERT INTO assessment (transaction_id, config_version, assurance_state, policy_decision, hold_reason,
                                               posterior_mean, ci90_low, ci90_high, effective_evidence, manipulation_risk,
                                               manipulation_level, manipulation_corroborated, rule_fired, explanation)
                       VALUES (%s, %s, %s, %s, %s, 0.85, 0.70, 0.94, 12.4, %s, %s, %s, %s, 'synthetic test explanation')
                       RETURNING id""",
               (txn, cfg, state, decision, hold, risk, level, corroborated, rule))


def to_checked(cur, w, txn):
    ev(cur, w, txn, "locality_checked", "SYSTEM", None, "LOCALITY_CHECKED", payload={"locality_outcome": "VERIFIED"})


def to_assessed(cur, w, txn):
    to_checked(cur, w, txn)
    a = assessment(cur, txn)
    ev(cur, w, txn, "assessment_generated", "SYSTEM", None, "ASSESSED", evidence={"assessment_id": str(a)}, config=CFG)


def report(cur, w, txn, phase, role, agreed=True, deposit=None):
    actor = w.l if role == "LENDER" else borrower_of(cur, txn)
    return one(cur, """INSERT INTO condition_report (transaction_id, phase, reporter_id, reporter_role, checklist,
                                                     condition_agreed, deposit_received)
                       VALUES (%s, %s, %s, %s, '{"parts": "complete"}', %s, %s) RETURNING id""",
               (txn, phase, actor, role, agreed, deposit))


def to_active(cur, w, txn, deposit=None):
    to_assessed(cur, w, txn)
    ev(cur, w, txn, "request_accepted", "LENDER", w.l, "ACCEPTED")
    report(cur, w, txn, "HANDOVER", "LENDER", deposit=deposit)
    report(cur, w, txn, "HANDOVER", "BORROWER")
    ev(cur, w, txn, "handover_confirmed", "BORROWER", borrower_of(cur, txn), "ACTIVE")


def to_completed(cur, w, txn):
    to_active(cur, w, txn)
    ev(cur, w, txn, "return_initiated", "BORROWER", borrower_of(cur, txn), "RETURN_INITIATED")
    report(cur, w, txn, "RETURN", "LENDER")
    report(cur, w, txn, "RETURN", "BORROWER")
    ev(cur, w, txn, "return_confirmed", "LENDER", w.l, "RETURNED")
    return ev(cur, w, txn, "transaction_closed", "SYSTEM", None, "COMPLETED", payload={"outcome": "on_time"})


def live_case(cur, txn):
    cur.execute("SELECT id, trigger_type, hold_reason, status FROM escalation_case WHERE transaction_id = %s "
                "ORDER BY opened_at DESC, opened_event_id DESC LIMIT 1", (txn,))
    return cur.fetchone()


def decide(cur, w, txn, kind, by=None, role="MODERATOR", safeguards="[]"):
    case_id = one(cur, "SELECT id FROM escalation_case WHERE transaction_id = %s AND status IN ('OPEN','AWAITING_INFORMATION')",
                  (txn,))
    return one(cur, """INSERT INTO moderator_decision (case_id, decided_by, decider_role, kind, reason, safeguards)
                       VALUES (%s, %s, %s, %s, 'evidence reviewed (synthetic)', %s) RETURNING id""",
               (case_id, by or w.m, role, kind, safeguards))


def state_of(cur, txn):
    return one(cur, "SELECT current_state FROM borrowing_transaction WHERE id = %s", (txn,))


# ----------------------------------------------------------------------------- checks
def main():
    conn = psycopg2.connect(dsn())
    with conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS dm CASCADE")
        cur.execute(open(os.path.join(HERE, "schema.sql"), encoding="utf-8").read())
    conn.cursor().execute("SET search_path = dm, public")
    conn.commit()
    w = seed(conn)

    # ---------- structure
    def c_structure():
        def body(cur):
            eq(one(cur, "SELECT count(*) FROM unnest(enum_range(NULL::lifecycle_state))"), 14, "states")
            eq(sorted(one(cur, "SELECT array_agg(x::text) FROM unnest(enum_range(NULL::lifecycle_state)) x")),
               sorted(lm.STATES), "state names")
            eq(sorted(one(cur, "SELECT array_agg(x::text) FROM unnest(enum_range(NULL::event_type)) x")),
               sorted(lm.EVENT_NAMES), "event types")
            cur.execute("SELECT from_state::text, event_type::text, to_state::text, allowed_roles::text[], ref, iteration "
                        "FROM allowed_transition")
            db = {(r[0], r[1], r[2]): (sorted(r[3]), r[4], r[5]) for r in cur.fetchall()}
            model = {(f, e, t): (sorted(a), ref, it) for f, e, t, a, ref, it in lm.leaf_rows()}
            eq(db, model, "allowed_transition vs lifecycle_model")
        run(conn, body)
    check(f"14 states, 21 event types, {len(lm.leaf_rows())}-row transition table identical to the A3 model", "FR-B-08; A3",
          c_structure)

    def c_csv():
        rows = list(csv.DictReader(open(os.path.join(HERE, "..", "07_state_machines", "transition_table.csv"), encoding="utf-8")))
        csv_keys = {(r["from_state"], r["event_type"], r["to_state"]) for r in rows if r["from_state"] != "(initial)"}
        db_keys = run(conn, lambda cur: (cur.execute("SELECT from_state::text, event_type::text, to_state::text "
                                                     "FROM allowed_transition"), set(cur.fetchall()))[1])
        eq(csv_keys, db_keys, "transition_table.csv vs allowed_transition")
    check("transition_table.csv (test matrix) matches the database rules", "A3; NFR-R-02", c_csv)

    def c_privacy():
        bad = run(conn, lambda cur: (cur.execute(
            """SELECT table_name || '.' || column_name FROM information_schema.columns WHERE table_schema = 'dm'
               AND column_name ~* '(^|_)(lat|latitude|lon|lng|longitude|gps|coord|coords|coordinates|address|geo|geojson|cnic|location)(_|$)'"""), cur.fetchall())[1])
        eq(bad, [], "location-like or identity-number columns")
    check("Privacy scan: no coordinate, address or CNIC column in any table", "NFR-PR-01, NFR-S-07", c_privacy)

    # ---------- happy path, replay, frozen fields
    def c_happy():
        def body(cur):
            txn = create(cur, w, new_item(w))
            closed = to_completed(cur, w, txn)
            eq(state_of(cur, txn), "COMPLETED", "state")
            eq(one(cur, "SELECT replay_state(%s)", (txn,)), "COMPLETED", "replay")
            eq(one(cur, "SELECT count(*) FROM verify_event_chain(%s)", (txn,)), 0, "chain problems")
            eq(one(cur, "SELECT status FROM booking WHERE transaction_id = %s", (txn,)), "RELEASED", "booking")
            eq(one(cur, "SELECT count(*) FROM lifecycle_event WHERE stream_id = %s", (txn,)), 8, "events")
            eq(one(cur, "SELECT count(*) FROM lifecycle_event WHERE stream_id = %s AND (event_type IS NULL OR schema_version IS NULL)",
                   (txn,)), 0, "frozen fields")
            eq(one(cur, "SELECT config_version FROM lifecycle_event WHERE stream_id = %s AND event_type = 'assessment_generated'",
                   (txn,)), CFG, "config_version")
            # FR-B-15: the closing event is the source of the verified outcome
            cur.execute("""INSERT INTO outcome (transaction_id, source_event_id, subject_id, observer_id, subject_role, metric,
                                                success, occurred_at, category_id, value_band, loan_duration)
                           VALUES (%s, %s, %s, %s, 'BORROWER', 'ON_TIME_RETURN', true, now(), %s, 'LOW', interval '3 days')""",
                        (txn, closed, w.b, w.l, w.cat))
        run(conn, body)
    check("Request-to-return path reaches COMPLETED; replay = projection; hash chain intact; booking released",
          "FR-B-09, FR-B-13, FR-B-15, NFR-R-03", c_happy)

    # ---------- invalid transitions
    def c_completed_accept():
        txn = run(conn, lambda cur: (lambda t: (to_completed(cur, w, t), t)[1])(create(cur, w, new_item(w))))
        expect_error(conn, "invalid transition", lambda cur: ev(cur, w, txn, "request_accepted", "LENDER", w.l, "ACCEPTED"),
                     "23514")
    check("COMPLETED -> request_accepted is rejected (acceptance criterion of FR-B-08)", "FR-B-08; NFR-R-02", c_completed_accept)

    def c_skip_assessment():
        txn = run(conn, lambda cur: (lambda t: (to_checked(cur, w, t), t)[1])(create(cur, w, new_item(w))))
        expect_error(conn, "invalid transition", lambda cur: ev(cur, w, txn, "request_accepted", "LENDER", w.l, "ACCEPTED"))
    check("Accepting before an assessment exists is rejected (no request reaches the lender unassessed)", "FR-B-07, ADR-0003",
          c_skip_assessment)

    def c_handover_one_sided():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_assessed(cur, w, t)
            ev(cur, w, t, "request_accepted", "LENDER", w.l, "ACCEPTED")
            report(cur, w, t, "HANDOVER", "LENDER")
            return t
        txn = run(conn, setup)
        expect_error(conn, "borrower''s agreeing confirmation".replace("''", "'"),
                     lambda cur: ev(cur, w, txn, "handover_confirmed", "LENDER", w.l, "ACTIVE"))
    check("ACCEPTED -> ACTIVE needs both confirmations (lender alone is rejected)", "FR-B-11; UC-B7", c_handover_one_sided)

    def c_wrong_role():
        txn = run(conn, lambda cur: (lambda t: (to_active(cur, w, t), t)[1])(create(cur, w, new_item(w))))
        expect_error(conn, "may not append", lambda cur: ev(cur, w, txn, "return_initiated", "LENDER", w.l, "RETURN_INITIATED"),
                     "42501")
    check("Lender cannot initiate the return (role not allowed for T20)", "NFR-S-02", c_wrong_role)

    def c_impersonation():
        txn = run(conn, lambda cur: create(cur, w, new_item(w)))
        run(conn, lambda cur: to_assessed(cur, w, txn))
        expect_error(conn, "not the lender", lambda cur: ev(cur, w, txn, "request_accepted", "LENDER", w.b2, "ACCEPTED"))
    check("Impersonation: a non-owner claiming party:lender is rejected", "NFR-S-02", c_impersonation)

    # ---------- concurrency, soft hold, overlap constraint
    def c_stale():
        txn = run(conn, lambda cur: create(cur, w, new_item(w)))
        expect_error(conn, "stale command", lambda cur: ev(cur, w, txn, "locality_checked", "SYSTEM", None, "LOCALITY_CHECKED",
                                                           payload={"locality_outcome": "VERIFIED"}, seq=1), "40001")
    check("Stale command (stream_seq already used) is rejected", "ADR-0002 (unique stream_id+stream_seq)", c_stale)

    def c_soft_hold():
        it = new_item(w)

        def body(cur):
            t1 = create(cur, w, it, 3, 6, borrower=w.b)
            t2 = create(cur, w, it, 4, 7, borrower=w.b2)
            to_assessed(cur, w, t1)
            to_assessed(cur, w, t2)
            ev(cur, w, t1, "request_accepted", "LENDER", w.l, "ACCEPTED")
            ev(cur, w, t2, "request_declined", "SYSTEM", None, "DECLINED", payload={"reason": "dates_taken"})
            eq(state_of(cur, t2), "DECLINED", "loser")
        run(conn, body)
    check("Two overlapping pending requests coexist; acceptance declines the other with dates_taken",
          "ADR-0001; FR-B-06, FR-B-10", c_soft_hold)

    def c_overlap_refused():
        it = new_item(w)

        def setup(cur):
            t1, t2 = create(cur, w, it, 3, 6, borrower=w.b), create(cur, w, it, 5, 8, borrower=w.b2)
            to_assessed(cur, w, t1)
            to_assessed(cur, w, t2)
            ev(cur, w, t1, "request_accepted", "LENDER", w.l, "ACCEPTED")
            return t2
        t2 = run(conn, setup)
        expect_error(conn, "booking_no_overlap", lambda cur: ev(cur, w, t2, "request_accepted", "LENDER", w.l, "ACCEPTED"),
                     "23P01")
        eq(run(conn, lambda cur: state_of(cur, t2)), "ASSESSED", "nothing committed for the refused acceptance")
    check("A second overlapping acceptance is refused by the exclusion constraint and commits nothing",
          "ADR-0002; FR-B-05 acceptance criterion", c_overlap_refused)

    def c_race():
        wins = []
        for _round in range(5):
            it = new_item(w)

            def setup(cur):
                ts = [create(cur, w, it, 3, 6, borrower=bw) for bw in (w.b, w.b2, w.b3)]
                for t in ts:
                    to_assessed(cur, w, t)
                return ts
            ts = run(conn, setup)
            barrier = threading.Barrier(len(ts))
            ok = []

            def worker(t):
                c = psycopg2.connect(dsn())
                c.cursor().execute("SET search_path = dm, public")
                try:
                    with c, c.cursor() as cur:
                        cur.execute("SELECT 1")
                        barrier.wait()
                        ev(cur, w, t, "request_accepted", "LENDER", w.l, "ACCEPTED")
                    ok.append(t)
                except psycopg2.Error:
                    pass
                finally:
                    c.close()
            th = [threading.Thread(target=worker, args=(t,)) for t in ts]
            [x.start() for x in th]
            [x.join() for x in th]
            wins.append(len(ok))
            held = run(conn, lambda cur: one(cur, "SELECT count(*) FROM booking WHERE item_id = %s AND status = 'HELD'", (it,)))
            eq(held, 1, "held bookings")
        eq(wins, [1] * 5, "commits per round")
    check("Race: 3 simultaneous acceptances for the same dates, 5 rounds -> exactly one commits each time",
          "NFR-R-01; ADR-0002; test suite 3", c_race)

    def c_system_decline_needs_overlap():
        txn = run(conn, lambda cur: (lambda t: (to_assessed(cur, w, t), t)[1])(create(cur, w, new_item(w))))
        expect_error(conn, "dates_taken", lambda cur: ev(cur, w, txn, "request_declined", "SYSTEM", None, "DECLINED",
                                                         payload={"reason": "dates_taken"}))
    check("The system cannot decline a request unless an overlapping booking is held", "ADR-0001/0002; T17",
          c_system_decline_needs_overlap)

    def c_g1():
        it = new_item(w)
        run(conn, lambda cur: (lambda t: (to_assessed(cur, w, t), ev(cur, w, t, "request_accepted", "LENDER", w.l, "ACCEPTED")))(
            create(cur, w, it, 3, 6)))
        expect_error(conn, "UC-B5 2a", lambda cur: create(cur, w, it, 5, 9, borrower=w.b2))
        expect_error(conn, "request not allowed", lambda cur: create(cur, w, new_item(w), borrower=w.b4))
        expect_error(conn, "not a member", lambda cur: create(cur, w, new_item(w), borrower=w.x))
        it2 = new_item(w)
        run(conn, lambda cur: create(cur, w, it2, 3, 6))
        expect_error(conn, "identical pending request", lambda cur: create(cur, w, it2, 3, 6))
    check("G1: dates of a held booking, blocked borrower, non-member and duplicate requests are rejected",
          "UC-B5 2a, 3a, 3b; FR-B-06", c_g1)

    # ---------- holds (ADR-0003)
    def c_locality_hold():
        def body(cur):
            t = create(cur, w, new_item(w), borrower=w.i)
            ev(cur, w, t, "held_for_review", "SYSTEM", None, "HELD_FOR_REVIEW", payload={"hold_reason": "locality_inconclusive"})
            eq(one(cur, "SELECT hold_reason FROM borrowing_transaction WHERE id = %s", (t,)), "locality_inconclusive", "projection")
            eq(live_case(cur, t)[1:], ("LOCALITY_HOLD", "locality_inconclusive", "OPEN"), "case")
            d = decide(cur, w, t, "CLEARED")
            ev(cur, w, t, "hold_cleared", "MODERATOR", w.m, "LOCALITY_CHECKED", evidence={"decision_id": str(d)})
            eq(live_case(cur, t)[3], "DECIDED", "case status")
            return t
        t = run(conn, body)
        expect_error(conn, "invalid transition", lambda cur: None or ev(cur, w, t, "hold_cleared", "MODERATOR", w.m, "ASSESSED"))
    check("Inconclusive locality -> HELD_FOR_REVIEW (case opened), cleared -> LOCALITY_CHECKED, never directly ASSESSED",
          "FR-B-07/FR-B-08 acceptance criteria; ES-10; ADR-0003", c_locality_hold)

    def c_locality_mismatch():
        txn = run(conn, lambda cur: create(cur, w, new_item(w), borrower=w.f))
        expect_error(conn, "VERIFIED coarse outcome", lambda cur: to_checked(cur, w, txn))
        expect_error(conn, "does not match", lambda cur: ev(cur, w, txn, "held_for_review", "SYSTEM", None, "HELD_FOR_REVIEW",
                                                            payload={"hold_reason": "locality_inconclusive"}))
        run(conn, lambda cur: ev(cur, w, txn, "held_for_review", "SYSTEM", None, "HELD_FOR_REVIEW",
                                 payload={"hold_reason": "locality_conflict"}))
    check("Conflicting locality can only be recorded as a locality_conflict hold (no auto-rejection)",
          "FR-A-08; ES-09; UC-B5 4b", c_locality_mismatch)

    def c_wrong_clear_target():
        def setup(cur):
            t = create(cur, w, new_item(w), borrower=w.i)
            ev(cur, w, t, "held_for_review", "SYSTEM", None, "HELD_FOR_REVIEW", payload={"hold_reason": "locality_inconclusive"})
            return t, decide(cur, w, t, "CLEARED")
        t, d = run(conn, setup)
        run(conn, lambda cur: ev(cur, w, t, "hold_cleared", "MODERATOR", w.m, "LOCALITY_CHECKED", evidence={"decision_id": str(d)}))
        a = run(conn, lambda cur: assessment(cur, t, hold="manipulation_risk", risk=72, state="REVIEW_RECOMMENDED"))
        run(conn, lambda cur: ev(cur, w, t, "held_for_review", "SYSTEM", None, "HELD_FOR_REVIEW",
                                 evidence={"assessment_id": str(a)}, payload={"hold_reason": "manipulation_risk"}, config=CFG))
        eq(run(conn, lambda cur: one(cur, "SELECT count(*) FROM escalation_case WHERE transaction_id = %s", (t,))), 2, "cases")
        d2 = run(conn, lambda cur: decide(cur, w, t, "CLEARED"))
        expect_error(conn, "cannot be cleared to LOCALITY_CHECKED",
                     lambda cur: ev(cur, w, t, "hold_cleared", "MODERATOR", w.m, "LOCALITY_CHECKED", evidence={"decision_id": str(d2)}))
        run(conn, lambda cur: ev(cur, w, t, "hold_cleared", "MODERATOR", w.m, "ASSESSED", evidence={"decision_id": str(d2)}))
    check("Re-held after clearance opens a new case; a manipulation hold clears only to ASSESSED",
          "UC-I4 4d; ADR-0003; ES-04", c_wrong_clear_target)

    def c_risk_check():
        txn = run(conn, lambda cur: create(cur, w, new_item(w)))
        # corroborated level 4 that is not held: refused
        expect_error(conn, "assessment_rule_ck",
                     lambda cur: assessment(cur, txn, risk=65, state="REVIEW_RECOMMENDED", rule="R9", corroborated=True))
        # level 4 claimed without corroboration: refused (ADR-0007 cap)
        expect_error(conn, "assessment_level_ck",
                     lambda cur: assessment(cur, txn, hold="manipulation_risk", risk=72, state="REVIEW_RECOMMENDED",
                                            corroborated=False, level=4))
        # a single strong signal (score 68, uncorroborated) is level 3: verification requested, request not held
        run(conn, lambda cur: assessment(cur, txn, risk=68, state="REVIEW_RECOMMENDED", rule="R5", corroborated=False))
    check("Corroborated manipulation risk >= 60 (level 4) must hold the request; an uncorroborated score is capped "
          "at level 3 and is not held", "FR-T-06 acceptance criterion; ADR-0007; test suite 12", c_risk_check)

    def c_rule_table():
        txn = run(conn, lambda cur: create(cur, w, new_item(w)))
        for rule, (state, decision, hold) in RULES.items():
            risk = 70 if rule == "R2" else 45 if rule == "R5" else 5
            run(conn, lambda cur: assessment(cur, txn, hold=hold, risk=risk, state=state, rule=rule))
        expect_error(conn, "assessment_rule_ck",       # SUFFICIENT_EVIDENCE is never produced by the sparse rule
                     lambda cur: assessment(cur, txn, state="SUFFICIENT_EVIDENCE", rule="R6_SPARSE"))
        expect_error(conn, "assessment_rule_ck",       # an open dispute is never held (decision D12)
                     lambda cur: assessment(cur, txn, hold="manipulation_risk", state="ACTIVE_DISPUTE", rule="R1"))
        expect_error(conn, "assessment_rule_ck", lambda cur: assessment(cur, txn, rule="R99", decision="PROCEED"))
    check("Every stored assessment follows the A5 decision table (rule -> state, decision, hold reason)",
          "FR-T-01; FR-T-06; ADR-0007; ADR-0008; decision D12", c_rule_table)

    def c_engine_failure():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_checked(cur, w, t)
            ev(cur, w, t, "held_for_review", "SYSTEM", None, "HELD_FOR_REVIEW", payload={"hold_reason": "engine_failure"})
            eq(one(cur, "SELECT count(*) FROM assessment WHERE transaction_id = %s", (t,)), 0, "no assurance state assigned")
            return t
        t = run(conn, setup)
        d = run(conn, lambda cur: decide(cur, w, t, "SAFEGUARDS_IMPOSED", safeguards='["handover photos"]'))
        expect_error(conn, "UC-I4 3c", lambda cur: ev(cur, w, t, "hold_cleared", "MODERATOR", w.m, "LOCALITY_CHECKED",
                                                      evidence={"decision_id": str(d)}))
        d2 = run(conn, lambda cur: decide(cur, w, t, "CLEARED"))
        run(conn, lambda cur: ev(cur, w, t, "hold_cleared", "MODERATOR", w.m, "LOCALITY_CHECKED", evidence={"decision_id": str(d2)}))
        eq(run(conn, lambda cur: state_of(cur, t)), "LOCALITY_CHECKED", "retry state")
    check("Engine failure: held with no assessment; safeguards not allowed; cleared -> LOCALITY_CHECKED for re-run",
          "FR-T-07 acceptance criterion; UC-I4 3c; ADR-0003", c_engine_failure)

    def c_assessment_link():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_checked(cur, w, t)
            return t, assessment(cur, t, hold="manipulation_risk", risk=80, state="REVIEW_RECOMMENDED"), assessment(cur, t)
        t, held, ok = run(conn, setup)
        expect_error(conn, "non-holding assessment", lambda cur: ev(cur, w, t, "assessment_generated", "SYSTEM", None, "ASSESSED",
                                                                    evidence={"assessment_id": str(held)}, config=CFG))
        expect_error(conn, "same config_version", lambda cur: ev(cur, w, t, "assessment_generated", "SYSTEM", None, "ASSESSED",
                                                                 evidence={"assessment_id": str(ok)}, config="other-cfg"))
    check("assessment_generated must point to a non-holding assessment with the same config_version",
          "FR-T-01; NFR-D-01", c_assessment_link)

    def c_moderator_rules():
        def setup(cur):
            t = create(cur, w, new_item(w), borrower=w.i)
            ev(cur, w, t, "held_for_review", "SYSTEM", None, "HELD_FOR_REVIEW", payload={"hold_reason": "locality_inconclusive"})
            return t
        t = run(conn, setup)
        expect_error(conn, "decision_id", lambda cur: ev(cur, w, t, "request_declined", "MODERATOR", w.m, "DECLINED"))
        d_other = run(conn, lambda cur: decide(cur, w, t, "RESTRICTED", by=w.o))
        expect_error(conn, "not an active moderator", lambda cur: ev(cur, w, t, "request_declined", "MODERATOR", w.o, "DECLINED",
                                                                     evidence={"decision_id": str(d_other)}))
        expect_error(conn, "may not append", lambda cur: ev(cur, w, t, "hold_cleared", "LENDER", w.l, "LOCALITY_CHECKED"))
        d = run(conn, lambda cur: decide(cur, w, t, "RESTRICTED"))
        run(conn, lambda cur: ev(cur, w, t, "request_declined", "MODERATOR", w.m, "DECLINED", evidence={"decision_id": str(d)}))
        eq(run(conn, lambda cur: live_case(cur, t)[3]), "DECIDED", "case")
    check("Moderator transitions need a recorded decision, the right community, and a moderator role; restriction -> DECLINED",
          "FR-T-11; NFR-S-03; ADR-0003 (T12)", c_moderator_rules)

    def c_cancel_while_held():
        def body(cur):
            t = create(cur, w, new_item(w), borrower=w.i)
            ev(cur, w, t, "held_for_review", "SYSTEM", None, "HELD_FOR_REVIEW", payload={"hold_reason": "locality_inconclusive"})
            ev(cur, w, t, "request_cancelled", "BORROWER", w.i, "CANCELLED")
            eq(live_case(cur, t)[3], "WITHDRAWN", "case")
        run(conn, body)
    check("Borrower cancels a held request -> CANCELLED and the case is withdrawn without a decision",
          "T16; case C07 (SM-I2)", c_cancel_while_held)

    # ---------- handover and return
    def c_deposit():
        def setup(cur):
            t = create(cur, w, w.ladder)
            to_assessed(cur, w, t)
            ev(cur, w, t, "request_accepted", "LENDER", w.l, "ACCEPTED")
            report(cur, w, t, "HANDOVER", "LENDER", deposit=False)
            report(cur, w, t, "HANDOVER", "BORROWER")
            return t
        t = run(conn, setup)
        expect_error(conn, "UC-B7 3b", lambda cur: ev(cur, w, t, "handover_confirmed", "BORROWER", w.b, "ACTIVE"))
        run(conn, lambda cur: (report(cur, w, t, "HANDOVER", "LENDER", deposit=True),
                               report(cur, w, t, "HANDOVER", "BORROWER"),
                               ev(cur, w, t, "handover_confirmed", "BORROWER", w.b, "ACTIVE")))
        expect_error(conn, "not allowed in state", lambda cur: report(cur, w, t, "HANDOVER", "LENDER"))
    check("Required deposit must be recorded (record-only) before ACTIVE; confirmations only in their state",
          "FR-B-11 acceptance criterion; UC-B7 3b; I-4", c_deposit)

    def c_late():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_active(cur, w, t)
            ev(cur, w, t, "return_initiated", "BORROWER", w.b, "RETURN_INITIATED")
            report(cur, w, t, "RETURN", "LENDER")
            report(cur, w, t, "RETURN", "BORROWER")
            ev(cur, w, t, "return_confirmed", "BORROWER", w.b, "RETURNED")
            return t
        t = run(conn, setup)
        # the requested period ends in the future, so this return is on time; claiming "late" must fail
        expect_error(conn, "must be on_time", lambda cur: ev(cur, w, t, "transaction_closed", "SYSTEM", None, "COMPLETED",
                                                             payload={"outcome": "late"}))
        run(conn, lambda cur: ev(cur, w, t, "transaction_closed", "SYSTEM", None, "COMPLETED", payload={"outcome": "on_time"}))
    check("transaction_closed records the timeliness the data supports (on_time vs late)", "FR-B-13; UC-B8 4a", c_late)

    # ---------- disputes (ADR-0004)
    def c_return_disagreement():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_active(cur, w, t)
            ev(cur, w, t, "return_initiated", "BORROWER", w.b, "RETURN_INITIATED")
            report(cur, w, t, "RETURN", "LENDER", agreed=False)
            report(cur, w, t, "RETURN", "BORROWER")
            return t
        t = run(conn, setup)
        expect_error(conn, "disagreement is a dispute", lambda cur: ev(cur, w, t, "return_confirmed", "BORROWER", w.b, "RETURNED"))
        run(conn, lambda cur: ev(cur, w, t, "dispute_opened", "LENDER", w.l, "DISPUTED", payload={"reason": "DAMAGE"}))
        eq(run(conn, lambda cur: live_case(cur, t)[1]), "DISPUTE", "case")
        expect_error(conn, "invalid transition",
                     lambda cur: ev(cur, w, t, "dispute_opened", "BORROWER", w.b, "DISPUTED", payload={"reason": "OTHER"}))
        return t
    check("Condition disagreement cannot complete; it becomes DISPUTED with a case; a second dispute is rejected",
          "UC-B8 3a; FR-B-16; ES-07; UC-B12 1a", c_return_disagreement)

    def c_no_dispute_after_returned():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_active(cur, w, t)
            ev(cur, w, t, "return_initiated", "BORROWER", w.b, "RETURN_INITIATED")
            report(cur, w, t, "RETURN", "LENDER")
            report(cur, w, t, "RETURN", "BORROWER")
            ev(cur, w, t, "return_confirmed", "BORROWER", w.b, "RETURNED")
            return t
        t = run(conn, setup)
        expect_error(conn, "invalid transition",
                     lambda cur: ev(cur, w, t, "dispute_opened", "LENDER", w.l, "DISPUTED", payload={"reason": "DAMAGE"}))
    check("No dispute can be opened from RETURNED (raise it in RETURN_INITIATED instead)",
          "team decision D4; UC-B12 pre-condition v1.2; UC-B8 3a", c_no_dispute_after_returned)

    def c_dispute_pending():
        txn = run(conn, lambda cur: (lambda t: (to_assessed(cur, w, t), t)[1])(create(cur, w, new_item(w))))
        expect_error(conn, "invalid transition",
                     lambda cur: ev(cur, w, txn, "dispute_opened", "BORROWER", w.b, "DISPUTED", payload={"reason": "OTHER"}))
    check("A dispute cannot be opened before acceptance", "UC-B12 pre-condition", c_dispute_pending)

    def c_withdraw():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_active(cur, w, t)
            ev(cur, w, t, "dispute_opened", "BORROWER", w.b, "DISPUTED", payload={"reason": "CONDITION_MISMATCH"})
            return t
        t = run(conn, setup)
        expect_error(conn, "only the party who raised", lambda cur: ev(cur, w, t, "dispute_withdrawn", "LENDER", w.l, "ACTIVE"))
        expect_error(conn, "must restore ACTIVE", lambda cur: ev(cur, w, t, "dispute_withdrawn", "BORROWER", w.b, "ACCEPTED"))
        run(conn, lambda cur: ev(cur, w, t, "dispute_withdrawn", "BORROWER", w.b, "ACTIVE"))
        eq(run(conn, lambda cur: (state_of(cur, t), live_case(cur, t)[3])), ("ACTIVE", "WITHDRAWN"), "state, case")
    check("dispute_withdrawn: only the raiser, and only back to the stored previous_state; case withdrawn",
          "ADR-0004; FR-B-17 acceptance criterion", c_withdraw)

    def c_resolve():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_active(cur, w, t)
            ev(cur, w, t, "dispute_opened", "LENDER", w.l, "DISPUTED", payload={"reason": "DAMAGE"})
            return t
        t = run(conn, setup)
        d_party = run(conn, lambda cur: decide(cur, w, t, "DISPUTE_RESOLVED", by=w.a, role="ADMIN"))
        expect_error(conn, "invalid transition", lambda cur: ev(cur, w, t, "transaction_closed", "SYSTEM", None, "COMPLETED",
                                                                payload={"outcome": "on_time"}))

        def body(cur):
            e = ev(cur, w, t, "dispute_resolved", "ADMIN", w.a, "COMPLETED", evidence={"decision_id": str(d_party)},
                   payload={"decision": "damage confirmed"})
            eq(state_of(cur, t), "COMPLETED", "state")
            eq(one(cur, "SELECT status FROM booking WHERE transaction_id = %s", (t,)), "RELEASED", "booking")
            cur.execute("""INSERT INTO outcome (transaction_id, source_event_id, subject_id, observer_id, subject_role, metric,
                                                success, occurred_at, category_id, value_band, loan_duration)
                           VALUES (%s, %s, %s, %s, 'BORROWER', 'CONDITION_AGREED', false, now(), %s, 'LOW', interval '3 days')""",
                        (t, e, w.b, w.l, w.cat))
        run(conn, body)
    check("dispute_resolved closes DISPUTED -> COMPLETED (not transaction_closed); resolved outcome counts as evidence",
          "ADR-0004; FR-T-11 acceptance criterion; FR-B-15", c_resolve)

    def c_system_dispute():
        txn = run(conn, lambda cur: (lambda t: (to_active(cur, w, t), t)[1])(create(cur, w, new_item(w))))
        expect_error(conn, "only for non-return",
                     lambda cur: ev(cur, w, txn, "dispute_opened", "SYSTEM", None, "DISPUTED", payload={"reason": "DAMAGE"}))
    check("The system opens disputes only for non-return (overdue escalation)", "FR-B-14; UC-B8 *a; T24", c_system_dispute)

    # ---------- append-only, tamper evidence, privileges
    def c_append_only():
        run(conn, lambda cur: cur.execute("""INSERT INTO audit_log (authorisation, action, target_type, target_id, outcome)
                                             VALUES ('system:api', 'seed_loaded', 'database', 'dm', 'SUCCESS')"""))
        for sql in ("UPDATE lifecycle_event SET payload = '{}' WHERE event_id = (SELECT min(event_id) FROM lifecycle_event)",
                    "DELETE FROM lifecycle_event WHERE event_id = (SELECT min(event_id) FROM lifecycle_event)",
                    "TRUNCATE lifecycle_event CASCADE",
                    "UPDATE audit_log SET reason = 'x'"):
            expect_error(conn, "append-only", lambda cur, s=sql: cur.execute(s))
    check("Events and the audit log reject UPDATE, DELETE and TRUNCATE", "FR-M-05; NFR-S-05; test suite 5", c_append_only)

    def c_tamper():
        txn = run(conn, lambda cur: (lambda t: (to_completed(cur, w, t), t)[1])(create(cur, w, new_item(w))))

        def tamper(cur):
            cur.execute("ALTER TABLE lifecycle_event DISABLE TRIGGER lifecycle_event_append_only")
            cur.execute("UPDATE lifecycle_event SET payload = '{\"outcome\": \"late\"}' WHERE stream_id = %s "
                        "AND event_type = 'transaction_closed'", (txn,))
            cur.execute("ALTER TABLE lifecycle_event ENABLE TRIGGER lifecycle_event_append_only")
        run(conn, tamper)
        probs = run(conn, lambda cur: (cur.execute("SELECT stream_seq, problem FROM verify_event_chain(%s)", (txn,)),
                                       cur.fetchall())[1])
        if not probs:
            raise Expect("tampering was not detected")
    check("An edit made by a superuser with triggers disabled is detected by verify_event_chain()",
          "NFR-S-05 (100% of altered entries detected)", c_tamper)

    def c_app_role():
        def body(cur):
            cur.execute("SET LOCAL ROLE dm_app")
            cur.execute("UPDATE borrowing_transaction SET current_state = 'COMPLETED'")
        expect_error(conn, "permission denied", body)
    check("The application role cannot write the projection directly", "R1; NFR-S-02", c_app_role)

    # ---------- evidence rules, privacy, audit
    def c_outcome_source():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_active(cur, w, t)
            return t, one(cur, "SELECT max(event_id) FROM lifecycle_event WHERE stream_id = %s", (t,))
        t, e = run(conn, setup)
        expect_error(conn, "outcomes come only", lambda cur: cur.execute(
            """INSERT INTO outcome (transaction_id, source_event_id, subject_id, observer_id, subject_role, metric, success,
                                    occurred_at, category_id, value_band, loan_duration)
               VALUES (%s, %s, %s, %s, 'BORROWER', 'ON_TIME_RETURN', true, now(), %s, 'LOW', interval '1 day')""",
            (t, e, w.b, w.l, w.cat)))
        expect_error(conn, "only for COMPLETED", lambda cur: cur.execute(
            "INSERT INTO review (transaction_id, reviewer_id, reviewee_id, reviewee_role, ratings) VALUES (%s, %s, %s, 'LENDER', '{}')",
            (t, w.b, w.l)))
    check("Unconfirmed loans produce no outcome; reviews only after COMPLETED", "FR-T-03; FR-T-09", c_outcome_source)

    def c_attachments_locality():
        txn = run(conn, lambda cur: create(cur, w, new_item(w)))
        expect_error(conn, "metadata_stripped", lambda cur: cur.execute(
            """INSERT INTO attachment (transaction_id, uploaded_by, storage_key, content_sha256, mime_type, metadata_stripped)
               VALUES (%s, %s, 'k1', decode(repeat('ab', 32), 'hex'), 'image/jpeg', false)""", (txn, w.b)))
        expect_error(conn, "locality_refusal_ck", lambda cur: cur.execute(
            """INSERT INTO locality_verification (membership_id, method, outcome, geofence_signal, permission_refused,
                                                 valid_until)
               SELECT id, 'GEOFENCE_INVITATION', 'INCONCLUSIVE', 'INSIDE', true, now() + interval '1 day'
                 FROM membership LIMIT 1"""))
    check("Photos must have location metadata stripped; permission refusal is recorded only as INCONCLUSIVE",
          "NFR-PR-01; FR-A-08; ES-10", c_attachments_locality)

    def c_locality_rule():
        mem = run(conn, lambda cur: one(cur, "SELECT id FROM membership WHERE user_id = %s", (w.b4,)))   # unused by later checks
        b3m = run(conn, lambda cur: one(cur, "SELECT id FROM membership WHERE user_id = %s", (w.b3,)))

        def invite(cur, community, inviter, days=7):
            return one(cur, """INSERT INTO invitation (community_id, inviter_id, code_hash, expires_at)
                                VALUES (%s, %s, sha256(gen_random_uuid()::text::bytea), now() + %s * interval '1 day')
                                RETURNING id""", (community, inviter, days))

        def lv(cur, m, outcome, signal, inv=None, mock=False, dup=False):
            cur.execute("""INSERT INTO locality_verification (membership_id, method, outcome, geofence_signal, invitation_id,
                                                              mock_provider_detected, duplicate_suspected, valid_until)
                           VALUES (%s, 'GEOFENCE_INVITATION', %s, %s, %s, %s, %s, now() + interval '365 days')""",
                        (m, outcome, signal, inv, mock, dup))
        inv = run(conn, lambda cur: invite(cur, w.c, w.l))
        run(conn, lambda cur: lv(cur, mem, "VERIFIED", "INSIDE", inv))                      # both signals: verified
        expect_error(conn, "locality_verification_invitation_id_key", lambda cur: lv(cur, b3m, "VERIFIED", "INSIDE", inv))
        expect_error(conn, "locality_rule_ck", lambda cur: lv(cur, mem, "VERIFIED", "NEAR_BOUNDARY", None))
        expect_error(conn, "locality_rule_ck", lambda cur: lv(cur, mem, "VERIFIED", "INSIDE", None, mock=True))
        run(conn, lambda cur: lv(cur, mem, "INCONCLUSIVE", "INSIDE", None))                 # visitor-like: no invitation
        run(conn, lambda cur: lv(cur, mem, "CONFLICTING", "OUTSIDE", None))
        expired = run(conn, lambda cur: one(cur, """INSERT INTO invitation (community_id, inviter_id, code_hash, created_at,
                                                                         expires_at)
                                                    VALUES (%s, %s, sha256('old'::bytea), now() - interval '10 days',
                                                            now() - interval '3 days') RETURNING id""", (w.c, w.l)))
        expect_error(conn, "UC-A3 3d", lambda cur: lv(cur, b3m, "VERIFIED", "INSIDE", expired))
        other = run(conn, lambda cur: invite(cur, w.c2, w.x))
        expect_error(conn, "UC-A3 3d", lambda cur: lv(cur, b3m, "VERIFIED", "INSIDE", other))
        expect_error(conn, "moderator of this community", lambda cur: cur.execute(
            """INSERT INTO locality_verification (membership_id, method, outcome, approved_by, valid_until)
               VALUES (%s, 'MODERATOR_APPROVAL', 'VERIFIED', %s, now() + interval '1 day')""", (b3m, w.o)))
    check("A11 locality rule: outcome follows its signals; invitations single-use, unexpired, same community; "
          "approval only by this community's moderator", "A11; FR-A-07, FR-A-08; UC-A3 3d", c_locality_rule)

    def c_decision_kind_matches():
        def setup(cur):
            t = create(cur, w, new_item(w), borrower=w.i)
            ev(cur, w, t, "held_for_review", "SYSTEM", None, "HELD_FOR_REVIEW", payload={"hold_reason": "locality_inconclusive"})
            return t, decide(cur, w, t, "RESTRICTED")
        t, d = run(conn, setup)
        expect_error(conn, "does not match", lambda cur: ev(cur, w, t, "hold_cleared", "MODERATOR", w.m, "LOCALITY_CHECKED",
                                                            evidence={"decision_id": str(d)}))
    check("A moderator event must match the kind of the recorded decision (RESTRICTED cannot clear a hold)",
          "FR-T-11; ADR-0003; review finding R1", c_decision_kind_matches)

    def c_confirmation_order():
        def setup(cur):
            t = create(cur, w, new_item(w))
            to_assessed(cur, w, t)
            ev(cur, w, t, "request_accepted", "LENDER", w.l, "ACCEPTED")
            report(cur, w, t, "HANDOVER", "BORROWER")          # borrower "confirms" before any checklist exists
            report(cur, w, t, "HANDOVER", "LENDER")
            return t
        t = run(conn, setup)
        expect_error(conn, "after the lender", lambda cur: ev(cur, w, t, "handover_confirmed", "LENDER", w.l, "ACTIVE"))
    check("The borrower's confirmation counts only if made after the lender's checklist",
          "UC-B7 step 3; UC-B8 steps 2-3; review finding R2", c_confirmation_order)

    def c_creation_data_in_event():
        it = new_item(w)

        def bad(cur):
            txn = one(cur, """INSERT INTO borrowing_transaction (item_id, borrower_id, lender_id, requested_period)
                              VALUES (%s, %s, %s, %s) RETURNING id""", (it, w.b, w.l, rng(2, 5)))
            cur.execute("""INSERT INTO lifecycle_event (stream_id, stream_seq, event_type, actor_id, new_state, authorisation,
                                                        payload)
                           VALUES (%s, 1, 'request_created', %s, 'REQUEST_CREATED', 'party:borrower', %s)""",
                        (txn, w.b, json.dumps({"item_id": str(it), "requested_period": rng(3, 9)})))
        expect_error(conn, "request_created payload", bad)
    check("request_created carries the item and dates, so a transaction can be rebuilt from its events",
          "FR-B-09 (replay and recovery); review finding R3", c_creation_data_in_event)

    def c_pending_outcomes():
        def body(cur):
            t = create(cur, w, new_item(w))
            closed = to_completed(cur, w, t)
            eq(one(cur, "SELECT count(*) FROM v_pending_outcomes WHERE event_id = %s", (closed,)), 1, "pending before")
            cur.execute("""INSERT INTO outcome (transaction_id, source_event_id, subject_id, observer_id, subject_role, metric,
                                                success, occurred_at, category_id, value_band, loan_duration)
                           VALUES (%s, %s, %s, %s, 'BORROWER', 'ON_TIME_RETURN', true, now(), %s, 'LOW', interval '3 days')""",
                        (t, closed, w.b, w.l, w.cat))
            eq(one(cur, "SELECT count(*) FROM v_pending_outcomes WHERE event_id = %s", (closed,)), 0, "pending after")
        run(conn, body)
    check("Closings whose outcomes never reached the engine are listed for catch-up (v_pending_outcomes)",
          "FR-B-15; NFR-R-04; review finding R4", c_pending_outcomes)

    def c_audit():
        def body(cur):
            for k in range(3):
                cur.execute("""INSERT INTO audit_log (actor_id, authorisation, action, target_type, target_id, outcome, reason)
                               VALUES (%s, 'role:admin', 'audit_log_viewed', 'audit_log', 'all', 'SUCCESS', NULL)""", (w.a,))
            cur.execute("SELECT count(*) FROM audit_log a WHERE a.row_hash IS NULL OR (a.id > (SELECT min(id) FROM audit_log) "
                        "AND a.prev_hash IS DISTINCT FROM (SELECT b.row_hash FROM audit_log b WHERE b.id < a.id ORDER BY b.id DESC LIMIT 1))")
            eq(cur.fetchone()[0], 0, "broken links")
        run(conn, body)
        expect_error(conn, "audit_reason_ck", lambda cur: cur.execute(
            """INSERT INTO audit_log (actor_id, authorisation, action, target_type, target_id, outcome)
               VALUES (NULL, 'system:api', 'transition_rejected', 'borrowing_transaction', 'x', 'REJECTED')"""))
    check("Audit log is hash-chained; a rejected command must record its reason; log views are logged",
          "FR-M-05; UC-I6", c_audit)

    def c_extension_overlap():
        it = new_item(w)

        def setup(cur):
            t1 = create(cur, w, it, 2, 4)
            to_active(cur, w, t1)
            t2 = create(cur, w, it, 5, 8, borrower=w.b2)
            to_assessed(cur, w, t2)
            ev(cur, w, t2, "request_accepted", "LENDER", w.l, "ACCEPTED")
            return t1
        t1 = run(conn, setup)
        expect_error(conn, "booking_no_overlap", lambda cur: ev(cur, w, t1, "extension_approved", "LENDER", w.l, "ACTIVE",
                                                                payload={"new_due": day(6).isoformat()}))
    check("An extension cannot run into another held booking (designed now, built in iteration 2)", "FR-B-14; I04; ADR-0002",
          c_extension_overlap)

    # ---------- report
    lines = [f"Digital Mohalla schema v2.3 tests - {dt.datetime.now().isoformat(timespec='seconds')}",
             f"Server: {run(conn, lambda cur: one(cur, 'SELECT version()'))}", ""]
    for status, name, ref, detail in RESULTS:
        lines.append(f"[{status}] {name}  ({ref})")
        if detail:
            lines.append(f"        {detail}")
    passed = sum(r[0] == "PASS" for r in RESULTS)
    lines += ["", f"{passed}/{len(RESULTS)} passed"]
    out = "\n".join(lines)
    print(out)
    with open(os.path.join(HERE, "test_results.txt"), "w", encoding="utf-8") as fh:
        fh.write(out + "\n")
    conn.close()
    sys.exit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
