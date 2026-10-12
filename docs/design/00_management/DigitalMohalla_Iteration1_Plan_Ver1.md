# Digital Mohalla — Iteration 1 (FYP-1 Mid) Plan

Oct 10, 2026 · status updated Oct 11, 2026 (integration)

> **Part A status, 11 October 2026.** Every Part A artefact now exists and the three students' work is integrated into one baseline (`../README.md` is the index; `Integration_Report_2026-10-11.md` lists what changed). Done: A1 to A13 (A2 domain model v1.0 by decision D18; A7 class diagrams for all three students). A14: the design and notation review is recorded in `Design_Review_A14_2026-10-11.md`; still open are the stack decision (D-15), the deployment target and the tag `design-v1.0`. A0's project-instructions wording is outside these files. Sign-offs still needed: ADR-0006 (Student 2), ADR-0007 and ADR-0008 (Students 2 and 3), data dictionary (all three, tag `schema-v1`). Decisions taken during integration are D10 to D17 in `Integration_Decisions_2026-10-11.md`.

## Bottom line

Iteration 1 runs in two parts: about a week of design and analysis ending in a design baseline (Part A), then three build slices ending in a live, tested, deployed core (Part B). Three decisions from 10 October shape it.

- **k-hop indirect evidence (Module 5) is in iteration 1.** UC-D3/4/5 has it in the main success scenario, and the proposal's contribution statement promises it.
- **No interviews or survey.** The team treats locality and location spoofing as a real issue. Locality is fully designed in iteration 1; whether one method is also built is decided at the D-11 gate.
- **Four design gaps come first.** Date-hold semantics, the concurrency rule in B5 extension 3c, the exits from HELD\_FOR\_REVIEW, and the SUFFICIENT\_EVIDENCE rule all block coding. They are steps A1 and A5.

The biggest risk is time. Proposal §13 planned iteration 1 as design only, but mid needs a live core module (Form 2, 25 marks), so design has to close in about a week.

The proposal action "show location is a real issue" still needs evidence in the Form 10 register. Without a survey, cite the spoofing threat model, the locality test cases and the privacy design from step A11. Also remove the "after interviews" wording from FR-A-07, I-10, NFR-PR-05 and the overview's Problem Validation section.

The mid-eval date is not in the project files, so the plan counts days back from it (D-21 means 21 days before), assuming about three weeks.

## What the mid eval grades

FYP-1 Mid is supervisor-only, 15 minutes, worth 20 marks of FYP-1, and is meant as a formative checkpoint (Handbook, Appendix A, Stage 1). Two forms score it. How they combine into the 20 marks isn't in the handbook, so ask Dr. Ali Zeeshan.

**Form 2: presentation and demo**

| Criterion | Max | What earns it |
| --- | --- | --- |
| Live prototype with core module | 25 | Real project logic working live, not screenshots or video; an edge or failure case shown |
| Design artefacts and evolution | 15 | Architecture plus data/process/behaviour artefacts tied to the code; changes since proposal justified |
| Proposal actions addressed | 10 | Action register with each change, status and evidence link |
| Iteration plan and progress | 10 | Milestones met, or delays justified with a recovery plan |
| Requirements and acceptance criteria | 10 | FRs/NFRs and acceptance checks technically correct and in scope |
| Repository and member evidence | 10 | Tagged code, commit timeline, task log, visible ownership; commit count alone doesn't count |
| Testing and early validation | 10 | Tests for the current module; one failure or edge case discussed |
| Team dynamics and tool ownership | 10 | Tool-assisted output defended by the team |

**Form 3: mid report**

| Criterion | Max | What earns it |
| --- | --- | --- |
| Problem, R&D, existing solutions | 15 | What was studied, the remaining gap, the complex challenge |
| Requirements and acceptance criteria | 15 | Precise, testable FRs/NFRs with acceptance checks |
| Architecture and component/interface design | 15 | Clear, justified; a generated diagram alone is capped |
| Implementation documentation | 15 | Setup, main files/classes/functions, technical decisions; reproducible |
| Testing plan and tool/risk disclosure | 15 | Test plan, early results, dependency disclosure, risk, privacy, limitations |
| Vision, scope, modules, success criteria | 10 | Consistent with what was approved |
| Data/process/behaviour design | 10 | Project-specific ERD, state, sequence or activity diagrams, explained |
| Format and required artefacts | 5 | Template followed; missing artefacts cap the relevant sections |

**Automatic caps that apply here** (Handbook §2.2):

- No live system: implementation/demo marks capped at 40%.
- Diagrams without design reasoning: design marks capped at 50%.
- Undisclosed core GenAI/API use: responsible tool-use item set to 0.
- A member who can't explain their claimed code gets an individual multiplier (Form 11: 1.00 down to 0.00).

## Iteration 1 scope

Iteration 1 builds the core module: the request-to-return loop (Module 3) with its assessment engine (Module 5), dispute and hold resolution (Module 9) and the scenario suite (Module 10), on minimal accounts (Module 1). Everything else is seeded, stubbed or scheduled for a later iteration in the module roadmap. Module numbers are the overview's ten modules; the roadmap maps the proposal's §8.1 components onto them.

| Item | Iteration 1 | FRs | Module |
| --- | --- | --- | --- |
| Borrowing request with date check (B5) | Build | FR-B-05, FR-B-06 | 3 |
| Event store, state machine, replay, invalid-transition rejection | Build | FR-B-08, FR-B-09 | 3 |
| No double booking: overlap constraint at acceptance (ADR-0002) | Build | FR-B-05, NFR-R-01 | 3 |
| Lender accept or decline (B6) | Build, no counter-offer | FR-B-10 | 3 |
| Handover, return, late outcome (B7, B8) | Build, photos optional | FR-B-11, FR-B-13 | 3 |
| Outcome sent to the engine as evidence | Build | FR-B-15 | 3, 5 |
| Raise and withdraw a dispute (B12) | Build | FR-B-16, FR-B-17 | 3 |
| Deposit | Record-only flag, no money moves | FR-B-11 | 3 |
| Recency-weighted Beta posterior, 90% credible interval | Build | FR-T-02 | 5 |
| Evidence weighting | Recency and value band | FR-T-03 | 5 |
| k-hop indirect evidence | Build, bounded (k from config) | FR-T-04 | 5 |
| Manipulation checks | 3: reciprocal clustering and review-text similarity (ES-04, corroborated as ADR-0007 requires), retaliation (ES-05) | FR-T-05 | 5 |
| Decision policy, 4 assurance states, safeguards, explanation | Build | FR-T-01, FR-T-06, FR-T-08 | 5 |
| Engine failure or timeout to HELD\_FOR\_REVIEW | Build | FR-T-07 | 5 |
| Escalation case with evidence trail (D6) | Build, chat messages later | FR-T-10 | 5 |
| Moderator decisions for disputes and holds (I4) | Build, no appeal or reversal | FR-T-11 | 9 |
| Append-only audit log and minimal view (I6) | Build | FR-M-05 | 9 |
| Frozen event logging | Build | FR-N-03 | 10 |
| Scenario suite ES-01 to ES-06 and ES-13 | Build, in CI | NFR-Q-01 | 10 |
| Login and roles | Minimal: seeded users, password login | FR-A-04 (part) | 1 |
| Locality check | Designed (A11) and stubbed in B5; method build decided at D-11 | FR-B-07, FR-A-06 to A-11 | 1, 3 |
| Communities, memberships, items | Seeded, no UI | FR-A-09, FR-B-01 | 1, 3 |
| Reviews (D1) | Seeded for ES-04 and ES-05 only | FR-T-09 | 5 |
| Iteration 2 (roadmap) | Membership and locality, scheduler jobs, counter-offer, extensions, remaining detection signals, reviews, appeal and reversal, in-app notifications, simulator and baselines | — | 1, 3, 5, 7, 9, 10 |
| Iteration 3 (roadmap) | Accounts, listings and calendar, search, chat, admin tools, trust profile, reporting | — | 1, 3, 4, 5, 7, 9 |
| Stretch, iteration 3 at the earliest and only one | Events, forum and chatbot, vendors | STRC | 2, 6, 8 |

ES-13 is now in the FR/NFR scenario list (v1.1). D1 is CORE M but only in Appendix B, so the report should say reviews are seeded in iteration 1 and built in iteration 2.

## Decisions

Eight decisions are settled, two are proposed and waiting for sign-off, and seven are open; each open one is tied to a step or gate below.

| Decision | Status | Where it gets closed |
| --- | --- | --- |
| Single borrowing state list (Use Cases §2) | Agreed | Drawn in the state machine, step A3 |
| Frozen event schema | Agreed; field names unified in v1.1 | Where event-specific data lives (N-6) is still open, step A4 |
| "Recency-weighted Beta posterior" wording | Done in all files | Project instructions still say Beta-Binomial (step A0) |
| I4 covers disputes and non-dispute holds | Done | — |
| k-hop indirect evidence in iteration 1 | Agreed | Module 5, indirect-trust part owned by S1 |
| No interviews or survey | Done; interview wording removed in v1.1 | Location evidence comes from step A11 |
| Deposits record-only | Done; I-4 closed in v1.1 | — |
| Module numbering | Agreed: the overview's ten modules (module roadmap) | Project instructions still say M1 to M9 (step A0) |
| ADR-0001 to ADR-0004: soft hold, overlap constraint, hold exits, dispute event types | Accepted 2026-10-11 (D3) | — |
| Work division | Proposed | Matches the roadmap's ownership table; assign names before D-15 |
| SUFFICIENT\_EVIDENCE rule and other missing thresholds | Done: rules R7 and R8 and the config file (Student 2, A5) | Algorithm doc §6; config 1.1.0 |
| When high value with weak evidence is held rather than reviewed (N-7) | Done: rule R4 holds it; strong similar evidence goes to the lender (R8) | Algorithm doc §6 |
| Field for event-specific data in the schema (N-6) | Done: `payload` (ADR-0005, D1) | — |
| Locality method built in iteration 1 or 2 | Open | D-11 gate |
| Frontend and backend stack | Open | Design gate, D-15; proposal §8.1 already names Python, FastAPI, PostgreSQL |
| Deployment target | Proposed: one AWS EC2 host with Docker Compose (D17, `04_deployment/`); size, region and domain to confirm | By D-14 (Student 3) |
| Evaluation datasets (Bitcoin OTC and YelpChi vs Epinions) and success targets (≥70% accuracy, <5% false positives vs TBD) | Open | Not needed for mid; settle in the FYP-2 evaluation plan |

## Timeline

Design closes at D-15, then three vertical slices each end in something deployable, so a slipped slice still leaves a live demo.

&#91;embedded content: iteration 1 roadmap · 5 phases, 4 gates\]

Report chapters 1 to 5 are written from the design artefacts while Slice A is built, so the last week is only chapters 6 to 10 and rehearsal.

## Part A: design and analysis (D-21 to D-15)

Fifteen steps take the baselined requirements to a design you can code from; the handbook places the design baseline at Mid-1, before implementation (Handbook C.5.1). Each artefact goes in the report with 2 to 4 sentences of rationale, the FRs it realises and the package it maps to, since diagrams without reasoning are capped at 50% (Handbook §2.2). Draw only what iteration 1 builds: Modules 3, 5, 9 and 10 in detail, and Module 1 as far as login and locality.

- [ ] **A0 Clean-up (D-21, all).** Done in v1.1 of the use cases, FR/NFR and overview: the 68 count, interview wording removed, deposits record-only (I-4 closed). Still to do: replace "Beta-Binomial" and the M1 to M9 module labels in the project instructions with the recency-weighted Beta posterior and the overview's ten modules. Give each design artefact a control block (version, date, author, status).
- [x] **A1 Close**** **** the four baseline gaps (D-21 to D-20, S1 with S2).** One short ADR each:
  1. Soft or hard date hold. A soft hold matches FR-B-05 and B6 step 5.
  2. A concurrency rule replacing B5 extension 3c. `stream_seq` counts within one transaction, so it can't order competing requests; use a database constraint on overlapping accepted bookings.
  3. HELD\_FOR\_REVIEW exits by hold reason: a locality hold runs the assessment when cleared, a manipulation hold goes to ASSESSED, an engine-failure hold re-runs the assessment.
  4. A `dispute_resolved` event type for moderator closures, so replay can tell them from clean completions.

  Drafted in DigitalMohalla\_ADRs.md, and v1.1 of the use cases and FRs already follows them. Done when all three sign off.
- [x] **A2 Domain model (D-20, all, one sitting).** User, Community, Membership, Item, BorrowingTransaction, LifecycleEvent, Outcome, TrustEdge, Assessment, EscalationCase, ModeratorDecision, Review, with associations and multiplicities. Done when every noun in the dressed use cases maps to a class or is deliberately left out.
- [x] **A3 State machines and transition table (D-20 to D-19, S1).** The borrowing lifecycle (14 states) with guards, actors and the HELD\_FOR\_REVIEW exits; the escalation case (open, awaiting information, decided, appealed or reversed); and a transition table of state × event → next state, guard, allowed actor. Done when every transition traces to a use case step. The table becomes the invalid-transition test matrix.
- [x] **A4 Data dictionary and event catalogue (D-19, S1).** Frozen fields with one spelling, every `event_type` with its evidence fields, the assessment output object, and the config parameter list. Done when all three sign off; tag `schema-v1`.
- [x] **A5 Algorithm and policy design (D-19 to D-17, S2; indirect-trust part by S1).**
  - Module 5, trust estimation: recency-weighted Beta posterior and 90% interval, with pseudocode and complexity.
  - Module 5, indirect trust: trust edges from verified outcomes; bounded path search to k; strongest path per first-hop neighbour; noisy-OR; reliability cap; complexity; a 6 to 8 node example worked by hand.
  - Module 5, manipulation detection: the reciprocal-clustering and retaliation checks, with their windows.
  - Module 5, decision policy: an activity diagram and decision table defining the SUFFICIENT\_EVIDENCE rule, how indirect evidence changes the outcome, high-value dissimilarity, risk bands and precedence (open dispute first).
  - Config file draft: every parameter with its source (Overview §5.2, §5.5, §5.6, or this step), labelled initial and unvalidated.

  Done when ES-01 to ES-06 and ES-13 each have fixture inputs and a hand-worked expected state and explanation.
- [x] **A6 ER diagram and schema (D-18, S1).** Append-only event store, read projections, trust edges, assessments with `config_version`, cases and decisions. Done when every data dictionary field has a column.
- [x] **A7 Class diagram, core packages (D-18 to D-17, each owner draws their module).** Classes for Module 3 (lifecycle), Module 5 (estimation, indirect trust, detection, policy), Module 9 (cases and decisions) and Module 1 (users, communities, membership), with assurance state and lifecycle state as separate attributes (ES-04 has REVIEW\_RECOMMENDED while the request is HELD\_FOR\_REVIEW). Done when each class names the FRs it realises.
- [x] **A8 Architecture (D-17, S1).** Component diagram of the ten modules, with Modules 1, 3, 5, 9 and 10 in detail, showing provided and required interfaces, the engine behind one `assess(request)` call; layer diagram; REST endpoint table. Done when each endpoint maps to a use case step.
- [x] **A9 Behaviour diagrams (D-17 to D-16).**
  - Sequence (a), B5 from request to assessment with the timeout branch (S2).
  - Sequence (b), B7 and B8 from dual confirmation to evidence (S1).
  - Sequence (c), B12 to D6 to I4 (S3).
  - Dispute-resolution activity diagram with swimlanes, SSDs for B5, B7 with B8, B12 and I4, and the core use case diagram (S3).
- [x] **A10 DFD (D-16, S2).** Level 0, and level 1 for the assurance pipeline, showing the boundary that exact location never crosses.
- [x] **A11 Locality design (D-17 to D-16, S1).** Compare coarse geofence, invitation, moderator approval and a combination on false accepts and rejects, privacy, spoofing resistance and cost; pick one. Write the six locality test cases from Overview §1: spoofing, boundary users, visitors, permission refusal, duplicate accounts, false rejection. This is the Form 10 evidence for the location action.
- [x] **A12 Wireframes (D-18 to D-16, S3).** Request with evidence summary, lender decision, handover and return checklists, dispute form, moderator queue and case view. Every assurance screen shows evidence, never one number (NFR-U-01).
- [x] **A13 Test plan and deployment diagram (D-16, S3).** Levels, techniques and the suites in the test plan section; provisional deployment diagram with the target marked to be confirmed.
- [ ] **A14 Design gate (D-15, all).** Stack decided. Every artefact reviewed by a second member. Walk Dr. Ali Zeeshan through it if possible. Tag `design-v1.0`.

## Part B: implementation (D-15 to D-0)

Three vertical slices build the loop first with stubs, then the assurance core, then the human loop; each ends with a gate checked on the deployed instance.

- [ ] **B0 Setup (D-15 to D-14).**
  - S1: repo layout (`backend/`, `frontend/`, `infra/`, `docs/`), protected `main` and `develop`, board and "Iteration 1" milestone, CI skeleton.
  - S1: Docker Compose with PostgreSQL, config loader, seed script with synthetic users labelled synthetic.
  - S3: deployment target chosen and reachable from CD.
  - All: start the AI usage log and Form 13 sheet.
- [ ] **Slice A: workflow skeleton (D-14 to D-11).**
  - S1: append-only event store with unique `stream_id` + `stream_seq`; transition table from A3; aggregate and replay; the concurrency rule from A1; authorisation on every transition.
  - S1: request → stub locality → stub assessment (always INSUFFICIENT\_EVIDENCE) → accept or decline → handover → ACTIVE → return → RETURNED → COMPLETED.
  - S2: the engine interface `assess(request)` returning the agreed output object, stubbed; fixtures for ES-01 to ES-06 and ES-13.
  - S3: minimal UI that clicks through the loop; first CD deploy with smoke test.
  - **Gate D-11:** the loop runs on the deployed instance, and the transition-matrix, replay, concurrency, authorisation and append-only tests pass. Decide whether the locality method is built in Slice C or in iteration 2.
- [ ] **Slice B: assurance core (D-11 to D-8).**
  - S2: outcome extraction (confirmed outcomes only, disputed ones excluded); Beta posterior with recency and value band; decision policy with safeguards and explanation; `config_version` stored; engine timeout goes to HELD\_FOR\_REVIEW.
  - S1: trust-edge projection and k-hop path search; paths shown in the explanation; latency and coverage at k = 1 to 4.
  - S3: lender screen showing the evidence summary; scenario suite (Module 10) running in CI.
  - **Gate D-8:** ES-01, ES-02, ES-03, ES-06 and ES-13 pass in CI with state and explanation.
- [ ] **Slice C: human loop (D-8 to D-5).**
  - S2: reciprocal-clustering and retaliation checks; ES-04 and ES-05 pass; a dense legitimate group stays below the review threshold.
  - S3: raise dispute and freeze; case with evidence trail (D6); moderator decisions for disputes and holds (I4); resolved outcome counted as evidence; minimal audit log view (I6).
  - S1: privacy checks on API responses and logs; the locality method if the D-11 gate chose it.
  - **Gate D-5:** feature freeze; tag `v0.1.0-rc1`.
- [ ] **Freeze, report and rehearsal (D-5 to D-0, all).**
  - System tests on the deployed instance; defect log with severity and fixes.
  - Latency numbers saved with the config version and raw output.
  - Screenshots and CI links for chapters 6 and 7.
  - Report chapters 6 to 10; abstract and executive summary last.
  - Two timed demo rehearsals, including the failure cases.
  - Update Form 10, Form 13 and the AI usage log; tag `v0.1.0-mid1`; reset demo data; submit.

## Work division per student (proposed)

Each student owns a technical part of the core, which is the handbook's scope test: remove a member and a technical piece with its evidence disappears (Handbook C.5). The split matches the module roadmap's ownership table, so each person keeps the same modules into iterations 2 to 4. Assign names to S1, S2 and S3 when you settle it.

|  | S1: lifecycle, indirect trust, locality | S2: estimation, policy, detection | S3: moderation, evaluation, apps |
| --- | --- | --- | --- |
| Modules in iteration 1 | Module 3 borrowing lifecycle; Module 5 indirect trust; Module 1 minimal login and locality design; CI | Module 5 trust estimation, decision policy, first manipulation checks | Module 9 case and dispute resolution (I4, I6); Module 10 scenario suite; resident and moderator apps; deployment |
| Part A design | A1 ADRs (lead), A3 state machines, A4 data dictionary, A6 ERD, A8 architecture, A11 locality, indirect-trust part of A5, sequence (b) | A5 (lead) for estimation, detection and policy, config file, decision-policy activity diagram, sequence (a), A10 DFD | Sequence (c), dispute activity diagram, SSDs, use case diagram, A12 wireframes, A13 test plan and deployment diagram |
| Part B build | B0 repo and CI; Slice A lifecycle; Slice B k-hop; Slice C privacy checks and the locality method if chosen | Slice A engine interface and fixtures; Slice B Beta posterior and policy; Slice C two checks | B0 deployment; Slice A UI and CD; Slice B lender screen and scenario suite in CI; Slice C dispute, cases, moderator decisions, audit view |
| Tests owned | Transition matrix, replay, concurrency, authorisation, append-only log, k-hop hand graph, k sweep latency, privacy | Beta math, policy decision table, scenario logic, dense-group guard, engine timeout | Dispute and hold resolution, UI smoke, deployed smoke and system tests |
| Report | 5.1 to 5.3, 5.7, state machine, 6.6 lifecycle and indirect trust, locality and spoofing design, CI/CD | 2.6 CCP, 2.8, 5.8, 6.7 algorithms and complexity, engine results | Ch. 1 including the ten modules, 2.2 to 2.4, Ch. 3, Ch. 4 diagrams, Ch. 7 lead, Ch. 9 from the roadmap, setup manual |
| Demo | Invalid transition, concurrent acceptances, replay, k-hop paths in the explanation | Newcomer vs established borrower, colluding scenario, engine timeout | Main request-to-return story, moderator decision, pipeline and deploy |
| Next, per the roadmap | Iteration 2: Module 1 membership and locality, Module 3 completion, Module 7 in-app notifications | Iteration 2: Module 5 completion and reviews | Iteration 2: Module 9 completion; Module 10 simulator, baselines, evaluation plan |

Why this split:

- Module 5 is shared on purpose: S2 owns estimation, policy and detection, S1 owns indirect trust. The component diagram shows that boundary as one interface, `assess(request)`.
- Module 10 sits with S3, so the attack generator built in iteration 3 is never written by the author of the manipulation checks.
- If S2 falls behind, S1 takes the reciprocal-clustering check, which is a graph check.
- Proposal §14 lists trust as shared by all three, which fails the scope test; record this split as the replacement in report §3.6.
- Shared by all: the domain model, the class diagram (each draws their part), report chapter 4, and review of every PR by someone other than its author.

## CI/CD

Two protected branches, short-lived feature branches, two workflows and one deployed environment are enough to show real CI and CD without overhead a 3-person team can't sustain.

&#91;embedded content: branch and pipeline flow · 2 gates\]

A red check or a missing review sends work back to its branch; a failed smoke test after deploy rolls back to the previous image.

**Branches**

- `main`: what runs on AWS. Protected; changes only through a release PR from `develop`.
- `develop`: integration branch. Protected; PRs only.
- `feature/<area>-<topic>`, `fix/…`, `docs/…`: e.g. `feature/engine-beta-posterior`, `feature/lifecycle-replay`. Each links an issue ("Closes #12").
- Merge rules on both protected branches: all CI jobs pass and one approval from a member who didn't write it.
- Tags per iteration: `v0.1.0-mid1` now, `v0.2.0-final1` at FYP-1 Final.

**`ci.yml`** (every PR and push to `develop` or `main`)

1. Lint and format: ruff (backend), eslint (frontend).
2. Type check: mypy on the engine and lifecycle packages.
3. Static and dependency scan: bandit, pip-audit (the handbook lists static analysis under the Development Phase).
4. Unit tests with coverage (pytest); proposed floor of 80% on engine and lifecycle packages.
5. Integration tests against a Postgres service container: lifecycle, replay, concurrency, authorisation, dispute.
6. Assurance scenario suite: the six scenarios with their expected states.
7. Frontend build.
8. Upload JUnit and coverage reports as artifacts; these are the evidence for chapter 7.

**`cd.yml`** (push to `main`)

1. Build Docker images and push to GHCR, tagged with the commit SHA.
2. Deploy to the AWS host over SSH: pull, run migrations, `docker compose up -d`.
3. Smoke test: `/health` plus one scripted request through to assessment.
4. On a failed smoke test, redeploy the previous image tag. This is the rollback, and it's worth showing once.

Secrets live in GitHub Environments, never in the repo (the handbook forbids committing keys). Add pre-commit hooks for ruff and Dependabot for updates. If you can afford a second environment later, `develop` can auto-deploy to staging; for iteration 1 one environment is fine.

## Test plan for iteration 1

Fifteen suites cover the workflow, the assurance pipeline and the deployment; each traces to an FR or NFR and lands in a named slice.

| # | Suite | Level | Technique | Pass condition | Traces to | Slice |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Transition matrix | Unit | State-transition testing over every (state, event) pair in the A3 table | Valid moves pass; every invalid one is rejected and logged | FR-B-08, NFR-R-02 | A |
| 2 | Replay | Integration | Rebuild in `stream_seq` order | Rebuilt state equals stored state | FR-B-09, NFR-R-03 | A |
| 3 | Double booking | Integration | N parallel requests and acceptances | Exactly one acceptance wins, every run | FR-B-05, NFR-R-01 | A |
| 4 | Authorisation | Integration | Decision table by actor and role | Only permitted actors transition; moderators act only in their community | NFR-S-02, NFR-S-03 | A |
| 5 | Append-only log | Integration | Negative and tamper test | UPDATE or DELETE fails; an altered entry is detected | FR-M-05, NFR-S-05 | A |
| 6 | Beta posterior | Unit | Known values and boundaries | Zero history gives Beta(1,1); 18 and 2 give Beta(19,3); weights about 0.96 and 0.25 at 10 and 360 days; interval narrows with evidence | FR-T-02, FR-T-03 | B |
| 7 | k-hop propagation | Unit | The hand-worked graph from A5 | Expected paths, decay, one path per first-hop neighbour, noisy-OR, ρ ≤ 0.6, nothing beyond k, cycles safe | FR-T-04 | B |
| 8 | k sweep | Performance | Benchmark at k = 1 to 4, seeded scale | Latency and coverage reported with the config version | NFR-P-03 | B |
| 9 | Policy rules | Unit | Decision table from A5 | Open dispute first; indirect evidence alone never gives SUFFICIENT; risk ≥ 60 holds, no restriction | FR-T-06 | B |
| 10 | Engine failure | Integration | Fault injection | Timeout goes to HELD\_FOR\_REVIEW, is logged, and assigns no state | FR-T-07, NFR-R-04 | B |
| 11 | Scenarios ES-01 to ES-06, ES-13 | Acceptance | Synthetic fixtures | State and explanation both match | NFR-Q-01 | B, C |
| 12 | Dense legitimate group | Unit | Negative test | A family-style reciprocal group stays below the review threshold | C3 guard | C |
| 13 | Dispute and hold resolution | Integration | Use-case paths | Dispute closes via `dispute_resolved` and the outcome counts; a hold ends cleared, with safeguards, or declined | FR-B-16, FR-T-10, FR-T-11 | C |
| 14 | Privacy | Integration | Negative test | No API response or log contains address, coordinates or CNIC fields | NFR-PR-01, NFR-S-07 | C |
| 15 | Transition latency and deployed smoke | Performance, system | Load test and end-to-end run | P95 recorded; the full loop passes on the deployed instance | NFR-P-04, NFR-D-04 | Freeze |

Write test cases in the input / expected / actual format from the start; FYP-1 Final asks for exactly that (Form 5). Scenario fixtures are for correctness only. Keep the future held-out attack generator in a separate package, written by someone other than the detector's author, so detector parameters are never tuned against it.

## 15-minute demo script

One story carries the demo: a newcomer's request, a damaged return, a moderator decision, and the evidence visibly updating afterwards. Run it on the deployed instance with seeded synthetic users, and say they are synthetic.

1. **0:00 to 1:00, framing (S3).** The CCP in one sentence, and what changed since proposal, from the action register.
2. **1:00 to 6:30, main story (S3 drives).**
   1. A newcomer requests a drill. The lender sees INSUFFICIENT\_EVIDENCE, "Insufficient verified history; lender review required", a wide interval and safeguards. The borrower isn't treated as risky.
   2. A borrower with history elsewhere but none with this lender requests it (ES-13). The explanation shows the indirect paths through two neighbours and what they changed (S1 explains).
   3. An established borrower gets SUFFICIENT\_EVIDENCE; show effective evidence and the narrow interval.
   4. The lender accepts the first request; both confirm handover; the loan is ACTIVE. On return the lender reports damage and it goes DISPUTED.
   5. The borrower's next request shows ACTIVE\_DISPUTE.
   6. The moderator opens the case, reads the evidence trail built from the event log, and decides with a reason. The next assessment shows the resolved outcome.
3. **6:30 to 9:00, edge and failure cases (S1, S2).** An invalid transition through the API is rejected and logged. Two simultaneous acceptances for the same dates: one wins. The colluding scenario puts the request in HELD\_FOR\_REVIEW with REVIEW\_RECOMMENDED and the anomaly shown, and no automatic block. A forced engine timeout lands the request in HELD\_FOR\_REVIEW.
4. **9:00 to 11:00, engineering evidence (S1).** A PR blocked by a failing check; a green pipeline; the CD run and smoke test; the iteration tag; replay rebuilding state; the k = 1 to 4 latency numbers.
5. **11:00 to 15:00, walkthrough and questions (all).** Each member opens one file they own and explains one design decision they made.

Keep a seed-reset script and a local Docker Compose fallback in case the network fails; a local run is still live.

## Report checklist

Every artefact in the handbook's Mid Evaluation list has a home in the template below. Pick design diagrams that fit the project (the handbook says "select the design that is appropriate"), explain each one, and point it at real code, or the design marks are capped at 50%.

| Template chapter | Must contain | Handbook artefacts covered | Owner |
| --- | --- | --- | --- |
| Front matter | Title page, declarations, abstract and executive summary (written last), abbreviations | — | all |
| 1 Introduction and vision | Post-defence vision; scope table tagged CORE/ENAB/SUPP/STRC; the ten modules with the proposal's components mapped onto them; stakeholders; measurable success criteria; constraints; ethics, legal and DEI (approximate location only, no CNIC, consent and withdrawal, decision support not a guarantee, newcomers not excluded, restrictions only after a human decision, data-protection obligations to confirm with the supervisor) | Project vision; DEI and ethical/legal statements | S3 |
| 2 Research and existing solutions | Comparison of existing products against project criteria (proposal §4 is the starting point); gap; CCP mapped to the Seoul Accord characteristics; research-to-design decisions | Research on related ideas/products | S3 (2.2 to 2.4), S2 (2.6, 2.8) |
| 3 Proposal feedback and iteration plan | Form 10 register; four-iteration strategy; iteration 1 and 2 plans; work breakdown; progress against the overview's week milestones; deviations (no interviews; locality build timing) with justification | Software development plan | S3 |
| 4 Software requirements | Prioritised use case list; core use case diagram; dressed core use cases; SSDs; FRs by module; NFRs with numbers; Given/When/Then acceptance criteria; traceability matrix opened | Use cases, use case diagram, SSD, SRS; wireframes and UI screens | all (own areas), S3 (diagrams) |
| 5 System design | Layer and component diagrams; REST interface table; ADRs (event sourcing vs CRUD plus audit table, rule-based detector vs trained model, config-driven parameters); design evolution since proposal; domain model; ERD and data dictionary; state machine; sequence diagrams; dispute activity diagram; deployment diagram | Structure design, behaviour design, DB representation, deployment diagram | S1, S2, S3 |
| 6 Iteration 1 | Objectives; selected use cases; files, classes and functions; algorithms with pseudocode and complexity; tools; coding conventions and static analysis setup; demo evidence (screens, URL, tag, CI run); setup and tool manual | Data structure and algorithm design; comments and naming conventions; static analysis; configuration/setup and tool manual | S1, S2 |
| 7 Testing and early validation | Strategy; levels and techniques; test cases with input/expected/actual; results from CI artifacts; edge and failure cases; defect log; current status | Test plan; unit test suites; system-level test suites | S1 (lead), all |
| 8 Project management evidence | Work done and remaining; ownership; repo, branch and tag evidence; Form 13 summary; dependency register; risk register; security and privacy; limitations | CI/CD | all |
| 9 Remaining plan | Iterations 2 to 4 from the module roadmap; evaluation plan with the overview's baselines and ablation list; deployment plan; timeline | — | S3, S2 (evaluation) |
| 10 Conclusion | Short summary of what exists and what's next | — | all |
| Appendices A to F | A register; B full requirements and brief use cases; C test cases; D repo screenshots and task log; E large diagrams; F supervisor meeting records | — | all |

The template has no slot for the setup manual; put a short version in 6.8 and keep the full one in the repo README. Give every document a control block with version, date, author and status, as the handbook asks (C.5.1).

## Evidence checklist

These are the items a supervisor checks before reading a line of code; missing disclosure alone zeroes the tool-use item.

- [ ] Form 10 action register in 3.2 and Appendix A, every action with status and an evidence link.
- [ ] Form 13 disclosure sheet signed by all three, each tool marked Support, Core-assist or Core-replacement.
- [ ] AI usage log with CCP-relevant entries saying how the output was checked; countersigned by the supervisor (Handbook C.8.4).
- [ ] Dependency register with licences (FastAPI, PostgreSQL, SciPy or whatever computes the interval, frontend libraries).
- [ ] GitHub: tag `v0.1.0-mid1`, closed "Iteration 1" milestone, board with assignees, PRs reviewed by another member, no secrets committed.
- [ ] Supervisor meeting records in Appendix F.
- [ ] Locality comparison and the six locality test cases (step A11), cited in the Form 10 entry on location.
- [ ] Synthetic data labelled synthetic in seed files, on screen and in the report.
- [ ] The report describes only what is built; deferred items are marked as deferred.
- [ ] Each member has rehearsed walking through their own files at function level.

## Risks and open questions

The risks most likely to cost marks are design running long and k-hop having no visible effect; both have a fix inside Part A.

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Design runs past a week | No live demo; implementation capped at 40% | Hard gate at D-15; anything unfinished becomes a dated design-debt item, not a delay |
| k-hop changes nothing in the decision | Panel asks "what does indirect trust change?" | Define its role in the decision table (A5) and demo ES-13 |
| Location action rests on design evidence only | Form 10 item marked Partly or carried forward | Cite the A11 comparison, spoofing test cases and privacy design in the register |
| Integration left to the end | No live demo | Slice A deployed by D-11 with stubs |
| S2 overloaded with three Module 5 components | Engine late | S1 takes the reciprocal-clustering check |
| No deployment target | No CD for mid | Decide by D-14 |
| Event schema changes later | Missing fields can't be rebuilt from old events | Freeze at A4; changes need all three to sign off |
| Thresholds look arbitrary | "How do you know the weights work?" | Config file with sources, labelled initial; sensitivity sweep in the FYP-2 plan |
| Code nobody can explain | Individual multiplier below 1.00 | Cross-review on every PR; walkthrough rehearsal |
| Scope creep into search or events | Core gets thinner | Not in iteration 1; needs a Form 12 change request |

**Open questions and missing files**

- Mid-eval date, and how Forms 2 and 3 combine into 20 marks.
- Does code from the proposal POC exist? Overview §5.11 mentions a Python policy module. Share the repo and I'll check it against this plan.
- The actual proposal feedback form; the overview summarises only three panel points.
- Claims C1 to C9 are referenced in the project instructions but defined nowhere except C1, C3 and C5.
- `11_assurance_engine/Algorithm_and_Data_Structure_Design.md` now exists (Student 2). Still missing: "Community Connect exclusions" (cited by NFR-S-07) and `phase2_assurance.py` (named in the Algorithm doc §11 but not in the project files).
- The project instructions still use the proposal's M1 to M9 as modules and say "Beta-Binomial"; update them to the overview's ten modules and the recency-weighted Beta posterior.
