"""Generates sequence diagram (a): UC-B5 from borrowing request to assessment, with the timeout branch.

    python generate_sequence_a.py   ->  sequence_a_request_to_assessment.drawio

Design step A9 (a), owner Student 2 (Sequence_A_Request_To_Assessment.md holds the message specification).
v1.2 redraws Student 2's hand-drawn v1.1 in standard UML 2.5 notation with the same messages: actors as stick
figures, lifelines named :Class as in the component diagram, activation bars, combined fragments with the operator
in the pentagon and one guard per operand, and the normal flow inside the [else] operand of the locality check.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

TOP, HEAD = 80, 56
LIFE = [  # key, label, x-centre, fill (None = actor)
    ("B", "Borrower", 70, None),
    ("SVC", ":BorrowingService<br>(M3)", 250, "#E3EEF9"),
    ("LOC", ":LocalityChecker<br>&#171;ILocality&#187; (M1)", 470, "#E3EEF9"),
    ("ENG", ":AssuranceFacade<br>&#171;IAssess&#187; (M5)", 690, "#FDEBDD"),
    ("DB", ":EventStore<br>(M3, PostgreSQL)", 900, "#E3EEF9"),
    ("NOT", ":Notifier<br>&#171;stub&#187; (M7)", 1100, "#F2F2F2"),
    ("L", "Lender", 1270, None),
    ("M", "Moderator", 1390, None),
]
X = {k: x for k, _, x, _ in LIFE}
SYNC = EDGE_BASE + "endArrow=block;endFill=1;strokeColor=#1D1D1D;fontSize=10.5;"
ASYNC = EDGE_BASE + "endArrow=open;endFill=0;strokeColor=#1D1D1D;fontSize=10.5;"
RET = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#46535F;fontColor=#33404D;fontSize=10.5;"
FAIL = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#B00020;fontColor=#B00020;fontSize=10.5;"
ACT = "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#46535F;"


class Seq:
    def __init__(self, d):
        self.d, self.y, self.n = d, TOP + HEAD + 30, 0

    def msg(self, a, b, text, style=SYNC, step=30, dx=0):
        self.n += 1
        x1, x2 = X[a], X[b]
        off = 6 if x2 > x1 else -6
        self.d.edge(None, None, f"<b>{self.n}</b> {text}", style=style, src_pt=(x1 + off, self.y),
                    tgt_pt=(x2 - off, self.y), label_dy=-9, label_dx=dx)
        self.y += step

    def self_msg(self, a, text, step=44, width=300):
        self.n += 1
        x = X[a] + 6
        self.d.edge(None, None, "", style=SYNC, src_pt=(x, self.y), tgt_pt=(x, self.y + 18),
                    points=[(x + 30, self.y), (x + 30, self.y + 18)], check=False)
        self.d.text(f"<b>{self.n}</b> {text}", x + 36, self.y - 4, width, 30, size=10.5, check=False)
        self.y += step

    def note(self, text, x, w, h=34, colour="#FFF8E1"):
        self.d.node(text, x, self.y - 6, w, h, "shape=note;size=10;whiteSpace=wrap;html=1;fontSize=10;align=left;"
                    f"spacingLeft=6;fillColor={colour};strokeColor=#B26A00;", check=False)
        self.y += h + 8

    def frame(self, op, y0, y1, x0, x1, guards):
        """Combined fragment: operator in the pentagon, one guard per operand, dashed operand separators."""
        d = self.d
        d.node(op, x0, y0, x1 - x0, y1 - y0, "shape=umlFrame;whiteSpace=wrap;html=1;width=46;height=22;"
               "boundedLbl=1;verticalAlign=middle;align=left;spacingLeft=4;fontStyle=1;fontSize=11;fillColor=none;"
               "strokeColor=#5F6B76;", check=False)
        for k, (gy, text) in enumerate(guards):
            if k:
                d.edge(None, None, "", style="endArrow=none;dashed=1;html=1;strokeColor=#5F6B76;",
                       src_pt=(x0, gy - 6), tgt_pt=(x1, gy - 6), check=False)
            d.text(f"<b>{text}</b>", x0 + 52 if k == 0 else x0 + 8, gy - 16 if k == 0 else gy - 2, 640, 18,
                   size=10.5, color="#33404D", check=False)

    def activation(self, key, y0, y1):
        self.d.node("", X[key] - 6, y0, 12, y1 - y0, ACT, check=False, id=f"act_{key}_{int(y0)}")


def build() -> Diagram:
    d = Diagram("Sequence (a) B5 request to assessment (A9)", 1460, 1500)
    d.text("<b>Digital Mohalla &#8212; Sequence diagram (a): send borrowing request (UC-B5) to assessment, with the "
           "timeout branch</b> &#8212; design step A9 (a), Student 2, v1.2", 30, 12, 1400, 24, size=15, check=False)
    d.text("Pre-condition: borrower is a verified member; listing published. Lifelines are components of the component "
           "diagram (A8); event types and T-numbers from the A3 table; config 1.1.0-iteration1-draft. Specification: "
           "Sequence_A_Request_To_Assessment.md.", 30, 36, 1400, 20, size=11, color="#4A5560", check=False)
    bottom = 1440
    for k, label, x, colour in LIFE:
        if colour is None:
            d.node(label, x - 40, TOP, 80, HEAD, "shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;"
                   f"whiteSpace=wrap;html=1;container=0;verticalAlign=top;spacingTop=36;size={HEAD - 14};fontSize=11;"
                   "fontStyle=1;", check=False, id=f"ll_{k}")
        else:
            d.node(label, x - 82, TOP, 164, HEAD, "shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;"
                   f"html=1;container=0;collapsible=0;size={HEAD};fontSize=11;fillColor={colour};strokeColor=#46535F;",
                   check=False, id=f"ll_{k}")
    s = Seq(d)
    svc_start = s.y - 6
    s.msg("B", "SVC", "submitBorrowRequest(itemId, dates, message)  [POST /requests]", dx=40)
    s.note("ADR-0001: dates only marked as requested (soft hold); no location in the request (A11, D13)", X["B"] - 40, 300)
    s.msg("SVC", "DB", "append request_created (&#8594; REQUEST_CREATED, T01)")
    s.msg("DB", "SVC", "ack(stream_seq = 1)", style=RET)
    loc0 = s.y - 6
    s.msg("SVC", "LOC", "outcomeFor(borrowerId, communityId)")
    s.activation("LOC", loc0 + 6, s.y + 4)
    s.msg("LOC", "SVC", "VERIFIED | INCONCLUSIVE | CONFLICTING  (stored A11 result; no coordinates)", style=RET, dx=20)

    # ---------------------------------------------------------------- locality alt
    alt1 = s.y - 4
    g1 = s.y + 24
    s.y += 58
    s.msg("SVC", "DB", "append held_for_review {hold_reason: locality_inconclusive | locality_conflict}  (T03, T04; case opened)",
          dx=60)
    s.msg("SVC", "NOT", "notify(moderators, locality_hold)", style=ASYNC, dx=120)
    s.msg("NOT", "M", "case in queue", style=ASYNC)
    s.msg("SVC", "B", "SubmissionResult(HELD_FOR_REVIEW, reason)", style=RET)
    g2 = s.y + 4
    s.y += 40
    s.msg("SVC", "DB", "append locality_checked (&#8594; LOCALITY_CHECKED, T02)")
    eng0 = s.y - 6
    s.msg("SVC", "ENG", "assess(request)  [timer 2,000 ms; config_version 1.1.0-iteration1-draft]", dx=-20)
    s.self_msg("ENG", "Algorithms 1&#8211;4: Beta posterior, bounded k-hop, manipulation risk, decision table "
                      "(rule fired, hold reason)", width=330)

    # ---------------------------------------------------------------- engine alt (nested in [else])
    alt2 = s.y - 4
    h1 = s.y + 24
    s.y += 58
    s.msg("ENG", "SVC", "timeout or exception", style=FAIL)
    eng1 = s.y - 26
    s.msg("SVC", "DB", "append held_for_review {hold_reason: engine_failure}  (T08; no assessment, no assurance state)",
          dx=60)
    s.msg("SVC", "NOT", "notify(moderators, engine_failure, priority 1)", style=ASYNC, dx=140)
    s.msg("NOT", "M", "case in queue", style=ASYNC)
    s.msg("SVC", "B", "SubmissionResult(HELD_FOR_REVIEW, engine_failure)", style=RET)
    h2 = s.y + 4
    s.y += 40
    s.msg("ENG", "SVC", "AssessmentResult(REVIEW_RECOMMENDED, rule R2 | R4, hold_reason)", style=RET)
    s.msg("SVC", "DB", "INSERT assessment; append held_for_review {hold_reason, config_version}  (T06, T07; case opened)",
          dx=60)
    s.msg("SVC", "NOT", "notify(moderators, case with evidence trail)", style=ASYNC, dx=140)
    s.msg("NOT", "M", "case in queue", style=ASYNC)
    s.msg("SVC", "B", "SubmissionResult(HELD_FOR_REVIEW, hold_reason)", style=RET)
    h3 = s.y + 4
    s.y += 40
    s.msg("ENG", "SVC", "AssessmentResult(state, decision, rule, safeguards, explanation, config_version)", style=RET)
    s.activation("ENG", eng0 + 6, s.y - 26)
    s.msg("SVC", "DB", "INSERT assessment; append assessment_generated (&#8594; ASSESSED, T05)  [same config_version]",
          dx=60)
    s.msg("SVC", "NOT", "notify(lender, new request, evidence summary)", style=ASYNC, dx=140)
    s.msg("NOT", "L", "new borrowing request (UC-B6)", style=ASYNC)
    s.msg("SVC", "B", "SubmissionResult(ASSESSED, safeguards that may apply)", style=RET)
    s.frame("alt", alt2, s.y, 160, 1440, [(h1, "[timeout > 2,000 ms or engine fault]  (FR-T-07, UC-B5 5d)"),
                                          (h2, "[result has a hold reason]  (R2 manipulation level 4, ES-04; R4 high value, ES-06)"),
                                          (h3, "[else: no hold reason]  (R1, R3, R5&#8211;R9; ES-01, 02, 03, 05, 13)")])
    s.y += 16
    s.frame("alt", alt1, s.y, 140, 1450, [(g1, "[outcome = INCONCLUSIVE or CONFLICTING]  (UC-B5 4a, 4b; ES-09, ES-10)"),
                                          (g2, "[else: outcome = VERIFIED]")])
    s.activation("SVC", svc_start, s.y - 20)
    s.y += 20
    s.note("UML 2.5: solid line + filled head = synchronous call; dashed line + open head = reply; solid line + open "
           "head = asynchronous message; white bar = activation; alt = alternatives, exactly one operand runs. Never a "
           "default assurance state on failure (FR-T-07); no automatic rejection on any hold (FR-B-07).",
           30, 1000, 44, colour="#F4F6F8")
    if s.y > bottom:
        raise SystemExit(f"content ({s.y}) runs past the lifeline bottom ({bottom})")
    end = s.y + 20
    for k, *_ in LIFE:
        d.by_id[f"ll_{k}"]["h"] = end - TOP
    d.height = end + 30
    # activation bars go behind messages and labels (draw.io paints cells in list order)
    acts = [c for c in d.cells if c["id"].startswith("act_")]
    heads = [c for c in d.cells if c["id"].startswith("ll_")]
    d.cells = heads + acts + [c for c in d.cells if c not in acts and c not in heads]
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "sequence_a_request_to_assessment.drawio"))
