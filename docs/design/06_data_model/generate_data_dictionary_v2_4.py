"""Generates Data_Dictionary_v2_4.md (iteration 2, DA-09, Student 1) from the live catalogue plus the meanings below.

    set DM_TEST_DSN=postgresql://...     (schema "dm" with schema.sql v2.3 and migration_0002_schema_v2_4.sql loaded)
    python generate_data_dictionary_v2_4.py

The meanings of every v2.3 column are reused from the iteration 1 generator; this file adds the tables and columns of
migration 0002. As before, it fails if a column has no meaning or a meaning names a column that does not exist, so the
dictionary and the schema cannot drift apart.
"""
import importlib.util
import os
import sys

import psycopg2

HERE = os.path.dirname(os.path.abspath(__file__))
IT1 = os.path.join(HERE, "generate_data_dictionary.py")
ENGINE_CONFIG = os.path.join(HERE, "..", "11_assurance_engine", "Assurance_Engine_Config_v1.4.0.json")

_spec = importlib.util.spec_from_file_location("dd_iteration1", IT1)
dd1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dd1)
dd1.ENGINE_CONFIG = ENGINE_CONFIG                    # config rows are read from the 1.4.0 draft

TABLES = dict(dd1.TABLES)
TABLES["allowed_transition"] = (None, "Module 3", "The lifecycle v3 transition table as reference data (39 rows).")
TABLES["item"] = ("Item", "Module 3", "An item offered for borrowing; lenders create listings from iteration 2 (FR-B-01).")
TABLES["attachment"] = (None, "Module 3 / 9", "Metadata of a photo or document of a listing, condition report or case "
                        "statement; the file is stored outside the database (ADR-0014).")
TABLES.update({
    "membership_decision": ("MembershipDecision", "Module 1", "A moderator's decision on a membership request; append-only, "
                            "so a reversal keeps both decisions (UC-A4, FR-A-10, FR-A-11)."),
    "item_embedding": ("ItemEmbedding", "Module 4", "The vector of an item's text for meaning-based search (ADR-0016)."),
    "search_query": ("SearchQuery", "Module 4 / 10", "One search a member ran, as served (FR-S-05). No location."),
    "search_impression": (None, "Module 4 / 10", "One result shown for a search, in rank order, with its score parts."),
    "search_click": (None, "Module 4 / 10", "A shown result the member opened; ignored results are impressions without one."),
    "notification": ("Notification", "Module 7", "An in-app notification for one member (ADR-0013)."),
    "job_run": (None, "Scheduler", "One run of a scheduled job for one due item; the unique key makes reruns harmless (ADR-0012)."),
})

NEW = {  # (table, column): (meaning, source)
    ("app_user", "terms_accepted_at"): ("When the member accepted the terms and privacy notice at registration", "FR-A-01"),
    ("community", "join_policy"): ("MODERATED (default) or OPEN; OPEN still records a locality outcome", "UC-A3 4a, I-10"),
    ("item", "condition"): ("NEW, GOOD, FAIR or WORN, chosen by the lender; needed to publish", "FR-B-01"),
    ("item", "usage_terms"): ("Restrictions and usage instructions written by the lender", "FR-B-01"),
    ("item", "handover_method"): ("How the handover happens, in the lender's words (no address)", "FR-B-01, NFR-PR-01"),
    ("item", "search_terms"): ("Other names people search for, e.g. Roman Urdu (\"seerhi\" for ladder)", "FR-S-01, NFR-U-05"),
    ("item", "expires_at"): ("When the listing expires; the listing-expiry job sets it EXPIRED", "FR-B-18"),
    ("item", "updated_at"): ("Last change to the listing; drives freshness in ranking and re-embedding", "FR-S-01"),
    ("item", "search_tsv"): ("Generated full-text vector of title, description and search terms ('simple', no stemming)",
                             "FR-S-02, FR-S-03, ADR-0016"),
    ("attachment", "item_id"): ("Listing the photo belongs to; exactly one of item_id and transaction_id is set", "FR-B-01, ADR-0014"),
    ("membership_decision", "id"): ("Identifier of the decision", "—"),
    ("membership_decision", "membership_id"): ("Membership request decided", "FR-A-10"),
    ("membership_decision", "decided_by"): ("Moderator of the community or admin; never the applicant", "FR-A-10, NFR-S-03"),
    ("membership_decision", "kind"): ("APPROVED, REJECTED, INFO_REQUESTED or REVERSED", "UC-A4"),
    ("membership_decision", "reason"): ("Mandatory reason shown to the applicant", "FR-A-10"),
    ("membership_decision", "reverses_decision_id"): ("Earlier decision a reversal undoes; both stay", "FR-A-11"),
    ("membership_decision", "decided_at"): ("When the decision was recorded", "—"),
    ("item_embedding", "item_id"): ("Item the vector describes", "FR-S-01"),
    ("item_embedding", "model"): ("Embedding model name and version", "ADR-0016"),
    ("item_embedding", "content_sha256"): ("Hash of the text that was embedded; a different hash means re-embed", "FR-B-03"),
    ("item_embedding", "embedding"): ("The vector (384 dimensions, provisional until the model is chosen)", "ADR-0016"),
    ("item_embedding", "created_at"): ("When the vector was computed", "—"),
    ("search_query", "id"): ("Identifier of the search", "—"),
    ("search_query", "user_id"): ("Member who searched", "FR-S-05"),
    ("search_query", "community_id"): ("Community searched; the eligibility filter", "FR-S-01, I-5"),
    ("search_query", "query_text"): ("What the member typed (1–200 characters)", "FR-S-05"),
    ("search_query", "filters"): ("Filters and sort chosen; may not contain location keys", "FR-S-03, NFR-PR-01"),
    ("search_query", "mode"): ("HYBRID, or KEYWORD_ONLY when the model or index was down", "FR-S-02"),
    ("search_query", "config_version"): ("Ranking configuration used", "NFR-D-01"),
    ("search_query", "result_count"): ("Number of results returned", "FR-S-05"),
    ("search_query", "latency_ms"): ("Time to answer, for NFR-P-01 and P-02", "NFR-P-01, NFR-P-02"),
    ("search_query", "created_at"): ("When the search ran", "—"),
    ("search_impression", "query_id"): ("Search the result belongs to", "FR-S-05"),
    ("search_impression", "rank"): ("Position shown, 1 = first", "FR-S-05, NFR-Q-05"),
    ("search_impression", "item_id"): ("Item shown", "FR-S-05"),
    ("search_impression", "score_parts"): ("Feature values behind the rank; also the source of the reason line", "FR-S-01"),
    ("search_click", "id"): ("Identifier of the click", "—"),
    ("search_click", "query_id"): ("Search the click belongs to", "FR-S-05"),
    ("search_click", "item_id"): ("Result opened; must have been shown in that search", "FR-S-05"),
    ("search_click", "clicked_at"): ("When the result was opened", "—"),
    ("search_click", "request_transaction_id"): ("Borrowing request that followed, if any", "Overview §4 Tier 3"),
    ("notification", "id"): ("Identifier of the notification", "—"),
    ("notification", "user_id"): ("Member who receives it", "FR-C-02"),
    ("notification", "type"): ("Kind, e.g. request_assessed, handover_reminder, dispute_opened", "FR-C-02"),
    ("notification", "payload"): ("Data the screen needs (ids, dates); no location", "FR-C-02, NFR-PR-01"),
    ("notification", "dedupe_key"): ("Unique per member: the same reminder is never sent twice", "FR-B-18, FR-C-02"),
    ("notification", "created_at"): ("When it was created", "—"),
    ("notification", "read_at"): ("When the member read it; null = unread", "FR-C-02"),
    ("job_run", "id"): ("Identifier of the run", "—"),
    ("job_run", "job_name"): ("Job, e.g. request_expiry, no_show, return_reminder, overdue_escalation", "FR-B-18"),
    ("job_run", "due_key"): ("What the run handled, e.g. a transaction id and step; unique with job_name", "NFR-R-05"),
    ("job_run", "started_at"): ("When the run started", "FR-B-18"),
    ("job_run", "finished_at"): ("When it finished; null while running", "FR-B-18"),
    ("job_run", "status"): ("RUNNING, SUCCEEDED or FAILED", "FR-B-18"),
    ("job_run", "attempts"): ("Tries so far (1–10); failures are retried", "FR-B-18"),
    ("job_run", "error"): ("Error text of a failed run", "FR-B-18"),
}
CHANGED = {  # existing columns whose meaning v2.4 extends (no type change)
    ("moderator_decision", "resolved_outcome"): ("Dispute result, recorded as evidence; v2.4: key `possession` "
                                                 "(NOT_HANDED_OVER, WITH_BORROWER, RETURNED or LOST) is required on a "
                                                 "DISPUTE_RESOLVED decision and decides the next state", "FR-B-15, FR-T-11, ADR-0009"),
}
M = {**dd1.M, **NEW, **CHANGED}


def config_rows():
    rows = dd1.config_rows()
    rows = [r for r in rows if not r[0].startswith("response window, handover grace")]
    cfg = dd1._cfg()
    sch, rk = cfg["scheduler_b13"], cfg["ranking_alg5"]
    rows += [
        ("request_response_window_hours", f"{sch['request_response_window_hours']} h", "request expiry T15", "FR-B-10"),
        ("handover_grace_hours", f"{sch['handover_grace_hours']} h", "no-show T19", "FR-B-12"),
        ("return_reminder_before_due_hours", f"{sch['return_reminder_before_due_hours']} h", "return reminder I02", "FR-B-14"),
        ("overdue_limit_hours", f"{sch['overdue_limit_hours']} h after {sch['min_reminders_before_escalation']} reminders",
         "overdue escalation T24", "FR-B-14"),
        ("dispute_window_days", f"{sch['dispute_window_days']} days", "raise dispute", "FR-B-16"),
        ("party_response_deadline_hours", f"{sch['party_response_deadline_hours']} h", "dispute response", "FR-B-17"),
        ("run_interval_minutes", f"{sch['run_interval_minutes']} min", "scheduler trigger", "ADR-0012"),
        ("ranking weights", ", ".join(f"{k} {v}" for k, v in rk["weights"].items() if k != "source"), "hybrid ranking",
         "FR-S-01, Overview §4"),
        ("relevance mix", f"semantic {rk['retrieval']['relevance_mix']['semantic']}, keyword "
         f"{rk['retrieval']['relevance_mix']['keyword']}", "hybrid ranking", "FR-S-01"),
        ("pair_repeat_discount", f"{cfg['trust_estimation_alg1']['pair_repeat_discount']['factor']} per repeat in "
         f"{cfg['trust_estimation_alg1']['pair_repeat_discount']['window_days']} days", "trivial-exchange guard", "DA-15"),
    ]
    return rows


def main():
    conn = psycopg2.connect(os.environ["DM_TEST_DSN"])
    with conn, conn.cursor() as cur:
        cur.execute("""SELECT c.table_name, c.column_name, c.is_nullable = 'YES',
                              CASE WHEN c.data_type = 'USER-DEFINED' THEN c.udt_name
                                   WHEN c.data_type = 'ARRAY' THEN substr(c.udt_name, 2) || '[]'
                                   WHEN c.data_type = 'timestamp with time zone' THEN 'timestamptz'
                                   WHEN c.data_type = 'numeric' THEN 'numeric(' || c.numeric_precision || ',' || c.numeric_scale || ')'
                                   ELSE c.data_type END
                       FROM information_schema.columns c JOIN information_schema.tables t
                         ON t.table_schema = c.table_schema AND t.table_name = c.table_name AND t.table_type = 'BASE TABLE'
                      WHERE c.table_schema = 'dm' ORDER BY c.table_name, c.ordinal_position""")
        cols = cur.fetchall()
        cur.execute("""SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder) FROM pg_type t
                       JOIN pg_enum e ON e.enumtypid = t.oid JOIN pg_namespace n ON n.oid = t.typnamespace
                      WHERE n.nspname = 'dm' GROUP BY t.typname ORDER BY t.typname""")
        enums = cur.fetchall()
        cur.execute("""SELECT rel.relname, att.attname, con.contype FROM pg_constraint con
                       JOIN pg_class rel ON rel.oid = con.conrelid JOIN pg_namespace ns ON ns.oid = rel.relnamespace
                       JOIN unnest(con.conkey) k(n) ON true JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = k.n
                      WHERE ns.nspname = 'dm' AND con.contype IN ('p', 'f', 'u')""")
        keys = {}
        for t, c, k in cur.fetchall():
            keys.setdefault((t, c), set()).add({"p": "PK", "f": "FK", "u": "UQ"}[k])
    db = {(t, c) for t, c, *_ in cols}
    missing, extra = db - set(M), set(M) - db
    if missing or extra:
        sys.exit(f"data dictionary out of date. Missing meanings: {sorted(missing)}. Unknown columns: {sorted(extra)}")
    if set(t for t, _ in db) != set(TABLES):
        sys.exit(f"table descriptions out of date: {set(t for t, _ in db) ^ set(TABLES)}")

    new_tables = {t for t, c in NEW if (t, "id") in NEW or t in ("item_embedding", "search_impression")}
    L = ["# Digital Mohalla: Data Dictionary, schema v2.4 (iteration 2, DA-09)", "",
         "| Field | Value |", "|---|---|",
         "| Owner | Fatima Khursheed, Student 1 (Areeba Javed owns the meaning of the assessment, outcome and review fields) |",
         "| Version | 2.4 draft, 3 November 2026 (schema.sql v2.3 plus migration_0002_schema_v2_4.sql) |",
         "| Status | Generated from the live database: every column has exactly one entry. To be signed by all three with the "
         "schema change, then tag `schema-v2` |",
         "| Generated by | `06_data_model/generate_data_dictionary_v2_4.py` (do not edit by hand) |",
         "| Replaces | `../06_data_model/Data_Dictionary.md` v1.1 (kept as the iteration 1 baseline) |",
         "| GenAI | Drafted with Claude (Claude Code); to be disclosed on Form 13 and in the AI usage log |", "",
         f"{len(TABLES)} tables, {len(db)} columns. Key: PK primary key, FK foreign key, UQ unique; \"null\" = optional. "
         f"**New in v2.4** is marked: {len(new_tables)} tables and {sum(1 for k in NEW if k[0] not in new_tables)} columns "
         "on existing tables. The event catalogue (payload per event type) is in "
         "`../07_state_machines/State_Machine_Design_v3.md` and the iteration 1 `State_Machine_Design.md` §5.", ""]
    for t in TABLES:
        cls, mod, desc = TABLES[t]
        tag = " **(new in v2.4)**" if t in new_tables else ""
        L += [f"## `{t}`" + (f" — {cls}" if cls else "") + tag, "", f"*{mod}.* {desc}", "",
              "| Column | Type | Key | Null | Meaning | Source |", "|---|---|---|---|---|---|"]
        for tt, c, nullable, typ in cols:
            if tt != t:
                continue
            meaning, src = M[(t, c)]
            mark = " **(new)**" if (t, c) in NEW and t not in new_tables else ""
            L.append(f"| `{c}`{mark} | {typ} | {', '.join(sorted(keys.get((t, c), [])))} | {'null' if nullable else ''} | "
                     f"{meaning} | {src} |")
        L.append("")
    L += ["## Enumerated types", "", "| Type | Values |", "|---|---|"]
    for name, vals in enums:
        L.append(f"| `{name}` | {', '.join(vals)} |")
    L += ["", "## Configuration parameters (NFR-D-01)", "",
          "All values are initial and unvalidated; each assessment and each search stores the `config_version` it used. "
          "Values are read from `../11_assurance_engine/Assurance_Engine_Config_v1.4.0.json`.", "",
          "| Parameter | Initial value | Used by | Source |", "|---|---|---|---|"]
    config = config_rows()
    for row in config:
        L.append("| " + " | ".join(row) + " |")
    L += ["", "## Sign-off", "", "| Fatima Khursheed | Areeba Javed | Minahil Kashif | Date | Tag |", "|---|---|---|---|---|",
          "| | | | | `schema-v2` |"]
    with open(os.path.join(HERE, "Data_Dictionary_v2_4.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"Data_Dictionary_v2_4.md: {len(TABLES)} tables, {len(db)} columns, {len(enums)} enum types, {len(config)} parameters")


if __name__ == "__main__":
    main()
