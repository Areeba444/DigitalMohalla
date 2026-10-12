"""Generates sequence diagram (b): UC-B7 handover and UC-B8 return, from dual confirmation to evidence.

    python generate_sequence_b.py   ->  sequence_b_handover_return.drawio

Design step A9 (b), Student 1. Lifelines are the components of component_diagram.drawio; messages use the
REST endpoints of Architecture_Design.md section 4 and the event types / transition IDs of the A3 table.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

TOP, HEAD = 80, 56
LIFE = [  # key, label, x-centre, owner colour
    ("L", "Lender", 80, None),
    ("B", "Borrower", 210, None),
    ("API", ":REST API", 370, "#F2F2F2"),
    ("SVC", ":BorrowingService<br>(M3)", 560, "#E3EEF9"),
    ("VAL", ":TransitionValidator<br>(M3)", 760, "#E3EEF9"),
    ("DB", ":EventStore<br>(PostgreSQL, triggers)", 960, "#E3EEF9"),
    ("ENG", ":AssuranceEngine<br>&#171;IOutcomeSink&#187; (M5)", 1170, "#FDEBDD"),
    ("TEP", ":TrustEdgeProjector<br>(M5, S1)", 1370, "#E3EEF9"),
    ("NOT", ":Notifier<br>&#171;stub&#187; (M7)", 1550, "#F2F2F2"),
]
X = {k: x for k, _, x, _ in LIFE}
SYNC = EDGE_BASE + "endArrow=block;endFill=1;strokeColor=#1D1D1D;fontSize=10.5;"
ASYNC = EDGE_BASE + "endArrow=open;endFill=0;strokeColor=#1D1D1D;fontSize=10.5;"
RET = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#46535F;fontColor=#33404D;fontSize=10.5;"
FAIL = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#B00020;fontColor=#B00020;fontSize=10.5;"


class Seq:
    def __init__(self, d):
        self.d, self.y, self.n = d, TOP + HEAD + 30, 0

    def msg(self, a, b, text, style=SYNC, step=30, number=True, dx=0):
        self.n += number
        label = (f"<b>{self.n}</b> " if number else "") + text
        x1, x2 = X[a], X[b]
        off = 5 if x2 > x1 else -5
        self.d.edge(None, None, label, style=style, src_pt=(x1 + off, self.y), tgt_pt=(x2 - off, self.y),
                    label_dy=-9, label_dx=dx, check=True)
        self.y += step

    def self_msg(self, a, text, step=40):
        self.n += 1
        x = X[a] + 5
        self.d.edge(None, None, f"<b>{self.n}</b> {text}", style=SYNC, src_pt=(x, self.y),
                    tgt_pt=(x, self.y + 18), points=[(x + 30, self.y), (x + 30, self.y + 18)],
                    label_dy=0, label_dx=0, label_x=0.0, check=True)
        # label to the right of the loop
        e = self.d.cells[-1]
        e["label_x"] = 0
        e["label_dx"] = 12 + len(text) * 2.6
        self.y += step

    def frame(self, op, y0, y1, x0, x1, guards=()):
        d = self.d
        d.node(op, x0, y0, x1 - x0, y1 - y0, "shape=umlFrame;whiteSpace=wrap;html=1;width=46;height=22;"
               "boundedLbl=1;verticalAlign=middle;align=left;spacingLeft=4;fontStyle=1;fontSize=11;fillColor=none;"
               "strokeColor=#5F6B76;", check=False)
        for k, (gy, text) in enumerate(guards):
            if k:
                d.edge(None, None, "", style="endArrow=none;dashed=1;html=1;strokeColor=#5F6B76;",
                       src_pt=(x0, gy - 6), tgt_pt=(x1, gy - 6), check=False)
            d.text(f"<b>{text}</b>", x0 + 52 if k == 0 else x0 + 8, gy - 16 if k == 0 else gy - 4, 760, 18, size=10.5, color="#33404D",
                   check=False)

    def note(self, text, x, w, h=34, colour="#FFF8E1"):
        self.d.node(text, x, self.y - 6, w, h, f"shape=note;size=10;whiteSpace=wrap;html=1;fontSize=10;align=left;"
                    f"spacingLeft=6;fillColor={colour};strokeColor=#B26A00;", check=False)
        self.y += h + 6


def build() -> Diagram:
    d = Diagram("Sequence (b) B7 + B8 (A9)", 1680, 2200)
    d.text("<b>Digital Mohalla &#8212; Sequence diagram (b): confirm handover (UC-B7) and return &#8594; evidence "
           "(UC-B8)</b> &#8212; design step A9 (b), Student 1, v1.1", 30, 12, 1500, 24, size=15, check=False)
    d.text("Precondition: request is ACCEPTED (UC-B6, T13; booking HELD). Event types and T-numbers: State_Machine_Design.md "
           "v2.2. Every append runs event_validate / event_apply (schema.sql) in one DB transaction.",
           30, 36, 1600, 20, size=11, color="#4A5560", check=False)
    bottom = 2140
    for k, label, x, colour in LIFE:
        if colour is None:
            d.node(label, x - 40, TOP, 80, HEAD, "shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;"
                   f"whiteSpace=wrap;html=1;container=0;verticalAlign=top;spacingTop=36;size={HEAD - 14};fontSize=11;"
                   f"fontStyle=1;", check=False, id=f"ll_{k}")
            d.by_id[f"ll_{k}"]["h"] = bottom - TOP
        else:
            d.node(label, x - 80, TOP, 160, bottom - TOP, "shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;"
                   f"html=1;container=0;collapsible=0;size={HEAD};fontSize=11;fillColor={colour};strokeColor=#46535F;",
                   check=False, id=f"ll_{k}")
    s = Seq(d)

    # ---------------------------------------------------------------- B7 handover
    d.text("<b>UC-B7 Confirm handover</b> (FR-B-11, FR-B-12)", 30, s.y - 14, 400, 18, size=12, color="#1F4E79", check=False)
    s.y += 34
    s.msg("L", "API", "POST /transactions/{id}/handover/checklist {checklist, photos?, deposit_received}", dx=230)
    s.msg("API", "SVC", "recordHandoverChecklist(id, lender, data)")
    s.msg("SVC", "VAL", "checkConfirmation(ACCEPTED, lender, HANDOVER)")
    s.msg("VAL", "SVC", "ok", style=RET)
    s.msg("SVC", "DB", "INSERT condition_report(HANDOVER, LENDER) &#8212; party_guard: state ACCEPTED", dx=0)
    s.msg("SVC", "NOT", "notify(borrower, review_handover)", style=ASYNC, dx=200)
    s.msg("API", "L", "202 awaiting borrower confirmation", style=RET)
    s.y += 6
    s.msg("B", "API", "POST /transactions/{id}/handover/confirm {condition_agreed}", dx=40)
    s.msg("API", "SVC", "confirmHandover(id, borrower, agreed)")
    s.msg("SVC", "DB", "INSERT condition_report(HANDOVER, BORROWER)")
    alt1 = s.y - 8
    g_ok = s.y + 22
    s.y += 50
    s.msg("SVC", "VAL", "validate(ACCEPTED, handover_confirmed, borrower)  [T18 guard]")
    s.msg("VAL", "SVC", "ok", style=RET)
    s.msg("SVC", "DB", "append handover_confirmed (stream_seq n+1, ACCEPTED &#8594; ACTIVE)")
    s.self_msg("DB", "trigger: check T18 guard, due_at := end date, hash chain; COMMIT")
    s.msg("SVC", "NOT", "notify(both, loan_active, due_at)", style=ASYNC, dx=200)
    s.msg("API", "B", "200 {state: ACTIVE, due_at}", style=RET)
    g_dep = s.y + 4
    s.y += 34
    s.msg("SVC", "DB", "append handover_confirmed", number=True)
    s.msg("DB", "SVC", "23514 deposit not recorded (UC-B7 3b): nothing committed, still ACCEPTED", style=FAIL, dx=40)
    s.msg("API", "B", "409 conflict: deposit not recorded", style=FAIL)
    g_dis = s.y + 4
    s.y += 34
    s.note("<b>ref</b> UC-B12 raise dispute &#8594; sequence (c): dispute_opened T23, ACCEPTED &#8594; DISPUTED "
           "(borrower disagrees with the recorded condition, UC-B7 3a)", X["API"] - 60, 640)
    s.frame("alt", alt1, s.y, 20, 1640, [(g_ok, "[lender checklist recorded AND borrower agrees AND (no deposit OR deposit "
                                                 "recorded)]"),
                                          (g_dep, "[required deposit not recorded as received]"),
                                          (g_dis, "[borrower does not agree (condition_agreed = false)]")])
    s.y += 30

    # ---------------------------------------------------------------- B8 return
    d.text("<b>UC-B8 Return item and complete</b> (FR-B-13, FR-B-15)", 30, s.y - 14, 500, 18, size=12, color="#1F4E79",
           check=False)
    s.y += 34
    s.msg("B", "API", "POST /transactions/{id}/return", dx=-10)
    s.msg("API", "SVC", "initiateReturn(id, borrower)")
    s.msg("SVC", "DB", "append return_initiated (ACTIVE &#8594; RETURN_INITIATED, T20)")
    s.msg("SVC", "NOT", "notify(lender, return_started)", style=ASYNC, dx=200)
    s.msg("API", "B", "200 {state: RETURN_INITIATED}", style=RET)
    s.y += 6
    s.msg("L", "API", "POST /transactions/{id}/return/confirm {checklist, photos?, condition_agreed}", dx=220)
    s.msg("API", "SVC", "confirmReturn(id, lender, data)")
    s.msg("SVC", "DB", "INSERT condition_report(RETURN, LENDER)")
    s.msg("API", "L", "202 awaiting borrower confirmation", style=RET)
    s.msg("B", "API", "POST /transactions/{id}/return/confirm {condition_agreed}", dx=40)
    s.msg("API", "SVC", "confirmReturn(id, borrower, agreed)")
    s.msg("SVC", "DB", "INSERT condition_report(RETURN, BORROWER)")
    alt2 = s.y - 8
    g2_ok = s.y + 22
    s.y += 50
    s.msg("SVC", "VAL", "validate(RETURN_INITIATED, return_confirmed, borrower)  [T21]")
    s.msg("VAL", "SVC", "ok", style=RET)
    s.msg("SVC", "DB", "BEGIN; append return_confirmed (&#8594; RETURNED, T21)")
    s.msg("SVC", "DB", "append transaction_closed {outcome: on_time | late} (&#8594; COMPLETED, T22)")
    s.self_msg("DB", "trigger: outcome checked vs due_at; booking RELEASED; COMMIT")
    s.msg("SVC", "ENG", "recordOutcome(closing event_id)  [after commit; idempotent]", style=ASYNC, dx=-120)
    s.self_msg("ENG", "OutcomeExtractor: confirmed outcomes per role / metric &#8594; INSERT outcome")
    s.msg("ENG", "TEP", "onOutcomes(outcomes)")
    s.self_msg("TEP", "upsert trust_edge (both directions)")
    s.msg("TEP", "ENG", "edges updated", style=RET)
    s.msg("SVC", "NOT", "notify(both, completed; deposit release recorded)", style=ASYNC, dx=200)
    s.msg("API", "B", "200 {state: COMPLETED, outcome}", style=RET)
    g2_dis = s.y + 4
    s.y += 34
    s.msg("SVC", "VAL", "validate(RETURN_INITIATED, return_confirmed)")
    s.msg("VAL", "SVC", "rejected: parties disagree on condition", style=FAIL)
    s.msg("API", "B", "409: condition disputed &#8212; raise a dispute", style=FAIL)
    s.note("<b>ref</b> sequence (c): dispute_opened T23 (RETURN_INITIATED &#8594; DISPUTED); deposit record frozen; "
           "outcome not counted until dispute_resolved (UC-B8 3a, ES-07)", X["API"] - 60, 640)
    s.frame("alt", alt2, s.y, 20, 1640, [(g2_ok, "[both parties confirm and agree on condition]"),
                                         (g2_dis, "[lender reports damage or the parties disagree]")])
    s.y += 26
    s.note("Concurrency: two confirmations arriving together both try stream_seq n+1; the unique (stream_id, stream_seq) "
           "key lets one commit and the other is re-read and retried (409 stale). Missed outcome deliveries are found by "
           "the view v_pending_outcomes and retried; outcome (source_event_id, subject_id, metric) is unique, so a retry never double-counts. Trust-edge "
           "weight: recency-weighted Beta posterior mean (ADR-0006).", 40, 1580, 46, colour="#F4F6F8")
    if s.y > bottom:
        raise SystemExit(f"content ({s.y}) runs past the lifeline bottom ({bottom})")
    end = s.y + 30                     # trim lifelines to the content
    for k, *_ in LIFE:
        d.by_id[f"ll_{k}"]["h"] = end - TOP
    d.height = end + 30
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "sequence_b_handover_return.drawio"))
