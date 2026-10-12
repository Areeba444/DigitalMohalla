"""Generates the ER diagram (crow's foot notation) from the live PostgreSQL catalogue.

Every table, column, type, key and cardinality is read from the database after
loading schema.sql, so the diagram cannot drift from the schema. Only the box
positions and line routes below are hand-made.

    pip install pgserver psycopg2-binary
    python generate_erd.py er_diagram.svg        (or set DM_TEST_DSN to use your own server)
"""
import html
import os
import sys
import tempfile

import psycopg2

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "Segoe UI, Arial, Helvetica, sans-serif"
BOX_W, ROW_H, HEAD_H = 290, 15, 36
OY = 70                                  # space for the title

AGREED = {  # Step-0 entity names
    'app_user': 'User', 'community': 'Community', 'request': 'Request', 'item': 'Item',
    'borrow_transaction': 'Transaction', 'transaction_event': 'TransactionEvent',
    'evidence_record': 'EvidenceRecord', 'assurance_result': 'AssuranceResult', 'dispute': 'Dispute',
    'moderator_decision': 'ModeratorDecision', 'audit_log': 'AuditLog', 'trust_edge': 'TrustEdge'}
APPEND_ONLY = {'transaction_event', 'audit_log', 'moderator_decision', 'assurance_result', 'condition_report',
               'dispute_statement', 'request', 'locality_verification', 'allowed_transition'}
OWNER_S2 = {'assurance_result', 'evidence_record', 'trust_edge', 'review'}

X = [30 + c * 390 for c in range(6)]
POS = {  # table: (column index, top y)
    'community': (0, 40), 'invitation': (0, 290), 'locality_verification': (0, 480), 'audit_log': (0, 760),
    'membership': (1, 40), 'app_user': (1, 260), 'user_block': (1, 520), 'trust_edge': (1, 660),
    'item': (2, 40), 'category': (2, 400), 'availability_block': (2, 560),
    'request': (3, 40), 'borrow_transaction': (3, 220), 'review': (3, 490), 'condition_report': (3, 760),
    'transaction_event': (4, 40), 'allowed_transition': (4, 380), 'assurance_result': (4, 530),
    'evidence_record': (5, 40), 'dispute': (5, 340), 'dispute_statement': (5, 640), 'attachment': (5, 830),
    'moderator_decision': (5, 1100),
}

# Drawn relationships: constraint name -> route (child end first, parent end last), y before OY.
ROUTES = {
    'membership_community_id_fkey': [(420, 100), (320, 100)],
    'membership_user_id_fkey': [(565, 187), (565, 260)],
    'locality_verification_membership_id_fkey': [(320, 520), (350, 520), (350, 160), (420, 160)],
    'locality_verification_invitation_id_fkey': [(175, 480), (175, 422)],
    'invitation_community_id_fkey': [(175, 290), (175, 232)],
    'user_block_blocker_id_fkey': [(530, 520), (530, 452)],
    'user_block_blocked_id_fkey': [(600, 520), (600, 452)],
    'trust_edge_from_user_id_fkey': [(420, 700), (385, 700), (385, 330), (420, 330)],
    'trust_edge_to_user_id_fkey': [(420, 740), (365, 740), (365, 300), (420, 300)],
    'item_owner_id_fkey': [(810, 300), (710, 300)],
    'item_community_id_fkey': [(870, 40), (870, 14), (175, 14), (175, 40)],
    'item_category_id_fkey': [(955, 337), (955, 400)],
    'availability_block_item_id_fkey': [(1100, 600), (1140, 600), (1140, 280), (1100, 280)],
    'borrow_transaction_item_id_fkey': [(1200, 250), (1100, 250)],
    'borrow_transaction_borrower_id_fkey': [(1200, 400), (1150, 400), (1150, 720), (780, 720), (780, 420), (710, 420)],
    'borrow_transaction_lender_id_fkey': [(1200, 415), (1172, 415), (1172, 740), (750, 740), (750, 435), (710, 435)],
    'request_transaction_id_fkey': [(1345, 157), (1345, 220)],
    'transaction_event_transaction_id_fkey': [(1590, 250), (1490, 250)],
    'event_transition_fk': [(1735, 292), (1735, 380)],
    'review_transaction_id_fkey': [(1345, 490), (1345, 427)],
    'assurance_result_transaction_id_fkey': [(1590, 560), (1550, 560), (1550, 370), (1490, 370)],
    'condition_report_transaction_id_fkey': [(1490, 790), (1520, 790), (1520, 400), (1490, 400)],
    'evidence_record_source_event_id_fkey': [(1980, 150), (1880, 150)],
    'dispute_opened_event_id_fkey': [(1980, 360), (1935, 360), (1935, 270), (1880, 270)],
    'dispute_transaction_id_fkey': [(1980, 400), (1915, 400), (1915, 338), (1490, 338)],
    'dispute_statement_dispute_id_fkey': [(2125, 640), (2125, 577)],
    'attachment_dispute_statement_id_fkey': [(2125, 830), (2125, 772)],
    'attachment_condition_report_id_fkey': [(1980, 900), (1490, 900)],
    'evidence_record_flagged_by_decision_id_fkey': [(2270, 200), (2330, 200), (2330, 1250), (2270, 1250)],
    'moderator_decision_dispute_id_fkey': [(2270, 1180), (2300, 1180), (2300, 450), (2270, 450)],
    'moderator_decision_reverses_decision_id_fkey': [(1980, 1150), (1945, 1150), (1945, 1215), (1980, 1215)],
}
# Unavoidable crossings: draw a line-jump at these x positions on horizontal segments.
HOPS = {'dispute_transaction_id_fkey': [1735]}
# Cardinalities the catalogue cannot express (enforced by the deferred trigger txn_require_start).
CHILD_OVERRIDE = {'request_transaction_id_fkey': 'one', 'transaction_event_transaction_id_fkey': 'one_many'}

out = []


def esc(s):
    return html.escape(str(s), quote=False)


def text(x, y, s, size=11, weight='normal', anchor='start', color='#1d1d1d', italic=False):
    st = ' font-style="italic"' if italic else ''
    wt = f' font-weight="{weight}"' if weight != 'normal' else ''
    out.append(f'<text x="{x}" y="{y}" font-size="{size}"{wt}{st} text-anchor="{anchor}" fill="{color}">{esc(s)}</text>')


def short_type(data_type, udt, num_prec, num_scale):
    if data_type == 'USER-DEFINED':
        return udt
    if data_type == 'ARRAY':
        return udt.lstrip('_') + '[]'
    return {'timestamp with time zone': 'timestamptz', 'integer': 'int', 'boolean': 'bool',
            'numeric': f'numeric({num_prec},{num_scale})' if num_prec else 'numeric'}.get(data_type, data_type)


def load(dsn):
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('DROP SCHEMA IF EXISTS dm CASCADE')
    cur.execute(open(os.path.join(HERE, 'schema.sql'), encoding='utf-8').read())
    cur.execute("""SELECT c.table_name, c.column_name, c.is_nullable, c.data_type, c.udt_name,
                          c.numeric_precision, c.numeric_scale
                     FROM information_schema.columns c
                     JOIN information_schema.tables t ON t.table_schema = c.table_schema
                      AND t.table_name = c.table_name AND t.table_type = 'BASE TABLE'
                    WHERE c.table_schema = 'dm' ORDER BY c.table_name, c.ordinal_position""")
    tables = {}
    for tname, col, nullable, dtype, udt, prec, scale in cur.fetchall():
        tables.setdefault(tname, []).append(dict(name=col, null=nullable == 'YES',
                                                 type=short_type(dtype, udt, prec, scale), keys=set()))
    cur.execute("""SELECT con.conname, con.contype, rel.relname, frel.relname,
                          ARRAY(SELECT a.attname FROM unnest(con.conkey) WITH ORDINALITY k(n, o)
                                JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.n ORDER BY k.o)
                     FROM pg_constraint con JOIN pg_class rel ON rel.oid = con.conrelid
                     LEFT JOIN pg_class frel ON frel.oid = con.confrelid
                    WHERE con.connamespace = 'dm'::regnamespace AND con.contype IN ('p', 'f', 'u')""")
    fks, uniques = [], []
    for name, ctype, tname, ftname, cols in cur.fetchall():
        bycol = {c['name']: c for c in tables[tname]}
        if ctype == 'p':
            for c in cols:
                bycol[c]['keys'].add('PK')
            uniques.append((tname, tuple(cols)))
        elif ctype == 'u':
            uniques.append((tname, tuple(cols)))
            if len(cols) == 1:
                bycol[cols[0]]['keys'].add('UQ')
        else:
            for c in cols:
                bycol[c]['keys'].add('FK')
            fks.append(dict(name=name, child=tname, parent=ftname, cols=cols,
                            nullable=any(bycol[c]['null'] for c in cols)))
    for fk in fks:
        fk['unique'] = (fk['child'], tuple(fk['cols'])) in uniques
    conn.close()
    return tables, fks


def box_geom(tables, t):
    c, y = POS[t]
    return X[c], y + OY, BOX_W, HEAD_H + ROW_H * len(tables[t]) + 6


def draw_box(tables, t):
    x, y, w, h = box_geom(tables, t)
    if t in AGREED:
        head, sub = '#1f3a5f', f'«{AGREED[t]}»'
    elif t == 'allowed_transition':
        head, sub = '#7a5a12', '«reference: state machine»'
    else:
        head, sub = '#4f6f7a', '«supporting»'
    tags = []
    if t in APPEND_ONLY:
        tags.append('append-only')
    if t in OWNER_S2:
        tags.append('fields: Student 2')
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#ffffff" stroke="#3b4a5e" stroke-width="1.3"/>')
    out.append(f'<path d="M{x},{y + 5} a5,5 0 0 1 5,-5 h{w - 10} a5,5 0 0 1 5,5 v{HEAD_H - 5} h{-w} z" fill="{head}"/>')
    text(x + 8, y + 15, t, size=12.5, weight='bold', color='#ffffff')
    text(x + 8, y + 30, sub + ('  ·  ' + ', '.join(tags) if tags else ''), size=9.5, color='#dfe7ef', italic=True)
    for i, col in enumerate(tables[t]):
        ry = y + HEAD_H + 12 + i * ROW_H
        if i % 2 == 1:
            out.append(f'<rect x="{x + 1}" y="{ry - 11}" width="{w - 2}" height="{ROW_H}" fill="#f3f6f9"/>')
        keys = ','.join(k for k in ('PK', 'FK', 'UQ') if k in col['keys'])
        color = '#888888' if col['null'] else '#1d1d1d'
        text(x + 6, ry, keys, size=9, weight='bold', color='#9a3b1c' if 'PK' in col['keys'] else '#2d5f8a')
        text(x + 44, ry, col['name'], size=10.5, color=color, weight='bold' if 'PK' in col['keys'] else 'normal')
        text(x + w - 6, ry, col['type'], size=10, anchor='end', color='#5a5a5a' if not col['null'] else '#a0a0a0')


def marker(px, py, dx, dy, kind):
    """Crow's foot marker at box edge point (px,py); (dx,dy) points into the box."""
    ox, oy = -dy, dx                       # perpendicular
    def pt(along, side):
        return px - dx * along + ox * side, py - dy * along + oy * side
    s = []
    def line(a, b):
        s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#3b4a5e" stroke-width="1.3"/>')
    def bar(along):
        line(pt(along, -6), pt(along, 6))
    def circle(along):
        cx, cy = pt(along, 0)
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="#ffffff" stroke="#3b4a5e" stroke-width="1.3"/>')
    def crow():
        line(pt(13, 0), pt(0, -7)); line(pt(13, 0), pt(0, 7)); line(pt(13, 0), pt(0, 0))
    if kind == 'one':
        bar(6); bar(12)
    elif kind == 'zero_one':
        bar(6); circle(19)
    elif kind == 'zero_many':
        crow(); circle(19)
    elif kind == 'one_many':
        crow(); bar(17)
    out.extend(s)


def draw_rel(fk):
    pts = [(x, y + OY) for x, y in ROUTES[fk['name']]]
    d = f'M {pts[0][0]},{pts[0][1]}'
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if y1 == y2:
            for hx in sorted(HOPS.get(fk['name'], []), reverse=x2 < x1):
                if min(x1, x2) < hx < max(x1, x2):
                    sgn = -1 if x2 < x1 else 1
                    d += f' L {hx - 6 * sgn},{y1} A 6 6 0 0 {1 if sgn > 0 else 0} {hx + 6 * sgn},{y1}'
        d += f' L {x2},{y2}'
    out.append(f'<path d="{d}" fill="none" stroke="#3b4a5e" stroke-width="1.3"/>')

    def direction(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = (dx * dx + dy * dy) ** 0.5
        return dx / n, dy / n
    child_kind = CHILD_OVERRIDE.get(fk['name']) or ('zero_one' if fk['unique'] else 'zero_many')
    parent_kind = 'zero_one' if fk['nullable'] else 'one'
    cdx, cdy = direction(pts[1], pts[0])
    marker(pts[0][0], pts[0][1], cdx, cdy, child_kind)
    pdx, pdy = direction(pts[-2], pts[-1])
    marker(pts[-1][0], pts[-1][1], pdx, pdy, parent_kind)


def main(path):
    dsn = os.environ.get('DM_TEST_DSN')
    if not dsn:
        import pgserver
        data = os.environ.get('DM_PGDATA') or os.path.join(tempfile.gettempdir(), 'dm_pgdata')
        dsn = pgserver.get_server(data, cleanup_mode='stop').get_uri()
    tables, fks = load(dsn)
    missing = set(tables) - set(POS)
    assert not missing, f'tables without a position: {missing}'
    unknown = set(ROUTES) - {f['name'] for f in fks}
    assert not unknown, f'routes for unknown constraints: {unknown}'

    W, H = 2360, OY + 1350
    text(30, 32, 'Digital Mohalla — ER Diagram (PostgreSQL schema "dm", committed core)', size=20, weight='bold', color='#10233d')
    text(30, 54, f'{len(tables)} tables · {sum(len(c) for c in tables.values())} columns · {len(fks)} foreign keys '
         f'({len(ROUTES)} drawn). Generated from the live database catalogue after loading schema.sql.', size=12, color='#444')
    for t in tables:
        draw_box(tables, t)
    for fk in fks:
        if fk['name'] in ROUTES:
            draw_rel(fk)

    # legend
    lx, ly = 420, 830 + OY
    out.append(f'<rect x="{lx}" y="{ly}" width="760" height="350" rx="6" fill="#ffffff" stroke="#999"/>')
    text(lx + 12, ly + 20, 'Legend', size=13, weight='bold')
    samples = [('one', 'exactly one'), ('zero_one', 'zero or one'), ('zero_many', 'zero or many'), ('one_many', 'one or many')]
    for i, (k, label) in enumerate(samples):
        sx = lx + 20 + i * 185
        out.append(f'<line x1="{sx}" y1="{ly + 45}" x2="{sx + 60}" y2="{ly + 45}" stroke="#3b4a5e" stroke-width="1.3"/>')
        marker(sx + 60, ly + 45, 1, 0, k)
        text(sx + 68, ly + 49, label, size=11)
    for i, (color, label) in enumerate([('#1f3a5f', 'Entity agreed at Step 0 («Name» = agreed entity name)'),
                                        ('#4f6f7a', 'Supporting table added by this design'),
                                        ('#7a5a12', 'Reference data (state machine transitions)')]):
        out.append(f'<rect x="{lx + 20}" y="{ly + 66 + i * 18}" width="22" height="12" fill="{color}"/>')
        text(lx + 50, ly + 76 + i * 18, label, size=11)
    notes = ['PK primary key · FK foreign key · UQ unique.  Grey column = nullable; black = NOT NULL.',
             '"append-only": UPDATE, DELETE and TRUNCATE are blocked by trigger (history cannot be rewritten).',
             '"fields: Student 2": structure agreed for integration; Student 2 owns the field-level design.']
    for i, n in enumerate(notes):
        text(lx + 20, ly + 140 + i * 16, n, size=11)
    undrawn = [f for f in fks if f['name'] not in ROUTES]
    text(lx + 12, ly + 200, f'Foreign keys not drawn as lines ({len(undrawn)}), to keep the diagram readable:', size=11.5, weight='bold')
    col_w = 370
    for i, f in enumerate(sorted(undrawn, key=lambda f: (f['child'], f['cols']))):
        cx = lx + 20 + (i % 2) * col_w
        cy = ly + 220 + (i // 2) * 15
        text(cx, cy, f"{f['child']}.{', '.join(f['cols'])} → {f['parent']}", size=10.5, color='#333')
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>', *out, '</svg>']
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
    print('ok', len(tables), 'tables', len(fks), 'fks', len(ROUTES), 'drawn', len(undrawn), 'listed')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'er_diagram.svg'))
