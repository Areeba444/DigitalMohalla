# Digital Mohalla: Architecture (design step A8)

| Field | Value |
|---|---|
| Document | Design step A8: component diagram, layer diagram, interface operations, REST endpoint table |
| Owner | Student 1 |
| Version | 1.2, 11 October 2026 (notation review: the layer diagram is a UML package diagram with «layer» packages and «use» dependencies; PostgreSQL is an external «component»). v1.1: baseline v1.3, `assess()` result fields, deployment in `04_deployment/` |
| Status | Draft for review (A14). Stack confirmation is the D-15 design gate. |
| Baseline | Iteration 1 plan (scope table, module roadmap, work division), Overview (ten modules), Use Cases v1.3, FR/NFR v1.3, ADR-0001 to ADR-0008 |
| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |

## Files

| File | What it is |
|---|---|
| `component_diagram.drawio` | UML component diagram: the ten modules; 1, 3, 5, 9, 10 in detail; provided (ball) and required (dependency) interfaces |
| `layer_diagram.drawio` | Layers (presentation, API, application, domain, infrastructure, platform) and cross-cutting concerns |
| `generate_architecture.py` | Regenerates both |

## 1. Design reasoning

- **One backend service, modules as packages.** Three students, one deployed environment and a mid-evaluation in about three weeks: a modular monolith (one FastAPI process, one PostgreSQL database, proposal §8.1) gives clear ownership without network boundaries to test and deploy. Module boundaries are the interfaces below, so a module can be split out later.
- **The engine behind one call.** Module 3 sees Module 5 only through `IAssess.assess(request) → AssessmentResult` (plan, A8). This is the Student 1 / Student 2 boundary: Slice A uses a stub that always returns INSUFFICIENT_EVIDENCE; Slice B swaps in the real engine without touching the lifecycle. Inside Module 5, Student 1's indirect-trust part is reached through `IIndirectEvidence`.
- **Lifecycle writes, others ask.** Only Module 3 appends lifecycle events. Module 9 decides and calls `ILifecycleCommands`; the scheduler (iteration 2) will do the same. One writer means one place where the transition table is enforced (FR-B-08), matching the database design.
- **Evidence flows one way.** Closing events (`transaction_closed`, `dispute_resolved`) are pushed to `IOutcomeSink` after commit; outcomes and trust edges are derived, idempotent and rebuildable from the event log, so an engine outage never blocks a loan from closing.
- **Location never crosses the boundary.** `ILocality` returns only verified / inconclusive / conflicting; the privacy filter in the API layer strips address, coordinate and CNIC fields from every response (NFR-PR-01).
- **Deferred modules are drawn, not detailed.** Modules 2, 4, 6 and 8 are outside iteration 1 (plan scope table); Module 7 is a stub interface so callers are written once.

## 2. Components and owners

| Module | Components (iteration 1) | Owner | Built in iteration 1 |
|---|---|---|---|
| 1 Accounts & communities | AuthService, MembershipDirectory, LocalityVerifier | S1 | Login with seeded users; membership seeded; locality method = geofence + invitation (A11), a stub until the D-11 gate decides the build |
| 3 Borrowing lifecycle | BorrowingService, TransitionValidator, EventStore, Projector & Replay, BookingGuard, OutcomePublisher | S1 | Yes (Slice A) |
| 5 Assurance engine | AssuranceFacade, OutcomeExtractor, BetaPosteriorEstimator, ManipulationDetector, DecisionPolicy & ExplanationBuilder, ConfigLoader (S2); IndirectTrust (S1) | S2 + S1 | Yes (Slices B, C) |
| 7 Communication & notifications | notify() stub | shared | Stub only |
| 9 Administration & moderation | CaseService, EvidenceTrailBuilder, DecisionService, AuditLogService | S3 | Yes (Slice C); appeal and reversal in iteration 2 |
| 10 Analytics & evaluation | ScenarioSuite (ES-01 to ES-06, ES-13) | S3 | Yes, in CI |
| 2, 4, 6, 8 | Events, search & matching, forum & chatbot, vendors | — | No |

## 3. Interfaces

| Interface | Provider → users | Operations | FRs |
|---|---|---|---|
| IRestApi | REST API → clients | endpoints of section 4 | all core |
| IAuth | M1 → API | `login(identifier, password) → Session`, `current_actor(token) → Actor` | FR-A-04 (part), NFR-S-01 |
| IMembership | M1 → M3 | `is_member(user, community)`, `is_moderator_of(user, community)` | FR-A-09, NFR-S-03 |
| ILocality | M1 → M3 | `outcome_for(user, community) → VERIFIED \| INCONCLUSIVE \| CONFLICTING` | FR-B-07, FR-A-08 |
| IBorrowingCommands | M3 → API | `create_request`, `accept`, `decline`, `cancel`, `record_handover_checklist`, `confirm_handover`, `initiate_return`, `confirm_return`, `open_dispute`, `withdraw_dispute`, `get_request` | FR-B-05 to FR-B-17 |
| ILifecycleCommands | M3 → M9 | `apply_decision(transaction_id, decision) → event` (appends `hold_cleared`, `request_declined` or `dispute_resolved`) | FR-T-11, ADR-0003, ADR-0004 |
| IEventQuery | M3 → M9 | `load_stream(id) → events`, `replay(id) → state`, `verify_chain(id)` | FR-B-09, FR-M-05, UC-D6 |
| IAssess | M5 → M3, M10 | `assess(request: AssessmentRequest) → AssessmentResult` (assurance state, policy decision, rule fired, hold reason, confidence, direct and indirect evidence, manipulation signals, safeguards, explanation, `config_version`); raises Timeout → `engine_failure` hold | FR-T-01 to FR-T-07 |
| IIndirectEvidence | M5 (S1 part) → AssuranceFacade | `indirect_evidence(lender, borrower, role, metric, t_v, b) → IndirectEvidence` | FR-T-04 |
| IOutcomeSink | M5 → M3 | `record_outcome(closing_event_id)` (idempotent); missed deliveries are found through the view `v_pending_outcomes` and retried | FR-B-15, FR-T-03, NFR-R-04 |
| ICaseIntake | M9 → M3 | `open_or_attach(transaction_id, trigger, reason)`; in iteration 1 realised inside the same DB transaction as the hold / dispute event | FR-T-10, UC-D6 1b |
| IModeration | M9 → API | case queue, case detail with evidence trail, `request_information`, `record_decision`, audit-log query | FR-T-11, FR-M-05 |
| INotify | M7 → M3, M9 | `notify(user, type, payload)` | FR-C-02 (stub) |

## 4. REST endpoints (iteration 1)

All under `/api/v1`, JSON over HTTPS. Errors: 401 not logged in, 403 not allowed (NFR-S-02), 404, 409 invalid transition / stale `stream_seq` / dates taken / guard failed, 422 invalid input. Every state-changing call is one command → at most one lifecycle event.

| Method and path | Actor | Use-case step | Lifecycle effect | FRs |
|---|---|---|---|---|
| `POST /auth/login`, `POST /auth/logout` | Member | A2 | — | FR-A-04 (part) |
| `GET /items/{id}` | Borrower | B5 step 1 | — (shows deposit, terms, booked periods) | FR-B-06 |
| `POST /requests` | Borrower | B5 steps 2–6 | `request_created` → locality → `assessment_generated` or `held_for_review`; returns ASSESSED or HELD_FOR_REVIEW | FR-B-05 to FR-B-07 |
| `GET /requests/{id}` | Borrower, Lender | B5 step 6; B6 step 2 | — (assurance state with evidence, never one number) | FR-T-01, FR-T-08, NFR-U-01 |
| `GET /lender/requests?state=ASSESSED` | Lender | B6 step 1 | — | FR-B-10 |
| `POST /requests/{id}/accept` | Lender | B6 steps 3–6 | `request_accepted` (T13), then `request_declined` dates_taken for overlaps (T17); 409 if the constraint refuses | FR-B-05, FR-B-10 |
| `POST /requests/{id}/decline` | Lender | B6 ext 3a | `request_declined` (T14) | FR-B-10 |
| `POST /requests/{id}/cancel` | Borrower | B6 ext *a | `request_cancelled` (T16) | FR-B-10 |
| `POST /transactions/{id}/handover/checklist` | Lender | B7 steps 1–2 | condition report; `handover_confirmed` if the borrower already confirmed | FR-B-11 |
| `POST /transactions/{id}/handover/confirm` | Borrower | B7 steps 3–4 | `handover_confirmed` (T18) when both confirm | FR-B-11 |
| `POST /transactions/{id}/return` | Borrower | B8 step 1 | `return_initiated` (T20) | FR-B-13 |
| `POST /transactions/{id}/return/confirm` | Lender, Borrower | B8 steps 2–5 | condition report; `return_confirmed` + `transaction_closed` (T21, T22) when both agree | FR-B-13, FR-B-15 |
| `POST /transactions/{id}/attachments` | Party | B7 step 2, B8 step 2, B12 step 3 | — (photos optional in iteration 1; metadata stripped) | FR-B-11, NFR-PR-01 |
| `POST /transactions/{id}/disputes` | Party | B12 steps 1–5 | `dispute_opened` (T23; not from RETURNED), case opened | FR-B-16 |
| `POST /transactions/{id}/disputes/withdraw` | Raising party | B12 ext 5b | `dispute_withdrawn` (T26) | FR-B-17 |
| `GET /transactions/{id}/events` | Party, Moderator, Admin | I6 step 3; replay demo | — (stream with `stream_seq`) | FR-B-09 |
| `GET /cases?status=OPEN` | Moderator, Admin | D6 step 3; I4 step 1 | — | FR-T-10 |
| `GET /cases/{id}` | Moderator, Admin | I4 step 1 | — (evidence trail from the event log) | FR-T-10 |
| `POST /cases/{id}/information-requests` | Moderator | I4 step 2 | case C02 | FR-T-11 |
| `POST /cases/{id}/statements` | Party | B12 step 5; I4 step 2 | case C03 | FR-B-17 |
| `POST /cases/{id}/decision` | Moderator, Admin | I4 steps 3–4 | `hold_cleared` (T09–T11), `request_declined` (T12) or `dispute_resolved` (T25); case C06 | FR-T-11 |
| `GET /audit-log?actor=&transaction=&from=&to=&type=` | Admin | I6 steps 1–2 | — (the view itself is logged) | FR-M-05 |
| `GET /audit-log/{entry_id}` | Admin | I6 step 3 | — (sensitive fields masked) | FR-M-05 |
| `GET /health` | CD pipeline | plan CD step 3 | — | NFR-D-04 |

Iteration 2 adds extension endpoints (I03–I05), scheduler-driven expiry and no-show, appeals (C08–C10) and membership requests (A3/A4).

## 5. Layer rules

Presentation → API → application → domain → infrastructure → platform; each layer calls only the one below. The domain layer (transition table, aggregate and replay, engine mathematics, case model) does no I/O, so it is unit-tested without a database (test suites 1, 6, 7, 9). Repository interfaces live in the application layer and are implemented in infrastructure (dependency inversion), which is how the stub engine and the stub locality checker are swapped for the real ones.

## 6. Open points

| # | Point | Note |
|---|---|---|
| AR-1 | Frontend and backend stack | Proposal §8.1 names Python, FastAPI, PostgreSQL; the client stack (NFR-D-05 assumes React Native / Expo) is decided at D-15 |
| AR-2 | Deployment target | Proposed in `04_deployment/Deployment_Design.md` (decision D17): one AWS EC2 host, Docker Compose, GHCR, CD over SSH; instance size, region and domain to be confirmed by D-14 (Student 3) |
| AR-3 | `ICaseIntake` realised by a database trigger in iteration 1 | Keeps hold and case atomic; Student 3 to confirm, since Module 9 owns the case |
| AR-4 | Notifications | Stub in iteration 1; in-app notifications in iteration 2 (roadmap) |
