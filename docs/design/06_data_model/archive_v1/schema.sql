-- =============================================================================
-- Digital Mohalla: committed-core database schema
-- Target: PostgreSQL 14 or later (tested on PostgreSQL 16.2)
-- Owner: Student 1 (transaction and location infrastructure), design phase 2
--
-- Design rules implemented here (see ER_Schema_Design.md for the rationale):
--   R1  Event sourcing: transaction_event is the source of truth; the
--       borrow_transaction row is a projection updated only by a trigger.
--   R2  The state machine (State_Machine_Design.md v1.1) is enforced in the
--       database: allowed_transition plus role, party and history checks.
--   R3  Append-only history: events, audit log, decisions, assurance results,
--       condition reports, statements, requests and locality results cannot
--       be updated or deleted. Events and the audit log are hash-chained.
--   R4  Location privacy: no column stores coordinates or an address. Only the
--       coarse locality outcome is kept; photos must have metadata stripped.
--   R5  No double booking: per-item lock plus overlap check covering accepted
--       bookings and lender-blocked dates.
-- Run inside one transaction:  psql -v ON_ERROR_STOP=1 -f schema.sql
-- =============================================================================

BEGIN;

CREATE SCHEMA dm;
SET search_path = dm, public;

-- -----------------------------------------------------------------------------
-- 1. Enumerated types (names agreed at Step 0)
-- -----------------------------------------------------------------------------
CREATE TYPE account_status      AS ENUM ('PENDING_VERIFICATION', 'ACTIVE', 'SUSPENDED', 'BANNED');
CREATE TYPE account_type        AS ENUM ('INDIVIDUAL', 'HOUSEHOLD');
-- Declaration order matters: later values are "higher" levels (overview section 5, Verification).
CREATE TYPE verification_level  AS ENUM ('UNVERIFIED', 'CONTACT_VERIFIED', 'COMMUNITY_VERIFIED', 'IDENTITY_VERIFIED');
CREATE TYPE platform_role       AS ENUM ('MEMBER', 'ADMIN');
CREATE TYPE join_policy         AS ENUM ('OPEN', 'APPROVAL', 'INVITE_ONLY');
CREATE TYPE membership_role     AS ENUM ('MEMBER', 'MODERATOR');
CREATE TYPE membership_status   AS ENUM ('PENDING', 'AWAITING_INFORMATION', 'APPROVED', 'REJECTED', 'WITHDRAWN', 'REVOKED');
CREATE TYPE verification_method AS ENUM ('COARSE_GEOFENCE', 'INVITATION', 'MODERATOR_APPROVAL', 'ADDRESS_EVIDENCE');
-- No negative outcome on purpose: GPS evidence never rejects anyone automatically (UC-A3 3a-3c).
CREATE TYPE locality_outcome    AS ENUM ('VERIFIED', 'INCONCLUSIVE', 'CONFLICTING', 'INSUFFICIENT');
CREATE TYPE eligibility_result  AS ENUM ('ELIGIBLE', 'INCONCLUSIVE', 'INELIGIBLE');
CREATE TYPE item_status         AS ENUM ('DRAFT', 'PENDING_REVIEW', 'PUBLISHED', 'PAUSED', 'EXPIRED', 'REMOVED');
CREATE TYPE item_condition      AS ENUM ('NEW', 'LIKE_NEW', 'GOOD', 'FAIR', 'POOR');
CREATE TYPE value_band          AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH');

CREATE TYPE txn_state AS ENUM (
    -- PENDING
    'REQUESTED', 'ASSESSING', 'MODERATOR_REVIEW', 'AWAITING_LENDER',
    -- IN_PROGRESS
    'AWAITING_HANDOVER', 'AWAITING_RECEIPT', 'ON_LOAN', 'OVERDUE', 'RETURN_PENDING',
    -- DISPUTED
    'DISPUTE_OPEN', 'DISPUTE_ESCALATED',
    -- closed
    'COMPLETED', 'RESOLVED', 'DECLINED', 'CANCELLED', 'EXPIRED', 'NO_SHOW', 'INELIGIBLE');

CREATE TYPE txn_event_type AS ENUM (
    'REQUEST_CREATED', 'LOCALITY_CHECKED', 'ASSURANCE_GENERATED', 'ASSURANCE_FAILED',
    'EVIDENCE_REQUESTED', 'EVIDENCE_SUBMITTED', 'MODERATOR_CLEARED', 'MODERATOR_RESTRICTED',
    'LENDER_ACCEPTED', 'LENDER_DECLINED', 'REQUEST_AUTO_DECLINED', 'REQUEST_EXPIRED',
    'TRANSACTION_CANCELLED', 'REMINDER_SENT', 'HANDOVER_RECORDED', 'CONDITION_NOTE_ADDED',
    'HANDOVER_CONFIRMED', 'HANDOVER_NO_SHOW', 'LOAN_OVERDUE', 'EXTENSION_REQUESTED',
    'EXTENSION_APPROVED', 'EXTENSION_DECLINED', 'RETURN_INITIATED', 'RETURN_CONFIRMED',
    'DISPUTE_OPENED', 'DISPUTE_RESPONSE_ADDED', 'DISPUTE_INFO_REQUESTED', 'DISPUTE_DEADLINE_ELAPSED',
    'DISPUTE_ESCALATED', 'DISPUTE_RESOLVED', 'DISPUTE_WITHDRAWN');

CREATE TYPE actor_role       AS ENUM ('BORROWER', 'LENDER', 'MODERATOR', 'ADMIN', 'SYSTEM');
CREATE TYPE audit_actor_role AS ENUM ('MEMBER', 'BORROWER', 'LENDER', 'MODERATOR', 'ADMIN', 'SYSTEM');
CREATE TYPE party_role       AS ENUM ('BORROWER', 'LENDER');
CREATE TYPE assurance_state  AS ENUM ('SUFFICIENT_EVIDENCE', 'REVIEW_RECOMMENDED', 'INSUFFICIENT_EVIDENCE', 'ACTIVE_DISPUTE');
CREATE TYPE confidence_level AS ENUM ('LOW', 'MEDIUM', 'HIGH');
CREATE TYPE dispute_reason   AS ENUM ('CONDITION_MISMATCH', 'DAMAGE', 'NON_RETURN', 'NO_SHOW',
                                      'HANDOVER_UNCONFIRMED', 'RETURN_UNCONFIRMED', 'PARTY_SUSPENDED', 'OTHER');
CREATE TYPE dispute_status   AS ENUM ('OPEN', 'ESCALATED', 'RESOLVED', 'WITHDRAWN');
CREATE TYPE decision_context AS ENUM ('MEMBERSHIP', 'PRE_ACCEPTANCE_REVIEW', 'DISPUTE');
CREATE TYPE decision_kind    AS ENUM ('APPROVE', 'REJECT', 'REQUEST_INFO', 'CLEAR', 'RESTRICT',
                                      'ESCALATE', 'CLOSE', 'RESUME', 'REVERSE');
CREATE TYPE condition_phase  AS ENUM ('HANDOVER', 'RETURN');
CREATE TYPE outcome_kind     AS ENUM ('SUCCESS', 'FAILURE');
CREATE TYPE evidence_status  AS ENUM ('VALID', 'FLAGGED_FOR_REEVALUATION', 'SUPERSEDED');
CREATE TYPE attachment_kind  AS ENUM ('PHOTO', 'DOCUMENT');

-- -----------------------------------------------------------------------------
-- 2. State-machine helper functions (used in CHECKs, so IMMUTABLE)
-- -----------------------------------------------------------------------------
CREATE FUNCTION is_closed(s txn_state) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT s IN ('COMPLETED', 'RESOLVED', 'DECLINED', 'CANCELLED', 'EXPIRED', 'NO_SHOW', 'INELIGIBLE')
$$;
CREATE FUNCTION is_pending(s txn_state) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT s IN ('REQUESTED', 'ASSESSING', 'MODERATOR_REVIEW', 'AWAITING_LENDER')
$$;
CREATE FUNCTION is_disputed(s txn_state) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT s IN ('DISPUTE_OPEN', 'DISPUTE_ESCALATED')
$$;
-- States in which the item's dates are firmly booked (accepted and not yet closed).
CREATE FUNCTION holds_dates(s txn_state) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT s IN ('AWAITING_HANDOVER', 'AWAITING_RECEIPT', 'ON_LOAN', 'OVERDUE', 'RETURN_PENDING',
                 'DISPUTE_OPEN', 'DISPUTE_ESCALATED')
$$;
-- Direct substate of IN_PROGRESS: what the shallow history pseudostate (H) remembers.
CREATE FUNCTION in_progress_phase(s txn_state) RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE
        WHEN s IN ('AWAITING_HANDOVER', 'AWAITING_RECEIPT') THEN 'HANDOVER_PENDING'
        WHEN s IN ('ON_LOAN', 'OVERDUE')                  THEN 'ACTIVE'
        WHEN s = 'RETURN_PENDING'                         THEN 'RETURN_PENDING'
    END
$$;
CREATE FUNCTION is_bounded_range(r tstzrange) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT NOT isempty(r) AND NOT lower_inf(r) AND NOT upper_inf(r) AND lower_inc(r) AND NOT upper_inc(r)
$$;

-- -----------------------------------------------------------------------------
-- 3. Users, communities, membership and locality (location privacy lives here)
-- -----------------------------------------------------------------------------
CREATE TABLE app_user (                                    -- entity: User
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name       text NOT NULL CHECK (length(btrim(display_name)) BETWEEN 1 AND 80),
    email              text,
    phone              text,
    password_hash      text,                                -- NULL when a social login is used
    account_type       account_type       NOT NULL DEFAULT 'INDIVIDUAL',
    verification_level verification_level NOT NULL DEFAULT 'UNVERIFIED',
    platform_role      platform_role      NOT NULL DEFAULT 'MEMBER',
    status             account_status     NOT NULL DEFAULT 'PENDING_VERIFICATION',
    created_at         timestamptz        NOT NULL DEFAULT now(),
    -- R4: deliberately no address, latitude or longitude columns.
    CONSTRAINT app_user_contact_ck CHECK (email IS NOT NULL OR phone IS NOT NULL)
);
CREATE UNIQUE INDEX app_user_email_uq ON app_user (lower(email)) WHERE email IS NOT NULL;
CREATE UNIQUE INDEX app_user_phone_uq ON app_user (phone)        WHERE phone IS NOT NULL;

CREATE TABLE user_block (                                  -- UC-A7
    blocker_id uuid NOT NULL REFERENCES app_user (id),
    blocked_id uuid NOT NULL REFERENCES app_user (id),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (blocker_id, blocked_id),
    CONSTRAINT user_block_self_ck CHECK (blocker_id <> blocked_id)
);

CREATE TABLE community (                                   -- entity: Community
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                   text NOT NULL CHECK (length(btrim(name)) > 0),
    join_code              text NOT NULL UNIQUE,
    join_policy            join_policy NOT NULL DEFAULT 'APPROVAL',
    allowed_methods        verification_method[] NOT NULL CHECK (cardinality(allowed_methods) > 0),
    -- Coarse geofence of the housing society. Community data, not personal data.
    boundary_geojson       jsonb,
    verification_valid_for interval NOT NULL DEFAULT interval '365 days',
    rules                  text,
    is_active              boolean NOT NULL DEFAULT true,
    created_at             timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT community_geofence_ck
        CHECK (NOT ('COARSE_GEOFENCE' = ANY (allowed_methods)) OR boundary_geojson IS NOT NULL)
);
CREATE UNIQUE INDEX community_name_uq ON community (lower(name));

CREATE TABLE membership (                                  -- User M:N Community, UC-A3/A4
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES app_user (id),
    community_id uuid NOT NULL REFERENCES community (id),
    role         membership_role   NOT NULL DEFAULT 'MEMBER',
    status       membership_status NOT NULL DEFAULT 'PENDING',
    requested_at timestamptz NOT NULL DEFAULT now(),
    decided_at   timestamptz,                               -- when it left PENDING/AWAITING_INFORMATION
    CONSTRAINT membership_decided_ck
        CHECK ((status IN ('PENDING', 'AWAITING_INFORMATION')) = (decided_at IS NULL))
);
-- UC-A3 4b: at most one live request or membership per user and community.
CREATE UNIQUE INDEX membership_one_live_uq ON membership (user_id, community_id)
    WHERE status IN ('PENDING', 'AWAITING_INFORMATION', 'APPROVED');

CREATE TABLE invitation (                                  -- invitation-based verification
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id uuid NOT NULL REFERENCES community (id),
    inviter_id   uuid NOT NULL REFERENCES app_user (id),
    code_hash    bytea NOT NULL UNIQUE,                     -- only the hash of the code is stored
    created_at   timestamptz NOT NULL DEFAULT now(),
    expires_at   timestamptz NOT NULL,
    CONSTRAINT invitation_expiry_ck CHECK (expires_at > created_at)
);

-- Result of one locality check. R4: the raw GPS fix is evaluated in memory and
-- discarded; only this coarse outcome is stored. Append-only (re-checks add rows).
CREATE TABLE locality_verification (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    membership_id       uuid NOT NULL REFERENCES membership (id),
    method              verification_method NOT NULL,
    outcome             locality_outcome    NOT NULL,
    boundary_case       boolean NOT NULL DEFAULT false,     -- UC-A3 3b
    permission_refused  boolean NOT NULL DEFAULT false,     -- UC-A3 3a
    location_conflict   boolean NOT NULL DEFAULT false,     -- UC-A3 3c (possible spoofing)
    duplicate_suspected boolean NOT NULL DEFAULT false,     -- UC-A3 4d
    invitation_id       uuid REFERENCES invitation (id),
    checked_at          timestamptz NOT NULL DEFAULT now(),
    valid_until         timestamptz NOT NULL,               -- "verified once or periodically"
    CONSTRAINT locality_invitation_ck   CHECK ((method = 'INVITATION') = (invitation_id IS NOT NULL)),
    CONSTRAINT locality_validity_ck     CHECK (valid_until > checked_at),
    CONSTRAINT locality_refusal_ck      CHECK (NOT permission_refused OR outcome = 'INSUFFICIENT'),
    CONSTRAINT locality_conflict_ck     CHECK (NOT location_conflict OR outcome = 'CONFLICTING')
);
CREATE UNIQUE INDEX locality_invitation_single_use_uq ON locality_verification (invitation_id)
    WHERE invitation_id IS NOT NULL;
CREATE INDEX locality_membership_ix ON locality_verification (membership_id, checked_at DESC);

-- -----------------------------------------------------------------------------
-- 4. Items and availability
-- -----------------------------------------------------------------------------
CREATE TABLE category (
    id               smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name             text NOT NULL UNIQUE,
    is_restricted    boolean NOT NULL DEFAULT false,        -- medical, automotive, high-value electronics
    min_verification verification_level NOT NULL DEFAULT 'COMMUNITY_VERIFIED'
);

CREATE TABLE item (                                        -- entity: Item
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id              uuid NOT NULL REFERENCES app_user (id),
    community_id          uuid NOT NULL REFERENCES community (id),  -- approximate location = community
    category_id           smallint NOT NULL REFERENCES category (id),
    title                 text NOT NULL CHECK (length(btrim(title)) BETWEEN 1 AND 120),
    description           text,
    condition             item_condition NOT NULL,
    value_band            value_band NOT NULL,              -- used for similarity (overview 5.12)
    estimated_value       numeric(12, 2) CHECK (estimated_value >= 0),
    deposit_amount        numeric(12, 2) NOT NULL DEFAULT 0 CHECK (deposit_amount >= 0),
    required_verification verification_level NOT NULL DEFAULT 'COMMUNITY_VERIFIED',
    usage_instructions    text,
    restrictions          text,
    status                item_status NOT NULL DEFAULT 'DRAFT',
    listing_expires_at    timestamptz,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX item_community_status_ix ON item (community_id, status);

CREATE TABLE availability_block (                          -- dates the lender blocks (UC-B2)
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id    uuid NOT NULL REFERENCES item (id),
    period     tstzrange NOT NULL CHECK (is_bounded_range(period)),
    note       text,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX availability_block_period_ix ON availability_block USING gist (period);

-- -----------------------------------------------------------------------------
-- 5. Transaction aggregate, request and the append-only event store
-- -----------------------------------------------------------------------------
CREATE TABLE borrow_transaction (                          -- entity: Transaction (projection)
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id       uuid NOT NULL REFERENCES item (id),
    borrower_id   uuid NOT NULL REFERENCES app_user (id),
    lender_id     uuid NOT NULL REFERENCES app_user (id),
    period        tstzrange NOT NULL CHECK (is_bounded_range(period)),  -- [start, due); extensions move the upper bound
    handover_time timestamptz,
    -- Projection fields: written only by trigger event_apply (R1).
    current_state txn_state,
    version       integer NOT NULL DEFAULT 0 CHECK (version >= 0),      -- = last sequence_no
    last_event_at timestamptz,
    closed_at     timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT txn_parties_ck CHECK (borrower_id <> lender_id),
    CONSTRAINT txn_version_ck CHECK ((version = 0) = (current_state IS NULL)),
    CONSTRAINT txn_closed_ck  CHECK ((closed_at IS NOT NULL) = (current_state IS NOT NULL AND is_closed(current_state)))
);
CREATE INDEX txn_item_ix     ON borrow_transaction (item_id);
CREATE INDEX txn_state_ix    ON borrow_transaction (current_state);
CREATE INDEX txn_borrower_ix ON borrow_transaction (borrower_id);
CREATE INDEX txn_lender_ix   ON borrow_transaction (lender_id);

CREATE TABLE request (                                     -- entity: Request (1:1 Transaction, DD-1)
    transaction_id      uuid PRIMARY KEY REFERENCES borrow_transaction (id),
    requested_period    tstzrange NOT NULL CHECK (is_bounded_range(requested_period)),
    message             text,
    accepted_safeguards jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(accepted_safeguards) = 'array'),
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- Reference data: every transition in State_Machine_Design.md section 6,
-- expanded from composite borders to leaf states.
CREATE TABLE allowed_transition (
    from_state    txn_state      NOT NULL,
    event_type    txn_event_type NOT NULL,
    to_state      txn_state      NOT NULL,
    allowed_roles actor_role[]   NOT NULL CHECK (cardinality(allowed_roles) > 0),
    ref           text           NOT NULL,                  -- T01..T33 / I01..I12
    PRIMARY KEY (from_state, event_type, to_state)
);

CREATE TABLE transaction_event (                           -- entity: TransactionEvent (append-only)
    event_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_id uuid NOT NULL REFERENCES borrow_transaction (id),
    sequence_no    integer NOT NULL CHECK (sequence_no > 0),
    event_type     txn_event_type NOT NULL,
    actor_user_id  uuid REFERENCES app_user (id),           -- actor
    actor_role     actor_role NOT NULL,
    occurred_at    timestamptz NOT NULL DEFAULT clock_timestamp(),  -- timestamp (set by server)
    previous_state txn_state,                                -- previous state
    new_state      txn_state NOT NULL,                       -- new state
    evidence       jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(evidence) = 'object'),
    authorisation  text  NOT NULL,
    payload        jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(payload) = 'object'),
    prev_hash      bytea,
    row_hash       bytea NOT NULL,                           -- set by trigger
    CONSTRAINT event_sequence_uq   UNIQUE (transaction_id, sequence_no),
    CONSTRAINT event_actor_ck      CHECK ((actor_role = 'SYSTEM') = (actor_user_id IS NULL)),
    CONSTRAINT event_first_ck      CHECK ((sequence_no = 1) = (previous_state IS NULL)),
    CONSTRAINT event_first_type_ck CHECK (sequence_no > 1 OR (event_type = 'REQUEST_CREATED' AND new_state = 'REQUESTED')),
    CONSTRAINT event_authorisation_ck CHECK (
        (actor_role = 'BORROWER'  AND authorisation = 'party:borrower') OR
        (actor_role = 'LENDER'    AND authorisation = 'party:lender')   OR
        (actor_role = 'MODERATOR' AND authorisation ~ '^role:moderator@[A-Za-z0-9-]+$') OR
        (actor_role = 'ADMIN'     AND authorisation = 'role:admin')     OR
        (actor_role = 'SYSTEM'    AND authorisation ~ '^system:[a-z0-9_.-]+$')),
    CONSTRAINT event_transition_fk FOREIGN KEY (previous_state, event_type, new_state)
        REFERENCES allowed_transition (from_state, event_type, to_state)
);
CREATE INDEX event_type_ix ON transaction_event (transaction_id, event_type);

-- -----------------------------------------------------------------------------
-- 6. Handover and return evidence
-- -----------------------------------------------------------------------------
CREATE TABLE condition_report (                            -- checklists (UC-B7, B8). Append-only.
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id   uuid NOT NULL REFERENCES borrow_transaction (id),
    phase            condition_phase NOT NULL,
    reported_by      uuid NOT NULL REFERENCES app_user (id),
    reporter_role    party_role NOT NULL,
    checklist        jsonb NOT NULL CHECK (jsonb_typeof(checklist) IN ('object', 'array')),
    notes            text,
    reduced_evidence boolean NOT NULL DEFAULT false,       -- UC-B7 3a: no photos
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX condition_report_txn_ix ON condition_report (transaction_id, phase);

-- -----------------------------------------------------------------------------
-- 7. Assurance (fields owned by Student 2; structure agreed for integration)
-- -----------------------------------------------------------------------------
CREATE TABLE assurance_result (                            -- entity: AssuranceResult (append-only)
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id          uuid NOT NULL REFERENCES borrow_transaction (id),
    generated_at            timestamptz NOT NULL DEFAULT now(),
    engine_version          text NOT NULL,
    assurance_state         assurance_state NOT NULL,
    requires_moderator      boolean NOT NULL,               -- drives T04 / T05
    escalation_reason       text,
    success_probability     numeric(5, 4) CHECK (success_probability BETWEEN 0 AND 1),   -- posterior mean
    credible_low            numeric(5, 4) CHECK (credible_low  BETWEEN 0 AND 1),
    credible_high           numeric(5, 4) CHECK (credible_high BETWEEN 0 AND 1),
    confidence              confidence_level NOT NULL,
    direct_evidence         jsonb NOT NULL DEFAULT '{}',
    indirect_evidence       jsonb NOT NULL DEFAULT '{}',
    manipulation_risk_score smallint NOT NULL CHECK (manipulation_risk_score BETWEEN 0 AND 100),
    manipulation_signals    jsonb NOT NULL DEFAULT '[]',
    safeguards              jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(safeguards) = 'array'),
    explanation             text NOT NULL,                  -- never a bare score (overview 5.7)
    parameters              jsonb NOT NULL DEFAULT '{}',    -- prior, decay, k: reproducibility
    CONSTRAINT assurance_interval_ck CHECK (
        credible_low IS NULL OR credible_high IS NULL OR success_probability IS NULL OR
        (credible_low <= success_probability AND success_probability <= credible_high)),
    CONSTRAINT assurance_escalation_ck CHECK (NOT requires_moderator OR escalation_reason IS NOT NULL)
);
CREATE INDEX assurance_txn_ix ON assurance_result (transaction_id, generated_at DESC);

-- -----------------------------------------------------------------------------
-- 8. Disputes and moderator decisions
-- -----------------------------------------------------------------------------
CREATE TABLE dispute (                                     -- entity: Dispute (created by trigger)
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id    uuid NOT NULL REFERENCES borrow_transaction (id),
    opened_event_id   bigint NOT NULL UNIQUE REFERENCES transaction_event (event_id),
    raised_by         uuid REFERENCES app_user (id),        -- NULL when the system opened it
    raised_by_role    actor_role NOT NULL CHECK (raised_by_role IN ('BORROWER', 'LENDER', 'SYSTEM')),
    reason            dispute_reason NOT NULL,
    description       text,
    status            dispute_status NOT NULL DEFAULT 'OPEN',
    assigned_to       uuid REFERENCES app_user (id),
    response_deadline timestamptz NOT NULL,
    opened_at         timestamptz NOT NULL DEFAULT now(),
    closed_at         timestamptz,
    closing_event_id  bigint REFERENCES transaction_event (event_id),
    CONSTRAINT dispute_raiser_ck CHECK ((raised_by_role = 'SYSTEM') = (raised_by IS NULL)),
    CONSTRAINT dispute_closed_ck CHECK ((status IN ('RESOLVED', 'WITHDRAWN')) = (closed_at IS NOT NULL))
);
-- UC-B12 2a / D6 2a: one live dispute per transaction.
CREATE UNIQUE INDEX dispute_one_live_uq ON dispute (transaction_id) WHERE status IN ('OPEN', 'ESCALATED');

CREATE TABLE dispute_statement (                           -- claims and responses. Append-only.
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id  uuid NOT NULL REFERENCES dispute (id),
    author_id   uuid NOT NULL REFERENCES app_user (id),
    author_role party_role NOT NULL,
    statement   text NOT NULL CHECK (length(btrim(statement)) > 0),
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE attachment (                                  -- photos and documents (files stored outside the DB)
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id       uuid NOT NULL REFERENCES borrow_transaction (id),
    condition_report_id  uuid REFERENCES condition_report (id),
    dispute_statement_id uuid REFERENCES dispute_statement (id),
    uploaded_by          uuid NOT NULL REFERENCES app_user (id),
    kind                 attachment_kind NOT NULL,
    storage_key          text  NOT NULL UNIQUE,
    content_sha256       bytea NOT NULL CHECK (octet_length(content_sha256) = 32),
    mime_type            text  NOT NULL CHECK (mime_type IN ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')),
    -- R4: EXIF/GPS metadata must be removed before a file is accepted.
    metadata_stripped    boolean NOT NULL CHECK (metadata_stripped),
    created_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT attachment_owner_ck CHECK (num_nonnulls(condition_report_id, dispute_statement_id) <= 1)
);

CREATE TABLE moderator_decision (                          -- entity: ModeratorDecision (append-only)
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    context              decision_context NOT NULL,
    kind                 decision_kind    NOT NULL,
    decided_by           uuid NOT NULL REFERENCES app_user (id),
    decider_role         actor_role NOT NULL CHECK (decider_role IN ('MODERATOR', 'ADMIN')),
    membership_id        uuid REFERENCES membership (id),
    transaction_id       uuid REFERENCES borrow_transaction (id),
    dispute_id           uuid REFERENCES dispute (id),
    event_id             bigint REFERENCES transaction_event (event_id),
    reason               text  NOT NULL CHECK (length(btrim(reason)) > 0),   -- DD-16
    outcome              jsonb NOT NULL DEFAULT '{}',
    reverses_decision_id uuid REFERENCES moderator_decision (id),            -- scenario 11
    decided_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT decision_subject_ck CHECK (CASE context
        WHEN 'MEMBERSHIP'            THEN membership_id IS NOT NULL AND transaction_id IS NULL AND dispute_id IS NULL
        WHEN 'PRE_ACCEPTANCE_REVIEW' THEN transaction_id IS NOT NULL AND membership_id IS NULL AND dispute_id IS NULL
        WHEN 'DISPUTE'               THEN dispute_id IS NOT NULL AND transaction_id IS NOT NULL AND membership_id IS NULL
    END),
    CONSTRAINT decision_kind_ck CHECK (CASE context
        WHEN 'MEMBERSHIP'            THEN kind IN ('APPROVE', 'REJECT', 'REQUEST_INFO', 'REVERSE')
        WHEN 'PRE_ACCEPTANCE_REVIEW' THEN kind IN ('CLEAR', 'RESTRICT', 'REQUEST_INFO', 'REVERSE')
        WHEN 'DISPUTE'               THEN kind IN ('REQUEST_INFO', 'ESCALATE', 'CLOSE', 'RESUME', 'REVERSE')
    END),
    CONSTRAINT decision_reversal_ck CHECK ((kind = 'REVERSE') = (reverses_decision_id IS NOT NULL)),
    CONSTRAINT decision_not_self_ck CHECK (reverses_decision_id IS NULL OR reverses_decision_id <> id)
);

-- -----------------------------------------------------------------------------
-- 9. Verified evidence, reviews and trust graph (inputs to the assurance engine)
-- -----------------------------------------------------------------------------
CREATE TABLE evidence_record (                             -- entity: EvidenceRecord
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_user_id        uuid NOT NULL REFERENCES app_user (id),
    subject_role           party_role NOT NULL,              -- role-specific reputation (5.3)
    source_event_id        bigint NOT NULL REFERENCES transaction_event (event_id),
    outcome                outcome_kind NOT NULL,
    on_time                boolean,                          -- borrower punctuality only
    condition_agreed       boolean NOT NULL,
    category_id            smallint NOT NULL REFERENCES category (id),     -- snapshot for similarity
    value_band             value_band NOT NULL,
    loan_duration          interval NOT NULL,
    occurred_at            timestamptz NOT NULL,             -- recency decay is computed at read time
    status                 evidence_status NOT NULL DEFAULT 'VALID',
    flagged_by_decision_id uuid REFERENCES moderator_decision (id),
    CONSTRAINT evidence_once_uq     UNIQUE (source_event_id, subject_user_id),
    CONSTRAINT evidence_on_time_ck  CHECK (subject_role = 'BORROWER' OR on_time IS NULL),
    CONSTRAINT evidence_flag_ck     CHECK (status <> 'FLAGGED_FOR_REEVALUATION' OR flagged_by_decision_id IS NOT NULL)
);
CREATE INDEX evidence_subject_ix ON evidence_record (subject_user_id, subject_role, occurred_at DESC);

CREATE TABLE review (                                      -- UC-D1 (input to manipulation signals)
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id   uuid NOT NULL REFERENCES borrow_transaction (id),
    reviewer_id      uuid NOT NULL REFERENCES app_user (id),
    reviewee_id      uuid NOT NULL REFERENCES app_user (id),
    reviewee_role    party_role NOT NULL,
    ratings          jsonb NOT NULL CHECK (jsonb_typeof(ratings) = 'object'),   -- one score per dimension
    comment          text,
    retaliation_flag boolean NOT NULL DEFAULT false,         -- UC-D1 3a
    similarity_flag  boolean NOT NULL DEFAULT false,         -- UC-D1 3b
    created_at       timestamptz NOT NULL DEFAULT now(),
    edit_until       timestamptz NOT NULL DEFAULT now() + interval '48 hours',  -- UC-D1 1b
    CONSTRAINT review_once_uq UNIQUE (transaction_id, reviewer_id),
    CONSTRAINT review_self_ck CHECK (reviewer_id <> reviewee_id)
);

CREATE TABLE trust_edge (                                  -- entity: TrustEdge (directed, weighted)
    from_user_id        uuid NOT NULL REFERENCES app_user (id),
    to_user_id          uuid NOT NULL REFERENCES app_user (id),
    weight              numeric(4, 3) NOT NULL CHECK (weight > 0 AND weight <= 1),
    evidence_count      integer NOT NULL CHECK (evidence_count > 0),
    last_interaction_at timestamptz NOT NULL,
    updated_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (from_user_id, to_user_id),
    CONSTRAINT trust_edge_self_ck CHECK (from_user_id <> to_user_id)
);
CREATE INDEX trust_edge_to_ix ON trust_edge (to_user_id);

-- -----------------------------------------------------------------------------
-- 10. Audit log (hash-chained, append-only; UC-I6)
-- -----------------------------------------------------------------------------
CREATE TABLE audit_log (                                   -- entity: AuditLog
    id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at    timestamptz NOT NULL DEFAULT clock_timestamp(),
    actor_user_id  uuid REFERENCES app_user (id),
    actor_role     audit_actor_role NOT NULL,
    action         text NOT NULL CHECK (action ~ '^[A-Z][A-Z0-9_]*$'),
    target_type    text NOT NULL,
    target_id      text NOT NULL,
    previous_value jsonb,
    new_value      jsonb,
    evidence       jsonb NOT NULL DEFAULT '{}',
    authorisation  text NOT NULL,
    outcome        text NOT NULL CHECK (outcome IN ('SUCCESS', 'REJECTED')),
    reason         text,
    prev_hash      bytea,
    row_hash       bytea NOT NULL,
    CONSTRAINT audit_actor_ck  CHECK ((actor_role = 'SYSTEM') = (actor_user_id IS NULL)),
    CONSTRAINT audit_reason_ck CHECK (outcome = 'SUCCESS' OR reason IS NOT NULL)
);
CREATE INDEX audit_actor_ix  ON audit_log (actor_user_id, occurred_at);
CREATE INDEX audit_target_ix ON audit_log (target_type, target_id);

-- =============================================================================
-- 11. Functions and triggers
-- =============================================================================

-- 11.1 Append-only guard (R3)
CREATE FUNCTION forbid_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION '% is append-only: % is not allowed', TG_TABLE_NAME, TG_OP
        USING ERRCODE = 'insufficient_privilege';
END $$;

DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['transaction_event', 'audit_log', 'moderator_decision', 'assurance_result',
                             'condition_report', 'dispute_statement', 'request', 'locality_verification',
                             'allowed_transition']
    LOOP
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION forbid_change()',
                       t || '_append_only', t);
        EXECUTE format('CREATE TRIGGER %I BEFORE TRUNCATE ON %I FOR EACH STATEMENT EXECUTE FUNCTION forbid_change()',
                       t || '_no_truncate', t);
    END LOOP;
END $$;
-- Attachments may be deleted by the retention policy (privacy) but never edited.
CREATE TRIGGER attachment_no_update BEFORE UPDATE ON attachment FOR EACH ROW EXECUTE FUNCTION forbid_change();

-- 11.2 Hashing
CREATE FUNCTION event_hash(p_prev bytea, p_txn uuid, p_seq integer, p_type txn_event_type, p_actor uuid,
                           p_role actor_role, p_at timestamptz, p_prev_state txn_state, p_new_state txn_state,
                           p_evidence jsonb, p_auth text, p_payload jsonb)
RETURNS bytea LANGUAGE sql STABLE AS $$
    SELECT sha256(coalesce(p_prev, '\x'::bytea) || convert_to(format('%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s',
        p_txn, p_seq, p_type, p_actor, p_role,
        to_char(p_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        p_prev_state, p_new_state, p_evidence, p_auth, p_payload), 'UTF8'))
$$;

CREATE FUNCTION audit_hash(p_prev bytea, r audit_log) RETURNS bytea LANGUAGE sql STABLE AS $$
    SELECT sha256(coalesce(p_prev, '\x'::bytea) || convert_to(format('%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s',
        r.id, to_char(r.occurred_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        r.actor_user_id, r.actor_role, r.action, r.target_type, r.target_id,
        r.previous_value, r.new_value, r.evidence, r.authorisation, r.outcome, r.reason), 'UTF8'))
$$;

-- 11.3 Locality eligibility (state REQUESTED, transitions T02/T03, DD-3).
-- Reads only the membership status and the stored coarse outcome: never coordinates.
CREATE FUNCTION locality_eligibility(p_user uuid, p_community uuid)
RETURNS eligibility_result LANGUAGE plpgsql STABLE AS $$
DECLARE
    m membership%ROWTYPE;
    v locality_verification%ROWTYPE;
BEGIN
    SELECT * INTO m FROM membership
     WHERE user_id = p_user AND community_id = p_community AND status = 'APPROVED';
    IF NOT FOUND THEN
        RETURN 'INELIGIBLE';                     -- a fact, not a GPS judgement
    END IF;
    SELECT * INTO v FROM locality_verification
     WHERE membership_id = m.id ORDER BY checked_at DESC LIMIT 1;
    IF FOUND AND v.outcome = 'VERIFIED' AND v.valid_until > now()
       AND NOT v.location_conflict AND NOT v.duplicate_suspected THEN
        RETURN 'ELIGIBLE';
    END IF;
    RETURN 'INCONCLUSIVE';                       -- weak, stale or conflicting: evidence, not rejection
END $$;

-- 11.4 Transaction creation guard (structural part of G1)
CREATE FUNCTION txn_guard_create() RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER SET search_path = dm, pg_temp AS $$
DECLARE
    i item%ROWTYPE;
    b app_user%ROWTYPE;
BEGIN
    IF NEW.current_state IS NOT NULL OR NEW.version <> 0 THEN
        RAISE EXCEPTION 'a transaction is created empty and started by REQUEST_CREATED'
            USING ERRCODE = 'check_violation';
    END IF;
    SELECT * INTO i FROM item WHERE id = NEW.item_id;
    IF i.status <> 'PUBLISHED' THEN
        RAISE EXCEPTION 'G1: item is not PUBLISHED' USING ERRCODE = 'check_violation';
    END IF;
    IF NEW.lender_id <> i.owner_id THEN
        RAISE EXCEPTION 'G1: lender must be the item owner' USING ERRCODE = 'check_violation';
    END IF;
    SELECT * INTO b FROM app_user WHERE id = NEW.borrower_id;
    IF b.status <> 'ACTIVE' THEN
        RAISE EXCEPTION 'G1: borrower account is not active' USING ERRCODE = 'check_violation';
    END IF;
    IF b.verification_level < i.required_verification THEN
        RAISE EXCEPTION 'G1: borrower is not verified to the level this item requires' USING ERRCODE = 'check_violation';
    END IF;
    IF EXISTS (SELECT 1 FROM user_block
                WHERE (blocker_id = NEW.lender_id AND blocked_id = NEW.borrower_id)
                   OR (blocker_id = NEW.borrower_id AND blocked_id = NEW.lender_id)) THEN
        -- The application must show a neutral message (UC-B5 7a: do not reveal the block).
        RAISE EXCEPTION 'G1: request not allowed between these users' USING ERRCODE = 'check_violation';
    END IF;
    IF lower(NEW.period) < now() THEN
        RAISE EXCEPTION 'G1: requested start is in the past' USING ERRCODE = 'check_violation';
    END IF;
    IF EXISTS (SELECT 1 FROM borrow_transaction o
                WHERE o.item_id = NEW.item_id AND o.borrower_id = NEW.borrower_id
                  AND o.current_state IS NOT NULL AND is_pending(o.current_state)
                  AND o.period && NEW.period) THEN
        RAISE EXCEPTION 'G1: duplicate pending request for this item and dates' USING ERRCODE = 'unique_violation';
    END IF;
    IF EXISTS (SELECT 1 FROM borrow_transaction o
                WHERE o.item_id = NEW.item_id AND o.current_state IS NOT NULL
                  AND holds_dates(o.current_state) AND o.period && NEW.period)
       OR EXISTS (SELECT 1 FROM availability_block a
                   WHERE a.item_id = NEW.item_id AND a.period && NEW.period) THEN
        RAISE EXCEPTION 'G1: dates unavailable' USING ERRCODE = 'exclusion_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER borrow_transaction_create BEFORE INSERT ON borrow_transaction
    FOR EACH ROW EXECUTE FUNCTION txn_guard_create();

-- Every transaction must have its REQUEST_CREATED event and its request row by commit time.
CREATE FUNCTION txn_require_start() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM transaction_event WHERE transaction_id = NEW.id)
       OR NOT EXISTS (SELECT 1 FROM request WHERE transaction_id = NEW.id) THEN
        RAISE EXCEPTION 'transaction % committed without REQUEST_CREATED event and request row', NEW.id
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER borrow_transaction_started AFTER INSERT ON borrow_transaction
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION txn_require_start();

-- 11.5 No double booking (R5). Runs whenever a transaction starts holding dates
-- or its period changes (acceptance, extension, resume with new due date).
CREATE FUNCTION txn_guard_dates() RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER SET search_path = dm, pg_temp AS $$
BEGIN
    IF NEW.current_state IS NULL OR NOT holds_dates(NEW.current_state) THEN
        RETURN NEW;
    END IF;
    IF TG_OP = 'UPDATE' AND OLD.current_state IS NOT NULL AND holds_dates(OLD.current_state)
       AND OLD.period = NEW.period THEN
        RETURN NEW;                              -- already holding the same dates
    END IF;
    PERFORM 1 FROM item WHERE id = NEW.item_id FOR UPDATE;   -- serialise bookings of this item
    IF EXISTS (SELECT 1 FROM borrow_transaction o
                WHERE o.item_id = NEW.item_id AND o.id <> NEW.id
                  AND o.current_state IS NOT NULL AND holds_dates(o.current_state)
                  AND o.period && NEW.period) THEN
        RAISE EXCEPTION 'dates unavailable: overlaps another accepted booking of this item'
            USING ERRCODE = 'exclusion_violation';
    END IF;
    IF EXISTS (SELECT 1 FROM availability_block a
                WHERE a.item_id = NEW.item_id AND a.period && NEW.period) THEN
        RAISE EXCEPTION 'dates unavailable: the lender has blocked these dates'
            USING ERRCODE = 'exclusion_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER borrow_transaction_dates BEFORE UPDATE OF current_state, period ON borrow_transaction
    FOR EACH ROW EXECUTE FUNCTION txn_guard_dates();

CREATE FUNCTION block_guard_dates() RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER SET search_path = dm, pg_temp AS $$
BEGIN
    PERFORM 1 FROM item WHERE id = NEW.item_id FOR UPDATE;
    IF EXISTS (SELECT 1 FROM borrow_transaction o
                WHERE o.item_id = NEW.item_id AND o.current_state IS NOT NULL
                  AND holds_dates(o.current_state) AND o.period && NEW.period) THEN
        RAISE EXCEPTION 'cannot block dates: they overlap an accepted or active booking (UC-B2 4a)'
            USING ERRCODE = 'exclusion_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER availability_block_dates BEFORE INSERT OR UPDATE ON availability_block
    FOR EACH ROW EXECUTE FUNCTION block_guard_dates();

-- 11.6 Event validation: concurrency, state machine, authorisation, guards, hash (R1, R2)
CREATE FUNCTION event_validate() RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER SET search_path = dm, pg_temp AS $$
DECLARE
    t            borrow_transaction%ROWTYPE;
    i            item%ROWTYPE;
    rule         allowed_transition%ROWTYPE;
    a            assurance_result%ROWTYPE;
    opened_from  txn_state;
    elig         eligibility_result;
    new_due      timestamptz;
    report_ok    boolean;
BEGIN
    NEW.occurred_at := clock_timestamp();        -- server time; clients cannot back-date events

    SELECT * INTO t FROM borrow_transaction WHERE id = NEW.transaction_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'transaction % does not exist', NEW.transaction_id USING ERRCODE = 'foreign_key_violation';
    END IF;
    SELECT * INTO i FROM item WHERE id = t.item_id;

    -- (a) Optimistic concurrency and continuity: the command must be based on the latest event.
    IF NEW.sequence_no <> t.version + 1 THEN
        RAISE EXCEPTION 'stale command: expected sequence_no %, got %', t.version + 1, NEW.sequence_no
            USING ERRCODE = 'serialization_failure';
    END IF;
    IF NEW.previous_state IS DISTINCT FROM t.current_state THEN
        RAISE EXCEPTION 'previous_state % does not match current state %', NEW.previous_state, t.current_state
            USING ERRCODE = 'serialization_failure';
    END IF;

    -- (b) State machine: the (state, event, target) triple must be drawn on the diagram.
    IF NEW.sequence_no = 1 THEN
        IF NEW.actor_role <> 'BORROWER' THEN
            RAISE EXCEPTION 'REQUEST_CREATED must be issued by the borrower' USING ERRCODE = 'insufficient_privilege';
        END IF;
    ELSE
        SELECT * INTO rule FROM allowed_transition
         WHERE from_state = NEW.previous_state AND event_type = NEW.event_type AND to_state = NEW.new_state;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'invalid transition: % --%--> %', NEW.previous_state, NEW.event_type, NEW.new_state
                USING ERRCODE = 'check_violation';
        END IF;
        IF NOT (NEW.actor_role = ANY (rule.allowed_roles)) THEN
            RAISE EXCEPTION 'role % may not issue % in state %', NEW.actor_role, NEW.event_type, NEW.previous_state
                USING ERRCODE = 'insufficient_privilege';
        END IF;
    END IF;

    -- (c) Authorisation: the actor really holds the claimed role in this transaction.
    IF NEW.actor_role IN ('BORROWER', 'LENDER') THEN
        IF NEW.actor_user_id <> (CASE NEW.actor_role WHEN 'BORROWER' THEN t.borrower_id ELSE t.lender_id END) THEN
            RAISE EXCEPTION 'actor is not the % of this transaction', lower(NEW.actor_role::text)
                USING ERRCODE = 'insufficient_privilege';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM app_user WHERE id = NEW.actor_user_id AND status = 'ACTIVE') THEN
            RAISE EXCEPTION 'actor account is not active' USING ERRCODE = 'insufficient_privilege';
        END IF;
    ELSIF NEW.actor_role IN ('MODERATOR', 'ADMIN') THEN
        IF NEW.actor_user_id IN (t.borrower_id, t.lender_id) THEN
            RAISE EXCEPTION 'a party cannot moderate its own transaction (DD-16)' USING ERRCODE = 'insufficient_privilege';
        END IF;
        IF NEW.actor_role = 'MODERATOR' AND NOT EXISTS (
               SELECT 1 FROM membership m JOIN app_user u ON u.id = m.user_id
                WHERE m.user_id = NEW.actor_user_id AND m.community_id = i.community_id
                  AND m.role = 'MODERATOR' AND m.status = 'APPROVED' AND u.status = 'ACTIVE') THEN
            RAISE EXCEPTION 'actor is not an active moderator of this item''s community'
                USING ERRCODE = 'insufficient_privilege';
        END IF;
        IF NEW.actor_role = 'ADMIN' AND NOT EXISTS (
               SELECT 1 FROM app_user WHERE id = NEW.actor_user_id AND platform_role = 'ADMIN' AND status = 'ACTIVE') THEN
            RAISE EXCEPTION 'actor is not an active admin' USING ERRCODE = 'insufficient_privilege';
        END IF;
        IF NEW.event_type IN ('MODERATOR_CLEARED', 'MODERATOR_RESTRICTED', 'DISPUTE_ESCALATED', 'DISPUTE_RESOLVED')
           AND coalesce(btrim(NEW.payload ->> 'reason'), '') = '' THEN
            RAISE EXCEPTION '% requires a recorded reason (DD-16)', NEW.event_type USING ERRCODE = 'check_violation';
        END IF;
    END IF;

    -- (d) Event-specific guards that the database can check.
    CASE NEW.event_type
    WHEN 'LOCALITY_CHECKED' THEN                                     -- T02 / T03
        elig := locality_eligibility(t.borrower_id, i.community_id);
        IF (NEW.payload ->> 'result') IS DISTINCT FROM elig::text THEN
            RAISE EXCEPTION 'LOCALITY_CHECKED result must be % (computed from stored membership evidence)', elig
                USING ERRCODE = 'check_violation';
        END IF;
        IF (elig = 'INELIGIBLE') <> (NEW.new_state = 'INELIGIBLE') THEN
            RAISE EXCEPTION 'locality result % cannot lead to %', elig, NEW.new_state USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'ASSURANCE_GENERATED' THEN                                  -- T04 / T05
        SELECT * INTO a FROM assurance_result
         WHERE id = (NEW.evidence ->> 'assurance_result_id')::uuid AND transaction_id = t.id;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'ASSURANCE_GENERATED must reference an assurance_result of this transaction'
                USING ERRCODE = 'check_violation';
        END IF;
        IF a.requires_moderator <> (NEW.new_state = 'MODERATOR_REVIEW') THEN
            RAISE EXCEPTION 'requiresModerator = % does not allow target %', a.requires_moderator, NEW.new_state
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'HANDOVER_RECORDED', 'RETURN_INITIATED', 'RETURN_CONFIRMED' THEN   -- T16, T25, T26
        SELECT EXISTS (SELECT 1 FROM condition_report c
                        WHERE c.id = (NEW.evidence ->> 'condition_report_id')::uuid
                          AND c.transaction_id = t.id
                          AND c.reported_by = NEW.actor_user_id
                          AND c.phase = CASE WHEN NEW.event_type = 'HANDOVER_RECORDED'
                                             THEN 'HANDOVER'::condition_phase ELSE 'RETURN'::condition_phase END)
          INTO report_ok;
        IF NOT report_ok THEN
            RAISE EXCEPTION '% needs the actor''s own % condition report as evidence', NEW.event_type,
                CASE WHEN NEW.event_type = 'HANDOVER_RECORDED' THEN 'HANDOVER' ELSE 'RETURN' END
                USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.event_type = 'HANDOVER_RECORDED' AND i.deposit_amount > 0
           AND coalesce((NEW.payload ->> 'deposit_received')::boolean, false) = false THEN
            RAISE EXCEPTION 'deposit of % must be recorded before handover (UC-B7 6a)', i.deposit_amount
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'EXTENSION_APPROVED' THEN                                   -- T23 / I05
        new_due := (NEW.payload ->> 'new_due')::timestamptz;
        IF new_due IS NULL OR new_due <= greatest(now(), upper(t.period)) THEN
            RAISE EXCEPTION 'EXTENSION_APPROVED needs payload.new_due later than now and the current due date'
                USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.previous_state = 'OVERDUE' AND NEW.new_state <> 'ON_LOAN' THEN
            RAISE EXCEPTION 'an approved extension moves an overdue loan back to ON_LOAN' USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'DISPUTE_OPENED' THEN                                       -- T19, T24, T27, T28
        IF NEW.actor_role = 'SYSTEM' AND coalesce(NEW.payload ->> 'reason', '') NOT IN
               ('NON_RETURN', 'HANDOVER_UNCONFIRMED', 'RETURN_UNCONFIRMED', 'PARTY_SUSPENDED') THEN
            RAISE EXCEPTION 'system-opened disputes need a system reason' USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.actor_role <> 'SYSTEM' AND coalesce(NEW.payload ->> 'reason', '') NOT IN
               ('CONDITION_MISMATCH', 'DAMAGE', 'NON_RETURN', 'NO_SHOW', 'OTHER') THEN
            RAISE EXCEPTION 'a party dispute needs a party reason' USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'DISPUTE_RESOLVED' THEN                                     -- T31 / T32
        IF (NEW.payload ->> 'resolution') IS DISTINCT FROM
           (CASE WHEN NEW.new_state = 'RESOLVED' THEN 'CLOSE' ELSE 'RESUME' END) THEN
            RAISE EXCEPTION 'payload.resolution must be CLOSE for RESOLVED and RESUME otherwise'
                USING ERRCODE = 'check_violation';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM dispute d WHERE d.transaction_id = t.id AND d.status IN ('OPEN', 'ESCALATED')
                          AND (d.response_deadline <= now()
                               OR (SELECT count(DISTINCT s.author_role) FROM dispute_statement s
                                    WHERE s.dispute_id = d.id) = 2)) THEN
            RAISE EXCEPTION 'both parties must be heard or the response deadline must pass first (X11)'
                USING ERRCODE = 'check_violation';
        END IF;
    WHEN 'DISPUTE_WITHDRAWN' THEN                                    -- T33
        IF NOT EXISTS (SELECT 1 FROM dispute WHERE transaction_id = t.id AND status IN ('OPEN', 'ESCALATED')
                          AND raised_by = NEW.actor_user_id) THEN
            RAISE EXCEPTION 'only the party who raised the dispute may withdraw it (X12)'
                USING ERRCODE = 'insufficient_privilege';
        END IF;
    ELSE
        NULL;
    END CASE;

    -- (e) Shallow history (H): leaving DISPUTED without closing must restore the phase it was opened from.
    IF is_disputed(NEW.previous_state) AND NOT is_disputed(NEW.new_state) AND NOT is_closed(NEW.new_state) THEN
        SELECT e.previous_state INTO opened_from FROM transaction_event e
         WHERE e.transaction_id = t.id AND e.event_type = 'DISPUTE_OPENED'
         ORDER BY e.sequence_no DESC LIMIT 1;
        IF in_progress_phase(opened_from) IS DISTINCT FROM in_progress_phase(NEW.new_state) THEN
            RAISE EXCEPTION 'history violation: dispute was opened in %, cannot resume into %',
                in_progress_phase(opened_from), NEW.new_state USING ERRCODE = 'check_violation';
        END IF;
        IF in_progress_phase(opened_from) = 'HANDOVER_PENDING' AND NEW.new_state <> 'AWAITING_HANDOVER' THEN
            RAISE EXCEPTION 'resuming HANDOVER_PENDING re-enters its default state AWAITING_HANDOVER'
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;

    -- (f) Hash chain per transaction (tamper evidence, R3).
    SELECT e.row_hash INTO NEW.prev_hash FROM transaction_event e
     WHERE e.transaction_id = t.id AND e.sequence_no = NEW.sequence_no - 1;
    NEW.row_hash := event_hash(NEW.prev_hash, NEW.transaction_id, NEW.sequence_no, NEW.event_type,
                               NEW.actor_user_id, NEW.actor_role, NEW.occurred_at, NEW.previous_state,
                               NEW.new_state, NEW.evidence, NEW.authorisation, NEW.payload);
    RETURN NEW;
END $$;
CREATE TRIGGER transaction_event_validate BEFORE INSERT ON transaction_event
    FOR EACH ROW EXECUTE FUNCTION event_validate();

-- 11.7 Apply the event to the projection (the only writer of borrow_transaction state, R1).
CREATE FUNCTION event_apply() RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER SET search_path = dm, pg_temp AS $$
BEGIN
    UPDATE borrow_transaction
       SET current_state = NEW.new_state,
           version       = NEW.sequence_no,
           last_event_at = NEW.occurred_at,
           closed_at     = CASE WHEN is_closed(NEW.new_state) THEN NEW.occurred_at END,
           handover_time = CASE WHEN NEW.event_type = 'LENDER_ACCEPTED' AND NEW.payload ? 'handover_time'
                                THEN (NEW.payload ->> 'handover_time')::timestamptz ELSE handover_time END,
           period        = CASE WHEN NEW.event_type IN ('EXTENSION_APPROVED', 'DISPUTE_RESOLVED') AND NEW.payload ? 'new_due'
                                THEN tstzrange(lower(period), (NEW.payload ->> 'new_due')::timestamptz) ELSE period END
     WHERE id = NEW.transaction_id;

    CASE NEW.event_type
    WHEN 'DISPUTE_OPENED' THEN
        INSERT INTO dispute (transaction_id, opened_event_id, raised_by, raised_by_role, reason, description,
                             response_deadline, opened_at)
        VALUES (NEW.transaction_id, NEW.event_id, NEW.actor_user_id, NEW.actor_role,
                (NEW.payload ->> 'reason')::dispute_reason, NEW.payload ->> 'description',
                coalesce((NEW.payload ->> 'response_deadline')::timestamptz, NEW.occurred_at + interval '48 hours'),
                NEW.occurred_at);
    WHEN 'DISPUTE_INFO_REQUESTED' THEN
        UPDATE dispute SET response_deadline = coalesce((NEW.payload ->> 'response_deadline')::timestamptz, response_deadline)
         WHERE transaction_id = NEW.transaction_id AND status IN ('OPEN', 'ESCALATED');
    WHEN 'DISPUTE_ESCALATED' THEN
        UPDATE dispute SET status = 'ESCALATED'
         WHERE transaction_id = NEW.transaction_id AND status = 'OPEN';
    WHEN 'DISPUTE_RESOLVED', 'DISPUTE_WITHDRAWN' THEN
        UPDATE dispute SET status = CASE WHEN NEW.event_type = 'DISPUTE_RESOLVED'
                                         THEN 'RESOLVED'::dispute_status ELSE 'WITHDRAWN'::dispute_status END,
                           closed_at = NEW.occurred_at, closing_event_id = NEW.event_id
         WHERE transaction_id = NEW.transaction_id AND status IN ('OPEN', 'ESCALATED');
    ELSE
        NULL;
    END CASE;
    RETURN NULL;
END $$;
CREATE TRIGGER transaction_event_apply AFTER INSERT ON transaction_event
    FOR EACH ROW EXECUTE FUNCTION event_apply();

-- 11.8 Integrity guards for evidence, reviews, statements and condition reports
CREATE FUNCTION evidence_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    e transaction_event%ROWTYPE;
    t borrow_transaction%ROWTYPE;
BEGIN
    IF TG_OP = 'UPDATE' THEN                     -- only the status may change (re-evaluation flags)
        IF to_jsonb(NEW) - 'status' - 'flagged_by_decision_id'
           IS DISTINCT FROM to_jsonb(OLD) - 'status' - 'flagged_by_decision_id' THEN
            RAISE EXCEPTION 'evidence_record facts are immutable; only status may change'
                USING ERRCODE = 'insufficient_privilege';
        END IF;
        RETURN NEW;
    END IF;
    SELECT * INTO e FROM transaction_event WHERE event_id = NEW.source_event_id;
    IF NOT ((e.event_type = 'RETURN_CONFIRMED' AND e.new_state = 'COMPLETED')
         OR (e.event_type = 'DISPUTE_RESOLVED' AND e.new_state = 'RESOLVED')) THEN
        RAISE EXCEPTION 'evidence may only come from a verified closing event (overview 5.12)'
            USING ERRCODE = 'check_violation';
    END IF;
    SELECT * INTO t FROM borrow_transaction WHERE id = e.transaction_id;
    IF NEW.subject_user_id <> (CASE NEW.subject_role WHEN 'BORROWER' THEN t.borrower_id ELSE t.lender_id END) THEN
        RAISE EXCEPTION 'evidence subject must be the % of the transaction', lower(NEW.subject_role::text)
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER evidence_record_guard BEFORE INSERT OR UPDATE ON evidence_record
    FOR EACH ROW EXECUTE FUNCTION evidence_guard();
CREATE TRIGGER evidence_record_no_delete BEFORE DELETE ON evidence_record
    FOR EACH ROW EXECUTE FUNCTION forbid_change();

CREATE FUNCTION review_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE t borrow_transaction%ROWTYPE;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF now() > OLD.edit_until THEN
            RAISE EXCEPTION 'review edit window has closed (UC-D1 1b)' USING ERRCODE = 'check_violation';
        END IF;
        IF to_jsonb(NEW) - 'ratings' - 'comment' IS DISTINCT FROM to_jsonb(OLD) - 'ratings' - 'comment' THEN
            RAISE EXCEPTION 'only ratings and comment can be edited' USING ERRCODE = 'insufficient_privilege';
        END IF;
        RETURN NEW;
    END IF;
    SELECT * INTO t FROM borrow_transaction WHERE id = NEW.transaction_id;
    IF t.current_state IS DISTINCT FROM 'COMPLETED' THEN
        RAISE EXCEPTION 'reviews are allowed only for COMPLETED transactions (UC-D1)' USING ERRCODE = 'check_violation';
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
    t       borrow_transaction%ROWTYPE;
    v_user  uuid;
    v_role  party_role;
BEGIN
    IF TG_TABLE_NAME = 'dispute_statement' THEN
        SELECT bt.* INTO t FROM dispute d JOIN borrow_transaction bt ON bt.id = d.transaction_id
         WHERE d.id = NEW.dispute_id AND d.status IN ('OPEN', 'ESCALATED');
        IF NOT FOUND THEN
            RAISE EXCEPTION 'statements can only be added to a live dispute' USING ERRCODE = 'check_violation';
        END IF;
        v_user := NEW.author_id;   v_role := NEW.author_role;
    ELSE
        SELECT * INTO t FROM borrow_transaction WHERE id = NEW.transaction_id;
        v_user := NEW.reported_by; v_role := NEW.reporter_role;
    END IF;
    IF v_user <> (CASE v_role WHEN 'BORROWER' THEN t.borrower_id ELSE t.lender_id END) THEN
        RAISE EXCEPTION 'author must be the % of the transaction', lower(v_role::text) USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER dispute_statement_party BEFORE INSERT ON dispute_statement FOR EACH ROW EXECUTE FUNCTION party_guard();
CREATE TRIGGER condition_report_party  BEFORE INSERT ON condition_report  FOR EACH ROW EXECUTE FUNCTION party_guard();

-- 11.9 Audit log hash chain (global order; advisory lock keeps the chain linear)
CREATE FUNCTION audit_chain() RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER SET search_path = dm, pg_temp AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtext('dm.audit_log'));
    NEW.occurred_at := clock_timestamp();
    SELECT row_hash INTO NEW.prev_hash FROM audit_log ORDER BY id DESC LIMIT 1;
    NEW.row_hash := audit_hash(NEW.prev_hash, NEW);
    RETURN NEW;
END $$;
CREATE TRIGGER audit_log_chain BEFORE INSERT ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_chain();

-- 11.10 Replay and verification (used by tests and by the Phase-2 pseudocode)
-- Rebuilds the current state from the event log only, checking every link.
CREATE FUNCTION replay_state(p_txn uuid) RETURNS txn_state LANGUAGE plpgsql STABLE AS $$
DECLARE
    e     transaction_event%ROWTYPE;
    state txn_state := NULL;
    n     integer := 0;
BEGIN
    FOR e IN SELECT * FROM transaction_event WHERE transaction_id = p_txn ORDER BY sequence_no LOOP
        n := n + 1;
        IF e.sequence_no <> n THEN
            RAISE EXCEPTION 'replay: gap before sequence_no %', e.sequence_no;
        END IF;
        IF e.previous_state IS DISTINCT FROM state THEN
            RAISE EXCEPTION 'replay: event % expects state % but replay is in %', e.sequence_no, e.previous_state, state;
        END IF;
        IF n > 1 AND NOT EXISTS (SELECT 1 FROM allowed_transition
                                  WHERE from_state = e.previous_state AND event_type = e.event_type
                                    AND to_state = e.new_state) THEN
            RAISE EXCEPTION 'replay: event % is not an allowed transition', e.sequence_no;
        END IF;
        state := e.new_state;
    END LOOP;
    RETURN state;
END $$;

-- Recomputes the hash chain of one transaction; returns the broken links (none = intact).
CREATE FUNCTION verify_event_chain(p_txn uuid)
RETURNS TABLE (sequence_no integer, problem text) LANGUAGE plpgsql STABLE AS $$
DECLARE
    e    transaction_event%ROWTYPE;
    prev bytea := NULL;
BEGIN
    FOR e IN SELECT * FROM transaction_event te WHERE te.transaction_id = p_txn ORDER BY te.sequence_no LOOP
        IF e.prev_hash IS DISTINCT FROM prev THEN
            sequence_no := e.sequence_no; problem := 'prev_hash does not match previous row'; RETURN NEXT;
        END IF;
        IF e.row_hash <> event_hash(e.prev_hash, e.transaction_id, e.sequence_no, e.event_type, e.actor_user_id,
                                    e.actor_role, e.occurred_at, e.previous_state, e.new_state, e.evidence,
                                    e.authorisation, e.payload) THEN
            sequence_no := e.sequence_no; problem := 'row content changed after it was written'; RETURN NEXT;
        END IF;
        prev := e.row_hash;
    END LOOP;
END $$;

-- =============================================================================
-- 12. Views
-- =============================================================================
-- Moderator queue (UC-D6, I4): pre-acceptance reviews and live disputes, per community.
CREATE VIEW v_moderation_queue AS
SELECT 'PRE_ACCEPTANCE_REVIEW'::text AS case_kind, t.id AS transaction_id, NULL::uuid AS dispute_id,
       i.community_id, t.current_state, t.last_event_at AS waiting_since
  FROM borrow_transaction t JOIN item i ON i.id = t.item_id
 WHERE t.current_state = 'MODERATOR_REVIEW'
UNION ALL
SELECT 'DISPUTE', d.transaction_id, d.id, i.community_id, t.current_state, d.opened_at
  FROM dispute d JOIN borrow_transaction t ON t.id = d.transaction_id JOIN item i ON i.id = t.item_id
 WHERE d.status IN ('OPEN', 'ESCALATED');

-- Item calendar (UC-B2): firm bookings and lender blocks. Pending requests are tentative and not listed.
CREATE VIEW v_item_calendar AS
SELECT item_id, period, 'BOOKED'::text AS kind, id AS source_id
  FROM borrow_transaction WHERE current_state IS NOT NULL AND holds_dates(current_state)
UNION ALL
SELECT item_id, period, 'BLOCKED', id FROM availability_block;

-- Audit trail (UC-I6): lifecycle events and other audited actions in one place.
CREATE VIEW v_audit_trail AS
SELECT e.occurred_at, e.actor_user_id, e.actor_role::text AS actor_role, e.event_type::text AS action,
       'borrow_transaction'::text AS target_type, e.transaction_id::text AS target_id,
       to_jsonb(e.previous_state) AS previous_value, to_jsonb(e.new_state) AS new_value,
       e.evidence, e.authorisation, 'SUCCESS'::text AS outcome
  FROM transaction_event e
UNION ALL
SELECT a.occurred_at, a.actor_user_id, a.actor_role::text, a.action, a.target_type, a.target_id,
       a.previous_value, a.new_value, a.evidence, a.authorisation, a.outcome
  FROM audit_log a;

-- =============================================================================
-- 13. Reference data: the state machine (State_Machine_Design.md v1.1, section 6)
-- =============================================================================
INSERT INTO allowed_transition (from_state, event_type, to_state, allowed_roles, ref)
SELECT f::txn_state, ev::txn_event_type, t::txn_state, r::actor_role[], ref
FROM (VALUES
    -- PENDING
    ('REQUESTED',        'LOCALITY_CHECKED',      'INELIGIBLE',        '{SYSTEM}',                 'T02'),
    ('REQUESTED',        'LOCALITY_CHECKED',      'ASSESSING',         '{SYSTEM}',                 'T03'),
    ('ASSESSING',        'ASSURANCE_GENERATED',   'AWAITING_LENDER',   '{SYSTEM}',                 'T04'),
    ('ASSESSING',        'ASSURANCE_GENERATED',   'MODERATOR_REVIEW',  '{SYSTEM}',                 'T05'),
    ('ASSESSING',        'ASSURANCE_FAILED',      'MODERATOR_REVIEW',  '{SYSTEM}',                 'T06'),
    ('MODERATOR_REVIEW', 'EVIDENCE_SUBMITTED',    'ASSESSING',         '{BORROWER,LENDER}',        'T07'),
    ('MODERATOR_REVIEW', 'MODERATOR_CLEARED',     'AWAITING_LENDER',   '{MODERATOR,ADMIN}',        'T08'),
    ('MODERATOR_REVIEW', 'MODERATOR_RESTRICTED',  'DECLINED',          '{MODERATOR,ADMIN}',        'T09'),
    ('AWAITING_LENDER',  'LENDER_ACCEPTED',       'AWAITING_HANDOVER', '{LENDER}',                 'T10'),
    ('AWAITING_LENDER',  'LENDER_DECLINED',       'DECLINED',          '{LENDER}',                 'T11'),
    ('AWAITING_LENDER',  'REQUEST_EXPIRED',       'EXPIRED',           '{SYSTEM}',                 'T12/T14'),
    ('REQUESTED',        'REQUEST_AUTO_DECLINED', 'DECLINED',          '{SYSTEM}',                 'T13'),
    ('ASSESSING',        'REQUEST_AUTO_DECLINED', 'DECLINED',          '{SYSTEM}',                 'T13'),
    ('MODERATOR_REVIEW', 'REQUEST_AUTO_DECLINED', 'DECLINED',          '{SYSTEM}',                 'T13'),
    ('AWAITING_LENDER',  'REQUEST_AUTO_DECLINED', 'DECLINED',          '{SYSTEM}',                 'T13'),
    ('REQUESTED',        'REQUEST_EXPIRED',       'EXPIRED',           '{SYSTEM}',                 'T14'),
    ('ASSESSING',        'REQUEST_EXPIRED',       'EXPIRED',           '{SYSTEM}',                 'T14'),
    ('MODERATOR_REVIEW', 'REQUEST_EXPIRED',       'EXPIRED',           '{SYSTEM}',                 'T14'),
    ('REQUESTED',        'TRANSACTION_CANCELLED', 'CANCELLED',         '{BORROWER,SYSTEM}',        'T15'),
    ('ASSESSING',        'TRANSACTION_CANCELLED', 'CANCELLED',         '{BORROWER,SYSTEM}',        'T15'),
    ('MODERATOR_REVIEW', 'TRANSACTION_CANCELLED', 'CANCELLED',         '{BORROWER,SYSTEM}',        'T15'),
    ('AWAITING_LENDER',  'TRANSACTION_CANCELLED', 'CANCELLED',         '{BORROWER,SYSTEM}',        'T15'),
    ('MODERATOR_REVIEW', 'EVIDENCE_REQUESTED',    'MODERATOR_REVIEW',  '{MODERATOR,ADMIN}',        'I01'),
    -- HANDOVER_PENDING
    ('AWAITING_HANDOVER','HANDOVER_RECORDED',     'AWAITING_RECEIPT',  '{LENDER}',                 'T16'),
    ('AWAITING_RECEIPT', 'HANDOVER_CONFIRMED',    'ON_LOAN',           '{BORROWER}',               'T17/T21'),
    ('AWAITING_RECEIPT', 'HANDOVER_CONFIRMED',    'OVERDUE',           '{BORROWER}',               'T17/T21'),
    ('AWAITING_HANDOVER','HANDOVER_NO_SHOW',      'NO_SHOW',           '{SYSTEM}',                 'T18'),
    ('AWAITING_HANDOVER','TRANSACTION_CANCELLED', 'CANCELLED',         '{BORROWER,LENDER}',        'T20'),
    ('AWAITING_RECEIPT', 'TRANSACTION_CANCELLED', 'CANCELLED',         '{BORROWER,LENDER}',        'T20'),
    ('AWAITING_HANDOVER','REMINDER_SENT',         'AWAITING_HANDOVER', '{SYSTEM}',                 'I02'),
    ('AWAITING_RECEIPT', 'CONDITION_NOTE_ADDED',  'AWAITING_RECEIPT',  '{BORROWER}',               'I03'),
    -- ACTIVE
    ('ON_LOAN',          'LOAN_OVERDUE',          'OVERDUE',           '{SYSTEM}',                 'T22'),
    ('OVERDUE',          'EXTENSION_APPROVED',    'ON_LOAN',           '{LENDER}',                 'T23'),
    ('ON_LOAN',          'RETURN_INITIATED',      'RETURN_PENDING',    '{BORROWER}',               'T25'),
    ('OVERDUE',          'RETURN_INITIATED',      'RETURN_PENDING',    '{BORROWER}',               'T25'),
    ('ON_LOAN',          'EXTENSION_REQUESTED',   'ON_LOAN',           '{BORROWER}',               'I04'),
    ('OVERDUE',          'EXTENSION_REQUESTED',   'OVERDUE',           '{BORROWER}',               'I04'),
    ('ON_LOAN',          'EXTENSION_APPROVED',    'ON_LOAN',           '{LENDER}',                 'I05'),
    ('ON_LOAN',          'EXTENSION_DECLINED',    'ON_LOAN',           '{LENDER}',                 'I06'),
    ('OVERDUE',          'EXTENSION_DECLINED',    'OVERDUE',           '{LENDER}',                 'I06'),
    ('ON_LOAN',          'REMINDER_SENT',         'ON_LOAN',           '{SYSTEM}',                 'I07'),
    ('OVERDUE',          'REMINDER_SENT',         'OVERDUE',           '{SYSTEM}',                 'I08'),
    -- RETURN_PENDING
    ('RETURN_PENDING',   'RETURN_CONFIRMED',      'COMPLETED',         '{LENDER}',                 'T26'),
    ('RETURN_PENDING',   'REMINDER_SENT',         'RETURN_PENDING',    '{SYSTEM}',                 'I09'),
    -- into DISPUTED (system triggers T19/T24/T27 and the border transition T28)
    ('AWAITING_HANDOVER','DISPUTE_OPENED',        'DISPUTE_OPEN',      '{BORROWER,LENDER,SYSTEM}', 'T28'),
    ('AWAITING_RECEIPT', 'DISPUTE_OPENED',        'DISPUTE_OPEN',      '{BORROWER,LENDER,SYSTEM}', 'T19/T28'),
    ('ON_LOAN',          'DISPUTE_OPENED',        'DISPUTE_OPEN',      '{BORROWER,LENDER,SYSTEM}', 'T28'),
    ('OVERDUE',          'DISPUTE_OPENED',        'DISPUTE_OPEN',      '{BORROWER,LENDER,SYSTEM}', 'T24/T28'),
    ('RETURN_PENDING',   'DISPUTE_OPENED',        'DISPUTE_OPEN',      '{BORROWER,LENDER,SYSTEM}', 'T27/T28'),
    -- inside DISPUTED
    ('DISPUTE_OPEN',     'DISPUTE_ESCALATED',     'DISPUTE_ESCALATED', '{MODERATOR,SYSTEM}',       'T30'),
    ('DISPUTE_OPEN',     'DISPUTE_RESPONSE_ADDED','DISPUTE_OPEN',      '{BORROWER,LENDER}',        'I10'),
    ('DISPUTE_ESCALATED','DISPUTE_RESPONSE_ADDED','DISPUTE_ESCALATED', '{BORROWER,LENDER}',        'I10'),
    ('DISPUTE_OPEN',     'DISPUTE_INFO_REQUESTED','DISPUTE_OPEN',      '{MODERATOR,ADMIN}',        'I11'),
    ('DISPUTE_ESCALATED','DISPUTE_INFO_REQUESTED','DISPUTE_ESCALATED', '{ADMIN}',                  'I11'),
    ('DISPUTE_OPEN',     'DISPUTE_DEADLINE_ELAPSED','DISPUTE_OPEN',    '{SYSTEM}',                 'I12'),
    ('DISPUTE_ESCALATED','DISPUTE_DEADLINE_ELAPSED','DISPUTE_ESCALATED','{SYSTEM}',                'I12'),
    -- out of DISPUTED: close (T31), resume via H (T32), withdraw via H (T33)
    ('DISPUTE_OPEN',     'DISPUTE_RESOLVED',      'RESOLVED',          '{MODERATOR,ADMIN}',        'T31'),
    ('DISPUTE_ESCALATED','DISPUTE_RESOLVED',      'RESOLVED',          '{ADMIN}',                  'T31'),
    ('DISPUTE_OPEN',     'DISPUTE_RESOLVED',      'AWAITING_HANDOVER', '{MODERATOR,ADMIN}',        'T32'),
    ('DISPUTE_OPEN',     'DISPUTE_RESOLVED',      'ON_LOAN',           '{MODERATOR,ADMIN}',        'T32'),
    ('DISPUTE_OPEN',     'DISPUTE_RESOLVED',      'OVERDUE',           '{MODERATOR,ADMIN}',        'T32'),
    ('DISPUTE_OPEN',     'DISPUTE_RESOLVED',      'RETURN_PENDING',    '{MODERATOR,ADMIN}',        'T32'),
    ('DISPUTE_ESCALATED','DISPUTE_RESOLVED',      'AWAITING_HANDOVER', '{ADMIN}',                  'T32'),
    ('DISPUTE_ESCALATED','DISPUTE_RESOLVED',      'ON_LOAN',           '{ADMIN}',                  'T32'),
    ('DISPUTE_ESCALATED','DISPUTE_RESOLVED',      'OVERDUE',           '{ADMIN}',                  'T32'),
    ('DISPUTE_ESCALATED','DISPUTE_RESOLVED',      'RETURN_PENDING',    '{ADMIN}',                  'T32'),
    ('DISPUTE_OPEN',     'DISPUTE_WITHDRAWN',     'AWAITING_HANDOVER', '{BORROWER,LENDER}',        'T33'),
    ('DISPUTE_OPEN',     'DISPUTE_WITHDRAWN',     'ON_LOAN',           '{BORROWER,LENDER}',        'T33'),
    ('DISPUTE_OPEN',     'DISPUTE_WITHDRAWN',     'OVERDUE',           '{BORROWER,LENDER}',        'T33'),
    ('DISPUTE_OPEN',     'DISPUTE_WITHDRAWN',     'RETURN_PENDING',    '{BORROWER,LENDER}',        'T33'),
    ('DISPUTE_ESCALATED','DISPUTE_WITHDRAWN',     'AWAITING_HANDOVER', '{BORROWER,LENDER}',        'T33'),
    ('DISPUTE_ESCALATED','DISPUTE_WITHDRAWN',     'ON_LOAN',           '{BORROWER,LENDER}',        'T33'),
    ('DISPUTE_ESCALATED','DISPUTE_WITHDRAWN',     'OVERDUE',           '{BORROWER,LENDER}',        'T33'),
    ('DISPUTE_ESCALATED','DISPUTE_WITHDRAWN',     'RETURN_PENDING',    '{BORROWER,LENDER}',        'T33')
) AS v (f, ev, t, r, ref);

-- =============================================================================
-- 14. Privileges: the application role cannot rewrite history or the projection
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
-- append-only tables: insert only
GRANT INSERT ON transaction_event, audit_log, moderator_decision, assurance_result, condition_report,
                dispute_statement, request, locality_verification, evidence_record, review, attachment TO dm_app;
-- the projection: the app may create the row, never change its state
GRANT INSERT (id, item_id, borrower_id, lender_id, period, handover_time) ON borrow_transaction TO dm_app;
-- ordinary mutable data
GRANT INSERT, UPDATE ON app_user, community, membership, item, category, invitation, trust_edge TO dm_app;
GRANT INSERT, DELETE ON user_block, availability_block TO dm_app;
GRANT DELETE ON attachment, trust_edge TO dm_app;
GRANT UPDATE (status, flagged_by_decision_id) ON evidence_record TO dm_app;
GRANT UPDATE (ratings, comment) ON review TO dm_app;
GRANT UPDATE (assigned_to) ON dispute TO dm_app;

COMMIT;
