# Class Diagram and Domain Model, Iteration 2 (DA-11)

| Field | Value |
|---|---|
| Owner | All three students, each for their own packages (plan A7): Fatima Khursheed (Modules 1, 3, the indirect-trust part of 5, search retrieval), Areeba Javed (Module 5, search ranking, Module 7; drawn by Fatima for Areeba's sign-off), Minahil Kashif (Modules 9, 10, uploads, search logging). Domain model: all three |
| Version | 3.0 draft, 13 November 2026. 2.0 (3 November) showed only the iteration 2 additions; 2.1 (13 November) drew them per student on two pages; 3.0 draws **one class diagram for the whole system** |
| Status | Draft for review by all three students |
| Files | `class_diagram.drawio` (+ `class_diagram.png`, `class_diagram.pdf`), built by `generate_class_diagram.py`; `domain_model.drawio` (`generate_class_model.py`) |
| Iteration 1 versions | `archive_v1/class_diagram_s1_iteration1.drawio`, `class_diagram_s2_iteration1.drawio`, `class_diagram_s3_iteration1.drawio`, `domain_model_iteration1.drawio` |
| GenAI | Drafted with Claude (Claude Code); reviewed by the owners. Logged in `docs/ai-usage-log.md` and on Form 13 |

## 1. One diagram, one model

The design has one class model, so it is drawn as one class diagram. Every design class of the three students appears **once**, in the package of the module that owns it:

| Area of the diagram | Packages | Owner |
|---|---|---|
| Top left | `accounts` (Module 1), `lifecycle` (Module 3), `assurance.indirect` (Module 5) | Student 1 |
| Below them | `accounts.membership`, `lifecycle.listings and scheduling`, `search.retrieval` (Module 4) | Student 1, new in iteration 2 |
| Top right | `assurance` (Module 5), with the five manipulation signals | Student 2 |
| Below it | `assurance.reviews and lender evidence`, `search.ranking` (Module 4), `notifications` (Module 7) | Student 2, new in iteration 2 |
| Bottom | `moderation` (Module 9), `uploads`, `search logging` (Module 4), `evaluation` (Module 10), the interfaces Module 9 uses | Student 3 |

A package name with a dot is part of one module (`accounts.membership` is Module 1; `search.retrieval`, `search.ranking` and `search logging` are the three parts of Module 4).

**How dependencies between modules are shown.** Inside a package every relationship is drawn. Between modules, a class depends on an interface or class of another module through the type in its attribute or operation (for example `- notify: INotify`, `- engine: AssuranceEngine`, `- ranker: HybridRanker`), and the module-level dependencies are drawn once in the component diagram (`03_architecture/component_diagram.drawio`). Drawing every such dependency as a line across a diagram of this size would hide the structure. Lines cross package borders only where one class uses another directly:

- RegistrationService «create» User;
- InvitationService uses GeofenceInvitationVerifier;
- BorrowingTransaction ◆ CounterOffer (0..1, rebuilt from its events, ADR-0015);
- JobRunner acts through BorrowingService (ADR-0012).

**Colour and marking** (the convention of the whole design set): fill colour = owner (blue S1, orange S2, purple S3); **green text** = member or value added or changed in iteration 2; **green border** = class new in iteration 2. Each class names the FRs it realises.

**Reading it.** `class_diagram.png` (about 5300 × 5400 px) can be zoomed; `class_diagram.pdf` is the vector copy, sharp at any zoom. In draw.io, use *View → Outline* to move around.

## 2. Student 1 packages

| Package | Classes | Design reasoning |
|---|---|---|
| accounts (Module 1) | User (+ `terms_accepted_at`), Membership, LocalityResult, Invitation, GeofenceInvitationVerifier, LocalityChecker, StoredResultLocalityChecker, AuthService | As iteration 1; the verifier, designed in A11, is built in iteration 2 |
| accounts.membership (Module 1) | RegistrationService, MembershipService, InvitationService, MembershipDecision, MembershipDecisionKind | `MembershipService.request_join()` approves at once only in an OPEN community with a VERIFIED result (membership M09, UC-A3 4a); every other request waits for a moderator |
| lifecycle (Module 3) | BorrowingService (+ six operations), BorrowingTransaction, LifecycleEvent, TransitionValidator, TransitionTable (lifecycle v3, 39 rows), Transition, EventStore, PostgresEventStore, Booking, ConditionReport, the enumerations (+ 3 event types, Possession), Actor | Lifecycle v3 changes only rows and values, not the structure (ADR-0009, ADR-0015) |
| lifecycle.listings and scheduling (Module 3) | CounterOffer, ListingService, Item, JobRunner, Job, NoShowJob, OverdueJob, ExpiryJob, JobRunStore | Jobs act only through BorrowingService, so the scheduler passes the same validator, guards and audit as a user |
| assurance.indirect (Module 5, S1 part) | TrustEdgeProjector, TrustEdge, TrustGraph, KHopPathSearch, Path, IndirectEvidence, IndirectTrustEngine | Unchanged from iteration 1 |
| search.retrieval (Module 4, S1) | ISearch, SearchService, SearchFilters, Candidate, SearchResults | One SQL query computes the full-text rank and the vector distance with the eligibility filters inside it (issue I-5); without a query vector it returns keyword results only (FR-S-02). As sequence (i) |

## 3. Student 2 packages (drawn for Areeba)

| Package | Classes | Design reasoning |
|---|---|---|
| assurance (Module 5) | As iteration 1, with BetaPosteriorEstimator per role and metric and a pair-repeat discount, ManipulationDetector with all five signals, DecisionPolicy with R4 before R3 (ADR-0010, proposed); new signal classes RatingVelocity, NewAccountActivity, InvitationLinkage realise the one `SignalCheck` | Roles and metrics are never mixed (overview §5.2); a missing signal returns None and the weights are renormalised |
| assurance.reviews and lender evidence (Module 5) | RoleMetric, PopulationBaseline, LenderEvidence, ReviewService, Review | LenderEvidence gives search the lender factors without ever showing one number (FR-S-04) |
| search.ranking (Module 4, S2) | EmbeddingProvider, EmbeddingJob, HybridRanker, RankingWeights, RankedResult | `EmbeddingProvider` is a port, so the model chosen in ADR-0016 can change without touching the ranker |
| notifications (Module 7) | INotify, NotificationService, Notification | One `notify(user, type, payload, dedupe_key)` for every module (ADR-0013) |

## 4. Student 3 packages

Minahil's class diagram v2.0 is Student 3's section, unchanged in content: `moderation` (Module 9), `uploads` (ADR-0014), `search logging` (Module 4), `evaluation` (Module 10). Its iteration 2 members are drawn in the shared green instead of the `{v2}` marker. The boundary copies of other students' classes are gone because the real classes are on the same diagram; the three interfaces Module 9 calls that no other section draws as boxes (`ILifecycleCommands`, `IEventQuery`, `IOutcomeFlags`) stay in a small package beside it.

## 5. Domain model (iteration 2)

The domain model (`domain_model.drawio`) is a separate diagram on purpose: it is the conceptual model of design step A2 (no operations, no implementation types), not a second class diagram. No class is removed. Five conceptual classes are new: MembershipDecision, Notification, SearchQuery, SearchImpression and Attachment. New attributes: Community `joinPolicy`, Item `description, condition, usageTerms, searchTerms, expiresAt`, EscalationCase `infoDeadline`, ModeratorDecision `possession` and `reverses`.

## 6. Names used across the design set

| Name | Was also called | Where fixed |
|---|---|---|
| NotificationService (M7, Student 2) | Notifier, Notifier «stub» | sequences (a), (b), (g), (h) |
| JobRunner (M3, Student 1) | Scheduler (F4) | sequence (g); Student 3 section |
| AppealService, ReversalService (M9, Student 3) | CaseService for appeals and reversals | sequence (h); component diagram |
| SearchService, EmbeddingProvider, HybridRanker, LenderEvidence (M4, M5) | KeywordRetriever, SemanticRetriever, Embedder, Ranker | sequence (i); component diagram; class diagram |
