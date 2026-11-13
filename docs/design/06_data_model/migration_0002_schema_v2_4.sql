-- =============================================================================
-- Digital Mohalla: schema v2.4 = migration 0002 on top of the frozen v2.3 baseline
--                  (iteration 2, design artefacts DA-09 and DA-23, Student 1 Fatima Khursheed)
-- Target: PostgreSQL 16 with btree_gist (v2.3), vector (pgvector, ADR-0016) and pg_trgm.
--         Neon supports all three; enable them on the Neon project before migrating.
-- Applies after: ../06_data_model/schema.sql v2.3 (Alembic revision 0001). Never edit v2.3:
--                every change below is additive or a new trigger, so revision 0001 stays byte-for-byte the same.
-- Status: DRAFT for the 10 November design gate. The three new event types extend the frozen event list and
--         need sign-off by all three students (FR-B-09). Generated parts are marked; edit their source instead.
-- Sources: ../07_state_machines/State_Machine_Design_v3.md (lifecycle v3), ../03_architecture/DigitalMohalla_ADRs_Ver1.md
--          (ADR-0009, 0012, 0013, 0015, 0016), ER_Schema_Design_v2_4.md (rationale, table by table).
-- GenAI:   drafted with Claude (Claude Code); reviewed by the owner. Log in docs/ai-usage-log.md and Form 13.
--
-- New design rules (continuing R1 to R5 of v2.3):
--   R6  Item possession decides how a dispute closes (ADR-0009): the decision's resolved_outcome and the
--       dispute_resolved payload carry the possession, and the trigger allows only the matching next state
--       (T25a, T25b, T25c), so an occupied item is never released.
--   R7  Search logs and notifications are personal data with no location: their JSON columns may not carry
--       coordinates or addresses (NFR-PR-01), and the query text is capped and never indexed for the public.
--   R8  Scheduled jobs are idempotent at the database: one job_run row per (job, due key) (NFR-R-05, ADR-0012).
--
-- Run: psql -v ON_ERROR_STOP=1 -f migration_0002_schema_v2_4.sql   (after schema.sql v2.3)
-- The file has two transactions: PostgreSQL cannot use a new enum value in the transaction that adds it.
-- In Alembic: part 1 inside op.get_context().autocommit_block(), part 2 as a normal migration body.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Part 1: extensions, new enum values and types (own transaction)
-- -----------------------------------------------------------------------------
BEGIN;
SET search_path = dm, public;

CREATE EXTENSION IF NOT EXISTS vector;       -- item embeddings (ADR-0016)
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- typo-tolerant title match for keyword search (ADR-0016)

-- Lifecycle v3 (ADR-0015): generated list = lifecycle_model.EVENTS with status "proposed"
ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'counter_offered';
ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'counter_accepted';
ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'counter_declined';

-- Listing condition (FR-B-01); four coarse grades a lender can choose without photos
CREATE TYPE item_condition   AS ENUM ('NEW', 'GOOD', 'FAIR', 'WORN');
-- Community joining rule (UC-A3 ext 4a, issue I-10): open-join still records a locality outcome
CREATE TYPE join_policy      AS ENUM ('MODERATED', 'OPEN');
-- Membership decisions (UC-A4; FR-A-10, FR-A-11)
CREATE TYPE membership_decision_kind AS ENUM ('APPROVED', 'REJECTED', 'INFO_REQUESTED', 'REVERSED');
-- Scheduler (ADR-0012)
CREATE TYPE job_status       AS ENUM ('RUNNING', 'SUCCEEDED', 'FAILED');
-- Search mode actually served (FR-S-02: keyword fallback when the model or index is down)
CREATE TYPE search_mode      AS ENUM ('HYBRID', 'KEYWORD_ONLY');
COMMIT;

-- -----------------------------------------------------------------------------
-- Part 2: tables, columns, triggers and reference data
-- -----------------------------------------------------------------------------
BEGIN;
SET search_path = dm, public;

-- Helper: JSON that must never carry location (R7, NFR-PR-01)
CREATE FUNCTION has_location_keys(j jsonb) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT j IS NOT NULL AND jsonb_typeof(j) = 'object'
       AND j ?| ARRAY['lat', 'lng', 'lon', 'latitude', 'longitude', 'coordinates', 'address', 'location', 'accuracy']
$$;

-- =============================================================================
-- 3'. Module 1: registration, joining, membership decisions (Fatima: F2, F7)
-- =============================================================================
ALTER TABLE app_user  ADD COLUMN terms_accepted_at timestamptz;                       -- FR-A-01: terms and privacy notice
ALTER TABLE app_user  ADD CONSTRAINT app_user_terms_ck
    CHECK (status = 'PENDING_VERIFICATION' OR is_synthetic OR terms_accepted_at IS NOT NULL) NOT VALID;
ALTER TABLE community ADD COLUMN join_policy join_policy NOT NULL DEFAULT 'MODERATED';   -- UC-A3 4a

-- One row per moderator decision on a membership request; append-only, so a reversal keeps both (FR-A-11).
CREATE TABLE membership_decision (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    membership_id        uuid NOT NULL REFERENCES membership (id),
    decided_by           uuid NOT NULL REFERENCES app_user (id),
    kind                 membership_decision_kind NOT NULL,
    reason               text NOT NULL CHECK (length(btrim(reason)) > 0),             -- FR-A-10: mandatory reason
    reverses_decision_id uuid REFERENCES membership_decision (id),
    decided_at           timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT membership_decision_reversal_ck CHECK ((kind = 'REVERSED') = (reverses_decision_id IS NOT NULL))
);
CREATE INDEX membership_decision_ix ON membership_decision (membership_id, decided_at);

-- Who may decide: a moderator of that community or an admin, never the applicant (FR-A-10, NFR-S-03)
CREATE FUNCTION membership_decision_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE m membership%ROWTYPE;
BEGIN
    SELECT * INTO m FROM membership WHERE id = NEW.membership_id;
    IF NEW.decided_by = m.user_id THEN
        RAISE EXCEPTION 'an applicant cannot decide their own membership' USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM membership mm WHERE mm.user_id = NEW.decided_by AND mm.community_id = m.community_id
                      AND mm.role = 'MODERATOR' AND mm.status = 'APPROVED')
       AND NOT EXISTS (SELECT 1 FROM app_user a WHERE a.id = NEW.decided_by AND a.platform_role = 'ADMIN'
                          AND a.status = 'ACTIVE') THEN
        RAISE EXCEPTION 'only a moderator of this community or an admin decides memberships (UC-A4 4b)'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF NEW.kind <> 'REVERSED' AND m.status NOT IN ('PENDING', 'AWAITING_INFORMATION') THEN
        RAISE EXCEPTION 'membership is already %; show the current state and apply nothing (UC-A4 4a)', m.status
            USING ERRCODE = 'serialization_failure';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER membership_decision_guard BEFORE INSERT ON membership_decision
    FOR EACH ROW EXECUTE FUNCTION membership_decision_guard();
CREATE TRIGGER membership_decision_append_only BEFORE UPDATE OR DELETE ON membership_decision
    FOR EACH ROW EXECUTE FUNCTION forbid_change();

-- =============================================================================
-- 4'. Module 3 listings (FR-B-01, DA-23; Fatima F9) and Module 4 keyword search (FR-S-02, S-03; Fatima F10)
-- =============================================================================
ALTER TABLE item
    ADD COLUMN condition       item_condition,
    ADD COLUMN usage_terms     text CHECK (usage_terms IS NULL OR length(usage_terms) <= 2000),
    ADD COLUMN handover_method text CHECK (handover_method IS NULL OR length(handover_method) <= 200),
    ADD COLUMN search_terms    text CHECK (search_terms IS NULL OR length(search_terms) <= 300),  -- other names, e.g. Roman Urdu
    ADD COLUMN expires_at      timestamptz,
    ADD COLUMN updated_at      timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN search_tsv      tsvector GENERATED ALWAYS AS (
        to_tsvector('simple'::regconfig,
                    coalesce(title, '') || ' ' || coalesce(description, '') || ' ' || coalesce(search_terms, ''))) STORED;
-- 'simple' rather than 'english': no stemming, so Roman Urdu words are matched as typed (NFR-U-05 decision).
-- New published listings need a description and a condition; iteration 1 seed rows are left as they are (NOT VALID).
ALTER TABLE item ADD CONSTRAINT item_published_complete_ck
    CHECK (status <> 'PUBLISHED' OR (description IS NOT NULL AND length(btrim(description)) > 0 AND condition IS NOT NULL))
    NOT VALID;
ALTER TABLE item ADD CONSTRAINT item_expiry_ck CHECK (expires_at IS NULL OR expires_at > created_at);
CREATE INDEX item_search_tsv_ix  ON item USING gin (search_tsv);
CREATE INDEX item_title_trgm_ix  ON item USING gin (title gin_trgm_ops);
CREATE INDEX item_expiry_ix      ON item (expires_at) WHERE status = 'PUBLISHED' AND expires_at IS NOT NULL;   -- listing-expiry job

-- Listing photos reuse attachment (ADR-0014): an attachment belongs to exactly one item or one transaction.
ALTER TABLE attachment ALTER COLUMN transaction_id DROP NOT NULL;
ALTER TABLE attachment ADD COLUMN item_id uuid REFERENCES item (id);
ALTER TABLE attachment ADD CONSTRAINT attachment_target_ck CHECK (num_nonnulls(transaction_id, item_id) = 1);
ALTER TABLE attachment ADD CONSTRAINT attachment_item_only_ck
    CHECK (item_id IS NULL OR (condition_report_id IS NULL AND case_statement_id IS NULL));

-- =============================================================================
-- 4''. Module 4: meaning-based search and search logs (FR-S-01, S-05; Areeba A9, Minahil M9)
-- =============================================================================
-- One embedding per item and model. Exact search over a few hundred rows needs no ANN index (ADR-0016),
-- so eligibility filters run in the same query (issue I-5). Dimension 384 is provisional: it is the size of
-- the small sentence-embedding models ADR-0016 compares, and is fixed when the model is chosen.
CREATE TABLE item_embedding (
    item_id        uuid NOT NULL REFERENCES item (id),
    model          text NOT NULL CHECK (length(model) BETWEEN 1 AND 120),     -- model name and version
    content_sha256 bytea NOT NULL CHECK (octet_length(content_sha256) = 32), -- hash of the embedded text: stale when it differs
    embedding      vector(384) NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (item_id, model)
);

CREATE TABLE search_query (                              -- FR-S-05; Module 10 evaluation input
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        uuid NOT NULL REFERENCES app_user (id),
    community_id   uuid REFERENCES community (id),
    query_text     text NOT NULL CHECK (length(btrim(query_text)) BETWEEN 1 AND 200),
    filters        jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(filters) = 'object' AND NOT has_location_keys(filters)),
    mode           search_mode NOT NULL,
    config_version text NOT NULL,                         -- ranking weights used (NFR-D-01)
    result_count   integer NOT NULL CHECK (result_count >= 0),
    latency_ms     integer CHECK (latency_ms >= 0),       -- NFR-P-01, P-02 measurements
    created_at     timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX search_query_user_ix ON search_query (user_id, created_at DESC);

CREATE TABLE search_impression (                         -- one row per result shown, in rank order
    query_id    uuid NOT NULL REFERENCES search_query (id),
    rank        smallint NOT NULL CHECK (rank >= 1),
    item_id     uuid NOT NULL REFERENCES item (id),
    score_parts jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(score_parts) = 'object'),  -- feature values, for the reason line
    PRIMARY KEY (query_id, rank),
    CONSTRAINT search_impression_item_uq UNIQUE (query_id, item_id)
);

CREATE TABLE search_click (                              -- a shown result opened; "ignored" = impression with no click
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id               uuid NOT NULL,
    item_id                uuid NOT NULL,
    clicked_at             timestamptz NOT NULL DEFAULT clock_timestamp(),
    request_transaction_id uuid REFERENCES borrowing_transaction (id),   -- set when the click led to a request
    CONSTRAINT search_click_shown_fk FOREIGN KEY (query_id, item_id) REFERENCES search_impression (query_id, item_id)
);
-- Logs are evidence for evaluation: no edits, no deletes (a retention job may archive later, NFR-PR-02 open)
CREATE TRIGGER search_query_append_only      BEFORE UPDATE OR DELETE ON search_query      FOR EACH ROW EXECUTE FUNCTION forbid_change();
CREATE TRIGGER search_impression_append_only BEFORE UPDATE OR DELETE ON search_impression FOR EACH ROW EXECUTE FUNCTION forbid_change();

-- =============================================================================
-- 7'. Module 7: in-app notifications (FR-C-02 in-app channel; ADR-0013; Areeba A2)
-- =============================================================================
CREATE TABLE notification (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid NOT NULL REFERENCES app_user (id),
    type       text NOT NULL CHECK (type ~ '^[a-z][a-z0-9_]*$'),
    payload    jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(payload) = 'object' AND NOT has_location_keys(payload)),
    dedupe_key text NOT NULL CHECK (length(dedupe_key) BETWEEN 1 AND 200),   -- e.g. "<transaction>:handover_reminder:1"
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    read_at    timestamptz,
    CONSTRAINT notification_once_uq UNIQUE (user_id, dedupe_key),          -- duplicate suppression (FR-B-18, FR-C-02)
    CONSTRAINT notification_read_ck CHECK (read_at IS NULL OR read_at >= created_at)
);
CREATE INDEX notification_inbox_ix ON notification (user_id, created_at DESC) WHERE read_at IS NULL;

-- =============================================================================
-- 3''. Scheduler (FR-B-18; ADR-0012; Fatima F4)
-- =============================================================================
CREATE TABLE job_run (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_name    text NOT NULL CHECK (job_name ~ '^[a-z][a-z0-9_]*$'),
    due_key     text NOT NULL CHECK (length(due_key) BETWEEN 1 AND 200),  -- what the run is for, e.g. "<transaction>:no_show"
    started_at  timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    status      job_status NOT NULL DEFAULT 'RUNNING',
    attempts    smallint NOT NULL DEFAULT 1 CHECK (attempts BETWEEN 1 AND 10),
    error       text,
    CONSTRAINT job_run_once_uq UNIQUE (job_name, due_key),                  -- R8: a rerun finds the row and does nothing
    CONSTRAINT job_run_finished_ck CHECK ((status = 'RUNNING') = (finished_at IS NULL)),
    CONSTRAINT job_run_error_ck CHECK (status <> 'FAILED' OR error IS NOT NULL)
);

-- =============================================================================
-- 7''. Module 9: dispute decision records item possession (ADR-0009, review DM14)
-- =============================================================================
-- No new column: the possession is a key of resolved_outcome (jsonb, v2.3), as ADR-0009 records.
-- Every new dispute decision names one of the four values; iteration 1 decisions predate the rule (NOT VALID keeps them).
ALTER TABLE moderator_decision ADD CONSTRAINT decision_possession_ck
    CHECK (kind <> 'DISPUTE_RESOLVED'
           OR coalesce(resolved_outcome ->> 'possession', '') IN ('NOT_HANDED_OVER', 'WITH_BORROWER', 'RETURNED', 'LOST')) NOT VALID;

-- =============================================================================
-- 8'. Lifecycle v3 guards and effects (ADR-0009, ADR-0015). New triggers, so event_validate and event_apply
--     of v2.3 stay unchanged. BEFORE triggers fire in name order: lifecycle_event_validate runs first and
--     computes the hash; lifecycle_event_validate_v3 only checks and never changes NEW.
-- =============================================================================
-- The open counter-offer of a request, if any (ADR-0015): the latest counter event is a counter_offered
CREATE FUNCTION open_counter_offer(p_txn uuid) RETURNS lifecycle_event LANGUAGE sql STABLE AS $$
    SELECT e.* FROM lifecycle_event e
     WHERE e.stream_id = p_txn AND e.event_type IN ('counter_offered', 'counter_accepted', 'counter_declined')
       AND e.event_type = 'counter_offered'
       AND NOT EXISTS (SELECT 1 FROM lifecycle_event later WHERE later.stream_id = p_txn AND later.stream_seq > e.stream_seq
                          AND later.event_type IN ('counter_accepted', 'counter_declined'))
     ORDER BY e.stream_seq DESC LIMIT 1
$$;

CREATE FUNCTION event_validate_v3() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = dm, pg_temp AS $$
DECLARE
    t        borrowing_transaction%ROWTYPE;
    d        moderator_decision%ROWTYPE;
    oc       lifecycle_event%ROWTYPE;
    restore  lifecycle_state;
    expect   lifecycle_state;
    poss     text;
    proposed tstzrange;
BEGIN
    SELECT * INTO t FROM borrowing_transaction WHERE id = NEW.stream_id;

    CASE NEW.event_type
    WHEN 'dispute_resolved' THEN                                                     -- T25a, T25b, T25c (ADR-0009)
        SELECT * INTO d FROM moderator_decision WHERE id::text = NEW.evidence_refs ->> 'decision_id';
        poss := d.resolved_outcome ->> 'possession';
        IF poss IS NULL THEN
            RAISE EXCEPTION 'a dispute decision must record where the item is (resolved_outcome.possession, ADR-0009)'
                USING ERRCODE = 'check_violation';
        END IF;
        SELECT e.previous_state INTO restore FROM lifecycle_event e
         WHERE e.stream_id = t.id AND e.event_type = 'dispute_opened' ORDER BY e.stream_seq DESC LIMIT 1;
        IF poss = 'NOT_HANDED_OVER' AND restore <> 'ACCEPTED' THEN
            RAISE EXCEPTION 'possession % fits only a dispute raised before handover (raised from %)', poss, restore
                USING ERRCODE = 'check_violation';
        END IF;
        IF poss IN ('WITH_BORROWER', 'RETURNED', 'LOST') AND restore NOT IN ('ACTIVE', 'RETURN_INITIATED') THEN
            RAISE EXCEPTION 'possession % fits only a dispute raised after handover (raised from %)', poss, restore
                USING ERRCODE = 'check_violation';
        END IF;
        expect := CASE poss WHEN 'NOT_HANDED_OVER' THEN 'NO_SHOW'                       -- T25a
                            WHEN 'WITH_BORROWER' THEN 'ACTIVE'                          -- T25b: due date unchanged
                            ELSE 'COMPLETED' END;                                       -- T25c: RETURNED, LOST
        IF NEW.new_state IS DISTINCT FROM expect THEN
            RAISE EXCEPTION 'possession % requires next state %, not %', poss, expect, NEW.new_state
                USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.payload ->> 'possession' IS DISTINCT FROM poss THEN
            RAISE EXCEPTION 'dispute_resolved payload.possession must copy the decision (replay needs it, FR-B-09)'
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'counter_offered' THEN                                                      -- I07
        BEGIN
            proposed := (NEW.payload ->> 'proposed_period')::tstzrange;
        EXCEPTION WHEN others THEN
            RAISE EXCEPTION 'counter_offered needs payload.proposed_period as a range' USING ERRCODE = 'check_violation';
        END;
        IF proposed IS NULL OR NOT is_bounded_range(proposed) OR lower(proposed) < now() OR proposed = t.requested_period THEN
            RAISE EXCEPTION 'a counter-offer proposes other, future, bounded dates (UC-B6 3b)' USING ERRCODE = 'check_violation';
        END IF;
        IF (open_counter_offer(t.id)).event_id IS NOT NULL THEN
            RAISE EXCEPTION 'a counter-offer is already open on this request (ADR-0015)' USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'counter_declined' THEN                                                     -- I08
        IF (open_counter_offer(t.id)).event_id IS NULL THEN
            RAISE EXCEPTION 'no open counter-offer to decline' USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'counter_accepted' THEN                                                     -- T29
        oc := open_counter_offer(t.id);
        IF oc.event_id IS NULL THEN
            RAISE EXCEPTION 'no open counter-offer to accept' USING ERRCODE = 'check_violation';
        END IF;
        proposed := (oc.payload ->> 'proposed_period')::tstzrange;
        IF (NEW.payload ->> 'requested_period')::tstzrange IS DISTINCT FROM proposed THEN
            RAISE EXCEPTION 'counter_accepted payload.requested_period must equal the offered dates' USING ERRCODE = 'check_violation';
        END IF;
        IF lower(proposed) < now() THEN
            RAISE EXCEPTION 'the offered dates have started; ask for a new offer' USING ERRCODE = 'check_violation';
        END IF;
        IF EXISTS (SELECT 1 FROM booking k WHERE k.item_id = t.item_id AND k.status = 'HELD' AND k.period && proposed) THEN
            RAISE EXCEPTION 'the offered dates are now taken (ADR-0002)' USING ERRCODE = 'exclusion_violation';
        END IF;
    ELSE
        NULL;
    END CASE;
    RETURN NEW;
END $$;
CREATE TRIGGER lifecycle_event_validate_v3 BEFORE INSERT ON lifecycle_event
    FOR EACH ROW EXECUTE FUNCTION event_validate_v3();

-- Effects after v2.3's event_apply (AFTER triggers also fire in name order)
CREATE FUNCTION event_apply_v3() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = dm, pg_temp AS $$
BEGIN
    IF NEW.event_type = 'counter_accepted' THEN                                      -- T29: the request now has the new dates
        UPDATE borrowing_transaction SET requested_period = (NEW.payload ->> 'requested_period')::tstzrange
         WHERE id = NEW.stream_id;
    ELSIF NEW.event_type = 'dispute_resolved' AND NEW.payload ->> 'possession' = 'LOST' THEN
        UPDATE item SET status = 'PAUSED', updated_at = now()                        -- not lendable until the lender acts
         WHERE id = (SELECT item_id FROM borrowing_transaction WHERE id = NEW.stream_id);
    END IF;
    -- NO_SHOW and COMPLETED already release the booking in v2.3's event_apply (T25a, T25c); T25b returns the
    -- loan to ACTIVE and leaves the booking HELD, which is the whole point of ADR-0009.
    RETURN NULL;
END $$;
CREATE TRIGGER lifecycle_event_apply_v3 AFTER INSERT ON lifecycle_event FOR EACH ROW EXECUTE FUNCTION event_apply_v3();

-- =============================================================================
-- 10'. Reference data: lifecycle v3 rows added to allowed_transition
--      GENERATED from ../_tools/lifecycle_model_v3.py (rows not in v2.3); checked by ../14_testing/verify_iteration2.py
-- =============================================================================
INSERT INTO allowed_transition (from_state, event_type, to_state, allowed_roles, ref, iteration)
SELECT f::lifecycle_state, ev::event_type, t::lifecycle_state, r::actor_role[], ref, it
FROM (VALUES
    ('ASSESSED'          , 'counter_accepted'     , 'LOCALITY_CHECKED' , '{BORROWER}', 'T29', 2),
    ('ASSESSED'          , 'counter_declined'     , 'ASSESSED'         , '{BORROWER}', 'I08', 2),
    ('ASSESSED'          , 'counter_offered'      , 'ASSESSED'         , '{LENDER}', 'I07', 2),
    ('DISPUTED'          , 'dispute_resolved'     , 'ACTIVE'           , '{MODERATOR,ADMIN}', 'T25b', 2),
    ('DISPUTED'          , 'dispute_resolved'     , 'NO_SHOW'          , '{MODERATOR,ADMIN}', 'T25a', 2)
) AS v (f, ev, t, r, ref, it);
-- v2.3's T25 row (DISPUTED, dispute_resolved, COMPLETED) is lifecycle v3's T25c: same row, narrower guard (the
-- trigger above). allowed_transition is append-only (v2.3 R2), so that row keeps ref 'T25'.

-- =============================================================================
-- 11'. Privileges for the new tables (same rule as v2.3: the app role cannot rewrite history)
-- =============================================================================
GRANT SELECT ON membership_decision, item_embedding, search_query, search_impression, search_click, notification, job_run TO dm_app;
GRANT INSERT ON membership_decision, item_embedding, search_query, search_impression, search_click, notification, job_run TO dm_app;
GRANT UPDATE (embedding, content_sha256, created_at) ON item_embedding TO dm_app;         -- re-embedding when text changes
GRANT UPDATE (read_at) ON notification TO dm_app;
GRANT UPDATE (finished_at, status, attempts, error) ON job_run TO dm_app;
-- item, community, app_user and membership keep v2.3's INSERT, UPDATE grant, which covers the new columns
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dm TO dm_app;
COMMIT;
