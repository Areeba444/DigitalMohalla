-- =============================================================================
-- Digital Mohalla schema v2.4, part 1: extension and new types (Alembic revision 0002; build item F1, Fatima Khursheed)
-- Source: docs/design/06_data_model/migration_0002_schema_v2_4.sql (part 1), copied unchanged except:
--   the pgvector extension and item_embedding (with its grants) move to the A9 migration, because the
--   local PostgreSQL and CI's postgres:16 image have no pgvector yet (ADR-0016). Edit the design file first.
-- PostgreSQL cannot use an enum value in the transaction that adds it, so part 1 and part 2 are two
-- revisions; alembic/env.py commits after each revision (transaction_per_migration).
-- =============================================================================
SET search_path = dm, public;

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
