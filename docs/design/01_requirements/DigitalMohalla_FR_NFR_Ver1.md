# **Digital Mohalla: Functional and Non-Functional Requirements (Baseline v1.3)**

| Field | Value |
| :---- | :---- |
| Version | 1.3 (v1.2 plus the integration decisions of 2026-10-11) |
| Date | 2026-10-11 (v1.1: 2026-10-10; v1.2 and v1.3: 2026-10-11) |
| Authors | Team Digital Mohalla (v1.1 edits drafted with Claude; reviewed by: Fatima Khursheed, Areeba Javed, Minahil Kashif) |
| Status | Requirements baseline: ADR-0001 to ADR-0005 accepted on 2026-10-11; ADR-0007 and ADR-0008 accepted for integration (Students 2 and 3 to initial) |
| Changes | See Part D, "Changes in v1.1", "Changes in v1.2" and "Changes in v1.3" |

**Companion files:** `01_requirements/DigitalMohalla_Use_Cases_Ver1.md` (same IDs, same state list, same terminology) and `03_architecture/DigitalMohalla_ADRs_Ver1.md` (design decisions referenced below as ADR-0001 to ADR-0008).
**Derived from:** Platform Overview (post-defence version) and the Use Case baseline. Every requirement is traced to a use case (UC) or overview section. Items marked ⚠ point to an open issue in Part D.
**Terminology:** direct reliability is a **recency-weighted Beta posterior** (Beta-Binomial is only the predictive distribution). Assurance states describe evidence, not people. High manipulation risk holds a request in moderator review (HELD_FOR_REVIEW); it never restricts automatically.

**Scope tags:** **CORE** = named in the committed core. **ENAB** = core-enabling (core cannot run without it). **SUPP** = supporting. **STRC** = stretch, built only after the core works.
**Evaluation scenarios:** ES-01 new user, ES-02 reliable, ES-03 reliable with one recent dispute, ES-04 colluding, ES-05 retaliatory review, ES-06 high value with weak evidence, ES-07 conflicting condition reports, ES-08 failure to return, ES-09 location mismatch, ES-10 location-permission refusal, ES-11 moderator reversal, ES-12 sparse or old history, ES-13 history with others but none with this lender, reachable through community paths (expected state REVIEW_RECOMMENDED, INSUFFICIENT_EVIDENCE without the paths; ADR-0008). ES-01 to ES-06 and ES-13 are built first.

# **Part A: Functional Requirements**

## **A.1 Accounts and Community (UC A1 to A8)**

| ID | The system shall… | Actor | Source | Scope |
| :---- | :---- | :---- | :---- | :---- |
| FR-A-01 | Register a guest by email or phone (social sign-in optional), show terms and privacy notice, and reject an already-registered identifier without revealing which identifier matched. | Guest | A1, A9 | ENAB |
| FR-A-02 | Create the account as pending and activate it at level "Email/phone verified" only after a valid OTP or link. Limit OTP attempts (default 5, then temporary lock), allow resend with cooldown, and expire unverified pending accounts (default 24 h). | Guest | A1 | ENAB |
| FR-A-03 | Rate-limit registrations per device/IP and record the event as a signal for duplicate-account checks. | System | A1 | ENAB |
| FR-A-04 | Authenticate users, create and invalidate sessions, show a generic error on invalid credentials, lock temporarily after repeated failures (default 5), and support password reset and "log out of all devices". | Member | A2 | ENAB |
| FR-A-05 | Deny login to suspended or banned accounts with a reason category and appeal route, redirect unverified accounts to verification, and require re-verification on a new device. | System | A2 | ENAB |
| FR-A-06 | List communities (nearby if coarse location is permitted, otherwise by name or code) and show each community's rules and available verification methods. | Member | A3 | CORE |
| FR-A-07 | Verify locality with the method selected in design step A11 (a one-time coarse geofence check plus an invitation from a verified member, a moderator deciding anything inconclusive or conflicting), chosen by comparing the candidate methods (Overview §1) on false accepts and rejects, privacy, spoofing resistance and cost. Store only the coarse community and verification outcome, and never store raw location traces or exact addresses. | Member | A3, Overview §1 | CORE |
| FR-A-08 | Treat locality outcomes as three-valued: verified, insufficient/inconclusive (e.g. permission refused, boundary case), or conflicting (possible spoofing). Inconclusive and conflicting outcomes go to moderator review and are never auto-rejected. | System | A3 (3a to 3c) | CORE |
| FR-A-09 | Create membership requests as Pending (or auto-approve for open-join communities and notify moderators), block duplicate requests, and handle closed or full communities. | Member | A3 | CORE |
| FR-A-10 | Give moderators a membership queue showing locality evidence and flags, and let them approve, reject or request more information, with a mandatory reason, limited to their own community. | Moderator | A4 | CORE |
| FR-A-11 | Handle concurrent or reversed moderator decisions by showing current state without re-applying, and keep both decisions in the log on reversal. | Moderator | A4 | CORE |
| FR-A-12 | Let members edit photo, bio, interests, skills and account type, with field validation, per-field visibility (public / community-only / private), a preview, and moderation hold for flagged text. | Member | A5, A6 | ENAB |
| FR-A-13 | Reject or coarsen any exact address entered in a profile, and keep the minimum counterpart information needed for active transactions when visibility is tightened. | System | A5 | CORE |
| FR-A-14 | Let a member block another user (mutual hiding, no new messages or requests), warn when a transaction is active (it continues or goes to a moderator, never silently cancelled), and support unblock. Blocking does not affect official moderation actions. | Member | A7 | ENAB |
| FR-A-15 | Let an eligible member apply for the Vendor or Moderator role (verified contact, community membership, no open dispute). The application creates a Pending request and does not grant the role. | Member | A8 | STRC ⚠I-8 |

## **A.2 Listings and Borrowing Lifecycle (UC B1, B2, B13 enabling; B5 to B8, B12 core)**

| ID | The system shall… | Actor | Source | Scope |
| :---- | :---- | :---- | :---- | :---- |
| FR-B-01 | Let a lender create an item listing with title, description, category, condition, images, terms (deposit, restrictions, usage instructions), availability dates, handover method, approximate location and expiry. Incomplete listings are saved as Draft. | Lender | B1 | ENAB |
| FR-B-02 | Apply stronger restrictions or require a verified account for restricted categories (medical, automotive, high-value electronics). | Lender | B1, I2 | CORE |
| FR-B-03 | Run automated moderation and duplicate checks on listings. Flagged listings go to Pending Review and are not visible in search. If embedding generation fails, publish with keyword search only and retry embedding later. | System | B1 | ENAB |
| FR-B-04 | Maintain an availability calendar per listing. Lenders can block, open, pause or renew, but cannot alter dates covered by held bookings (from acceptance until COMPLETED or NO_SHOW, ADR-0002). Affected pending requests are declined with notification. | Lender | B2 | ENAB |
| FR-B-05 | Guarantee that no two held bookings for the same item overlap; a booking is held from acceptance until the transaction is COMPLETED or NO_SHOW (ADR-0002). Pending requests may overlap (soft hold, ADR-0001). The guarantee is enforced by a database constraint when a request is accepted (ADR-0002): if two acceptances for overlapping dates race, the first to commit wins, the other is refused, its lender is told the dates are taken, and that request ends DECLINED with reason "dates taken". | System | B5, B6, ADR-0001, ADR-0002 | CORE |
| FR-B-06 | Create a borrowing request (REQUEST_CREATED) with dates and optional message, show item terms, mark the dates as requested (soft hold: pending requests do not block dates, ADR-0001), and notify the lender once the request is ASSESSED. Reject duplicates and requests from users blocked by the lender (without revealing the block). | Borrower | B5 | CORE |
| FR-B-07 | On request creation, run the locality eligibility check and then the assurance assessment (FR-T-01) before the lender sees the request. Inconclusive or conflicting locality, corroborated high manipulation risk (ADR-0007), a high-value request with weak or dissimilar evidence (A5 rule R4), or engine failure puts the request in HELD_FOR_REVIEW with a recorded hold reason, never an automatic rejection. The locality check reads the stored coarse result of the member's verification (A11); the request itself carries no location. | System | B5, Overview §3, D3 pre-condition | CORE |
| FR-B-08 | Enforce the single borrowing lifecycle (REQUEST_CREATED, LOCALITY_CHECKED, HELD_FOR_REVIEW, ASSESSED, ACCEPTED, ACTIVE, RETURN_INITIATED, RETURNED, COMPLETED; side states DECLINED, CANCELLED, EXPIRED, NO_SHOW, DISPUTED) so that only valid transitions are accepted and invalid ones are rejected and logged. Exits from HELD_FOR_REVIEW depend on the recorded hold reason (ADR-0003). DISPUTED exits to COMPLETED through `dispute_resolved` or back to the stored previous state through `dispute_withdrawn` (ADR-0004). The full list of valid transitions is the transition table of design step A3. | System | Use Cases §2, B5 to B8, ADR-0003, ADR-0004 | CORE |
| FR-B-09 | Store every transition as an immutable event with the frozen schema (`event_id`, `stream_id`, `stream_seq`, `event_type`, `schema_version`, `actor_id`, `occurred_at`, `previous_state`, `new_state`, `evidence_refs`, `authorisation`, `payload`; assessment events also `config_version`). `payload` holds event-specific data defined per event type in the event catalogue (ADR-0005). Derive current state from the event history and support replay and recovery. Schema additions, including new event types, need sign-off from all three students. | System | Overview §3, Use Cases §2 | CORE |
| FR-B-10 | Let a lender accept, reject (optional reason) or counter-offer dates. Acceptance is committed under the overlap constraint (ADR-0002), blocks the dates, opens a chat thread and auto-declines overlapping pending requests. Unanswered requests expire after a response window. | Lender | B6 | CORE |
| FR-B-11 | Record handover through a condition checklist and photos from the lender and explicit confirmation from the borrower. The booking becomes Active only when both confirm (and a required deposit is recorded as received, record-only). Photo failure allows checklist-only with a "reduced evidence" mark. | Lender, Borrower | B7 | CORE |
| FR-B-12 | Mark unhandled accepted bookings as No-show after reminders and a grace period. Let the borrower dispute the recorded condition. | System | B7 | CORE |
| FR-B-13 | Support return: borrower initiates, lender inspects against the handover checklist and confirms, and the system records return time, compares it with the due date, and completes the booking through `transaction_closed` (late returns recorded as a late outcome). | Borrower, Lender | B8 | CORE |
| FR-B-14 | Support extension requests approved or declined by the lender, and escalate overdue items through reminders and then an automatic dispute. | System | B8, B13 | CORE |
| FR-B-15 | On completion, send the outcome (timeliness, condition agreement, dispute result) to the assurance engine, release the calendar, record deposit release (record-only), and unlock reviews. | System | B8, Overview §3 step 13 | CORE |
| FR-B-16 | Let a party raise a dispute (damage, non-return, condition mismatch, no-show, other) with evidence within the allowed window, while the booking is ACCEPTED, ACTIVE or RETURN_INITIATED. The booking moves to Disputed (previous state stored in the `dispute_opened` event), further transitions and deposit handling freeze, and the evidence trail is compiled for a moderator. | Lender, Borrower | B12 | CORE |
| FR-B-17 | Notify the other party of a dispute, allow a response with evidence, pass the case on when no response arrives, and allow the raising party to withdraw, which restores the previous state through `dispute_withdrawn` (ADR-0004). | System | B12, ADR-0004 | CORE |
| FR-B-18 | Run scheduled jobs (listing expiry, request expiry, handover no-show, return reminders, overdue escalation) as idempotent, locked, logged jobs that retry failures and never send duplicate notifications. | Scheduler | B13 | CORE |

## **A.3 Search, Requests and Matching (UC B3, B4, B9, B10, B11)**

| ID | The system shall… | Actor | Source | Scope |
| :---- | :---- | :---- | :---- | :---- |
| FR-S-01 | Return ranked item results for a query using semantic retrieval plus hybrid re-ranking (similarity, lender evidence, availability, distance, recency), with a short explanation per result. Eligibility filters (community, visibility, state) must be applied inside retrieval or with enough over-fetch to avoid thin results. ⚠I-5 | Borrower | B3, Overview §4 | SUPP |
| FR-S-02 | Fall back to keyword search if embedding or vector index is unavailable, and to a default prior if the assurance service is unavailable. | System | B3 | SUPP |
| FR-S-03 | Support filters (category, radius, dates, price, condition, transaction type) and sort orders (relevance, distance, evidence, newest). | Borrower | B3, Overview §4 | SUPP |
| FR-S-04 | Show item details with the lender's evidence factors and confidence (never a single number), and show "not enough history" for lenders without history. | Borrower | B4 | SUPP |
| FR-S-05 | Log queries, displayed results, clicks and ignored impressions for evaluation. | System | B3 | SUPP |
| FR-S-06 | Let a borrower post an item request when nothing is found, and check it against existing listings. Requests can be cancelled, fulfilled or expire. | Borrower | B9 | SUPP |
| FR-S-07 | Propose request-to-item matches using bipartite matching with fairness constraints. A match is only a proposal: no booking is created without borrower and lender acceptance. ⚠I-7 | System | B10 | SUPP |
| FR-S-08 | Report fairness measures (e.g. Gini coefficient) per matching run and log a warning if disparity remains high. | Admin | B10 | SUPP |
| FR-S-09 | Let a borrower save searches or requests and notify them of new matches. | Borrower | B11 | SUPP |

## **A.4 Trust, Assurance and Safety (UC D1 to D7)**

| ID | The system shall… | Actor | Source | Scope |
| :---- | :---- | :---- | :---- | :---- |
| FR-T-01 | For every borrowing request, return exactly one assurance state (SUFFICIENT\_EVIDENCE, REVIEW\_RECOMMENDED, INSUFFICIENT\_EVIDENCE, ACTIVE\_DISPUTE) with confidence, direct evidence, indirect evidence, manipulation-risk signals, recommended safeguards and an explanation. States describe evidence for the transaction, not the person. | Trust Engine | D3, D4, D5, Overview §5.1, §5.11 | CORE |
| FR-T-02 | Estimate direct reliability per user and per role with a recency-weighted Beta posterior, retain the posterior, and expose a 90% credible interval. A user with no history yields INSUFFICIENT_EVIDENCE ("Insufficient verified history; lender review required"), not a negative result. | Trust Engine | D3, Overview §5.2 to §5.4 | CORE |
| FR-T-03 | Weight evidence by recency and by similarity of category, value band and duration. Count an outcome only once its handover and return confirmations exist. Keep conflicting condition reports uncounted until resolved, and record the resolved outcome afterwards. | Trust Engine | Overview §5.12 | CORE |
| FR-T-04 | Add bounded k-hop indirect evidence (initial k=3, decay 0.7^(hops-1), path-diversity handling), capped below direct evidence. When direct evidence is sparse, reliability ρ ≥ ρ_sup (initial 0.3) moves the state from INSUFFICIENT_EVIDENCE to REVIEW_RECOMMENDED, never to SUFFICIENT_EVIDENCE (ADR-0008), and the explanation lists the paths. All of these are configurable parameters. | Trust Engine | D3, Overview §5.5 | CORE |
| FR-T-05 | Compute manipulation risk (0 to 100\) as a separate dimension from trust using interpretable signals (reciprocal rating clustering, rating velocity, new-account activity, similar review text, linked accounts where legitimately available), and present anomalies with evidence, never accusations. Iteration 1 uses reciprocal clustering, review-text similarity and the retaliation check (ADR-0007). | Trust Engine | D3, Overview §5.6, §5.13 | CORE |
| FR-T-06 | Apply a context-aware decision policy (item value, verification, dispute history, role) that outputs proceed / proceed with safeguards / request verification / restrict high-value / escalate. Trust and manipulation risk are never averaged. Corroborated high manipulation risk (level 4: ≥ 60 with at least two signals ≥ 0.5, ADR-0007) holds the request in moderator review (HELD_FOR_REVIEW) and does not restrict automatically; an uncorroborated score ≥ 60 is level 3 (request verification). A high-value request with weak or dissimilar evidence is held for a moderator (rule R4, N-7 resolved). The rules, their order and their states are the A5 decision table (Algorithm doc §6). | Trust Engine | D3, Overview §5.6, §5.8 | CORE |
| FR-T-07 | If the engine fails or times out, put the request in HELD_FOR_REVIEW with hold reason `engine_failure` and log the failure, never assigning a default state. | System | D3 (\*a), ADR-0003 | CORE |
| FR-T-08 | Show assurance factors separately with confidence and suppress detail when observations are too few to display safely. Never show a single trust number to users. | Member | D2, B4, Overview §5.7 | CORE |
| FR-T-09 | Accept reviews only from parties to a Completed transaction, with multi-dimension ratings, one review per party, and a short edit window. Flag suspected retaliation (follows a dispute, conflicts with confirmed records) and near-identical text, with reduced weight pending review. | Member | D1 | CORE |
| FR-T-10 | Create an escalation case with trigger type (dispute, manipulation flag, high-value low-confidence, locality hold, engine failure) and an evidence trail (transaction, value, both claims, photos, relevant messages, history, trust analysis, manipulation signals), priority and reason. Attach to an existing case rather than duplicating, and route to Admin if no moderator is available. | Trust Engine | D6, Overview §5.9 | CORE |
| FR-T-11 | Let a moderator resolve an escalated case or dispute: request more information with a deadline, decide with a mandatory reason, and record the outcome. A dispute closes through `dispute_resolved` (DISPUTED → COMPLETED) and the resolved outcome becomes evidence. A non-dispute hold ends as cleared or safeguards imposed (`hold_cleared`, next state set by the hold reason, ADR-0003) or restricted (`request_declined`, only by human decision). Support appeal to a second moderator and later reversal (both decisions retained, affected evidence flagged). | Moderator | D6, I4, ADR-0003, ADR-0004 | CORE |
| FR-T-12 | Let members report a user, item, event or post with category, description and evidence. Flag clustered reports against one user as possible reporting abuse, and prioritise immediate-safety reports. | Member | D7 | ENAB |

## **A.5 Administration, Moderation and Audit (UC I1 to I6)**

| ID | The system shall… | Actor | Source | Scope |
| :---- | :---- | :---- | :---- | :---- |
| FR-M-01 | Let an admin suspend, ban or change roles with a mandatory reason. Actions against another admin need additional authorisation, sessions are invalidated on suspend/ban, and users with active transactions are routed to moderator handling. | Admin | I1 | ENAB |
| FR-M-02 | Let an admin create, edit and deactivate communities (boundary, rules, verification methods) and categories, detecting duplicates and requiring a disposition for active listings. | Admin | I2 | ENAB |
| FR-M-03 | Give moderators a prioritised report queue with decisions (remove, keep, warn, escalate), mandatory reasons, appeal to a second moderator, and escalation to Admin when a moderator is involved. | Moderator | I3 | ENAB |
| FR-M-04 | Automatically flag spam, profanity, duplicates and suspicious links, route uncertain (e.g. mixed English/Urdu) content to human review, and never permanently remove content automatically. | System | I5 | SUPP |
| FR-M-05 | Write every privileged action and state transition to a tamper-evident audit log (actor, timestamp, previous/new state, evidence, authorisation). Support filtering, mask sensitive data, highlight concentration patterns in a moderator's decisions, and log log-views themselves. | Admin | I6, Overview §5.13 | CORE |

## **A.6 Communication and Notifications (UC G1 to G4)**

| ID | The system shall… | Actor | Source | Scope |
| :---- | :---- | :---- | :---- | :---- |
| FR-C-01 | Provide a chat thread linked to an item or booking, screening messages for abuse, spam and suspicious links, with message reporting, block handling (without revealing the block) and read-only status after the retention period. | Member | G1 | ENAB |
| FR-C-02 | Offer a shared notify(user, type, payload) service covering in-app, email and push channels, with template rendering, duplicate suppression, digesting, and retry on delivery failure. | Modules | G3 | ENAB |
| FR-C-03 | Let members set notification preferences per type and channel with quiet hours, while critical types (security, dispute) stay on. | Member | G4 | SUPP |

## **A.7 Analytics and Evaluation Support (UC J1, J2)**

| ID | The system shall… | Actor | Source | Scope |
| :---- | :---- | :---- | :---- | :---- |
| FR-N-01 | Show an admin dashboard (active users, requests, completed borrowings, reports/disputes, assurance-state distribution) and suppress figures for communities below a minimum sample threshold (threshold TBD). | Admin | J1 | SUPP |
| FR-N-02 | Show a member only their own activity and evidence-factor history. | Member | J2 | SUPP |
| FR-N-03 | Record all events needed for project evaluation under the frozen event schema (FR-B-09), agreed up front. | System | Overview §3, §11 | CORE |

## **A.8 Stretch Modules (condensed)**

| ID | The system shall… | Actor | Source | Scope |
| :---- | :---- | :---- | :---- | :---- |
| FR-EV-01 | Let organizers create, edit, postpone and cancel events (Draft state, validation, duplicate warning, approximate location only) and notify registrants of material changes. | Organizer | C1 | STRC |
| FR-EV-02 | Route event publication through moderator approval when the community requires it, with the organizer's evidence summary shown. | Organizer, Moderator | C2 | STRC |
| FR-EV-03 | Support event browse and search with visibility-aware results and logged searches and clicks. | Member | C3 | STRC |
| FR-EV-04 | Register and cancel registrations atomically without exceeding capacity, with eligibility checks, waitlist with auto-promotion, and check-in by QR/short code with manual fallback. | Attendee | C4, C5, C6 | STRC |
| FR-EV-05 | Support agenda/volunteers (C7, marked "do we need it?" in the source), event announcements, polls and Q\&A (C8), and post-event feedback limited to attendees (C9). | Organizer | C7, C8, C9 | STRC |
| FR-EV-06 | Recommend events with an explained, normalised score and a cold-start fallback. ⚠I-6 | Member | C10, Overview §2 | STRC |
| FR-EV-07 | Provide event group discussion for registrants and organizers with moderation and read-only after completion. | Attendee | G2 | STRC |
| FR-FO-01 | Support forum post create/edit/delete with moderation screening and rate limiting, and comments, replies and one vote per member per item. | Contributor | E1, E2 | STRC |
| FR-FO-02 | Support best-answer marking (E3), search and filter (E4), follow/save (E5), and transparent-criteria badges with Verified expert granted only by an admin (E6). | Contributor | E3 to E6 | STRC |
| FR-CB-01 | Answer questions via routed retrieval (unstructured for policy/forum, whitelisted parameterised queries for events/items), with filters applied inside retrieval, reranking, enforced per-claim citation and groundedness verification. | Member | F1 | STRC |
| FR-CB-02 | Abstain with a low-confidence response and offer escalation to forum or admin when confidence is low or no permitted passages exist. | Member | F1, F2 | STRC |
| FR-CB-03 | Refuse out-of-scope intents, never resolve disputes, explain assurance factors only, and strip personal identifiers from output. | System | F1 | STRC |
| FR-CB-04 | Support answer feedback (F3), admin knowledge-base management with pipeline screening for prompt injection (F4), and a content-gap report (F5). | Member, Admin | F3 to F5 | STRC |
| FR-VD-01 | Support vendor registration, admin verification (approve / reject / request information), product and service listings for verified vendors only, nearby vendor search, inquiries and eligibility-gated reviews. | Vendor | H1 to H5 | STRC ⚠I-8 |
| FR-NA-01 | Show neighbourhood activity and responsiveness metrics with a minimum-sample suppression rule and user-set comparison weights. Safety and dispute indicators are excluded. | Guest, Member | J3 | STRC |

# **Part B: Non-Functional Requirements**

Numeric gates are kept only where iteration 1 can measure them: NFR-R-01 to R-03, P-03 (direct evidence only), P-04, S-02, S-05, D-01, D-04, and Q-01 (7 of 13 scenarios at Mid-1). All other targets are set in iteration 2 after a baseline exists. **[doc]** comes from the overview, **[proposed]** is a team proposal awaiting approval, **[TBD]** has no defensible value yet. Every NFR has a stated verification.

## **B.1 Correctness and Reliability**

| ID | Requirement | Verification | Basis |
| :---- | :---- | :---- | :---- |
| NFR-R-01 | No double-booking under concurrency: with N simultaneous acceptances for overlapping dates on one item, exactly one commits (100% over repeated runs). | Concurrency test harness | FR-B-05, ADR-0002 |
| NFR-R-02 | Invalid lifecycle transitions are rejected 100% of the time. | State-transition test matrix | FR-B-08 |
| NFR-R-03 | Replaying the event log reproduces the stored current state exactly for every test transaction. | Replay test | FR-B-09 |
| NFR-R-04 | Graceful degradation: embedding/vector failure falls back to keyword search, assurance unavailable falls back to prior plus safeguards, engine failure routes to human review. | Fault-injection tests | B3, D3 |
| NFR-R-05 | Scheduled jobs are idempotent: a rerun produces no duplicate state changes or notifications. | Rerun test | FR-B-18 |
| NFR-R-06 | Availability during pilot hours is monitored and reported; numeric target set in iteration 2. | Uptime monitoring | [proposed] |

## **B.2 Performance and Scalability**

| ID | Requirement | Verification | Basis |
| :---- | :---- | :---- | :---- |
| NFR-P-01 | Vector retrieval latency for the top-100 candidates is benchmarked and reported; numeric target set in iteration 2. | Latency benchmark | [doc] states a latency intent |
| NFR-P-02 | End-to-end search response time is measured under load and reported; numeric target set in iteration 2. | Load test | [proposed] |
| NFR-P-03 | The assurance assessment using **direct evidence only** completes with P95 ≤ 1 s at dataset scale. Latency for k = 1 to 4 is reported but not gated in iteration 1. | Benchmark | [proposed] |
| NFR-P-04 | State transition commit P95 ≤ 500 ms. | Load test | [proposed] |
| NFR-P-05 | A matching run on a synthetic set is timed and reported; numeric target set in iteration 2. | Benchmark | [doc] says "500+"; [proposed] |
| NFR-P-06 | The system is load-tested at pilot size and the result reported; numeric target set in iteration 2. | Load test | [proposed] |

## **B.3 Decision Quality (Technical Evaluation)**

| ID | Requirement | Verification | Basis |
| :---- | :---- | :---- | :---- |
| NFR-Q-01 | At Mid-1 the pipeline returns the documented expected state **and** a correct evidence-based explanation on at least 7 of the 13 evaluation scenarios (ES-01 to ES-06 and ES-13). Final target 13 of 13. A scenario passes only if state and explanation both match. | Scenario suite | [doc]; Mid-1 threshold [proposed] |
| NFR-Q-02 | The full system beats the global-average and role-specific-average baselines on Brier score and calibration; every component is justified by the ablation study. | Baseline and ablation study | \[doc\] |
| NFR-Q-03 | False trust rate, false suspicion rate, manipulation-detection rate and false-positive rate are measured and reported on controlled cases. | Controlled manipulation tests | \[doc\]; numeric targets \[TBD\] until baseline exists |
| NFR-Q-04 | Location-verification false accepts and false rejects are measured on the six listed test cases. | Locality test cases | \[doc\]; targets \[TBD\] |
| NFR-Q-05 | Search precision@k and gain over the keyword baseline are measured on 20 to 30 hand-labelled queries; numeric targets are set after the baseline is measured (⚠I-15). | Offline evaluation | [doc] (estimate) |
| NFR-Q-06 | Matching reports the Gini coefficient, confirms no item is over-matched, and measures acceptance of proposed matches; numeric targets set after the pilot (⚠I-15). | Synthetic set plus pilot | [doc] (estimate) |
| NFR-Q-07 | Assurance fairness between new and established users is reported. | Fairness analysis | \[doc\] |

## **B.4 Security**

| ID | Requirement | Verification | Basis |
| :---- | :---- | :---- | :---- |
| NFR-S-01 | Passwords are stored only as salted hashes (bcrypt or argon2), and all traffic uses TLS. | Config review | \[proposed\] |
| NFR-S-02 | Every state transition and privileged action checks the actor's authorisation and records it; 100% of attempts without valid authorisation are rejected and logged. | Authorisation test matrix | [doc] |
| NFR-S-03 | Role-based access: a moderator can act only in their own community, and members see only permitted data. | Access-control tests | A4, J1 |
| NFR-S-04 | OTP, login and registration are rate-limited. | Abuse tests | A1, A2 |
| NFR-S-05 | The audit log is append-only and tamper-evident; 100% of modified or deleted test entries are detected by the integrity check. | Tamper test | I6 |
| NFR-S-06 | Uploads are validated by type and size, and user content is screened before display. | Upload tests | A5, B1 |
| NFR-S-07 | Identity document numbers (e.g. CNIC) are not stored. | Data review | Community Connect exclusions |

## **B.5 Privacy**

| ID | Requirement | Verification | Basis |
| :---- | :---- | :---- | :---- |
| NFR-PR-01 | Exact location never appears in profiles, listings, API responses or logs. | Automated privacy checks | \[doc\] §13 |
| NFR-PR-02 | Raw location traces are not persisted. Retention period for coarse results is \[TBD\]. | Data review | \[doc\] |
| NFR-PR-03 | Chat content is accessible to moderators only for a disputed or reported transaction. ⚠I-12 | Access test | G1, I4 |
| NFR-PR-04 | Metrics for small communities are suppressed below a minimum sample threshold \[TBD\]. | Test | J1, J3 |
| NFR-PR-05 | Pilot and usability-test data are collected with consent, with the right to withdraw, and anonymised. Applicable Pakistani data-protection obligations are to be confirmed with the supervisor. | Consent records | Overview |

## **B.6 Explainability and Usability**

| ID | Requirement | Verification | Basis |
| :---- | :---- | :---- | :---- |
| NFR-U-01 | Every screen showing an assurance state also shows its supporting evidence, never a single trust number. | UI review | \[doc\] |
| NFR-U-02 | First-time test users attempt request to handover confirmation without assistance; completion rate, time and errors are reported; numeric target set in iteration 2. | Usability test | [proposed] |
| NFR-U-03 | A SUS usability score is collected and reported; numeric target set in iteration 2. | SUS survey | [proposed] |
| NFR-U-04 | Perceived fairness and understanding of the assurance explanation are measured with residents. | Survey | \[doc\] |
| NFR-U-05 | Interface language (English only, or Urdu/Roman Urdu) is \[TBD\]. Chatbot Urdu-English handling is a stretch item. | Decision | open question |

## **B.7 Maintainability and Deployment**

| ID | Requirement | Verification | Basis |
| :---- | :---- | :---- | :---- |
| NFR-D-01 | Trust parameters (prior, decay, k, cap, thresholds, recency rate) live in versioned configuration, and 100% of stored assessments record the `config_version` used. | Config test | [doc] |
| NFR-D-02 | A person outside the team can install and run the system from documentation in a clean environment. | Clean-install test | School guide |
| NFR-D-03 | Deployment target and rollback are rehearsed before release. Target per the confirmed stack is AWS. | Deployment rehearsal | School guide |
| NFR-D-04 | The state machine, assurance pipeline and privacy checks have automated tests that run on every build; a failing test blocks the merge. | CI report | [doc] §13 |
| NFR-D-05 | Client platform is Android and iOS via React Native/Expo (assumption from the stack, to be confirmed). | Device test | \[proposed\] |

# **Part C: Traceability**

Every use case ID in the Use Case baseline maps to at least one FR through the Source column (A9 via FR-A-01, A6 via FR-A-12). The table below traces the core chain. Verification of NFRs is listed in Part B.

| UC | FRs | NFRs | Evaluation scenarios |
| :--- | :--- | :--- | :--- |
| B5 | FR-B-05, B-06, B-07, B-08, B-09 | NFR-R-02, R-03, P-04, S-02 | ES-01, ES-06, ES-09, ES-10 |
| B6 | FR-B-05, B-10 | NFR-R-01, S-02 | ES-01 |
| B7 | FR-B-11, B-12 | NFR-R-02, S-02 | none |
| B8 | FR-B-13, B-14, B-15 | NFR-R-02, R-03 | ES-08 |
| B12 | FR-B-16, B-17 | NFR-R-02, S-02 | ES-07, ES-08 |
| D3/4/5 | FR-T-01 to T-07 | NFR-P-03, D-01, Q-01 | ES-01 to ES-07, ES-11, ES-12, ES-13 |
| D1, D2 | FR-T-08, T-09 | NFR-U-01 | ES-05 |
| D6 | FR-T-10 | NFR-R-04, PR-03 | ES-04, ES-07 |
| I4 | FR-T-11 | NFR-S-02, S-03 | ES-07, ES-11 |
| I6 | FR-M-05 | NFR-S-02, S-05 | ES-11 |
| A3, A4 | FR-A-06 to A-11 | NFR-Q-04, PR-01, PR-02 | ES-09, ES-10 |
| All events | FR-B-09, N-03 | NFR-R-03, D-01 | all |

# **Part D: Issues**

**Resolved in v1:** I-1 (B5 5b now holds in review), I-2 (single lifecycle from Overview §3; B5 has locality and assessment steps), I-3 for A1, A2, G1, G3 (tagged ENAB, Core-enabling), I-13 (module labels, housekeeping only).

**Resolved in v1.1:** I-4 (deposits are record-only; the system never moves money), N-1 (72 came from Part C of the previous FR/NFR draft; the correct count is 68), I-11 (interview dependency removed; the team does not run interviews or a survey).

**Resolved in v1.2 (team decisions of 2026-10-11):** N-5 (ADR-0001 to ADR-0004 accepted, with the ADR-0002 wording amendment), N-6 (event-specific data stored in `payload`, ADR-0005).

**Resolved in v1.3 (integration decisions of 2026-10-11):** N-7 (A5 rule R4 holds a high-value request with weak or dissimilar evidence; with strong similar evidence it reaches the lender, rule R8).

**Changes in v1.1**

| # | Change | Affects |
| :---- | :---- | :---- |
| A0 | Use case count corrected to 68; interview dependencies removed (FR-A-07, NFR-PR-05, I-10, I-11); deposits confirmed record-only (I-4); document control block added | FR-A-07, NFR-PR-05, Part D |
| ADR-0001 | Soft hold: pending requests mark dates as requested and block nothing | FR-B-05, B-06, Part E |
| ADR-0002 | Overlap constraint enforced by the database at acceptance; replaces "lower `stream_seq` wins" | FR-B-05, B-10, NFR-R-01, Part E |
| ADR-0003 | HELD_FOR_REVIEW exits by hold reason; new event type `hold_cleared` | FR-B-07, B-08, T-07, T-11 |
| ADR-0004 | New event types `dispute_resolved` and `dispute_withdrawn` | FR-B-08, B-16, B-17, T-11, Part E |
| Schema spelling | FR-B-09 now uses the field names of Use Cases §2 (`actor_id`, `occurred_at`, `previous_state`, `new_state`, `evidence_refs`) | FR-B-09 |
| ES-13 | Scenario added so indirect evidence has a case that exercises it | Header, NFR-Q-01, Part C, Part E |

**Changes in v1.2**

| # | Change | Affects |
| :---- | :---- | :---- |
| D1, ADR-0005 | `payload` added to the frozen event record; N-6 resolved | FR-B-09 |
| D3 | ADR-0001 to ADR-0004 accepted; N-5 resolved | header, Part D |
| D4 | No dispute from RETURNED | FR-B-16 |
| D6 | ADR-0002 wording: bookings held until COMPLETED or NO_SHOW | FR-B-05 |
| A11 | Locality method selected (geofence + invitation, moderator fallback); I-10 narrowed to open-join only | FR-A-07, Part D |

**Changes in v1.3**

| # | Change | Affects |
| :---- | :---- | :---- |
| D10, ADR-0007 | Manipulation hold needs corroboration (level 4); S4 active in iteration 1 | FR-T-05, FR-T-06, Part E |
| D11, ADR-0008 | Community paths lift sparse evidence to REVIEW_RECOMMENDED; ES-13 expected state set | FR-T-04, header |
| N-7 | Resolved by A5 rule R4 | FR-B-07, FR-T-06, Part D |
| D13 | Locality at request time reads the stored result (A11) | FR-B-07 |
| D6 (follow-up) | FR-B-04 wording: held bookings, not "Accepted or Active" | FR-B-04 |

**Still open**

| # | Severity | Finding | Suggested fix |
| :---- | :---- | :---- | :---- |
| I-3 | Medium | Remaining ENAB items (B1/B2, I1/I2/I3, D7) still need team confirmation as core-enabling | Confirm |
| I-5 | Medium | Search filters applied after top-100 retrieval | Per-community index or filtered vector query |
| I-6 | Medium | Event recommendation weights sum to 1.05 | Normalise to 1.00 |
| I-7 | Medium | Hungarian matching is one-to-one but B10 allows K matches per item; fairness boost must not contradict "no history is not negative" | Replicate items K times or use min-cost flow |
| I-8 | Medium | A8 (vendor role) overlaps H1; Admin missing from the overview role list | Merge A8-Vendor into H1; add Admin |
| I-9 | Medium | Identity, organizer and vendor verification levels have no use case | Drop or define |
| I-10 | Medium | Locality method decided in A11 (geofence + invitation); open-join communities still bypass locality | Open-join must still record a locality outcome (team to confirm) |
| I-12 | Low | Chat as dispute evidence vs privacy (NFR-PR-03) | Confirm rule |
| I-14 | Low | Household accounts vs per-person evidence | Decide |
| I-15 | Low | Search and matching targets are estimates, not measurements | Measure baseline first |
| N-2 | Low | Other CORE FRs have no acceptance criteria yet: FR-A-06 to A-11, A-13, B-02, B-18, N-03 (A-06 to A-11 matter once A3/A4 are built) | Add when A3/A4 are scheduled |
| N-3 | Low | B13 is tagged CORE but is in Appendix B only | Promote if the supervisor wants it dressed |
| N-4 | Low | Project instructions still say "Beta-Binomial" | Team to update the instructions to "recency-weighted Beta posterior" |

# **Part E: Acceptance Criteria (core FRs)**

One Given/When/Then per FR, with at most one "And" for the key edge case.

| FR | Given | When | Then | And | UC / ES |
| :---- | :---- | :---- | :---- | :---- | :---- |
| FR-B-05 | Two ASSESSED requests for the same item with overlapping dates | Their lenders' acceptances are submitted at the same moment | Exactly one commits as ACCEPTED; the database refuses the other, whose lender is told the dates are taken | The refused request ends DECLINED with reason "dates taken", logged as an event | B6 / none |
| FR-B-06 | A published item and a borrower the lender has not blocked | The borrower submits a request for dates another pending request already covers | The request is created in REQUEST_CREATED, its dates are marked as requested and `request_created` is logged | If the lender has blocked the borrower, the request is denied with no mention of the block | B5 / none |
| FR-B-07 | A request in REQUEST_CREATED | The locality check returns *verified* | An assessment is stored before the lender can see the request | If locality is inconclusive, the request goes to HELD_FOR_REVIEW with hold reason `locality_inconclusive` and is not rejected | B5 / ES-09, ES-10 |
| FR-B-08 | A booking in COMPLETED | A transition to ACCEPTED is attempted | The transition is rejected and logged with the reason | Clearing a locality hold returns the request to LOCALITY_CHECKED, never directly to ASSESSED | B5 to B8 / none |
| FR-B-09 | A transaction with N logged events | The state is rebuilt by replaying the events in `stream_seq` order | The rebuilt state equals the stored current state | Every event carries `event_type` and `schema_version` | all / none |
| FR-B-10 | An ASSESSED request and an authorised lender | The lender accepts | The request is ACCEPTED, dates are blocked, a chat thread opens and overlapping pending requests are DECLINED | A request unanswered past the window becomes EXPIRED | B6 / none |
| FR-B-11 | An ACCEPTED booking | The lender submits the checklist and photos and the borrower confirms receipt | The booking becomes ACTIVE with timestamps and a due date | If a required deposit is not recorded, the booking stays ACCEPTED | B7 / none |
| FR-B-12 | An ACCEPTED booking whose handover time and grace period have passed | The scheduler runs | The booking becomes NO_SHOW and the dates are released | The borrower can raise a condition dispute before confirming | B7 / none |
| FR-B-13 | An ACTIVE booking | The borrower initiates return and both parties confirm condition | The booking passes RETURNED to COMPLETED through `transaction_closed` and the return time is compared with the due date | A late return is recorded as a late outcome | B8 / ES-02 |
| FR-B-14 | An ACTIVE booking past its due date with reminders unanswered | The overdue limit is exceeded | A dispute is opened automatically and the booking is DISPUTED | An approved extension moves the due date instead | B8 / ES-08 |
| FR-B-15 | A booking closing with confirmed handover and return | The booking reaches COMPLETED | The outcome is sent to the engine, the calendar is freed and reviews unlock | An outcome under dispute is not counted until resolved | B8 / ES-07 |
| FR-B-16 | A booking in an allowed state inside the dispute window | A party raises a dispute with a reason and evidence | The booking is DISPUTED with its previous state stored, transitions and the deposit record are frozen and a case is queued | A second dispute on the same booking shows the existing case | B12 / ES-07 |
| FR-B-17 | An open dispute | The other party does not respond within the period | The case is marked "no response" and passed to a moderator | If the raising party withdraws, `dispute_withdrawn` restores the previous state | B12 / none |
| FR-T-01 | A request whose locality is verified | The assessment runs | Exactly one of the four assurance states is returned with confidence, direct and indirect evidence, manipulation signals, safeguards and explanation | No single trust number is shown | D3/4/5 / ES-01 to ES-07 |
| FR-T-02 | A user with no verified history | The assessment runs | The state is INSUFFICIENT_EVIDENCE with "Insufficient verified history; lender review required" | The estimate is the prior Beta(1,1) with a wide credible interval | D3 / ES-01 |
| FR-T-03 | Two outcomes aged 10 and 360 days and a 180-day half-life | Evidence weights are computed | Weights are about 0.96 and 0.25 | Unconfirmed or conflicting outcomes are excluded | D3 / ES-02, ES-12 |
| FR-T-04 | A target reachable from the lender by two paths of at most 3 hops via different first hops | Indirect evidence is computed | Reliability is at most 0.6 and uses decay 0.7^(hops−1) | Paths longer than 3 hops are ignored | D3 / ES-12, ES-13 |
| FR-T-05 | A small group of accounts exchanging similar, closely timed positive ratings | Manipulation risk is computed | A 0 to 100 risk value is shown separately from trust, with the signals and evidence | The wording describes anomalies and does not accuse a user | D3 / ES-04 |
| FR-T-06 | A request with strong trust and corroborated manipulation risk ≥ 60 (two signals ≥ 0.5) | The decision policy runs | The request is HELD_FOR_REVIEW with hold reason `manipulation_risk`, a case is created, trust and risk are shown separately, and nothing is restricted before a moderator decides | A score ≥ 60 from a single signal is level 3: the request reaches the lender as REVIEW_RECOMMENDED with a verification safeguard | B5, D3 / ES-04 |
| FR-T-07 | An injected engine timeout | A request is assessed | The request goes to HELD_FOR_REVIEW with hold reason `engine_failure` and the failure is logged | No assurance state is assigned | D3 / none |
| FR-T-08 | A user with too few observations | A member opens the trust profile | Factors are shown separately with confidence and the detail is suppressed | No single number appears anywhere | D2 / ES-01 |
| FR-T-09 | A COMPLETED transaction | A party submits a review | The multi-dimension review is stored and linked to the transaction | A negative review right after the other party's complaint that conflicts with records is flagged and down-weighted | D1 / ES-05 |
| FR-T-10 | An escalation trigger such as a dispute or a manipulation flag | The case is created | It carries trigger type, priority, reason and the full evidence trail | A case already open for the transaction is reused | D6 / ES-04, ES-07 |
| FR-T-11 | An open dispute and an authorised moderator | The moderator submits a decision with a reason | `dispute_resolved` moves the booking to COMPLETED, the decision is logged and the resolved outcome becomes evidence | A later reversal keeps both decisions and flags the affected evidence | I4 / ES-11 |
| FR-M-05 | Any privileged action or lifecycle transition | It is performed | An audit entry with actor, timestamp, previous and new state, evidence and authorisation exists | An attempt to alter the entry is detected | I6 / ES-11 |

# **Part F: Framing note for report chapter 1**

Do not reuse the overview's Executive Overview ("AI-powered matching", "AI layer"). Suggested replacement: *Digital Mohalla is a neighbourhood borrowing and lending platform. Its central computing problem is to decide whether a proposed loan has enough trustworthy evidence when history is sparse, role-dependent and possibly manipulated, while protecting location privacy and sending uncertain cases to people. A recency-weighted Beta posterior, bounded indirect evidence and interpretable manipulation signals produce an explained assurance state; the platform never labels a person or issues a single trust score.* Use the spelling "Mohalla" throughout.
