# Digital Mohalla: Architecture, Iteration 2 (DA-10)

| Field | Value |
|---|---|
| Owner | Fatima Khursheed (Student 1) |
| Version | 2.0 draft, 3 November 2026 |
| Status | Draft for the 10 November design gate. Section 4 is the **API contract** that Areeba's screen shells are built against; changes after the gate go through Fatima |
| Builds on | `../03_architecture/Architecture_Design.md` v1.2 (iteration 1 endpoints unchanged) |
| Files | `component_diagram_v2.drawio`, `layer_diagram_v2.drawio`, `generate_architecture_v2.py`, `DigitalMohalla_ADRs_Ver1.md` |
| GenAI | Drafted with Claude (Claude Code); reviewed by the owner. Log in `docs/ai-usage-log.md` and on Form 13 |

## 1. Design reasoning

The architecture stays a modular monolith: one FastAPI service, one PostgreSQL database, and modules that talk through narrow interfaces. Iteration 2 adds three kinds of work, and each keeps that shape.

- **New user-facing features** (joining, listings, search, reviews, notifications, appeals) are new application services behind the same REST API. They use the existing ports pattern, so the domain logic stays free of I/O and unit-testable.
- **Time-based behaviour** (expiry, no-show, reminders, overdue escalation) has no user to trigger it. It runs in a JobRunner that an external schedule calls, because the free hosting tier sleeps (ADR-0011, ADR-0012). The jobs append ordinary lifecycle events through the same validator, so the database rules apply to them as to any user.
- **Search ranking needs trust evidence** but must not compute or display a trust score itself. Module 4 asks Module 5 through `ILenderEvidence`, which returns factors with confidence, exactly as the lender's request screen does (FR-S-04, NFR-U-01).

Splitting into separate services was rejected again for the same reason as in iteration 1. One team of three, one database with rules enforced in triggers, and a free-tier host make one deployable unit the simpler and safer choice.

## 2. Components and owners

| Module | Component | Responsibility | Owner | New in it. 2 |
|---|---|---|---|---|
| 1 | AuthService | Login, roles, registration with terms (A1) | Fatima | Registration |
| 1 | MembershipService | Join request, moderator queue, decisions, reversal (A3, A4) | Fatima | Yes |
| 1 | LocalityVerifier | Geofence plus invitation decision table (A11); the fix is used in memory only | Fatima | Built (was a stub) |
| 1 | InvitationService | Single-use codes, only the hash stored | Fatima | Yes |
| 3 | BorrowingService | B5 to B8, B12; counter-offer, extension | Fatima | Extended |
| 3 | ListingService | Create, edit, draft, publish, expiry (B1) | Fatima | Yes |
| 3 | JobRunner | `run_due_jobs(now)` for expiry, no-show, reminders, overdue, listing expiry, embedding backfill, population baseline | Fatima | Yes |
| 3 | TransitionValidator, EventStore, BookingGuard, OutcomePublisher | As iteration 1, on lifecycle v3 | Fatima | Updated |
| 4 | KeywordRetriever | Full-text and trigram retrieval with eligibility filters in the query | Fatima | Yes |
| 4 | SemanticRetriever, EmbeddingJob | Item embeddings, pgvector exact search, keyword fallback | Areeba | Yes |
| 4 | HybridRanker | Algorithm 5 and the reason line per result | Areeba | Yes |
| 4 | SearchLogger | Queries, impressions, clicks, with no location | Minahil | Yes |
| 5 | AssuranceFacade, BetaPosteriorEstimator, ManipulationDetector, DecisionPolicy, ConfigLoader | As iteration 1, plus roles and metrics, S2, S3, S5, R4 before R3 | Areeba | Extended |
| 5 | ReviewService | D1 reviews from parties, once each, flags | Areeba | Yes |
| 5 | LenderEvidence, PopulationBaseline | Lender factors for search and item details; baselines per role and metric | Areeba | Yes |
| 5 | IndirectTrust | Bounded k-hop | Fatima | Unchanged |
| 7 | NotificationService | `notify()`, in-app table, polling (ADR-0013) | Areeba | Yes |
| 9 | CaseService, DecisionService | Information requests, deadlines, admin routing, possession (ADR-0009) | Minahil | Extended |
| 9 | AppealService, AuditLogService, AttachmentService | Appeal and reversal; audit API and screen; photos (ADR-0014) | Minahil | Yes |
| 10 | ScenarioSuite, EvaluationHarness, SearchEvaluation | 13 scenarios; baselines and holdout; precision@k | Minahil | Extended |

## 3. Interfaces

Iteration 1 interfaces keep their operations. New or changed ones:

| Interface | Provider → consumers | Operations | FRs |
|---|---|---|---|
| IAuth | M1 → API | `register(email, password, display_name, terms_accepted) → Account` (new), `login`, `current_actor` | FR-A-01, FR-A-04 |
| IMembership | M1 → M3, API | `communities(query) → list`, `request_join(user, community, locality_input, invitation_code) → Membership`, `queue(moderator) → list`, `decide(moderator, membership, kind, reason)`, `is_member`, `is_moderator_of` | FR-A-06, A-09 to A-11 |
| ILocality | M1 → M3 | `verify(membership, fix, accuracy, mock_flag, permission_refused, invitation) → LocalityResult` (new); `outcome_for(user, community)` unchanged | FR-A-07, A-08, FR-B-07 |
| IBorrowingCommands | M3 → API | iteration 1 commands plus `counter_offer`, `respond_counter`, `request_extension`, `respond_extension` | FR-B-10, FR-B-14 |
| IListings | M3 → API, M4 | `create`, `update`, `publish`, `pause`, `get(item)`; publishes `listing_changed` for re-embedding | FR-B-01 |
| IJobTrigger | M3 (JobRunner) → API | `run_due_jobs(now, as_of?) → JobReport` | FR-B-18, NFR-R-05 |
| ISearch | M4 → API | `search(actor, query, filters, sort, page) → Results`, `record_click(query_id, item_id)` | FR-S-01 to S-05 |
| ILenderEvidence | M5 → M4 | `lender_factors(lender, profile) → Factors` (never one number), `ranking_value(lender) → float` (internal, never returned to clients) | FR-S-01, FR-S-04 |
| IReviews | M5 → API | `submit(actor, transaction, ratings, comment)`, `edit(...)` inside the window | FR-T-09 |
| INotify | M7 → M3, M9, M1 | `notify(user, type, payload, dedupe_key)`; `inbox(user, unread)`; `mark_read(ids)` | FR-C-02 |
| IModeration | M9 → API | iteration 1 plus `request_information`, `respond(case, party, statement, attachments)`, `appeal`, `reverse` | FR-B-17, FR-T-11 |
| IAudit | M9 → API | `search(filters, page)`; the view itself is logged | FR-M-05 |

## 4. REST endpoints, iteration 2

All under `/api/v1`, JSON over HTTPS, the same error codes as iteration 1 (401, 403, 404, 409, 422). Every state-changing call is one command and one database transaction. Owners build their own endpoints; Areeba's screens use the typed client generated from the OpenAPI export.

| Method and path | Actor | Use-case step | Effect | FRs | Builder |
|---|---|---|---|---|---|
| `POST /auth/register` | Guest | A1 steps 1–3 | Account PENDING_VERIFICATION with `terms_accepted_at`; generic error if the e-mail exists | FR-A-01 | Fatima |
| `GET /communities?query=` | Member | A3 steps 1–2 | Communities by name or code, with rules and methods | FR-A-06 | Fatima |
| `POST /communities/{id}/join` | Member | A3 steps 3–4 | Body: one-time fix (lat, lng, accuracy, mock flag) or `permission_refused`, plus invitation code. The fix is evaluated in memory and dropped; returns the membership with VERIFIED, INCONCLUSIVE or CONFLICTING | FR-A-07 to A-09, NFR-PR-01 | Fatima |
| `POST /communities/{id}/invitations` | Approved member | A3 (A11) | Returns a single-use code once; only its hash is stored | FR-A-07 | Fatima |
| `GET /moderation/memberships` | Moderator | A4 step 1 | Pending requests of the moderator's communities with locality evidence and flags | FR-A-10 | Fatima |
| `POST /moderation/memberships/{id}/decision` | Moderator | A4 steps 3–4 | `{kind, reason}`; 409 if already decided (A4 4a) | FR-A-10, A-11 | Fatima |
| `POST /items`, `PATCH /items/{id}` | Lender | B1 | Draft or publish a listing; publishing needs a description and condition; queues embedding | FR-B-01 | Fatima |
| `POST /items/{id}/photos` | Lender | B1 | Multipart upload; EXIF stripped; type and size checked | FR-B-01, NFR-S-06 | Minahil |
| `GET /search?q=&category=&community=&from=&to=&max_deposit=&condition=&sort=` | Member | B3 | Ranked results, each with a reason line and a `mode` (HYBRID or KEYWORD_ONLY); logs query and impressions | FR-S-01 to S-03, S-05 | Fatima (keyword), Areeba (ranking) |
| `POST /search/{query_id}/click` | Member | B3 | Records the click for evaluation | FR-S-05 | Minahil |
| `GET /items/{id}` (extended) | Borrower | B4, B5 step 1 | Adds condition, terms and the lender's evidence factors with confidence; "not enough history" for new lenders | FR-S-04 | Areeba |
| `POST /requests/{id}/counter-offer` | Lender | B6 ext 3b | `counter_offered` (I07) | FR-B-10 | Fatima |
| `POST /requests/{id}/counter-offer/accept`, `/decline` | Borrower | B6 ext 3b | `counter_accepted` then reassessment (T29), or `counter_declined` (I08) | FR-B-10 | Fatima |
| `POST /transactions/{id}/extension`, `/extension/approve`, `/extension/decline` | Borrower, Lender | B8 ext 1a | I03 to I05; approval moves the due date and the booking | FR-B-14 | Fatima |
| `POST /transactions/{id}/review` | Party | D1 | Once per party after COMPLETED; flags set by ReviewService | FR-T-09, B-15 | Areeba |
| `GET /me/evidence` | Member | D2 | Own factors per role and metric, suppressed when too few | FR-T-08 | Areeba |
| `GET /notifications?unread=`, `POST /notifications/read` | Member | G3 | Inbox and read marks | FR-C-02 | Areeba |
| `POST /moderation/cases/{id}/information-request` | Moderator | I4 step 2 | Case AWAITING_INFORMATION with a deadline; parties notified | FR-B-17, FR-T-11 | Minahil |
| `POST /cases/{id}/statements` | Party | I4 step 2, B12 | A response with optional attachments before the deadline | FR-B-17 | Minahil |
| `POST /moderation/cases/{id}/decision` (extended) | Moderator | I4 steps 3–4 | Dispute decisions now carry `resolved_outcome.possession`: NOT_HANDED_OVER, WITH_BORROWER, RETURNED or LOST (ADR-0009) | FR-T-11 | Minahil |
| `POST /cases/{id}/appeal`, `POST /moderation/decisions/{id}/reversal` | Party; Moderator | I4 ext 4b, 4c | Second moderator; reversal flags outcomes (ES-11) | FR-T-11 | Minahil |
| `GET /admin/audit?actor=&target=&from=&to=&action=` | Admin | I6 | Filtered, masked entries with tamper warnings; the view is logged | FR-M-05 | Minahil |
| `POST /internal/jobs/run` | GitHub Actions (token) | B13 | Runs due jobs; returns a report of what ran and what was skipped | FR-B-18 | Fatima |

Request logging must never record the body of `POST /communities/{id}/join`, because it carries the fix (privacy suite 14).

## 5. Layer rules

Unchanged from iteration 1, with two additions:

- Module 4 reads Module 5 only through `ILenderEvidence`; it never reads the `assessment` table or computes a posterior.
- The JobRunner is an application service. It appends events through `BorrowingService`, never by writing SQL into `lifecycle_event` directly, so the pre-checks, audit and notifications are the same as for a user's command.

## 6. Open points

| Point | Owner | By |
|---|---|---|
| Embedding model and its memory use on Render's free tier (ADR-0016) | Fatima, Areeba | Design gate |
| Polling interval for notifications if Neon or Render limits bite | Areeba | Slice 1 |
| Whether `GET /search` needs paging beyond 20 results at pilot size | Fatima | Slice 2 |
