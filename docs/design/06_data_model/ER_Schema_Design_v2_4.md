# Schema v2.4: Design and Rationale (iteration 2, DA-09 and DA-23)

| Field | Value |
|---|---|
| Owner | Fatima Khursheed (Student 1) |
| Version | 2.4 draft, 3 November 2026 |
| Status | Draft for the 10 November design gate. Needs all three signatures (frozen event schema, FR-B-09), then tag `schema-v2` |
| Builds on | `../06_data_model/schema.sql` v2.3, which stays frozen as Alembic revision 0001 |
| Files | `migration_0002_schema_v2_4.sql` (the change), `er_diagram.drawio` and `generate_erd_v2_4.py`, `Data_Dictionary_v2_4.md` and `generate_data_dictionary_v2_4.py` |
| GenAI | Drafted with Claude (Claude Code); decisions and review by the owner. Log in `docs/ai-usage-log.md` and on Form 13 |

## 1. Summary

Migration 0002 adds what iteration 2 needs and changes nothing that already exists. It adds 7 tables, 10 columns on existing tables, 5 enum types, 3 event-type values, 2 transition rows, one check on `moderator_decision.resolved_outcome` and 6 triggers. Every v2.3 trigger, constraint and row stays as it is, so revision 0001 is never edited (README rule).

| Area | Addition | Requirements | Built by |
|---|---|---|---|
| Lifecycle v3 | Event types `counter_offered`, `counter_accepted`, `counter_declined`; 2 `allowed_transition` rows (T25a, T25b); T29, I07, I08 rows; triggers `event_validate_v3` and `event_apply_v3` | FR-B-08, FR-B-10, FR-T-11, review DM14 | Fatima (F1, F6), Minahil (M1) |
| Disputes by possession | `possession` key of `moderator_decision.resolved_outcome` (check `decision_possession_ck`) | ADR-0009, DM14 | Minahil (M1) |
| Registration and joining | `app_user.terms_accepted_at`, `community.join_policy`, table `membership_decision` | FR-A-01, FR-A-09 to A-11 | Fatima (F2, F7) |
| Listings | `item.condition`, `usage_terms`, `handover_method`, `search_terms`, `expires_at`, `updated_at`; `attachment.item_id` | FR-B-01, FR-B-18 | Fatima (F9), Minahil (M4) |
| Keyword search | Generated column `item.search_tsv` with a GIN index; trigram index on `item.title` | FR-S-02, FR-S-03 | Fatima (F10) |
| Meaning-based search | Table `item_embedding` (pgvector) | FR-S-01 | Areeba (A9) |
| Search logs | Tables `search_query`, `search_impression`, `search_click` | FR-S-05, NFR-Q-05 | Minahil (M9) |
| Notifications | Table `notification` | FR-C-02 (in-app), FR-B-06, FR-B-17 | Areeba (A2) |
| Scheduler | Table `job_run` | FR-B-18, NFR-R-05 | Fatima (F4) |

## 2. Decisions table by table

**Lifecycle v3 as separate triggers.** The new guards live in `event_validate_v3`, a second BEFORE trigger that PostgreSQL fires after v2.3's `event_validate` because trigger names fire in alphabetical order. It only checks and never changes the row, so the hash v2.3 computes stays correct. The alternative, `CREATE OR REPLACE` on v2.3's 220-line function, would put two versions of the core guard in two migrations and make review harder.

**Possession on the decision, copied into the event.** `moderator_decision.resolved_outcome.possession` is what the moderator records, one of `NOT_HANDED_OVER`, `WITH_BORROWER`, `RETURNED` or `LOST` (ADR-0009). It is a key of the existing `resolved_outcome` column rather than a new column, as the ADR records. `dispute_resolved.payload.possession` must equal it, so replay can rebuild the outcome from the event log alone (FR-B-09). The trigger allows exactly one next state per possession value (table in `../07_state_machines/State_Machine_Design_v3.md` §2). The constraint is `NOT VALID`, so iteration 1 decisions without possession remain readable; every new decision needs it.

**Counter-offer data in the payload.** `counter_offered.payload.proposed_period` holds the offer and `counter_accepted.payload.requested_period` repeats it. `event_apply_v3` then copies it into `borrowing_transaction.requested_period`. Replay must therefore take the period from the latest `counter_accepted`, falling back to `request_created`. The backend aggregate changes accordingly (F6).

**`membership_decision` instead of more audit rows.** FR-A-11 asks that a reversal keeps both decisions, and UC-A4 asks for a reason shown to the applicant. That is data the application reads, not only an audit trail, so it gets a table. Its guard refuses the applicant deciding their own request, a moderator from another community, and a second decision after the request is settled (UC-A4 4a).

**Listing columns with `NOT VALID` completeness.** A published listing needs a description and a condition. Search cannot rank an item with no text, and the overview's search design assumes titles and descriptions. The seeded iteration 1 items have neither, so the check applies only to rows written after the migration.

**Full-text configuration `simple`.** English stemming would turn Roman Urdu words into wrong stems. `simple` matches words as typed, and `search_terms` lets a lender add the names neighbours actually use. The trigram index catches typing mistakes in titles. The choice is recorded in ADR-0016.

**Embeddings without an ANN index.** At a few hundred items per community, an exact cosine scan over `item_embedding` is fast. It also lets the community, status and block filters sit in the same query, which closes issue I-5 (filters applied after the top 100). An HNSW index can be added later without a schema change. The dimension 384 is provisional until ADR-0016 picks the model.

**Search logs append-only and location-free.** The logs are the evaluation data for precision@k and later learning-to-rank (Overview §4 Tier 3), so they cannot be edited. `has_location_keys()` refuses coordinates or addresses in `filters`, and the same rule covers `notification.payload` (R7, NFR-PR-01). A click must point at a result that was actually shown, so "ignored" is computable as an impression with no click.

**`job_run` makes reruns harmless.** Each job writes one row per due item, keyed by `(job_name, due_key)`. A second run of the same job finds the row and does nothing, which is NFR-R-05 at the database level. The lifecycle triggers also refuse a second `no_show` or `request_expired`, because the state has already moved. `notification_once_uq` stops a duplicate reminder.

## 3. Compatibility and order of work

- **Migration 0002 and M1 must merge together.** After the migration, the iteration 1 `decide()` path fails, because a `DISPUTE_RESOLVED` decision now needs `resolved_outcome.possession`. That is the DM14 fix taking effect, so the two land in one release.
- **The backend transition table must be regenerated** from `lifecycle_model_v3.py` in the same change (F1), or the Python pre-check would reject the new transitions before the database sees them.
- **Neon:** enable `vector` and `pg_trgm` before running the migration. `btree_gist` is already enabled.
- **Alembic:** part 1 runs in an autocommit block, because a new enum value cannot be used in the transaction that adds it.

## 4. How this was checked (3 November, repeated 12 November after the ADR-0009 alignment)

The schema was loaded into an embedded PostgreSQL 16.2 with pgvector, from `pgserver`, because Docker was not running on the laptop. That build has no `btree_gist` or `pg_trgm`. The test copy therefore replaced only the v2.3 booking `EXCLUDE` constraint and skipped the trigram index; every other statement ran as written.

| Check | Result |
|---|---|
| v2.3 then migration 0002 load without error | Pass |
| `allowed_transition` has the 39 rows of lifecycle v3 | Pass |
| Dispute from ACCEPTED, `NOT_HANDED_OVER`: NO_SHOW, booking released (T25a) | Pass |
| Dispute from ACTIVE, `WITH_BORROWER`: ACTIVE, booking held (T25b) | Pass |
| Dispute from RETURN_INITIATED, `WITH_BORROWER`: ACTIVE, booking held (T25b) | Pass |
| Dispute from ACTIVE, `LOST`: COMPLETED, booking released, item PAUSED (T25c) | Pass |
| A dispute decision without a possession is refused | Pass |
| `RETURNED` or `WITH_BORROWER` on a dispute raised from ACCEPTED is refused | Pass |
| `WITH_BORROWER` with next state COMPLETED is refused | Pass |
| Counter-offer: offer, second offer refused, accept moves to LOCALITY_CHECKED with the new dates | Pass |
| Declining with no open offer is refused; the lender cannot accept their own offer | Pass |
| Full-text search finds an item by a name held only in `search_terms` | Pass |
| A notification with a latitude is refused | Pass |
| Notification and job-run duplicates are suppressed | Pass |
| An applicant cannot decide their own membership | Pass |
| A 384-dimension vector is stored and found by cosine distance | Pass |

**Not checked yet:** the 44 iteration 1 schema tests (`../06_data_model/test_schema.py`) on v2.4, the booking exclusion constraint together with the new triggers, and the trigram index. All three need PostgreSQL with `btree_gist` and `pg_trgm`: the project's Docker database, CI, or Neon. Run them before the design gate.

## 5. Open items

| Item | Owner | By |
|---|---|---|
| Embedding model and its dimension (ADR-0016 memory test) | Fatima, Areeba | Design gate |
| Review edit window (FR-T-09): a column or a guard on `review` | Areeba | Slice 2 |
| Retention period for search logs and coarse locality results (NFR-PR-02) | All three, supervisor | FR/NFR v1.4 |
| Signatures of all three on the event-type additions | All three | Design gate |
