# Sequence diagrams (g) and (h): information requests, appeal and reversal (DA-12)

| Field | Value |
|---|---|
| Owner / reviewer | Student 3 (Minahil Kashif) / Student 1 (Fatima Khursheed) |
| Version | 1.0, 7 November 2026 (draft for review) |
| Scope | UC-I4 step 2 and extensions 2a, 4b, 4c; UC-B12 / FR-B-17 (party response); FR-T-11; escalation-case transitions C02 to C04 and C08 to C11 |
| Files | `sequence_g_information_request.drawio`, `generate_sequence_g.py`; `sequence_h_appeal_reversal.drawio`, `generate_sequence_h.py`; shared helpers `seqlib.py` |
| Author note | Drafted with Claude Code (GenAI); disclosed in the AI usage log. |

## Sequence (g): information request, party response and deadline

**What it shows.** A moderator asks a party for more information (C02); the case moves to AWAITING_INFORMATION with a deadline. Either the party answers with a statement, and optional photos once uploads exist (C03), or the scheduler finds the deadline passed and reopens the case with a "no response" note (C04). In both branches the case is OPEN again and the moderator decides on the evidence available (UC-I4 2a).

**Rationale.** The deadline is enforced by the scheduler's `run_due_jobs(now)` (ADR-0012), not by an in-process timer, because the free hosting tier sleeps; the job selects due cases with `FOR UPDATE SKIP LOCKED` and notifies with a dedupe key, so a rerun changes nothing (NFR-R-05). A non-response is recorded as a fact for the moderator, never as an automatic loss, which keeps the "no restriction without human review" rule. Statements are append-only in `case_statement`, so the evidence trail cannot be rewritten.

**Realises:** FR-T-11 (information requests), FR-B-17 (response with evidence, "no response" passes to a moderator), NFR-R-05, NFR-S-02, NFR-S-03.
**Maps to code (M2 in the plan):** a new module under `backend/app/domain/moderation/` (the plan keeps new commands out of `service.py`); tables `escalation_case` (`status`, `info_deadline`) and `case_statement`; the scheduler runner (F4); the notifier (A2).

## Sequence (h): appeal, second moderator, reversal and flagged evidence

**What it shows.** A party appeals a decided case within the appeal window (C08). A second moderator, never the first decider, upholds (C09, `APPEAL_UPHELD`) or overturns (C10, `APPEAL_OVERTURNED`) it. Later, an authorised moderator or admin can reverse a decision (C11, `REVERSAL`). An overturn or reversal flags the outcomes that came from the overturned decision as `FLAGGED_FOR_REEVALUATION` and refreshes both parties' trust edges.

**Rationale.** A reversal does not rewind the loan: COMPLETED, DECLINED and NO_SHOW are final lifecycle states, and rewriting history would break the append-only event log. It corrects the evidence instead. This needs no engine change: the estimator already skips flagged outcomes (`estimation/posterior.py`) and trust edges are rebuilt only from VALID outcomes (`indirect/edges.py`), so the next assessment of either party changes, which is the ES-11 scenario. Both decisions stay in `moderator_decision`, and the database already requires `reverses_decision_id` for `REVERSAL` and `APPEAL_OVERTURNED` (`decision_reversal_ck`).

**Realises:** FR-T-11 (appeal, reversal), FR-A-11 pattern for cases, ES-11, NFR-S-03.
**Maps to code (M3 in the plan):** `domain/moderation/decisions.py` (`plan()` gains the appeal and reversal kinds); the outcome writer in `infra/db/outcomes.py` (`flagged_by_decision_id`); the trust-edge refresh in `infra/db/trust_edges.py`.

## Open points

| Point | Proposed handling | Settled in |
|---|---|---|
| Where the moderator's question is stored | `case_statement.author_role` allows only BORROWER or LENDER, so a moderator-authored record needs a schema change (for example a MODERATOR role or an `information_request` row) | DA-09, schema v2.4 (Fatima) |
| Response window and appeal window | Values in the configuration, not in code | DA-03 (FR/NFR v1.4) |
| Endpoint paths | Drawn as proposals | DA-10 REST table (Fatima) |
| Which outcomes an overturn flags | All outcomes whose source is the overturned decision's `dispute_resolved` event; a hold decision produces no outcome | M3 build, test suite 26 |
| Restoring a flagged outcome after re-evaluation | A later moderator action | FYP-2 |
