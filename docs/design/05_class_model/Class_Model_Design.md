# Digital Mohalla: Domain Model (A2) and Class Diagrams (A7)

| Field | Value |
|---|---|
| Owner | Domain model: all three students. Class diagrams: each student their own packages (plan A7). Student 2 and Student 3 diagrams drafted during integration from their own artefacts; **owners to review** (A14) |
| Version | Domain model 1.0 (baseline; decision D18), class diagrams 1.0 (Student 1, Student 2, Student 3); 11 October 2026 |
| Files | `domain_model.drawio`, `class_diagram_s1.drawio`, `class_diagram_s2.drawio`, `class_diagram_s3.drawio`; generators `generate_class_model.py` (domain model, Student 1) and `generate_class_diagrams_s2_s3.py` (Students 2 and 3), sharing one class-drawing helper and one notation |
| Notation | UML 2.5 class diagrams: three compartments (name with optional «stereotype», attributes, operations) plus the FRs each class realises; ◆ composition, ◇ aggregation, solid line association with multiplicities, dashed open arrow dependency (with keyword), dashed hollow triangle realisation; packages as folders |
| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |

## 1. Domain model (A2), v1.0

The twelve classes the plan lists for A2 (User, Community, Membership, Item, BorrowingTransaction, LifecycleEvent, Outcome, TrustEdge, Assessment, EscalationCase, ModeratorDecision, Review), plus three that carry nouns of the dressed use cases: LocalityResult (UC-A3/B5 "coarse locality result"), ConditionReport (UC-B7/B8 "checklist", "confirm condition") and Booking (ADR-0002 "accepted booking").

**Decision D18 (A2 open point of the 2026-10-11 team meeting): the three extra classes stay.** Each is already realised by a table (`locality_verification`, `condition_report`, `booking`), used by an A3 guard (T02–T04, T18/T21, T13) and drawn in sequence (b). Removing them would hide rules the database enforces: the coarse-only locality outcome, the lender-first dual confirmation, and the overlap constraint.

**Noun check (A2 "done when").**

| Noun in the dressed use cases | Class or decision |
|---|---|
| borrower, lender, moderator, admin, member | User (roles via Membership.role and User.platformRole; borrower / lender are association roles) |
| community, neighbourhood, membership | Community, Membership |
| coarse locality result, verification method | LocalityResult |
| invitation code (UC-A3 3d) | Invitation (design class added by A11; single use, hash only) |
| item, listing, deposit | Item (deposit is a record-only attribute, I-4) |
| request, booking, loan, transaction | BorrowingTransaction (the request is its creation event); Booking for the held dates |
| event, event log, audit entry | LifecycleEvent; audit entries are records of Module 9 (Student 3 class diagram) |
| assurance state, evidence summary, safeguards, explanation, manipulation risk, rule | Assessment |
| checklist, photos, condition, deposit received | ConditionReport (photos are attachments of it) |
| verified outcome, resolved outcome | Outcome |
| community path, trust relationship | TrustEdge |
| case, evidence trail, dispute, hold | EscalationCase (the trail is derived from the event log, not stored) |
| decision, reason, appeal, reversal | ModeratorDecision (appeal and reversal are later decisions) |
| review, rating | Review (seeded in iteration 1) |
| chat thread, message, notification, calendar, counter-offer | Deliberately left out of iteration 1 (G1, G3, B2, B6 3b) |

## 2. Class diagram, Student 1 packages (A7)

| Class | Package | FRs / NFRs it realises |
|---|---|---|
| User, Membership, AuthService | accounts | FR-A-04 (part), FR-A-09 (seeded), NFR-S-01, NFR-S-03, NFR-S-07 |
| LocalityResult, Invitation, GeofenceInvitationVerifier (A11), LocalityChecker, StoredResultLocalityChecker | accounts | FR-A-07, FR-A-08, FR-B-07, NFR-PR-02, UC-A3 3d |
| BorrowingService | lifecycle | FR-B-05, B-06, B-07, B-10, B-11, B-13, B-15, B-16, B-17 |
| BorrowingTransaction (aggregate), LifecycleEvent | lifecycle | FR-B-08, FR-B-09, FR-N-03, NFR-R-03, NFR-D-01 |
| TransitionValidator, TransitionTable, Transition, Actor | lifecycle | FR-B-08, NFR-R-02, NFR-S-02, NFR-S-03 |
| EventStore, PostgresEventStore | lifecycle | FR-B-09, FR-M-05, NFR-S-05, ADR-0002 |
| Booking | lifecycle | FR-B-05, NFR-R-01, ADR-0002 |
| ConditionReport | lifecycle | FR-B-11, FR-B-13 |
| TrustEdgeProjector, TrustEdge, TrustGraph, KHopPathSearch, Path, IndirectTrustEngine, IndirectEvidence | assurance.indirect | FR-T-03 (confirmed outcomes only), FR-T-04, NFR-P-03 |
| AssuranceEngine (IAssess), AssessmentResult, OutcomeSink | Student 2 boundary | FR-T-01 to FR-T-07, FR-B-15 |

## 3. Class diagram, Student 2 packages (A7)

| Class | Kind | FRs / NFRs it realises |
|---|---|---|
| IAssess, IOutcomeSink | interfaces | FR-T-01, FR-T-07, FR-B-15, NFR-R-04 |
| AssuranceFacade (realises both) | service | FR-T-01, FR-T-07, FR-B-15, NFR-D-01 |
| ConfigLoader, EngineConfig | service, value | NFR-D-01 |
| OutcomeExtractor, OutcomeEvent | service, value | FR-T-03 |
| BetaPosteriorEstimator, TrustEstimate | service, value | FR-T-02, FR-T-03, ADR-0006 (shared posterior mean) |
| ManipulationDetector, SignalCheck, ReciprocalClustering (S1), ReviewSimilarity (S4), RetaliationCheck, ManipulationSignal, ManipulationRiskAssessment | services, interface, values | FR-T-05, FR-T-09, ADR-0007 |
| DecisionPolicy, TransactionContext, DecisionPolicyResult, SafeguardRecommendation | service, values | FR-T-06, ADR-0003, ADR-0007, ADR-0008 |
| ExplanationBuilder, EvidenceRecord | service, value | FR-T-08, NFR-U-01 |
| AssessmentResult, AssessmentRequest | values | FR-T-01, FR-B-07, NFR-D-01 |

Trust and manipulation risk are separate attributes of AssessmentResult. A timeout raises EngineTimeout, which the lifecycle turns into an `engine_failure` hold. Iteration 2 adds three more SignalCheck realisations.

## 4. Class diagram, Student 3 packages (A7)

| Class | Kind | FRs / NFRs it realises |
|---|---|---|
| IModeration, ICaseIntake | interfaces | FR-T-10, FR-T-11, FR-M-05 |
| CaseService (realises both) | service | FR-T-10, FR-T-11, FR-B-17, UC-D6 2a |
| EvidenceTrailBuilder, EvidenceTrail | service, value | FR-T-10, NFR-PR-03 |
| DecisionService, ModeratorDecision | service, entity | FR-T-11, FR-B-15, ADR-0003, ADR-0004, ES-11 |
| EscalationCase, CaseStatement | entities | FR-T-10, FR-B-17; escalation-case state machine C01–C11 |
| AuditLogService, AuditEntry | service, value | FR-M-05, NFR-S-05 |
| ScenarioSuite, ScenarioFixture, ExpectedResult, ScenarioResult (Module 10) | service, values | NFR-Q-01, test suite 11 |

Module 9 changes lifecycle state only through `ILifecycleCommands.apply_decision()`. The scenario suite tests the engine only through `IAssess`.

## 5. Design reasoning

Lifecycle state and assurance state are attributes of different classes (BorrowingTransaction, AssessmentResult), so ES-04 (HELD_FOR_REVIEW with REVIEW_RECOMMENDED) is representable (plan A7). The aggregate changes state only through `apply(event)`, and `replay(events)` rebuilds it, which is what the replay test checks. The module boundaries are interfaces (`IAssess`, `IIndirectEvidence`, `ILocality`, `ILifecycleCommands`, `IEventQuery`, `ICaseIntake`, `IModeration`), so Slice A runs with stubs, and later slices replace them without touching the callers.
