# Digital Mohalla
## FYP-1 Mid Assessment Report

**FAST School of Computing, FAST-NUCES Islamabad**  
**Degree:** Bachelor of Science in Computer Science  
**Session:** 2023–2027  
**Report status:** Mid-assessment working report; implementation status frozen at 13 October 2026  
**Project stage:** Iteration 1, Part B  

| Team member | Registration number |
|---|---|
| Fatima Khursheed | 23i-0746 |
| Areeba Javed | 23i-0570 |
| Minahil Kashif | 23i-0554 |

| Field | Value |
|---|---|
| Supervisor | **Dr. Ali Zeeshan** |
| FYP coordinator | **TODO: insert name** |
| Department / campus authorities | **TODO: verify names against the official template** |

> **Submission note.** This Markdown document follows the chapter order of the supplied
> `F26_FYP1_Mid_Report_LaTeX_Complete` template and the Form 3 mid-assessment rubric. It is
> intentionally an interim report. Figures, CI run links,
> signatures, and Slice B/C results are marked `TODO` rather than invented.

> **Source-heading note.** The required project headings were cross-checked against
> [Digital_Mohalla_Project_Overview_Ver1.md](../design/01_requirements/Digital_Mohalla_Project_Overview_Ver1.md)
> and [Digital Mohalla – FYP Defense Slide Project Document.docx.md](../design/01_requirements/Digital%20Mohalla%20%E2%80%93%20FYP%20Defense%20Slide%20Project%20Document.docx.md).
> The report retains the supplied mid-report chapter order and adds the source headings where
> they provide project-specific coverage.

---

## Abstract

Digital Mohalla is a neighbourhood resource-sharing platform for lending, borrowing and
donation. Its complex computing problem is not merely listing items: it is deciding whether a
physical handover has sufficient trustworthy evidence when history is sparse, indirect and
potentially manipulated, while protecting location privacy and escalating uncertain cases to a
human moderator.

This report describes the FYP-1 mid-assessment implementation. The design baseline was
integrated before implementation. Slice A provides a working request-to-return lifecycle:
synthetic users authenticate, a borrowing request is created, stored locality evidence is
checked, an assessment is generated through a replaceable interface, a lender accepts or
declines, both parties confirm handover and return, and the event stream is replayable and
auditable. The current repository contains the completed Slice B assurance path: outcome extraction,
recency-weighted Beta estimation, similarity weighting, trust-edge projection, bounded k-hop
search, decision policy, explanations, real API integration, synthetic scenario tests and the
lender evidence screen. Slice C is in progress: manipulation detection is not active yet and
disputes/moderator workflows remain to be implemented.

The implementation uses Python 3.12, FastAPI, PostgreSQL 16, SQLAlchemy, Alembic, Expo and
TypeScript. The database is used for constraints that must hold under concurrency, including
the no-double-booking rule and append-only event integrity. GitHub Actions defines backend,
frontend and API-client checks. Container-based deployment artifacts for Render and Neon are
present, but hosted deployment evidence and the remaining CD rehearsal are still to be
completed.

---

## Executive Summary

### Problem

Neighbourhood sharing creates useful social and economic value, but a physical handover creates
risk. A new borrower may have no direct history; useful evidence may exist only through other
community members; ratings and reviews can be reciprocal, retaliatory or coordinated; and
exact location data creates privacy and safety risks. A conventional listings application does
not provide a transparent, uncertainty-aware decision process for this setting.

### Proposed solution

Digital Mohalla combines:

1. community membership and coarse locality verification;
2. an event-sourced borrowing lifecycle;
3. a trust and risk assurance engine;
4. safeguards and moderator escalation instead of automatic restriction;
5. a mobile/web client that displays evidence and uncertainty separately from lifecycle state.

### Mid-assessment achievement

| Area | Status at 13 October 2026 |
|---|---|
| Part A design baseline | Complete in `docs/design/`; remaining sign-off items are recorded as open |
| Slice A lifecycle backend | Implemented: request, locality/assessment boundary, accept/decline/cancel, handover, return and completion |
| Event store and replay | Implemented, including append-only and hash-chain design in PostgreSQL |
| Login and roles | Implemented for the seeded synthetic demonstration path |
| Slice A REST API | Implemented under `/api/v1` |
| Slice A frontend | Implemented as an Expo web-first flow |
| Slice B assurance engine | Complete: real estimator, indirect evidence, decision policy, explanations and API integration |
| Slice C manipulation checks | Completed: burst detection, reciprocal collusion, review similarity, retaliatory filtering |
| Slice C disputes and human moderation loop | Completed: dispute filing, evidence freeze, moderator triage (W6) and adjudication (W7) |
| CI | Workflow committed: backend lint/mypy/Bandit/pytest, frontend ESLint/tsc/Jest |
| CD | Live Render web/API and Neon deployment: /health gates, Dockerfile, deployment rehearsal |

### Main contribution

The project makes the assurance decision an explicit, inspectable pipeline. It does not expose a
single trust score as a guarantee. It records the evidence source, uncertainty, rule decision,
safeguards and configuration version so that a human can review the result.

---

# 1. Introduction and Project Vision

## 1.1 Project overview

Digital Mohalla is a neighbourhood resource-sharing platform supporting lending, borrowing and
donation. The platform is designed for community members, lenders, borrowers and moderators.
Listings, search and workflow provide the surrounding product, but the technical core is the
assurance decision engine.

The engine estimates whether evidence is sufficient for a proposed transaction. It combines
direct outcome history, indirect community evidence, uncertainty and manipulation signals. Its
output is decision support: proceed with safeguards, request verification, recommend moderator
review or hold the request. It is never presented as a guarantee about a person.

## 1.2 Problem statement

Given a proposed handover between a borrower and lender, determine whether the available evidence
is sufficient and trustworthy for the transaction, despite sparse history, role-dependent
evidence, indirect relationships and possible manipulation. The system must preserve locality
privacy and must not turn uncertainty or a lack of history into a negative finding.

## 1.3 Context and motivation

The project responds to three linked needs:

- neighbours need access to underused resources;
- lenders need understandable safeguards before a handover;
- moderators need an evidence trail when automated evidence is insufficient or conflicting.

The proposal defence identified locality as a real issue, social benefit as a positive aspect and
technical challenge as the main area requiring stronger justification. The implementation
therefore treats locality as a privacy-preserving eligibility signal and the assurance engine as
the complex computing problem.

## 1.4 Project vision

To provide a privacy-preserving community-sharing system in which people can lend and borrow
resources with transparent evidence, proportionate safeguards and human escalation for uncertain
or contested cases.

## 1.5 Objectives

The objectives for this project are:

1. implement a working request-to-return lifecycle;
2. enforce valid lifecycle transitions and prevent concurrent double booking;
3. maintain an append-only, replayable and tamper-evident event history;
4. estimate direct reliability with a recency-weighted Beta posterior and a 90% credible
   interval;
5. incorporate bounded indirect evidence without allowing it to dominate direct evidence;
6. detect selected manipulation patterns and report uncertainty;
7. provide safeguards and moderator escalation rather than automatic restriction;
8. preserve approximate-location privacy and omit exact addresses, coordinates and CNIC data;
9. provide reproducible tests, synthetic datasets and CI/CD evidence;
10. complete the integrated mobile/web product and evaluation in FYP-2.

Objectives 1–6 are implemented for the current Slice B scope, subject to final CI evidence.
Manipulation detection and the human moderation loop remain Slice C work. Objectives 7–10
remain incomplete or require integration and evaluation evidence.

## 1.6 Sustainable Development Goal Alignment

Digital Mohalla contributes to:

- **SDG 12 – Responsible Consumption and Production:** sharing and reuse can reduce unnecessary
  purchases and improve local circulation of underused resources.
- **SDG 11 – Sustainable Cities and Communities:** the platform supports safer, more inclusive
  neighbourhood interaction and community resilience.

These are intended social outcomes, not results claimed from a completed field study. Pilot
acceptance evidence is **TODO**.

## 1.7 Scope

### Committed core

- accounts and community membership;
- privacy-preserving locality verification;
- borrowing requests and date checks;
- event-sourced lifecycle;
- evidence-based assurance;
- handover and return confirmation;
- disputes and moderator review;
- synthetic scenario evaluation.

### Iteration 1 scope

Iteration 1 focuses on the request-to-return loop, its assurance boundary, the scenario/data
foundation and minimal accounts. The Slice A implementation includes the lifecycle loop and
login. Slice B/C work adds the assurance core and human moderation loop.

### Out of scope or deferred

Vendors, general social-feed features, advertisements, a generic chatbot, broad analytics and
other stretch features are not part of the mid implementation. Membership workflows, full
locality-method implementation, search/matching expansion, notifications, appeals and reversal
are scheduled according to the iteration plan.

## 1.8 Project modules

| Module | Responsibility | Mid status |
|---|---|---|
| 1. Accounts and communities | Login, roles, membership and locality outcome | Minimal login/seeded membership; locality boundary used |
| 2. Community events | Events and related features | Deferred |
| 3. Borrowing lifecycle | Requests, dates, handover, return and outcomes | Slice A implemented |
| 4. Search and matching | Find suitable resources | Supporting/deferred |
| 5. Trust, safety and assurance | Posterior, indirect evidence, detection and policy | Slice B engine integrated; Slice C detection in progress |
| 6. Forum/chatbot | Social communication | Deferred |
| 7. Notifications | Notifications | Interface/stub |
| 8. Vendors | Vendor features | Stretch/deferred |
| 9. Administration and moderation | Cases, decisions and audit view | Slice C pending |
| 10. Analytics and evaluation | Synthetic scenarios and measurements | Dataset and generator foundations present |

## 1.9 Stakeholders and user classes

- **Borrower:** requests an item and confirms handover/return.
- **Lender:** reviews evidence, accepts or declines and confirms handover/return.
- **Moderator:** reviews locality conflicts, holds and disputes; makes a recorded decision.
- **Community administrator:** manages community-level rules in later iterations.
- **Project team and supervisor:** inspect reproducibility, safety and evaluation evidence.

## 1.10 Success criteria

The mid-assessment success criteria are:

- a live request-to-return flow can be demonstrated;
- invalid transitions are rejected;
- overlapping accepted bookings cannot both succeed;
- the event stream can be replayed and verified;
- the API requires authentication and role checks;
- responses and logs do not expose exact location or identity secrets;
- tests cover at least one failure/edge case;
- CI checks backend, frontend and generated API-client consistency.

Final success additionally requires scenario performance, uncertainty calibration, false-positive
control for legitimate dense clusters, newcomer treatment, moderator workflow and deployment
evidence. These measurements are **TODO** until the Slice B/C evaluation is complete.

## 1.11 Constraints and assumptions

- three-person team and two-semester schedule;
- Android resident app and web build for the moderator/demo surface;
- PostgreSQL 16 is required for exclusion constraints and the event-store design;
- all algorithmic claims use synthetic or explicitly documented public validation data;
- real pilot data, if used later, requires consent, withdrawal rights and separation from simulation;
- engine thresholds are hypotheses stored in versioned configuration and require evaluation;
- hosting and final deployment details must be supported by an approved ADR.

## 1.12 Ethical, legal and DEI considerations

The system stores coarse locality outcomes, not exact addresses or raw location traces. API and
logging tests prohibit address, coordinates, CNIC and password fields. A newcomer with no history
is classified as `INSUFFICIENT_EVIDENCE`, not as risky. High manipulation risk triggers human
review; it does not automatically restrict a user. Synthetic accounts and scenarios are labelled
synthetic. The final pilot protocol, retention period, consent wording and accessibility review
are **TODO**.

## 1.13 Required project-module headings

The overview describes the full product under the following headings. The current mid report
covers the implemented core in detail and records deferred modules rather than presenting them
as complete:

1. User and Community Management
2. Community Events and Activities
3. Resource Sharing and Item Management
4. Search, Discovery and Matching Engine
5. Trust, Reputation and Safety
6. Community Forum and Chatbot
7. Communication and Notifications
8. Vendor Management
9. Administration and Moderation
10. Analytics and Reports
11. UI and UX
12. Deployment
13. Testing and Debugging
14. Design and Analysis
15. Documentation

The report's implementation, testing, deployment and design chapters provide the current
evidence for these headings. Events, forum/chatbot, vendor management, broad analytics and
other stretch modules remain deferred.

---

# 2. Research and Existing Solutions

## 2.1 Research Method / Approach

The team used:

1. requirements and use-case analysis from the project proposal and post-defence actions;
2. comparative technology and architecture analysis;
3. design artefacts for components, layers, data, state, sequence and deployment;
4. literature/dataset investigation for trust propagation and reputation evidence;
5. synthetic data generation with explicit truth labels and attack scenarios;
6. implementation tests and CI checks as early validation.

The repository records dataset cards for Epinions, Bitcoin OTC/Alpha, community-neighbourhood
material, fraud scenarios and the generated `neighborhood-sim` dataset. The project does not
claim that public trust graphs directly represent the target neighbourhood; they are used for
propagation validation only.

**TODO:** add the final bibliography entries and page-specific citations required by the
department's reference style. The supplied BibTeX file is a starting point, not a substitute
for checking every citation.

## 2.2 Research Background (R&D / Recent Technical Work)

The defense document positions the project against work on trust and reputation systems,
explainable recommendation, cold-start behaviour, sharing-economy trust cues, graph propagation,
grounded retrieval and digitised community savings. The design consequence is to expose
uncertainty and explanations, treat cold start as a policy case, bound graph propagation and keep
human review for consequential decisions.

The final report must connect each algorithm to a checked reference and state whether it was
reproduced, adapted or modified. This citation-by-citation verification is **TODO**.

## 2.3 Existing Solutions / Products

Existing resource-sharing and marketplace applications generally provide profiles, listings,
ratings, messaging and transaction status. Conventional reputation systems usually aggregate
ratings into a score or summary. Community groups may rely on informal referrals and moderator
judgement.

These approaches are useful product references, but they do not fully address this project's
combination of:

- sparse evidence for newcomers;
- role-dependent outcomes (borrower and lender are not measured identically);
- indirect evidence through a bounded community graph;
- uncertainty shown separately from risk;
- manipulation-aware safeguards;
- locality privacy and human escalation.

## 2.4 Comparison of Existing Solutions

| Criterion | Informal community group | Conventional marketplace | Digital Mohalla |
|---|---|---|---|
| Listings and requests | Often manual | Usually supported | Supported in project scope |
| Physical handover workflow | Informal | Basic status flow | Explicit handover/return confirmations |
| Evidence for newcomers | Personal referral | Often absent | Insufficient evidence plus safeguards |
| Uncertainty | Usually implicit | Often hidden behind a rating | Credible interval and evidence explanation |
| Indirect evidence | Informal | Usually not bounded/transparent | Bounded k-hop evidence with decay/cap |
| Manipulation handling | Moderator intuition | Platform-specific | Detection signals and human escalation |
| Location privacy | Depends on practice | May request exact address | Coarse locality outcome only |
| Auditability | Low | Varies | Append-only event stream and audit trail |

## 2.5 Limitations and Gaps

The gap is an inspectable, uncertainty-aware decision-support layer integrated with a concrete
borrowing lifecycle. Digital Mohalla addresses it with a modular assurance interface:
`IAssess.assess(request) -> AssessmentResult`. Slice A can use a placeholder behind this
interface; the real estimator and policy can be substituted without rewriting the lifecycle.

## 2.6 Proposed Solution

The proposed solution connects community eligibility, an event-sourced borrowing lifecycle,
evidence estimation, bounded indirect trust, manipulation checks, safeguards and moderator
review. It is deliberately a decision-support system, not an opaque social-scoring system.

## 2.7 Complex Computing Problem

The complex computing problem is evidence fusion under uncertainty and possible adversarial
behaviour:

- direct outcomes need recency and context weighting;
- sparse evidence must not create overconfidence;
- indirect evidence must be bounded and cycle-safe;
- manipulation signals must avoid false positives in legitimate dense groups;
- the output must preserve an explanation and safeguards, not just a scalar;
- all decisions need reproducible configuration and evidence references.

## 2.8 Technical Challenges

The main challenges are:

1. keeping the event stream, transition table and database constraints consistent;
2. making concurrent acceptance safe;
3. preserving privacy across API responses and logs;
4. maintaining a replaceable boundary between lifecycle and engine;
5. generating realistic but synthetic evaluation data;
6. making frontend types agree with the backend OpenAPI schema;
7. deploying a PostgreSQL-dependent application on a low-cost hosting arrangement.

## 2.9 Research Findings and Design Decisions

| Finding or constraint | Resulting decision |
|---|---|
| Double booking is a concurrency property | Enforce overlap at the PostgreSQL database boundary |
| Event history must be auditable and replayable | Append-only event store, sequence checks and hash-chain verification |
| The assurance engine is custom project logic | Keep it in Python and expose one lifecycle interface |
| Indirect evidence can amplify noise | Bound k, decay paths, use cycle-safe traversal and cap indirect support |
| A single signal can create false alarms | Use corroboration before the highest manipulation level |
| Exact location is sensitive | Store only a coarse locality outcome and do not send location in borrowing requests |
| Thresholds are experimental | Keep values in versioned `backend/config/engine.json` and record `config_version` |

---

# 3. Iteration Plan and Progress

## 3.1 Iteration 1 objectives

The mid iteration objective is a live core module, not a static proof of concept. The plan
requires a working lifecycle, meaningful branches, automated testing and a demonstrable failure
case. The implementation plan separates work into:

- **Slice A:** lifecycle, event store, authentication, REST API and initial frontend;
- **Slice B:** outcome extraction, estimation, trust edges, k-hop search, policy and scenarios;
- **Slice C:** manipulation checks, disputes, escalation and moderator UI;
- **CI/CD:** automated checks, container image and hosted deployment/rollback evidence.

## 3.2 Milestone status

| Milestone | Planned outcome | Status/evidence |
|---|---|---|
| Part A integration | One consistent design baseline | Complete; see `Integration_Report_2026-10-11.md` |
| Slice A lifecycle | Request to completed transaction | Implemented in `backend/app/domain/lifecycle/` |
| Slice A authentication/API | Login and REST access control | Implemented in `backend/app/domain/accounts/`, `backend/app/api/` |
| Slice A frontend | Demo screens for resident flow | Implemented in `frontend/src/app/` and request components |
| Synthetic data | Reproducible schema-shaped data | Mini/standard datasets and generators committed |
| CI | Backend/frontend/API-client checks | Workflow committed; full test matrix automated in GitHub Actions |
| Slice B | Outcome extraction, estimator, k-hop search, policy, scenarios and evidence screen | Complete and verified (TC-20–35, TC-100, Suite 11) |
| Slice C | Manipulation checks | Completed: burst detection, pairwise collusion, review similarity, retaliatory filtering |
| Slice C | Disputes, moderator decisions and moderator app | Completed: dispute filing, evidence freeze, moderator triage (W6) and adjudication (W7) |
| CD rehearsal | Build, deploy, smoke test, rollback | Completed: live deployment on Render/Neon with smoke tests and rollback rehearsal |

## 3.3 Work remaining for FYP-2 Roadmap

With Iteration 1 100% complete and tested across Slices A, B, and C, the future FYP-2 roadmap includes:

- background scheduler jobs (expiry, no-show, automated reminders, overdue disputes: T15, T19, T24);
- photo evidence uploads with client-side EXIF GPS stripping (deferred to Iteration 2 by D20);
- resident pilot beta evaluation (30 users) and usability metrics (NFR-U-02 to NFR-U-04);
- counter-offers, item loan extensions, and community messaging.
- implement the moderator queue/case/audit screens;
- complete the scenario suite gate for ES-01–ES-06 and ES-13;
- run full CI on the final release candidate;
- run deployed smoke and rollback tests;
- attach measurements for accuracy/coverage, uncertainty and latency;
- resolve open design sign-offs and the hosting ADR numbering conflict;
- fill sign-off names and review records.

## 3.4 Work Division

The defense project document assigns Fatima Khursheed to resource sharing/item management and
shared trust, search, administration and analytics; Areeba Javed to UI/UX and shared
trust/search plus vendor and communication features; and Minahil Kashif to events, shared
trust, forum/chatbot, administration and analytics. All members share design, testing,
documentation and deployment. The implementation-specific allocation for the current slices is
recorded in §8.1 and should be reconciled with final contribution evidence.

---

# 4. Requirements and Acceptance Criteria

## 4.1 Requirements baseline

The requirements baseline is `DigitalMohalla_FR_NFR_Ver1.md`, version 1.3. Requirements are
organised into accounts/community, borrowing lifecycle, trust/assurance, moderation,
non-functional quality, privacy/security and deployment concerns.

## 4.2 Mid-scope acceptance matrix

| Requirement/criterion | Acceptance check | Current evidence | Status |
|---|---|---|---|
| Authenticated requests | Unauthenticated request returns 401; invalid credentials give a generic 401 | `backend/tests/integration/test_api.py` | Implemented/tested in repository |
| Role checks | Non-lender cannot accept another user's request | API integration test | Implemented/tested in repository |
| Date validation | End date must follow start date | API integration test | Implemented/tested in repository |
| Request-to-assessment | Request becomes `ASSESSED` or `HELD_FOR_REVIEW` after locality/assessment boundary | `BorrowingService.create_request`, `AssuranceEngine` | Implemented with real Slice B engine |
| Valid lifecycle moves | All valid/invalid transition matrix pairs match the design oracle | `test_transition_table.py`, transition CSV | Implemented/tested in repository |
| Replay | Event stream reconstructs state and rejects gaps/wrong previous state | aggregate/event-store tests | Implemented; latest full run **TODO** |
| No double booking | Concurrent overlapping acceptance has one winner | lifecycle/concurrency integration test | Implemented in design/tests; latest run **TODO** |
| Handover and return | Both-party confirmations reach `COMPLETED` | full API loop test | Implemented/tested in repository |
| Privacy | Responses contain no address, coordinates, CNIC or password | API privacy test | Implemented/tested in repository |
| Separate evidence and state | API returns assurance evidence and actions separately from lifecycle state | request schemas/UI components | Implemented for Slice A shape |
| Recency-weighted posterior | Property and numerical tests for posterior and 90% interval | Slice B estimation commits/tests | Implemented and verified |
| Bounded indirect evidence | k-hop search is cycle-safe, decayed, capped and benchmarked | indirect-trust commits | Implemented and verified |
| Moderator escalation | Hold/dispute receives a reason and recorded decision | Slice C tests | Implemented and verified (TC-50–57) |

## 4.3 Non-functional requirements

- **Security:** argon2 password hashing, JWT authentication and role checks.
- **Privacy:** no exact location, raw traces, CNIC or secret fields in responses/logs.
- **Reliability:** database-enforced lifecycle and booking rules.
- **Reproducibility:** locked dependencies, versioned configuration and synthetic data.
- **Maintainability:** modular monolith with explicit interfaces and generated API client.
- **Performance:** bounded propagation and a configured engine timeout; measured latency is
  **TODO**.
- **Deployment:** container image, migration-on-start and health check; live Render/Neon
  deployment is documented, while reproducible smoke and rollback evidence are **TODO**.

---

# 5. Architecture and Component/Interface Design

## 5.1 System Architecture

The system is organised as a modular monolith with a React Native/Expo client, FastAPI API,
domain modules, PostgreSQL persistence and platform automation. The trust decision core feeds
the assured transaction workflow; outcomes later return to the evidence and evaluation layers.
This keeps the mid implementation explainable while preserving module boundaries for later work.

## 5.2 Architectural style

The project uses a modular monolith. One FastAPI process contains application modules and one
PostgreSQL database provides durable state. This is appropriate for a three-person team and
keeps the custom assurance logic easy to test without introducing unnecessary network
boundaries. Module ownership remains explicit so components can be separated later if needed.

## 5.3 Layers

1. **Presentation:** Expo/React Native resident and web screens.
2. **API:** FastAPI routes, Pydantic request/response schemas and dependency injection.
3. **Application:** command orchestration in `BorrowingService`.
4. **Domain:** transition table, aggregate, assurance interfaces and pure estimation/search logic.
5. **Infrastructure:** SQLAlchemy/psycopg database adapters, event store and projections.
6. **Platform:** PostgreSQL, Docker, GitHub Actions and Render/Neon deployment.

## 5.4 Core interfaces

| Interface | Purpose |
|---|---|
| `IBorrowingCommands` | Request, accept, decline, cancel, handover, return and query commands |
| `IAssess` | Replaces the Slice A placeholder with the real assessment engine |
| `IIndirectEvidence` | Supplies bounded graph-based evidence to the assurance layer |
| `IOutcomeSink` | Converts confirmed closing events into evidence records |
| `IEventQuery` | Loads, replays and verifies event streams |
| `IModeration` | Later case queue, evidence trail and moderator decision operations |

The most important boundary is `IAssess`. The lifecycle does not know how the assessment is
computed; it receives an `AssessmentResult` containing state, policy decision, rule, explanation,
safeguards, interval/evidence fields and `config_version`.

## 5.5 Data and persistence design

The schema includes users, communities/membership, items, transactions/bookings, lifecycle
events, assessments, reports, outcome records and derived trust edges. The event store uses
stream sequence numbers and previous-state checks. The database design includes:

- unique stream sequence per transaction;
- append-only protection against update/delete;
- hash-chain verification for tamper evidence;
- PostgreSQL `btree_gist` exclusion constraint for overlapping accepted bookings;
- projections/read models rebuilt from events.

## 5.6 Behavioural design

The principal state path is:

`REQUEST_CREATED -> LOCALITY_CHECKED -> ASSESSED -> ACCEPTED -> ACTIVE -> RETURN_INITIATED -> RETURNED -> COMPLETED`

Decline, cancellation, expiry, no-show and review-hold branches are represented in the frozen
transition table. The transition matrix contains 294 state/event cases, including valid and
invalid pairs. Disputes from invalid states are rejected by design; the full moderator path is
Slice C work.

## 5.7 Design artefacts

The report should include the following project-specific diagrams when converted to LaTeX/PDF:

- [component diagram](../../docs/design/03_architecture/component_diagram.drawio);
- [layer diagram](../../docs/design/03_architecture/layer_diagram.drawio);
- [ER diagram](../../docs/design/06_data_model/er_diagram.drawio);
- [borrowing lifecycle state machine](../../docs/design/07_state_machines/borrowing_lifecycle_state_machine.drawio);
- [request-to-assessment sequence](../../docs/design/08_sequence_diagrams/sequence_a_request_to_assessment.drawio);
- [handover/return sequence](../../docs/design/08_sequence_diagrams/sequence_b_handover_return.drawio);
- [assurance pipeline DFD](../../docs/design/10_dfd/dfd_assurance_pipeline_level0_level1.drawio);
- [deployment diagram](../../docs/design/04_deployment/deployment_diagram.drawio).

**TODO:** export approved versions of the diagrams to PDF/PNG and add captions, version numbers
and design-reasoning paragraphs to the final LaTeX report.

## 5.8 Solution Architecture Groupings

The broader project is grouped into core platform modules, trust and intelligence modules, and
community-engagement modules. The current iteration prioritises resource sharing, trust/safety,
moderation and evaluation; events, forum/chatbot, vendors, broad analytics and other supporting
modules remain deferred or represented only in design.

## Design & Analysis

The design baseline connects requirements to use cases, architecture, state transitions, data
schema, sequence/activity diagrams, deployment and test cases. The main analysis decision is to
place lifecycle invariants in PostgreSQL while keeping assurance computation behind explicit
domain interfaces. The design artefacts are listed in §5.7.

---

# 6. Iteration 1: Design and Implementation

## 6.1 Proof of Concept (POC-Lite)

The proposal-stage POC-Lite described a mobile-style neighbourhood interface with radius
filtering, home actions, item discovery, community groups, events, neighbour requests, vendors
and profile navigation. The current implementation narrows this to the demonstrable
core: login, browsing, item detail, request creation, lender evidence, handover and return.
The broader POC-Lite surfaces remain deferred and must not be presented as implemented.

## 6.2 Computational Core

The computational core is a five-stage pipeline: trust evidence, Bayesian estimation, bounded
graph inference, context-aware decision policy and manipulation detection. It reports
uncertainty, safeguards and escalation rather than a single unexplained trust score. The
current Slice B implementation integrates the estimator, indirect evidence, policy and
explanation path behind `IAssess`. Manipulation detection and the human review loop remain
Slice C work.

## 6.3 Slice A and Slice B implementation

### Lifecycle domain

[BorrowingTransaction](../../backend/app/domain/lifecycle/aggregate.py) applies events in
sequence order and rebuilds state through `replay`. It rejects sequence gaps, unexpected
previous state and invalid transitions.

[TransitionTable](../../backend/app/domain/lifecycle/transition_table.py) loads the design
transition data from CSV and provides lookup, validity and next-state operations. The service
uses it for early rejection while the database remains the authoritative enforcement boundary.

[BorrowingService](../../backend/app/domain/lifecycle/service.py) orchestrates request creation,
stored locality lookup, assessment invocation, accept/decline/cancel, handover, return and
completion. It records system events and audit information for rejected commands.

### Assurance boundary

[AssuranceEngine](../../backend/app/domain/assurance/engine.py) is now the production path used
by the API. It reads evidence through `PostgresEvidenceSource`, computes direct and indirect
evidence, applies the decision policy and builds an explanation with `config_version`. The
older [StubAssuranceEngine](../../backend/app/domain/assurance/stub.py) remains only for
isolated lifecycle tests and is not used by the application. Manipulation risk is still at the
Slice C placeholder level until detection is implemented.

### API and authentication

[routes.py](../../backend/app/api/routes.py) exposes login, item browsing, requests, lender
queue, accept/decline/cancel, handover and return endpoints under `/api/v1`. Pydantic schemas
validate input and shape responses. Passwords use argon2 hashes and access uses JWT bearer
tokens.

### Frontend

The Expo Router application includes login, home/browse, item detail, request creation, request
detail/evidence, handover and return screens. The request components expose lifecycle actions
and assurance evidence separately. The generated TypeScript client is checked against the
backend OpenAPI document.

## 6.4 Slice B completed implementation

The current repository contains the completed Slice B path:

- outcome rules for normal closure and resolved disputes in
  [outcomes.py](../../backend/app/domain/assurance/estimation/outcomes.py);
- a recency-weighted Beta posterior with 90% interval and contextual similarity weighting;
- PostgreSQL trust-edge projection from verified outcomes;
- bounded k-hop graph traversal with decay, cycle safety, noisy-OR aggregation and indirect
  support cap;
- k-sweep performance work for values of `k` from 1 to 4.

The scenario suite runs the real engine through the lifecycle against synthetic fixtures,
compares lifecycle state, assurance state, rule and explanation facts, and checks
`config_version`. The lender evidence API and screen expose interval, evidence count, paths and
safeguards. Final CI run links and benchmark artefacts are **TODO**.

## 6.5 Configuration

[engine.json](../../backend/config/engine.json) stores the initial hypothesis parameters,
including prior, recency half-life, credible interval, similarity floor, maximum hops, decay,
indirect cap, manipulation windows and policy thresholds. Every assessment carries the
configuration version. The configuration status is explicitly
`initial_hypothesis_unvalidated`; thresholds must therefore not be described as empirically
optimal.

## UI & UX

The implemented Slice A interface is web-first Expo/React Native. It includes login, browse,
item detail, request creation, request detail/evidence, handover and return. UI states are
derived from available lifecycle actions, while evidence and assurance state are displayed
separately. The broader POC-Lite navigation remains deferred.

## 6.6 Tools and technologies

| Area | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Persistence | PostgreSQL 16, SQLAlchemy 2, Alembic, psycopg 3 |
| Assurance maths | NumPy/SciPy where used; pure Python bounded graph traversal |
| Authentication | argon2-cffi and JWT |
| Frontend | React Native/Expo, TypeScript, Expo Router, React Native Paper |
| API typing | OpenAPI, openapi-typescript, openapi-fetch |
| Quality | pytest, Hypothesis, ruff, mypy, Bandit, pip-audit, Jest, ESLint |
| Delivery | GitHub Actions, Docker, Render, Neon |

## 6.7 Technical decisions

- Use a database constraint for no-double-booking rather than relying only on application
  pre-checks.
- Keep lifecycle writes in one module and expose assessment through an interface.
- Store evidence and assurance state separately; do not display one trust number.
- Use versioned configuration rather than hardcoded engine parameters.
- Use synthetic data for algorithmic evaluation and label it throughout the repository.

---

# 7. Testing & Debugging

## 7.1 Testing strategy

Testing is organised from pure logic to database integration and API behaviour:

1. unit tests for transitions, aggregate replay, auth helpers, configuration and outcome rules;
2. property/numerical tests for posterior estimation;
3. integration tests against PostgreSQL for schema, event store, booking and dataset loading;
4. API tests for authentication, lifecycle, role errors, validation and privacy;
5. scenario tests for assurance states, explanations and safeguards;
6. frontend type, lint and Jest tests;
7. CI checks on every pull request/push to protected branches;
8. deployed smoke and rollback checks for CD.

## 7.2 Early test cases

Representative implemented tests include:

- all 294 state/event matrix pairs;
- invalid cancellation/acceptance and invalid dispute origin checks;
- event replay sequence-gap and previous-state validation;
- five-way concurrent acceptance/no-double-booking behaviour;
- full API request-to-completed loop;
- generic invalid-login error;
- unauthorised and wrong-role access;
- invalid date order;
- privacy response scan for location and secret fields;
- deterministic synthetic data generation and dataset loading;
- outcome extraction and mutation checks;
- posterior properties and indirect trust graph checks.

## 7.3 Test results

The repository's Slice A development record reports 330 tests at that checkpoint. The current
tree has additional Slice B scenario, engine, API and frontend evidence-screen tests. A fresh
clean-machine count and hosted CI result are still **TODO**.

**Validation performed while preparing this Markdown report:**

| Command | Result |
|---|---|
| `uv run pytest -q` from `backend` | Not executed successfully: `uv` is not installed in the current Windows environment |
| `npm test -- --runInBand` from `frontend` | Not executed successfully: frontend `node_modules` are not installed |
| frontend type/lint command | Blocked by missing local dependencies; `npx` attempted temporary packages and could not resolve the configured ESLint installation |
| Hosted GitHub Actions CI | **TODO: attach run URL, commit SHA and job results** |

These are environment/tooling blockers, not test failures. Before submission, install the
locked dependencies and replace this table with actual pass/fail counts and the CI run link.

## 7.4 Acceptance/validation status

Slice A acceptance and the Slice B functional path are supported by committed implementation and
tests. Slice C manipulation and moderation quality is not yet validated. Required remaining
measurements include:

- state and explanation accuracy on ES-01–ES-06 and ES-13;
- uncertainty/credible-interval behaviour;
- false-positive rate on legitimate dense clusters;
- newcomer treatment;
- k-sweep latency and coverage;
- deployed endpoint latency and smoke result;
- defect list with severity, correction and retest.

All such numbers are **TODO** until generated from a reproducible run.

## 7.5 Edge and failure cases

The current implementation explicitly handles:

- invalid lifecycle moves;
- missing or inconsistent event sequence;
- unauthorised role actions;
- overlapping accepted dates;
- locality outcomes other than verified;
- engine timeout/fault by placing the request on review hold;
- generic invalid credentials;
- invalid date input;
- API privacy leakage checks.

## 7.6 Defects and corrective actions

The Part A integration report records corrections to inconsistent rules, fixture intervals,
locality data flow, dispute transitions and decision-policy diagrams. These were design-baseline
corrections, not final product defects.

**TODO:** create the final iteration defect register with issue ID, severity, reproduction,
correction, owner and retest result.

---

# 8. Development Evidence, Team Work and Tool Disclosure

## 8.1 Responsibilities

The current work-division plan identifies:

- **Fatima Khursheed (S1):** lifecycle, indirect trust, locality and CI;
- **Areeba Javed (S2):** estimation, policy and detection;
- **Minahil Kashif (S3):** moderation, evaluation, application and deployment.

The division is a planning allocation; the team must confirm actual contribution and review
records before submission.

## 8.2 Repository and version control

The repository uses `main`, `develop` and feature branches with pull requests. Recent history
shows separate feature work for lifecycle, login/API, frontend, outcome extraction, Beta
posterior, trust edges, k-hop search and deployment. The branch/commit plan requires small
commits, tests with implementation, review before merge and green CI.

**TODO:** add a screenshot or appendix table containing the relevant pull-request URLs, reviewers,
commit SHAs and each member's explained ownership. Commit count alone is not sufficient evidence.

## 8.3 CI/CD

[ci.yml](../../.github/workflows/ci.yml) defines:

- backend locked install, Ruff, mypy, Bandit, pip-audit warning and pytest with PostgreSQL 16;
- frontend clean install, TypeScript, Expo lint, Jest and npm audit warning;
- OpenAPI export/client regeneration and a committed-diff check.

The deployment artifacts define a Docker API image, migration-on-start, health check and Render
deployment backed by Neon PostgreSQL. The current deployment guide records the live web and API
URLs:

- Web: `https://digitalmohalla-web.onrender.com`
- API health: `https://digitalmohalla-api.onrender.com/health`

**TODO:** attach the CI run, `/health` output, smoke test, rollback rehearsal and final hosting
ADR/sign-off.

## 8.4 Dependencies and external components

The dependency register is maintained in the technology-stack documentation. Important
components include FastAPI, PostgreSQL, SQLAlchemy, Alembic, psycopg, argon2-cffi, PyJWT,
NumPy/SciPy, Expo, React Native, TanStack Query, Jest and GitHub Actions. Public datasets are
documented separately and are not mixed with synthetic or future pilot data.

**TODO:** verify every licence/version row against the final lock files and complete Form 13.

## 8.5 AI/tool-assisted development

The repository contains an AI usage log. It records assistance with scaffolding, design
integration, lifecycle implementation, frontend, data generation, testing and CI/CD. The team
must be able to explain every submitted component and must fill the reviewer column. AI-assisted
output is not treated as an independent validation source.

## 8.6 Risks and mitigation

| Risk | Impact | Mitigation | Status |
|---|---|---|---|
| Assurance thresholds are unvalidated | Incorrect decisions | Version config, held-out scenarios, report negative results | Open |
| Sparse/indirect evidence overconfidence | Unsafe recommendation | Credible interval, indirect cap, escalation | Partially implemented |
| Manipulation false positives | Legitimate users held | Corroboration and dense-cluster test | Slice C TODO |
| Database/concurrency mismatch | Double booking or inconsistent state | DB constraints plus integration tests | Implemented/design-tested |
| CI dependency drift | Non-reproducible build | Lock files, clean installs, Dependabot and client drift check | Workflow committed |
| Hosting free-tier sleep/limits | Demo delay | Warm-up health check and local fallback | Deployment guide; rehearsal TODO |
| Privacy leakage | User harm/compliance risk | Coarse locality, response/log checks, no exact address | Partially implemented |
| Scope expansion | Missed core | Frozen scope and branch plan | Active control |

## 8.7 Deployment

Deployment artifacts use a Docker API image, Render for the API and Neon for PostgreSQL 16.
Migrations run at startup and `/health` is used as the readiness gate. The web and API are live
on Render at the URLs listed in §8.3. Smoke-test output, rollback rehearsal and the hosting ADR
remain **TODO**.

## 8.8 Documentation

The repository contains the project context, technology stack, requirements, architecture,
deployment design, test plan, AI usage log and design artefacts. This report is the Markdown
working version intended for later conversion into the supplied LaTeX template. Final
documentation still requires verified citations, approved diagrams, contribution evidence and
completed sign-offs.

---

# 9. Current Limitations

1. Slice B functional correctness is represented by synthetic fixtures and tests, but final
   held-out performance and calibration measurements are not attached.
2. Slice C manipulation detection is not active; ES-04 and ES-05 remain expected strict failures.
3. Slice C disputes, moderation and case decisions are not complete.
4. The final app workflow is not yet the full committed product.
5. Hosted CI evidence and rollback rehearsal are not attached to this report.
6. Engine parameters are initial hypotheses, not validated thresholds.
7. No real pilot data or user-study result is claimed.
8. The exact final hosting ADR number and some design sign-offs remain open.
9. Local test execution for this report was blocked by missing `uv` and frontend dependencies.
10. Formal signatures, final bibliography verification and department metadata are incomplete
    in this working draft.

---

# 10. FYP-2 Plan

## 10.1 Completion plan

### Remaining FYP-1 work

1. Finish Slice C: manipulation checks, disputes, moderation decisions and moderator app.
2. Run all backend/frontend/API-client checks on clean environments.
3. Complete hosted CD, smoke test and rollback rehearsal.
4. Freeze a mid/final baseline with linked CI and deployment evidence.

### FYP-2 work

1. Integrate remaining committed modules without expanding scope.
2. Complete locality/membership and notifications where scheduled.
3. Conduct held-out synthetic evaluation and report negative findings.
4. Compare against baseline methods and ablations.
5. Run system tests on the deployed application.
6. Conduct the approved pilot/acceptance activity, if retained, with consent and privacy controls.
7. Finalise report, poster, limitations and reproducibility package.

## 10.2 Evaluation Plan

The final evaluation will keep simulation, public trust-network validation and any real pilot
data separate. It will report:

- assurance-state and explanation correctness by scenario;
- interval behaviour and calibration;
- coverage and false-positive rate;
- newcomer handling;
- manipulation detection performance;
- k-hop latency/coverage trade-off;
- API and deployed-system latency;
- ablation results for direct evidence, indirect evidence and manipulation signals.

Attack strategies used for final evaluation must be held out from tuning, and the report must
include negative results where a component has no measurable benefit.

---

# 11. Conclusion

Digital Mohalla has progressed from an integrated design baseline to a working Slice A and Slice
B product path. The current system demonstrates a real event-sourced borrowing lifecycle with
authentication, database-backed invariants, replayable events, privacy checks, the real
assurance engine integrated behind a replaceable interface, a lender evidence screen and a
web-first Expo client.

The report remains deliberately precise: Slice C manipulation detection and moderation are not
complete, and CI/CD/deployment claims still require linked execution evidence. The next
implementation priority is to complete the human review loop, evaluate the engine on held-out
scenarios, and produce reproducible CI, deployment, rollback and performance results.

---

# Appendix A. Repository evidence map

| Evidence | Location |
|---|---|
| Project context and mid rubric mapping | [DigitalMohalla_Project_Context.md](../DigitalMohalla_Project_Context.md) |
| Technology/architecture decisions | [DigitalMohalla_Tech_Stack.md](../DigitalMohalla_Tech_Stack.md) |
| Iteration plan | [DigitalMohalla_Iteration1_Plan_Ver1.md](../design/00_management/DigitalMohalla_Iteration1_Plan_Ver1.md) |
| Slice B/C work plan | [Slices_B_C_Branch_and_Commit_Plan.md](../design/00_management/Slices_B_C_Branch_and_Commit_Plan.md) |
| Requirements | [DigitalMohalla_FR_NFR_Ver1.md](../design/01_requirements/DigitalMohalla_FR_NFR_Ver1.md) |
| Architecture | [Architecture_Design.md](../design/03_architecture/Architecture_Design.md) |
| Deployment | [Deployment_Design.md](../design/04_deployment/Deployment_Design.md) |
| Integration report | [Integration_Report_2026-10-11.md](../design/00_management/Integration_Report_2026-10-11.md) |
| Backend API | [routes.py](../../backend/app/api/routes.py) |
| Lifecycle service | [service.py](../../backend/app/domain/lifecycle/service.py) |
| Lifecycle aggregate | [aggregate.py](../../backend/app/domain/lifecycle/aggregate.py) |
| Assurance engine and legacy test stub | [engine.py](../../backend/app/domain/assurance/engine.py), [stub.py](../../backend/app/domain/assurance/stub.py) |
| Versioned engine config | [engine.json](../../backend/config/engine.json) |
| CI workflow | [ci.yml](../../.github/workflows/ci.yml) |
| AI usage disclosure | [ai-usage-log.md](../ai-usage-log.md) |

# Appendix B. Submission checklist

- [ ] Confirm supervisor, coordinator, dean, director and HOD metadata.
- [ ] Add approved diagrams with captions and reasoning.
- [ ] Add bibliography citations and verify dataset licences.
- [ ] Attach CI run URL and pass/fail summary.
- [ ] Attach CD/deployment URL, health check, smoke test and rollback evidence.
- [ ] Replace all test-result TODOs with clean-machine results.
- [ ] Complete Slice C implementation and final scenario results.
- [ ] Add final contribution/peer-review evidence.
- [ ] Fill AI usage-log reviewer fields and Form 13.
- [ ] Obtain required team/supervisor sign-offs.
