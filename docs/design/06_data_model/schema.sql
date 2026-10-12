-- =============================================================================
-- Digital Mohalla: iteration-1 core database schema, v2.3 (design step A6, Student 1)
-- Target: PostgreSQL 14 or later WITH the contrib extension btree_gist
--         (present in the official postgres Docker image and EDB installers).
--         Tested on PostgreSQL 16.6.
--
-- Baseline: 01_requirements/DigitalMohalla_Use_Cases_Ver1.md v1.3 section 2, 01_requirements/DigitalMohalla_FR_NFR_Ver1.md v1.3,
--           ADR-0001..ADR-0005, ADR-0007, ADR-0008, 07_state_machines/State_Machine_Design.md v2.2.
-- v2.3 (integration, 2026-10-11): assessment.manipulation_level, manipulation_corroborated and
--           rule_fired with the A5 decision-table check (ADR-0007, ADR-0008, decision D12);
--           value_band reduced to Student 2's three bands (decision D14).
-- Replaces v1.0 (archive_v1/), whose state and event vocabulary predates the agreed
-- single state list.
--
-- Design rules implemented here (rationale in ER_Schema_Design.md):
--   R1  Event sourcing: lifecycle_event is the source of truth. borrowing_transaction
--       is a projection that only the event trigger updates (FR-B-09).
--   R2  The lifecycle (14 states, transition table T01-T26) is enforced in the database:
--       allowed_transition + authorisation + guard checks (FR-B-08, NFR-R-02, NFR-S-02).
--   R3  Append-only, hash-chained history: events and the audit log cannot be updated
--       or deleted; an edit made with triggers disabled is still detected (FR-M-05, NFR-S-05).
--   R4  No double booking: exclusion constraint on held bookings, written in the same
--       DB transaction as request_accepted; held from acceptance until COMPLETED or NO_SHOW
--       (ADR-0002 as amended 2026-10-11; FR-B-05, NFR-R-01).
--       Pending requests block nothing (soft hold, ADR-0001).
--   R5  Location privacy: no coordinates or addresses anywhere; only the coarse locality
--       outcome is stored; photos must have metadata stripped (NFR-PR-01, NFR-PR-02).
-- Run:  psql -v ON_ERROR_STOP=1 -f schema.sql
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS btree_gist;     -- needed for (item_id WITH =) in the exclusion constraint
CREATE SCHEMA dm;
SET search_path = dm, public;

-- -----------------------------------------------------------------------------
-- 1. Enumerated types
-- -----------------------------------------------------------------------------
CREATE TYPE account_status      AS ENUM ('PENDING_VERIFICATION', 'ACTIVE', 'SUSPENDED', 'BANNED');
CREATE TYPE verification_level  AS ENUM ('UNVERIFIED', 'CONTACT_VERIFIED', 'COMMUNITY_VERIFIED');   -- ordered
CREATE TYPE platform_role       AS ENUM ('MEMBER', 'ADMIN');
CREATE TYPE membership_role     AS ENUM ('MEMBER', 'MODERATOR');
CREATE TYPE membership_status   AS ENUM ('PENDING', 'AWAITING_INFORMATION', 'APPROVED', 'REJECTED', 'WITHDRAWN', 'REVOKED');
-- Locality method chosen in design step A11 (12_locality/Locality_Design_A11.md): a one-time coarse geofence
-- check plus an invitation from a verified member; a moderator decides anything inconclusive or conflicting.
CREATE TYPE verification_method AS ENUM ('GEOFENCE_INVITATION', 'MODERATOR_APPROVAL');
-- Coarse result of the one-time GPS check. Coordinates are evaluated in memory and never stored (NFR-PR-02).
CREATE TYPE geofence_signal     AS ENUM ('INSIDE', 'NEAR_BOUNDARY', 'OUTSIDE', 'UNAVAILABLE');
-- Three-valued, never negative (FR-A-08): permission refusal and boundary cases are INCONCLUSIVE.
CREATE TYPE locality_outcome    AS ENUM ('VERIFIED', 'INCONCLUSIVE', 'CONFLICTING');
CREATE TYPE item_status         AS ENUM ('DRAFT', 'PENDING_REVIEW', 'PUBLISHED', 'PAUSED', 'EXPIRED', 'REMOVED');
CREATE TYPE value_band          AS ENUM ('LOW', 'MEDIUM', 'HIGH');   -- thresholds: Student 2 config (decision D14)

-- Use Cases v1.2 section 2 / FR-B-08: the single borrowing state list (14 states).
CREATE TYPE lifecycle_state AS ENUM (
    'REQUEST_CREATED', 'LOCALITY_CHECKED', 'HELD_FOR_REVIEW', 'ASSESSED',
    'ACCEPTED', 'ACTIVE', 'RETURN_INITIATED', 'RETURNED',
    'COMPLETED', 'DECLINED', 'CANCELLED', 'EXPIRED', 'NO_SHOW', 'DISPUTED');

-- 17 event types of Use Cases section 2 (ADR-0003, ADR-0004 accepted 2026-10-11) + 4 internal event
-- types agreed on 2026-10-11 (team decision D2; built in iteration 2).
CREATE TYPE event_type AS ENUM (
    'request_created', 'locality_checked', 'held_for_review', 'assessment_generated', 'hold_cleared',
    'request_accepted', 'request_declined', 'request_cancelled', 'request_expired',
    'handover_confirmed', 'no_show', 'return_initiated', 'return_confirmed', 'transaction_closed',
    'dispute_opened', 'dispute_resolved', 'dispute_withdrawn',
    'reminder_sent', 'extension_requested', 'extension_approved', 'extension_declined');

CREATE TYPE hold_reason AS ENUM ('locality_inconclusive', 'locality_conflict', 'manipulation_risk',
                                 'high_value_low_confidence', 'engine_failure');          -- ADR-0003
CREATE TYPE actor_role      AS ENUM ('BORROWER', 'LENDER', 'MODERATOR', 'ADMIN', 'SYSTEM');
CREATE TYPE party_role      AS ENUM ('BORROWER', 'LENDER');
CREATE TYPE assurance_state AS ENUM ('SUFFICIENT_EVIDENCE', 'REVIEW_RECOMMENDED', 'INSUFFICIENT_EVIDENCE', 'ACTIVE_DISPUTE');
CREATE TYPE policy_decision AS ENUM ('PROCEED', 'PROCEED_WITH_SAFEGUARDS', 'REQUEST_VERIFICATION',
                                     'RESTRICT_HIGH_VALUE', 'ESCALATE');                   -- FR-T-06
CREATE TYPE booking_status  AS ENUM ('HELD', 'RELEASED');
CREATE TYPE condition_phase AS ENUM ('HANDOVER', 'RETURN');
CREATE TYPE dispute_reason  AS ENUM ('DAMAGE', 'NON_RETURN', 'CONDITION_MISMATCH', 'NO_SHOW', 'OTHER');   -- UC-B12 step 2
CREATE TYPE case_trigger    AS ENUM ('DISPUTE', 'MANIPULATION_FLAG', 'HIGH_VALUE_LOW_CONFIDENCE',
                                     'LOCALITY_HOLD', 'ENGINE_FAILURE');                    -- FR-T-10
CREATE TYPE case_status     AS ENUM ('OPEN', 'AWAITING_INFORMATION', 'DECIDED', 'APPEALED', 'REVERSED', 'WITHDRAWN');
CREATE TYPE decision_kind   AS ENUM ('CLEARED', 'SAFEGUARDS_IMPOSED', 'RESTRICTED', 'DISPUTE_RESOLVED',
                                     'APPEAL_UPHELD', 'APPEAL_OVERTURNED', 'REVERSAL');     -- UC-I4; last three it.2
-- Outcome metrics (FR-B-15: timeliness, condition agreement, dispute result). Final list: Student 2 (A4/A5).
CREATE TYPE outcome_metric  AS ENUM ('ON_TIME_RETURN', 'CONDITION_AGREED', 'DISPUTE_FREE');
CREATE TYPE outcome_status  AS ENUM ('VALID', 'FLAGGED_FOR_REEVALUATION');

-- -----------------------------------------------------------------------------
-- 2. Helper functions (IMMUTABLE: used in constraints)
-- -----------------------------------------------------------------------------
CREATE FUNCTION is_terminal(s lifecycle_state) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT s IN ('COMPLETED', 'DECLINED', 'CANCELLED', 'EXPIRED', 'NO_SHOW')
$$;
CREATE FUNCTION is_pending(s lifecycle_state) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT s IN ('REQUEST_CREATED', 'LOCALITY_CHECKED', 'HELD_FOR_REVIEW', 'ASSESSED')
$$;
-- Role encoded in the frozen `authorisation` field (party:borrower, party:lender,
-- role:moderator@<community>, role:admin, system:<component>).
CREATE FUNCTION auth_role(a text) RETURNS actor_role LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE
        WHEN a = 'party:borrower'                        THEN 'BORROWER'::actor_role
        WHEN a = 'party:lender'                          THEN 'LENDER'::actor_role
        WHEN a ~ '^role:moderator@[A-Za-z0-9-]+$'        THEN 'MODERATOR'::actor_role
        WHEN a = 'role:admin'                            THEN 'ADMIN'::actor_role
        WHEN a ~ '^system:[a-z0-9_.-]+$'                 THEN 'SYSTEM'::actor_role
    END
$$;
CREATE FUNCTION is_bounded_range(r tstzrange) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT NOT isempty(r) AND NOT lower_inf(r) AND NOT upper_inf(r) AND lower_inc(r) AND NOT upper_inc(r)
$$;

-- -----------------------------------------------------------------------------
-- 3. Module 1: users, communities, membership, coarse locality (R5)
-- -----------------------------------------------------------------------------
CREATE TABLE app_user (                                  -- User
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name       text NOT NULL CHECK (length(btrim(display_name)) BETWEEN 1 AND 80),
    email              text,
    phone              text,
    password_hash      text,                              -- salted bcrypt/argon2 hash only (NFR-S-01)
    verification_level verification_level NOT NULL DEFAULT 'UNVERIFIED',
    platform_role      platform_role      NOT NULL DEFAULT 'MEMBER',
    status             account_status     NOT NULL DEFAULT 'PENDING_VERIFICATION',
    is_synthetic       boolean            NOT NULL DEFAULT false,   -- seed data labelled synthetic (plan, evidence list)
    created_at         timestamptz        NOT NULL DEFAULT now(),
    -- R5: deliberately no address, latitude, longitude or CNIC columns (NFR-PR-01, NFR-S-07).
    CONSTRAINT app_user_contact_ck CHECK (email IS NOT NULL OR phone IS NOT NULL)
);
CREATE UNIQUE INDEX app_user_email_uq ON app_user (lower(email)) WHERE email IS NOT NULL;
CREATE UNIQUE INDEX app_user_phone_uq ON app_user (phone)        WHERE phone IS NOT NULL;

CREATE TABLE user_block (                                -- UC-B5 ext 3a guard (seeded in iteration 1)
    blocker_id uuid NOT NULL REFERENCES app_user (id),
    blocked_id uuid NOT NULL REFERENCES app_user (id),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (blocker_id, blocked_id),
    CONSTRAINT user_block_self_ck CHECK (blocker_id <> blocked_id)
);

CREATE TABLE community (                                 -- Community
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name       text NOT NULL CHECK (length(btrim(name)) > 0),
    join_code  text NOT NULL UNIQUE,
    rules      text,
    -- Coarse boundary of the housing society (A11 geofence). Community data, not personal data.
    boundary_polygon jsonb CHECK (boundary_polygon IS NULL OR jsonb_typeof(boundary_polygon) = 'object'),
    is_active  boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX community_name_uq ON community (lower(name));

CREATE TABLE membership (                                -- Membership (User M:N Community)
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES app_user (id),
    community_id uuid NOT NULL REFERENCES community (id),
    role         membership_role   NOT NULL DEFAULT 'MEMBER',
    status       membership_status NOT NULL DEFAULT 'PENDING',
    requested_at timestamptz NOT NULL DEFAULT now(),
    decided_at   timestamptz,
    CONSTRAINT membership_decided_ck CHECK ((status IN ('PENDING', 'AWAITING_INFORMATION')) = (decided_at IS NULL))
);
CREATE UNIQUE INDEX membership_one_live_uq ON membership (user_id, community_id)
    WHERE status IN ('PENDING', 'AWAITING_INFORMATION', 'APPROVED');                   -- UC-A3 4b

-- A11: single-use invitation issued by a verified member. Only a hash of the code is stored.
CREATE TABLE invitation (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id uuid NOT NULL REFERENCES community (id),
    inviter_id   uuid NOT NULL REFERENCES app_user (id),
    code_hash    bytea NOT NULL UNIQUE CHECK (octet_length(code_hash) = 32),   -- SHA-256 of the code
    created_at   timestamptz NOT NULL DEFAULT now(),
    expires_at   timestamptz NOT NULL,
    CONSTRAINT invitation_expiry_ck CHECK (expires_at > created_at)
);

-- One coarse locality result per check (R5). The raw fix is evaluated in memory and discarded.
-- The outcome must follow from its own signals (A11 decision table), so it cannot contradict its evidence.
CREATE TABLE locality_verification (
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    membership_id          uuid NOT NULL REFERENCES membership (id),
    method                 verification_method NOT NULL,
    outcome                locality_outcome    NOT NULL,
    geofence_signal        geofence_signal,                   -- NULL only for MODERATOR_APPROVAL
    invitation_id          uuid UNIQUE REFERENCES invitation (id),   -- UNIQUE: an invitation is used once
    permission_refused     boolean NOT NULL DEFAULT false,    -- ES-10 / UC-A3 3a
    mock_provider_detected boolean NOT NULL DEFAULT false,    -- spoofing signal reported by the device
    duplicate_suspected    boolean NOT NULL DEFAULT false,    -- UC-A3 4d
    approved_by            uuid REFERENCES app_user (id),     -- moderator, for MODERATOR_APPROVAL only
    checked_at             timestamptz NOT NULL DEFAULT now(),
    valid_until            timestamptz NOT NULL,              -- re-check period (config); retention open (NFR-PR-02)
    CONSTRAINT locality_validity_ck CHECK (valid_until > checked_at),
    CONSTRAINT locality_refusal_ck  CHECK (NOT permission_refused OR geofence_signal = 'UNAVAILABLE'),
    CONSTRAINT locality_method_ck   CHECK (CASE method
        WHEN 'MODERATOR_APPROVAL'  THEN approved_by IS NOT NULL AND outcome = 'VERIFIED' AND geofence_signal IS NULL
        WHEN 'GEOFENCE_INVITATION' THEN approved_by IS NULL AND geofence_signal IS NOT NULL END),
    CONSTRAINT locality_rule_ck     CHECK (method <> 'GEOFENCE_INVITATION' OR outcome = CASE
        WHEN mock_provider_detected OR duplicate_suspected OR geofence_signal = 'OUTSIDE' THEN 'CONFLICTING'
        WHEN geofence_signal = 'INSIDE' AND invitation_id IS NOT NULL                    THEN 'VERIFIED'
        ELSE 'INCONCLUSIVE' END::locality_outcome)
);
CREATE INDEX locality_membership_ix ON locality_verification (membership_id, checked_at DESC);

-- -----------------------------------------------------------------------------
-- 4. Module 3: items (seeded in iteration 1)
-- -----------------------------------------------------------------------------
CREATE TABLE category (
    id               smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name             text NOT NULL UNIQUE,
    is_restricted    boolean NOT NULL DEFAULT false,      -- FR-B-02
    min_verification verification_level NOT NULL DEFAULT 'COMMUNITY_VERIFIED'
);

CREATE TABLE item (                                      -- Item
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id              uuid NOT NULL REFERENCES app_user (id),
    community_id          uuid NOT NULL REFERENCES community (id),   -- approximate location = community
    category_id           smallint NOT NULL REFERENCES category (id),
    title                 text NOT NULL CHECK (length(btrim(title)) BETWEEN 1 AND 120),
    description           text,
    value_band            value_band NOT NULL,
    deposit_amount        numeric(12, 2) NOT NULL DEFAULT 0 CHECK (deposit_amount >= 0),  -- record-only (I-4)
    required_verification verification_level NOT NULL DEFAULT 'COMMUNITY_VERIFIED',
    status                item_status NOT NULL DEFAULT 'DRAFT',
    created_at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX item_community_status_ix ON item (community_id, status);

-- -----------------------------------------------------------------------------
-- 5. Module 3: borrowing transaction (projection), event store, bookings
-- -----------------------------------------------------------------------------
CREATE TABLE borrowing_transaction (                     -- BorrowingTransaction (aggregate; projection, R1)
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),     -- = stream_id of its events
    item_id           uuid NOT NULL REFERENCES item (id),
    borrower_id       uuid NOT NULL REFERENCES app_user (id),
    lender_id         uuid NOT NULL REFERENCES app_user (id),
    requested_period  tstzrange NOT NULL CHECK (is_bounded_range(requested_period)),
    message           text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    -- projection columns: written only by trigger event_apply
    current_state     lifecycle_state,
    stream_version    integer NOT NULL DEFAULT 0 CHECK (stream_version >= 0),   -- = last stream_seq
    hold_reason       hold_reason,                                             -- set while HELD_FOR_REVIEW
    due_at            timestamptz,                                             -- set at handover_confirmed
    last_event_at     timestamptz,
    closed_at         timestamptz,
    CONSTRAINT txn_parties_ck CHECK (borrower_id <> lender_id),
    CONSTRAINT txn_version_ck CHECK ((stream_version = 0) = (current_state IS NULL)),
    CONSTRAINT txn_hold_ck    CHECK ((current_state = 'HELD_FOR_REVIEW') = (hold_reason IS NOT NULL)),
    CONSTRAINT txn_closed_ck  CHECK ((closed_at IS NOT NULL) = (current_state IS NOT NULL AND is_terminal(current_state)))
);
CREATE INDEX txn_item_ix     ON borrowing_transaction (item_id);
CREATE INDEX txn_state_ix    ON borrowing_transaction (current_state);
CREATE INDEX txn_borrower_ix ON borrowing_transaction (borrower_id);
CREATE INDEX txn_lender_ix   ON borrowing_transaction (lender_id);

-- The transition table of design step A3 as reference data (generated from _tools/lifecycle_model.py).
CREATE TABLE allowed_transition (
    from_state    lifecycle_state NOT NULL,
    event_type    event_type      NOT NULL,
    to_state      lifecycle_state NOT NULL,
    allowed_roles actor_role[]    NOT NULL CHECK (cardinality(allowed_roles) > 0),
    ref           text            NOT NULL,              -- T01..T26 / I01..I06
    iteration     smallint        NOT NULL CHECK (iteration IN (1, 2)),
    PRIMARY KEY (from_state, event_type, to_state)
);

-- The frozen event record (Use Cases section 2, FR-B-09), including payload and the hash columns (ADR-0005).
CREATE TABLE lifecycle_event (                           -- LifecycleEvent (append-only, R3)
    event_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stream_id      uuid     NOT NULL REFERENCES borrowing_transaction (id),
    stream_seq     integer  NOT NULL CHECK (stream_seq > 0),
    event_type     event_type NOT NULL,
    schema_version smallint NOT NULL DEFAULT 1 CHECK (schema_version > 0),
    actor_id       uuid REFERENCES app_user (id),        -- NULL only for system events
    occurred_at    timestamptz NOT NULL DEFAULT clock_timestamp(),     -- set by the server
    previous_state lifecycle_state,                      -- NULL only for request_created
    new_state      lifecycle_state NOT NULL,
    evidence_refs  jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(evidence_refs) = 'object'),
    authorisation  text  NOT NULL CHECK (auth_role(authorisation) IS NOT NULL),
    config_version text,                                 -- assessment events only (NFR-D-01)
    payload        jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(payload) = 'object'),   -- ADR-0005 (N-6)
    prev_hash      bytea,                                -- storage-level tamper evidence (ADR-0005), not event content
    row_hash       bytea NOT NULL,
    CONSTRAINT event_stream_seq_uq UNIQUE (stream_id, stream_seq),
    CONSTRAINT event_actor_ck      CHECK ((auth_role(authorisation) = 'SYSTEM') = (actor_id IS NULL)),
    CONSTRAINT event_first_ck      CHECK ((stream_seq = 1) = (previous_state IS NULL)),
    CONSTRAINT event_first_type_ck CHECK (stream_seq > 1 OR (event_type = 'request_created' AND new_state = 'REQUEST_CREATED')),
    CONSTRAINT event_config_ck     CHECK (config_version IS NULL OR event_type IN ('assessment_generated', 'held_for_review')),
    CONSTRAINT event_transition_fk FOREIGN KEY (previous_state, event_type, new_state)
        REFERENCES allowed_transition (from_state, event_type, to_state)
);
CREATE INDEX event_type_ix ON lifecycle_event (stream_id, event_type);

-- ADR-0002: one row per accepted request; held dates of one item can never overlap.
CREATE TABLE booking (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id uuid NOT NULL UNIQUE REFERENCES borrowing_transaction (id),
    item_id        uuid NOT NULL REFERENCES item (id),
    period         tstzrange NOT NULL CHECK (is_bounded_range(period)),
    status         booking_status NOT NULL DEFAULT 'HELD',
    created_at     timestamptz NOT NULL DEFAULT now(),
    released_at    timestamptz,
    CONSTRAINT booking_released_ck CHECK ((status = 'RELEASED') = (released_at IS NOT NULL)),
    CONSTRAINT booking_no_overlap  EXCLUDE USING gist (item_id WITH =, period WITH &&) WHERE (status = 'HELD')
);

-- Handover and return confirmations: each party's record (UC-B7, UC-B8). Append-only.
CREATE TABLE condition_report (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id   uuid NOT NULL REFERENCES borrowing_transaction (id),
    phase            condition_phase NOT NULL,
    reporter_id      uuid NOT NULL REFERENCES app_user (id),
    reporter_role    party_role NOT NULL,
    checklist        jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(checklist) IN ('object', 'array')),
    condition_agreed boolean NOT NULL,                   -- false = disagreement (UC-B7 3a, UC-B8 3a)
    deposit_received boolean,                            -- lender at handover only; record-only (I-4)
    reduced_evidence boolean NOT NULL DEFAULT false,     -- UC-B7 2a: photos failed
    notes            text,
    created_at       timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT condition_deposit_ck CHECK (deposit_received IS NULL OR (phase = 'HANDOVER' AND reporter_role = 'LENDER'))
);
CREATE INDEX condition_report_txn_ix ON condition_report (transaction_id, phase, reporter_role, created_at DESC);

-- -----------------------------------------------------------------------------
-- 6. Module 5: assessments, outcomes, trust edges, reviews (fields: Student 2 unless noted)
-- -----------------------------------------------------------------------------
CREATE TABLE assessment (                                -- Assessment (append-only; one per engine run)
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id       uuid NOT NULL REFERENCES borrowing_transaction (id),
    generated_at         timestamptz NOT NULL DEFAULT now(),
    config_version       text NOT NULL,                  -- NFR-D-01
    assurance_state      assurance_state NOT NULL,       -- FR-T-01 (separate from lifecycle_state)
    policy_decision      policy_decision NOT NULL,       -- FR-T-06
    hold_reason          hold_reason,                    -- set when the policy holds the request
    posterior_mean       numeric(5, 4) CHECK (posterior_mean BETWEEN 0 AND 1),
    ci90_low             numeric(5, 4) CHECK (ci90_low  BETWEEN 0 AND 1),
    ci90_high            numeric(5, 4) CHECK (ci90_high BETWEEN 0 AND 1),
    effective_evidence   numeric(8, 3) CHECK (effective_evidence >= 0),
    direct_evidence      jsonb NOT NULL DEFAULT '{}',
    indirect_evidence    jsonb NOT NULL DEFAULT '{}',   -- Student 1: paths, I(u,v), rho, prior_backed
    manipulation_risk    smallint NOT NULL CHECK (manipulation_risk BETWEEN 0 AND 100),
    manipulation_level   smallint NOT NULL CHECK (manipulation_level BETWEEN 1 AND 4),   -- ADR-0007
    manipulation_corroborated boolean NOT NULL DEFAULT false,  -- >= 2 signals at or above 0.5 (ADR-0007)
    manipulation_signals jsonb NOT NULL DEFAULT '[]',
    safeguards           jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(safeguards) = 'array'),
    explanation          text NOT NULL CHECK (length(btrim(explanation)) > 0),   -- never a bare number
    rule_fired           text NOT NULL,                  -- A5 decision-table rule (Algorithm doc §6)
    CONSTRAINT assessment_hold_ck CHECK (hold_reason IS NULL OR hold_reason IN ('manipulation_risk', 'high_value_low_confidence')),
    -- ADR-0007: level from the risk bands; a score >= 60 without corroboration is capped at level 3
    CONSTRAINT assessment_level_ck CHECK (manipulation_level = CASE WHEN manipulation_risk < 20 THEN 1
                                                                   WHEN manipulation_risk < 40 THEN 2
                                                                   WHEN manipulation_risk < 60 OR NOT manipulation_corroborated THEN 3
                                                                   ELSE 4 END),
    -- FR-T-06, ADR-0007, ADR-0008, decision D12: rule -> assurance state, policy decision, hold reason, risk level
    CONSTRAINT assessment_rule_ck CHECK (CASE rule_fired
        WHEN 'R1' THEN assurance_state = 'ACTIVE_DISPUTE' AND policy_decision = 'ESCALATE' AND hold_reason IS NULL
        WHEN 'R2' THEN assurance_state = 'REVIEW_RECOMMENDED' AND policy_decision = 'ESCALATE'
                       AND hold_reason IS NOT DISTINCT FROM 'manipulation_risk' AND manipulation_level = 4
        WHEN 'R3' THEN assurance_state = 'INSUFFICIENT_EVIDENCE' AND policy_decision = 'REQUEST_VERIFICATION'
                       AND hold_reason IS NULL AND manipulation_level <= 3
        WHEN 'R4' THEN assurance_state = 'REVIEW_RECOMMENDED' AND policy_decision = 'RESTRICT_HIGH_VALUE'
                       AND hold_reason IS NOT DISTINCT FROM 'high_value_low_confidence' AND manipulation_level <= 3
        WHEN 'R5' THEN assurance_state = 'REVIEW_RECOMMENDED' AND policy_decision = 'REQUEST_VERIFICATION'
                       AND hold_reason IS NULL AND manipulation_level = 3
        WHEN 'R6_DISPUTE' THEN assurance_state = 'REVIEW_RECOMMENDED' AND policy_decision = 'PROCEED_WITH_SAFEGUARDS'
                       AND hold_reason IS NULL AND manipulation_level <= 2
        WHEN 'R6_SPARSE' THEN assurance_state = 'INSUFFICIENT_EVIDENCE' AND policy_decision = 'REQUEST_VERIFICATION'
                       AND hold_reason IS NULL AND manipulation_level <= 2
        WHEN 'R7' THEN assurance_state = 'SUFFICIENT_EVIDENCE' AND policy_decision = 'PROCEED'
                       AND hold_reason IS NULL AND manipulation_level = 1
        WHEN 'R8' THEN assurance_state = 'SUFFICIENT_EVIDENCE' AND policy_decision = 'PROCEED_WITH_SAFEGUARDS'
                       AND hold_reason IS NULL AND manipulation_level <= 2
        WHEN 'R9' THEN assurance_state = 'REVIEW_RECOMMENDED' AND policy_decision = 'PROCEED_WITH_SAFEGUARDS'
                       AND hold_reason IS NULL AND manipulation_level <= 2
        ELSE false END),
    CONSTRAINT assessment_interval_ck CHECK (ci90_low IS NULL OR ci90_high IS NULL OR posterior_mean IS NULL
                                             OR (ci90_low <= posterior_mean AND posterior_mean <= ci90_high))
);
CREATE INDEX assessment_txn_ix ON assessment (transaction_id, generated_at DESC);

CREATE TABLE outcome (                                   -- Outcome (verified evidence, Overview 5.10 OutcomeEvent)
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id         uuid NOT NULL REFERENCES borrowing_transaction (id),
    source_event_id        bigint NOT NULL REFERENCES lifecycle_event (event_id),   -- transaction_closed | dispute_resolved
    subject_id             uuid NOT NULL REFERENCES app_user (id),
    observer_id            uuid NOT NULL REFERENCES app_user (id),
    subject_role           party_role NOT NULL,
    metric                 outcome_metric NOT NULL,
    success                boolean NOT NULL,
    occurred_at            timestamptz NOT NULL,
    category_id            smallint NOT NULL REFERENCES category (id),   -- similarity snapshot (FR-T-03)
    value_band             value_band NOT NULL,
    loan_duration          interval NOT NULL,
    status                 outcome_status NOT NULL DEFAULT 'VALID',
    flagged_by_decision_id uuid,                         -- FK added below (I4 ext 4c, ES-11)
    CONSTRAINT outcome_once_uq UNIQUE (source_event_id, subject_id, metric),
    CONSTRAINT outcome_self_ck CHECK (subject_id <> observer_id)
);
CREATE INDEX outcome_subject_ix ON outcome (subject_id, subject_role, metric, occurred_at DESC);

CREATE TABLE trust_edge (                                -- TrustEdge (Student 1, indirect trust, FR-T-04)
    source_id      uuid NOT NULL REFERENCES app_user (id),
    target_id      uuid NOT NULL REFERENCES app_user (id),
    role           party_role NOT NULL,                  -- role of the target the evidence is about
    metric         outcome_metric NOT NULL,
    weight         numeric(4, 3) NOT NULL CHECK (weight > 0 AND weight <= 1),
    evidence_count integer NOT NULL CHECK (evidence_count > 0),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source_id, target_id, role, metric),
    CONSTRAINT trust_edge_self_ck CHECK (source_id <> target_id)
);
CREATE INDEX trust_edge_source_ix ON trust_edge (source_id, role, metric);

CREATE TABLE review (                                    -- Review (seeded for ES-04 / ES-05 in iteration 1)
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id   uuid NOT NULL REFERENCES borrowing_transaction (id),
    reviewer_id      uuid NOT NULL REFERENCES app_user (id),
    reviewee_id      uuid NOT NULL REFERENCES app_user (id),
    reviewee_role    party_role NOT NULL,
    ratings          jsonb NOT NULL CHECK (jsonb_typeof(ratings) = 'object'),
    comment          text,
    retaliation_flag boolean NOT NULL DEFAULT false,
    similarity_flag  boolean NOT NULL DEFAULT false,
    created_at       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT review_once_uq UNIQUE (transaction_id, reviewer_id),
    CONSTRAINT review_self_ck CHECK (reviewer_id <> reviewee_id)
);

-- -----------------------------------------------------------------------------
-- 7. Module 9: escalation cases, statements, moderator decisions, audit log
-- -----------------------------------------------------------------------------
CREATE TABLE escalation_case (                           -- EscalationCase (status is a projection, see A3)
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id  uuid NOT NULL REFERENCES borrowing_transaction (id),
    opened_event_id bigint NOT NULL UNIQUE REFERENCES lifecycle_event (event_id),
    trigger_type    case_trigger NOT NULL,
    hold_reason     hold_reason,                         -- non-dispute cases
    dispute_reason  dispute_reason,                      -- dispute cases
    raised_by       uuid REFERENCES app_user (id),       -- dispute raiser (NULL if system-opened)
    status          case_status NOT NULL DEFAULT 'OPEN',
    priority        smallint NOT NULL DEFAULT 2 CHECK (priority BETWEEN 1 AND 3),
    reason          text NOT NULL,                       -- FR-T-10: priority and reason
    assigned_to     uuid REFERENCES app_user (id),
    info_deadline   timestamptz,
    opened_at       timestamptz NOT NULL DEFAULT now(),
    closed_at       timestamptz,
    CONSTRAINT case_kind_ck CHECK ((trigger_type = 'DISPUTE') = (dispute_reason IS NOT NULL)
                                   AND (trigger_type = 'DISPUTE') = (hold_reason IS NULL)),
    CONSTRAINT case_closed_ck CHECK ((status IN ('OPEN', 'AWAITING_INFORMATION')) = (closed_at IS NULL))
);
CREATE UNIQUE INDEX case_one_live_uq ON escalation_case (transaction_id)
    WHERE status IN ('OPEN', 'AWAITING_INFORMATION');                                    -- UC-D6 1b

CREATE TABLE case_statement (                            -- claims, responses, requested information. Append-only.
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id     uuid NOT NULL REFERENCES escalation_case (id),
    author_id   uuid NOT NULL REFERENCES app_user (id),
    author_role party_role NOT NULL,
    statement   text NOT NULL CHECK (length(btrim(statement)) > 0),
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE attachment (                                -- photo / document metadata; files live outside the DB
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id      uuid NOT NULL REFERENCES borrowing_transaction (id),
    condition_report_id uuid REFERENCES condition_report (id),
    case_statement_id   uuid REFERENCES case_statement (id),
    uploaded_by         uuid NOT NULL REFERENCES app_user (id),
    storage_key         text  NOT NULL UNIQUE,
    content_sha256      bytea NOT NULL CHECK (octet_length(content_sha256) = 32),
    mime_type           text  NOT NULL CHECK (mime_type IN ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')),
    metadata_stripped   boolean NOT NULL CHECK (metadata_stripped),   -- R5: no EXIF GPS
    created_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT attachment_owner_ck CHECK (num_nonnulls(condition_report_id, case_statement_id) <= 1)
);

CREATE TABLE moderator_decision (                        -- ModeratorDecision (append-only)
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id              uuid NOT NULL REFERENCES escalation_case (id),
    decided_by           uuid NOT NULL REFERENCES app_user (id),
    decider_role         actor_role NOT NULL CHECK (decider_role IN ('MODERATOR', 'ADMIN')),
    kind                 decision_kind NOT NULL,
    reason               text NOT NULL CHECK (length(btrim(reason)) > 0),   -- mandatory reason (FR-T-11)
    safeguards           jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(safeguards) = 'array'),
    resolved_outcome     jsonb,                          -- dispute result counted as evidence (FR-B-15)
    reverses_decision_id uuid REFERENCES moderator_decision (id),          -- iteration 2
    decided_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT decision_reversal_ck CHECK ((kind IN ('REVERSAL', 'APPEAL_OVERTURNED')) = (reverses_decision_id IS NOT NULL)),
    CONSTRAINT decision_safeguards_ck CHECK (kind = 'SAFEGUARDS_IMPOSED' OR safeguards = '[]'::jsonb)
);
ALTER TABLE outcome ADD CONSTRAINT outcome_flag_fk FOREIGN KEY (flagged_by_decision_id) REFERENCES moderator_decision (id);
ALTER TABLE outcome ADD CONSTRAINT outcome_flag_ck CHECK (status <> 'FLAGGED_FOR_REEVALUATION' OR flagged_by_decision_id IS NOT NULL);

CREATE TABLE audit_log (                                 -- privileged actions, rejected commands, log views (UC-I6)
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at   timestamptz NOT NULL DEFAULT clock_timestamp(),
    actor_id      uuid REFERENCES app_user (id),
    authorisation text NOT NULL CHECK (auth_role(authorisation) IS NOT NULL OR authorisation = 'member'),
    action        text NOT NULL CHECK (action ~ '^[a-z][a-z0-9_]*$'),
    target_type   text NOT NULL,
    target_id     text NOT NULL,
    previous_value jsonb,
    new_value     jsonb,
    evidence_refs jsonb NOT NULL DEFAULT '{}',
    outcome       text NOT NULL CHECK (outcome IN ('SUCCESS', 'REJECTED')),
    reason        text,
    prev_hash     bytea,
    row_hash      bytea NOT NULL,
    CONSTRAINT audit_reason_ck CHECK (outcome = 'SUCCESS' OR reason IS NOT NULL)
);
CREATE INDEX audit_actor_ix  ON audit_log (actor_id, occurred_at);
CREATE INDEX audit_target_ix ON audit_log (target_type, target_id);

-- =============================================================================
-- 8. Triggers and functions
-- =============================================================================
-- 8.1 Append-only guard (R3)
CREATE FUNCTION forbid_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION '% is append-only: % is not allowed', TG_TABLE_NAME, TG_OP USING ERRCODE = 'insufficient_privilege';
END $$;

DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['lifecycle_event', 'audit_log', 'moderator_decision', 'assessment', 'condition_report',
                             'case_statement', 'locality_verification', 'allowed_transition']
    LOOP
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION forbid_change()',
                       t || '_append_only', t);
        EXECUTE format('CREATE TRIGGER %I BEFORE TRUNCATE ON %I FOR EACH STATEMENT EXECUTE FUNCTION forbid_change()',
                       t || '_no_truncate', t);
    END LOOP;
END $$;
CREATE TRIGGER attachment_no_update BEFORE UPDATE ON attachment FOR EACH ROW EXECUTE FUNCTION forbid_change();

-- 8.2 Hashing (per-stream chain for events, global chain for the audit log)
CREATE FUNCTION event_hash(p_prev bytea, e lifecycle_event) RETURNS bytea LANGUAGE sql STABLE AS $$
    SELECT sha256(coalesce(p_prev, '\x'::bytea) || convert_to(format('%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s',
        e.stream_id, e.stream_seq, e.event_type, e.schema_version, e.actor_id,
        to_char(e.occurred_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        e.previous_state, e.new_state, e.evidence_refs, e.authorisation, e.config_version, e.payload), 'UTF8'))
$$;
CREATE FUNCTION audit_hash(p_prev bytea, r audit_log) RETURNS bytea LANGUAGE sql STABLE AS $$
    SELECT sha256(coalesce(p_prev, '\x'::bytea) || convert_to(format('%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s',
        r.id, to_char(r.occurred_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'), r.actor_id, r.authorisation,
        r.action, r.target_type, r.target_id, r.previous_value, r.new_value, r.evidence_refs, r.outcome, r.reason), 'UTF8'))
$$;

-- 8.3 Coarse locality outcome for a request (UC-B5 step 4). Reads stored results only, never coordinates.
-- Iteration 1: this is the "stub" of plan item B5; the verification method itself is chosen in A11.
CREATE FUNCTION locality_outcome_for(p_user uuid, p_community uuid) RETURNS locality_outcome
LANGUAGE plpgsql STABLE AS $$
DECLARE v locality_verification%ROWTYPE;
BEGIN
    SELECT lv.* INTO v FROM locality_verification lv JOIN membership m ON m.id = lv.membership_id
     WHERE m.user_id = p_user AND m.community_id = p_community AND m.status = 'APPROVED'
     ORDER BY lv.checked_at DESC LIMIT 1;
    IF NOT FOUND OR v.valid_until <= now() THEN
        RETURN 'INCONCLUSIVE';                   -- missing or stale evidence is not negative (FR-A-08)
    END IF;
    RETURN v.outcome;
END $$;

-- A11 invitation rules: same community, not expired, inviter is an approved member and not the invitee.
CREATE FUNCTION locality_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    m   membership%ROWTYPE;
    inv invitation%ROWTYPE;
BEGIN
    SELECT * INTO m FROM membership WHERE id = NEW.membership_id;
    IF NEW.invitation_id IS NOT NULL THEN
        SELECT * INTO inv FROM invitation WHERE id = NEW.invitation_id;
        IF inv.community_id <> m.community_id OR inv.expires_at <= NEW.checked_at OR inv.inviter_id = m.user_id
           OR NOT EXISTS (SELECT 1 FROM membership im WHERE im.user_id = inv.inviter_id
                             AND im.community_id = inv.community_id AND im.status = 'APPROVED') THEN
            RAISE EXCEPTION 'invitation is invalid, expired or not from a member of this community (UC-A3 3d)'
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;
    IF NEW.method = 'MODERATOR_APPROVAL' AND NOT EXISTS (
           SELECT 1 FROM membership mm WHERE mm.user_id = NEW.approved_by AND mm.community_id = m.community_id
              AND mm.role = 'MODERATOR' AND mm.status = 'APPROVED')
       AND NOT EXISTS (SELECT 1 FROM app_user a WHERE a.id = NEW.approved_by AND a.platform_role = 'ADMIN') THEN
        RAISE EXCEPTION 'locality approval needs a moderator of this community or an admin' USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER locality_verification_guard BEFORE INSERT ON locality_verification
    FOR EACH ROW EXECUTE FUNCTION locality_guard();

-- 8.4 Request creation guard G1 (UC-B5 pre-conditions, ext 2a, 3a, 3b; ADR-0001)
CREATE FUNCTION txn_guard_create() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = dm, pg_temp AS $$
DECLARE
    i item%ROWTYPE;
    b app_user%ROWTYPE;
BEGIN
    IF NEW.current_state IS NOT NULL OR NEW.stream_version <> 0 OR NEW.hold_reason IS NOT NULL OR NEW.due_at IS NOT NULL THEN
        RAISE EXCEPTION 'a transaction is created empty and started by request_created' USING ERRCODE = 'check_violation';
    END IF;
    SELECT * INTO i FROM item WHERE id = NEW.item_id;
    IF i.status <> 'PUBLISHED' THEN
        RAISE EXCEPTION 'G1: listing is not published (UC-B5 1a)' USING ERRCODE = 'check_violation';
    END IF;
    IF NEW.lender_id <> i.owner_id THEN
        RAISE EXCEPTION 'G1: lender must be the listing owner' USING ERRCODE = 'check_violation';
    END IF;
    SELECT * INTO b FROM app_user WHERE id = NEW.borrower_id;
    IF b.status <> 'ACTIVE' OR b.verification_level < i.required_verification THEN
        RAISE EXCEPTION 'G1: borrower is not active or not verified to the level this item requires' USING ERRCODE = 'check_violation';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM membership m WHERE m.user_id = NEW.borrower_id AND m.community_id = i.community_id
                      AND m.status = 'APPROVED') THEN
        RAISE EXCEPTION 'G1: borrower is not a member of the listing''s community' USING ERRCODE = 'check_violation';
    END IF;
    IF EXISTS (SELECT 1 FROM user_block WHERE blocker_id = NEW.lender_id AND blocked_id = NEW.borrower_id) THEN
        -- UC-B5 3a: the application shows a neutral message that does not reveal the block.
        RAISE EXCEPTION 'G1: request not allowed' USING ERRCODE = 'check_violation';
    END IF;
    IF lower(NEW.requested_period) < now() THEN
        RAISE EXCEPTION 'G1: requested start is in the past' USING ERRCODE = 'check_violation';
    END IF;
    IF EXISTS (SELECT 1 FROM borrowing_transaction o
                WHERE o.item_id = NEW.item_id AND o.borrower_id = NEW.borrower_id
                  AND o.current_state IS NOT NULL AND is_pending(o.current_state)
                  AND o.requested_period = NEW.requested_period) THEN
        RAISE EXCEPTION 'G1: identical pending request exists (UC-B5 3b)' USING ERRCODE = 'unique_violation';
    END IF;
    IF EXISTS (SELECT 1 FROM booking k WHERE k.item_id = NEW.item_id AND k.status = 'HELD'
                  AND k.period && NEW.requested_period) THEN
        RAISE EXCEPTION 'G1: dates conflict with an accepted or active booking (UC-B5 2a)' USING ERRCODE = 'exclusion_violation';
    END IF;
    -- ADR-0001: overlapping PENDING requests are allowed; nothing is blocked here.
    RETURN NEW;
END $$;
CREATE TRIGGER borrowing_transaction_create BEFORE INSERT ON borrowing_transaction
    FOR EACH ROW EXECUTE FUNCTION txn_guard_create();

CREATE FUNCTION txn_require_start() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM lifecycle_event WHERE stream_id = NEW.id) THEN
        RAISE EXCEPTION 'transaction % committed without its request_created event', NEW.id USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER borrowing_transaction_started AFTER INSERT ON borrowing_transaction
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION txn_require_start();

-- 8.5 Event validation: concurrency, transition table, authorisation, guards, hash (R1, R2, R3)
CREATE FUNCTION latest_report(p_txn uuid, p_phase condition_phase, p_role party_role) RETURNS condition_report
LANGUAGE sql STABLE AS $$
    SELECT * FROM condition_report WHERE transaction_id = p_txn AND phase = p_phase AND reporter_role = p_role
     ORDER BY created_at DESC, id DESC LIMIT 1
$$;

CREATE FUNCTION event_validate() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = dm, pg_temp AS $$
DECLARE
    t       borrowing_transaction%ROWTYPE;
    i       item%ROWTYPE;
    rule    allowed_transition%ROWTYPE;
    a       assessment%ROWTYPE;
    c       escalation_case%ROWTYPE;
    rl      condition_report%ROWTYPE;
    rb      condition_report%ROWTYPE;
    role    actor_role := auth_role(NEW.authorisation);
    loc     locality_outcome;
    reason  hold_reason;
    prev_h  hold_reason;
    ret_at  timestamptz;
    expect  text;
    restore lifecycle_state;
BEGIN
    NEW.occurred_at := clock_timestamp();                          -- clients cannot back-date events

    SELECT * INTO t FROM borrowing_transaction WHERE id = NEW.stream_id FOR UPDATE;   -- serialise writers of one stream
    IF NOT FOUND THEN
        RAISE EXCEPTION 'stream % does not exist', NEW.stream_id USING ERRCODE = 'foreign_key_violation';
    END IF;
    SELECT * INTO i FROM item WHERE id = t.item_id;

    -- (a) Optimistic concurrency: the command must be based on the latest event.
    IF NEW.stream_seq <> t.stream_version + 1 THEN
        RAISE EXCEPTION 'stale command: expected stream_seq %, got %', t.stream_version + 1, NEW.stream_seq
            USING ERRCODE = 'serialization_failure';
    END IF;
    IF NEW.previous_state IS DISTINCT FROM t.current_state THEN
        RAISE EXCEPTION 'previous_state % does not match current state %', NEW.previous_state, t.current_state
            USING ERRCODE = 'serialization_failure';
    END IF;

    -- (b) Transition table (A3): (state, event, next state) must exist and the role must be allowed.
    IF NEW.stream_seq = 1 THEN
        IF role <> 'BORROWER' THEN
            RAISE EXCEPTION 'request_created must be issued by the borrower' USING ERRCODE = 'insufficient_privilege';
        END IF;
        -- creation data travels with the event, so the transaction can be rebuilt from the log (FR-B-09)
        IF NEW.payload ->> 'item_id' IS DISTINCT FROM t.item_id::text
           OR (NEW.payload ->> 'requested_period')::tstzrange IS DISTINCT FROM t.requested_period THEN
            RAISE EXCEPTION 'request_created payload must carry the item_id and requested_period of the transaction'
                USING ERRCODE = 'check_violation';
        END IF;
    ELSE
        SELECT * INTO rule FROM allowed_transition
         WHERE from_state = NEW.previous_state AND event_type = NEW.event_type AND to_state = NEW.new_state;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'invalid transition: % --%--> %', NEW.previous_state, NEW.event_type, NEW.new_state
                USING ERRCODE = 'check_violation';
        END IF;
        IF NOT (role = ANY (rule.allowed_roles)) THEN
            RAISE EXCEPTION 'role % may not append % in state %', role, NEW.event_type, NEW.previous_state
                USING ERRCODE = 'insufficient_privilege';
        END IF;
    END IF;

    -- (c) Authorisation: the actor really holds the claimed role (NFR-S-02, NFR-S-03).
    IF role IN ('BORROWER', 'LENDER') THEN
        IF NEW.actor_id IS DISTINCT FROM (CASE role WHEN 'BORROWER' THEN t.borrower_id ELSE t.lender_id END) THEN
            RAISE EXCEPTION 'actor is not the % of this transaction', lower(role::text) USING ERRCODE = 'insufficient_privilege';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM app_user WHERE id = NEW.actor_id AND status = 'ACTIVE') THEN
            RAISE EXCEPTION 'actor account is not active' USING ERRCODE = 'insufficient_privilege';
        END IF;
    ELSIF role IN ('MODERATOR', 'ADMIN') THEN
        IF NEW.actor_id IN (t.borrower_id, t.lender_id) THEN
            RAISE EXCEPTION 'a party cannot decide its own case' USING ERRCODE = 'insufficient_privilege';
        END IF;
        IF role = 'MODERATOR' AND (NEW.authorisation <> 'role:moderator@' || i.community_id OR NOT EXISTS (
               SELECT 1 FROM membership m JOIN app_user u ON u.id = m.user_id
                WHERE m.user_id = NEW.actor_id AND m.community_id = i.community_id AND m.role = 'MODERATOR'
                  AND m.status = 'APPROVED' AND u.status = 'ACTIVE')) THEN
            RAISE EXCEPTION 'actor is not an active moderator of this item''s community' USING ERRCODE = 'insufficient_privilege';
        END IF;
        IF role = 'ADMIN' AND NOT EXISTS (SELECT 1 FROM app_user WHERE id = NEW.actor_id AND platform_role = 'ADMIN'
                                             AND status = 'ACTIVE') THEN
            RAISE EXCEPTION 'actor is not an active admin' USING ERRCODE = 'insufficient_privilege';
        END IF;
        -- every moderator transition must reference the recorded decision of the live case (FR-T-11)
        SELECT * INTO c FROM escalation_case WHERE transaction_id = t.id AND status IN ('OPEN', 'AWAITING_INFORMATION');
        IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM moderator_decision d WHERE d.case_id = c.id
                                       AND d.id::text = NEW.evidence_refs ->> 'decision_id' AND d.decided_by = NEW.actor_id) THEN
            RAISE EXCEPTION '% needs evidence_refs.decision_id of a decision recorded by this actor on the live case',
                NEW.event_type USING ERRCODE = 'check_violation';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM moderator_decision d WHERE d.id::text = NEW.evidence_refs ->> 'decision_id'
                          AND d.kind = ANY (CASE NEW.event_type
                              WHEN 'hold_cleared'     THEN ARRAY['CLEARED', 'SAFEGUARDS_IMPOSED']::decision_kind[]
                              WHEN 'request_declined' THEN ARRAY['RESTRICTED']::decision_kind[]
                              WHEN 'dispute_resolved' THEN ARRAY['DISPUTE_RESOLVED']::decision_kind[] END)) THEN
            RAISE EXCEPTION 'the recorded decision kind does not match %', NEW.event_type USING ERRCODE = 'check_violation';
        END IF;
    END IF;

    -- (d) Event-specific guards (transition table column "guard").
    IF NEW.config_version IS NOT NULL AND NEW.event_type = 'held_for_review'
       AND NEW.payload ->> 'hold_reason' NOT IN ('manipulation_risk', 'high_value_low_confidence') THEN
        RAISE EXCEPTION 'config_version belongs only to events that carry an assessment' USING ERRCODE = 'check_violation';
    END IF;

    CASE NEW.event_type
    WHEN 'locality_checked' THEN                                                     -- T02
        loc := locality_outcome_for(t.borrower_id, i.community_id);
        IF loc <> 'VERIFIED' OR NEW.payload ->> 'locality_outcome' IS DISTINCT FROM 'VERIFIED' THEN
            RAISE EXCEPTION 'locality_checked needs a VERIFIED coarse outcome (stored outcome is %)', loc
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'held_for_review' THEN                                                      -- T03, T04, T06-T08
        reason := (NEW.payload ->> 'hold_reason')::hold_reason;
        IF reason IS NULL THEN
            RAISE EXCEPTION 'held_for_review needs payload.hold_reason (ADR-0003)' USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.previous_state = 'REQUEST_CREATED' THEN
            loc := locality_outcome_for(t.borrower_id, i.community_id);
            expect := CASE loc WHEN 'INCONCLUSIVE' THEN 'locality_inconclusive' WHEN 'CONFLICTING' THEN 'locality_conflict' END;
            IF reason::text IS DISTINCT FROM expect THEN
                RAISE EXCEPTION 'hold reason % does not match the stored locality outcome %', reason, loc
                    USING ERRCODE = 'check_violation';
            END IF;
        ELSIF reason IN ('manipulation_risk', 'high_value_low_confidence') THEN
            SELECT * INTO a FROM assessment WHERE id::text = NEW.evidence_refs ->> 'assessment_id' AND transaction_id = t.id;
            IF NOT FOUND OR a.hold_reason IS DISTINCT FROM reason OR NEW.config_version IS DISTINCT FROM a.config_version THEN
                RAISE EXCEPTION 'a % hold must reference an assessment of this request with the same hold reason and config_version',
                    reason USING ERRCODE = 'check_violation';
            END IF;
        ELSIF reason = 'engine_failure' THEN
            IF NEW.evidence_refs ? 'assessment_id' THEN
                RAISE EXCEPTION 'an engine_failure hold has no assessment (FR-T-07)' USING ERRCODE = 'check_violation';
            END IF;
        ELSE
            RAISE EXCEPTION 'hold reason % cannot follow LOCALITY_CHECKED', reason USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'assessment_generated' THEN                                                 -- T05
        SELECT * INTO a FROM assessment WHERE id::text = NEW.evidence_refs ->> 'assessment_id' AND transaction_id = t.id;
        IF NOT FOUND OR a.hold_reason IS NOT NULL OR NEW.config_version IS DISTINCT FROM a.config_version THEN
            RAISE EXCEPTION 'assessment_generated must reference a non-holding assessment of this request with the same config_version'
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'hold_cleared' THEN                                                         -- T09-T11 (ADR-0003)
        prev_h := t.hold_reason;
        IF (prev_h IN ('locality_inconclusive', 'locality_conflict', 'engine_failure')) <> (NEW.new_state = 'LOCALITY_CHECKED') THEN
            RAISE EXCEPTION 'a % hold cannot be cleared to % (ADR-0003)', prev_h, NEW.new_state USING ERRCODE = 'check_violation';
        END IF;
        IF prev_h = 'engine_failure' AND EXISTS (SELECT 1 FROM moderator_decision d
               WHERE d.id::text = NEW.evidence_refs ->> 'decision_id' AND d.kind = 'SAFEGUARDS_IMPOSED') THEN
            RAISE EXCEPTION 'safeguards cannot be imposed on an engine_failure hold: no assessment exists (UC-I4 3c)'
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'request_declined' THEN                                                     -- T12, T14, T17
        IF role = 'SYSTEM' AND (NEW.payload ->> 'reason' IS DISTINCT FROM 'dates_taken' OR NOT EXISTS (
               SELECT 1 FROM booking k WHERE k.item_id = t.item_id AND k.status = 'HELD'
                  AND k.transaction_id <> t.id AND k.period && t.requested_period)) THEN
            RAISE EXCEPTION 'the system declines only with reason dates_taken after an overlapping acceptance (ADR-0001/0002)'
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'handover_confirmed' THEN                                                   -- T18
        rl := latest_report(t.id, 'HANDOVER', 'LENDER');
        rb := latest_report(t.id, 'HANDOVER', 'BORROWER');
        IF rl.id IS NULL OR rb.id IS NULL OR NOT rb.condition_agreed THEN
            RAISE EXCEPTION 'handover needs the lender''s checklist and the borrower''s agreeing confirmation (UC-B7)'
                USING ERRCODE = 'check_violation';
        END IF;
        IF rb.created_at <= rl.created_at THEN
            RAISE EXCEPTION 'the borrower must confirm after the lender''s latest checklist (UC-B7 step 3)'
                USING ERRCODE = 'check_violation';
        END IF;
        IF i.deposit_amount > 0 AND rl.deposit_received IS NOT TRUE THEN
            RAISE EXCEPTION 'required deposit is not recorded as received (UC-B7 3b)' USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'return_confirmed' THEN                                                     -- T21
        rl := latest_report(t.id, 'RETURN', 'LENDER');
        rb := latest_report(t.id, 'RETURN', 'BORROWER');
        IF rl.id IS NULL OR rb.id IS NULL OR NOT rl.condition_agreed OR NOT rb.condition_agreed THEN
            RAISE EXCEPTION 'return needs both parties to confirm and agree on condition (UC-B8 step 3); disagreement is a dispute'
                USING ERRCODE = 'check_violation';
        END IF;
        IF rb.created_at <= rl.created_at THEN
            RAISE EXCEPTION 'the borrower must confirm after the lender''s latest return checklist (UC-B8 steps 2-3)'
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'transaction_closed' THEN                                                   -- T22
        SELECT occurred_at INTO ret_at FROM lifecycle_event WHERE stream_id = t.id AND event_type = 'return_confirmed'
         ORDER BY stream_seq DESC LIMIT 1;
        expect := CASE WHEN ret_at <= t.due_at THEN 'on_time' ELSE 'late' END;
        IF NEW.payload ->> 'outcome' IS DISTINCT FROM expect THEN
            RAISE EXCEPTION 'payload.outcome must be % (return time vs due date, UC-B8 step 4)', expect USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'dispute_opened' THEN                                                       -- T23, T24
        IF (NEW.payload ->> 'reason') IS NULL OR NOT (NEW.payload ->> 'reason') = ANY (enum_range(NULL::dispute_reason)::text[]) THEN
            RAISE EXCEPTION 'dispute_opened needs payload.reason in %', enum_range(NULL::dispute_reason) USING ERRCODE = 'check_violation';
        END IF;
        IF role = 'SYSTEM' AND NEW.payload ->> 'reason' <> 'NON_RETURN' THEN
            RAISE EXCEPTION 'the system opens disputes only for non-return (UC-B8 *a)' USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'dispute_withdrawn' THEN                                                    -- T26
        SELECT * INTO c FROM escalation_case WHERE transaction_id = t.id AND status IN ('OPEN', 'AWAITING_INFORMATION');
        IF c.raised_by IS DISTINCT FROM NEW.actor_id THEN
            RAISE EXCEPTION 'only the party who raised the dispute may withdraw it' USING ERRCODE = 'insufficient_privilege';
        END IF;
        SELECT e.previous_state INTO restore FROM lifecycle_event e WHERE e.stream_id = t.id AND e.event_type = 'dispute_opened'
         ORDER BY e.stream_seq DESC LIMIT 1;
        IF NEW.new_state IS DISTINCT FROM restore THEN
            RAISE EXCEPTION 'dispute_withdrawn must restore % (previous_state of dispute_opened, ADR-0004)', restore
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'extension_approved' THEN                                                   -- I04 (iteration 2)
        IF (NEW.payload ->> 'new_due')::timestamptz IS NULL OR (NEW.payload ->> 'new_due')::timestamptz <= greatest(now(), t.due_at) THEN
            RAISE EXCEPTION 'extension_approved needs payload.new_due later than now and the current due date' USING ERRCODE = 'check_violation';
        END IF;
    ELSE
        NULL;
    END CASE;

    -- (e) Hash chain per stream.
    SELECT e.row_hash INTO NEW.prev_hash FROM lifecycle_event e WHERE e.stream_id = t.id AND e.stream_seq = NEW.stream_seq - 1;
    NEW.row_hash := event_hash(NEW.prev_hash, NEW);
    RETURN NEW;
END $$;
CREATE TRIGGER lifecycle_event_validate BEFORE INSERT ON lifecycle_event FOR EACH ROW EXECUTE FUNCTION event_validate();

-- 8.6 Apply the event: projection, booking (ADR-0002) and case status (the only writer of these, R1)
CREATE FUNCTION event_apply() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = dm, pg_temp AS $$
DECLARE
    t borrowing_transaction%ROWTYPE;
    r hold_reason;
BEGIN
    SELECT * INTO t FROM borrowing_transaction WHERE id = NEW.stream_id;
    r := CASE WHEN NEW.new_state = 'HELD_FOR_REVIEW' THEN (NEW.payload ->> 'hold_reason')::hold_reason END;
    UPDATE borrowing_transaction
       SET current_state  = NEW.new_state,
           stream_version = NEW.stream_seq,
           hold_reason    = r,
           last_event_at  = NEW.occurred_at,
           closed_at      = CASE WHEN is_terminal(NEW.new_state) THEN NEW.occurred_at END,
           due_at         = CASE WHEN NEW.event_type = 'handover_confirmed' THEN upper(requested_period)
                                 WHEN NEW.event_type = 'extension_approved' THEN (NEW.payload ->> 'new_due')::timestamptz
                                 ELSE due_at END
     WHERE id = NEW.stream_id;

    -- Bookings: written in the same DB transaction as the event, so a refused booking refuses the event.
    IF NEW.event_type = 'request_accepted' THEN
        INSERT INTO booking (transaction_id, item_id, period) VALUES (t.id, t.item_id, t.requested_period);
    ELSIF NEW.event_type = 'extension_approved' THEN
        UPDATE booking SET period = tstzrange(lower(period), (NEW.payload ->> 'new_due')::timestamptz)
         WHERE transaction_id = t.id AND status = 'HELD';
    ELSIF NEW.new_state IN ('COMPLETED', 'NO_SHOW') THEN
        UPDATE booking SET status = 'RELEASED', released_at = NEW.occurred_at WHERE transaction_id = t.id AND status = 'HELD';
    END IF;

    -- Escalation cases (UC-D6): opened by the hold or dispute event, closed by the lifecycle.
    IF NEW.event_type = 'held_for_review' THEN
        INSERT INTO escalation_case (transaction_id, opened_event_id, trigger_type, hold_reason, priority, reason, opened_at)
        VALUES (t.id, NEW.event_id,
                CASE r WHEN 'manipulation_risk' THEN 'MANIPULATION_FLAG' WHEN 'high_value_low_confidence' THEN 'HIGH_VALUE_LOW_CONFIDENCE'
                       WHEN 'engine_failure' THEN 'ENGINE_FAILURE' ELSE 'LOCALITY_HOLD' END::case_trigger,
                r, CASE WHEN r = 'manipulation_risk' THEN 1 ELSE 2 END, 'request held: ' || r, NEW.occurred_at);
    ELSIF NEW.event_type = 'dispute_opened' THEN
        INSERT INTO escalation_case (transaction_id, opened_event_id, trigger_type, dispute_reason, raised_by, priority, reason, opened_at)
        VALUES (t.id, NEW.event_id, 'DISPUTE', (NEW.payload ->> 'reason')::dispute_reason, NEW.actor_id, 1,
                coalesce(NEW.payload ->> 'description', 'dispute: ' || (NEW.payload ->> 'reason')), NEW.occurred_at);
    ELSIF auth_role(NEW.authorisation) IN ('MODERATOR', 'ADMIN') THEN                 -- C06: decision applied
        UPDATE escalation_case SET status = 'DECIDED', closed_at = NEW.occurred_at
         WHERE transaction_id = t.id AND status IN ('OPEN', 'AWAITING_INFORMATION');
    ELSIF NEW.event_type IN ('dispute_withdrawn', 'request_cancelled', 'request_declined') THEN  -- C07
        UPDATE escalation_case SET status = 'WITHDRAWN', closed_at = NEW.occurred_at
         WHERE transaction_id = t.id AND status IN ('OPEN', 'AWAITING_INFORMATION');
    END IF;
    RETURN NULL;
END $$;
CREATE TRIGGER lifecycle_event_apply AFTER INSERT ON lifecycle_event FOR EACH ROW EXECUTE FUNCTION event_apply();

-- 8.7 Guards on evidence written by other modules
CREATE FUNCTION outcome_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    e lifecycle_event%ROWTYPE;
    t borrowing_transaction%ROWTYPE;
BEGIN
    IF TG_OP = 'UPDATE' THEN                     -- only the re-evaluation flag may change (ES-11)
        IF to_jsonb(NEW) - 'status' - 'flagged_by_decision_id' IS DISTINCT FROM to_jsonb(OLD) - 'status' - 'flagged_by_decision_id' THEN
            RAISE EXCEPTION 'outcome facts are immutable; only the re-evaluation flag may change' USING ERRCODE = 'insufficient_privilege';
        END IF;
        RETURN NEW;
    END IF;
    SELECT * INTO e FROM lifecycle_event WHERE event_id = NEW.source_event_id;
    IF e.event_type NOT IN ('transaction_closed', 'dispute_resolved') OR e.stream_id <> NEW.transaction_id THEN
        RAISE EXCEPTION 'outcomes come only from transaction_closed or dispute_resolved of the same transaction (FR-T-03)'
            USING ERRCODE = 'check_violation';
    END IF;
    SELECT * INTO t FROM borrowing_transaction WHERE id = NEW.transaction_id;
    IF (NEW.subject_id, NEW.observer_id) NOT IN ((t.borrower_id, t.lender_id), (t.lender_id, t.borrower_id))
       OR NEW.subject_id <> (CASE NEW.subject_role WHEN 'BORROWER' THEN t.borrower_id ELSE t.lender_id END) THEN
        RAISE EXCEPTION 'outcome subject and observer must be the two parties in their roles' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER outcome_guard BEFORE INSERT OR UPDATE ON outcome FOR EACH ROW EXECUTE FUNCTION outcome_guard();
CREATE TRIGGER outcome_no_delete BEFORE DELETE ON outcome FOR EACH ROW EXECUTE FUNCTION forbid_change();

CREATE FUNCTION review_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE t borrowing_transaction%ROWTYPE;
BEGIN
    SELECT * INTO t FROM borrowing_transaction WHERE id = NEW.transaction_id;
    IF t.current_state IS DISTINCT FROM 'COMPLETED' THEN
        RAISE EXCEPTION 'reviews only for COMPLETED transactions (FR-T-09)' USING ERRCODE = 'check_violation';
    END IF;
    IF NOT ((NEW.reviewer_id = t.borrower_id AND NEW.reviewee_id = t.lender_id AND NEW.reviewee_role = 'LENDER')
         OR (NEW.reviewer_id = t.lender_id AND NEW.reviewee_id = t.borrower_id AND NEW.reviewee_role = 'BORROWER')) THEN
        RAISE EXCEPTION 'reviewer and reviewee must be the two parties' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER review_guard BEFORE INSERT OR UPDATE ON review FOR EACH ROW EXECUTE FUNCTION review_guard();

CREATE FUNCTION party_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    t borrowing_transaction%ROWTYPE;
    v_user uuid;
    v_role party_role;
BEGIN
    IF TG_TABLE_NAME = 'case_statement' THEN
        SELECT bt.* INTO t FROM escalation_case ec JOIN borrowing_transaction bt ON bt.id = ec.transaction_id
         WHERE ec.id = NEW.case_id AND ec.status IN ('OPEN', 'AWAITING_INFORMATION');
        IF NOT FOUND THEN
            RAISE EXCEPTION 'statements can only be added to a live case' USING ERRCODE = 'check_violation';
        END IF;
        v_user := NEW.author_id; v_role := NEW.author_role;
    ELSE
        SELECT * INTO t FROM borrowing_transaction WHERE id = NEW.transaction_id;
        v_user := NEW.reporter_id; v_role := NEW.reporter_role;
        IF NOT ((NEW.phase = 'HANDOVER' AND t.current_state = 'ACCEPTED')
             OR (NEW.phase = 'RETURN' AND t.current_state = 'RETURN_INITIATED')) THEN
            RAISE EXCEPTION '% confirmation is not allowed in state %', NEW.phase, t.current_state USING ERRCODE = 'check_violation';
        END IF;
    END IF;
    IF v_user <> (CASE v_role WHEN 'BORROWER' THEN t.borrower_id ELSE t.lender_id END) THEN
        RAISE EXCEPTION 'author must be the % of the transaction', lower(v_role::text) USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER case_statement_party   BEFORE INSERT ON case_statement   FOR EACH ROW EXECUTE FUNCTION party_guard();
CREATE TRIGGER condition_report_party BEFORE INSERT ON condition_report FOR EACH ROW EXECUTE FUNCTION party_guard();

-- 8.8 Audit log hash chain (global order)
CREATE FUNCTION audit_chain() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = dm, pg_temp AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtext('dm.audit_log'));
    NEW.occurred_at := clock_timestamp();
    SELECT row_hash INTO NEW.prev_hash FROM audit_log ORDER BY id DESC LIMIT 1;
    NEW.row_hash := audit_hash(NEW.prev_hash, NEW);
    RETURN NEW;
END $$;
CREATE TRIGGER audit_log_chain BEFORE INSERT ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_chain();

-- 8.9 Replay (FR-B-09, NFR-R-03) and integrity check (NFR-S-05)
CREATE FUNCTION replay_state(p_stream uuid) RETURNS lifecycle_state LANGUAGE plpgsql STABLE AS $$
DECLARE
    e     lifecycle_event%ROWTYPE;
    state lifecycle_state := NULL;
    n     integer := 0;
BEGIN
    FOR e IN SELECT * FROM lifecycle_event WHERE stream_id = p_stream ORDER BY stream_seq LOOP
        n := n + 1;
        IF e.stream_seq <> n THEN
            RAISE EXCEPTION 'replay: gap before stream_seq %', e.stream_seq;
        END IF;
        IF e.previous_state IS DISTINCT FROM state THEN
            RAISE EXCEPTION 'replay: event % expects % but replay is in %', e.stream_seq, e.previous_state, state;
        END IF;
        IF n > 1 AND NOT EXISTS (SELECT 1 FROM allowed_transition WHERE from_state = e.previous_state
                                    AND event_type = e.event_type AND to_state = e.new_state) THEN
            RAISE EXCEPTION 'replay: event % is not an allowed transition', e.stream_seq;
        END IF;
        state := e.new_state;
    END LOOP;
    RETURN state;
END $$;

CREATE FUNCTION verify_event_chain(p_stream uuid) RETURNS TABLE (stream_seq integer, problem text)
LANGUAGE plpgsql STABLE AS $$
DECLARE
    e    lifecycle_event%ROWTYPE;
    prev bytea := NULL;
BEGIN
    FOR e IN SELECT * FROM lifecycle_event le WHERE le.stream_id = p_stream ORDER BY le.stream_seq LOOP
        IF e.prev_hash IS DISTINCT FROM prev THEN
            stream_seq := e.stream_seq; problem := 'prev_hash does not match previous row'; RETURN NEXT;
        END IF;
        IF e.row_hash <> event_hash(e.prev_hash, e) THEN
            stream_seq := e.stream_seq; problem := 'row content changed after it was written'; RETURN NEXT;
        END IF;
        prev := e.row_hash;
    END LOOP;
END $$;

-- =============================================================================
-- 9. Views
-- =============================================================================
CREATE VIEW v_moderation_queue AS                       -- UC-D6 step 2, UC-I4 step 1
SELECT ec.id AS case_id, ec.transaction_id, ec.trigger_type, ec.hold_reason, ec.dispute_reason, ec.priority,
       ec.status, ec.assigned_to, i.community_id, t.current_state, ec.opened_at
  FROM escalation_case ec JOIN borrowing_transaction t ON t.id = ec.transaction_id JOIN item i ON i.id = t.item_id
 WHERE ec.status IN ('OPEN', 'AWAITING_INFORMATION');

CREATE VIEW v_pending_outcomes AS                      -- R4: closing events not yet turned into outcomes (FR-B-15)
SELECT e.event_id, e.stream_id, e.event_type, e.occurred_at
  FROM lifecycle_event e
 WHERE e.event_type IN ('transaction_closed', 'dispute_resolved')
   AND NOT EXISTS (SELECT 1 FROM outcome o WHERE o.source_event_id = e.event_id);

CREATE VIEW v_item_calendar AS                          -- held bookings only; pending requests block nothing (ADR-0001)
SELECT item_id, period, transaction_id FROM booking WHERE status = 'HELD';

CREATE VIEW v_audit_trail AS                            -- UC-I6: lifecycle events and other audited actions together
SELECT e.occurred_at, e.actor_id, e.authorisation, e.event_type::text AS action, 'borrowing_transaction'::text AS target_type,
       e.stream_id::text AS target_id, to_jsonb(e.previous_state) AS previous_value, to_jsonb(e.new_state) AS new_value,
       e.evidence_refs, 'SUCCESS'::text AS outcome
  FROM lifecycle_event e
UNION ALL
SELECT a.occurred_at, a.actor_id, a.authorisation, a.action, a.target_type, a.target_id, a.previous_value, a.new_value,
       a.evidence_refs, a.outcome
  FROM audit_log a;

-- =============================================================================
-- 10. Reference data: transition table (generated from _tools/lifecycle_model.py; 34 leaf rows)
-- =============================================================================
INSERT INTO allowed_transition (from_state, event_type, to_state, allowed_roles, ref, iteration)
SELECT f::lifecycle_state, ev::event_type, t::lifecycle_state, r::actor_role[], ref, it
FROM (VALUES
    ('REQUEST_CREATED'   , 'locality_checked'     , 'LOCALITY_CHECKED' , '{SYSTEM}', 'T02', 1),
    ('REQUEST_CREATED'   , 'held_for_review'      , 'HELD_FOR_REVIEW'  , '{SYSTEM}', 'T03/T04', 1),
    ('LOCALITY_CHECKED'  , 'assessment_generated' , 'ASSESSED'         , '{SYSTEM}', 'T05', 1),
    ('LOCALITY_CHECKED'  , 'held_for_review'      , 'HELD_FOR_REVIEW'  , '{SYSTEM}', 'T06/T07/T08', 1),
    ('HELD_FOR_REVIEW'   , 'hold_cleared'         , 'LOCALITY_CHECKED' , '{ADMIN,MODERATOR}', 'T09/T10', 1),
    ('HELD_FOR_REVIEW'   , 'hold_cleared'         , 'ASSESSED'         , '{MODERATOR,ADMIN}', 'T11', 1),
    ('HELD_FOR_REVIEW'   , 'request_declined'     , 'DECLINED'         , '{ADMIN,MODERATOR,SYSTEM}', 'T12/T17', 1),
    ('ASSESSED'          , 'request_accepted'     , 'ACCEPTED'         , '{LENDER}', 'T13', 1),
    ('ASSESSED'          , 'request_declined'     , 'DECLINED'         , '{LENDER,SYSTEM}', 'T14/T17', 1),
    ('ASSESSED'          , 'request_expired'      , 'EXPIRED'          , '{SYSTEM}', 'T15', 2),
    ('REQUEST_CREATED'   , 'request_cancelled'    , 'CANCELLED'        , '{BORROWER}', 'T16', 1),
    ('LOCALITY_CHECKED'  , 'request_cancelled'    , 'CANCELLED'        , '{BORROWER}', 'T16', 1),
    ('HELD_FOR_REVIEW'   , 'request_cancelled'    , 'CANCELLED'        , '{BORROWER}', 'T16', 1),
    ('ASSESSED'          , 'request_cancelled'    , 'CANCELLED'        , '{BORROWER}', 'T16', 1),
    ('REQUEST_CREATED'   , 'request_declined'     , 'DECLINED'         , '{SYSTEM}', 'T17', 1),
    ('LOCALITY_CHECKED'  , 'request_declined'     , 'DECLINED'         , '{SYSTEM}', 'T17', 1),
    ('ACCEPTED'          , 'handover_confirmed'   , 'ACTIVE'           , '{BORROWER,LENDER}', 'T18', 1),
    ('ACCEPTED'          , 'no_show'              , 'NO_SHOW'          , '{SYSTEM}', 'T19', 2),
    ('ACTIVE'            , 'return_initiated'     , 'RETURN_INITIATED' , '{BORROWER}', 'T20', 1),
    ('RETURN_INITIATED'  , 'return_confirmed'     , 'RETURNED'         , '{BORROWER,LENDER}', 'T21', 1),
    ('RETURNED'          , 'transaction_closed'   , 'COMPLETED'        , '{SYSTEM}', 'T22', 1),
    ('ACCEPTED'          , 'dispute_opened'       , 'DISPUTED'         , '{BORROWER,LENDER}', 'T23', 1),
    ('ACTIVE'            , 'dispute_opened'       , 'DISPUTED'         , '{BORROWER,LENDER,SYSTEM}', 'T23/T24', 1),
    ('RETURN_INITIATED'  , 'dispute_opened'       , 'DISPUTED'         , '{BORROWER,LENDER}', 'T23', 1),
    ('DISPUTED'          , 'dispute_resolved'     , 'COMPLETED'        , '{MODERATOR,ADMIN}', 'T25', 1),
    ('DISPUTED'          , 'dispute_withdrawn'    , 'ACCEPTED'         , '{BORROWER,LENDER}', 'T26', 1),
    ('DISPUTED'          , 'dispute_withdrawn'    , 'ACTIVE'           , '{BORROWER,LENDER}', 'T26', 1),
    ('DISPUTED'          , 'dispute_withdrawn'    , 'RETURN_INITIATED' , '{BORROWER,LENDER}', 'T26', 1),
    ('ACCEPTED'          , 'reminder_sent'        , 'ACCEPTED'         , '{SYSTEM}', 'I01', 2),
    ('ACTIVE'            , 'reminder_sent'        , 'ACTIVE'           , '{SYSTEM}', 'I02', 2),
    ('ACTIVE'            , 'extension_requested'  , 'ACTIVE'           , '{BORROWER}', 'I03', 2),
    ('ACTIVE'            , 'extension_approved'   , 'ACTIVE'           , '{LENDER}', 'I04', 2),
    ('ACTIVE'            , 'extension_declined'   , 'ACTIVE'           , '{LENDER}', 'I05', 2),
    ('RETURN_INITIATED'  , 'reminder_sent'        , 'RETURN_INITIATED' , '{SYSTEM}', 'I06', 2)
) AS v (f, ev, t, r, ref, it);

-- =============================================================================
-- 11. Privileges: the application role cannot rewrite history or the projection
-- =============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dm_app') THEN
        CREATE ROLE dm_app NOLOGIN;
    END IF;
END $$;
GRANT USAGE ON SCHEMA dm TO dm_app;
GRANT SELECT ON ALL TABLES IN SCHEMA dm TO dm_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dm TO dm_app;
GRANT INSERT ON lifecycle_event, audit_log, moderator_decision, assessment, condition_report, case_statement,
                locality_verification, outcome, review, attachment TO dm_app;
GRANT INSERT (id, item_id, borrower_id, lender_id, requested_period, message) ON borrowing_transaction TO dm_app;
GRANT INSERT, UPDATE ON app_user, community, membership, item, category, trust_edge TO dm_app;
GRANT INSERT ON invitation TO dm_app;
GRANT INSERT, DELETE ON user_block TO dm_app;
GRANT DELETE ON attachment, trust_edge TO dm_app;
GRANT UPDATE (status, flagged_by_decision_id) ON outcome TO dm_app;
GRANT UPDATE (status, assigned_to, info_deadline) ON escalation_case TO dm_app;   -- C02-C05 case actions

COMMIT;
