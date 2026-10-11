# Digital Mohalla — Project Context for Implementation

| Field | Value |
| :--- | :--- |
| Purpose | Single handoff document for coding with Claude Code. Put it at the repo root as `CLAUDE.md`, or keep it in `docs/` and point to it from `CLAUDE.md`. |
| Compiled | 2026-10-11, from the project files and planning work to date (compiled with Claude; reviewed by: ______) |
| Current stage | Iteration 1 (FYP-1 Mid). Part A (design) done by the team's account. Part B (implementation) starts now. |
| Source of truth | The project files listed in §17. Where this summary and a source file disagree, the source file wins; flag the conflict. |

---

## 1. What the project is

**Digital Mohalla** is a neighbourhood resource-sharing platform (lending, borrowing, donation). The technical core, and the complex computing problem (CCP), is a **trust and risk decision engine**: it estimates whether a physical handover is safe from sparse, indirect, manipulable evidence, reports its own uncertainty, and recommends safeguards or human escalation. Everything else (listings, workflow, search, UI) exists to feed or act on that decision.

- **Team:** Fatima Khursheed, Areeba Javed, Minahil Kashif. **Supervisor:** Dr. Ali Zeeshan. FAST School of Computing, FAST-NUCES Islamabad.
- **Proposal defence:** approved with minor modifications. Panel points: (1) location needs to be shown to be a real issue, (2) positive social potential, (3) limited technical challenges. Point 3 is the serious one; the assurance engine is the answer to it.

**CCP statement (Overview, Post-Defence Direction):**
> Determine whether a proposed borrowing transaction has sufficient trustworthy evidence under sparse, role-dependent and potentially manipulated history, while protecting location privacy and escalating uncertain cases to humans.

**Committed core:** community membership; privacy-preserving locality verification; borrowing requests; event-sourced transaction lifecycle; evidence-based assurance; handover and return confirmation; dispute management; moderator review.

**Supporting or stretch (only after the core works):** vendors, community events, kameti, general chatbot, social feed, advertisements, broad analytics. Search and matching are supporting scope.

**Scope protections — the project must not become:** a generic social network; a conventional listings app; a neighbourhood surveillance system; an opaque social-scoring system; an LLM-based substitute for a computing challenge.

**Never say "AI-powered".** The overview's Executive Overview still uses that framing; do not reuse it. Use the framing in FR/NFR Part F.

---

## 2. Rules for working on this codebase

### Engineering
- Read the relevant code and docs before changing anything. Small diffs over rewrites. Don't touch files outside the task; don't delete things unasked.
- Simplest thing that satisfies the spec. 3 people, 2 semesters: no extra frameworks or abstractions.
- Map every piece of work to a **module (§4)** and, where relevant, a claim (§11). If it maps to neither, question whether it should exist.
- **Tunable parameters live in versioned config, never hardcoded.** Every stored assessment records `config_version`. Parameters need experimental backing later.
- Testable and reproducible: fixed seeds, deterministic where possible, no magic numbers.
- Add or update tests for anything touching state transitions, trust maths, propagation or detection. **Every invalid state transition must be tested.**
- Log experiment configs and outputs so every report figure can be regenerated.
- Report latency alongside coverage and accuracy for any k sweep. Mention latency for anything in the propagation path.
- When analysing, separate what was verified (ran it, read it) from what is inferred. Give numbers, not adjectives.
- **The event schema is frozen.** Don't add or rename fields or event types without flagging it; it needs sign-off from all three students.
- If a task touches Module 5 engine internals, the schema or the event log and is bigger than it looks, stop and flag it.
- After a change: say what ran, what passed, what's untested.

### Scope
- Stay inside the frozen scope. Anything outside needs a formal change request (Form 12). Push back before doing it.
- Anything user-facing is **decision support, not a guarantee**.

### Data and ethics
- Three data sources, never mixed: **simulation** (all algorithmic claims), **public trust network** (propagation validation only), **real pilot** (acceptance only).
- Approximate location only. No exact addresses, no CNIC. Consent and withdrawal rights for pilot data.
- Generated text shown to users is filtered for personal identifiers.
- Synthetic attack scenarios and seed data are labelled synthetic everywhere (files, screens, report).

### Evaluation discipline
- Headline claims: **C1** uncertainty beats averages at low evidence; **C3** false-positive rate on legitimate dense clusters; **C5** newcomers not excluded. (C2, C4, C6–C9 are referenced in the project instructions but not defined in any file.)
- Attack strategies used for final evaluation are held out from tuning. Detector parameters are set without looking at the attack generator; the attack generator is written by someone other than the detector's author.
- A component with no measurable benefit in ablation is reported as such. A negative result is a finding.
- Don't overclaim. Results come only from actual runs; simulation and pilot results stay separate.

### Academic integrity
- Keep `docs/ai-usage-log.md` and the dependency disclosure (Form 13) up to date. After any substantial AI-assisted change, append: date, what, which files, who reviewed.
- Don't write anything the team couldn't explain at a viva. For complex code or maths, add a plain-language note on what it does and why this choice over the alternative.
- Cite algorithm sources (e.g. Golbeck 2005 for trust propagation; Beta posterior reputation) and say whether reproduced, adapted or modified.
- Don't fabricate references, datasets, results or metrics.

---

## 3. Process: the four iterations and what mid eval grades

| Iteration | Stage | Theme | What the stage requires (Handbook Appendix A) |
| :--- | :--- | :--- | :--- |
| 1 | FYP-1 Mid, week 8; supervisor; 20 marks | Core module | Live module implementing project logic (not a POC re-run); design artefacts evolved since proposal; function-level walkthrough; one failure/edge case tested; CI/CD with meaningful branches and automated tests |
| 2 | FYP-1 Final; panel + supervisor; 50 marks | At least 45% of committed scope | ~45% of committed work implemented, modular, buildable by someone else; testing beyond happy path; report matches live system; written FYP-2 evaluation plan; poster |
| 3 | FYP-2 Mid / job fair; panel + supervisor; 50 marks | Full integrated system | All major modules connected; realistic scenarios; CCP visible; integration tests, known bugs, preliminary comparison against the FYP-1 Final baseline |
| 4 | FYP-2 Final; supervisor; 50 marks | Evaluation, testing, wrap-up | No regression; final report traced to evaluation results; honest limitations; no new scope (no Form 12 at this stage) |

**Mid-eval brief (from the school):** implement at least the core module with a CI/CD pipeline, using the live interface (or improved version) shown as POC at the proposal defence. Use GitHub meaningfully: meaningful branches, automated testing for CI and CD. Treat the project as a product.

**Form 2 (demo) criteria:** live prototype with core module 25; design artefacts and evolution 15; proposal actions addressed 10; iteration plan and progress 10; requirements and acceptance criteria 10; repository and member evidence 10; testing and early validation 10; team dynamics and tool ownership 10.

**Form 3 (report) criteria:** problem/R&D/existing solutions 15; requirements and acceptance criteria 15; architecture and component/interface design 15; implementation documentation 15; testing plan and tool/risk disclosure 15; vision/scope/modules/success criteria 10; data/process/behaviour design 10; format and artefacts 5. How Forms 2 and 3 combine into 20 marks is not in the handbook; ask the supervisor.

**Automatic caps (Handbook §2.2):** no live system → implementation/demo capped at 40%; diagrams without design reasoning → design capped at 50%; undisclosed core GenAI/API use → tool-use item 0; a member who can't explain their claimed code gets an individual multiplier below 1.00 (Form 11).

---

## 4. The ten modules

Modules are the overview's ten feature sections (numbering follows the overview's **table of contents**; the overview body numbers differently from §6 onward and needs renumbering). The proposal's §8.1 "M1–M9" labels are technical **components inside** these modules, not modules.

| # | Module | Scope | Use cases | FRs | Proposal §8.1 components inside |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | User & Community Management | Core: membership, locality; rest enabling | A1–A9 | FR-A-01 to A-15 | Part of Platform |
| 2 | Community Events & Activities | Stretch | C1–C10 | FR-EV-01 to EV-06 | — |
| 3 | Resource Sharing & Item Management | Core: borrowing lifecycle; listings enabling | B1, B2, B5–B8, B12, B13 | FR-B-01 to B-18 | Transaction workflow; listings |
| 4 | Search, Discovery & Matching | Supporting | B3, B4, B9–B11 | FR-S-01 to S-09 | Semantic search and fair matching |
| 5 | Trust, Reputation & Safety | **Core, the CCP** | D1–D7 | FR-T-01 to T-10, T-12 | Trust estimation, indirect trust, manipulation detection, decision policy |
| 6 | Community Forum & Chatbot | Stretch | E1–E6, F1–F5 | FR-FO-*, FR-CB-* | — |
| 7 | Communication & Notifications | Enabling | G1–G4 | FR-C-01 to C-03, FR-EV-07 | Part of Platform |
| 8 | Vendor Management | Stretch | H1–H5 | FR-VD-01 | — |
| 9 | Administration & Moderation | Core: case/dispute resolution, audit; rest enabling | I1–I6 | FR-M-01 to M-05, FR-T-11 | Moderator console; admin |
| 10 | Analytics & Reports | Core: event logging and evaluation; rest supporting/stretch | J1–J3 | FR-N-01 to N-03, FR-NA-01 | Evaluation harness |

Overview §11–§15 (UI & UX, Deployment, Testing, Design, Documentation) are cross-cutting, not modules.

---

## 5. Borrowing lifecycle (Module 3)

Event-sourced: every transition is an immutable event; current state is derived by replay.

### States (Use Cases v1.1 §2)

| State | Meaning | Entered by `event_type` |
| :--- | :--- | :--- |
| REQUEST_CREATED | Request submitted; dates marked as requested (soft hold, ADR-0001) | `request_created` |
| LOCALITY_CHECKED | Coarse locality *verified*, or a locality / engine-failure hold was cleared | `locality_checked`, `hold_cleared` |
| HELD_FOR_REVIEW | Locality inconclusive/conflicting, manipulation risk ≥ 60, high value with low confidence, or engine failure; waits for a moderator; never an automatic rejection; hold reason recorded | `held_for_review` |
| ASSESSED | Assurance state and evidence summary attached; waits for lender | `assessment_generated`, `hold_cleared` |
| ACCEPTED | Lender accepted; dates blocked under the overlap constraint (ADR-0002) | `request_accepted` |
| ACTIVE | Handover confirmed by both | `handover_confirmed` |
| RETURN_INITIATED | Borrower started return | `return_initiated` |
| RETURNED | Both confirmed condition | `return_confirmed` |
| COMPLETED | Closed normally or by moderator; outcome sent to the engine | `transaction_closed` (normal), `dispute_resolved` (moderator) |
| DECLINED, CANCELLED, EXPIRED, NO_SHOW, DISPUTED | Side/terminal states | `request_declined`, `request_cancelled`, `request_expired`, `no_show`, `dispute_opened` |

Extensions and reminders are events inside ACTIVE; they don't change state.

**Assurance state ≠ lifecycle state.** Keep them as separate attributes. Example ES-04: lifecycle HELD_FOR_REVIEW, assurance REVIEW_RECOMMENDED.

### Exits from HELD_FOR_REVIEW (ADR-0003)
Hold reasons: `locality_inconclusive`, `locality_conflict`, `manipulation_risk`, `high_value_low_confidence`, `engine_failure`.

| Hold reason | Cleared | Safeguards imposed | Restricted |
| :--- | :--- | :--- | :--- |
| Locality (inconclusive/conflict) | `hold_cleared` → LOCALITY_CHECKED, then assessment runs | Same, with safeguards | `request_declined` → DECLINED |
| Manipulation risk, high value low confidence | `hold_cleared` → ASSESSED (existing assessment + moderator note) | → ASSESSED with added safeguards | → DECLINED |
| Engine failure | `hold_cleared` → LOCALITY_CHECKED, assessment re-run | Not allowed (no assessment exists) | → DECLINED |

A request held again after clearance re-enters HELD_FOR_REVIEW with the new reason.

### Exits from DISPUTED (ADR-0004)
`dispute_resolved` → COMPLETED (moderator, decision + reason; resolved outcome becomes evidence). `dispute_withdrawn` → the `previous_state` stored in the `dispute_opened` event.

### Frozen event schema
`event_id, stream_id (transaction), stream_seq, event_type, schema_version, actor_id, occurred_at, previous_state, new_state, evidence_refs, authorisation`; assessment events also `config_version`.
- Unique key on (`stream_id`, `stream_seq`). `stream_seq` orders events **within one transaction only**.
- Event types added in v1.1 (pending sign-off): `hold_cleared`, `dispute_resolved`, `dispute_withdrawn`.
- **Open (N-6, decided in design step A4 — fill in §15):** where event-specific data lives (requested dates, hold reason, moderator decision and reason, safeguards). Proposal was a `payload` JSON field defined per `event_type`, or defining `evidence_refs` to cover it.

### Concurrency (ADR-0001, ADR-0002)
- **Soft hold:** pending requests block nothing; several may overlap.
- **Overlap constraint at acceptance:** PostgreSQL exclusion constraint — no two bookings for the same item with status ACCEPTED or ACTIVE may have overlapping date ranges. The transition, booking write and `request_accepted` event commit in **one DB transaction**. If refused: nothing commits, lender told "dates taken", request ends DECLINED with reason "dates taken". On a successful accept, overlapping pending requests are auto-DECLINED.
- Three layers per acceptance: state machine checks the move and actor → DB enforces the calendar → event appended.

---

## 6. Assurance engine (Module 5) — the CCP

Pipeline: Direct evidence → recency-weighted Beta posterior → bounded k-hop indirect evidence → manipulation detection → context policy → assurance state + safeguards + explanation, or human escalation.

### 6.1 Direct evidence: recency-weighted Beta posterior (Overview §5.2)
- Each outcome (e.g. "returned on time") is a Bernoulli trial, per subject, role and metric.
- Weight for an outcome `d` days old: `w = 2^(-d/h)`, half-life `h = 180` days.
- `s_w = Σ w·y`, `f_w = Σ w·(1−y)`; posterior `Beta(α0 + s_w, β0 + f_w)`, prior `α0 = β0 = 1`.
- Report posterior mean, **90% credible interval**, effective evidence.
- Zero history → Beta(1,1) → INSUFFICIENT_EVIDENCE ("Insufficient verified history; lender review required"). **Not a negative finding.**
- Terminology: "recency-weighted Beta posterior". Beta-Binomial is only the predictive distribution; never call the posterior that.
- Only outcomes with both handover and return confirmations count. Disputed/conflicting outcomes are excluded until resolved; the resolved outcome is recorded afterwards.
- Similarity weighting (FR-T-03): category, value band, duration. Iteration 1 does value band only.
- Check values: Beta(1,1) at zero history; 18 successes + 2 failures → Beta(19,3); weights ≈ 0.96 and 0.25 at 10 and 360 days.

### 6.2 Indirect evidence: bounded k-hop (Overview §5.5)
- Directed weighted graph; nodes = users; edges derived from the source user's **verified** outcomes for the same role and metric (never manual vouches).
- Simple paths up to `k = 3` hops. Path weight = product of edge weights × `γ^(hops−1)`, `γ = 0.7` (first hop not penalised).
- Keep at most the **strongest path per first-hop neighbour** (correlated paths aren't independent evidence).
- Aggregate selected paths with noisy-OR: `I(u,v) = 1 − Π(1 − q(P))`.
- Reliability: `ρ = min(0.6, min(1, |P|/3) · min(1, |first hops|/2) · I(u,v))`.
- Estimate: `t_indirect = b + ρ(t_v − b)`, `t_v` = target's direct mean, `b` = role/metric population baseline. With no direct evidence `t_v = b` and the result is labelled prior-backed.
- **Indirect evidence alone can never produce SUFFICIENT_EVIDENCE.**
- k-hop is useful when the borrower has history but none with this lender (ES-13); for a true newcomer it changes nothing.
- Its effect on the decision is defined in the A5 decision table (fill in §15).
- Evaluate k = 1..4 for accuracy, coverage, latency, calibration, false positives.

### 6.3 Manipulation detection (Overview §5.6, §5.13)
- Separate 0–100 risk dimension; **never averaged with trust**. Shows anomalies with evidence, never accusations.
- Signals: reciprocal rating clustering, rating velocity, new-account activity, similar review text, linked accounts (only where legitimately available). Threat model also: retaliatory reviews, trivial exchanges, sudden high-value requests, false damage claims, location spoofing, moderator misuse.
- Risk bands: 0–19 proceed; 20–39 monitor; 40–59 request verification; **60–100 flag for moderator review — restrict only after a human decision** (holds the request in HELD_FOR_REVIEW).
- Iteration 1 builds two checks: **reciprocal clustering (ES-04)** and **retaliation check (ES-05)**, plus a guard test that a legitimate family-style dense group stays below the review threshold (C3).

### 6.4 Decision policy and assurance states (Overview §5.8, §5.11)
- Inputs: direct trust, indirect trust, confidence, manipulation risk, role, transaction type, item value, dispute history, verification status.
- Policy outputs: proceed / proceed with safeguards / request verification / restrict high-value / escalate.
- Four assurance states (describe the evidence, not the person):

| State | Meaning |
| :--- | :--- |
| SUFFICIENT_EVIDENCE | Verified evidence adequate for this item, value and context; no unresolved conflict or manipulation signal |
| REVIEW_RECOMMENDED | Evidence exists but is mixed, dated, dissimilar or anomalous |
| INSUFFICIENT_EVIDENCE | Not enough verified history; not a negative finding |
| ACTIVE_DISPUTE | An unresolved dispute affects this transaction |

- Mapping: proceed → SUFFICIENT; proceed with safeguards → SUFFICIENT only if the strong-evidence rule holds, else REVIEW; request verification → INSUFFICIENT for cold start, else REVIEW; restrict high-value → REVIEW pending human decision; escalate → REVIEW, or ACTIVE_DISPUTE when a dispute is open.
- Rules: open disputes take precedence; indirect evidence alone cannot give SUFFICIENT; no restriction without human review.
- Engine failure or timeout → HELD_FOR_REVIEW (`engine_failure`), logged, **no default state**.
- Every output explains which evidence raised or lowered assurance. Never show a single trust number to users.
- Safeguards: deposit record, handover photos, fixed return date, verification.

### 6.5 Parameters (all in config, labelled initial and unvalidated)

| Parameter | Initial value | Source |
| :--- | :--- | :--- |
| Prior α0, β0 | 1, 1 | Overview §5.2 |
| Half-life | 180 days | §5.2 |
| Credible interval | 90% | §5.2 |
| Max hops k / decay γ / indirect cap | 3 / 0.7 / 0.6 | §5.5 |
| Manipulation risk bands | 0–19 / 20–39 / 40–59 / 60–100 | §5.6 |
| SUFFICIENT_EVIDENCE rule (min effective evidence, min interval lower bound) | **Decided in A5 — fill in §15** | was undefined |
| High-value dissimilarity (value-band ratio) | **Decided in A5 — fill in §15** | was undefined |
| Velocity, new-account and retaliation windows | **Decided in A5 — fill in §15** | was undefined |

### 6.6 Data structures (Overview §5.10)
```text
OutcomeEvent  { event_id, subject_id, observer_id, role, metric, success, occurred_at, transaction_id }
TrustEdge     { source_id, target_id, role, metric, weight, evidence_count, updated_at }
TrustEstimate { subject_id, role, metric, alpha, beta, mean, lower_90, upper_90,
                effective_sample_size, direct_event_count, computed_at }
PathEvidence  { nodes, hops, path_weight }
```
`Algorithm_and_Data_Structure_Design.md` is cited by the overview as the engine's source of truth but is **not in the project files**. Overview §5.11 says a "Python Phase 2 module" implements a dependency-free policy slice; whether that code exists is unconfirmed.

---

## 7. Architecture decisions (ADRs)

File: `DigitalMohalla_ADRs.md` (in the project as `claude/DigitalMohalla_ADRs.md`). Signed off in design step A1 by the team's account; record sign-off dates in the file.

| ADR | Decision |
| :--- | :--- |
| 0001 | Soft hold: pending requests mark dates as requested, block nothing |
| 0002 | Overlap constraint enforced by PostgreSQL at acceptance; replaces "lower `stream_seq` wins" |
| 0003 | HELD_FOR_REVIEW exits depend on hold reason; new event `hold_cleared` |
| 0004 | `dispute_resolved` and `dispute_withdrawn` event types |

Still to write as ADRs (report §5.4): stack choice; event-specific data field (N-6); SUFFICIENT rule and N-7; locality method; event sourcing vs CRUD + audit table; rule-based vs trained manipulation detection.

---

## 8. Requirements summary

Full text: `DigitalMohalla_Use_Cases.md` v1.1 and `DigitalMohalla_FR_NFR.md` v1.1. 68 use case IDs (A 9, B 13, C 10, D 7, E 6, F 5, G 4, H 5, I 6, J 3).

**Dressed core use cases:** B5 send request; B6 respond; B7 confirm handover; B8 return and complete; B12 raise dispute; D3/4/5 assess transaction assurance; D6 escalate case; I4 resolve escalated case or dispute; I6 view audit logs; A3 request membership and A4 approve membership (core, iteration 2).

**Core FRs:** 35 (CORE-tagged in Modules 1, 3, 5, 9, 10). Acceptance criteria (Given/When/Then) exist for 25 of them in FR/NFR Part E. Missing for FR-N-03 and FR-A-04 (both built in iteration 1) — add them.

**NFRs with numeric gates in iteration 1:**

| NFR | Gate |
| :--- | :--- |
| NFR-R-01 | N simultaneous acceptances for overlapping dates → exactly one commits, 100% of runs |
| NFR-R-02 | Invalid lifecycle transitions rejected 100% |
| NFR-R-03 | Replay reproduces stored state exactly |
| NFR-P-03 | Direct-evidence assessment P95 ≤ 1 s; k = 1..4 latency reported, not gated |
| NFR-P-04 | State transition commit P95 ≤ 500 ms |
| NFR-S-02 | 100% of unauthorised transitions rejected and logged |
| NFR-S-05 | Audit log append-only; 100% of tampered entries detected |
| NFR-D-01 | 100% of assessments store `config_version` |
| NFR-D-04 | Tests run on every build; failing test blocks merge |
| NFR-Q-01 | Mid-1: ≥ 7 of 13 scenarios (ES-01–06, ES-13) pass with correct state **and** explanation; final 13/13 |

Other key rules: NFR-PR-01 exact location never in profiles, listings, API responses or logs; NFR-S-07 no CNIC stored; NFR-U-01 every assurance state shown with its evidence, never one number.

### Evaluation scenarios (Overview §11 table; ES IDs from FR/NFR)

| ID | Scenario | Expected state |
| :--- | :--- | :--- |
| ES-01 | New user, no history | INSUFFICIENT_EVIDENCE |
| ES-02 | Consistently reliable | SUFFICIENT_EVIDENCE |
| ES-03 | Reliable with one recent dispute | REVIEW_RECOMMENDED (ACTIVE_DISPUTE if still open) |
| ES-04 | Colluding participants | REVIEW_RECOMMENDED (request HELD_FOR_REVIEW) |
| ES-05 | Retaliatory review | REVIEW_RECOMMENDED |
| ES-06 | High-value request, weak evidence | REVIEW_RECOMMENDED |
| ES-07 | Conflicting condition reports | ACTIVE_DISPUTE |
| ES-08 | Failure to return | ACTIVE_DISPUTE |
| ES-09 | Location mismatch | REVIEW_RECOMMENDED |
| ES-10 | Location-permission refusal | INSUFFICIENT_EVIDENCE |
| ES-11 | Moderator reversal | REVIEW_RECOMMENDED |
| ES-12 | Sparse or old history | INSUFFICIENT_EVIDENCE |
| ES-13 | History with others, none with this lender, reachable via community paths (proposed) | Set in A5 — fill in §15 |

Iteration 1 builds ES-01–ES-06 and ES-13 as synthetic fixtures (labelled synthetic) running in CI.

---

## 9. Iteration 1 scope

| Item | Iteration 1 | FRs | Module |
| :--- | :--- | :--- | :--- |
| Borrowing request with date check (B5) | Build | FR-B-05, B-06 | 3 |
| Event store, state machine, replay, invalid-transition rejection | Build | FR-B-08, B-09 | 3 |
| No double booking (ADR-0002) | Build | FR-B-05, NFR-R-01 | 3 |
| Lender accept/decline (B6) | Build, no counter-offer | FR-B-10 | 3 |
| Handover, return, late outcome (B7, B8) | Build, photos optional | FR-B-11, B-13 | 3 |
| Outcome sent to engine | Build | FR-B-15 | 3, 5 |
| Raise and withdraw dispute (B12) | Build | FR-B-16, B-17 | 3 |
| Deposit | Record-only flag; never moves money | FR-B-11 | 3 |
| Recency-weighted Beta posterior, 90% interval | Build | FR-T-02 | 5 |
| Evidence weighting | Recency + value band | FR-T-03 | 5 |
| k-hop indirect evidence | Build, bounded, k from config | FR-T-04 | 5 |
| Manipulation checks | 2: reciprocal clustering, retaliation | FR-T-05 | 5 |
| Decision policy, states, safeguards, explanation | Build | FR-T-01, T-06, T-08 | 5 |
| Engine failure → HELD_FOR_REVIEW | Build | FR-T-07 | 5 |
| Escalation case with evidence trail (D6) | Build; chat messages later | FR-T-10 | 5 |
| Moderator decisions for disputes and holds (I4) | Build; no appeal/reversal | FR-T-11 | 9 |
| Append-only audit log + minimal view (I6) | Build | FR-M-05 | 9 |
| Frozen event logging | Build | FR-N-03 | 10 |
| Scenario suite ES-01–06, ES-13 | Build, in CI | NFR-Q-01 | 10 |
| Login and roles | Minimal: seeded users, password login | FR-A-04 (part) | 1 |
| Locality check | Designed (A11), stubbed in B5; method build decided at D-11 gate | FR-B-07, FR-A-06–A-11 | 1, 3 |
| Communities, memberships, items | Seeded, no UI | FR-A-09, FR-B-01 | 1, 3 |
| Reviews (D1) | Seeded for ES-04/ES-05 only | FR-T-09 | 5 |

Not in iteration 1: scheduler jobs, counter-offer, extensions, remaining detection signals, appeal/reversal, notifications, chat, listings UI, search, all stretch modules.

---

## 10. Iteration 1 plan

Days are counted back from the mid eval (D-21 = 21 days before). **The mid-eval date is not in any project file** — get it from the supervisor.

### Part A: design (done, by the team's account)
A0 clean-up · A1 four ADRs · A2 domain model · A3 state machines + transition table · A4 data dictionary + event catalogue · A5 algorithm and policy design + config draft + hand-worked scenario expectations · A6 ERD · A7 class diagram · A8 component + layer diagrams, REST endpoint table · A9 sequence diagrams (B5 request→assessment with timeout; B7/B8 confirmation→evidence; B12→D6→I4), dispute activity diagram, SSDs (B5, B7+B8, B12, I4), use case diagram · A10 DFD L0 + L1 · A11 locality method comparison + six locality test cases · A12 wireframes · A13 test plan + deployment diagram · A14 design gate (stack decided).

**The artefacts are not in the project files.** Add them to the repo under `docs/design/` so code can be checked against them (state machine vs ADR-0003, ERD vs data dictionary).

### Before Slice A
- [ ] Add Part A artefacts to `docs/design/`.
- [ ] Record the Part A decisions in §15 and in FR/NFR v1.2 + use cases: N-6, N-7, SUFFICIENT thresholds, locality method, stack.
- [ ] Tag the requirements baseline and `schema-v1`.
- [ ] Log AI help on Part A artefacts in the AI usage log.

### Part B: implementation (three vertical slices, each ending deployable)
- **B0 setup (D-15 to D-14):** repo layout `backend/ frontend/ infra/ docs/`; protected `main` and `develop`; GitHub board + "Iteration 1" milestone; CI skeleton; Docker Compose + PostgreSQL; config loader; seed script with synthetic users (labelled); deployment target chosen; start AI usage log and Form 13 sheet.
- **Slice A, workflow skeleton (D-14 to D-11):**
  - S1: append-only event store with unique (`stream_id`, `stream_seq`); transition table from A3; aggregate + replay; overlap constraint; authorisation on every transition; request → stub locality → stub assessment (always INSUFFICIENT_EVIDENCE) → accept/decline → handover → ACTIVE → return → RETURNED → COMPLETED.
  - S2: `assess(request)` interface returning the agreed output object (stubbed); fixtures for ES-01–06, ES-13.
  - S3: minimal UI clicking through the loop; first CD deploy with smoke test.
  - **Gate D-11:** loop runs on the deployed instance; transition-matrix, replay, concurrency, authorisation, append-only tests pass. Decide whether the locality method is built in Slice C or iteration 2.
- **Slice B, assurance core (D-11 to D-8):**
  - S2: outcome extraction (confirmed only, disputed excluded); Beta posterior with recency + value band; decision policy, safeguards, explanation; `config_version` stored; engine timeout → HELD_FOR_REVIEW.
  - S1: trust-edge projection + k-hop; paths in explanation; latency/coverage at k = 1..4.
  - S3: lender screen with evidence summary; scenario suite (Module 10) in CI.
  - **Gate D-8:** ES-01, 02, 03, 06, 13 pass with state and explanation.
- **Slice C, human loop (D-8 to D-5):**
  - S2: reciprocal clustering + retaliation checks; ES-04, ES-05 pass; dense-group guard.
  - S3: raise dispute + freeze; case with evidence trail (D6); moderator decisions for disputes and holds (I4); resolved outcome counted as evidence; minimal audit view (I6).
  - S1: privacy checks on API responses and logs; locality method if the D-11 gate chose it.
  - **Gate D-5:** feature freeze; tag `v0.1.0-rc1`.
- **Freeze, report, rehearsal (D-5 to D-0):** system tests on the deployed instance; defect log; latency numbers saved with config version and raw output; screenshots and CI links; report chapters 6–10; two timed demo rehearsals; update Form 10, Form 13, AI log; tag `v0.1.0-mid1`; reset demo data; submit.

---

## 11. Work division (proposed; matches the module roadmap)

| | S1: lifecycle, indirect trust, locality | S2: estimation, policy, detection | S3: moderation, evaluation, apps |
| :--- | :--- | :--- | :--- |
| Iteration 1 modules | Module 3 lifecycle; Module 5 indirect trust; Module 1 minimal login + locality design; CI | Module 5 trust estimation, decision policy, first manipulation checks | Module 9 cases/disputes (I4, I6); Module 10 scenario suite; resident + moderator apps; deployment |
| Build | B0 repo + CI; Slice A lifecycle; Slice B k-hop; Slice C privacy + locality if chosen | Slice A engine interface + fixtures; Slice B posterior + policy; Slice C two checks | B0 deployment; Slice A UI + CD; Slice B lender screen + scenario suite; Slice C dispute, cases, decisions, audit view |
| Tests owned | Transition matrix, replay, concurrency, authorisation, append-only, k-hop hand graph, k sweep latency, privacy | Beta maths, policy table, scenario logic, dense-group guard, engine timeout | Dispute + hold resolution, UI smoke, deployed smoke, system tests |
| Report | 5.1–5.3, 5.7, state machine, 6.6 lifecycle + indirect trust, locality/spoofing design, CI/CD | 2.6 CCP, 2.8, 5.8, 6.7 algorithms + complexity, engine results | Ch. 1 (incl. ten modules), 2.2–2.4, Ch. 3, Ch. 4 diagrams, Ch. 7 lead, Ch. 9, setup manual |
| Demo | Invalid transition, concurrent acceptances, replay, k-hop paths | Newcomer vs established, colluding scenario, engine timeout | Main story, moderator decision, pipeline + deploy |

- Module 5 is shared: S2 owns estimation, policy, detection; S1 owns indirect trust. The boundary is one interface, `assess(request)`.
- Module 10 sits with S3 so the iteration 3 attack generator is never written by the detector's author.
- If S2 falls behind, S1 takes the reciprocal-clustering check.
- Names for S1/S2/S3: **assign — open**. Every PR is reviewed by someone other than its author.

---

## 12. CI/CD

- **Branches:** `main` (deployed; release PRs from `develop` only), `develop` (integration; PRs only), `feature/<area>-<topic>`, `fix/…`, `docs/…`, each linked to an issue. Merge needs all CI jobs green + one approval from a non-author. Tags per iteration: `v0.1.0-mid1`, `v0.2.0-final1`.
- **`ci.yml`** (every PR and push to `develop`/`main`): ruff + eslint; mypy on engine and lifecycle packages; bandit + pip-audit; pytest with coverage (proposed floor 80% on engine and lifecycle); integration tests against a Postgres service container (lifecycle, replay, concurrency, authorisation, dispute); scenario suite; frontend build; upload JUnit + coverage reports as artifacts.
- **`cd.yml`** (push to `main`): build Docker images tagged with commit SHA → push to GHCR → deploy over SSH (pull, migrate, `docker compose up -d`) → smoke test (`/health` + one scripted request to assessment) → on failure, redeploy previous image (rollback).
- Secrets in GitHub Environments, never in the repo. Pre-commit hooks for ruff; Dependabot.
- Deployment target: AWS per NFR-D-03 (one small instance + Docker Compose) — **confirm; open decision**.

---

## 13. Test plan (iteration 1)

| # | Suite | Level | Pass condition | Traces to | Slice |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Transition matrix (every state × event from A3) | Unit | Valid moves pass; every invalid one rejected and logged | FR-B-08, NFR-R-02 | A |
| 2 | Replay in `stream_seq` order | Integration | Rebuilt = stored state | FR-B-09, NFR-R-03 | A |
| 3 | Double booking (N parallel acceptances) | Integration | Exactly one commits, every run | FR-B-05, NFR-R-01 | A |
| 4 | Authorisation decision table | Integration | Only permitted actors; moderators only in own community | NFR-S-02, S-03 | A |
| 5 | Append-only + tamper | Integration | UPDATE/DELETE fail; altered entry detected | FR-M-05, NFR-S-05 | A |
| 6 | Beta posterior | Unit | Beta(1,1); Beta(19,3); weights ≈0.96/0.25; interval narrows | FR-T-02, T-03 | B |
| 7 | k-hop on hand-worked graph | Unit | Expected paths, decay, one path per first hop, noisy-OR, ρ ≤ 0.6, nothing beyond k, cycles safe | FR-T-04 | B |
| 8 | k sweep k = 1..4 | Performance | Latency + coverage reported with config version | NFR-P-03 | B |
| 9 | Policy decision table | Unit | Dispute first; indirect alone never SUFFICIENT; risk ≥ 60 holds, no restriction | FR-T-06 | B |
| 10 | Engine failure (fault injection) | Integration | HELD_FOR_REVIEW, logged, no state assigned | FR-T-07, NFR-R-04 | B |
| 11 | Scenarios ES-01–06, ES-13 | Acceptance | State and explanation both match | NFR-Q-01 | B, C |
| 12 | Dense legitimate group | Unit | Stays below review threshold | C3 guard | C |
| 13 | Dispute and hold resolution | Integration | `dispute_resolved` closes and outcome counts; holds end cleared / safeguards / declined | FR-B-16, T-10, T-11 | C |
| 14 | Privacy | Integration | No address, coordinates or CNIC in any API response or log | NFR-PR-01, S-07 | C |
| 15 | Transition latency + deployed smoke | Perf/system | P95 recorded; full loop passes on deployed instance | NFR-P-04, D-04 | Freeze |

Write test cases in input / expected / actual format (Form 5). Scenario fixtures are for correctness only; the future held-out attack generator lives in a separate package.

---

## 14. Demo script (15 minutes, on the deployed instance, synthetic users labelled synthetic)

1. **0:00–1:00 (S3):** CCP in one sentence; what changed since proposal (action register).
2. **1:00–6:30 main story (S3):** newcomer request → INSUFFICIENT_EVIDENCE with wide interval and safeguards; borrower with history elsewhere (ES-13) → explanation shows indirect paths (S1 explains); established borrower → SUFFICIENT_EVIDENCE; accept → handover → ACTIVE → return with damage → DISPUTED; next request shows ACTIVE_DISPUTE; moderator decides with reason → COMPLETED; next assessment shows the resolved outcome.
3. **6:30–9:00 edge/failure (S1, S2):** invalid transition rejected and logged; two simultaneous acceptances, one wins; colluding scenario → HELD_FOR_REVIEW with REVIEW_RECOMMENDED, no automatic block; forced engine timeout → HELD_FOR_REVIEW.
4. **9:00–11:00 engineering (S1):** PR blocked by failing check; green pipeline; CD run + smoke test; tag; replay; k = 1..4 latency.
5. **11:00–15:00 (all):** each member opens one file they own and explains one design decision.

Keep a seed-reset script and a local Docker Compose fallback.

---

## 15. Decisions log

### Settled
Single state list · frozen schema (field names unified in v1.1) · "recency-weighted Beta posterior" wording · I4 covers disputes and holds · k-hop in iteration 1 · no interviews or survey (location evidence comes from A11: method comparison, six test cases, threat model, privacy design) · deposits record-only (I-4 closed) · modules = overview's ten · ADR-0001–0004 signed off in A1.

### Decided in Part A — fill in before coding
| Decision | Value |
| :--- | :--- |
| Event-specific data field (N-6) | ______ |
| SUFFICIENT_EVIDENCE rule (min effective evidence, min lower bound) | ______ |
| High-value hold vs REVIEW_RECOMMENDED (N-7) | ______ |
| High-value dissimilarity ratio; velocity, new-account, retaliation windows | ______ |
| How indirect evidence changes the decision | ______ |
| ES-13 expected state | ______ |
| Locality method (A11) | ______ |
| Frontend stack | ______ (NFR-D-05 assumed React Native/Expo) |
| Backend stack | ______ (proposal: Python, FastAPI, PostgreSQL) |

### Still open
| Decision | Settle by |
| :--- | :--- |
| Mid-eval date; how Forms 2 and 3 combine | Ask supervisor now |
| Locality method built in iteration 1 or 2 | D-11 gate |
| Deployment target | D-14 |
| Names for S1/S2/S3 | Before B0 |
| Public trust network: Epinions (instructions, overview) vs Bitcoin OTC (proposal §11.4); YelpChi for robustness | Iteration 2 |
| Success targets: proposal ≥70% accuracy and <5% FP vs NFR-Q-03 TBD | FYP-2 evaluation plan |
| Which stretch module, if any; pilot community and size | End of iteration 2 |
| Whether POC code from the proposal defence exists (overview mentions a Python policy module) | Now |

### Open issues (FR/NFR Part D)
I-3 confirm ENAB items · I-5 search filters after retrieval · I-6 event weights sum 1.05 · I-7 Hungarian vs K matches · I-8 A8 overlaps H1; Admin missing from role list · I-9 verification levels without use cases · I-10 locality method / open-join · I-12 chat as dispute evidence · I-14 household accounts · I-15 search/matching targets are estimates · N-2 missing acceptance criteria · N-3 B13 core but undressed · N-4 project instructions still cite "Beta-Binomial reputation" · N-6, N-7 above.

---

## 16. Module roadmap (iterations 2–4)

| Module | Started | Core part finished | Whole module finished | Evaluated |
| :--- | :--- | :--- | :--- | :--- |
| 1 User & Community | 1 (login, locality design) | 2 (membership, locality A3/A4) | 3 (accounts A1/A2, profile A5, block A7) | 4 (six locality cases, pilot privacy) |
| 2 Events | — | — | 3 only if chosen as stretch | — |
| 3 Resource Sharing | 1 | 2 (B13 scheduler, no-show, extensions, overdue, counter-offer) | 3 (B1 listings, B2 calendar) | 4 (load, regression) |
| 4 Search | 3 | — | 3 (B3, B4; B9–B11 if time) | 4 (precision@k) |
| 5 Trust | 1 | 2 (all roles/metrics, similarity, remaining signals, D1 reviews; ES-07–12) | 3 (D2 trust profile, D7 reporting) | 3 preliminary, 4 full |
| 6 Forum & Chatbot | — | — | 3 only if chosen as stretch | — |
| 7 Communication | 2 (in-app notifications) | — | 3 (G1 chat, email/push) | 4 |
| 8 Vendors | — | — | 3 only if chosen as stretch | — |
| 9 Administration | 1 | 2 (I4 info requests, appeal, reversal; I6 tamper-evident, filters, masking) | 3 (I1–I3) | 4 (pilot moderators) |
| 10 Analytics | 1 (logging, scenarios) | 2 (simulator 50–100 users / 200–300 transactions, baselines, time-ordered holdout, FYP-2 evaluation plan) | 3 (held-out attack generator; J1 if time) | runs evaluation in 4 |

- Stretch: at most one module in iteration 3, only if the core is integrated and evaluation is on track; none in iteration 4.
- Coverage estimate (plan counts, not measurements): core FRs fully met — 12/35 after iteration 1, 30/35 after iteration 2. Recount from passing tests at each gate.
- Iteration 4 evaluation: baselines (global average, role-specific average, recency-weighted average, Beta without indirect, direct only, direct + uncertainty, direct + k-hop, full system); ablations (without uncertainty, without indirect trust, without detection, without context policy); metrics (Brier, log loss, interval coverage/calibration, FPR/FNR, escalation precision/recall, coverage and latency at k = 1..4, fairness new vs established); time-ordered holdout; pilot usability (task completion, SUS, perceived fairness, privacy acceptability) reported separately.

---

## 17. Files

| File | What it is | Where |
| :--- | :--- | :--- |
| `Digital_Mohalla_Project_Overview_Updated.md` | Feature spec, post-defence direction, CCP, engine specification (§5), evaluation | Project files |
| `Digital Mohalla – FYP Project Document.docx.md` | Original proposal (module components §8.1, datasets §11.4, team §14) | Project files |
| `DigitalMohalla_Use_Cases.md` (v1.1) | 68 use cases; 11 dressed; state list, exits, schema | Project files |
| `DigitalMohalla_FR_NFR.md` (v1.1) | FRs, NFRs, traceability, issues, acceptance criteria, framing note | Project files |
| `DigitalMohalla_ADRs.md` | ADR-0001 to 0004 | Project files (`claude/`) |
| `BSFYPHandbook2026_DRAFT.pdf` | FYP process rules, forms, marks, stage requirements | Project files |
| `F26_FYP1_Mid_Report_LaTeX_Complete.pdf` | Mid report template (chapters 1–10, appendices A–F) | Provided in chat |
| Iteration 1 Plan | Full plan with grading, decisions, Part A/B, CI/CD, tests, demo, report checklist, risks | claude.ai doc: https://claude.ai/code/artifact/2e0e828f-f33e-4168-b931-f94acbc7e6f8 |
| Module Roadmap | Iterations 1–4 by module | claude.ai doc: https://claude.ai/code/artifact/a27d2a0e-e8dd-4d36-bef6-579f6e7f8d24 |
| Part A design artefacts | Domain model, state machines, data dictionary, ERD, class, component, layer, sequence, activity, DFD, algorithm design, wireframes, test plan, deployment diagram | **Team's — add to `docs/design/`** |
| `Algorithm_and_Data_Structure_Design.md` | Engine source of truth per overview | **Missing** |

### Known conflicts to keep in mind
- Overview body section numbers differ from its table of contents (§6 onward); the TOC numbering is used.
- Overview Executive Overview uses "AI-powered" framing; don't reuse it.
- Proposal §14 lists trust as shared by all three students, which fails the handbook scope test; §11 replaces it.
- Proposal §13 planned iteration 1 as design-only; mid eval needs a live core module.
- Project instructions: "Beta-Binomial reputation" and "M2–M5 internals" are leftovers.

---

## 18. Report template map (mid report, chapters 4–6 status)

- **Ch. 4 Requirements:** 4.1/4.3 done (v1.1); 4.2 diagram done (A9); 4.4 regroup FRs under the ten modules (4.4.1–4.4.10; FR-T-11 under Module 9); 4.5 map NFRs onto Reliability/Usability/Performance/Security + extras; 4.6 add FR-N-03 and FR-A-04 criteria; 4.7 add design, code and test columns to traceability.
- **Ch. 5 Design:** diagrams done in Part A; each needs 2–4 sentences of rationale + FRs + package (else 50% cap); 5.4 write remaining ADRs; 5.5 design evolution (proposal → post-defence → v1.1) not written; recheck class diagram, ERD and state machine against code at freeze.
- **Ch. 6 Iteration 1:** 6.1–6.3 and 6.7–6.8 writable now; 6.4–6.6 per slice (files, classes, functions, config); 6.9 demo evidence and 6.10 outcome at freeze.
- **Evidence:** Form 10 action register with evidence links; Form 13 disclosure signed by all three; AI usage log countersigned by supervisor; dependency register with licences; GitHub tag, milestone, board, cross-reviewed PRs, no secrets; supervisor meeting records (Appendix F); locality comparison and test cases cited for the location action.
