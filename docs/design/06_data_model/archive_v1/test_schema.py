"""Automated checks for schema.sql (Digital Mohalla, Phase 2, Student 1).

Each test exercises one rule from the state machine or the schema design and
reports PASS/FAIL. Run:

    pip install pgserver psycopg2-binary     # embedded PostgreSQL, no server needed
    python test_schema.py                     # or: set DM_TEST_DSN=postgresql://... to use your own server

WARNING: the script drops and recreates the schema "dm" in the target database.
"""
import datetime as dt
import json
import os
import sys
import tempfile
import threading
import uuid

import psycopg2
from psycopg2.extras import register_uuid

register_uuid()
HERE = os.path.dirname(os.path.abspath(__file__))
NOW = dt.datetime.now(dt.timezone.utc)
RESULTS = []


# ----------------------------------------------------------------------------- infrastructure
def get_dsn():
    if os.environ.get('DM_TEST_DSN'):
        return os.environ['DM_TEST_DSN'], None
    import pgserver
    data = os.environ.get('DM_PGDATA') or os.path.join(tempfile.gettempdir(), 'dm_pgdata')
    srv = pgserver.get_server(data, cleanup_mode='stop')
    return srv.get_uri(), srv


def day(n, hour=10):
    d = (NOW + dt.timedelta(days=n)).replace(hour=hour, minute=0, second=0, microsecond=0)
    return d


def rng(a, b):
    return f'[{day(a).isoformat()},{day(b).isoformat()})'


class Expect(Exception):
    pass


def check(name, ref, fn):
    try:
        fn()
        RESULTS.append(('PASS', name, ref, ''))
    except Exception as e:  # noqa: BLE001 - report every failure
        RESULTS.append(('FAIL', name, ref, f'{type(e).__name__}: {str(e).strip()[:300]}'))


def expect_error(conn, fragment, fn, sqlstate=None):
    """Run fn in its own DB transaction; it must fail with a message containing fragment."""
    try:
        with conn:
            with conn.cursor() as cur:
                fn(cur)
    except psycopg2.Error as e:
        msg = (e.pgerror or str(e))
        if fragment.lower() not in msg.lower():
            raise Expect(f'failed for the wrong reason: {msg.strip()[:250]}')
        if sqlstate and e.pgcode != sqlstate:
            raise Expect(f'expected SQLSTATE {sqlstate}, got {e.pgcode}: {msg.strip()[:200]}')
        return
    raise Expect(f'expected an error containing "{fragment}" but the statement succeeded')


def run(conn, fn):
    with conn:
        with conn.cursor() as cur:
            return fn(cur)


def one(cur, sql, args=()):
    cur.execute(sql, args)
    return cur.fetchone()[0]


# ----------------------------------------------------------------------------- fixtures
class W:
    """World: ids of seeded rows."""


def seed(conn):
    w = W()

    def body(cur):
        def user(name, level='COMMUNITY_VERIFIED', role='MEMBER', status='ACTIVE'):
            return one(cur, """INSERT INTO app_user (display_name, email, verification_level, platform_role, status)
                               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                       (name, f'{name.lower()}@example.test', level, role, status))

        def community(name, code):
            return one(cur, """INSERT INTO community (name, join_code, allowed_methods, boundary_geojson)
                               VALUES (%s, %s, '{COARSE_GEOFENCE,INVITATION,MODERATOR_APPROVAL}',
                                       '{"type":"Polygon","coordinates":[]}') RETURNING id""", (name, code))

        def member(u, c, role='MEMBER', outcome='VERIFIED', conflict=False):
            m = one(cur, """INSERT INTO membership (user_id, community_id, role, status, decided_at)
                            VALUES (%s, %s, %s, 'APPROVED', now()) RETURNING id""", (u, c, role))
            cur.execute("""INSERT INTO locality_verification (membership_id, method, outcome, location_conflict, valid_until)
                           VALUES (%s, 'COARSE_GEOFENCE', %s, %s, now() + interval '180 days')""", (m, outcome, conflict))
            return m

        w.c = community('Gulberg Block C', 'GBC')
        w.c2 = community('Model Town A', 'MTA')
        w.b, w.l, w.m, w.a = user('Borrower'), user('Lender'), user('Moderator'), user('Admin', role='ADMIN')
        w.b2, w.b3, w.o = user('Borrower2'), user('Borrower3'), user('OtherMod')
        w.x = user('Outsider')                 # member of another community only
        w.f = user('Flagged')                  # member whose location evidence conflicts
        for u in (w.b, w.l, w.b2, w.b3):
            member(u, w.c)
        member(w.m, w.c, role='MODERATOR')
        member(w.o, w.c2, role='MODERATOR')
        member(w.x, w.c2)
        member(w.f, w.c, outcome='CONFLICTING', conflict=True)
        w.cat = one(cur, "INSERT INTO category (name) VALUES ('Tools') RETURNING id")

        def item(title, deposit=0, owner=None):
            return one(cur, """INSERT INTO item (owner_id, community_id, category_id, title, condition, value_band,
                                                 deposit_amount, status)
                               VALUES (%s, %s, %s, %s, 'GOOD', 'LOW', %s, 'PUBLISHED') RETURNING id""",
                       (owner or w.l, w.c, w.cat, title, deposit))
        w.item = item('Drill')
        w.item2 = item('Ladder', deposit=500)
        w.item3 = item('Spade')
        w.item4 = item('Tent')
        w.item5 = item('Mower')
        w.item_m = item('Saw', owner=w.l)
        w.draft = one(cur, """INSERT INTO item (owner_id, community_id, category_id, title, condition, value_band)
                              VALUES (%s, %s, %s, 'Draft thing', 'GOOD', 'LOW') RETURNING id""", (w.l, w.c, w.cat))
    run(conn, body)
    return w


# ----------------------------------------------------------------------------- domain helpers
def auth_for(w, role):
    return {'BORROWER': 'party:borrower', 'LENDER': 'party:lender', 'MODERATOR': f'role:moderator@{w.c}',
            'ADMIN': 'role:admin', 'SYSTEM': 'system:test-runner'}[role]


def ev(cur, w, txn, etype, role, actor, new_state, evidence=None, payload=None, seq=None, prev=None):
    cur.execute('SELECT current_state, version FROM borrow_transaction WHERE id = %s', (txn,))
    state, version = cur.fetchone()
    cur.execute("""INSERT INTO transaction_event (transaction_id, sequence_no, event_type, actor_user_id, actor_role,
                                                  previous_state, new_state, evidence, authorisation, payload)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING event_id""",
                (txn, seq if seq is not None else version + 1, etype, None if role == 'SYSTEM' else actor, role,
                 prev if prev is not None else state, new_state, json.dumps(evidence or {}), auth_for(w, role),
                 json.dumps(payload or {})))
    return cur.fetchone()[0]


def create_txn(cur, w, item, borrower, a, b, lender=None):
    txn = uuid.uuid4()
    cur.execute("""INSERT INTO borrow_transaction (id, item_id, borrower_id, lender_id, period)
                   VALUES (%s, %s, %s, %s, %s)""", (txn, item, borrower, lender or w.l, rng(a, b)))
    cur.execute('INSERT INTO request (transaction_id, requested_period) VALUES (%s, %s)', (txn, rng(a, b)))
    cur.execute("""INSERT INTO transaction_event (transaction_id, sequence_no, event_type, actor_user_id, actor_role,
                                                  new_state, authorisation)
                   VALUES (%s, 1, 'REQUEST_CREATED', %s, 'BORROWER', 'REQUESTED', 'party:borrower')""", (txn, borrower))
    return txn


def assurance(cur, txn, requires_moderator=False, state='SUFFICIENT_EVIDENCE'):
    return one(cur, """INSERT INTO assurance_result (transaction_id, engine_version, assurance_state, requires_moderator,
                                                    escalation_reason, success_probability, credible_low, credible_high,
                                                    confidence, manipulation_risk_score, explanation)
                       VALUES (%s, 'test-1', %s, %s, %s, 0.80, 0.60, 0.92, 'MEDIUM', 5, 'test explanation') RETURNING id""",
               (txn, state, requires_moderator, 'test escalation' if requires_moderator else None))


def report(cur, txn, phase, by, role):
    return one(cur, """INSERT INTO condition_report (transaction_id, phase, reported_by, reporter_role, checklist)
                       VALUES (%s, %s, %s, %s, '{"scratches": false}') RETURNING id""", (txn, phase, by, role))


def to_awaiting_lender(cur, w, txn, borrower):
    ev(cur, w, txn, 'LOCALITY_CHECKED', 'SYSTEM', None, 'ASSESSING', payload={'result': 'ELIGIBLE'})
    ar = assurance(cur, txn)
    ev(cur, w, txn, 'ASSURANCE_GENERATED', 'SYSTEM', None, 'AWAITING_LENDER', evidence={'assurance_result_id': str(ar)})


def to_on_loan(cur, w, txn, borrower, deposit=False):
    to_awaiting_lender(cur, w, txn, borrower)
    ev(cur, w, txn, 'LENDER_ACCEPTED', 'LENDER', w.l, 'AWAITING_HANDOVER')
    r = report(cur, txn, 'HANDOVER', w.l, 'LENDER')
    ev(cur, w, txn, 'HANDOVER_RECORDED', 'LENDER', w.l, 'AWAITING_RECEIPT',
       evidence={'condition_report_id': str(r)}, payload={'deposit_received': deposit})
    ev(cur, w, txn, 'HANDOVER_CONFIRMED', 'BORROWER', borrower, 'ON_LOAN')


def state_of(cur, txn):
    return one(cur, 'SELECT current_state FROM borrow_transaction WHERE id = %s', (txn,))


# ----------------------------------------------------------------------------- tests
def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    dsn, srv = get_dsn()
    admin = psycopg2.connect(dsn)
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute('DROP SCHEMA IF EXISTS dm CASCADE')
        cur.execute(open(os.path.join(HERE, 'schema.sql'), encoding='utf-8').read())
    conn = psycopg2.connect(dsn, options='-c search_path=dm')
    w = seed(conn)
    S = {}

    # --- structure ------------------------------------------------------------------
    def t_structure():
        def body(cur):
            assert one(cur, 'SELECT count(*) FROM allowed_transition') == 74, 'allowed_transition rows'
            assert one(cur, "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'txn_state'") == 18
            assert one(cur, "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'txn_event_type'") == 31
            used = one(cur, 'SELECT count(DISTINCT event_type) FROM allowed_transition')
            assert used == 30, f'every event except REQUEST_CREATED appears in the rules (got {used})'
        run(conn, body)
    check('Schema loads; 18 states, 31 event types, 74 leaf transitions', 'SM §4-6', t_structure)

    # --- happy path -------------------------------------------------------------------
    def t_happy():
        def body(cur):
            txn = create_txn(cur, w, w.item, w.b, 3, 6)
            to_on_loan(cur, w, txn, w.b)
            ev(cur, w, txn, 'REMINDER_SENT', 'SYSTEM', None, 'ON_LOAN', payload={'type': 'DUE_SOON'})
            rb = report(cur, txn, 'RETURN', w.b, 'BORROWER')
            ev(cur, w, txn, 'RETURN_INITIATED', 'BORROWER', w.b, 'RETURN_PENDING', evidence={'condition_report_id': str(rb)})
            rl = report(cur, txn, 'RETURN', w.l, 'LENDER')
            e = ev(cur, w, txn, 'RETURN_CONFIRMED', 'LENDER', w.l, 'COMPLETED',
                   evidence={'condition_report_id': str(rl)}, payload={'outcome': 'ON_TIME'})
            S['happy'], S['happy_close_event'] = txn, e
            return txn
        txn = run(conn, body)

        def verify(cur):
            assert state_of(cur, txn) == 'COMPLETED'
            assert one(cur, 'SELECT version FROM borrow_transaction WHERE id = %s', (txn,)) == 9
            assert one(cur, 'SELECT closed_at IS NOT NULL FROM borrow_transaction WHERE id = %s', (txn,))
            assert one(cur, 'SELECT replay_state(%s)', (txn,)) == 'COMPLETED', 'replay must equal projection'
            assert one(cur, 'SELECT count(*) FROM verify_event_chain(%s)', (txn,)) == 0, 'hash chain intact'
        run(conn, verify)
    check('Happy path request→COMPLETED; replay = projection; hash chain intact', 'T01,T03,T04,T10,T16,T17,I07,T25,T26', t_happy)

    def t_outputs_after_close():
        def body(cur):
            cur.execute("""INSERT INTO evidence_record (subject_user_id, subject_role, source_event_id, outcome, on_time,
                                                        condition_agreed, category_id, value_band, loan_duration, occurred_at)
                           VALUES (%s, 'BORROWER', %s, 'SUCCESS', true, true, %s, 'LOW', interval '3 days', now())""",
                        (w.b, S['happy_close_event'], w.cat))
            cur.execute("""INSERT INTO review (transaction_id, reviewer_id, reviewee_id, reviewee_role, ratings)
                           VALUES (%s, %s, %s, 'LENDER', '{"communication": 5}')""", (S['happy'], w.b, w.l))
        run(conn, body)
    check('COMPLETED unlocks verified evidence and reviews', '§3 step 13; UC-D1', t_outputs_after_close)

    # --- invalid transitions ------------------------------------------------------------
    def setup_on_loan(item, borrower, a, b):
        def body(cur):
            txn = create_txn(cur, w, item, borrower, a, b)
            to_on_loan(cur, w, txn, borrower)
            return txn
        return run(conn, body)

    S['loan'] = setup_on_loan(w.item3, w.b, 3, 6)

    check('X1 ON_LOAN --RETURN_CONFIRMED--> COMPLETED (skip return) rejected', 'X1', lambda: expect_error(
        conn, 'invalid transition',
        lambda cur: ev(cur, w, S['loan'], 'RETURN_CONFIRMED', 'LENDER', w.l, 'COMPLETED'), '23514'))

    check('X6 cancel while ON_LOAN rejected', 'X6', lambda: expect_error(
        conn, 'invalid transition',
        lambda cur: ev(cur, w, S['loan'], 'TRANSACTION_CANCELLED', 'BORROWER', w.b, 'CANCELLED')))

    def t_x4():
        txn = run(conn, lambda cur: (lambda t: (ev(cur, w, t, 'LOCALITY_CHECKED', 'SYSTEM', None, 'ASSESSING',
                                                    payload={'result': 'ELIGIBLE'}), t)[1])(
            create_txn(cur, w, w.item4, w.b, 3, 5)))
        S['assessing'] = txn
        expect_error(conn, 'invalid transition',
                     lambda cur: ev(cur, w, txn, 'LENDER_ACCEPTED', 'LENDER', w.l, 'AWAITING_HANDOVER'))
    check('X4 lender accepts before the evidence summary (in ASSESSING) rejected', 'X4', t_x4)

    check('Wrong role: borrower issues LENDER_ACCEPTED rejected', 'auth', lambda: expect_error(
        conn, 'may not issue',
        lambda cur: (ev(cur, w, S['assessing'], 'ASSURANCE_GENERATED', 'SYSTEM', None, 'AWAITING_LENDER',
                        evidence={'assurance_result_id': str(assurance(cur, S['assessing']))}),
                     ev(cur, w, S['assessing'], 'LENDER_ACCEPTED', 'BORROWER', w.b, 'AWAITING_HANDOVER')), '42501'))

    check('Impersonation: borrower claims the LENDER role rejected', 'auth', lambda: expect_error(
        conn, 'actor is not the lender',
        lambda cur: (ev(cur, w, S['assessing'], 'ASSURANCE_GENERATED', 'SYSTEM', None, 'AWAITING_LENDER',
                        evidence={'assurance_result_id': str(assurance(cur, S['assessing']))}),
                     ev(cur, w, S['assessing'], 'LENDER_ACCEPTED', 'LENDER', w.b, 'AWAITING_HANDOVER')), '42501'))

    check('Stale command (old sequence_no) rejected', 'concurrency §8', lambda: expect_error(
        conn, 'stale command',
        lambda cur: ev(cur, w, S['loan'], 'REMINDER_SENT', 'SYSTEM', None, 'ON_LOAN', seq=3), '40001'))

    check('previous_state that does not match the current state rejected', 'replay continuity', lambda: expect_error(
        conn, 'does not match current state',
        lambda cur: ev(cur, w, S['loan'], 'LOAN_OVERDUE', 'SYSTEM', None, 'OVERDUE', prev='AWAITING_RECEIPT'), '40001'))

    def t_race():
        """Lender declines while borrower cancels at the same moment: first commit wins."""
        txn = run(conn, lambda cur: (lambda t: (to_awaiting_lender(cur, w, t, w.b2), t)[1])(
            create_txn(cur, w, w.item5, w.b2, 20, 22)))
        c1 = psycopg2.connect(dsn, options='-c search_path=dm')
        c2 = psycopg2.connect(dsn, options='-c search_path=dm')
        cur1 = c1.cursor()
        cur1.execute('SELECT version, current_state FROM borrow_transaction WHERE id = %s', (txn,))
        ver, st = cur1.fetchone()
        cur1.execute("""INSERT INTO transaction_event (transaction_id, sequence_no, event_type, actor_user_id, actor_role,
                        previous_state, new_state, authorisation) VALUES (%s,%s,'LENDER_DECLINED',%s,'LENDER',%s,
                        'DECLINED','party:lender')""", (txn, ver + 1, w.l, st))
        out = {}

        def second():
            try:
                with c2.cursor() as cur2:
                    cur2.execute("""INSERT INTO transaction_event (transaction_id, sequence_no, event_type, actor_user_id,
                                    actor_role, previous_state, new_state, authorisation) VALUES (%s,%s,'TRANSACTION_CANCELLED',
                                    %s,'BORROWER',%s,'CANCELLED','party:borrower')""", (txn, ver + 1, w.b2, st))
                c2.commit()
                out['r'] = 'committed'
            except psycopg2.Error as e:
                c2.rollback()
                out['r'] = e.pgcode
        th = threading.Thread(target=second)
        th.start()
        th.join(1.5)
        assert th.is_alive(), 'second writer should be waiting on the row lock'
        c1.commit()
        th.join(10)
        c1.close(); c2.close()
        assert out.get('r') == '40001', f'second writer should get serialization_failure, got {out}'
        assert run(conn, lambda cur: state_of(cur, txn)) == 'DECLINED'
    check('Race: lender declines vs borrower cancels concurrently; loser gets 40001', 'UC-B6 *a; §8', t_race)

    # --- append-only and tamper evidence ------------------------------------------------
    for sql, label in (('UPDATE transaction_event SET payload = \'{"x":1}\'', 'UPDATE'),
                       ('DELETE FROM transaction_event', 'DELETE'),
                       ('TRUNCATE transaction_event CASCADE', 'TRUNCATE')):
        check(f'Append-only: {label} on transaction_event rejected (even for superuser)', 'R3; X14',
              lambda sql=sql: expect_error(conn, 'append-only', lambda cur: cur.execute(sql)))

    def t_tamper():
        txn = S['happy']
        with admin.cursor() as cur:
            cur.execute('ALTER TABLE dm.transaction_event DISABLE TRIGGER transaction_event_append_only')
            cur.execute("""UPDATE dm.transaction_event SET payload = '{"outcome":"LATE"}'
                            WHERE transaction_id = %s AND sequence_no = 9""", (txn,))
            cur.execute('ALTER TABLE dm.transaction_event ENABLE TRIGGER transaction_event_append_only')
        broken = run(conn, lambda cur: (cur.execute('SELECT sequence_no, problem FROM verify_event_chain(%s)', (txn,)),
                                        cur.fetchall())[1])
        assert broken == [(9, 'row content changed after it was written')], broken
    check('Tamper evidence: a row edited behind the triggers is detected by the hash chain', 'R3; UC-I6', t_tamper)

    def t_privileges():
        expect_error(conn, 'permission denied', lambda cur: (
            cur.execute('SET LOCAL ROLE dm_app'),
            cur.execute("UPDATE borrow_transaction SET current_state = 'COMPLETED' WHERE id = %s", (S['loan'],))), '42501')
        expect_error(conn, 'permission denied', lambda cur: (
            cur.execute('SET LOCAL ROLE dm_app'), cur.execute('DELETE FROM transaction_event')), '42501')

        def ok(cur):
            cur.execute('SET LOCAL ROLE dm_app')
            ev(cur, w, S['loan'], 'REMINDER_SENT', 'SYSTEM', None, 'ON_LOAN', payload={'type': 'DUE_SOON'})
        run(conn, ok)
    check('App role cannot edit the projection or delete events, but can append events', 'R1; R3', t_privileges)

    # --- bookings ---------------------------------------------------------------------
    def t_double_booking():
        a = run(conn, lambda cur: (lambda t: (to_awaiting_lender(cur, w, t, w.b), t)[1])(
            create_txn(cur, w, w.item, w.b, 30, 35)))
        b = run(conn, lambda cur: (lambda t: (to_awaiting_lender(cur, w, t, w.b2), t)[1])(
            create_txn(cur, w, w.item, w.b2, 32, 34)))       # overlapping pending request is allowed (DD-13)
        run(conn, lambda cur: ev(cur, w, a, 'LENDER_ACCEPTED', 'LENDER', w.l, 'AWAITING_HANDOVER'))
        expect_error(conn, 'overlaps another accepted booking',
                     lambda cur: ev(cur, w, b, 'LENDER_ACCEPTED', 'LENDER', w.l, 'AWAITING_HANDOVER'), '23P01')
        c = run(conn, lambda cur: (lambda t: (to_awaiting_lender(cur, w, t, w.b3), t)[1])(
            create_txn(cur, w, w.item, w.b3, 35, 38)))       # starts exactly when a ends: half-open ranges
        run(conn, lambda cur: ev(cur, w, c, 'LENDER_ACCEPTED', 'LENDER', w.l, 'AWAITING_HANDOVER'))
        S['booked_a'], S['booked_c'] = a, c
    check('No double booking: overlapping pending requests coexist, second acceptance rejected', 'R5; DD-13; X15', t_double_booking)

    check('G1: a new request into firmly booked dates rejected', 'G1; UC-B5 4a', lambda: expect_error(
        conn, 'G1: dates unavailable', lambda cur: create_txn(cur, w, w.item, w.b3, 31, 33), '23P01'))

    def t_blocks():
        expect_error(conn, 'cannot block dates', lambda cur: cur.execute(
            'INSERT INTO availability_block (item_id, period) VALUES (%s, %s)', (w.item, rng(33, 36))), '23P01')
        run(conn, lambda cur: cur.execute('INSERT INTO availability_block (item_id, period) VALUES (%s, %s)',
                                          (w.item, rng(50, 55))))
        expect_error(conn, 'G1: dates unavailable', lambda cur: create_txn(cur, w, w.item, w.b2, 52, 53))
    check('Lender blocks: cannot block booked dates; requests into blocked dates rejected', 'UC-B2 4a', t_blocks)

    def t_extension():
        def to_loan(cur):
            r = report(cur, S['booked_a'], 'HANDOVER', w.l, 'LENDER')
            ev(cur, w, S['booked_a'], 'HANDOVER_RECORDED', 'LENDER', w.l, 'AWAITING_RECEIPT',
               evidence={'condition_report_id': str(r)})
            ev(cur, w, S['booked_a'], 'HANDOVER_CONFIRMED', 'BORROWER', w.b, 'ON_LOAN')
        run(conn, to_loan)
        expect_error(conn, 'overlaps another accepted booking', lambda cur: ev(
            cur, w, S['booked_a'], 'EXTENSION_APPROVED', 'LENDER', w.l, 'ON_LOAN',
            payload={'new_due': day(37).isoformat()}), '23P01')
        expect_error(conn, 'new_due later than', lambda cur: ev(
            cur, w, S['booked_a'], 'EXTENSION_APPROVED', 'LENDER', w.l, 'ON_LOAN',
            payload={'new_due': day(34).isoformat()}))
    check('Extension into the next booking rejected (v1.1 guard "dates free"); shortening rejected', 'T23/I05', t_extension)

    def t_extension_ok():
        txn = run(conn, lambda cur: (lambda t: (to_on_loan(cur, w, t, w.b3), t)[1])(create_txn(cur, w, w.item4, w.b3, 40, 42)))
        run(conn, lambda cur: ev(cur, w, txn, 'EXTENSION_APPROVED', 'LENDER', w.l, 'ON_LOAN',
                                 payload={'new_due': day(44).isoformat()}))
        upper = run(conn, lambda cur: one(cur, 'SELECT upper(period) FROM borrow_transaction WHERE id = %s', (txn,)))
        assert upper == day(44), upper
    check('Valid extension moves the due date (projection updated by trigger)', 'I05', t_extension_ok)

    # --- closed states ----------------------------------------------------------------
    check('X13 any event after COMPLETED rejected', 'X13', lambda: expect_error(
        conn, 'invalid transition',
        lambda cur: ev(cur, w, S['happy'], 'DISPUTE_OPENED', 'BORROWER', w.b, 'DISPUTE_OPEN', payload={'reason': 'DAMAGE'})))

    # --- disputes and history -----------------------------------------------------------
    def t_dispute_withdraw():
        txn = S['loan']
        run(conn, lambda cur: ev(cur, w, txn, 'DISPUTE_OPENED', 'BORROWER', w.b, 'DISPUTE_OPEN',
                                 payload={'reason': 'DAMAGE', 'description': 'handle broke'}))
        assert run(conn, lambda cur: one(cur, "SELECT status FROM dispute WHERE transaction_id = %s", (txn,))) == 'OPEN'
        expect_error(conn, 'invalid transition', lambda cur: ev(cur, w, txn, 'DISPUTE_OPENED', 'LENDER', w.l,
                                                                'DISPUTE_OPEN', payload={'reason': 'OTHER'}))
        expect_error(conn, 'only the party who raised', lambda cur: ev(cur, w, txn, 'DISPUTE_WITHDRAWN', 'LENDER',
                                                                       w.l, 'ON_LOAN'), '42501')
        expect_error(conn, 'history violation', lambda cur: ev(cur, w, txn, 'DISPUTE_WITHDRAWN', 'BORROWER',
                                                               w.b, 'RETURN_PENDING'))
        run(conn, lambda cur: ev(cur, w, txn, 'DISPUTE_WITHDRAWN', 'BORROWER', w.b, 'ON_LOAN'))
        assert run(conn, lambda cur: one(cur, "SELECT status FROM dispute WHERE transaction_id = %s", (txn,))) == 'WITHDRAWN'
        assert run(conn, lambda cur: state_of(cur, txn)) == 'ON_LOAN'
    check('Dispute: one live case; only the raiser withdraws; H restores ON_LOAN, not another phase',
          'T28,T33; X8; X12; DD-11', t_dispute_withdraw)

    def t_dispute_resolve():
        txn = S['loan']
        run(conn, lambda cur: ev(cur, w, txn, 'DISPUTE_OPENED', 'LENDER', w.l, 'DISPUTE_OPEN',
                                 payload={'reason': 'DAMAGE'}))
        expect_error(conn, 'both parties must be heard', lambda cur: ev(
            cur, w, txn, 'DISPUTE_RESOLVED', 'MODERATOR', w.m, 'RESOLVED', payload={'resolution': 'CLOSE', 'reason': 'x'}))

        def statements(cur):
            d = one(cur, "SELECT id FROM dispute WHERE transaction_id = %s AND status = 'OPEN'", (txn,))
            cur.execute("INSERT INTO dispute_statement (dispute_id, author_id, author_role, statement) VALUES (%s,%s,'LENDER','scratched')", (d, w.l))
            cur.execute("INSERT INTO dispute_statement (dispute_id, author_id, author_role, statement) VALUES (%s,%s,'BORROWER','was already scratched')", (d, w.b))
            ev(cur, w, txn, 'DISPUTE_RESPONSE_ADDED', 'BORROWER', w.b, 'DISPUTE_OPEN')
        run(conn, statements)
        expect_error(conn, 'requires a recorded reason', lambda cur: ev(
            cur, w, txn, 'DISPUTE_RESOLVED', 'MODERATOR', w.m, 'RESOLVED', payload={'resolution': 'CLOSE'}))
        expect_error(conn, 'not an active moderator', lambda cur: ev(
            cur, w, txn, 'DISPUTE_RESOLVED', 'MODERATOR', w.o, 'RESOLVED', payload={'resolution': 'CLOSE', 'reason': 'x'}), '42501')
        e = run(conn, lambda cur: ev(cur, w, txn, 'DISPUTE_RESOLVED', 'MODERATOR', w.m, 'RESOLVED',
                                     payload={'resolution': 'CLOSE', 'reason': 'photos show prior damage'}))
        run(conn, lambda cur: cur.execute(
            """INSERT INTO evidence_record (subject_user_id, subject_role, source_event_id, outcome, on_time,
                                            condition_agreed, category_id, value_band, loan_duration, occurred_at)
               VALUES (%s, 'BORROWER', %s, 'SUCCESS', true, false, %s, 'LOW', interval '3 days', now())""", (w.b, e, w.cat)))
        assert run(conn, lambda cur: state_of(cur, txn)) == 'RESOLVED'
    check('Dispute resolution: needs both statements (or deadline), a reason and a moderator of that community',
          'T31; X10; X11; DD-16', t_dispute_resolve)

    def t_system_dispute():
        txn = run(conn, lambda cur: (lambda t: (to_on_loan(cur, w, t, w.b2), t)[1])(create_txn(cur, w, w.item3, w.b2, 70, 72)))
        run(conn, lambda cur: ev(cur, w, txn, 'LOAN_OVERDUE', 'SYSTEM', None, 'OVERDUE'))
        expect_error(conn, 'system-opened disputes need a system reason', lambda cur: ev(
            cur, w, txn, 'DISPUTE_OPENED', 'SYSTEM', None, 'DISPUTE_OPEN', payload={'reason': 'DAMAGE'}))
        expect_error(conn, 'a party dispute needs a party reason', lambda cur: ev(
            cur, w, txn, 'DISPUTE_OPENED', 'BORROWER', w.b2, 'DISPUTE_OPEN', payload={'reason': 'PARTY_SUSPENDED'}))
        run(conn, lambda cur: (None,
                               ev(cur, w, txn, 'DISPUTE_OPENED', 'SYSTEM', None, 'DISPUTE_OPEN', payload={'reason': 'NON_RETURN'})))
        expect_error(conn, 'only the party who raised', lambda cur: ev(cur, w, txn, 'DISPUTE_WITHDRAWN', 'BORROWER',
                                                                       w.b2, 'OVERDUE'))
        run(conn, lambda cur: ev(cur, w, txn, 'DISPUTE_ESCALATED', 'SYSTEM', None, 'DISPUTE_ESCALATED',
                                 payload={'reason': 'no moderator available'}))
        expect_error(conn, 'may not issue', lambda cur: ev(cur, w, txn, 'DISPUTE_RESOLVED', 'MODERATOR', w.m, 'RESOLVED',
                                                           payload={'resolution': 'CLOSE', 'reason': 'x'}), '42501')
        S['escalated'] = txn
    check('System NON_RETURN dispute cannot be withdrawn; once escalated only an admin decides', 'T24; T30; X12', t_system_dispute)

    def t_resume():
        txn = S['escalated']

        def hear(cur):
            d = one(cur, "SELECT id FROM dispute WHERE transaction_id = %s AND status = 'ESCALATED'", (txn,))
            cur.execute("INSERT INTO dispute_statement (dispute_id, author_id, author_role, statement) VALUES (%s,%s,'LENDER','late')", (d, w.l))
            cur.execute("INSERT INTO dispute_statement (dispute_id, author_id, author_role, statement) VALUES (%s,%s,'BORROWER','will return')", (d, w.b2))
        run(conn, hear)
        expect_error(conn, 'history violation', lambda cur: ev(cur, w, txn, 'DISPUTE_RESOLVED', 'ADMIN', w.a,
                                                               'AWAITING_HANDOVER', payload={'resolution': 'RESUME', 'reason': 'x'}))
        run(conn, lambda cur: ev(cur, w, txn, 'DISPUTE_RESOLVED', 'ADMIN', w.a, 'ON_LOAN',
                                 payload={'resolution': 'RESUME', 'reason': 'new date agreed', 'new_due': day(80).isoformat()}))
        assert run(conn, lambda cur: state_of(cur, txn)) == 'ON_LOAN'
    check('RESUME restores the ACTIVE phase with a new due date (shallow history)', 'T32; DD-11', t_resume)

    # --- locality and assurance (Student 1 / Student 2 interface) ---------------------------
    def t_locality():
        out = run(conn, lambda cur: create_txn(cur, w, w.item5, w.x, 90, 91))
        expect_error(conn, 'result must be INELIGIBLE', lambda cur: ev(
            cur, w, out, 'LOCALITY_CHECKED', 'SYSTEM', None, 'ASSESSING', payload={'result': 'ELIGIBLE'}))
        run(conn, lambda cur: ev(cur, w, out, 'LOCALITY_CHECKED', 'SYSTEM', None, 'INELIGIBLE', payload={'result': 'INELIGIBLE'}))
        fl = run(conn, lambda cur: create_txn(cur, w, w.item5, w.f, 92, 93))
        expect_error(conn, 'result must be INCONCLUSIVE', lambda cur: ev(
            cur, w, fl, 'LOCALITY_CHECKED', 'SYSTEM', None, 'ASSESSING', payload={'result': 'ELIGIBLE'}))
        run(conn, lambda cur: ev(cur, w, fl, 'LOCALITY_CHECKED', 'SYSTEM', None, 'ASSESSING', payload={'result': 'INCONCLUSIVE'}))
        S['inconclusive'] = fl
    check('Locality: non-member → INELIGIBLE; conflicting GPS evidence → INCONCLUSIVE (continues, never auto-rejected)',
          'T02/T03; DD-3; scenarios 9-10', t_locality)

    def t_assurance_link():
        txn = S['inconclusive']
        expect_error(conn, 'does not allow target', lambda cur: ev(
            cur, w, txn, 'ASSURANCE_GENERATED', 'SYSTEM', None, 'AWAITING_LENDER',
            evidence={'assurance_result_id': str(assurance(cur, txn, True, 'REVIEW_RECOMMENDED'))}))

        def path(cur):
            ar = assurance(cur, txn, True, 'REVIEW_RECOMMENDED')
            ev(cur, w, txn, 'ASSURANCE_GENERATED', 'SYSTEM', None, 'MODERATOR_REVIEW', evidence={'assurance_result_id': str(ar)})
            ev(cur, w, txn, 'EVIDENCE_REQUESTED', 'MODERATOR', w.m, 'MODERATOR_REVIEW', payload={'needed': 'invitation'})
            ev(cur, w, txn, 'EVIDENCE_SUBMITTED', 'BORROWER', w.f, 'ASSESSING')
            ar2 = assurance(cur, txn, False, 'REVIEW_RECOMMENDED')
            ev(cur, w, txn, 'ASSURANCE_GENERATED', 'SYSTEM', None, 'AWAITING_LENDER', evidence={'assurance_result_id': str(ar2)})
        run(conn, path)
        assert run(conn, lambda cur: state_of(cur, txn)) == 'AWAITING_LENDER'
    check('Assurance link: requiresModerator decides T04/T05; review → evidence → re-assess loop works',
          'T05,I01,T07,T04; DD-5 (mid-eval demo path)', t_assurance_link)

    def t_party_moderator():
        def body(cur):
            t = create_txn(cur, w, w.item_m, w.m, 100, 101)
            ev(cur, w, t, 'LOCALITY_CHECKED', 'SYSTEM', None, 'ASSESSING', payload={'result': 'ELIGIBLE'})
            ev(cur, w, t, 'ASSURANCE_GENERATED', 'SYSTEM', None, 'MODERATOR_REVIEW',
               evidence={'assurance_result_id': str(assurance(cur, t, True, 'REVIEW_RECOMMENDED'))})
            return t
        t = run(conn, body)
        expect_error(conn, 'cannot moderate its own', lambda cur: ev(cur, w, t, 'MODERATOR_CLEARED', 'MODERATOR', w.m,
                                                                     'AWAITING_LENDER', payload={'reason': 'ok'}), '42501')
        expect_error(conn, 'requires a recorded reason', lambda cur: ev(cur, w, t, 'MODERATOR_RESTRICTED', 'ADMIN', w.a,
                                                                       'DECLINED'))
    check('A moderator cannot decide a case they are party to; restriction needs a reason', 'X10; DD-16', t_party_moderator)

    # --- handover evidence ------------------------------------------------------------
    def t_handover():
        txn = run(conn, lambda cur: (lambda t: (to_awaiting_lender(cur, w, t, w.b),
                                                ev(cur, w, t, 'LENDER_ACCEPTED', 'LENDER', w.l, 'AWAITING_HANDOVER'), t)[2])(
            create_txn(cur, w, w.item2, w.b, 110, 112)))
        expect_error(conn, 'own HANDOVER condition report', lambda cur: ev(
            cur, w, txn, 'HANDOVER_RECORDED', 'LENDER', w.l, 'AWAITING_RECEIPT', payload={'deposit_received': True}))
        expect_error(conn, 'deposit of 500.00 must be recorded', lambda cur: ev(
            cur, w, txn, 'HANDOVER_RECORDED', 'LENDER', w.l, 'AWAITING_RECEIPT',
            evidence={'condition_report_id': str(report(cur, txn, 'HANDOVER', w.l, 'LENDER'))}))
        expect_error(conn, 'invalid transition', lambda cur: ev(cur, w, txn, 'HANDOVER_CONFIRMED', 'BORROWER', w.b, 'ON_LOAN'))
        run(conn, lambda cur: ev(cur, w, txn, 'HANDOVER_RECORDED', 'LENDER', w.l, 'AWAITING_RECEIPT',
                                 evidence={'condition_report_id': str(report(cur, txn, 'HANDOVER', w.l, 'LENDER'))},
                                 payload={'deposit_received': True}))
    check('Handover needs the lender\'s checklist and the deposit; borrower cannot confirm first', 'T16; X2; X3; UC-B7 6a', t_handover)

    # --- G1 and creation rules ------------------------------------------------------------
    def t_g1():
        expect_error(conn, 'G1: item is not PUBLISHED', lambda cur: create_txn(cur, w, w.draft, w.b, 120, 121))
        expect_error(conn, 'txn_parties_ck', lambda cur: create_txn(cur, w, w.item5, w.l, 120, 121))
        run(conn, lambda cur: cur.execute('INSERT INTO user_block (blocker_id, blocked_id) VALUES (%s, %s)', (w.l, w.b3)))
        expect_error(conn, 'G1: request not allowed', lambda cur: create_txn(cur, w, w.item5, w.b3, 120, 121))
        run(conn, lambda cur: create_txn(cur, w, w.item5, w.b2, 120, 121))
        expect_error(conn, 'G1: duplicate pending request', lambda cur: create_txn(cur, w, w.item5, w.b2, 120, 122))
        expect_error(conn, 'G1: requested start is in the past', lambda cur: create_txn(cur, w, w.item5, w.b, -2, 1))
    check('G1 guard: unpublished item, self-borrowing, blocked users, duplicates, past dates rejected', 'G1; X5', t_g1)

    def t_deferred():
        def body(cur):
            cur.execute("""INSERT INTO borrow_transaction (item_id, borrower_id, lender_id, period)
                           VALUES (%s, %s, %s, %s)""", (w.item5, w.b, w.l, rng(130, 131)))
        expect_error(conn, 'committed without REQUEST_CREATED', body)
    check('A transaction cannot be committed without its REQUEST_CREATED event and request row', 'R1', t_deferred)

    def t_suspended():
        txn = S['booked_c']
        run(conn, lambda cur: cur.execute("UPDATE app_user SET status = 'SUSPENDED' WHERE id = %s", (w.b3,)))
        expect_error(conn, 'actor account is not active', lambda cur: ev(cur, w, txn, 'TRANSACTION_CANCELLED', 'BORROWER',
                                                                         w.b3, 'CANCELLED'), '42501')
        run(conn, lambda cur: ev(cur, w, txn, 'DISPUTE_OPENED', 'SYSTEM', None, 'DISPUTE_OPEN',
                                 payload={'reason': 'PARTY_SUSPENDED'}))
        run(conn, lambda cur: cur.execute("UPDATE app_user SET status = 'ACTIVE' WHERE id = %s", (w.b3,)))
    check('Suspended party cannot act; system opens PARTY_SUSPENDED dispute instead', 'UC-I1 3a; T28', t_suspended)

    # --- other integrity rules --------------------------------------------------------------
    check('Review before completion rejected', 'UC-D1', lambda: expect_error(conn, 'only for COMPLETED', lambda cur: cur.execute(
        """INSERT INTO review (transaction_id, reviewer_id, reviewee_id, reviewee_role, ratings)
           VALUES (%s, %s, %s, 'LENDER', '{}')""", (S['booked_a'], w.b, w.l))))

    def t_evidence_rules():
        ev_id = run(conn, lambda cur: one(cur, "SELECT event_id FROM transaction_event WHERE transaction_id = %s AND sequence_no = 2",
                                          (S['happy'],)))
        expect_error(conn, 'verified closing event', lambda cur: cur.execute(
            """INSERT INTO evidence_record (subject_user_id, subject_role, source_event_id, outcome, condition_agreed,
                                            category_id, value_band, loan_duration, occurred_at)
               VALUES (%s, 'LENDER', %s, 'SUCCESS', true, %s, 'LOW', interval '1 day', now())""", (w.l, ev_id, w.cat)))
        expect_error(conn, 'facts are immutable', lambda cur: cur.execute(
            "UPDATE evidence_record SET outcome = 'FAILURE' WHERE subject_user_id = %s", (w.b,)))
    check('Evidence only from verified closing events; evidence facts immutable', '§5.12; R3', t_evidence_rules)

    check('Photo without stripped metadata (EXIF GPS) rejected', 'R4', lambda: expect_error(
        conn, 'attachment_metadata_stripped_check', lambda cur: cur.execute(
            """INSERT INTO attachment (transaction_id, uploaded_by, kind, storage_key, content_sha256, mime_type, metadata_stripped)
               VALUES (%s, %s, 'PHOTO', 'k1', decode(repeat('ab', 32), 'hex'), 'image/jpeg', false)""", (S['happy'], w.l))))

    check('Duplicate live membership request rejected', 'UC-A3 4b', lambda: expect_error(
        conn, 'membership_one_live_uq', lambda cur: cur.execute(
            "INSERT INTO membership (user_id, community_id) VALUES (%s, %s)", (w.b, w.c))))

    check('Permission refusal can only be recorded as INSUFFICIENT evidence, never a negative result', 'UC-A3 3a', lambda: expect_error(
        conn, 'locality_refusal_ck', lambda cur: cur.execute(
            """INSERT INTO locality_verification (membership_id, method, outcome, permission_refused, valid_until)
               SELECT id, 'COARSE_GEOFENCE', 'INCONCLUSIVE', true, now() + interval '1 day' FROM membership LIMIT 1""")))

    def t_privacy_scan():
        cols = run(conn, lambda cur: (cur.execute(r"""
            SELECT table_name || '.' || column_name FROM information_schema.columns
             WHERE table_schema = 'dm'
               AND column_name ~* '(^|_)(lat|latitude|lng|lon|long|longitude|coords?|coordinates|gps|geo_?point|address|street|house_no)(_|$)'"""),
            cur.fetchall())[1])
        assert cols == [], f'location-like columns found: {cols}'
    check('Privacy scan: no coordinate or address columns anywhere in the schema', 'R4; overview §13', t_privacy_scan)

    def t_audit():
        def body(cur):
            for act in ('COMMAND_REJECTED', 'AUDIT_VIEWED'):
                cur.execute("""INSERT INTO audit_log (actor_user_id, actor_role, action, target_type, target_id,
                                                      authorisation, outcome, reason)
                               VALUES (%s, 'ADMIN', %s, 'borrow_transaction', 'x', 'role:admin', 'REJECTED', 'test')""",
                            (w.a, act))
            cur.execute('SELECT prev_hash, row_hash FROM audit_log ORDER BY id')
            rows = cur.fetchall()
            assert rows[0][0] is None and bytes(rows[1][0]) == bytes(rows[0][1]), 'audit rows must be chained'
        run(conn, body)
        expect_error(conn, 'append-only', lambda cur: cur.execute('DELETE FROM audit_log'))
    check('Audit log is hash-chained and append-only', 'UC-I6; R3', t_audit)

    check('Moderator decision without a reason rejected', 'DD-16', lambda: expect_error(
        conn, 'moderator_decision_reason_check', lambda cur: cur.execute(
            """INSERT INTO moderator_decision (context, kind, decided_by, decider_role, transaction_id, reason)
               VALUES ('PRE_ACCEPTANCE_REVIEW', 'CLEAR', %s, 'MODERATOR', %s, '  ')""", (w.m, S['happy']))))

    # --- report ---------------------------------------------------------------------------
    conn.close()
    admin.close()
    passed = sum(r[0] == 'PASS' for r in RESULTS)
    lines = [f'Digital Mohalla schema tests: {passed}/{len(RESULTS)} passed', '']
    for status, name, ref, detail in RESULTS:
        lines.append(f'[{status}] {name}  ({ref})')
        if detail:
            lines.append(f'        {detail}')
    report_txt = '\n'.join(lines)
    print(report_txt)
    with open(os.path.join(HERE, 'test_results.txt'), 'w', encoding='utf-8') as f:
        f.write(f'Run: {NOW.isoformat()}  PostgreSQL via {"DM_TEST_DSN" if srv is None else "pgserver (embedded)"}\n')
        f.write(report_txt + '\n')
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
