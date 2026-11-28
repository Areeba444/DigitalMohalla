# Prototype ↔ backend API map

Checked against `iteration2/slice3` (commit de20418), which has 55 endpoints. Every endpoint below has a screen. The mock data in `js/data.js` uses the field names and enum values of the response models in `backend/app/api/schemas.py`. Open **Screens** in the app to jump to any route listed here.

## Accounts and communities (Module 1)

| Endpoint | Screen | Route | Notes |
| --- | --- | --- | --- |
| `POST /auth/register` | Register (W8) | `#/register` | Answers `202` with one generic message, whether or not the e-mail is already registered |
| `POST /auth/login` | Log in | `#/login` | Interim sign-in. E-mail/phone OTP is iteration 3 |
| `GET /communities` | Find your mohalla (W9) | `#/join` | Shows `member_count`, `join_code`, `methods`, `has_boundary` and your membership status (`APPROVED`, `PENDING`, `REJECTED`) |
| `POST /communities/{id}/join` | Location + invitation (W10) | `#/join/c1/verify` | Sends a one-time `fix` or `permission_refused`, plus an optional `invitation_code` |
| ↳ `JoinOut.locality` | Results | `#/join/c1/result/{VERIFIED,INCONCLUSIVE,CONFLICTING}` | Uses the backend's own `LOCALITY_WORDS` sentences. `VERIFIED` = inside the boundary + a valid invitation |
| `POST /communities/{id}/invitations` | Invite a neighbour | `#/invite` | The code is shown once. It lasts 7 days, and a member can hold at most 3 open codes |
| `GET /moderation/memberships` | Join requests (W11) | `#/mod/members` | Shows only the coarse `locality_outcome`, `boundary_signal`, `invitation_used`, `permission_refused`, `mock_provider_detected`, `duplicate_suspected` |
| `POST /moderation/memberships/{id}/decision` | Join request detail | `#/mod/members/M-87`, `#/mod/members/M-86` | Decisions: `APPROVED` / `REJECTED` / `INFO_REQUESTED` / `REVERSED`, each with a reason |

## Listings and search (Modules 3, 4)

| Endpoint | Screen | Route | Notes |
| --- | --- | --- | --- |
| `GET /categories` | Listing wizard, admin categories | `#/lend`, `#/admin/communities` | `is_restricted` categories need a community-verified member |
| `POST /items` | Lend an item (W22) | `#/lend` | Fields: `title`, `description`, `category_id`, `condition` (NEW/GOOD/FAIR/WORN), `value_band` (LOW/MEDIUM/HIGH), `deposit`, `usage_terms`, `handover_method`, `search_terms`. Publishing needs a description and a condition |
| `PATCH /items/{id}` | Edit listing | `#/lend/edit` | |
| `GET /me/items` | My listings | `#/listings` | Statuses: `PUBLISHED`, `DRAFT`, `PENDING_REVIEW`, `PAUSED`, `EXPIRED`, `REMOVED` |
| `POST /items/{id}/photos` | Wizard step 1 | `#/lend` | JPEG/PNG, up to 5 MB |
| `GET /items` | Home "free near you" | `#/home` | Browse list |
| `GET /items/{id}` | Item details (W24) | `#/item/makita` | Includes the lender's `LenderEvidenceOut` (factors, never a score) and booked dates |
| `GET /search` | Borrow (W23) | `#/borrow`, `#/borrow/fallback` | Filters: `category`, `community`, `from`, `to`, `max_deposit`, `condition`, `sort` (relevance / evidence / newest). Results carry a plain-words `reason` and `same_community`. Mode `KEYWORD_ONLY` gets its own banner |
| `POST /search/{query_id}/clicks` | Tapping a result | `#/borrow` | Not visible; it is logged for search evaluation |

## Requests and the loan lifecycle (Module 3)

| Endpoint | Screen | Route | Notes |
| --- | --- | --- | --- |
| `POST /requests` | Request to borrow | `#/request/deg` | `end_date` is exclusive ("back by"). The message is up to 500 characters |
| ↳ `CommandOut` | Request sent / held | `#/request/deg/sent` | `ASSESSED`, or `HELD_FOR_REVIEW` with any of the 5 hold reasons |
| `GET /requests`, `GET /lender/requests` | Activity board | `#/activity` | Grouped by `your_role` and what needs doing |
| `GET /requests/{id}` | Lender decides (W1) | `#/requests/r1`, `r2`, `r3` | `AssessmentOut`: state, policy, rule fired, 90% interval, effective evidence, community paths, manipulation level, safeguards, engine explanation |
| `POST /requests/{id}/accept` | Accept dialog | `#/requests/r2` | Includes the `409` "dates already taken" race |
| `POST /requests/{id}/decline` | Decline dialog | `#/requests/r1` | Optional reason, up to 200 characters |
| `POST /requests/{id}/cancel` | Cancel (borrower) | `#/counter/b9`, `#/loan/b14` | |
| `POST /requests/{id}/counter-offer` | Suggest other dates | `#/requests/r1` | Other dates plus a message (≤500 characters) |
| `POST .../counter-offer/accept` | Take the new dates (W14) | `#/counter/b9` | The new dates are checked and assessed again |
| `POST .../counter-offer/decline` | Keep my dates | `#/counter/b9` | The original dates stand |
| `POST /transactions/{id}/handover/checklist` | Lender checklist (W3a, W17) | `#/handover/b6/lender` | Sends `checklist`, `deposit_received`, `notes`. Photos come after the checklist; with no photos the handover is marked "reduced evidence" |
| `POST /transactions/{id}/handover/confirm` | Borrower confirms (W3b) | `#/handover/b1/borrower` | `condition_agreed: false` records a disagreement and the loan stays `ACCEPTED` |
| `POST /transactions/{id}/photos` | Handover and return photos | `#/handover/b6/lender`, `#/return/b2` | |
| `GET /transactions/{id}/events` | Loan timeline | `#/loan/b2`, `#/loan/b7`, `#/loan/b12`, `#/loan/b14` | Shows real event names (`request_created`, `assessment_generated`, `handover_confirmed`, `no_show`, …) |
| `POST /transactions/{id}/extension` | Ask for more days (W13) | `#/extend/b2` | `new_due_date` (exclusive) and an optional reason. One pending request at a time |
| `POST .../extension/approve`, `.../decline` | Respond to an extension | `#/extend-respond/b10` | |
| `POST /transactions/{id}/return` | Borrower starts the return | `#/return/b2` | |
| `POST /transactions/{id}/return/confirm` (lender) | Return checklist (W4) | `#/inspect/b3` | The lender's condition report |
| `POST /transactions/{id}/return/confirm` (borrower) | Confirm the return | `#/return-confirm/b13` | Confirming closes the loan as `COMPLETED`, and the outcome becomes evidence |
| `POST /transactions/{id}/review` | Review (W15) | `#/review/b4` | 1–5 for each of the other role's 4 dimensions, plus a comment (≤1000 characters). The window is 14 days and edits are allowed for 24 h |

## Disputes and moderation (Modules 5, 9)

| Endpoint | Screen | Route | Notes |
| --- | --- | --- | --- |
| `POST /transactions/{id}/dispute` | Report a problem (W5) | `#/report/b3` | Reasons: `DAMAGE`, `NON_RETURN`, `CONDITION_MISMATCH`, `NO_SHOW`, `OTHER`. Description up to 1000 characters, within 7 days |
| `POST /transactions/{id}/dispute/withdraw` | Withdraw report | `#/case/b3` | Only the person who raised it can withdraw |
| `GET /transactions/{id}/dispute` | Case progress | `#/case/b3`, `#/case/b5` | `DisputeTrailOut` |
| `POST /cases/{id}/statements` | Statement to a moderator (W18) | `#/case/b5` | Up to 2000 characters; reply within 72 h |
| `GET /moderation/cases` | Case queue (W6) | `#/mod` | `CaseQueueOut` carries no names: trigger, reason, status, priority 1–3 |
| `GET /moderation/cases/{id}` | Case detail | `#/mod/case/D-014` and the others | `ModeratorCaseOut` shows names |
| `POST /moderation/cases/{id}/decision` | Decision form | `#/mod/case/*` | Disputes: `DISPUTE_RESOLVED` + `at_fault` + `possession`, limited to what fits the stage. Holds: `CLEARED`, `SAFEGUARDS_IMPOSED` (needs safeguards; not allowed after `engine_failure`) or `RESTRICTED` |
| `POST /moderation/cases/{id}/information-requests` | "Ask for information" | `#/mod/case/D-014` | `to`: BORROWER / LENDER / BOTH, plus the question. 72 h deadline |
| `POST /cases/{id}/appeal` | Appeal (W20) | `#/decision/b11` | Reason only (≤1000 characters). One per case, within 7 days |
| `POST /moderation/cases/{id}/appeal-decision` | Appeal, second moderator | `#/mod/case/A-003` | `UPHELD` / `OVERTURNED` plus a reason |
| `POST /moderation/decisions/{id}/reversal` | Reverse a decision | `#/mod/case/A-003`, `#/mod/members/M-86` | Moderator of the community or an admin |

## Evidence, notifications, admin

| Endpoint | Screen | Route | Notes |
| --- | --- | --- | --- |
| `GET /me/evidence` | My evidence (W16) | `#/evidence` | Factors per role, each with its own interval. Detail is hidden below the loan minimum |
| `GET /notifications` | Notifications (W12) | `#/notifications`, bell popover | Sentences are built from `type` + `payload` (`NOTE` map in `core.js`) |
| `POST /notifications/read` | Mark all read | `#/notifications` | |
| `GET /admin/audit` | Audit log (W21) | `#/admin/audit`, `#/mod/audit` | Filters by category and outcome; shows `hash_valid` and the concentration flag |
| `POST /admin/audit/{source}/{id}/unmask` | Unmask dialog | `#/admin/audit` | Needs a purpose of at least 10 characters, and is itself logged |
| `POST /internal/jobs/run` | Scheduled jobs | `#/admin/jobs` | `JobReportOut`: ran / skipped / failed for each job, run under a lock and idempotent |
| `GET /attachments/{id}`, `GET /files/{key}` | Photos shown in loans and cases | (everywhere photos appear) | Served by the API in the real app; Unsplash stand-ins in the prototype |

## Shown in the prototype, but without an endpoint yet (marked "Soon")

These are iteration 3 or later. The screens are designs to agree on, not wired flows:

- Ask the mohalla, fair matching and saved searches (B9–B11)
- Setting availability on a listing (blocking your own dates)
- Platform analytics (J1) and personal impact (J2)
- Forum, assistant, events, vendors, kameti, insights
- Reports and automatic flags (I3, I5), event approvals (C2)
- User, community and vendor management (I1, I2, H5)
- Role applications (A8)
- E-mail/phone OTP and push notifications
- Chat (the inbox is a design; there are no message endpoints yet)
