# Class Diagrams, Iteration 2 (DA-11)

| Field | Value |
|---|---|
| Owner | Fatima Khursheed draws S1 and S2 (S2 for Areeba's review and sign-off); Minahil Kashif draws S3 |
| Version | 2.0 draft, 3 November 2026 |
| Status | Draft for the 10 November design gate |
| Files | `class_diagram_s1_iteration2.drawio`, `class_diagram_s2_iteration2.drawio`, `generate_class_diagrams_iteration2.py` |
| Builds on | `../05_class_model/` (domain model, class diagrams S1 to S3, unchanged) |
| GenAI | Drafted with Claude (Claude Code); reviewed by the owner. Log in `docs/ai-usage-log.md` and on Form 13 |

## 1. How to read them

Each diagram shows only what iteration 2 adds or changes. A class marked «changed» already exists in iteration 1 and lists only its additions, so the iteration 1 diagram plus this one gives the whole package. Each class names the FRs it realises, as plan step A7 required. Classes of other students appear only as boundary interfaces in their owner's colour.

## 2. Student 1 packages

| Package | Classes | Design reasoning |
|---|---|---|
| accounts (Module 1) | RegistrationService, User «changed», MembershipService, GeofenceInvitationVerifier, InvitationService, MembershipDecision, MembershipDecisionKind | The verifier was designed in A11 and is now built. It takes the device fix as a parameter and returns a `LocalityResult` with no coordinates, so a coordinate cannot reach storage through the class's own interface (NFR-PR-01). Decisions are separate append-only objects, so a reversal is a new object that points at the old one (FR-A-11) |
| lifecycle and listings (Module 3) | BorrowingService «changed», CounterOffer, TransitionTable «changed», Possession, ListingService, Item «changed», JobRunner, Job, NoShowJob, OverdueJob, ExpiryJob, JobRunStore | CounterOffer is a value rebuilt from the event stream, not a table, because the events already carry it (ADR-0015). Each scheduled job implements one `Job` interface and appends events through `BorrowingService`, never directly, so jobs get the same validation, audit and notifications as users. `JobRunStore` is the port to `job_run` that makes reruns harmless |
| search (Module 4, Student 1 part) | IRetriever, KeywordRetriever, SearchFilters, Candidate | Both retrievers implement one `IRetriever`, so the search service can switch to keywords when the model is down (FR-S-02) without knowing which one answered. `SearchFilters` has no radius, because there are no coordinates; the eligibility filters are applied inside the query (I-5) |

## 3. Student 2 packages (drawn for Areeba)

| Package | Classes | Design reasoning |
|---|---|---|
| assurance (Module 5) | BetaPosteriorEstimator «changed», RoleMetric, PopulationBaseline, LenderEvidence, ReviewService, Review «changed», ManipulationDetector «changed», Signal, RatingVelocity, NewAccountActivity, InvitationLinkage, DecisionPolicy «changed» | Every signal implements `Signal`, so S2, S3 and S5 plug into the iteration 1 combination rule without changing it. `LenderEvidence` is the only way Module 4 sees trust: it returns factors for the item page and a ranking value that never leaves the server (FR-S-04, NFR-U-01) |
| search (Module 4, Student 2 part) | SearchService, SemanticRetriever, EmbeddingProvider, EmbeddingJob, HybridRanker, RankingWeights, RankedResult | `EmbeddingProvider` is a port, so the model chosen in ADR-0016 can be swapped without touching the ranker. A provider failure raises `ModelUnavailable`, which the search service turns into keyword-only mode |
| notifications (Module 7) | NotificationService, Notification | One `notify()` for every module, with the dedupe key as the guard against duplicates (ADR-0013) |

## 4. Changes to the iteration 1 domain model

No class is removed. Two concepts are new: MembershipDecision, the record of a moderator's decision on a join request, and SearchQuery with its impressions, the evidence for search evaluation. Possession is a new attribute of ModeratorDecision. The domain model drawing is updated at the gate, after Minahil's S3 diagram fixes the shape of appeals.
