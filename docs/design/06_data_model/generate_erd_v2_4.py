"""Builds er_diagram.drawio from the live database catalogue (iteration 2, DA-09 and DA-23, Student 1).

    set DM_TEST_DSN=postgresql://...      a database with schema.sql v2.3 and then migration_0002_schema_v2_4.sql loaded
    python generate_erd_v2_4.py                reads the catalogue of schema "dm" -> er_diagram.drawio

Same notation and checks as the iteration 1 generator (../06_data_model/generate_erd.py). Tables are
stacked per column in a fixed order instead of fixed y positions, because migration 0002 makes several tables taller.
Columns and tables added by migration 0002 are drawn in green with a "+" so the change since v2.3 is visible.

Tables, columns, types, nullability, keys and foreign keys are read from PostgreSQL, so the diagram
cannot disagree with schema.sql. Only the positions, the module grouping and the choice of which
foreign keys are drawn as lines (the rest are marked "-> table" in the row) are set here.
"""
import os
import sys

import psycopg2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

ROW, HEAD, GAP = 17, 30, 34
COLS = {"A": 40, "B": 420, "C": 820, "D": 1260, "E": 1700, "F": 2160}
WIDTH = {"A": 300, "B": 320, "C": 360, "D": 360, "E": 340, "F": 340}

# column -> tables top to bottom: (table, domain class, module colour key)
STACK = {
    "A": [("app_user", "User", "m1"), ("user_block", None, "m1"), ("community", "Community", "m1"),
          ("membership", "Membership", "m1"), ("locality_verification", None, "m1"),
          ("membership_decision", "MembershipDecision", "m1")],
    "B": [("category", None, "m3"), ("item", "Item", "m3"), ("booking", None, "m3"), ("condition_report", None, "m3"),
          ("invitation", None, "m1")],
    "C": [("borrowing_transaction", "BorrowingTransaction", "m3"), ("lifecycle_event", "LifecycleEvent", "m3"),
          ("allowed_transition", None, "ref"), ("audit_log", None, "m9")],
    "D": [("assessment", "Assessment", "m5"), ("outcome", "Outcome", "m5"), ("trust_edge", "TrustEdge", "m5"),
          ("review", "Review", "m5")],
    "E": [("escalation_case", "EscalationCase", "m9"), ("moderator_decision", "ModeratorDecision", "m9"),
          ("case_statement", None, "m9"), ("attachment", None, "m9")],
    "F": [("search_query", "SearchQuery", "m4"), ("search_impression", None, "m4"), ("search_click", None, "m4"),
          ("item_embedding", "ItemEmbedding", "m4"), ("notification", "Notification", "m7"), ("job_run", None, "sys")],
}
LAYOUT = {t: (col, None, cls, mod) for col, ts in STACK.items() for t, cls, mod in ts}
HEAD_COLOUR = {"m1": ("#DCE8F5", "#1F4E79"), "m3": ("#E2F0D9", "#2E5E1E"), "m5": ("#FCE9D9", "#8A4B12"),
               "m9": ("#EDE3F5", "#5B2C83"), "ref": ("#EEEEEE", "#555555"), "m4": ("#DFF3F1", "#00695C"),
               "m7": ("#FFF3D6", "#8A6100"), "sys": ("#ECEFF1", "#37474F")}
NEW_GREEN = "#0A7A36"
NEW_TABLES = {"membership_decision", "item_embedding", "search_query", "search_impression", "search_click",
              "notification", "job_run"}
NEW_COLUMNS = {("app_user", "terms_accepted_at"), ("community", "join_policy"), ("item", "condition"),
               ("item", "usage_terms"), ("item", "handover_method"), ("item", "search_terms"), ("item", "expires_at"),
               ("item", "updated_at"), ("item", "search_tsv"), ("attachment", "item_id")}
APPEND_ONLY = {"lifecycle_event", "audit_log", "assessment", "condition_report", "moderator_decision", "case_statement",
               "locality_verification", "allowed_transition", "membership_decision", "search_query", "search_impression"}

# foreign keys drawn as lines: (child table, child column) ; everything else is annotated in the row
DRAWN = {("membership", "user_id"), ("membership", "community_id"), ("locality_verification", "membership_id"),
         ("item", "community_id"), ("item", "category_id"), ("booking", "item_id"), ("booking", "transaction_id"),
         ("condition_report", "transaction_id"), ("borrowing_transaction", "item_id"),
         ("lifecycle_event", "stream_id"), ("lifecycle_event", "previous_state"),
         ("assessment", "transaction_id"), ("outcome", "source_event_id"), ("outcome", "flagged_by_decision_id"),
         ("escalation_case", "transaction_id"), ("escalation_case", "opened_event_id"),
         ("moderator_decision", "case_id"), ("case_statement", "case_id"), ("attachment", "case_statement_id"),
         ("review", "transaction_id"), ("membership_decision", "membership_id"),
         ("search_impression", "query_id"), ("search_click", "query_id")}

# per drawn FK: lane x (vertical channel) and sides; chosen so that no line crosses a table
ROUTES = {
    ("membership", "user_id"): dict(side="R", lane=362, pside="R"),
    ("membership", "community_id"): dict(side="R", lane=374, pside="R"),
    ("locality_verification", "membership_id"): dict(side="R", lane=386, pside="R"),
    ("membership_decision", "membership_id"): dict(side="R", lane=352, pside="R"),
    ("item", "community_id"): dict(side="L", lane=398, pside="R"),
    ("item", "category_id"): dict(side="L", lane=408, pside="L"),
    ("booking", "item_id"): dict(side="L", lane=400, pside="L"),
    ("booking", "transaction_id"): dict(side="R", lane=790, pside="L"),
    ("condition_report", "transaction_id"): dict(side="R", lane=800, pside="L"),
    ("borrowing_transaction", "item_id"): dict(side="L", lane=780, pside="R"),
    ("lifecycle_event", "stream_id"): dict(side="R", lane=1200, pside="R"),
    ("lifecycle_event", "previous_state"): dict(side="R", lane=1212, pside="R"),
    ("assessment", "transaction_id"): dict(side="L", lane=1224, pside="R"),
    ("outcome", "source_event_id"): dict(side="L", lane=1236, pside="R"),
    ("outcome", "flagged_by_decision_id"): dict(side="R", lane=1650, pside="L"),
    ("escalation_case", "transaction_id"): dict(side="L", lane=1640, pside="R", via_top=80),
    ("escalation_case", "opened_event_id"): dict(side="L", lane=1660, pside="R", via_gap=("assessment", "outcome"),
                                                 via_x=1242),
    ("moderator_decision", "case_id"): dict(side="R", lane=2075, pside="R"),
    ("case_statement", "case_id"): dict(side="R", lane=2085, pside="R"),
    ("attachment", "case_statement_id"): dict(side="R", lane=2095, pside="R"),
    ("review", "transaction_id"): dict(side="L", lane=1248, pside="R"),
    ("search_impression", "query_id"): dict(side="R", lane=2520, pside="R"),
    ("search_click", "query_id"): dict(side="R", lane=2532, pside="R"),
}


def table_height(n_cols, tagged):
    return HEAD + ROW * n_cols + 6 + (12 if tagged else 0)


def catalogue(cur):
    cur.execute("""SELECT c.table_name, c.column_name, c.ordinal_position, c.is_nullable = 'YES',
                          CASE WHEN c.data_type = 'USER-DEFINED' THEN c.udt_name
                               WHEN c.data_type = 'ARRAY' THEN substr(c.udt_name, 2) || '[]'
                               WHEN c.data_type LIKE 'timestamp with time zone' THEN 'timestamptz'
                               WHEN c.data_type = 'character varying' THEN 'text'
                               WHEN c.data_type = 'numeric' THEN 'numeric(' || c.numeric_precision || ',' || c.numeric_scale || ')'
                               ELSE c.data_type END
                   FROM information_schema.columns c JOIN information_schema.tables t
                     ON t.table_schema = c.table_schema AND t.table_name = c.table_name AND t.table_type = 'BASE TABLE'
                  WHERE c.table_schema = 'dm' ORDER BY c.table_name, c.ordinal_position""")
    cols = {}
    for t, c, _, nullable, typ in cur.fetchall():
        cols.setdefault(t, []).append(dict(name=c, nullable=nullable, type=typ))
    cur.execute("""SELECT con.contype, rel.relname, array_agg(att.attname ORDER BY k.ord), frel.relname,
                          (SELECT array_agg(fa.attname ORDER BY fk.ord) FROM unnest(con.confkey) WITH ORDINALITY fk(n, ord)
                             JOIN pg_attribute fa ON fa.attrelid = con.confrelid AND fa.attnum = fk.n)
                   FROM pg_constraint con JOIN pg_class rel ON rel.oid = con.conrelid
                   JOIN pg_namespace ns ON ns.oid = rel.relnamespace AND ns.nspname = 'dm'
                   JOIN unnest(con.conkey) WITH ORDINALITY k(n, ord) ON true
                   JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = k.n
                   LEFT JOIN pg_class frel ON frel.oid = con.confrelid
                  WHERE con.contype IN ('p', 'u', 'f', 'x')
                  GROUP BY con.oid, con.contype, rel.relname, frel.relname""")
    keys = cur.fetchall()
    return cols, keys


def build(cur) -> Diagram:
    cols, keys = catalogue(cur)
    pk = {(t, c) for typ, t, cs, *_ in keys if typ == "p" for c in cs}
    uq = {(t, cs[0]) for typ, t, cs, *_ in keys if typ == "u" and len(cs) == 1}
    fks = [(t, cs, ft, fcs) for typ, t, cs, ft, fcs in keys if typ == "f"]
    fk_of = {}
    for t, cs, ft, fcs in fks:
        for c in cs:
            fk_of[(t, c)] = ft
    missing = set(cols) - set(LAYOUT)
    if missing:
        raise SystemExit(f"tables without a position: {missing}")

    # stack each column; every table carries one note line under its name
    ypos, bottoms = {}, {}
    for col, ts in STACK.items():
        y = 110
        for t, _, _ in ts:
            ypos[t] = y
            y += table_height(len(cols[t]), True) + GAP
        bottoms[col] = y
    page_h = max(bottoms.values()) + 230
    d = Diagram("ER diagram v2.4 (DA-09)", 2580, int(page_h))
    d.text("<b>Digital Mohalla &#8212; ER diagram, schema v2.4</b> (iteration 2, DA-09 and DA-23: v2.3 plus migration 0002; "
           "generated from the PostgreSQL catalogue). <span style='color:#0A7A36'><b>Green +</b> = added in v2.4</span>",
           40, 12, 2200, 24, size=16, check=False)
    d.text(f"{len(cols)} tables, {sum(len(v) for v in cols.values())} columns, {len(fks)} foreign keys "
           f"({len(DRAWN)} drawn as lines; the rest are marked &#8594; table in the row). Crow's foot: "
           "|| exactly one, o| zero or one, o&lt; zero or many, |&lt; one or many.", 40, 38, 1600, 20,
           size=11, color="#4A5560", check=False)
    rows = {}
    for t, (col, _, cls, mod) in LAYOUT.items():
        y = ypos[t]
        x, w = COLS[col], WIDTH[col]
        fill, ink = HEAD_COLOUR[mod]
        h = HEAD + ROW * len(cols[t]) + 6
        title = f"<b>{t}</b>" + (f" <span style='font-weight:normal'>&#171;{cls}&#187;</span>" if cls else "")
        tags = []
        if t in NEW_TABLES:
            tags.append("<span style='color:#0A7A36'><b>+ new in v2.4</b></span>")
        if t in APPEND_ONLY:
            tags.append("append-only")
        if t in ("lifecycle_event", "audit_log"):
            tags.append("hash-chained")
        if t == "borrowing_transaction":
            tags.append("projection of lifecycle_event")
        if t == "booking":
            tags.append("EXCLUDE (item_id =, period &amp;&amp;) WHERE HELD")
        if t in ("assessment", "outcome", "review"):
            tags.append("fields: Student 2")
        if t == "item":
            tags.append("search_tsv: full-text (simple)")
        if t == "item_embedding":
            tags.append("vector(384), exact search")
        if t == "job_run":
            tags.append("UNIQUE (job_name, due_key)")
        if t == "notification":
            tags.append("UNIQUE (user_id, dedupe_key)")
        if not tags:
            tags.append("&#160;")
        if tags:
            title += f"<br><span style='font-weight:normal;font-size:9.5px;font-style:italic'>{' &#183; '.join(tags)}</span>"
        hh = HEAD + (12 if tags else 0)
        h += 12 if tags else 0
        tid = d.node(title, x, y, w, h,
                     f"swimlane;html=1;startSize={hh};fillColor={fill};strokeColor={ink};fontColor={ink};fontSize=11.5;"
                     f"swimlaneFillColor=#FFFFFF;rounded=0;childLayout=stackLayout;horizontal=1;horizontalStack=0;"
                     f"resizeParent=1;resizeParentMax=0;collapsible=0;marginBottom=0;whiteSpace=wrap;", id=f"t_{t}")
        d.mark_container(tid)
        for i, c in enumerate(cols[t]):
            mark = []
            if (t, c["name"]) in pk:
                mark.append("PK")
            if (t, c["name"]) in fk_of:
                mark.append("FK")
            if (t, c["name"]) in uq:
                mark.append("UQ")
            colour = "#9A9A9A" if c["nullable"] else "#1D1D1D"
            plus = ""
            if t in NEW_TABLES or (t, c["name"]) in NEW_COLUMNS:
                colour = NEW_GREEN
                plus = "<b style='color:#0A7A36'>+</b>"
            ref = ""
            if (t, c["name"]) in fk_of and (t, c["name"]) not in DRAWN and not (t == "lifecycle_event" and
                                                                                c["name"] in ("event_type", "new_state")):
                ref = f" <span style='color:#6A7A8A'>&#8594; {fk_of[(t, c['name'])]}</span>"
            if t == "lifecycle_event" and c["name"] == "payload":
                ref = " <span style='color:#B26A00'>(ADR-0005)</span>"
            label = (f"<span style='display:inline-block;width:40px;color:#555;font-size:9px'><b>{','.join(mark)}</b></span>"
                     f"{plus}<span style='color:{colour}'>{c['name']}</span> <span style='color:#8A8A8A;font-size:9.5px'>"
                     f"{c['type']}</span>{ref}")
            rid = d.node(label, x, y + hh + i * ROW, w, ROW,
                         "text;html=1;align=left;verticalAlign=middle;spacingLeft=6;fontSize=10.5;overflow=hidden;"
                         "rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;",
                         id=f"r_{t}_{c['name']}", parent=tid)
            rows[(t, c["name"])] = rid
            d.by_id[rid]["no_label_check"] = True

    # ---- relationship lines
    nullable = {(t, c["name"]): c["nullable"] for t in cols for c in cols[t]}
    for t, cs, ft, fcs in fks:
        key = (t, cs[0])
        if key not in DRAWN:
            continue
        r = ROUTES[key]
        src, tgt = rows[key], rows[(ft, fcs[0])]
        sb, tb = d.box(src), d.box(tgt)
        sy, ty = (sb[1] + sb[3]) / 2, (tb[1] + tb[3]) / 2
        sx = sb[2] if r["side"] == "R" else sb[0]
        tx = tb[2] if r["pside"] == "R" else tb[0]
        lane = r["lane"]
        pts = [(lane, sy), (lane, ty)]
        if "via_gap" in r:                       # dog-leg through the gap between two tables of column D
            upper, lower = r["via_gap"]
            vy = (d.box(f"t_{upper}")[3] + d.box(f"t_{lower}")[1]) / 2
            pts = [(lane, sy), (lane, vy), (r["via_x"], vy), (r["via_x"], ty)]
        if "via_top" in r:
            pts = [(lane, sy), (lane, r["via_top"]), (tx + 30 if r["pside"] == "R" else tx - 30, r["via_top"]),
                   (tx + 30 if r["pside"] == "R" else tx - 30, ty)]
        # cardinality: parent end exactly one (NOT NULL FK) or zero-or-one; child end many unless unique
        parent_end = "ERzeroToOne" if nullable[key] else "ERmandOne"
        if key in uq:
            child_end = "ERzeroToOne"
        elif key == ("lifecycle_event", "stream_id"):
            child_end = "ERoneToMany"            # every transaction has >= 1 event (deferred trigger)
        else:
            child_end = "ERzeroToMany"
        style = (EDGE_BASE + f"strokeColor=#46535F;endArrow={parent_end};startArrow={child_end};endFill=0;startFill=0;"
                 "strokeWidth=1.2;endSize=10;startSize=10;")
        d.edge(src, tgt, "", style=style, exit=(1 if r["side"] == "R" else 0, 0.5),
               entry=(1 if r["pside"] == "R" else 0, 0.5), points=pts)
    # legend
    lx, ly = 40, page_h - 200
    d.node("", lx, ly, 1180, 170, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#B0BAC4;", check=False)
    legend = ("<b>Legend</b><br>"
              "Header colour = module: <span style='background:#DCE8F5'>&nbsp;1 Accounts &amp; communities&nbsp;</span> "
              "<span style='background:#E2F0D9'>&nbsp;3 Borrowing lifecycle&nbsp;</span> "
              "<span style='background:#FCE9D9'>&nbsp;5 Assurance&nbsp;</span> "
              "<span style='background:#EDE3F5'>&nbsp;9 Moderation &amp; audit&nbsp;</span> "
              "<span style='background:#DFF3F1'>&nbsp;4 Search&nbsp;</span> "
              "<span style='background:#FFF3D6'>&nbsp;7 Notifications&nbsp;</span> "
              "<span style='background:#ECEFF1'>&nbsp;scheduler&nbsp;</span> "
              "<span style='background:#EEEEEE'>&nbsp;reference data&nbsp;</span><br>"
              "<span style='color:#0A7A36'><b>+ green</b></span> = table or column added by migration 0002 (v2.4); "
              "everything else is v2.3 unchanged.<br>"
              "&#171;Class&#187; = domain-model class (A2) the table realises. PK / FK / UQ = primary, foreign, unique key. "
              "Black column = NOT NULL, grey = nullable.<br>"
              "&#8594; table = foreign key not drawn as a line (mostly &#8216;who did it&#8217; columns to app_user).<br>"
              "lifecycle_event (previous_state, event_type, new_state) &#8594; allowed_transition is one composite foreign key "
              "(the A3 transition table).<br>No column stores coordinates, an address or a CNIC (privacy scan in test_schema.py).")
    d.text(legend, lx + 10, ly + 6, 1160, 158, size=10.5, check=False)
    return d


if __name__ == "__main__":
    conn = psycopg2.connect(os.environ["DM_TEST_DSN"])
    with conn, conn.cursor() as cur:
        diagram = build(cur)
    diagram.save(os.path.join(HERE, "er_diagram.drawio"))
