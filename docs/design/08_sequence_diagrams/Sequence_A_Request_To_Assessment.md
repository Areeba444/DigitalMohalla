# Sequence Diagram Specification: UC-B5 Borrowing Request to Assessment
## Module 5: Trust & Assurance Engine — Sequence Diagram (a)

**Project:** Digital Mohalla  
**Component:** UC-B5 Send Borrowing Request & Module 5 Assessment Pipeline  
**Deliverable:** T6 — Sequence Diagram (a) (Mermaid, Draw.io XML, and Hand-Drawing Guide)  
**Owner:** Student 2  
**Version:** 1.2, 11 October 2026. v1.2 (notation review): the diagram is redrawn in standard UML 2.5 by `generate_sequence_a.py` with the same messages (actors as stick figures, `:Class` lifelines as in the component diagram, activation bars, one guard per `alt` operand, the normal flow in the `[else]` operand of the locality check). v1.0 (Student 2). v1.1 (integration): the request carries no location and the locality check reads the stored A11 result (decision D13); frozen event-field names; config 1.1.0; manipulation hold = corroborated level 4 (ADR-0007); hold decided by the assessment's hold reason (D12)  
**Status:** Design baseline; awaiting A14 second-member review  
**Traceability:** UC-B5 (Steps 1–6, Extensions 4a, 4b, 5a–5d); FR-B-05, FR-B-06, FR-B-07, FR-B-08, FR-B-09; FR-T-01, FR-T-06, FR-T-07, FR-T-10; ADR-0001, ADR-0003; NFR-D-01, NFR-R-02, NFR-P-04; FR-A-07, NFR-PR-01

---

## 1. Overview & Scope

This sequence diagram specifies the dynamic interactions between the **Borrower**, **Borrowing Controller** (Application Service boundary), **Locality Service**, **Trust Engine (Module 5)**, **Event Store**, **Notification Service**, **Lender**, and **Community Moderator**.

It specifies the complete end-to-end borrowing request lifecycle from initial submission to assessment generation, addressing all structural and protocol requirements:
1. **The Primary Success Path:** Request submission $\rightarrow$ Soft date hold (ADR-0001) $\rightarrow$ Locality check against the member's stored coarse result (A11; the request itself carries no location) $\rightarrow$ Trust & assurance evaluation $\rightarrow$ Immutable event append with `config_version` $\rightarrow$ Asynchronous lender notification $\rightarrow$ Immediate response to borrower.
2. **Alternative Fragment 1 (Engine Timeout / Fault - FR-T-07):** Injected engine timeout (> 2000ms) or runtime exception triggering cancellation of the engine call, immediate transition to `HELD_FOR_REVIEW` with hold reason `engine_failure`, and urgent moderator alert. **Crucial Invariant:** **No default assurance state is assigned.**
3. **Alternative Fragment 2 (High Manipulation Risk / High-Value Hold - FR-T-06, ADR-0003, ADR-0007):** Engine detects corroborated collusion (Level 4, rule R2, ES-04) or high-value dissimilarity (rule R4, N-7, ES-06), so the result carries a hold reason $\rightarrow$ transition to `HELD_FOR_REVIEW` with hold reason `manipulation_risk` or `high_value_low_confidence`.
4. **Alternative Fragment 3 (Inconclusive / Conflicting Locality - UC-B5 ext 4a/4b):** The stored locality result is inconclusive, conflicting or expired $\rightarrow$ transition to `HELD_FOR_REVIEW` with hold reason `locality_inconclusive` or `locality_conflict`.
5. **Formal UML Correctness:**
   - **Activation Bars:** Balanced activation (`+`) and deactivation (`-`) across all paths to prevent hung lifeline leaks.
   - **Asynchronous Decoupling:** Notifications to external parties are non-blocking fire-and-forget dispatches (`-)`).
   - **Tier Separation:** Controller returns domain responses (`SubmissionResult`), which the API Gateway translates to HTTP 201/202 at the transport edge.

---

## 2. Sequence Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor Borrower as Borrower
    participant API as Borrowing Controller<br/>(Application Service)
    participant Locality as Locality Service<br/>(Privacy Boundary)
    participant Engine as Trust Engine<br/>(Module 5)
    participant Store as Event Store<br/>(PostgreSQL Stream)
    participant Notif as Notification<br/>Service (G3)
    actor Lender as Lender
    actor Moderator as Community<br/>Moderator

    %% Step 1: Request Submission
    Borrower->>+API: submitBorrowRequest(itemId, dates, message)
    Note over Borrower,API: ADR-0001: Soft hold on dates (marks 'requested', competing requests not blocked)

    %% Step 2: Request Created Event (no location anywhere in the request)
    API->>Store: appendEvent(streamId, 'request_created', REQUEST_CREATED)
    Store-->>API: ack(stream_seq=1)

    %% Step 3: Locality Verification (Privacy Barrier)
    API->>+Locality: outcomeFor(borrowerId, communityId)
    Note over Locality: A11 / FR-A-07 / NFR-PR-01: reads the stored coarse result of the<br/>member's verification (geofence + invitation, done once at joining).<br/>No coordinates are sent, read or stored here.
    Locality-->>-API: VERIFIED | INCONCLUSIVE | CONFLICTING

    %% Alt: Locality Inconclusive or Conflicting
    alt Locality Inconclusive or Conflicting (UC-B5 ext 4a, 4b / ES-09, ES-10)
        API->>Store: appendEvent(streamId, 'held_for_review', HELD_FOR_REVIEW,<br/>reason='locality_inconclusive' | 'locality_conflict')
        Store-->>API: ack(stream_seq=2)
        API-)Notif: enqueueModeratorAlert(communityId, caseType='locality_hold')
        Notif-)Moderator: Push Alert: Locality Verification Hold
        API-->>-Borrower: SubmissionResult(status=HELD_FOR_REVIEW, reason='locality_inconclusive')

    else Locality Verified (Normal Flow)
        API->>Store: appendEvent(streamId, 'locality_checked', LOCALITY_CHECKED)
        Store-->>API: ack(stream_seq=2)

        %% Step 4: Assessment Invocation
        API->>+Engine: assess(request, config_version="1.1.0-iteration1-draft")
        Note over Engine: Module 5 Pipeline (Algs 1–4):<br/>1. Direct Beta Posterior<br/>2. Bounded k-Hop Indirect Trust<br/>3. Manipulation Risk Scoring<br/>4. Decision Policy & Safeguards

        %% Alt: Engine Timeout / Fault Branch (FR-T-07)
        alt Engine Timeout (> 2000ms) or Runtime Fault (FR-T-07 / ext 5d)
            Note over API,Engine: Timer expires (> 2000ms). Engine call cancelled / aborted.
            Engine-->>-API: [Timeout / Fault Exception]
            API->>Store: appendEvent(streamId, 'held_for_review', HELD_FOR_REVIEW,<br/>reason='engine_failure', failure_log_ref)
            Store-->>API: ack(stream_seq=3)
            API-)Notif: enqueueModeratorAlert(communityId, caseType='engine_failure', priority=HIGH)
            Notif-)Moderator: High Priority Alert: Engine Failure Escalation Case
            API-->>-Borrower: SubmissionResult(status=HELD_FOR_REVIEW, reason='engine_failure')

        %% Alt: High Manipulation Risk / High Value Weak Evidence (FR-T-06, ADR-0003)
        else Result has a hold reason (rule R2 / ES-04, rule R4 / ES-06)
            Engine-->>-API: AssuranceResult(state=REVIEW_RECOMMENDED, rule=R2|R4,<br/>hold_reason='manipulation_risk' | 'high_value_low_confidence')
            API->>Store: appendEvent(streamId, 'held_for_review', HELD_FOR_REVIEW,<br/>reason, assuranceResult, config_version)
            Store-->>API: ack(stream_seq=3)
            API-)Notif: enqueueEscalationCase(communityId, escalationCase, evidenceTrail)
            Notif-)Moderator: Push Case: Escalation Queue (UC-D6)
            API-->>-Borrower: SubmissionResult(status=HELD_FOR_REVIEW, reason=hold_reason)

        %% Primary Success Flow
        else No hold reason (R1, R3, R5 to R9 / ES-01, ES-02, ES-03, ES-05, ES-13)
            Engine-->>-API: AssuranceResult(decision, state, safeguards, explanation, hold_reason=none)
            
            %% Step 5: Append Assessment Generated Event
            API->>Store: appendEvent(streamId, 'assessment_generated', ASSESSED,<br/>assuranceResult, config_version="1.1.0-iteration1-draft")
            Note over API,Store: NFR-D-01 / FR-B-09: 100% of stored assessments record config_version
            Store-->>API: ack(stream_seq=3)

            %% Step 6: Asynchronous Notify Lender & Immediate Borrower Response
            API-)Notif: enqueueLenderNotification(lenderId, requestId, factorSummary, safeguards)
            Notif-)Lender: Push Notification: New Borrowing Request (UC-B6)
            API-->>-Borrower: SubmissionResult(status=REQUEST_SENT, requestId, safeguards)
        end
    end
```

---

## 3. Message Sequence & Contract Specifications

### Message 1: `submitBorrowRequest`
- **Sender:** `Borrower` $\rightarrow$ **Receiver:** `Borrowing Controller`
- **Payload:** `{ itemId: "item_drill_01", startDate: "2026-10-15", endDate: "2026-10-18", message: "Need for shelf installation" }`. No location of any kind: the borrower's locality was verified once, when joining the community (UC-A3, A11).
- **Semantics:** Creates the transaction; its UUID is the event `stream_id`. Applies **ADR-0001 soft hold** (dates marked requested; competing pending requests are not blocked until acceptance under ADR-0002).

### Message 2: `appendEvent('request_created')`
- **Sender:** `Borrowing Controller` $\rightarrow$ **Receiver:** `Event Store`
- **Privacy Invariant:** **Zero location data is stored.** The event has the frozen fields (FR-B-09) and nothing else:
  `{ stream_id: "<transaction uuid>", stream_seq: 1, event_type: "request_created", schema_version: 1, actor_id: "<borrower uuid>", occurred_at: <server time>, previous_state: null, new_state: "REQUEST_CREATED", evidence_refs: {}, authorisation: "party:borrower", payload: { item_id: "<item uuid>", requested_period: "[2026-10-15, 2026-10-18)" } }`.

### Message 4: `outcomeFor`
- **Sender:** `Borrowing Controller` $\rightarrow$ **Receiver:** `Locality Service` (`ILocality`, Module 1)
- **Privacy Boundary (A11 / FR-A-07 / NFR-PR-01):** The device location is read once, in memory, when the member joins a community (UC-A3); only the coarse outcome is stored (`locality_verification`). At request time the service reads that stored outcome and its validity date: `VERIFIED` | `INCONCLUSIVE` (also when expired) | `CONFLICTING`. No coordinates exist anywhere in this sequence.

### Message 9: `assess(transactionContext, config_version)`
- **Sender:** `Borrowing Controller` $\rightarrow$ **Receiver:** `Trust Engine`
- **Payload:** `{ requester_id, target_id, item_value: 4500, category: "TOOLS", duration_days: 3, value_band: "LOW", role: "borrower", metric: "ON_TIME_RETURN", config_version: "1.1.0-iteration1-draft" }` (4,500 PKR is LOW: ≤ 5,000 in the config).
- **Execution:** Runs the 4 modular algorithms:
  1. Recency-weighted Beta Posterior (Algorithm 1)
  2. Bounded $k$-Hop Graph Traversal (Algorithm 2)
  3. Manipulation Risk Scoring & Retaliation Check (Algorithm 3)
  4. Context-Aware Decision Policy (Algorithm 4)

### Message 10–14: Alternative Branches & Architectural Rules

1. **Engine Timeout / Fault (FR-T-07):**
   - The Controller maintains an internal timer (`engine_timeout_ms = 2000`).
   - If expired, the controller cancels the engine context, records an `engine_failure` log, and appends `held_for_review` with `reason = "engine_failure"`.
   - **Non-Negotiable Invariant:** **No default assurance state is assigned.**
   - Enqueues high-priority alert to Community Moderator queue. Deactivates both engine and controller lifelines.
2. **High Risk / High Value Escalation (FR-T-06, ADR-0003, Issue N-7):**
   - If the result has a hold reason (rule R2: corroborated manipulation level 4, ADR-0007; or rule R4: high value with weak evidence):
   - Transitions request to `HELD_FOR_REVIEW` with recorded reason (`manipulation_risk` or `high_value_low_confidence`).
   - Enqueues full evidence trail to moderator queue (UC-D6). No automatic ban/restriction takes effect without human approval.
3. **Primary Success Flow (Normal Assessment):**
   - If there is no hold reason (including R1, an open dispute: the lender sees ACTIVE_DISPUTE, decision D12): Appends `assessment_generated` with `new_state = "ASSESSED"` and `config_version`.
   - Dispatches asynchronous non-blocking notification to Lender (`API-)Notif`).
   - Immediately returns domain success `SubmissionResult(status: REQUEST_SENT)` to Borrower.

---

## 4. Diagram source and notation

- **File:** `sequence_a_request_to_assessment.drawio`, generated by `generate_sequence_a.py` (layout-checked; do not edit
  by hand). The hand-drawn v1.1 drawing is kept in `archive_v1/`.
- **Lifelines** (component diagram, A8): Borrower (actor) · `:BorrowingService` (M3, the "Borrowing Controller" above) ·
  `:LocalityChecker «ILocality»` (M1, the "Locality Service") · `:AssuranceFacade «IAssess»` (M5, the "Trust Engine") ·
  `:EventStore` (M3) · `:Notifier «stub»` (M7, the "Notification Service") · Lender and Moderator (actors).
- **UML 2.5 notation:** solid line with filled head = synchronous call; dashed line with open head = reply; solid line
  with open head = asynchronous message; white bar = activation; `alt` frame = alternatives (one guard per operand,
  exactly one runs), nested for the engine outcomes inside the `[else: outcome = VERIFIED]` operand.
