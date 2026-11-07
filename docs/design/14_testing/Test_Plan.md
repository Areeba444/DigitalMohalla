# Digital Mohalla: Test Plan, Iterations 1 and 2 (design step A13; DA-16)

| Field | Value |
|---|---|
| Document | Design step A13: test plan for iteration 1 (FYP-1 Mid), with test cases in input / expected / actual form |
| Owner | Student 3 (A13, plan work division); suites are owned as in §4. Drafted during integration by Student 1; **Student 3 to review** (A14). Report chapter 7 lead: Student 1 |
| Version | 2.0 draft, 7 November 2026 (DA-16, Student 3, drafted with Claude Code; review by Student 1 pending): iteration 2 suites 20 to 31 (§4.1) and test cases TC-110 to TC-169 (§6.10), in input / expected / actual form; the plan's suites 19 to 30 are numbered 20 to 31 here because suite 19 is already Mobile UI; entry and exit criteria for the iteration 2 gates (§5.1). v1.3, 13 October 2026. v1.3: Android only, no iOS device (team decision 13 October, D15); gap UI-1 resolved (the borrower's new-request and request-status screens were built in Slice A); the tools in §3 are a guide, each added only when a test first needs it. v1.2: aligned with the team's wireframes W1–W7 (`13_wireframes/`): one mobile app for every role, so no web console; new suite 19 (mobile UI, TC-100 to TC-107); wireframe gaps and deviations listed in §6.9. v1.1, 12 October 2026: test types named and scoped (§2.1); regression policy (§11); alpha in scope and beta out of scope (§12); new suites 16 (handover, return, outcome feed), 17 (API security) and 18 (smoke, split out of suite 15); traceability gaps for FR-B-06, B-10, B-11, B-13, B-15, T-01, N-03 and NFR-D-01 closed; mobile tooling (Jest, React Native Testing Library, Maestro) replaces Playwright; device check for NFR-D-05. v1.0, 11 October 2026: first baseline |
| Status | Baseline for Part B. Design-time checks have run (§8); implementation tests run from Slice A onwards |
| Baseline | Iteration 1 plan ("Test plan for iteration 1", CI/CD), FR/NFR v1.3 (Part B verification column, Part E acceptance criteria), Use Cases v1.3, A3 transition table, ADR-0001 to ADR-0008, fixtures v1.1, `04_deployment/Deployment_Design.md`, the D-15 stack (Expo / React Native app, FastAPI, PostgreSQL 16) |
| Files | this plan; `transition_test_matrix.csv` (suite 1 oracle, generated); `scenario_fixtures_iteration1.json` (suites 6, 7, 9, 11, 12); `verify_fixtures.py` and `fixture_verification_results.md` (oracle and its results); `verify_design.py` (design consistency and notation checks) |
| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |

## 1. Purpose and scope

The plan tests the iteration-1 core:

- the request-to-return loop (Module 3);
- the assessment engine (Module 5);
- dispute and hold resolution (Module 9);
- the scenario suite (Module 10);
- minimal accounts (Module 1, login only).

Locality is tested at design level (`12_locality/`, 18/18 cases). The locality method is tested as code only if the D-11 gate builds it.

**Out of scope for iteration 1** (scope table of the plan): scheduler jobs (expiry, no-show, reminders, overdue disputes: T15, T19, T24, I01 to I06), extensions, counter-offers, chat (G1), appeals and reversals, notifications beyond the stub, search, reviews other than the seeded ones, and the evaluation datasets. Test cases for these are marked "It. 2" or "It. 3" and are not run.

**Items under test:**

| Item | Where |
|---|---|
| Backend (FastAPI) | `backend/` |
| Database schema | `06_data_model/schema.sql` v2.3 |
| Engine configuration | `Assurance_Engine_Config_Draft.json`, 1.1.0-iteration1-draft |
| Mobile app (Expo / React Native) for every role: lender W1–W2, handover and return W3a–W4, dispute W5, moderator W6–W7 | `13_wireframes/` (PNG screens and `Wireframes_Iteration1_Engineering_Annotations.md`) |
| Deployed instance | `04_deployment/` |

## 2. Strategy

1. **The design is the oracle.** Every expected result comes from a baselined artefact: the A3 transition table (suite 1), the A5 decision table and fixtures (suites 6, 7, 9, 11, 12), the ADRs, and the FR acceptance criteria (FR/NFR Part E). No expected value is invented in test code.
2. **Push checks down.** Rules the database can enforce are tested at the database level and again through the API: the transition table, the overlap constraint, the append-only log and decision-table consistency. The domain layer (transition table, replay, engine mathematics, policy) does no I/O, so it is unit-tested without a database (A8 layer rules).
3. **Failure and edge cases are first-class.** Every suite has at least one negative case, and the demo shows one failure per presenter (plan, demo script).
4. **Everything runs in CI.** Suites 1 to 7, 9 to 14, 16, 17, the build smoke of 18 and the component tests of 19 run on every PR (`ci.yml`), and a red check blocks the merge (NFR-D-04). Suite 8 and the performance part of suite 15 run on demand and at the freeze, with the config version and raw output saved.
5. **Separation of duties.** The scenario fixtures are for correctness only. The future held-out attack generator lives in a separate package, written by someone other than the detector's author (Student 3, Module 10).

### 2.1 Test types and where they apply

| Test type | In iteration 1? | How it is done here | Suites / cases |
|---|---|---|---|
| **Unit** | Yes | pytest on the domain layer (no database), including property-based tests with Hypothesis; Jest + React Native Testing Library for the app's screens and components | 1, 6, 7, 9, 12, 19; TC-16, TC-39, TC-74 to TC-77, TC-100 to TC-107 |
| **Integration** | Yes | API + PostgreSQL in CI (service container with `btree_gist`); API contract test against the OpenAPI spec | 2 to 5, 10, 13, 14, 16; TC-78 |
| **Acceptance** | Yes | Scenario suite: state, rule, lifecycle state and explanation must all match | 11 |
| **Regression** | Yes | The automated suites rerun on every PR, plus triggered reruns and defect-pinned tests (§11) | §11 |
| **Security** | Yes | Authorisation and audit (4, 5), privacy (14), API security (17), static and dependency scans in CI | 4, 5, 14, 17 |
| **Smoke** | Yes | Three levels: every PR build, after every deploy, before every demo | 18 |
| **Performance** | Yes (reported, one gate) | k sweep and transition-commit latency with the config version | 8, 15 |
| **System** | Yes | The full demo story on the deployed instance; Maestro flows over the W1–W7 screens on an Android phone | 15, 19 |
| **Alpha** | Yes, as an internal team session | Bug-bash on the deployed release candidate, with roles swapped | §12 |
| **Beta** | **No: FYP-2 pilot** | Real residents need consent, the locality method, the scheduler and confirmed data-protection obligations; none exist in iteration 1 | §12 |
| **Usability** | No: FYP-2 | NFR-U-02 to U-04 are measured in the pilot | §12 |

## 3. Test levels, techniques and environment

| Level | What | Technique | Tooling | Environment |
|---|---|---|---|---|
| Unit | Domain classes: transition table, aggregate and replay, Beta posterior, k-hop search, manipulation score, decision policy, config loader, explanation builder; app components | State-transition testing, boundary values, decision tables, known values, property-based tests | pytest, Hypothesis, coverage (floor 80% on engine and lifecycle packages); Jest + React Native Testing Library | CI runner, no database |
| Integration | API + PostgreSQL: lifecycle, handover and return, outcome feed, concurrency, authorisation, append-only log, disputes and holds, privacy, API contract | Use-case paths, concurrency harness, negative and tamper tests, decision table by actor, contract checks | pytest + httpx; Postgres 16 service container with `btree_gist`; Schemathesis (OpenAPI) | CI runner |
| Acceptance | Scenario suite ES-01 to ES-06 and ES-13 | Fixture-driven; state **and** explanation must match | pytest, `scenario_fixtures_iteration1.json` | CI runner |
| Security | Authentication, authorisation, input handling, secrets, dependencies, deployed host | Negative tests, fuzzing, static and dependency scans | pytest; Schemathesis; bandit, pip-audit, gitleaks; Trivy (images); npm audit (app) | CI runner; deployed host |
| Smoke | Build, deploy, demo readiness | Shallow end-to-end checks | pytest smoke marker; `cd.yml` smoke step; Maestro smoke flow | CI; AWS host; demo laptop |
| Performance | k sweep (k = 1 to 4), transition commit latency | Benchmark, load test | pytest-benchmark; Locust | CI on demand; deployed instance at the freeze |
| System | Full loop on the deployed instance; app on real devices | End-to-end run; device check | Maestro flows on an Android device (Expo Go or an EAS build); manual checklist | AWS host; phones |
| UI | The mobile screens W1–W7: annotated elements present, bound to API data, correct per role | Component tests with a mocked API; Maestro flows; review against NFR-U-01 and the wireframe annotations | Jest + React Native Testing Library; Maestro; checklist from `Wireframes_Iteration1_Engineering_Annotations.md` | CI (component tests); phones (flows, review) |
| Static | Lint, types | Linters, type checks | ruff, mypy (backend); ESLint, TypeScript strict (app) | `ci.yml` |

The tools above are a guide, not a shopping list: each is added only when a test first needs it, and recorded in the dependency register at that point.

**Test data.** Synthetic users only, flagged `is_synthetic` and shown as synthetic. They are seeded by a seed script and reset with the seed-reset script; the fixtures carry their own inputs. No real personal data, location or identity documents are used (NFR-PR-01, NFR-PR-05, NFR-S-07).

## 4. Suites

The plan's "Test plan for iteration 1" table, extended with owners, gates and suites 16 to 18.

| # | Suite | Level | Technique | Pass condition | Traces to | Owner | Slice / gate |
|---|---|---|---|---|---|---|---|
| 1 | Transition matrix | Unit + integration | State-transition testing over all 294 (state, event) pairs of `transition_test_matrix.csv` | 31 valid pairs (34 triples) pass with their guard satisfied; all 263 other pairs are rejected with 409 and an audit entry | FR-B-08, NFR-R-02 | S1 | A / D-11 |
| 2 | Replay | Integration + property | Rebuild each test stream in `stream_seq` order; random valid sequences | Rebuilt state equals the projection for every test transaction | FR-B-09, NFR-R-03 | S1 | A / D-11 |
| 3 | Double booking | Integration | N parallel acceptances for overlapping dates, repeated | Exactly one commits, every run; the others end DECLINED "dates taken" | FR-B-05, FR-B-10, NFR-R-01, ADR-0002 | S1 | A / D-11 |
| 4 | Authorisation | Integration | Decision table by actor and role over every command | Only permitted actors transition; a moderator acts only in their community; every refusal is 403 and logged | NFR-S-02, NFR-S-03 | S1 | A / D-11 |
| 5 | Append-only log | Integration | Negative and tamper tests | UPDATE and DELETE fail; an edit made with triggers disabled is detected by the hash chain | FR-M-05, NFR-S-05 | S1 | A / D-11 |
| 6 | Beta posterior | Unit | Known values and boundaries | Zero history gives Beta(1,1); 18 and 2 give Beta(19,3); weights about 0.96 and 0.25 at 10 and 360 days; the interval narrows with evidence; fixture intervals match | FR-T-02, FR-T-03 | S2 | B / D-8 |
| 7 | k-hop propagation | Unit | Hand-worked graphs (A5 example, ES-13) | Expected paths, decay, one path per first hop, noisy-OR, ρ ≤ 0.6, nothing beyond k, cycles safe | FR-T-04, ADR-0006 | S1 | B / D-8 |
| 8 | k sweep | Performance | Benchmark at k = 1 to 4, seeded scale | Latency and coverage reported with the config version (not gated, NFR-P-03) | NFR-P-03 | S1 | B |
| 9 | Policy rules | Unit + property | Decision table (Algorithm doc §6) with the policy unit fixtures | Rule order R1 … R9 holds; an open dispute first; exactly one state; indirect evidence alone never gives SUFFICIENT; corroborated level 4 holds, an uncorroborated score ≥ 60 does not; no restriction without a human | FR-T-01, FR-T-06, ADR-0007, ADR-0008 | S2 | B / D-8 |
| 10 | Engine failure | Integration | Fault injection (timeout above 2,000 ms, exception) | HELD_FOR_REVIEW with `engine_failure`, failure logged, no assessment row, no assurance state | FR-T-07, NFR-R-04 | S2 | B / D-8 |
| 11 | Scenarios ES-01 to ES-06, ES-13 | Acceptance | Synthetic fixtures | State, rule, lifecycle state and explanation all match; 7 of 7 at Mid-1 | NFR-Q-01 | S3 (S2 fixtures) | B, C / D-8, D-5 |
| 12 | Dense legitimate group | Unit | Negative test | A family-style reciprocal group (fixture PU-02) stays below the moderator-review threshold | FR-T-05 guard, ADR-0007 | S2 | C / D-5 |
| 13 | Dispute and hold resolution | Integration | Use-case paths (UC-B12, D6, I4) | A dispute closes via `dispute_resolved` and the outcome counts; a withdrawal restores the previous state; each hold ends cleared, with safeguards, or declined, as its hold reason allows | FR-B-16, FR-B-17, FR-T-10, FR-T-11, ADR-0003, ADR-0004 | S3 | C / D-5 |
| 14 | Privacy | Integration | Negative test over the API and logs | No response or log line contains an address, coordinates or a CNIC field; uploads keep no location metadata | NFR-PR-01, NFR-PR-02, NFR-S-07 | S1 | C / D-5 |
| 15 | Performance and system | Performance, system | Load test; end-to-end demo story; device check | P95 of transition commits recorded (target ≤ 500 ms); the full loop passes on the deployed instance; the app runs on one Android device | NFR-P-04, NFR-D-05, demo script | S3 (S1 latency) | Freeze |
| **16** | **Handover, return and outcome feed** | Integration | Use-case paths (UC-B7, UC-B8) | Both confirmations (and the deposit record when required) are needed for ACTIVE; return closes via `transaction_closed`; late returns are recorded; the outcome appears in the next assessment and a disputed one does not; every assessment carries `config_version`; every event has the frozen fields | FR-B-06, FR-B-11, FR-B-13, FR-B-15, FR-N-03, NFR-D-01 | S1 | A (handover, return) to B (outcome feed) |
| **17** | **API security** | Integration + static | Negative tests, fuzzing, scans | TC-80 to TC-88 pass | NFR-S-01, S-02, S-03, S-04, S-06, NFR-D-03 | S1 | A to C |
| **18** | **Smoke** | Build, deploy, demo | Shallow end-to-end checks | TC-90 to TC-92 pass at their level | NFR-D-03, NFR-D-04 | S3 (CI part S1) | A onward |
| **19** | **Mobile UI (W1–W7)** | Unit (components) + system (Maestro) | Screen-by-screen checks against the wireframe annotations, with real or mocked API responses | Each screen shows its annotated elements from API data, offers only the actions its role and state allow, and never shows a single trust number | FR-B-10, B-11, B-13, B-16, B-17, FR-T-08, T-10, T-11, NFR-U-01, NFR-S-03 | S3 | A (W2–W4), B (W1), C (W5–W7) |

### 4.1 Iteration 2 suites (v2.0)

The iteration 2 plan lists new suites 19 to 30. Suite 19 already exists (Mobile UI, v1.2), so they are numbered **20 to 31** here; the plan's number is given in brackets. Suites 1, 11 and 14 are extended. All 19 existing suites stay green in CI.

| # | Suite | Level | Technique | Pass condition | Traces to | Owner | Slice |
|---|---|---|---|---|---|---|---|
| 1 (regenerated) | Transition matrix | Unit + integration | State-transition testing over the regenerated matrix | Every new valid pair (T25a, T25b, T25c; reminders and extensions) passes; every other pair is rejected and logged | FR-B-08, ADR-0009 | S1 | 2 |
| 11 (extended) | Scenarios ES-01 to ES-13 | Acceptance | Synthetic fixtures (iteration 1 and 2 files) | 13 of 13: state, rule, lifecycle state and explanation facts match | NFR-Q-01 | S3 (S2 reviews fixtures) | 2, 3 |
| 14 (extended) | Privacy on every new endpoint | Integration | Negative tests over responses, logs and audit rows | No coordinates, address or CNIC anywhere, search and its log included; the locality request body is never logged | NFR-PR-01, NFR-PR-02, NFR-S-07 | S1 | 2, 3 |
| 20 (plan 19) | Scheduler | Integration | Rerun and parallel-run tests | A rerun or an overlapping run changes no state and sends no duplicate notice | FR-B-18, NFR-R-05 | S1 | 2 |
| 21 (plan 20) | Locality at runtime | Integration | The six A11 cases through the real service | The six cases and 18 checks pass; no outcome is ever a rejection | FR-A-07, FR-A-08, NFR-Q-04 | S1 | 2 |
| 22 (plan 21) | Membership | Integration | Use-case paths UC-A3, UC-A4; concurrency | Duplicates blocked; wrong-community moderator refused; concurrent decisions not reapplied | FR-A-09, FR-A-10, FR-A-11 | S1 | 2 |
| 23 (plan 22) | Notifications | Integration | Dedupe and access tests | Dedupe holds; a member sees only their own | FR-C-02 | S2 | 2 |
| 24 (plan 23) | Reviews | Integration | Use-case paths UC-D1; boundaries of the windows | Only parties to a completed loan, once each; flags set by the moderator path; edit window enforced | FR-T-09 | S2 | 2 |
| 25 (plan 24) | Detection | Unit | Hand-made cases defined by the owner | S2, S3 and S5 fire on their cases; the C3 family group stays below a hold | FR-T-05, ADR-0007 | S2 | 3 |
| 26 (plan 25) | Dispute closure | Integration | From each dispute stage and each possession | No phantom return; an occupied item's dates are never released | FR-B-16, FR-T-11, ADR-0009 | S3 | 2 |
| 27 (plan 26) | Appeal and reversal | Integration | Use-case paths UC-I4 4b, 4c | The second moderator differs from the first; both decisions kept; outcomes flagged and excluded | FR-T-11, ES-11 | S3 | 2 |
| 28 (plan 27) | Uploads | Integration | Negative tests and metadata checks | EXIF stripped; wrong type or size gives 422 (TC-59, TC-85) | NFR-S-06, NFR-PR-01 | S3 | 2 |
| 29 (plan 28) | Audit | Integration | Filter, masking and tamper tests | Filters, masking, tamper warning; each view is itself logged | FR-M-05, NFR-S-05, NFR-S-03 | S3 | 3 |
| 30 (plan 29) | Search behaviour | Integration | Eligibility, fallback and fairness checks | No result from another community, an unpublished item or a blocking lender; keyword results when the model is down; a new lender is never ranked below an otherwise equal lender for lack of history; every result has a reason line | FR-S-01 to S-04, NFR-R-04 | S2, S1 | 2, 3 |
| 31 (plan 30) | Search quality and logging | Evaluation + integration | Frozen labelled query set (DA-25) | Precision@5, recall@10 and NDCG@10 recorded for keyword and hybrid; the log holds queries, impressions and clicks and no location | FR-S-05, NFR-Q-05, NFR-P-01, NFR-P-02 | S3 | 3 |

**Owed from iteration 1** (kept with their IDs): TC-70 duplicate request, TC-61 transition P95 (NFR-P-04), full assessment P95 (NFR-P-03, suite 8), TC-73 Android device test, TC-91 post-deploy smoke test, TC-59 and TC-85 (now in suite 28).

## 5. Entry, exit and suspension criteria

| Gate | Entry | Exit (pass) |
|---|---|---|
| Every PR | Builds; lint and type checks clean | Regression set green (§11); smoke TC-90; review by a member who did not write the change |
| D-11 (Slice A) | Lifecycle on stubs deployed | Suites 1 to 5 green; suite 16 handover and return cases (TC-64 to TC-68, TC-70, TC-72) green; TC-80 to TC-83 and TC-87 green; UI TC-101 to TC-104 green; TC-91 passes after the first deploy |
| D-8 (Slice B) | Engine integrated | Suites 6, 7, 9, 10 green; outcome feed TC-69 and TC-71 green; lender evidence screen TC-100 green; ES-01, ES-02, ES-03, ES-06 and ES-13 pass with state and explanation |
| D-5 (feature freeze) | Human loop integrated | Suites 12 to 14 and 17 green (TC-59 and TC-85 deferred, D20); UI TC-105 to TC-107 green; ES-04 and ES-05 pass; alpha session held (§12); tag `v0.1.0-rc1` |
| Freeze (D-5 to D-0) | rc1 deployed | Full regression run saved (§11); suite 15 run on the deployed instance; TC-92 before each rehearsal and the demo; no open severity-1 or severity-2 defect; tag `v0.1.0-mid1` |

### 5.1 Iteration 2 gates (v2.0)

| Gate | Entry | Exit (pass) |
|---|---|---|
| Design gate (10 November) | Design artefacts drafted | Every new suite has its cases in §6.10; the schema change (migration 0002) signed by all three students |
| Slice 2 | Scheduler, locality, membership, disputes, appeals, uploads, reviews and keyword search built | Suites 1 (regenerated), 20 to 24, 26 to 28 and 30 (keyword part) green; ES-07, ES-08, ES-09, ES-10 and ES-11 pass; no open severity-1 or severity-2 defect; TC-91 on the deployed instance |
| Slice 3 | Detection, audit screen, meaning-based search and evaluation built | Suites 25, 29, 30 and 31 green; 13 of 13 scenarios (NFR-Q-01); suite 14 over every new endpoint |
| Final release | Release candidate deployed | Criteria of `14_testing/Test_Deployment_Rollback_Handover_Plan.md` §3, including the rollback rehearsal |

Testing of a slice is suspended when the deployed smoke test (TC-91) fails. It resumes after the rollback (`04_deployment/Deployment_Design.md` §4) and a smoke rerun.

## 6. Test cases (input / expected / actual)

"Actual" records the latest result:

- **"Design-verified":** the expected behaviour is already enforced and tested at the database or oracle level (§8); the implementation test still has to be written in Part B.
- **"Not run":** the code does not exist yet.

### 6.1 Lifecycle and data integrity (suites 1 to 5)

| ID | Suite | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-01 | 1 | Each of the 294 rows of `transition_test_matrix.csv`, issued as a command | VALID rows succeed when their guard holds; REJECT rows return 409, append no event and write an audit entry with the reason | Design-verified (schema: 34-row model check, CSV check, invalid-transition checks) | FR-B-08, NFR-R-02 |
| TC-02 | 1 | A booking in COMPLETED; the lender sends `request_accepted` | 409 "invalid transition"; audit entry REJECTED | Design-verified | FR-B-08 AC |
| TC-03 | 1 | A request held with `locality_inconclusive`; a moderator clears it | Next state LOCALITY_CHECKED, never ASSESSED (T09) | Design-verified | FR-B-08 AC, ADR-0003 |
| TC-04 | 1 | A request held with `manipulation_risk`; a moderator clears it to LOCALITY_CHECKED | Refused; only ASSESSED is allowed (T11) | Design-verified | ADR-0003 |
| TC-05 | 1 | A booking in RETURNED; a party opens a dispute | Refused (decision D4) | Design-verified | FR-B-16 |
| TC-06 | 1 | A command carrying a stale `stream_seq` | 409 stale; nothing appended | Design-verified | ADR-0002 |
| TC-07 | 2 | A transaction driven through the happy path (8 events) | `replay_state()` equals the projection; `request_created` carries the item and dates | Design-verified | FR-B-09 AC, NFR-R-03 |
| TC-08 | 3 | Two ASSESSED requests for overlapping dates; both lenders accept at once (3 connections × 5 rounds) | Exactly one ACCEPTED each round; the other DECLINED "dates taken" | Design-verified (race test) | FR-B-05 AC, NFR-R-01 |
| TC-09 | 3 | Two overlapping pending requests | Both are created (soft hold); accepting one declines the other | Design-verified | ADR-0001 |
| TC-10 | 4 | A lender who does not own the item tries to accept | 403, logged | Design-verified (impersonation check) | NFR-S-02 |
| TC-11 | 4 | A moderator of another community decides a case | 403, logged | Design-verified | NFR-S-03 |
| TC-12 | 4 | A party to the loan tries to decide its case as moderator | Refused | Design-verified | FR-T-11 |
| TC-13 | 5 | `UPDATE` or `DELETE` on `lifecycle_event` and on `audit_log` as the application role | Refused | Design-verified | NFR-S-05 |
| TC-14 | 5 | An event edited with the triggers disabled | `verify_event_chain()` reports the stream as tampered | Design-verified | FR-M-05 AC |
| TC-15 | 3 | An ASSESSED request and an authorised lender; two other pending requests, one overlapping and one not | The request is ACCEPTED and its dates blocked; the overlapping request is DECLINED "dates taken"; the other stays pending. The chat thread of the acceptance criterion is not built in iteration 1 (G1, iteration 3) | Design-verified (DB path); API not run | FR-B-10 AC |
| TC-16 | 2 | Hypothesis generates random valid event sequences from the transition table | For every sequence, replay equals the projection, and every prefix is a valid state | Not run | FR-B-09, NFR-R-03 |

### 6.2 Assurance engine (suites 6 to 12)

| ID | Suite | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-20 | 6 | No outcomes | Beta(1,1), mean 0.5, 90% CI [0.05, 0.95] | Oracle-verified (ES-01) | FR-T-02 AC |
| TC-21 | 6 | 18 successes and 2 failures, all today | Beta(19,3), mean 0.864 | Not run | FR-T-02 |
| TC-22 | 6 | One success 10 days ago, one 360 days ago, half-life 180 days | Weights 0.962 and 0.25 | Not run | FR-T-03 AC |
| TC-23 | 6 | A disputed outcome and an unconfirmed one | Both ignored until resolved | Not run | FR-T-03 |
| TC-24 | 6 | Fixture intervals ES-02 to ES-06 | Lower and upper 90% bounds equal the Beta quantiles (e.g. ES-02 [0.752, 0.995]) | Oracle-verified (13/13) | FR-T-02 |
| TC-25 | 7 | The A5 hand-worked 8-node graph at k = 3 | 3 selected paths (q = 0.54, 0.2195, 0.21), I = 0.7164, ρ = 0.6 (capped) | Verified by `generate_khop_example.py` | FR-T-04 AC |
| TC-26 | 7 | Same graph, k = 1 to 4 | ρ = 0, 0.424, 0.600, 0.600; nothing beyond k | Verified by `generate_khop_example.py` | FR-T-04 |
| TC-27 | 7 | ES-13 edges derived from outcomes (ADR-0006) | Edge weights 0.801, 0.777, 0.658, 0.648; paths q = 0.369, 0.352; I = 0.591; ρ = 0.394 | Oracle-verified | FR-T-04, ADR-0006 |
| TC-28 | 7 | A graph with a cycle and a self-loop | Search terminates; no path repeats a node | Not run | FR-T-04 |
| TC-29 | 9 | Fixture PU-03: open dispute and a strong history | R1, ACTIVE_DISPUTE, ASSESSED (not held) | Oracle-verified; DB check | D12 |
| TC-30 | 9 | Fixture PU-01: S1 = 1.0, S4 = 0.2 (score 68) | Level 3, R5, REVIEW_RECOMMENDED, not held | Oracle-verified; DB check | ADR-0007, FR-T-06 AC |
| TC-31 | 9 | Fixture PU-04: no history, high-value item | R3, INSUFFICIENT_EVIDENCE, not held | Oracle-verified | FR-T-02 |
| TC-32 | 9 | Fixture PU-05: sparse old history, no paths | R6_SPARSE, INSUFFICIENT_EVIDENCE | Oracle-verified | ADR-0008 |
| TC-33 | 9 | Fixture PU-06: strong history, medium value, risk level 2 | R8, SUFFICIENT_EVIDENCE with safeguards | Oracle-verified | FR-T-06 |
| TC-34 | 9 | Hypothesis: any input where only indirect evidence is strong | Never SUFFICIENT_EVIDENCE (R7 and R8 need n_eff ≥ 3 from direct evidence) | Not run (property test) | FR-T-04, Overview §5.11 |
| TC-35 | 9 | An assessment row whose rule, state, decision or hold reason disagree | Refused by `assessment_rule_ck` | Design-verified | FR-T-06 |
| TC-36 | 10 | Engine stub sleeps 2,500 ms | HELD_FOR_REVIEW `engine_failure`; failure logged; no assessment row | Design-verified (DB path); not run (timeout) | FR-T-07 AC |
| TC-37 | 10 | Engine raises an exception | As TC-36 | Not run | FR-T-07, NFR-R-04 |
| TC-38 | 12 | Fixture PU-02: family group, S1 = 0.83, S4 = 0.10 | Score 53.8, level 3; not held | Oracle-verified | ADR-0007 |
| TC-39 | 9 | Hypothesis: random valid engine inputs (direct, indirect, risk, context) | Exactly one of the four assurance states, with confidence, direct and indirect evidence, signals, safeguards, explanation and rule; no single trust number in the explanation | Not run (property test) | FR-T-01 AC |

### 6.3 Scenario suite (suite 11, NFR-Q-01)

Each scenario passes only if the assurance state, the rule, the lifecycle state **and** the explanation match. The explanation check asserts the listed facts, not the exact wording.

| ID | Scenario | Expected state / lifecycle | Rule | Explanation must contain | Actual |
|---|---|---|---|---|---|
| TC-40 | ES-01 new user | INSUFFICIENT_EVIDENCE / ASSESSED | R3 | "Insufficient verified history; lender review required"; wide interval; no negative wording | Oracle-verified |
| TC-41 | ES-02 reliable | SUFFICIENT_EVIDENCE / ASSESSED | R7 | 90% CI [0.752, 0.995]; effective evidence 9.5 | Oracle-verified |
| TC-42 | ES-03 recent resolved dispute | REVIEW_RECOMMENDED / ASSESSED | R6_DISPUTE | the resolved dispute; safeguards | Oracle-verified |
| TC-43 | ES-04 colluding group | REVIEW_RECOMMENDED / HELD_FOR_REVIEW (`manipulation_risk`) | R2 | both signals with evidence (S1 = 1.0, S4 = 0.92), score 96.8, "not proof"; case opened | Oracle-verified |
| TC-44 | ES-05 retaliatory review | SUFFICIENT_EVIDENCE / ASSESSED | R8 | the review flagged as suspected retaliation and down-weighted | Oracle-verified |
| TC-45 | ES-06 high value, weak evidence | REVIEW_RECOMMENDED / HELD_FOR_REVIEW (`high_value_low_confidence`) | R4 | similarity 0.25; lower bound 0.30 | Oracle-verified |
| TC-46 | ES-13 community paths | REVIEW_RECOMMENDED / ASSESSED | R9 | both paths with weights; ρ 0.39; "without these paths: INSUFFICIENT_EVIDENCE" | Oracle-verified |
| TC-47 | ES-13 counterfactual (no paths) | INSUFFICIENT_EVIDENCE / ASSESSED | R6_SPARSE | sparse history, no community support | Oracle-verified |

### 6.4 Human loop, privacy, performance and system (suites 13 to 15)

| ID | Suite | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-50 | 13 | An ACTIVE loan; the lender raises a dispute with photos | DISPUTED; `previous_state` stored; case opened; deposit record frozen | Design-verified | FR-B-16 AC |
| TC-51 | 13 | An open dispute; the raising party withdraws | Previous state restored (`dispute_withdrawn`); case WITHDRAWN | Design-verified | FR-B-17 AC |
| TC-52 | 13 | An open dispute; the other party tries to withdraw | Refused | Design-verified | FR-B-17 |
| TC-53 | 13 | A moderator resolves a dispute with a reason | COMPLETED via `dispute_resolved`; decision logged; resolved outcome recorded as evidence | Design-verified | FR-T-11 AC |
| TC-54 | 13 | A decision without a reason | Refused | Design-verified | FR-T-11 |
| TC-55 | 13 | An engine-failure hold; a moderator imposes safeguards | Refused (UC-I4 3c); "clear" re-runs the assessment from LOCALITY_CHECKED | Design-verified | ADR-0003 |
| TC-56 | 13 | A request cancelled while held | CANCELLED; case WITHDRAWN without a decision | Design-verified | UC-B6 *a, D8 |
| TC-57 | 13 | Two moderators decide the same case at once | One decision applied; the other sees the current state, nothing applied | Not run | UC-I4 4a |
| TC-58 | 14 | Every API response of the seeded loop | No address, coordinate or CNIC field | Design-verified (catalogue scan: no such columns); API not run | NFR-PR-01, NFR-S-07 |
| TC-59 | 14 | An uploaded photo with EXIF GPS data | Refused unless metadata is stripped (`metadata_stripped`) | Deferred to iteration 2 (D20: no upload storage yet) | NFR-PR-01 |
| TC-60 | 14 | A borrowing request payload | Contains no location fields; locality read from the stored A11 result | Design-verified (A11, D13) | FR-B-07 |
| TC-61 | 15 | 200 transition commits under load | P95 ≤ 500 ms recorded with the config version | Not run | NFR-P-04 |
| TC-62 | — | (v1.0: CD smoke and rollback) | Moved to suite 18 as TC-91 | — | — |
| TC-63 | 15 | The demo story on the deployed instance (plan demo 2.1 to 2.6), full length | Every step behaves as scripted | Not run | Demo script |
| TC-73 | 15 | The app on one Android phone (Expo Go or EAS build); Maestro flows over W1–W7 for each role | The flows complete; screens readable at the wireframes' 390-pt width; no crash | Not run | NFR-D-05 |

### 6.5 Handover, return and outcome feed (suite 16)

| ID | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|
| TC-64 | ACCEPTED booking; the lender submits the checklist; the borrower confirms; the deposit is recorded | ACTIVE with a due date; `handover_confirmed` logged | Design-verified (DB path); API not run | FR-B-11 AC |
| TC-65 | As TC-64, but a required deposit is not recorded | Stays ACCEPTED | Design-verified (DB path); API not run | FR-B-11, UC-B7 3b |
| TC-66 | Only the lender has confirmed, or the borrower confirmed before the lender's latest checklist | Stays ACCEPTED | Design-verified (confirmation order) | FR-B-11, UC-B7 3 |
| TC-67 | ACTIVE loan returned on time; both parties confirm | RETURNED, then COMPLETED via `transaction_closed`; on-time outcome sent to the engine; booking RELEASED; deposit release recorded | Design-verified (DB path); engine feed not run | FR-B-13 AC, FR-B-15 |
| TC-68 | Return after the due date | COMPLETED with a late outcome recorded | Design-verified | FR-B-13 AC |
| TC-69 | A closed loan, then a new request from the same borrower; a second loan of the same borrower is DISPUTED | The new assessment's direct evidence includes the closed loan's outcome; the disputed loan's outcome is not counted until `dispute_resolved` | Not run (Slice B) | FR-B-15 AC, FR-T-03 |
| TC-70 | An identical pending request from the same borrower for the same item and dates | Rejected as a duplicate (UC-B5 3b) | Not run | FR-B-06 AC |
| TC-71 | All assessments stored after the scenario run | 100% carry `config_version`, equal to the loaded config | Design-verified (NOT NULL; same version on the event); run not done | NFR-D-01 |
| TC-72 | All events of a full loop | Every event has the frozen fields and `schema_version`; each `payload` matches the event catalogue | Design-verified (creation data); full check not run | FR-B-09, FR-N-03 |

### 6.6 Additional unit and contract tests

| ID | Level | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-74 | Unit | The engine config file; a copy with a missing or out-of-range parameter | Loads with its `config_version`, which every assessment then stores; a missing or invalid parameter fails at start-up instead of falling back to a default | Not run | NFR-D-01 |
| TC-75 | Unit | Explanation builder on the fixtures | Asserts facts: state, interval, effective evidence, paths (ES-13), signals (ES-04), rule; never a bare number on its own | Not run | FR-T-08, NFR-U-01 |
| TC-76 | Unit | Outcome extractor on closings: on time, late, disputed, resolved, flagged | One outcome per subject and metric for confirmed closings; none for an open dispute; outcome after `dispute_resolved`; flagged ones excluded | Not run | FR-T-03, FR-B-15 |
| TC-77 | Unit | Item values 5,000, 5,001, 15,000, 15,001 PKR; similarity of category, value band and duration | Bands LOW, MEDIUM, MEDIUM, HIGH (config D14); similarity weight in (0, 1] | Not run | FR-T-03, D14 |
| TC-78 | Integration | Every endpoint of the A8 REST table, called with valid and invalid input; the mobile client regenerated from the OpenAPI spec | Each returns its documented status codes (200/201/401/403/404/409/422); CI fails if the spec changed without regenerating the client | Not run | FR-B-08, NFR-S-02 |

### 6.7 API security (suite 17)

| ID | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|
| TC-80 | No token, an expired token, a tampered token | 401; the attempt is logged | Not run | NFR-S-02 |
| TC-81 | A command body that sets `actor_id`, `authorisation` or `new_state` itself | Ignored: the actor comes from the session and the state from the transition table | Not run | NFR-S-02, FR-B-08 |
| TC-82 | A borrower requests another pair's transaction, assessment or case | 403 or 404; no data returned | Not run | NFR-S-03 |
| TC-83 | Stored passwords and log output after logins | Salted argon2 (or bcrypt) hashes only; no plaintext password or token in any log | Not run | NFR-S-01 |
| TC-84 | Schemathesis fuzzing against the OpenAPI spec: injection strings and malformed payloads in message, date and ID fields | 422 for bad input, never a 500; no database error text leaked | Not run | NFR-S-02 |
| TC-85 | Upload of a disallowed file type or an oversize file | Rejected with 422 | Deferred to iteration 2 (D20) | NFR-S-06 |
| TC-86 | Repeated failed logins | Throttled or locked temporarily (It. 2 if the lockout is not built in iteration 1) | Not run (It. 2) | NFR-S-04, FR-A-04 |
| TC-87 | CI scans: gitleaks (secrets), bandit, pip-audit, npm audit (app), Trivy (images) | No committed secret; no open high-severity finding | Not run | NFR-D-04, handbook |
| TC-88 | The deployed host | HTTPS only (HTTP redirects); no stack traces in responses; database port not reachable from outside | Not run | NFR-S-01, NFR-D-03 |

### 6.8 Smoke (suite 18)

| ID | Level | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-90 | Every PR (build smoke) | A fresh CI database | The backend boots; migrations apply to an empty database; the seed runs; `/health` returns 200; the app bundle builds | Not run | NFR-D-04 |
| TC-91 | After every deploy | The deployed instance (replaces v1.0 TC-62) | `/health`; log in as a seeded user; one scripted request reaches ASSESSED; on failure the previous tag is redeployed | Not run | NFR-D-03 |
| TC-92 | Before each rehearsal and the demo | Seed-reset, then demo steps 2.1 to 2.6 in fast form (Maestro smoke flow on a phone) | All pass; the local Compose fallback also starts. Step 2.1 needs the borrower's request screen, which is not yet wireframed (§6.9) | Not run | Demo script |

### 6.9 Mobile UI, screens W1 to W7 (suite 19)

The screens are the team's wireframes in `13_wireframes/` (PNG files and `Wireframes_Iteration1_Engineering_Annotations.md`). Component tests run in CI with a mocked API; the same checks run as Maestro flows on phones against the seeded backend. Every check uses values returned by the API, never values copied from the wireframe images.

| ID | Screen | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-100 | W1 Lender request with assurance summary | Assessments for ES-01, ES-02 and ES-13 from the API | Shows the borrower, dates and message; the assurance state as text; the 90% interval bar with the API's bounds (ES-01: 0.05 to 0.95); the manipulation band separate from the evidence; the safeguards list; for ES-13 the community paths; Accept and Decline enabled; counter-offer shown as unavailable (it. 2); no single trust number or rating anywhere | Not run | UC-B6 1–2, FR-T-01, FR-T-08, NFR-U-01 |
| TC-101 | W2 Lender decision and conflict | Accept chosen; decline chosen with and without a reason; the API answers 409 "dates taken" | The pre-warning says overlapping requests will be declined; decline works with an optional reason; on 409 the "dates taken" banner shows and the request is shown as DECLINED | Not run | UC-B6 3–6, 3a, 3c; FR-B-10; ADR-0001, ADR-0002 |
| TC-102 | W3a Handover inspection (lender) | ACCEPTED booking; photos recommended by the assessment; deposit required | The checklist and notes are editable; the photo slots are mandatory when recommended; "send for borrower review" stays disabled until they are filled; the deposit checkbox says record only; uploaded photos carry no location metadata; on a failed upload the app offers retry or "reduced evidence" | Not run | UC-B7 1–2, 2a; FR-B-11; NFR-PR-01 |
| TC-103 | W3b Handover confirmation (borrower) | The lender's record exists | The summary shows the lender's checklist, notes, photos and deposit record; "confirm receipt" moves the booking to ACTIVE with the due date; "I disagree" opens the dispute form (W5); confirming before the lender's latest checklist is not possible | Not run | UC-B7 3–4, 3a, 3b; FR-B-11 |
| TC-104 | W4 Return inspection | RETURN_INITIATED booking, returned on time and late | Handover baseline and return condition side by side; new damage highlighted; on-time or late computed from the due date the API returns; dual sign-off status shown; "agree and close" ends COMPLETED; "report damage" opens W5 | Not run | UC-B8 1–5, 3a, 4a; FR-B-13 |
| TC-105 | W5 Dispute form and progress | ACCEPTED, ACTIVE and RETURN_INITIATED bookings; a RETURNED booking; an open dispute | Reasons offered as in UC-B12 step 2 (damage, non-return, condition mismatch, no-show, **other**); evidence upload; the freeze warning; the case card after submit; "withdraw" shown only to the raising party; no dispute offered from RETURNED; an existing dispute is shown instead of a new form | Not run | UC-B12 1–5, 1a, 5b; FR-B-16, FR-B-17; ADR-0004 |
| TC-106 | W6 Moderator queue | Cases from two communities; DISPUTED and HELD_FOR_REVIEW cases; no moderator in one community | Only the moderator's own community is listed; disputes and holds appear in one feed; priority comes from the trigger type, never from a trust number; a case without a moderator is routed to an admin | Not run | UC-D6 2, 2a; UC-I4 1; FR-T-10; NFR-S-03 |
| TC-107 | W7 Case adjudication | A dispute case; holds with each hold reason; a second moderator deciding first | The event trail comes from the API in `stream_seq` order; claims and photos side by side; the decision needs a reason; only the options ADR-0003 allows for the case are offered (no "safeguards" for `engine_failure`); "already decided" shows the current state and applies nothing | Not run | UC-I4 1–4, 3c, 4a; FR-T-11; ADR-0003, ADR-0004; NFR-U-01 |

**Gaps and deviations to resolve with the wireframe owner (Student 3)**

| # | Finding | Effect on testing | Proposed resolution |
|---|---|---|---|
| UI-1 | No screen yet for the borrower's request and its status (UC-B5 steps 1–3 and 6, held and engine-failure states) | The request is created through the API in tests; TC-92 step 2.1 and the alpha "happy path" need the screen | **Resolved in Slice A:** new-request and request-detail screens in `frontend/src/app/(resident)/` |
| UI-2 | No screen yet for the admin audit log (UC-I6) | FR-M-05 is tested at API and database level only (suite 5) | Add a simple audit-log list for the admin role, or record I6's UI as iteration 2. **Recorded as iteration 2 (C3, 13 October): there is no audit-log API yet; the moderator screens W5 to W7 were built instead** |
| UI-3 | W5 lists four dispute reasons; UC-B12 step 2 and the `dispute_reason` enum have five (with "other") | TC-105 expects five | Add "other" to W5 |
| UI-4 | W1's example interval [0.10, 0.90] differs from the prior Beta(1,1) bounds [0.05, 0.95] | TC-100 checks the API's bounds, so the example values do not affect the test | Correct the example or mark it illustrative |
| UI-5 | W5 states a 7-day dispute window and W6 an "SLA" auto-route to the admin; both timer values are TBD and the scheduler is iteration 2 | Not tested in iteration 1; TC-106 tests the iteration-1 rule (no moderator → admin) | Keep the values configurable and mark them as iteration 2 in the annotations |

### 6.10 Iteration 2 test cases (v2.0; suites 1, 11, 14 and 20 to 31)

"Actual" is "Not run" for every case below: the code is built in slices 2 and 3. Cases in suites owned by Students 1 and 2 are drafted here so every suite has concrete inputs at the design gate; their owners confirm or change them. All data is SYNTHETIC. Timer values are the proposed ones of FR/NFR v1.4 Part D and come from configuration, so a test sets them rather than waiting.

**Scenario suite, ES-07 to ES-12 (suite 11).** Fixtures: `14_testing/scenario_fixtures_iteration2.json` (computed by the real engine); hand-worked in `14_testing/Scenario_Specifications_ES07_ES12.md`.

| ID | Scenario | Expected state / lifecycle | Rule | Explanation must show | Actual |
|---|---|---|---|---|---|
| TC-110 | ES-07 conflicting condition reports, dispute open | ACTIVE_DISPUTE / ASSESSED | R1 | "A dispute involving a party is still open"; estimate 0.88, interval 0.66 to 0.99 | Not run (engine values computed) |
| TC-111 | ES-07 after resolution (possession RETURNED) | REVIEW_RECOMMENDED / ASSESSED | R6_DISPUTE | "Resolved disputes in the last 12 months: 1."; 9 loans | Not run (engine values computed) |
| TC-112 | ES-08 failure to return: open, then resolved LOST | ACTIVE_DISPUTE, then REVIEW_RECOMMENDED / ASSESSED | R1, then R6_DISPUTE | estimate falls from 0.84 to 0.72 | Not run (engine values computed) |
| TC-113 | ES-09 stored locality CONFLICTING | none, then REVIEW_RECOMMENDED after clearing / HELD_FOR_REVIEW (`locality_conflict`), then ASSESSED | none, then R9 | no assessment while held; no coordinates anywhere | Not run |
| TC-114 | ES-10 permission refused, no history | none, then INSUFFICIENT_EVIDENCE / HELD_FOR_REVIEW (`locality_inconclusive`), then ASSESSED | none, then R3 | "This is not a negative finding about the borrower." | Not run |
| TC-115 | ES-11 reversal flags the failure | REVIEW_RECOMMENDED before and after / ASSESSED | R6_DISPUTE (Q2 of the spec may change it to R9) | 6 loans before, 5 after; estimate 0.73 then 0.83 | Not run (engine values computed) |
| TC-116 | ES-12 old history and ES-12b sparse history | INSUFFICIENT_EVIDENCE / ASSESSED | R6_SPARSE | effective outcomes 0.5 and 1.9 | Not run (engine values computed) |

**Other suites.**

| ID | Suite | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-117 | 1 | The regenerated matrix, including `dispute_resolved` from DISPUTED to NO_SHOW, ACTIVE and COMPLETED | Each passes only with its possession and stored previous state; every other new pair is rejected with 409 and audited | Not run | FR-B-08, ADR-0009 |
| TC-118 | 14 | Every response and log line of search, uploads, reviews, membership and the audit screen in a full synthetic run | No coordinates, address or CNIC; the search log has no location column | Not run | NFR-PR-01, NFR-S-07 |
| TC-119 | 14 | A join request with a location fix | The fix is not in any log line, response or audit row; only the coarse outcome is stored | Not run | NFR-PR-02, FR-A-07 |
| TC-120 | 20 | A request past its response window; `run_due_jobs` called twice in a row | EXPIRED once; one `request_expired` event; one notification | Not run | FR-B-18, NFR-R-05 |
| TC-121 | 20 | Two overlapping `run_due_jobs` calls on the same due work | The advisory lock lets one run do the work; the other does nothing and returns | Not run | NFR-R-05 |
| TC-122 | 20 | An ACCEPTED booking past start date + 24 h grace | NO_SHOW (T19); dates released; outcome not attributed | Not run | FR-B-12 |
| TC-123 | 20 | An ACTIVE loan 72 h past due with no approved extension | `dispute_opened` with reason NON_RETURN (T24); a case opened once | Not run | FR-B-14 |
| TC-124 | 21 | Geofence INSIDE with a valid unused invitation | VERIFIED, method GEOFENCE_INVITATION; no coordinates stored | Not run | FR-A-07 |
| TC-125 | 21 | NEAR_BOUNDARY; UNAVAILABLE (permission refused) | INCONCLUSIVE, moderator review; never rejected | Not run | FR-A-08, NFR-Q-04 |
| TC-126 | 21 | OUTSIDE; mock-location flag | CONFLICTING with a flag, moderator review; never rejected | Not run | FR-A-08, NFR-Q-04 |
| TC-127 | 22 | A second request to a community where the member has a PENDING one | Refused; existing status shown | Not run | FR-A-09 |
| TC-128 | 22 | A moderator of community B decides a request for community A | 403; audit entry REJECTED | Not run | FR-A-10, NFR-S-03 |
| TC-129 | 22 | A decision without a reason | Refused until a reason is given | Not run | FR-A-10 |
| TC-130 | 22 | Two moderators approve the same request at the same moment | One decision applied; the other sees the current state; nothing applied twice | Not run | FR-A-11 |
| TC-131 | 23 | The same notification produced twice with the same dedupe key | One notification stored and shown | Not run | FR-C-02 |
| TC-132 | 23 | Member A asks for member B's notifications | 403 or empty; never B's data | Not run | FR-C-02, NFR-S-03 |
| TC-133 | 24 | A party reviews a COMPLETED loan; then tries again | First stored; second refused (one review per party) | Not run | FR-T-09 |
| TC-134 | 24 | A non-party reviews; a party reviews an ACTIVE loan | Both refused by the database guard | Not run | FR-T-09 |
| TC-135 | 24 | Edit at 23 h and at 25 h after submission (edit window 24 h, proposed) | First accepted; second refused | Not run | FR-T-09 |
| TC-136 | 24 | A low review 3 days after the reviewee's complaint on a loan with confirmed return | Set aside by the next assessment; not counted in S1 and S4; flag written only when a moderator confirms | Not run | FR-T-09, ES-05 |
| TC-137 | 25 | Owner's hand-made cases for S2 (velocity), S3 (new-account activity), S5 (linkage) | Each signal fires on its case with its evidence | Not run (cases defined by the owner) | FR-T-05 |
| TC-138 | 25 | The C3 family group | Stays below a hold (level 4 not reached) | Not run | FR-T-05, ADR-0007 |
| TC-139 | 25 | One strong signal alone | Level 3, not held (corroboration rule) | Not run | ADR-0007 |
| TC-140 | 26 | Dispute raised from ACCEPTED, resolved with NOT_HANDED_OVER | NO_SHOW (T25a); booking released; no return outcome | Not run | FR-T-11, ADR-0009 |
| TC-141 | 26 | Dispute raised from ACTIVE, resolved WITH_BORROWER | ACTIVE (T25b); booking stays held; due date unchanged | Not run | FR-T-11, ADR-0009 |
| TC-142 | 26 | Dispute raised from RETURN_INITIATED, resolved RETURNED | COMPLETED (T25c); booking released; return outcome recorded | Not run | FR-T-11, FR-B-15 |
| TC-143 | 26 | Dispute raised from ACTIVE, resolved LOST | COMPLETED; item PAUSED; borrower fails ON_TIME_RETURN | Not run | ADR-0009 |
| TC-144 | 26 | Dispute raised from ACCEPTED, the moderator sends RETURNED | Refused: possession not allowed for the stored previous state | Not run | ADR-0009 |
| TC-145 | 27 | A party appeals a decision within 7 days | Case APPEALED; assigned to a moderator other than the first decider (Admin if none) | Not run | FR-T-11 |
| TC-146 | 27 | A second appeal on the same case; an appeal on day 8 | Both refused | Not run | FR-T-11 |
| TC-147 | 27 | The first decider tries to decide the appeal | Refused (second moderator ≠ first) | Not run | FR-T-11 |
| TC-148 | 27 | The appeal is overturned | APPEAL_OVERTURNED references the first decision; case REVERSED; both kept; the outcomes from the first decision FLAGGED_FOR_REEVALUATION | Not run | FR-T-11, ES-11 |
| TC-149 | 27 | A reversal without a reason; a reversal by a member | Both refused; a reversal never changes the loan's lifecycle state | Not run | FR-T-11 |
| TC-150 | 28 | A JPEG with EXIF GPS | Stored without EXIF; the stored file has no location tags (replaces TC-59) | Not run | NFR-PR-01 |
| TC-151 | 28 | A `.exe` renamed `.jpg`; a file over the size limit | 422 for both, judged on content, not the name (replaces TC-85) | Not run | NFR-S-06 |
| TC-152 | 28 | A signed URL used by the other party, by a non-party, and after it expires | First allowed; second and third refused | Not run | NFR-S-03 |
| TC-153 | 28 | Storage unavailable while raising a dispute | The dispute is raised, marked reduced evidence; files can be added later | Not run | FR-B-16 |
| TC-154 | 29 | Filter by case, by date range, by result REJECTED | Only matching entries, newest first | Not run | FR-M-05 |
| TC-155 | 29 | Any listing | E-mail, phone and free text masked; unmasking needs a purpose and is itself logged | Not run | FR-M-05 |
| TC-156 | 29 | An entry altered with triggers disabled (test database only) | Tamper warning on that entry; the entry is still shown | Not run | NFR-S-05 |
| TC-157 | 29 | A moderator opens the log | Only their community's entries; the view is logged | Not run | NFR-S-03 |
| TC-158 | 29 | Ten decisions by one moderator about the same two users | The concentration highlight shows the pattern | Not run | FR-M-05 |
| TC-159 | 30 | Items in another community, a DRAFT item, and an item of a lender who blocked the borrower, all matching the query | None appears | Not run | FR-S-01 |
| TC-160 | 30 | The embedding model disabled | Keyword results returned; mode KEYWORD_ONLY; notice shown | Not run | FR-S-02, NFR-R-04 |
| TC-161 | 30 | Two items equal in every ranking input except the lender: one lender has no history, the other has evidence whose estimate equals the prior mean (0.5) | The new lender is not ranked below the other; lack of history is never a penalty | Not run | FR-S-01, FR-S-04 |
| TC-162 | 30 | Any result list | Every result has a reason line; no single trust number | Not run | FR-S-01, NFR-U-01 |
| TC-163 | 30 | Filters: category, maximum deposit, condition, dates | Only items matching all filters and free on the dates | Not run | FR-S-03 |
| TC-164 | 31 | The frozen query set (DA-25) in keyword-only and hybrid mode | Precision@5, recall@10 and NDCG@10 recorded per mode with the model and config versions | Not run | NFR-Q-05 |
| TC-165 | 31 | One search showing ten results; the third is opened | The log holds the query, the ten ranks, the click and no location | Not run | FR-S-05 |
| TC-166 | 31 | 100 searches on the seeded catalogue | Latency of retrieval and of the whole search recorded (no target yet) | Not run | NFR-P-01, NFR-P-02 |
| TC-167 | 11 | The scenario suite run on both fixture files | 13 of 13 scenarios pass with state and explanation | Not run | NFR-Q-01 |
| TC-168 | 18 | The extended smoke after a deploy (one search, one upload, one run-due-jobs call twice) | All pass; the second jobs call changes nothing | Not run | NFR-D-03, NFR-R-05 |
| TC-169 | 18 | The rollback rehearsal (`14_testing/Test_Deployment_Rollback_Handover_Plan.md` §5.3) | Previous version live; TC-91 and suites 1 to 5 green on it; time recorded | Not run | NFR-D-03 |

## 7. Traceability summary

| Requirement | Test cases |
|---|---|
| FR-A-07, FR-A-08, NFR-Q-04 | TC-119, TC-124 to TC-126 |
| FR-A-09 to FR-A-11 | TC-127 to TC-130 |
| FR-B-18, NFR-R-05 | TC-120, TC-121, TC-168 |
| FR-T-09 | TC-133 to TC-136 |
| FR-T-11 (iteration 2) | TC-140 to TC-149 |
| FR-S-01 to FR-S-05 | TC-159 to TC-163, TC-165 |
| NFR-Q-05, NFR-P-01, NFR-P-02 | TC-164, TC-166 |
| FR-B-05, NFR-R-01 | TC-08, TC-09 |
| FR-B-06 | TC-70 |
| FR-B-07 | TC-03, TC-60 |
| FR-B-08, NFR-R-02 | TC-01 to TC-06, TC-78, TC-81 |
| FR-B-09, NFR-R-03 | TC-07, TC-16, TC-72 |
| FR-B-10 | TC-15 (chat clause: iteration 3), TC-101 |
| FR-B-11 | TC-64 to TC-66, TC-102, TC-103 |
| FR-B-13 | TC-67, TC-68, TC-104 |
| FR-B-15 | TC-67, TC-69, TC-76 |
| FR-B-16, FR-B-17 | TC-05, TC-50 to TC-52, TC-105 |
| FR-N-03 | TC-72 |
| FR-T-01 | TC-35, TC-39 |
| FR-T-02, FR-T-03 | TC-20 to TC-24, TC-31, TC-40, TC-69, TC-76, TC-77 |
| FR-T-04 | TC-25 to TC-28, TC-34, TC-46, TC-47 |
| FR-T-05, FR-T-06 | TC-29 to TC-35, TC-38, TC-43, TC-45 |
| FR-T-07, NFR-R-04 | TC-36, TC-37 |
| FR-T-08, NFR-U-01 | TC-75, TC-100, TC-107 |
| FR-T-10, FR-T-11 | TC-53 to TC-57, TC-106, TC-107 |
| FR-M-05, NFR-S-05 | TC-13, TC-14 |
| NFR-S-01 | TC-83, TC-88 |
| NFR-S-02, NFR-S-03 | TC-10 to TC-12, TC-78, TC-80 to TC-82, TC-84, TC-106 |
| NFR-S-04 | TC-86 (It. 2) |
| NFR-S-06 | TC-85 |
| NFR-PR-01, NFR-S-07 | TC-58 to TC-60 |
| NFR-Q-01 | TC-40 to TC-47 |
| NFR-D-01 | TC-71, TC-74 |
| NFR-D-03, NFR-D-04 | TC-87, TC-90, TC-91 |
| NFR-D-05 | TC-73 |
| NFR-P-03, NFR-P-04 | suite 8, TC-61 |

The full requirement-to-artefact-to-test matrix is `01_requirements/Traceability_Matrix.md`.

## 8. Design-time verification already run (evidence for chapter 7)

| Check | Command | Result (11 October 2026) |
|---|---|---|
| Schema rules on PostgreSQL 16.6 (transition table, guards, overlap race, append-only, tamper, privacy scan, decision-table check) | `python 06_data_model/test_schema.py` (needs `DM_TEST_DSN`) | **44/44 passed** (`06_data_model/test_results.txt`) |
| Locality decision table and the six Overview §1 cases | `python 12_locality/test_locality_cases.py` | **18/18 passed** |
| Fixture oracle (posterior, intervals, k-hop, manipulation score, decision table) | `python 14_testing/verify_fixtures.py` | **13/13 fixtures consistent** (`fixture_verification_results.md`) |
| Design consistency and notation (paths, vocabulary, config values, generated files, UML / DFD rules) | `python 14_testing/verify_design.py` | **12/12 checks passed** |
| Diagram layout checks | each `generate_*.py` | 0 layout problems |

Defects found by these checks during integration (report chapter 7.7, "defects and corrective actions"):

- all six fixture intervals were miscomputed;
- the ES-04 score was miscalculated (86.8 instead of 96.8);
- ES-13 was impossible under ADR-0006;
- the ES-04 hold could not happen with one active signal;
- R1 sent a new request to DISPUTED.

All are fixed, and each fix is recorded in `00_management/Integration_Report_2026-10-11.md`.

## 9. Defect management

Defects are GitHub issues labelled `defect` and `sev-1` to `sev-4`:

- **Severity 1:** wrong state, data loss or a privacy leak.
- **Severity 2:** a failed acceptance criterion.
- **Severity 3:** a degraded feature with a workaround.
- **Severity 4:** cosmetic.

Each defect links its failing test case, and the fix PR adds or updates the test that would have caught it. For severity 1 and 2 that test is tagged `regression-<issue number>` and joins the regression set (§11). The defect log (report chapter 7 and Appendix C) lists the ID, severity, test case, cause, fix and commit.

## 10. Risks to testing

| Risk | Effect | Mitigation |
|---|---|---|
| `btree_gist` missing in a test database | Suite 3 cannot run | Use the official `postgres:16` image in CI and Compose (the embedded `pgserver` lacks it) |
| Flaky concurrency tests | False reds block merges | Repeat rounds deterministically; use a fresh item per round; fail on any double commit |
| Fixtures tuned to the detector | Overstated detection quality | The held-out attack generator stays separate (Module 10, Student 3) |
| Timer-dependent cases (expiry, no-show) | Not testable without the scheduler | Marked iteration 2; the DB guards are tested now with explicit events |
| Engine timeout depends on machine speed | Flaky suite 10 | Inject the delay in the stub instead of relying on load |
| Fuzzing (TC-84) produces many low-value findings | Noise in CI | Run Schemathesis with a fixed seed on PRs and a longer run nightly; triage findings weekly |
| No device lab | Device-specific bugs found late | One Android phone from the team for TC-73, TC-92 and suite 19; Expo Go for quick checks |
| Missing screen (UI-2) | Demo and alpha steps cannot run through the app | Wireframe owner adds them before Slice A ends; until then the step runs through the API |

## 11. Regression policy

Regression testing already happens because every suite reruns on every PR. This section names the regression set and when it runs.

| Trigger | What reruns | Rule |
|---|---|---|
| Every PR and every push to `develop` or `main` | **Regression set:** suites 1 to 7, 9 to 14, 16, 17, the component tests of suite 19, and the build smoke TC-90 | Blocking: a red check blocks the merge (NFR-D-04) |
| A severity-1 or severity-2 defect is fixed | The new `regression-<issue number>` test joins the set permanently | The test must fail before the fix and pass after it |
| A new engine `config_version` | Scenario suite 11 and policy suite 9 as a golden-master check against the fixtures' expected state, rule and explanation | Any changed state or explanation needs a reviewed approval and updated fixtures (`verify_fixtures.py` green) |
| A schema change or a new event type (`schema_version` bump) | Replay suite 2 on streams stored under the previous `schema_version`, plus suite 1 | Old streams must still replay to the same state (FR-B-09) |
| A rollback after a failed deploy | Smoke TC-91 and suites 1 to 5 against the restored version | Testing resumes only when both are green |
| Freeze (D-5 to D-0) | The full regression set plus suites 8 and 15 | Saved with raw output, the commit SHA and the config version, as chapter 7 evidence |

## 12. Alpha and beta testing

### 12.1 Alpha (in scope: internal team session)

- **When:** on the deployed `v0.1.0-rc1`, between D-5 and D-3.
- **Who:** the three students. Each plays a role they did not build: resident (borrower), lender, or moderator. The supervisor walkthrough at Mid-1 is recorded as informal acceptance.
- **How:** each member follows a short charter of about 45 minutes, on a phone with the role's screens (lender W1–W4, borrower W3b–W5, moderator W6–W7):
  1. the happy path, request to return (demo steps 2.1 to 2.4);
  2. the failure paths: dates taken, deposit not recorded, invalid transition, engine timeout, a locality hold, a dispute and its decision;
  3. a "break it" round: wrong inputs, double taps, back navigation, a lost connection mid-request.
- **Output:** every finding goes into the defect log with a severity, and severity 1 and 2 follow §9 and §11.
- **Exit:** no open severity-1 or severity-2 defect; findings summarised in report chapter 7.

### 12.2 Beta (out of scope for iteration 1; FYP-2 pilot)

Iteration 1 uses synthetic data only. Locality and the scheduler jobs are not built, and testing with real residents needs consent (NFR-PR-05). A beta in iteration 1 would claim something the project cannot show, so it is planned as the FYP-2 pilot.

- **Participants:** residents of one community and one moderator.
- **Entry criteria:**
  - consent and withdrawal process in place (NFR-PR-05);
  - locality method built (A11);
  - scheduler jobs built (B13);
  - Pakistani data-protection obligations confirmed with the supervisor;
  - no open severity-1 or severity-2 defect.
- **Measures:** NFR-U-02 (task completion without help), NFR-U-03 (SUS), NFR-U-04 (perceived fairness and understanding of the explanation), and the defect rate during the pilot.
- **Open point to settle before FYP-2:** the team decided "no interviews or survey" for problem validation (plan, 10 October), but NFR-U-03 and NFR-U-04 use a SUS questionnaire and a survey for evaluation. The team should confirm with the supervisor that post-use usability questionnaires in the pilot are acceptable, or change those NFRs.
