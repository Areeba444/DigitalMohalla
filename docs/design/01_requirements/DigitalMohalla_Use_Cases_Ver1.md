# Digital Mohalla: Use Cases (Baseline v1.3)

| Field | Value |
| :--- | :--- |
| Version | 1.3 (v1.2 plus the integration decisions of 2026-10-11) |
| Date | 2026-10-11 (v1.1: 2026-10-10; v1.2 and v1.3: 2026-10-11) |
| Authors | Team Digital Mohalla (v1.1 edits drafted with Claude; reviewed by: ______) |
| Status | Baseline: ADR-0001 to ADR-0005 accepted on 2026-10-11; ADR-0007 and ADR-0008 accepted for integration (Students 2 and 3 to initial) |
| Changes | See Appendix A (v1.2 rows at the end) |

**Companion files:** `01_requirements/DigitalMohalla_FR_NFR_Ver1.md` (same IDs, same terminology) and `03_architecture/DigitalMohalla_ADRs_Ver1.md` (ADR-0001 to ADR-0008).
**Derived from:** Platform Overview (post-defence version). Where this file and the overview differ, the overview wins, except where an accepted ADR says otherwise.
**Gate:** Mid-1 asks for requirements that are uniquely identified, testable and prioritised. The main body therefore holds only the core use cases, fully dressed. All other use cases are in Appendix B in brief form.

## 1. Conventions

**Scope tags:** **CORE** = named in the committed core. **ENAB** = core-enabling (the core cannot run without it). **SUPP** = supporting. **STRC** = stretch, built only after the core works.
**Priority:** **M** = must, needed for the borrowing loop. **S** = should, after the loop works. **C** = could.
**Terminology (fixed for all documents):**
- Direct reliability is a **recency-weighted Beta posterior** with a 90% credible interval. "Beta-Binomial" is not used for it, because Beta-Binomial is only the predictive distribution for future counts (Overview §5.2).
- **Assurance states** describe the evidence for a transaction, not the person: SUFFICIENT_EVIDENCE, REVIEW_RECOMMENDED, INSUFFICIENT_EVIDENCE, ACTIVE_DISPUTE. A single trust number is never shown. The assurance state is a separate attribute from the lifecycle state below: a request can be HELD_FOR_REVIEW in the lifecycle while its assurance state is REVIEW_RECOMMENDED (ES-04).
- Trust and manipulation risk are separate dimensions. High manipulation risk **holds a request in moderator review**; it never restricts automatically.
- The platform records and releases deposits as **record-only** entries. It never moves money (I-4, confirmed).

## 2. Borrowing lifecycle (single state list)

Event-sourced, as in Overview §3. Module label for B5 to B8 and B12: **Borrowing lifecycle**.

| State | Meaning | Entered by `event_type` |
| :--- | :--- | :--- |
| REQUEST_CREATED | Borrower submitted a request; dates marked as requested (soft hold, ADR-0001) | request_created |
| LOCALITY_CHECKED | Coarse locality outcome is *verified*, or a locality or engine-failure hold was cleared | locality_checked, hold_cleared |
| HELD_FOR_REVIEW | Locality inconclusive/conflicting, corroborated manipulation risk ≥ 60 (level 4, ADR-0007), high value with low confidence, or engine failure; waiting for a moderator. Never an automatic rejection. The hold reason is recorded | held_for_review |
| ASSESSED | Assurance state and evidence summary attached; waiting for the lender | assessment_generated, hold_cleared |
| ACCEPTED | Lender accepted; dates blocked under the overlap constraint (ADR-0002) until COMPLETED or NO_SHOW; handover pending | request_accepted |
| ACTIVE | Handover confirmed by both parties; loan running (reminders, extensions) | handover_confirmed |
| RETURN_INITIATED | Borrower started the return | return_initiated |
| RETURNED | Both parties confirmed condition | return_confirmed |
| COMPLETED | Transaction closed, normally or by moderator decision; outcome sent to the assurance engine | transaction_closed (normal), dispute_resolved (moderator) |
| DECLINED, CANCELLED, EXPIRED, NO_SHOW, DISPUTED | Side or terminal states (DISPUTED holds until a moderator decides or the raising party withdraws) | request_declined, request_cancelled, request_expired, no_show, dispute_opened |

Extension requests and reminders are events inside ACTIVE and do not change state (event types `reminder_sent`, `extension_requested`, `extension_approved`, `extension_declined`; built in iteration 2). `reminder_sent` is also used in ACCEPTED and RETURN_INITIATED.

**Exits from HELD_FOR_REVIEW (ADR-0003).** Hold reasons: `locality_inconclusive`, `locality_conflict`, `manipulation_risk`, `high_value_low_confidence`, `engine_failure`.

| Hold reason | Cleared | Safeguards imposed | Restricted |
| :--- | :--- | :--- | :--- |
| Locality (inconclusive or conflict) | → LOCALITY_CHECKED, then the assessment runs | Same, with safeguards attached | → DECLINED |
| Manipulation risk, high value with low confidence | → ASSESSED (existing assessment plus moderator note) | → ASSESSED with added safeguards | → DECLINED |
| Engine failure | → LOCALITY_CHECKED, assessment re-run | Not available (no assessment exists) | → DECLINED |

**Exits from DISPUTED (ADR-0004).** `dispute_resolved` → COMPLETED (moderator decision); `dispute_withdrawn` → the state stored as `previous_state` in the `dispute_opened` event. A dispute can be opened from ACCEPTED, ACTIVE or RETURN_INITIATED, not from RETURNED (B12).

**Event record (schema frozen):** `event_id, stream_id (transaction), stream_seq, event_type, schema_version, actor_id, occurred_at, previous_state, new_state, evidence_refs, authorisation, payload`. Assessment events also store `config_version`. `payload` is a JSON object holding event-specific data (dates, hold reason, decision, dispute reason, outcome), defined per event type in the event catalogue (ADR-0005). Any addition, including a new event type, needs sign-off from all three students and is reviewed in the class diagram. v1.1 added the event types `hold_cleared`, `dispute_resolved` and `dispute_withdrawn` (ADR-0003, ADR-0004); v1.2 adds `payload` and the four internal event types (ADR-0005).

## 3. Prioritisation of the main body

| Use case | Scope | Pri | FRs | Note |
| :--- | :--- | :--- | :--- | :--- |
| B5 Send borrowing request | CORE | M | FR-B-05 to B-07 | Locality and assessment steps added |
| B6 Respond to request | CORE | M | FR-B-05, B-10 | Overlap constraint at acceptance (ADR-0002) |
| B7 Confirm handover | CORE | M | FR-B-11, B-12 | |
| B8 Return and complete | CORE | M | FR-B-13 to B-15 | |
| B12 Raise dispute | CORE | M | FR-B-16, B-17 | |
| D3/4/5 Assess transaction assurance | CORE | M | FR-T-01 to T-07 | Computing core |
| D6 Escalate case | CORE | M | FR-T-10 | |
| I4 Resolve escalated case or dispute | CORE | M | FR-T-11 | Generalised from "Resolve disputes" |
| I6 View audit logs | CORE | M | FR-M-05 | |
| A3 Select neighbourhood, request membership | CORE (iteration 2) | M | FR-A-06 to A-09 | |
| A4 Approve or reject membership | CORE (iteration 2) | M | FR-A-10, A-11 | |

---

## 4. Fully dressed use cases

### UC-B5: Send borrowing request
| | |
| :--- | :--- |
| Module / Scope / Level | Borrowing lifecycle / CORE, M / User goal |
| Primary actor | Borrower. Secondary: Lender, Trust Engine (D3/4/5) |
| Stakeholders | **Borrower:** a clear, quick request. **Lender:** receives only valid requests with an evidence summary and matching safeguards. **Moderator:** risky requests held for review. **Platform:** every step logged as an event. |
| Pre-conditions | Borrower is logged in, is a verified member of a community with visibility of the listing, and is not suspended. Listing is Published and active. |
| Post-conditions | **Success:** request is ASSESSED (lender notified) or HELD_FOR_REVIEW; dates marked as requested (soft hold, ADR-0001; nothing is blocked); one event per transition with the frozen schema. **Failure:** no request is created and the calendar is unchanged. |

| # | Borrower | System |
| :-: | :--- | :--- |
| 1 | Opens an item, selects "Request to borrow" | Shows calendar, deposit, restrictions |
| 2 | Chooses start and end dates, adds an optional message | Checks the dates against held bookings (accepted and not yet closed, ADR-0002) |
| 3 | Confirms and sends | Validates, creates the request (REQUEST_CREATED), marks the dates as requested, appends `request_created` |
| 4 | | Runs the locality eligibility check on the coarse locality result; appends `locality_checked` (LOCALITY_CHECKED) |
| 5 | | Calls the assessment (D3/4/5); stores the assurance state, evidence, signals, safeguards and `config_version`; appends `assessment_generated` (ASSESSED) |
| 6 | | Notifies the lender (G3) and shows the borrower "request sent" with the safeguards that may apply |

**Extensions**
- *a. Borrower cancels before sending: nothing is created.
- 1a. Item is paused, expired or removed: block and offer similar items.
- 2a. Dates conflict with a held booking (ADR-0002): reject and suggest the next free window.
- 3a. Borrower is blocked by the lender: deny without revealing the block.
- 3b. Identical pending request exists: reject the duplicate.
- 3c. Other pending requests already cover these dates: the request is still created, since pending requests block nothing (ADR-0001). The first acceptance decides (B6 3c).
- 4a. Locality is inconclusive (permission refused, boundary, inaccurate GPS): HELD_FOR_REVIEW with hold reason `locality_inconclusive`, no rejection (ES-10).
- 4b. Locality conflicts with the claimed community: HELD_FOR_REVIEW with hold reason `locality_conflict` and a flag, no automatic rejection (ES-09).
- 5a. No verified history: state INSUFFICIENT_EVIDENCE with "Insufficient verified history; lender review required"; the request still reaches the lender (ES-01).
- 5b. Manipulation risk is high and corroborated (level 4: ≥ 60 with at least two signals ≥ 0.5, ADR-0007): the system **holds the request in moderator review** (HELD_FOR_REVIEW, hold reason `manipulation_risk`) and opens a case (D6). It does not block or restrict automatically. A score ≥ 60 from a single signal is level 3: verification is requested and the request reaches the lender as REVIEW_RECOMMENDED.
- 5c. High-value request with weak or dissimilar history (A5 rule R4: similarity < 0.5 or 90% lower bound < 0.60): HELD_FOR_REVIEW with hold reason `high_value_low_confidence`; when the moderator clears it, it reaches the lender as REVIEW_RECOMMENDED with extra safeguards (higher deposit record, verification) (ES-06). A high-value request with strong, similar evidence is not held (rule R8). N-7 resolved in A5.
- 5d. Engine fails or times out: HELD_FOR_REVIEW with hold reason `engine_failure`, failure logged, no default state assigned.

### UC-B6: Respond to borrowing request
| | |
| :--- | :--- |
| Module / Scope / Level | Borrowing lifecycle / CORE, M / User goal |
| Primary actor | Lender. Secondary: Borrower |
| Stakeholders | **Lender:** decides with the evidence summary. **Borrower:** timely answer, reason if declined. **Trust Engine:** receives the decision as an event. |
| Pre-conditions | Lender owns the listing and is logged in. Request is ASSESSED. |
| Post-conditions | Request is ACCEPTED, DECLINED, EXPIRED or CANCELLED. Calendar, notifications and event log updated. |

| # | Lender | System |
| :-: | :--- | :--- |
| 1 | Opens the notification or the requests inbox | Lists ASSESSED requests with borrower, dates, message |
| 2 | Selects a request | Shows the assurance state, factors with confidence, manipulation-risk summary and recommended safeguards (never a single number) |
| 3 | Chooses "Accept" | Checks the transition ASSESSED→ACCEPTED is allowed and the lender is authorised |
| 4 | | In one database transaction: writes the booking under the overlap constraint (ADR-0002), sets ACCEPTED, blocks the dates and appends `request_accepted`; then opens a chat thread (G1) |
| 5 | | Declines other pending requests that overlap the dates (DECLINED, reason "dates taken") |
| 6 | | Notifies the borrower and the declined borrowers (G3) |

**Extensions**
- 3a. Lender chooses "Decline": optional reason, DECLINED, requested-date mark removed, borrower notified.
- 3b. Lender proposes different dates: counter-offer; the borrower accepts or declines.
- 3c. Another acceptance for overlapping dates committed first: the database refuses this one and nothing is committed (ADR-0002). The lender is told the dates are taken and the request ends DECLINED with reason "dates taken".
- 3d. Actor is not the listing owner: deny and log the attempt.
- 2a. Assurance state is INSUFFICIENT_EVIDENCE: show "Insufficient verified history; lender review required"; the lender decides.
- *a. Borrower cancels first, from any pending state (REQUEST_CREATED, LOCALITY_CHECKED, HELD_FOR_REVIEW or ASSESSED): CANCELLED, requested-date mark removed, any open case withdrawn without a decision.
- *b. No response within the window: EXPIRED, requested-date mark removed, both notified.

### UC-B7: Confirm handover
| | |
| :--- | :--- |
| Module / Scope / Level | Borrowing lifecycle / CORE, M / User goal |
| Primary actor | Lender. Secondary: Borrower |
| Stakeholders | **Lender:** proof of condition before the item leaves. **Borrower:** proof that existing damage is not theirs. **Moderator:** evidence for any dispute. |
| Pre-conditions | Request is ACCEPTED. Both parties are logged in with active accounts. |
| Post-conditions | **Success:** ACTIVE, condition evidence stored, due date and return reminders scheduled. **Failure:** stays ACCEPTED, or moves to NO_SHOW or DISPUTED. |

| # | Actor | System |
| :-: | :--- | :--- |
| 1 | Lender selects "Start handover" at the meeting | Shows the condition checklist (photos mandatory when the assessment recommends them) |
| 2 | Lender completes the checklist and uploads photos | Stores them with a timestamp; asks the borrower to review |
| 3 | Borrower reviews and selects "Confirm receipt" | Checks both confirmations exist and any required deposit is recorded as received (record-only) |
| 4 | | Sets ACTIVE, records the due date, schedules reminders, appends `handover_confirmed`, notifies both |

**Extensions**
- *a. Handover time passes with no action: reminder; after the grace period NO_SHOW and the item is released.
- 2a. Photo upload fails: retry, or continue with the checklist only and mark "reduced evidence".
- 3a. Borrower disagrees with the recorded condition: adds comments or photos; if unresolved, raises a dispute (B12).
- 3b. Required deposit not yet recorded: block ACTIVE until the lender confirms receipt.

### UC-B8: Return item and complete borrowing
| | |
| :--- | :--- |
| Module / Scope / Level | Borrowing lifecycle / CORE, M / User goal |
| Primary actor | Borrower. Secondary: Lender, Trust Engine |
| Stakeholders | **Borrower:** clear record of a proper return. **Lender:** item back on time and in agreed condition. **Trust Engine:** accurate outcome data (timeliness, condition agreement). |
| Pre-conditions | Request is ACTIVE. Borrower is logged in with an active account. |
| Post-conditions | **Success:** COMPLETED; outcome sent to the engine as a verified event; calendar freed; deposit release recorded (record-only); reviews unlocked (D1). **Failure:** DISPUTED, or overdue with escalation running. |

| # | Actor | System |
| :-: | :--- | :--- |
| 1 | Borrower selects "Return item" | Sets RETURN_INITIATED, notifies the lender (G3) |
| 2 | Lender inspects against the handover checklist and uploads return photos | Shows the return checklist beside the handover record |
| 3 | Lender and borrower each confirm the condition | Sets RETURNED when both confirm; records the return time |
| 4 | | Compares return time with the due date (on time or late), sets COMPLETED, appends `transaction_closed` |
| 5 | | Sends the outcome to the engine, records the deposit release, frees the calendar, unlocks reviews, notifies both |

**Extensions**
- 1a. Borrower needs more time: extension request; the lender approves (due date updated) or declines.
- *a. Item overdue beyond the limit: escalating reminders, then an automatic dispute (B12) (ES-08).
- 3a. Lender reports damage or missing parts, or the parties disagree on condition: DISPUTED (B12), deposit record held, outcome not counted until resolved (ES-07).
- 3b. Lender does not confirm within the window: reminder, then flagged for moderator attention.
- 4a. Return is late: record a "late return" outcome and continue.

### UC-B12: Raise a dispute on a booking
| | |
| :--- | :--- |
| Module / Scope / Level | Borrowing lifecycle / CORE, M / User goal |
| Primary actor | Lender or Borrower (raising party). Secondary: Moderator (I4) |
| Stakeholders | **Raising party:** fair resolution. **Other party:** can respond with evidence. **Moderator:** complete evidence trail. **Trust Engine:** receives the resolved outcome. |
| Pre-conditions | Actor is a party to the booking. State is ACCEPTED, ACTIVE or RETURN_INITIATED and inside the dispute window. (RETURNED is closed at once by B8 step 4; a disagreement at return is raised in RETURN_INITIATED, B8 ext 3a.) |
| Post-conditions | Booking is DISPUTED (previous state stored in the `dispute_opened` event); deposit record and further transitions frozen; case in the moderator queue; both parties notified; events logged. |

| # | Actor | System |
| :-: | :--- | :--- |
| 1 | Party selects "Raise a dispute" | Checks state and time window |
| 2 | Chooses a reason (damage, non-return, condition mismatch, no-show, other) and describes it | Offers evidence upload |
| 3 | Attaches photos or documents and submits | Sets DISPUTED, freezes the deposit record and transitions, appends `dispute_opened` |
| 4 | | Triggers D6 to compile the evidence trail and queue the case |
| 5 | | Notifies the other party (who can respond with evidence) and the moderator (G3) |

**Extensions**
- *a. Party withdraws before submitting: draft discarded.
- 1a. A dispute is already open: show the existing case.
- 1b. Window closed: explain, suggest reporting the user (D7).
- 5a. Other party does not respond within the period: mark "no response" and pass to the moderator anyway.
- 5b. Parties settle: the raising party withdraws; `dispute_withdrawn` restores the previous state and the outcome is logged (ADR-0004).

### UC-D3/4/5: Assess transaction assurance
| | |
| :--- | :--- |
| Module / Scope / Level | Trust, reputation & safety / CORE, M / Subfunction (system-triggered) |
| Primary actor | Trust Engine (an internal component, Module 5; system-triggered through B5's «include», so it is not drawn as a UML actor) |
| Stakeholders | **Lender:** informed accept/decline. **Borrower:** not penalised for having no history. **Moderator:** anomalies visible with evidence. **Platform:** auditable, explainable decisions. |
| Pre-conditions | A request exists in LOCALITY_CHECKED (locality *verified*, or a locality or engine-failure hold cleared by a moderator). Transaction and item-value data are available. |
| Post-conditions | **Success:** one assurance state with confidence, evidence, manipulation-risk signals, safeguards, explanation and `config_version`, attached to the request and logged (`assessment_generated`). **Failure:** the request goes to HELD_FOR_REVIEW (`engine_failure`); no default state is assigned. |

| # | Trigger / Actor | System |
| :-: | :--- | :--- |
| 1 | Request reaches LOCALITY_CHECKED | Collects the parties' direct outcomes by role, recency and similarity of category, value band and duration; only confirmed outcomes count, disputed ones are excluded until resolved |
| 2 | | Computes the **recency-weighted Beta posterior**: mean and 90% credible interval, with effective evidence |
| 3 | | Adds bounded k-hop indirect evidence (k = 3, decay 0.7^(hops−1), reliability capped at 0.6), always below direct evidence |
| 4 | | Computes manipulation risk (0 to 100) as a separate dimension |
| 5 | | Applies the context policy (item value, verification, dispute history, role) and selects the assurance state |
| 6 | | Produces safeguards (deposit record, handover photos, fixed return date) and the explanation; stores the result |
| 7 | | Shows the evidence summary to the lender (B6) |

**Extensions**
- 1a. No verified history, or sparse history (effective evidence < 3) without community support (ρ < 0.3): INSUFFICIENT_EVIDENCE, wide interval, message "Insufficient verified history; lender review required" (ES-01, ES-12; ADR-0008).
- 3a. No community connections: skip indirect evidence and use direct evidence only, or the prior plus safeguards when there is no direct history either.
- 3b. History with other members but none with this lender: indirect evidence through community paths is shown in the explanation with its paths and reliability; with ρ ≥ 0.3 a sparse history becomes REVIEW_RECOMMENDED instead of INSUFFICIENT_EVIDENCE, never SUFFICIENT_EVIDENCE (ES-13, ADR-0008).
- 4a. Manipulation risk is high and corroborated (level 4, ADR-0007): flag for moderator review (D6) and hold the request (HELD_FOR_REVIEW, `manipulation_risk`). No automatic restriction (ES-04).
- 5a. Conflicting condition reports or an open dispute: ACTIVE_DISPUTE (ES-07). The request still reaches the lender (ASSESSED); the dispute is handled in its own case (decision D12).
- 5b. High-value request with dissimilar or weak history: held for a moderator (rule R4, see B5 ext 5c) (ES-06). A recent resolved dispute on an otherwise strong history gives REVIEW_RECOMMENDED (ES-03).
- 5c. A review that follows the other party's complaint and conflicts with confirmed records: flagged, reduced weight (ES-05).
- *a. Engine fails or times out: HELD_FOR_REVIEW with hold reason `engine_failure`, failure logged.

### UC-D6: Escalate case to moderator with evidence trail
| | |
| :--- | :--- |
| Module / Scope / Level | Trust, reputation & safety / CORE, M / Subfunction |
| Primary actor | Trust Engine or the dispute flow (internal; reached through «include» from B12 and «extend» from D3/4/5, not a UML actor) |
| Stakeholders | **Moderator:** complete, organised evidence. **Parties:** fair, prompt handling. **Platform:** ambiguous cases are not fully automated. |
| Pre-conditions | An escalation trigger exists: dispute filed, high-value low-confidence request, manipulation flag, contradictory evidence, failed transaction with manipulation signals, locality hold, or engine failure. |
| Post-conditions | A case exists in the moderator queue with trigger type, priority, reason and evidence trail. Parties are notified. Escalation is logged. |

| # | Trigger / Actor | System |
| :-: | :--- | :--- |
| 1 | Trigger occurs | Creates the case and assembles the trail: transaction details, item value, both claims, handover and return photos, relevant messages, history, trust analysis, manipulation signals |
| 2 | | Queues it with priority and reason, notifies the moderator and both parties |
| 3 | Moderator opens the case | Displays the evidence trail and continues in I4 |

**Extensions**
- 1a. Evidence incomplete (missing photos): mark the gaps and request them from the parties.
- 1b. A case for this transaction already exists: attach to it, no duplicate.
- 2a. No moderator available in the community: route to Admin.
- 2b. Chat is included only for a disputed or reported transaction (privacy rule, I-12).

### UC-I4: Resolve escalated case or dispute
| | |
| :--- | :--- |
| Module / Scope / Level | Administration & moderation / CORE, M / User goal |
| Primary actor | Moderator (Admin as alternate) |
| Stakeholders | **Parties:** fair, evidence-based outcome. **Moderator:** full evidence. **Trust Engine:** resolved outcomes feed later assessments. **Admin:** decisions are reviewable. |
| Case types | **Dispute** (booking is DISPUTED) and **non-dispute escalation** (request is HELD_FOR_REVIEW: manipulation flag, high value with low confidence, locality hold, engine failure). |
| Pre-conditions | A case from D6 exists and is assigned to this moderator, who holds the role for the community. |
| Post-conditions | A decision with reason is recorded as an event with actor, evidence and authorisation. **Dispute:** `dispute_resolved` moves the booking to COMPLETED and the resolved outcome is recorded as evidence. **Non-dispute:** cleared or safeguards imposed (`hold_cleared`, next state set by the hold reason: LOCALITY_CHECKED for locality and engine-failure holds, ASSESSED for manipulation and high-value holds), or restricted (`request_declined`, DECLINED by human decision only). See the exit table in §2 (ADR-0003). Parties notified. |

| # | Moderator | System |
| :-: | :--- | :--- |
| 1 | Opens the case | Shows the type-specific evidence trail (claims, photos, messages, timestamps, trust analysis, manipulation signals) and, for a hold, the hold reason |
| 2 | Reviews; requests more information if needed | Notifies the parties and sets a response deadline |
| 3 | Enters a decision and a reason | Validates that a reason exists, the moderator is authorised, and the decision is allowed for this hold reason |
| 4 | Confirms | Applies the state change, records the decision event, updates the evidence, notifies both parties |

**Extensions**
- 2a. A party misses the deadline: decide on the available evidence and note the non-response.
- 3a. Evidence is contradictory and cannot be resolved: record "unresolved", escalate to Admin.
- 3b. Case involves a moderator: escalate to Admin.
- 3c. Moderator chooses "safeguards imposed" for an engine-failure hold: not allowed, since no assessment exists; the options are retry (cleared) or restricted.
- 4a. Another moderator decided first: show the current state, apply nothing.
- 4b. A party appeals: a second moderator reviews.
- 4c. Decision is reversed later: both decisions stay in the log and the affected evidence is flagged until re-evaluated (ES-11).
- 4d. A cleared request is held again by the re-run assessment (for example, manipulation risk): it re-enters HELD_FOR_REVIEW with the new hold reason.

### UC-I6: View audit logs
| | |
| :--- | :--- |
| Module / Scope / Level | Administration & moderation / CORE, M / User goal |
| Primary actor | Admin |
| Stakeholders | **Admin:** investigates actions and detects misuse. **Members:** moderator decisions are accountable. **Platform:** logs are tamper-evident and privacy-safe. |
| Pre-conditions | Admin is logged in. Audit events exist (privileged actions and every lifecycle event). |
| Post-conditions | Matching events are displayed. The view is itself logged. Logs are not altered. |

| # | Admin | System |
| :-: | :--- | :--- |
| 1 | Opens the audit log | Shows recent events: actor, timestamp, previous and new state, evidence, authorisation |
| 2 | Filters by actor, user, transaction, date or event type | Returns matching events |
| 3 | Opens an event | Shows full details and related events |

**Extensions**
- 1a. No matching results: empty state.
- 3a. Event contains sensitive data: mask it per privacy rules.
- 3b. Pattern detected (e.g. one moderator's decisions concentrated on the same users): highlight it (supports the moderator-misuse case).
- 3c. Integrity check fails for an entry: show a tamper warning.

### UC-A3: Select neighbourhood and request community membership (core, iteration 2)
| | |
| :--- | :--- |
| Module / Scope / Level | Accounts & communities / CORE (iteration 2), M / User goal |
| Primary actor | Member (registered, no community yet) |
| Stakeholders | **Member:** joins the right community without exposing an address. **Moderator:** enough evidence to decide. **Residents:** only genuine neighbours get in. **Platform:** stores coarse results only. |
| Pre-conditions | Member is logged in with verified contact and is not a member of, or pending in, the chosen community. |
| Post-conditions | **Success:** membership request Pending (or Approved if open-join) with a coarse locality result and evidence; no exact location stored. **Failure:** no request; alternatives shown. |

| # | Member | System |
| :-: | :--- | :--- |
| 1 | Opens "Join a community" | Lists communities (nearby if coarse location is permitted, otherwise by name or code) |
| 2 | Selects a community | Shows rules and verification methods |
| 3 | Allows a one-time coarse location check and enters an invitation code from a verified member (method fixed in design step A11: geofence + invitation, moderator for anything uncertain) | Evaluates both in memory; stores only the coarse result (verified / inconclusive / conflicting) |
| 4 | Confirms and submits | Creates the request (Pending), notifies moderators |

**Extensions**
- 3a. Permission refused: offer another method; outcome is "insufficient evidence", not negative (ES-10).
- 3b. Boundary or inaccurate GPS: inconclusive, send to moderator review.
- 3c. Evidence conflicts with the claimed community: flag for review, no automatic rejection (ES-09).
- 3d. Invitation code invalid, expired or used: error, retry.
- 4a. Open-join community: approve automatically, notify moderators (what evidence this leaves is open, I-10).
- 4b. Duplicate request or membership: block and show status.
- 4c. Community closed or full: suggest others. 4d. Duplicate account suspected: attach the flag.

### UC-A4: Approve or reject membership request (core, iteration 2)
| | |
| :--- | :--- |
| Module / Scope / Level | Accounts & communities / CORE (iteration 2), M / User goal |
| Primary actor | Moderator (Admin as alternate) |
| Stakeholders | **Moderator:** a clear queue with evidence. **Applicant:** fair, timely decision with a reason. **Admin:** decisions auditable. |
| Pre-conditions | Moderator holds the role for this community. At least one request is Pending. |
| Post-conditions | Request is Approved (member role granted) or Rejected (reason recorded); audit event written; applicant notified. |

| # | Moderator | System |
| :-: | :--- | :--- |
| 1 | Opens the queue | Lists pending requests for the community |
| 2 | Selects a request | Shows minimal profile, locality evidence and result, duplicate/mismatch flags |
| 3 | Chooses Approve or Reject with a reason | Validates the reason and authorisation |
| 4 | Confirms | Updates the request, grants membership if approved, writes the audit event, notifies the applicant |

**Extensions**
- 2a. Evidence insufficient: request more evidence ("Awaiting information").
- 3a. Reason missing: block the decision.
- 3b. Earlier decision reversed: both stay in the log.
- 4a. Another moderator decided first: show current state. 4b. Not authorised for this community: deny and log. 4c. Applicant withdrew or was suspended: not applied.
- 4d. Applicant disputes a rejection: resubmits with new evidence (A3).

---

## Appendix A: Changes from earlier drafts

**v1 (from the previous draft)**

| # | Change |
| :-: | :--- |
| I-1 | B5 ext 5b now "holds the request in moderator review", matching D3 4a and Overview §5.6 |
| I-2 | B5 to B8 and B12 rewritten on the Overview §3 lifecycle; B5 gained locality and assessment steps |
| 3 | "Beta-Binomial" replaced by "recency-weighted Beta posterior" (D3, FR-T-02) |
| 4 | I4 generalised to "Resolve escalated case or dispute"; no separate UC-I7 |
| 5 | B5 to B8 and B12 relabelled "Borrowing lifecycle" |
| 6 | Main body reduced to the core set; all other use cases in Appendix B |

**v1.1 (design steps A0 and A1)**

| # | Change |
| :-: | :--- |
| A0 | Use case count confirmed at 68; deposits confirmed record-only (I-4); A3 method choice tied to design step A11 instead of interviews; document control block added |
| ADR-0001 | Soft hold: §2 REQUEST_CREATED, B5 step 3, post-conditions and ext 3c; B6 ext 3a and *a/*b wording |
| ADR-0002 | Overlap constraint at acceptance: B6 steps 3 to 5 and ext 3c; B5 ext 3c no longer uses `stream_seq` |
| ADR-0003 | HELD_FOR_REVIEW exits by hold reason: §2 exit table, hold reasons in B5 ext 4a, 4b, 5b, 5d and D3 *a, I4 post-conditions, steps 1 and 3 and ext 3c, 4d |
| ADR-0004 | `dispute_resolved` and `dispute_withdrawn`: §2, B12 ext 5b, I4 post-conditions |
| Other | §1 notes that assurance state and lifecycle state are separate attributes; D3 ext 3a wording fixed; D3 ext 3b added for ES-13; B5 ext 5c points to the open hold-or-review question (N-7) |

**v1.2 (team decisions of 2026-10-11, `00_management/Team_Decisions_2026-10-11.md`)**

| # | Change |
| :-: | :--- |
| D1, ADR-0005 | Event record gains `payload` (event-specific data); N-6 closed |
| D2 | Internal event types `reminder_sent`, `extension_requested`, `extension_approved`, `extension_declined` named in §2; built in iteration 2 |
| D3 | ADR-0001 to ADR-0004 accepted; status changed to baseline |
| D4 | B12 pre-condition: no dispute from RETURNED; note added to §2 |
| D6 | ADR-0002 wording: dates held from acceptance until COMPLETED or NO_SHOW; §2 ACCEPTED, B5 step 2 and ext 2a |
| D8 | B6 ext *a: the borrower may cancel from any pending state; an open case is withdrawn |
| A11 | A3 step 3: locality method fixed as coarse geofence + invitation with moderator fallback (`12_locality/Locality_Design_A11.md`) |

**v1.3 (integration decisions of 2026-10-11, `00_management/Integration_Decisions_2026-10-11.md`)**

| # | Change |
| :-: | :--- |
| D10, ADR-0007 | Manipulation hold needs corroboration (level 4): §2 HELD_FOR_REVIEW, B5 ext 5b, D3 ext 4a |
| D11, ADR-0008 | Sparse history without community support is INSUFFICIENT_EVIDENCE; community paths lift it to REVIEW_RECOMMENDED: D3 ext 1a, 3b |
| N-7 | Resolved by A5 rule R4: B5 ext 5c, D3 ext 5b |
| D12 | An open dispute gives ACTIVE_DISPUTE and the request still reaches the lender: D3 ext 5a |

## Appendix B: Remaining use cases (brief)

Detail for these is in the previous full draft; they are re-dressed only if promoted. Priority M/S/C as defined in section 1.

| ID | Name | Actor | Goal and key rule | Scope | Pri | FRs |
| :--- | :--- | :--- | :--- | :--- | :-: | :--- |
| A1 (+A9) | Register and verify contact | Guest | Register by email/phone/social; OTP limits; no identifier leak | ENAB | M | FR-A-01 to A-03 |
| A2 | Log in / out | Guest, Member | Sessions, lockout, suspended accounts denied | ENAB | M | FR-A-04, A-05 |
| A5 (+A6) | Manage profile and privacy | Member | Per-field visibility; exact addresses rejected | ENAB | S | FR-A-12, A-13 |
| A7 | Block a user | Member | Mutual hiding; active transactions not silently cancelled | ENAB | S | FR-A-14 |
| A8 | Apply for a role | Member | Vendor/Moderator application; role not granted by this UC | STRC | C | FR-A-15 |
| B1 | Create item listing | Lender | Listing with approximate location; moderation; restricted categories | ENAB | M | FR-B-01 to B-03 |
| B2 | Manage availability calendar | Lender | Block/open/pause; cannot touch Accepted/Active bookings | ENAB | M | FR-B-04 |
| B3 | Search for items | Borrower | Semantic retrieval, hybrid re-rank, keyword fallback | SUPP | S | FR-S-01 to S-03, S-05 |
| B4 | View item details and lender evidence | Borrower | Factors with confidence, never one number | SUPP | S | FR-S-04 |
| B9 | Post item request | Borrower | Request when nothing found | SUPP | C | FR-S-06 |
| B10 | Match requests to items | Scheduler | Fairness-constrained matching; proposals only | SUPP | C | FR-S-07, S-08 |
| B11 | Save a search or request | Borrower | Alerts on new matches | SUPP | C | FR-S-09 |
| B13 | Run scheduled jobs | Scheduler | Expiry, no-show, reminders, overdue escalation; idempotent | CORE | M | FR-B-18 |
| C1 | Create, edit, cancel event | Organizer | Draft, validate, notify | STRC | C | FR-EV-01 |
| C2 | Publish event with approval | Organizer, Moderator | Approval workflow | STRC | C | FR-EV-02 |
| C3 | Browse and search events | Member | Visibility-aware search | STRC | C | FR-EV-03 |
| C4 | Register / cancel registration | Attendee | Capacity never exceeded | STRC | C | FR-EV-04 |
| C5 | Waitlist and auto-promote | Attendee | First-come promotion | STRC | C | FR-EV-04 |
| C6 | Check in attendee | Organizer | QR/short code, manual fallback | STRC | C | FR-EV-04 |
| C7 | Agenda, volunteers, tasks | Organizer | Marked "do we need it?" in source; candidate to drop | STRC | C | FR-EV-05 |
| C8 | Event announcement, poll, Q&A | Organizer | Moderated posts | STRC | C | FR-EV-05 |
| C9 | Post-event feedback | Attendee | Attendees only | STRC | C | FR-EV-05 |
| C10 | Event recommendations | Member | Explained, normalised score (weights must sum to 1.00, I-6) | STRC | C | FR-EV-06 |
| D1 | Submit review and rating | Member | Only after a completed transaction; retaliation flag | CORE | M | FR-T-09 |
| D2 | View trust profile | Member | Factors separately; small samples suppressed | CORE | M | FR-T-08 |
| D7 | Report user, item, event, post | Member | Categories, priority for safety | ENAB | S | FR-T-12 |
| E1 | Create, edit, delete post | Contributor | Moderation screening | STRC | C | FR-FO-01 |
| E2 | Comment, reply, vote | Contributor | One vote per item | STRC | C | FR-FO-01 |
| E3 | Mark best answer | Author | Solved posts | STRC | C | FR-FO-02 |
| E4 | Search and filter discussions | Member | Duplicate avoidance | STRC | C | FR-FO-02 |
| E5 | Follow or save post | Member | Notifications | STRC | C | FR-FO-02 |
| E6 | Award badges | Scheduler | Transparent criteria | STRC | C | FR-FO-02 |
| F1 | Ask the chatbot | Member | Routed retrieval, cited answers | STRC | C | FR-CB-01, CB-03 |
| F2 | Low-confidence fallback | Member | Abstain, escalate to forum | STRC | C | FR-CB-02 |
| F3 | Chatbot feedback | Member | Report incorrect answer | STRC | C | FR-CB-04 |
| F4 | Manage knowledge base | Admin | Injection screening | STRC | C | FR-CB-04 |
| F5 | Content-gap report | Admin | Unanswered topics | STRC | C | FR-CB-04 |
| G1 | Item-request chat | Member | Linked to item or booking; screened | ENAB | M | FR-C-01 |
| G2 | Event group discussion | Attendee | Registrants only | STRC | C | FR-EV-07 |
| G3 | Notifications | Member | In-app, email, push; digest, retry | ENAB | M | FR-C-02 |
| G4 | Notification preferences | Member | Critical types stay on | SUPP | C | FR-C-03 |
| H1 | Register vendor | Vendor | Pending verification (overlaps A8, I-8) | STRC | C | FR-VD-01 |
| H2 | Post product or service | Vendor | Verified vendors only | STRC | C | FR-VD-01 |
| H3 | Search nearby vendors | Member | Rank by relevance, distance, rating | STRC | C | FR-VD-01 |
| H4 | Vendor inquiry and review | Member | Eligibility-gated review | STRC | C | FR-VD-01 |
| H5 | Verify vendor | Admin | Approve, reject, request information | STRC | C | FR-VD-01 |
| I1 | Manage users | Admin | Suspend, ban, roles, with reason | ENAB | S | FR-M-01 |
| I2 | Manage communities and categories | Admin | Boundaries, rules, restricted categories | ENAB | S | FR-M-02 |
| I3 | Review report queue | Moderator | Remove, keep, warn, escalate | ENAB | S | FR-M-03 |
| I5 | Flag spam and duplicates | AI moderation | Never auto-remove | SUPP | S | FR-M-04 |
| J1 | Admin dashboard | Admin | Small samples suppressed | SUPP | S | FR-N-01 |
| J2 | Personal contribution | Member | Own data only | SUPP | C | FR-N-02 |
| J3 | Neighbourhood analysis | Guest, Member | Activity only, no safety ranking | STRC | C | FR-NA-01 |

**Counts:** 13 IDs in the main body (11 sections), 55 IDs here (53 rows), 68 IDs in total (A 9, B 13, C 10, D 7, E 6, F 5, G 4, H 5, I 6, J 3). An earlier figure of 72 came from the previous FR/NFR draft and is corrected (N-1 resolved).
