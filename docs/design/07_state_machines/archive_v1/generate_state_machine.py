"""Generates the Digital Mohalla transaction state machine (UML-style SVG).

Usage: python generate_state_machine.py transaction_state_machine.svg
Edit coordinates/labels below and re-run; keep names identical to State_Machine_Design.md."""
import html, sys

W, H = 1850, 2040
COL = dict(borrower='#1f5fa8', lender='#2a7f3f', moderator='#7a3b9a',
           party='#b35900', system='#6b6b6b', neutral='#333333')
LABEL_COL = dict(borrower='#174a85', lender='#20662f', moderator='#64307f',
                 party='#8f4700', system='#3f3f3f', neutral='#222222')

shapes, lines, labels, top = [], [], [], []
FONT = "Segoe UI, Arial, Helvetica, sans-serif"


def esc(s):
    return html.escape(s, quote=False)


def text(x, y, s, size=10.5, weight='normal', anchor='start', color='#222',
         halo=False, italic=False, layer=None):
    a = f'x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}"'
    if weight != 'normal':
        a += f' font-weight="{weight}"'
    if italic:
        a += ' font-style="italic"'
    if halo:
        a += ' paint-order="stroke" stroke="#ffffff" stroke-width="3.2" stroke-linejoin="round"'
    (layer if layer is not None else labels).append(f'<text {a}>{esc(s)}</text>')


def body_lines(x, y0, rows, step=14, size=10.5, layer=None):
    for i, r in enumerate(rows):
        indent = 0
        if r.startswith('  '):
            indent, r = 22, r.strip()
        text(x + indent, y0 + i * step, r, size=size, color='#1d1d1d', layer=layer)


def state(x, y, w, h, name, rows=(), kind='state'):
    if kind == 'final':
        fill, stroke, sw = '#ececec', '#4a4a4a', 1.8
    else:
        fill, stroke, sw = '#eaf2fb', '#2f4f75', 1.5
    shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" ry="10" '
                  f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    text(x + w / 2, y + 18, name, size=12.5, weight='bold', anchor='middle',
         color='#10233d' if kind != 'final' else '#222', layer=shapes)
    if rows:
        shapes.append(f'<line x1="{x}" y1="{y + 26}" x2="{x + w}" y2="{y + 26}" '
                      f'stroke="{stroke}" stroke-width="1"/>')
        body_lines(x + 8, y + 41, rows, layer=shapes)


def composite(x, y, w, h, name, sub=None, rows=(), kind='outer', row_y=None, step=14):
    styles = {
        'outer': ('#fafbfd', '#5d6b80', 1.8),
        'inner': ('#ffffff', '#7e8ba0', 1.4),
        'dispute': ('#fff6f3', '#a8483a', 1.8),
    }
    fill, stroke, sw = styles[kind]
    shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" ry="16" '
                  f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    text(x + 12, y + 20, name, size=13, weight='bold', color='#10233d', layer=shapes)
    if sub:
        text(x + 12 + len(name) * 9.2 + 6, y + 20, sub, size=10.5, italic=True,
             color='#555', layer=shapes)
    if rows:
        body_lines(x + 12, row_y if row_y else y + 38, rows, step=step, layer=shapes)


def initial(cx, cy):
    shapes.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="#222"/>')


def final(cx, cy):
    shapes.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="#fff" stroke="#222" stroke-width="1.6"/>')
    shapes.append(f'<circle cx="{cx}" cy="{cy}" r="5.5" fill="#222"/>')


def choice(cx, cy):
    shapes.append(f'<polygon points="{cx},{cy - 14} {cx + 14},{cy} {cx},{cy + 14} {cx - 14},{cy}" '
                  f'fill="#fff" stroke="#333" stroke-width="1.5"/>')


def history(cx, cy):
    shapes.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="#fff" stroke="#333" stroke-width="1.6"/>')
    text(cx, cy + 5, 'H', size=13, weight='bold', anchor='middle', layer=shapes)


def arrow(pts, who='system'):
    d = 'M ' + ' L '.join(f'{x},{y}' for x, y in pts)
    dash = ' stroke-dasharray="6,4"' if who == 'system' else ''
    lines.append(f'<path d="{d}" fill="none" stroke="{COL[who]}" stroke-width="1.5"{dash} '
                 f'marker-end="url(#ah-{who})"/>')


def lab(x, y, rows, who='system', anchor='start', step=13):
    for i, r in enumerate(rows):
        text(x, y + i * step, r, size=10.5, anchor=anchor, color=LABEL_COL[who], halo=True)


def note(x, y, w, h, rows, title=None):
    top.append(f'<path d="M{x},{y} H{x + w - 14} L{x + w},{y + 14} V{y + h} H{x} Z" '
               f'fill="#fffbe8" stroke="#a89350" stroke-width="1.2"/>')
    top.append(f'<path d="M{x + w - 14},{y} V{y + 14} H{x + w}" fill="none" stroke="#a89350" stroke-width="1.2"/>')
    yy = y + 17
    if title:
        text(x + 10, yy, title, size=11, weight='bold', color='#4a3f12', layer=top)
        yy += 15
    for r in rows:
        indent = 0
        if r.startswith('  '):
            indent, r = 12, r.strip()
        text(x + 10 + indent, yy, r, size=10.5, color='#2d2a1d', layer=top)
        yy += 13.5


def terminal(x, y, w, h, name, rows):
    state(x, y, w, h, name, rows, kind='final')
    mid = y + min(h / 2, 34)
    arrow([(x + w, mid), (x + w + 16, mid)], 'neutral')
    final(x + w + 28, mid)


# ------------------------------------------------------------------ title
text(20, 30, 'Digital Mohalla — Borrowing Transaction Lifecycle (UML State Machine)',
     size=18, weight='bold', color='#10233d', layer=top)
text(20, 50, 'Context object: Transaction (event-sourced aggregate). Every transition and every internal '
     'event is appended to TransactionEvent (actor, timestamp, previous state, new state, evidence, authorisation).',
     size=11, color='#444', layer=top)

# ------------------------------------------------------------------ composites
composite(20, 100, 1020, 750, 'PENDING', '(request not yet agreed)')
composite(20, 900, 1020, 930, 'IN_PROGRESS', '(agreement in force: lender accepted)')
composite(290, 960, 480, 270, 'HANDOVER_PENDING', '(“Accepted” in UC-B6)', kind='inner')
composite(290, 1290, 730, 260, 'ACTIVE', '(loan active)', kind='inner', rows=[
    'EXTENSION_REQUESTED [none pending] / notify lender',
    'EXTENSION_APPROVED [newDue > now ∧ dates free]',
    '  / dueDate := newDue',
    'EXTENSION_DECLINED / notify borrower'], row_y=1326)
composite(1230, 1270, 300, 490, 'DISPUTED', kind='dispute', rows=[
    'entry / freeze deposit and lifecycle commands;',
    '  compile evidence trail (UC-D6);',
    '  notify both parties + moderator; set deadline;',
    '  signal ACTIVE_DISPUTE to assurance engine',
    'DISPUTE_RESPONSE_ADDED / attach evidence',
    'DISPUTE_INFO_REQUESTED / extend deadline',
    'after(deadline) / DISPUTE_DEADLINE_ELAPSED',
    'exit / unfreeze deposit and commands'], row_y=1308, step=13)

# ------------------------------------------------------------------ PENDING
initial(490, 78)
state(330, 145, 320, 86, 'REQUESTED', [
    'entry / hold requested dates (tentative)',
    'do / check locality eligibility',
    '  (membership + coarse result only)'])
choice(490, 272)
state(330, 322, 320, 66, 'ASSESSING', [
    'do / run assurance engine (UC-D3/4/5)',
    '  → AssuranceResult'])
choice(490, 440)
state(805, 350, 227, 120, 'MODERATOR_REVIEW', [
    'entry / open review case (UC-D6);',
    '  notify moderator',
    'EVIDENCE_REQUESTED / notify party,',
    '  set evidence deadline'])
state(330, 640, 320, 82, 'AWAITING_LENDER', [
    'entry / show evidence summary +',
    '  safeguards; start response window'])

arrow([(490, 87), (490, 145)], 'borrower')
lab(500, 128, ['REQUEST_CREATED [G1] / create Request'], 'borrower')
arrow([(490, 231), (490, 258)])
lab(500, 249, ['LOCALITY_CHECKED(result)'])
arrow([(504, 272), (1580, 272)])
lab(520, 265, ["[result = INELIGIBLE]  (no APPROVED membership in the item's community)"])
arrow([(490, 286), (490, 322)])
lab(500, 308, ['[result ∈ {ELIGIBLE, INCONCLUSIVE}] / attach result as evidence'])
arrow([(490, 388), (490, 426)])
lab(500, 411, ['ASSURANCE_GENERATED'])
arrow([(504, 440), (805, 440)])
lab(560, 433, ['[requiresModerator]'])
arrow([(490, 454), (490, 640)])
lab(500, 478, ['[else]'])
arrow([(650, 372), (805, 372)])
lab(660, 365, ['ASSURANCE_FAILED'])
lab(660, 387, ['(error / timeout)'])
arrow([(920, 350), (920, 333), (650, 333)], 'party')
lab(660, 326, ['EVIDENCE_SUBMITTED [was requested] / re-assess'], 'party')
arrow([(900, 470), (900, 600), (620, 600), (620, 640)], 'moderator')
lab(628, 593, ['MODERATOR_CLEARED / attach safeguards'], 'moderator')
arrow([(1032, 455), (1580, 455)], 'moderator')
lab(1048, 448, ['MODERATOR_RESTRICTED [reason recorded] / release dates'], 'moderator')
arrow([(1040, 505), (1580, 505)])
lab(1050, 498, ['REQUEST_AUTO_DECLINED [dates unavailable ∨ listing withdrawn ∨ users blocked]'])
arrow([(650, 660), (1110, 660), (1110, 540), (1580, 540)], 'lender')
lab(660, 653, ['LENDER_DECLINED / release dates'], 'lender')
arrow([(650, 705), (1580, 705)])
lab(660, 698, ['after(responseWindow) / REQUEST_EXPIRED'])
arrow([(1040, 780), (1580, 780)])
lab(1050, 773, ['when(now ≥ requestedStart) / REQUEST_EXPIRED'])
arrow([(1040, 830), (1580, 830)], 'borrower')
lab(1050, 823, ['TRANSACTION_CANCELLED [actor = borrower ∨ system: party suspended]'], 'borrower')
arrow([(490, 722), (490, 960)], 'lender')
lab(500, 760, ['LENDER_ACCEPTED [dates still free]',
               '/ block dates; auto-decline overlapping',
               '  requests; open request chat'], 'lender')

note(1065, 92, 470, 122, [
    '• borrower ≠ lender; listing PUBLISHED and not paused',
    '• dates inside availability, not overlapping a HANDOVER_PENDING',
    '  or ACTIVE booking; no duplicate pending request by this borrower',
    '• borrower not blocked by lender; account active and verified',
    '  to the level the item requires (UC-B5 pre-conditions)',
    '• otherwise the command is rejected and no event is stored'],
    title='G1 — guard on REQUEST_CREATED')
top.append('<path d="M752,124 L1065,124" stroke="#a89350" stroke-width="1" stroke-dasharray="3,3" fill="none"/>')

# ------------------------------------------------------------------ IN_PROGRESS
initial(318, 1037)
state(340, 1002, 320, 68, 'AWAITING_HANDOVER', [
    'entry / enable exact meeting-point sharing',
    'when(now ≥ handoverTime) / REMINDER_SENT'])
state(340, 1130, 320, 84, 'AWAITING_RECEIPT', [
    'entry / ask borrower to review checklist',
    '  and handover photos',
    'CONDITION_NOTE_ADDED / attach note'])
arrow([(326, 1037), (340, 1037)], 'neutral')
arrow([(500, 1070), (500, 1130)], 'lender')
lab(510, 1092, ['HANDOVER_RECORDED',
                '[checklist ∧ deposit ∧ safeguards met]',
                '/ store photos + timestamp'], 'lender')
arrow([(660, 1045), (1580, 1045)])
lab(1050, 1038, ['when(now > handoverTime + grace) / HANDOVER_NO_SHOW'])
arrow([(770, 975), (1300, 975), (1300, 905), (1580, 905)], 'party')
lab(780, 968, ['TRANSACTION_CANCELLED [actor ∈ {borrower, lender}]'], 'party')
arrow([(500, 1214), (500, 1290)], 'borrower')
lab(510, 1241, ['HANDOVER_CONFIRMED',
                '/ dueDate := agreed end; schedule reminders'], 'borrower')
arrow([(660, 1195), (1230, 1300)])
lab(1050, 1222, ['after(receiptWindow)', '/ DISPUTE_OPENED', '(HANDOVER_UNCONFIRMED)'])

# ACTIVE internals
initial(705, 1322)
choice(705, 1362)
arrow([(705, 1330), (705, 1348)], 'neutral')
state(380, 1405, 240, 62, 'ON_LOAN', [
    'when(now ≥ dueDate − lead)',
    '  / REMINDER_SENT'])
state(790, 1400, 220, 105, 'OVERDUE', [
    'entry / flag late; notify both',
    'after(interval) / REMINDER_SENT',
    '  (escalating)'])
arrow([(691, 1362), (600, 1405)], 'neutral')
lab(650, 1374, ['[now ≤ dueDate]'], 'neutral', anchor='end')
arrow([(719, 1362), (840, 1400)], 'neutral')
lab(762, 1368, ['[else]'], 'neutral')
arrow([(620, 1430), (790, 1430)])
lab(628, 1423, ['when(now > dueDate)'])
lab(628, 1445, ['/ LOAN_OVERDUE'])
arrow([(790, 1485), (620, 1458)], 'lender')
lab(640, 1500, ['EXTENSION_APPROVED', '[newDue > now ∧', ' dates free]'], 'lender')
arrow([(1010, 1470), (1230, 1470)])
lab(1045, 1463, ['when(now > dueDate + overdueLimit)'])
lab(1045, 1485, ['/ DISPUTE_OPENED(NON_RETURN)'])
arrow([(1040, 1385), (1230, 1385)], 'party')
lab(1048, 1348, ['DISPUTE_OPENED(reason)', '[actor is borrower/lender ∨', ' system: party suspended]'], 'party')

state(370, 1615, 260, 112, 'RETURN_PENDING', [
    'entry / record returnTime;',
    '  late := returnTime > dueDate; notify',
    'after(confirmWindow) / REMINDER_SENT',
    '(mismatch → lender raises DISPUTE_OPENED)'])
arrow([(500, 1550), (500, 1615)], 'borrower')
lab(510, 1586, ['RETURN_INITIATED'], 'borrower')
arrow([(630, 1680), (1230, 1690)])
lab(700, 1659, ['after(2 × confirmWindow)', '/ DISPUTE_OPENED(RETURN_UNCONFIRMED)'])
history(990, 1790)

# ------------------------------------------------------------------ DISPUTED internals
initial(1262, 1451)
state(1290, 1420, 220, 62, 'DISPUTE_OPEN', ['entry / assign moderator (not a party)'])
state(1290, 1580, 220, 56, 'DISPUTE_ESCALATED', ['entry / assign to admin'])
arrow([(1270, 1451), (1290, 1451)], 'neutral')
arrow([(1400, 1482), (1400, 1580)], 'moderator')
lab(1392, 1515, ['DISPUTE_ESCALATED', '[unresolvable ∨ no', 'moderator available]'], 'moderator', anchor='end')
arrow([(1230, 1735), (1002, 1785)], 'party')
lab(1048, 1716, ['DISPUTE_WITHDRAWN', '[actor = raising party]'], 'party')
arrow([(1380, 1760), (1380, 1836)], 'moderator')
lab(1390, 1780, ['DISPUTE_RESOLVED(resolution)', '[authorised decider ∧', ' (all responded ∨ deadline passed)]'], 'moderator')
choice(1380, 1850)
arrow([(1394, 1850), (1580, 1850)], 'moderator')
lab(1450, 1868, ['[resolution = CLOSE]'], 'moderator')
arrow([(1366, 1850), (990, 1850), (990, 1803)], 'moderator')
lab(1100, 1843, ['[resolution = RESUME]'], 'moderator')

# ------------------------------------------------------------------ terminal (closed) states
TX, TW = 1580, 220
terminal(TX, 250, TW, 52, 'INELIGIBLE', ['entry / release held dates'])
terminal(TX, 430, TW, 130, 'DECLINED', ['entry / release dates;', '  notify borrower (reason)'])
terminal(TX, 685, TW, 115, 'EXPIRED', ['entry / release dates;', '  notify both parties'])
terminal(TX, 815, TW, 110, 'CANCELLED', ['entry / release dates;', '  notify other party'])
terminal(TX, 1010, TW, 70, 'NO_SHOW', ['entry / release dates;', '  outcome not attributed'])
terminal(TX, 1815, TW, 80, 'RESOLVED', ['entry / apply deposit decision;', '  emit resolved outcome'])
terminal(370, 1880, 260, 80, 'COMPLETED', ['entry / release deposit; free dates;', '  emit verified outcome; unlock reviews'])
arrow([(500, 1727), (500, 1880)], 'lender')
lab(510, 1770, ['RETURN_CONFIRMED', '[condition matches handover record]', '/ outcome := on-time or late'], 'lender')

# ------------------------------------------------------------------ legend
LX, LY = 20, 1852
top.append(f'<rect x="{LX}" y="{LY}" width="340" height="178" rx="6" fill="#ffffff" stroke="#999" stroke-width="1"/>')
text(LX + 10, LY + 17, 'Legend', size=11.5, weight='bold', layer=top)
top.append(f'<circle cx="{LX + 16}" cy="{LY + 33}" r="6" fill="#222"/>')
text(LX + 28, LY + 37, 'initial', layer=top)
top.append(f'<polygon points="{LX + 82},{LY + 25} {LX + 91},{LY + 33} {LX + 82},{LY + 41} {LX + 73},{LY + 33}" fill="#fff" stroke="#333"/>')
text(LX + 96, LY + 37, 'choice', layer=top)
top.append(f'<circle cx="{LX + 148}" cy="{LY + 33}" r="8" fill="#fff" stroke="#333"/>')
text(LX + 148, LY + 37, 'H', size=9.5, weight='bold', anchor='middle', layer=top)
text(LX + 160, LY + 37, 'shallow history', layer=top)
top.append(f'<circle cx="{LX + 252}" cy="{LY + 33}" r="7" fill="#fff" stroke="#222"/>')
top.append(f'<circle cx="{LX + 252}" cy="{LY + 33}" r="3.6" fill="#222"/>')
text(LX + 264, LY + 37, 'final', layer=top)
keys = [('borrower', 'Borrower'), ('lender', 'Lender'), ('party', 'Either party'),
        ('moderator', 'Moderator / Admin'), ('system', 'System (engine, scheduler)')]
for i, (k, name) in enumerate(keys):
    cx = LX + 12 + (i % 3) * 110 if i < 3 else LX + 12 + (i - 3) * 140
    cy = LY + 56 + (i // 3) * 16
    dash = ' stroke-dasharray="5,3"' if k == 'system' else ''
    top.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + 22}" y2="{cy}" stroke="{COL[k]}" stroke-width="2"{dash}/>')
    text(cx + 27, cy + 4, name, size=10, color=LABEL_COL[k], layer=top)
for i, r in enumerate([
        'Label = EVENT [guard] / action; EVENT = TransactionEvent type',
        'when(c) = change event; after(d) = time since state entry',
        'Arrow from a composite border applies to all its substates',
        'Grey = closed state. Any (state, event) pair not drawn is',
        'INVALID: command rejected, no event stored (see matrix)']):
    text(LX + 10, LY + 102 + i * 13, r, size=10, color='#222', layer=top)

# ------------------------------------------------------------------ write
defs = ['<defs>']
for k, c in COL.items():
    defs.append(f'<marker id="ah-{k}" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="7.5" '
                f'markerHeight="7.5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
defs.append('</defs>')
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="{FONT}">',
       *defs, f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
       *shapes, *lines, *labels, *top, '</svg>']
open(sys.argv[1], 'w', encoding='utf-8').write('\n'.join(svg))
print('ok', len(shapes), len(lines), len(labels))
