"""Single source of truth for the borrowing lifecycle (design step A3, Student 1).

States, event types and transitions are taken from 01_requirements/DigitalMohalla_Use_Cases_Ver1.md v1.3 section 2,
01_requirements/DigitalMohalla_FR_NFR_Ver1.md v1.3 (FR-B-05..FR-B-17, FR-T-06, FR-T-07, FR-T-11), ADR-0001..ADR-0005
and ADR-0007 (guards of T05 to T07 name the A5 decision-table rules).
The state-machine diagram text, transition_table.csv, the allowed_transition seed in schema.sql and
the transition table in State_Machine_Design.md are all generated from this file, so they cannot
disagree with each other.
"""

# --------------------------------------------------------------------------- states (Use Cases section 2)
PENDING = ["REQUEST_CREATED", "LOCALITY_CHECKED", "HELD_FOR_REVIEW", "ASSESSED"]
IN_PROGRESS = ["ACCEPTED", "ACTIVE", "RETURN_INITIATED", "RETURNED"]
TERMINAL = ["COMPLETED", "DECLINED", "CANCELLED", "EXPIRED", "NO_SHOW"]
SIDE = ["DISPUTED"]
STATES = PENDING + IN_PROGRESS + TERMINAL + SIDE          # the 14 states of FR-B-08

COMPOSITES = {"PENDING": PENDING, "IN_PROGRESS": IN_PROGRESS}

STATE_MEANING = {
    "REQUEST_CREATED": "Borrower submitted a request; dates marked as requested (soft hold, ADR-0001)",
    "LOCALITY_CHECKED": "Coarse locality verified, or a locality or engine-failure hold was cleared",
    "HELD_FOR_REVIEW": "Waiting for a moderator; hold reason recorded; never an automatic rejection",
    "ASSESSED": "Assurance state and evidence summary attached; waiting for the lender",
    "ACCEPTED": "Lender accepted; dates blocked by the overlap constraint (ADR-0002); handover pending",
    "ACTIVE": "Handover confirmed by both parties; loan running",
    "RETURN_INITIATED": "Borrower started the return",
    "RETURNED": "Both parties confirmed the return condition",
    "COMPLETED": "Closed normally or by moderator decision; outcome sent to the assurance engine",
    "DECLINED": "Declined by the lender, by a moderator (restriction), or by the system (dates taken)",
    "CANCELLED": "Withdrawn by the borrower before acceptance",
    "EXPIRED": "Lender did not respond within the response window",
    "NO_SHOW": "Handover did not happen within the grace period; dates released",
    "DISPUTED": "Dispute open; deposit record and other transitions frozen until a moderator decides "
                "or the raising party withdraws",
}

HOLD_REASONS = ["locality_inconclusive", "locality_conflict", "manipulation_risk",
                "high_value_low_confidence", "engine_failure"]                       # ADR-0003

# --------------------------------------------------------------------------- event types
# status: "frozen"   = listed in Use Cases section 2 / FR-B-09 (ADR-0001..0004 accepted 2026-10-11)
#         "accepted" = internal event types agreed on 2026-10-11 (team decision D2); built in iteration 2
EVENTS = [
    # name,                 status,     iteration, note
    ("request_created",      "frozen",   1, "B5 step 3"),
    ("locality_checked",     "frozen",   1, "B5 step 4"),
    ("held_for_review",      "frozen",   1, "B5 ext 4a, 4b, 5b, 5c, 5d; payload.hold_reason"),
    ("assessment_generated", "frozen",   1, "B5 step 5; carries config_version"),
    ("hold_cleared",         "frozen",   1, "ADR-0003"),
    ("request_accepted",     "frozen",   1, "B6 step 4"),
    ("request_declined",     "frozen",   1, "B6 ext 3a, 3c, step 5; I4 restriction"),
    ("request_cancelled",    "frozen",   1, "B6 ext *a"),
    ("request_expired",      "frozen",   2, "B6 ext *b (scheduler, iteration 2)"),
    ("handover_confirmed",   "frozen",   1, "B7 step 4"),
    ("no_show",              "frozen",   2, "B7 ext *a (scheduler, iteration 2)"),
    ("return_initiated",     "frozen",   1, "B8 step 1"),
    ("return_confirmed",     "frozen",   1, "B8 step 3"),
    ("transaction_closed",   "frozen",   1, "B8 step 4 (normal completion only, ADR-0004)"),
    ("dispute_opened",       "frozen",   1, "B12 step 3; stores previous_state"),
    ("dispute_resolved",     "frozen",   1, "ADR-0004"),
    ("dispute_withdrawn",    "frozen",   1, "ADR-0004"),
    # internal events (no state change), named in this design, iteration 2
    ("reminder_sent",        "accepted", 2, "Use Cases section 2 ('reminders are events inside ACTIVE'); B7 *a; B8 3b"),
    ("extension_requested",  "accepted", 2, "B8 ext 1a; FR-B-14"),
    ("extension_approved",   "accepted", 2, "B8 ext 1a; FR-B-14; moves the due date"),
    ("extension_declined",   "accepted", 2, "B8 ext 1a; FR-B-14"),
]
EVENT_NAMES = [e[0] for e in EVENTS]

# --------------------------------------------------------------------------- transitions
# frm may be a leaf state, a composite name (border transition) or None (initial pseudostate).
# to may be a state or "H" (shallow history of IN_PROGRESS = the previous_state stored in dispute_opened).
# actors: roles allowed to append the event (checked against the event's authorisation field).
T = []


def t(tid, frm, event, to, guard, action, actors, source, frs, es="", it=1, exclude=()):
    """exclude: leaf states of a composite source (or of the history target) the transition does not apply to."""
    T.append(dict(id=tid, frm=frm, event=event, to=to, guard=guard, action=action, actors=actors,
                  source=source, frs=frs, es=es, it=it, exclude=tuple(exclude)))


def froms(tr):
    """Leaf source states of a transition (composite border expanded, exclusions removed)."""
    return [s for s in COMPOSITES.get(tr["frm"], [tr["frm"]]) if s not in tr["exclude"]]


def tos(tr):
    """Leaf target states (history H expanded to the IN_PROGRESS states a dispute can be opened from)."""
    return [s for s in IN_PROGRESS if s not in tr["exclude"]] if tr["to"] == "H" else [tr["to"]]


B, L, M, A, S = "BORROWER", "LENDER", "MODERATOR", "ADMIN", "SYSTEM"
MOD = [M, A]

t("T01", None, "request_created", "REQUEST_CREATED",
  "G1: borrower is an active, verified member who can see the listing; listing published; dates free of "
  "held bookings (ADR-0002); no identical pending request; borrower not blocked by the lender",
  "mark dates as requested (blocks nothing)", [B], "B5 step 3; ext 2a, 3a, 3b, 3c; ADR-0001", "FR-B-06")
t("T02", "REQUEST_CREATED", "locality_checked", "LOCALITY_CHECKED",
  "coarse locality outcome = verified", "attach coarse result as evidence", [S], "B5 step 4", "FR-B-07, FR-A-08")
t("T03", "REQUEST_CREATED", "held_for_review", "HELD_FOR_REVIEW",
  "outcome = inconclusive; hold_reason = locality_inconclusive", "open case (D6)", [S],
  "B5 ext 4a", "FR-B-07, FR-A-08", "ES-10")
t("T04", "REQUEST_CREATED", "held_for_review", "HELD_FOR_REVIEW",
  "outcome = conflicting; hold_reason = locality_conflict", "flag; open case (D6)", [S],
  "B5 ext 4b", "FR-B-07, FR-A-08", "ES-09")
t("T05", "LOCALITY_CHECKED", "assessment_generated", "ASSESSED",
  "engine returned in time; assessment has no hold reason (rules R1, R3, R5 to R9)",
  "store assessment + config_version; notify lender", [S],
  "B5 steps 5-6; D3/4/5", "FR-B-07, FR-T-01", "ES-01, ES-02, ES-03, ES-05, ES-13")
t("T06", "LOCALITY_CHECKED", "held_for_review", "HELD_FOR_REVIEW",
  "rule R2: manipulation level 4 (risk >= 60, corroborated, ADR-0007); hold_reason = manipulation_risk",
  "store assessment; open case (D6)", [S],
  "B5 ext 5b; D3 ext 4a", "FR-T-05, FR-T-06", "ES-04")
t("T07", "LOCALITY_CHECKED", "held_for_review", "HELD_FOR_REVIEW",
  "rule R4: high value with weak or dissimilar evidence (N-7 resolved in A5); "
  "hold_reason = high_value_low_confidence", "store assessment; open case (D6)", [S],
  "B5 ext 5c; ADR-0003", "FR-T-06, FR-T-10", "ES-06")
t("T08", "LOCALITY_CHECKED", "held_for_review", "HELD_FOR_REVIEW",
  "engine failed or timed out; hold_reason = engine_failure", "log failure; no assurance state; open case (D6)", [S],
  "B5 ext 5d; D3 ext *a", "FR-T-07")
t("T09", "HELD_FOR_REVIEW", "hold_cleared", "LOCALITY_CHECKED",
  "hold_reason in {locality_inconclusive, locality_conflict}; authorised moderator; reason recorded",
  "attach any safeguards; assessment runs", MOD, "ADR-0003; I4 steps 3-4", "FR-T-11")
t("T10", "HELD_FOR_REVIEW", "hold_cleared", "LOCALITY_CHECKED",
  "hold_reason = engine_failure; no safeguards (none can attach); authorised moderator; reason recorded",
  "assessment re-runs", MOD, "ADR-0003; I4 ext 3c", "FR-T-07, FR-T-11")
t("T11", "HELD_FOR_REVIEW", "hold_cleared", "ASSESSED",
  "hold_reason in {manipulation_risk, high_value_low_confidence}; authorised moderator; reason recorded",
  "existing assessment + moderator note (+ safeguards) to lender", MOD, "ADR-0003; I4 steps 3-4", "FR-T-11", "ES-04")
t("T12", "HELD_FOR_REVIEW", "request_declined", "DECLINED",
  "moderator restricts; authorised; reason recorded", "remove requested-date mark; notify borrower", MOD,
  "ADR-0003; I4 steps 3-4", "FR-T-06, FR-T-11")
t("T13", "ASSESSED", "request_accepted", "ACCEPTED",
  "actor = listing owner; booking insert satisfies the overlap constraint (ADR-0002)",
  "write booking and event in one DB transaction; block dates; decline overlapping pending requests (T17)", [L],
  "B6 steps 3-5", "FR-B-05, FR-B-10")
t("T14", "ASSESSED", "request_declined", "DECLINED",
  "actor = listing owner", "optional reason; remove requested-date mark; notify borrower", [L],
  "B6 ext 3a", "FR-B-10")
t("T15", "ASSESSED", "request_expired", "EXPIRED",
  "response window elapsed", "remove requested-date mark; notify both", [S], "B6 ext *b", "FR-B-10, FR-B-18", it=2)
t("T16", "PENDING", "request_cancelled", "CANCELLED",
  "actor = borrower of this request", "remove requested-date mark; withdraw any open case", [B],
  "B6 ext *a (all pending states: SM-I2)", "FR-B-10")
t("T17", "PENDING", "request_declined", "DECLINED",
  "an overlapping acceptance committed first (reason = dates_taken)",
  "remove requested-date mark; notify borrower; withdraw any open case", [S],
  "B6 step 5, ext 3c; ADR-0001; ADR-0002", "FR-B-05, FR-B-10")
t("T18", "ACCEPTED", "handover_confirmed", "ACTIVE",
  "lender's handover checklist recorded AND borrower confirmed receipt AND (no deposit required OR deposit "
  "recorded as received)", "set due date; schedule reminders (it. 2); notify both", [B, L],
  "B7 steps 1-4; ext 2a, 3b", "FR-B-11")
t("T19", "ACCEPTED", "no_show", "NO_SHOW",
  "handover time + grace period passed without both confirmations", "release booking; notify both", [S],
  "B7 ext *a", "FR-B-12, FR-B-18", it=2)
t("T20", "ACTIVE", "return_initiated", "RETURN_INITIATED",
  "actor = borrower", "notify lender", [B], "B8 step 1", "FR-B-13")
t("T21", "RETURN_INITIATED", "return_confirmed", "RETURNED",
  "lender's return checklist AND borrower's confirmation recorded AND both agree on condition",
  "record return time", [B, L], "B8 steps 2-3", "FR-B-13")
t("T22", "RETURNED", "transaction_closed", "COMPLETED",
  "appended by the system immediately after RETURNED",
  "outcome = on_time | late; release booking; record deposit release (record-only); send outcome to engine; "
  "unlock reviews", [S], "B8 steps 4-5; ext 4a", "FR-B-13, FR-B-15", "ES-02")
t("T23", "IN_PROGRESS", "dispute_opened", "DISPUTED",
  "actor is a party; state is not RETURNED (team decision D4); inside the dispute window; no open dispute",
  "store previous_state; freeze deposit record and transitions; open case (D6); notify",
  [B, L], "B12 steps 1-5; B7 ext 3a; B8 ext 3a", "FR-B-16", "ES-07", exclude=["RETURNED"])
t("T24", "ACTIVE", "dispute_opened", "DISPUTED",
  "overdue beyond the limit (reason = non_return)", "as T23", [S], "B8 ext *a", "FR-B-14", "ES-08", it=2)
t("T25", "DISPUTED", "dispute_resolved", "COMPLETED",
  "authorised moderator of the community, not a party; decision and reason recorded",
  "record decision; resolved outcome sent to engine as evidence", MOD, "ADR-0004; I4 steps 3-4",
  "FR-T-11, FR-B-15", "ES-07")
t("T26", "DISPUTED", "dispute_withdrawn", "H",
  "actor = the party who raised the dispute",
  "restore previous_state from dispute_opened; unfreeze; withdraw case", [B, L],
  "ADR-0004; B12 ext 5b", "FR-B-17", exclude=["RETURNED"])

# internal transitions (state unchanged; event still appended with previous_state = new_state)
INTERNAL = [
    dict(id="I01", state="ACCEPTED", event="reminder_sent", guard="handover time reached", actors=[S],
         source="B7 ext *a", frs="FR-B-12, FR-B-18", it=2),
    dict(id="I02", state="ACTIVE", event="reminder_sent", guard="due date approaching or passed", actors=[S],
         source="B8 ext *a; Use Cases section 2", frs="FR-B-14, FR-B-18", it=2),
    dict(id="I03", state="ACTIVE", event="extension_requested", guard="actor = borrower; none pending",
         actors=[B], source="B8 ext 1a", frs="FR-B-14", it=2),
    dict(id="I04", state="ACTIVE", event="extension_approved",
         guard="actor = lender; new due date later; booking still satisfies the overlap constraint",
         actors=[L], source="B8 ext 1a", frs="FR-B-14", it=2),
    dict(id="I05", state="ACTIVE", event="extension_declined", guard="actor = lender", actors=[L],
         source="B8 ext 1a", frs="FR-B-14", it=2),
    dict(id="I06", state="RETURN_INITIATED", event="reminder_sent", guard="confirmation window elapsed",
         actors=[S], source="B8 ext 3b", frs="FR-B-13, FR-B-18", it=2),
]

# states that hold the item's dates (booking status HELD) - used by the schema
HOLDS_DATES = ["ACCEPTED", "ACTIVE", "RETURN_INITIATED", "RETURNED", "DISPUTED"]   # ADR-0002 as amended


def leaf_rows():
    """Expand border and history transitions to (from, event, to, actors, ref, it) leaf rows."""
    rows = []
    for tr in T:
        if tr["frm"] is None:
            continue
        for f in froms(tr):
            for to in tos(tr):
                rows.append((f, tr["event"], to, tr["actors"], tr["id"], tr["it"]))
    for it in INTERNAL:
        rows.append((it["state"], it["event"], it["state"], it["actors"], it["id"], it["it"]))
    # transitions that differ only by guard (e.g. T03/T04) share one (from, event, to) row;
    # the guard that distinguishes them is checked by the event trigger, not by the table key
    merged = {}
    for f, e, to, actors, ref, it in rows:
        k = (f, e, to)
        if k in merged:
            m = merged[k]
            merged[k] = (f, e, to, sorted(set(m[3]) | set(actors)),
                         m[4] + "/" + ref, min(m[5], it))
        else:
            merged[k] = (f, e, to, actors, ref, it)
    return list(merged.values())


if __name__ == "__main__":
    rows = leaf_rows()
    print(f"{len(STATES)} states, {len(EVENTS)} event types, {len(T)} transitions "
          f"(+{len(INTERNAL)} internal), {len(rows)} leaf rows")
    used = {r[1] for r in rows} | {"request_created"}
    assert used == set(EVENT_NAMES), set(EVENT_NAMES) ^ used
    reach = {"REQUEST_CREATED"}
    for _ in range(20):
        for f, e, to, *_ in rows:
            if f in reach:
                reach.add(to)
    assert reach == set(STATES), set(STATES) - reach
    print("every event type is used and every state is reachable")
