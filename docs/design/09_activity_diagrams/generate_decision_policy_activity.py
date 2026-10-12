"""Generates decision_policy_activity_diagram.drawio: the A5 decision policy as a UML 2.5 activity diagram.

    python generate_decision_policy_activity.py

Owner Student 2 (Decision_Policy_Activity_Diagram.md holds the rule matrix). v1.2 redraws Student 2's hand-drawn
diagram in standard notation with the same rules: decision nodes carry no text and every outgoing edge has a guard;
alternative flows meet in explicit merge nodes (several edges into one action would be an implicit join); control
flows have open arrowheads; the three partitions are the components that do the work (A8).
Rule order and contents: Algorithm_and_Data_Structure_Design.md §6, ADR-0007, ADR-0008, decision D12.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

LANE = ("swimlane;html=1;startSize=34;horizontal=1;fillColor=#F4F6F8;swimlaneFillColor=#FFFFFF;strokeColor=#5F6B76;"
        "fontStyle=1;fontSize=12;")
ACTION = ("rounded=1;arcSize=24;whiteSpace=wrap;html=1;fontSize=11;fillColor=#FFFFFF;strokeColor=#33404D;"
          "spacing=4;")
DECISION = "rhombus;html=1;fillColor=#FFFFFF;strokeColor=#33404D;"
INITIAL = "ellipse;html=1;fillColor=#1D1D1D;strokeColor=#1D1D1D;"
FINAL = "ellipse;shape=endState;html=1;fillColor=#1D1D1D;strokeColor=#1D1D1D;"
FLOW = EDGE_BASE + "endArrow=open;endFill=0;strokeColor=#1D1D1D;fontSize=10.5;"
STATE_FILL = {"SUFF": "#E3F4E3", "REV": "#FFF6D6", "INS": "#E6EAFF", "DIS": "#FDE3E0"}

CX = 520            # centre of the decision spine
RULE_X, RULE_W = 760, 300
BUS = 1120


def build() -> Diagram:
    d = Diagram("Decision policy activity (A5)", 1600, 1820)
    d.text("<b>Digital Mohalla &#8212; Decision policy (Algorithm 4) as a UML activity diagram</b> &#8212; design step "
           "A5, Student 2, v1.2", 30, 10, 1400, 24, size=15, check=False)
    d.text("First matching rule wins. Thresholds from config 1.1.0-iteration1-draft (&#964;<sub>&#956;</sub> 0.75, "
           "&#964;<sub>L</sub> 0.60, n<sub>min</sub> 3, &#961;<sub>sup</sub> 0.3, similarity floor 0.5, value bands). "
           "Rule matrix: Decision_Policy_Activity_Diagram.md &#167;3.", 30, 34, 1400, 20, size=11, color="#4A5560",
           check=False)
    top, h = 64, 1650
    for x, w, name in ((30, 300, "BorrowingService (lifecycle, M3)"),
                       (330, 880, "AssuranceFacade: decision policy (M5, Algorithm 4)"),
                       (1210, 350, "Moderation (M9)")):
        lid = d.node(name, x, top, w, h, LANE, check=False)
        d.mark_container(lid, pass_through=True)

    n = {}
    n["init"] = d.node("", 165, 110, 30, 30, INITIAL)
    n["call"] = d.node("Call assess(request); start 2,000 ms timer", 70, 160, 220, 50, ACTION)
    n["dt"] = d.node("", 160, 240, 40, 40, DECISION)
    n["inputs"] = d.node("Collect inputs: direct estimate (Alg. 1), indirect evidence (Alg. 2), manipulation "
                         "assessment (Alg. 3), transaction context", 370, 228, 300, 64, ACTION)
    n["t1"] = d.node("Append held_for_review {hold_reason: engine_failure}; no assessment, no assurance state (T08)",
                     1240, 340, 290, 64, ACTION + "fillColor=#FFE9D6;")
    d.edge(n["init"], n["call"], "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))
    d.edge(n["call"], n["dt"], "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))
    d.edge(n["dt"], n["inputs"], "[result returned]", style=FLOW, exit=(1, 0.5), entry=(0, 0.5), label_dy=-10)
    d.edge(n["dt"], n["t1"], "[timeout &gt; 2,000 ms or fault]", style=FLOW, exit=(0.5, 1), entry=(0.5, 0),
           points=[(180, 316), (1385, 316)], label_x=0.0, label_dy=-1)

    # ---------------------------------------------------------------- decision spine
    spine = [  # key, guard to the rule, rule label, colour
        ("R1", "[open dispute affects<br>the parties]", "<b>R1</b> ESCALATE &#8594; ACTIVE_DISPUTE<br>"
         "not held: the dispute has its own case (D12)", "DIS"),
        ("R2", "[manipulation level 4<br>(&#8805; 60, corroborated)]", "<b>R2</b> ESCALATE &#8594; REVIEW_RECOMMENDED<br>"
         "hold: manipulation_risk (ADR-0007)", "REV"),
        ("R3", "[no verified direct history<br>and &#961; &lt; 0.3]", "<b>R3</b> REQUEST_VERIFICATION &#8594; "
         "INSUFFICIENT_EVIDENCE<br>no history: lender review required", "INS"),
        ("R4", "[high value and (similarity &lt; 0.5<br>or lower bound L &lt; 0.60)]", "<b>R4</b> RESTRICT_HIGH_VALUE "
         "&#8594; REVIEW_RECOMMENDED<br>hold: high_value_low_confidence (N-7)", "REV"),
        ("R5", "[manipulation level 3]", "<b>R5</b> REQUEST_VERIFICATION &#8594;<br>REVIEW_RECOMMENDED", "REV"),
        ("R6_DISPUTE", "[resolved dispute<br>in the last 12 months]", "<b>R6_DISPUTE</b> PROCEED_WITH_SAFEGUARDS "
         "&#8594;<br>REVIEW_RECOMMENDED (ES-03)", "REV"),
        ("R6_SPARSE", "[n<sub>eff</sub> &lt; 3 and &#961; &lt; 0.3]", "<b>R6_SPARSE</b> REQUEST_VERIFICATION &#8594;<br>"
         "INSUFFICIENT_EVIDENCE (ADR-0008)", "INS"),
    ]
    prev = n["inputs"]
    y = 340
    rule_ids = {}
    for i, (key, guard, label, colour) in enumerate(spine):
        dk = d.node("", CX - 20, y, 40, 40, DECISION)
        d.edge(prev, dk, "" if i == 0 else "[else]", style=FLOW, exit=(0.5, 1), entry=(0.5, 0), label_dx=-24)
        r = d.node(label, RULE_X, y - 4, RULE_W, 48, ACTION + f"fillColor={STATE_FILL[colour]};")
        d.edge(dk, r, guard, style=FLOW, exit=(1, 0.5), entry=(0, 0.5), label_dy=-1)
        rule_ids[key] = (r, y + 20)
        prev, y = dk, y + 75
    d8 = d.node("", CX - 20, y, 40, 40, DECISION)
    d.edge(prev, d8, "[else]", style=FLOW, exit=(0.5, 1), entry=(0.5, 0), label_dx=-24)
    d9 = d.node("", CX - 20, y + 75, 40, 40, DECISION)
    d.edge(d8, d9, "[strong: &#956; &#8805; 0.75, L &#8805; 0.60,<br>n<sub>eff</sub> &#8805; 3; verification ok]",
           style=FLOW, exit=(0.5, 1), entry=(0.5, 0), label_dx=104)
    r7 = d.node("<b>R7</b> PROCEED &#8594; SUFFICIENT_EVIDENCE", RULE_X, y + 71, RULE_W, 48,
                ACTION + f"fillColor={STATE_FILL['SUFF']};")
    d.edge(d9, r7, "[risk level 1 and<br>standard value]", style=FLOW, exit=(1, 0.5), entry=(0, 0.5), label_dy=-1)
    rule_ids["R7"] = (r7, y + 95)
    r9 = d.node("<b>R9</b> PROCEED_WITH_SAFEGUARDS &#8594; REVIEW_RECOMMENDED (sparse with paths, ES-13; weak "
                "lower bound; unverified)", 345, y + 95, 150, 92, ACTION + f"fillColor={STATE_FILL['REV']};")
    d.edge(d8, r9, "[else]", style=FLOW, exit=(0, 0.5), entry=(0.5, 0), points=[(420, y + 20)], label_dy=-9)
    r8 = d.node("<b>R8</b> PROCEED_WITH_SAFEGUARDS &#8594; SUFFICIENT_EVIDENCE (medium or high value, or risk level 2)",
                CX - 80, y + 200, 300, 48, ACTION + f"fillColor={STATE_FILL['SUFF']};")
    d.edge(d9, r8, "[else]", style=FLOW, exit=(0.5, 1), entry=(80 / 300, 0), label_dx=24)

    # ---------------------------------------------------------------- merge and result
    my = y + 290
    merge = d.node("", CX - 20, my, 40, 40, DECISION)
    for key, (rid, ry) in rule_ids.items():
        d.edge(rid, merge, "", style=FLOW, exit=(1, 0.5), entry=(1, 0.5), points=[(BUS, ry), (BUS, my + 20)])
    d.edge(r8, merge, "", style=FLOW, exit=(80 / 300, 1), entry=(0.5, 0))
    d.edge(r9, merge, "", style=FLOW, exit=(0.5, 1), entry=(0, 0.5), points=[(420, my + 20)])
    a3 = d.node("Select safeguards (value band, interval width)", 370, my + 70, 300, 44, ACTION)
    a4 = d.node("Build explanation: state, mean with 90% interval, n<sub>eff</sub>, paths, signals, rule fired",
                370, my + 140, 300, 50, ACTION)
    a5 = d.node("Return AssessmentResult (state, decision, rule fired, hold reason, config_version)",
                370, my + 216, 300, 50, ACTION)
    d.edge(merge, a3, "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))
    d.edge(a3, a4, "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))
    d.edge(a4, a5, "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))

    hy = my + 300
    dh = d.node("", 160, hy, 40, 40, DECISION)
    d.edge(a5, dh, "", style=FLOW, exit=(0, 0.5), entry=(0.5, 0), points=[(180, my + 241)])
    a6 = d.node("Store assessment; append assessment_generated (&#8594; ASSESSED, T05)", 70, hy + 80, 220, 50, ACTION)
    a7 = d.node("Notify the lender with the evidence summary (UC-B6)", 70, hy + 160, 220, 44, ACTION)
    f1 = d.node("", 165, hy + 236, 30, 30, FINAL)
    d.edge(dh, a6, "[else: no hold reason]", style=FLOW, exit=(0.5, 1), entry=(0.5, 0), label_dx=0)
    d.edge(a6, a7, "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))
    d.edge(a7, f1, "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))
    h1 = d.node("Store assessment; append held_for_review {hold_reason, config_version} (T06, T07)",
                1240, hy - 5, 290, 50, ACTION + "fillColor=#FFE9D6;")
    d.edge(dh, h1, "[hold reason set: R2 or R4]", style=FLOW, exit=(1, 0.5), entry=(0, 0.5), label_x=-0.2)
    m2 = d.node("", 1365, hy + 80, 40, 40, DECISION)
    d.edge(h1, m2, "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))
    d.edge(n["t1"], m2, "", style=FLOW, exit=(1, 0.5), entry=(1, 0.5), points=[(1545, 372), (1545, hy + 100)])
    oc = d.node("Open escalation case with evidence trail (D6); notify moderators", 1240, hy + 150, 290, 50, ACTION)
    f2 = d.node("", 1370, hy + 236, 30, 30, FINAL)
    d.edge(m2, oc, "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))
    d.edge(oc, f2, "", style=FLOW, exit=(0.5, 1), entry=(0.5, 0))

    d.node("UML 2.5 notation: &#9679; initial node; &#9673; activity final; rounded box = action; diamond = decision "
           "(one guard per outgoing edge) or merge (several incoming); arrow = control flow; columns = activity "
           "partitions. Fill colour of a rule = assurance state (green sufficient, yellow review, blue insufficient, "
           "red active dispute; orange = hold). No path restricts a person automatically: a restriction is a "
           "moderator decision (FR-T-06).", 30, 1730, 1530, 46,
           "shape=note;size=12;whiteSpace=wrap;html=1;fontSize=10.5;align=left;spacingLeft=8;fillColor=#F4F6F8;"
           "strokeColor=#8C99A6;", check=False)
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "decision_policy_activity_diagram.drawio"))
