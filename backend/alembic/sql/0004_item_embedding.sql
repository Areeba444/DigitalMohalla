-- =============================================================================
-- Digital Mohalla schema v2.4, part 3: item embeddings for meaning-based search (Alembic revision 0004)
-- Source: docs/design/06_data_model/migration_0002_schema_v2_4.sql (the pgvector part that 0003 left
-- for build item A9, ADR-0016), copied unchanged except that it runs only where the server offers
-- the `vector` extension. Neon does; the local PostgreSQL 16 and CI's postgres:16 image may not.
-- Without it there is no item_embedding table, and search runs keyword-only (FR-S-02), which is the
-- designed fallback, not an error. Migration owner: Fatima Khursheed (plan rule: only Student 1
-- edits migrations); requested by Areeba Javed for A9.
-- =============================================================================
SET search_path = dm, public;

DO $mig$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector') THEN
        RAISE NOTICE 'pgvector is not available: item_embedding not created; search stays keyword-only';
        RETURN;
    END IF;
    CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;   -- item embeddings (ADR-0016)

    -- One embedding per item and model. Exact search over a few hundred rows needs no ANN index
    -- (ADR-0016), so eligibility filters run in the same query (issue I-5). Dimension 384 is the
    -- size of the small sentence-embedding models ADR-0016 compares.
    EXECUTE $ddl$
    CREATE TABLE item_embedding (
        item_id        uuid NOT NULL REFERENCES item (id),
        model          text NOT NULL CHECK (length(model) BETWEEN 1 AND 120),     -- model name and version
        content_sha256 bytea NOT NULL CHECK (octet_length(content_sha256) = 32), -- hash of the embedded text: stale when it differs
        embedding      public.vector(384) NOT NULL,
        created_at     timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (item_id, model)
    )
    $ddl$;

    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dm_app') THEN
        EXECUTE 'GRANT SELECT, INSERT ON item_embedding TO dm_app';
        EXECUTE 'GRANT UPDATE (embedding, content_sha256, created_at) ON item_embedding TO dm_app';
    END IF;
END
$mig$;
