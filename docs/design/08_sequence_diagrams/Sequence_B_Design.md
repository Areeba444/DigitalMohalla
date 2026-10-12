# Sequence diagram (b): confirm handover and return to evidence (design step A9 b)

| Field | Value |
|---|---|
| Owner | Student 1 |
| Version | 1.0, 11 October 2026 |
| Scope | UC-B7 (FR-B-11, FR-B-12) and UC-B8 (FR-B-13, FR-B-15), from dual confirmation to evidence |
| Files | `sequence_b_handover_return.drawio`, `generate_sequence_b.py` |
| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |

**What it shows.** Lifelines are the components of the component diagram (REST API, BorrowingService, TransitionValidator, EventStore, AssuranceEngine through `IOutcomeSink`, TrustEdgeProjector, Notifier stub). Messages use the REST endpoints of `Architecture_Design.md` §4 and the event types and transition IDs of the A3 table.

**Design reasoning.**
- Each party's confirmation is stored first (`condition_report`); the lender's checklist comes first and the borrower's confirmation counts only if made after it; the transition (T18, T21) is appended when the pair is complete, so neither party can move the loan alone.
- `return_confirmed` and `transaction_closed` are appended in one database transaction (UC-B8 steps 3–4); the trigger checks on-time versus late against `due_at` and releases the booking.
- The outcome reaches the engine after commit through `record_outcome(closing_event_id)`. The call is idempotent (unique source event, subject and metric), so a retry never double-counts, and an engine outage never blocks the loan from closing (NFR-R-04). Closings whose outcomes were never recorded are listed by the view `v_pending_outcomes`, which a catch-up job retries. Only confirmed outcomes are recorded; a disagreement goes to a dispute and is counted only after `dispute_resolved` (FR-T-03, ES-07).
- The two `alt` fragments carry the failure paths a demo should show: deposit not recorded (UC-B7 3b, stays ACCEPTED) and condition disagreement (UC-B8 3a, DISPUTED, continued in Student 3's sequence (c)).

**Traceability.** Messages 1–19: UC-B7 steps 1–4, ext 3a, 3b; T18. Messages 20–46: UC-B8 steps 1–5, ext 3a; T20–T23; FR-B-15 (outcome, calendar release, deposit release record). Trust-edge weights follow ADR-0006 (awaiting Student 2).
