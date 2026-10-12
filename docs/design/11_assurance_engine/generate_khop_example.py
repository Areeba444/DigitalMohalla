"""Worked example for bounded k-hop indirect evidence (design step A5, indirect-trust part, Student 1).

    python generate_khop_example.py  ->  khop_worked_example.drawio, khop_example_results.md

Formulas: Overview section 5.5 and FR-T-04 (k = 3, gamma = 0.7, cap 0.6, strongest path per first hop, noisy-OR,
rho = min(0.6, min(1,|P|/3) * min(1,|first hops|/2) * I)). The graph, its edge weights, t_v and b are ILLUSTRATIVE
inputs for a hand check (test suite 7); they are not measured values. The same numbers become the unit-test fixture.
"""
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

GAMMA, CAP = 0.7, 0.6
T_V, BASE = 0.80, 0.70          # illustrative: borrower's direct posterior mean (from others) and population baseline
NODES = {"L": (120, 380, "Lender (u)"), "A": (360, 150, "A"), "C": (360, 380, "C"), "D": (360, 600, "D"),
         "E": (620, 330, "E"), "F": (600, 560, "F"), "G": (860, 520, "G"), "B": (1100, 380, "Borrower (v)")}
# Edge weight rule (ADR-0006): weight(A->B) = recency-weighted Beta posterior mean of the outcomes A has
# confirmed about B in that role and metric, prior Beta(1, 1). Counts below are synthetic, all recent (age ~0 days).
OUTCOMES = {("L", "A"): (8, 0), ("L", "C"): (3, 0), ("L", "D"): (2, 1), ("A", "B"): (5, 0), ("A", "E"): (8, 0),
            ("E", "B"): (3, 0), ("C", "E"): (6, 2), ("C", "F"): (8, 0), ("F", "G"): (8, 0), ("G", "B"): (8, 0),
            ("D", "B"): (1, 1), ("B", "A"): (3, 0)}


def edge_weight(successes_w, failures_w, alpha0=1.0, beta0=1.0):
    return (alpha0 + successes_w) / (alpha0 + beta0 + successes_w + failures_w)


EDGES = {e: edge_weight(s, f) for e, (s, f) in OUTCOMES.items()}


def simple_paths(u, v, k):
    out = []

    def dfs(node, path):
        if len(path) - 1 > k:
            return
        if node == v and len(path) > 1:
            out.append(list(path))
            return
        for (a, b), _ in EDGES.items():
            if a == node and b not in path:          # simple paths only: cycles are never followed
                dfs(b, path + [b])
    dfs(u, [u])
    return out


def q(path):
    w = 1.0
    for a, b in zip(path, path[1:]):
        w *= EDGES[(a, b)]
    return w * GAMMA ** (len(path) - 2), w


def evaluate(k):
    paths = simple_paths("L", "B", k)
    best = {}
    for p in paths:
        qq, _ = q(p)
        if p[1] not in best or qq > q(best[p[1]])[0]:
            best[p[1]] = p
    sel = list(best.values())
    prod = 1.0
    for p in sel:
        prod *= 1 - q(p)[0]
    I = 1 - prod if sel else 0.0
    rho = min(CAP, min(1, len(sel) / 3) * min(1, len(best) / 2) * I) if sel else 0.0
    return paths, sel, I, rho, BASE + rho * (T_V - BASE)


def build():
    all4, sel3, I3, rho3, t3 = evaluate(4)[0], *evaluate(3)[1:]
    d = Diagram("k-hop worked example (A5)", 1860, 1080)
    d.text("<b>Digital Mohalla &#8212; Bounded k-hop indirect evidence: worked example</b> (design step A5, indirect-trust "
           "part, Student 1; fixture for test suite 7)", 30, 12, 1500, 24, size=16, check=False)
    d.text("Question for ES-13: the borrower has history with others but none with this lender. How much may the lender "
           "rely on it through community paths? Outcome counts, t_v and b are synthetic hand-check inputs; weights follow ADR-0006.",
           30, 38, 1600, 20, size=11, color="#4A5560", check=False)
    sel_edges = {(a, b) for p in sel3 for a, b in zip(p, p[1:])}
    for n, (x, y, label) in NODES.items():
        fill = "#E3EEF9" if n in ("L", "B") else "#FFFFFF"
        d.node(f"<b>{n}</b>", x, y, 56, 56, f"ellipse;html=1;fillColor={fill};strokeColor=#1F4E79;strokeWidth=2;fontSize=14;",
               id=n)
        if n in ("L", "B"):
            lx, ly = (x - 22, y + 60) if n == "L" else (x + 60, y + 19)
            d.text(label, lx, ly, 100, 18, size=10.5, align="center" if n == "L" else "left", color="#1F4E79",
                   check=False)
    route = {("D", "B"): [(388 + 300, 628), (1128, 628)], ("B", "A"): [(1128, 100), (388, 100)]}
    exits = {("D", "B"): ((1, 0.5), (0.5, 1)), ("B", "A"): ((0.5, 0), (0.5, 0))}
    lpos = {("L", "A"): 0, ("A", "B"): -0.1, ("D", "B"): 0.0, ("B", "A"): 0.0, ("C", "F"): 0.0}
    for (a, b), w in EDGES.items():
        on = (a, b) in sel_edges
        col = "#1D1D1D" if on else "#9AA4AE"
        st = EDGE_BASE + f"endArrow=block;endFill=1;strokeColor={col};fontColor={col};strokeWidth={2.4 if on else 1.2};"
        if (a, b) == ("B", "A"):
            st += "dashed=1;"
        ex = exits.get((a, b))
        pts = route.get((a, b), [])
        if (a, b) == ("D", "B"):
            pts = [(1128, 628)]
        s_, f_ = OUTCOMES[(a, b)]
        lab = f"{w:.2f} ({s_}&#10003;{f' {f_}&#10007;' if f_ else ''})"
        d.edge(a, b, lab if (a, b) != ("B", "A") else lab + " B&#8594;A: not on any simple L&#8594;B path",
               style=st, exit=ex[0] if ex else None, entry=ex[1] if ex else None, points=pts,
               label_x=lpos.get((a, b), 0), check=True)
    # ---- calculation table
    rows = []
    names = {}
    for idx, p in enumerate(sorted(all4, key=lambda p: (len(p), p)), 1):
        names[tuple(p)] = f"P{idx}"
    for p in sorted(all4, key=lambda p: (len(p), p)):
        qq, prod = q(p)
        hops = len(p) - 1
        status = ("selected (strongest via " + p[1] + ")" if p in sel3 else
                  "excluded: hops &gt; k = 3" if hops > 3 else f"dropped: weaker path via {p[1]}")
        rows.append(f"<tr><td><b>{names[tuple(p)]}</b></td><td>{'&#8594;'.join(p)}</td><td align='center'>{hops}</td>"
                    f"<td align='center'>{prod:.4f}</td><td align='center'>{GAMMA ** (hops - 1):.2f}</td>"
                    f"<td align='center'><b>{qq:.4f}</b></td><td>{status}</td></tr>")
    table = ("<table border='1' cellpadding='4' style='border-collapse:collapse;font-size:11px'>"
             "<tr style='background:#E3EEF9'><th>Path</th><th>nodes</th><th>hops</th><th>&#8719; w</th>"
             "<th>&#947;<sup>hops&#8722;1</sup></th><th>q(P)</th><th>k = 3 decision</th></tr>" + "".join(rows) + "</table>")
    d.text("<b>Step 1&#8211;3: simple paths L&#8594;B, path strength q(P) = &#8719; edge weights &#215; 0.7<sup>hops&#8722;1</sup>, "
           "strongest path per first hop</b><br><br>" + table, 1220, 120, 620, 300, size=11, check=False)
    calc = (f"<b>Step 4: noisy-OR over selected paths</b><br>I(L,B) = 1 &#8722; &#8719;(1 &#8722; q) = 1 &#8722; "
            + " &#215; ".join(f"(1 &#8722; {q(p)[0]:.4f})" for p in sel3) + f" = <b>{I3:.4f}</b><br><br>"
            f"<b>Step 5: reliability with path-diversity and cap</b><br>|P| = {len(sel3)}, first hops = {len(sel3)}<br>"
            f"&#961; = min(0.6, min(1, {len(sel3)}/3) &#183; min(1, {len(sel3)}/2) &#183; {I3:.4f}) = min(0.6, "
            f"{min(1, len(sel3) / 3) * min(1, len(sel3) / 2) * I3:.4f}) = <b>{rho3:.4f}</b> (capped)<br><br>"
            f"<b>Step 6: indirect estimate</b> (t_v = {T_V:.2f} borrower's direct mean from others, b = {BASE:.2f} "
            f"baseline; illustrative)<br>t_indirect = b + &#961;(t_v &#8722; b) = {BASE:.2f} + {rho3:.2f} &#215; "
            f"{T_V - BASE:.2f} = <b>{t3:.3f}</b><br>Indirect evidence supplements direct evidence; on its own it can "
            "never give SUFFICIENT_EVIDENCE (Overview 5.11).")
    d.text(calc, 1220, 470, 620, 230, size=11, check=False)
    sweep = []
    for k in (1, 2, 3, 4):
        paths, sel, I, rho, tt = evaluate(k)
        sweep.append(f"<tr><td align='center'>{k}</td><td align='center'>{len(paths)}</td>"
                     f"<td align='center'>{len(sel)}</td><td align='center'>{I:.4f}</td><td align='center'>{rho:.4f}</td>"
                     f"<td align='center'>{f'{tt:.3f}' if sel else 'none (D3 ext 3a)'}</td></tr>")
    d.text("<b>k sweep on this graph</b> (NFR-P-03 reports latency for k = 1..4)<br><br>"
           "<table border='1' cellpadding='4' style='border-collapse:collapse;font-size:11px'><tr style='background:#E3EEF9'>"
           "<th>k</th><th>paths found</th><th>selected</th><th>I</th><th>&#961;</th><th>t_indirect</th></tr>"
           + "".join(sweep) + "</table><br>k = 4 finds P5 but it is weaker than P4 through the same first hop C, so the "
           "result does not change: one path per first hop stops correlated paths being double-counted.",
           1220, 740, 620, 230, size=11, check=False)
    d.node("", 30, 760, 1160, 280, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#B0BAC4;", check=False)
    d.text("<b>How to read the graph</b><br>Directed edge X&#8594;Y = verified evidence X holds about Y for the same role "
           "and metric (weight in (0, 1]), built by TrustEdgeProjector from confirmed outcomes only. Bold edges lie on the "
           "selected paths; grey edges are found but not used.<br><br><b>What the example checks</b> (test suite 7: "
           "expected paths, decay, one path per first hop, noisy-OR, &#961; &#8804; 0.6, nothing beyond k, cycles safe)"
           "<br>&#8226; decay: P3 (3 hops) is multiplied by 0.49, P1 (2 hops) by 0.7, a 1-hop path by 1.<br>&#8226; one "
           "path per first hop: P1 and P3 both start L&#8594;A; only the stronger P1 counts.<br>&#8226; bound: P5 has 4 hops and is "
           "ignored at k = 3.<br>&#8226; cycles: B&#8594;A would allow L&#8594;A&#8594;B&#8594;A&#8230;; simple paths never "
           "revisit a node.<br>&#8226; cap: I = " f"{I3:.2f} would give &#961; = {I3:.2f}; the cap keeps indirect reliability "
           "&#8804; 0.6 (always below direct evidence).<br>&#8226; diversity: if only P1 existed, &#961; = "
           f"min(1,1/3)&#183;min(1,1/2)&#183;{q(sel3[0])[0]:.4f} = {min(1, 1 / 3) * min(1, 1 / 2) * q(sel3[0])[0]:.4f}."
           "<br><br><b>Complexity</b>: bounded DFS from u visits at most &#931;<sub>h&#8804;k</sub> d<sup>h</sup> = "
           "O(d<sup>k</sup>) partial paths (d = max out-degree); with k = 3 and neighbourhood-sized d this is small. "
           "Selection is O(|paths|), noisy-OR O(|first hops|).<br><b>Edge weight (ADR-0006)</b>: weight = (1 + s<sub>w</sub>) / "
           "(2 + s<sub>w</sub> + f<sub>w</sub>), the recency-weighted Beta posterior mean of what the source confirmed about the "
           "target; labels show successes &#10003; and failures &#10007;.", 40, 768, 1140, 262, size=11,
           check=False)
    return d, all4, sel3, I3, rho3, t3


def write_md(all4, sel3, I3, rho3, t3):
    lines = ["# k-hop worked example: computed values", "",
             "Generated by `generate_khop_example.py` (do not edit by hand). Inputs are illustrative.", "",
             "| Path | Nodes | Hops | q(P) | Selected at k = 3 |", "|---|---|---|---|---|"]
    for idx, p in enumerate(sorted(all4, key=lambda p: (len(p), p)), 1):
        lines.append(f"| P{idx} | {' -> '.join(p)} | {len(p) - 1} | {q(p)[0]:.4f} | {'yes' if p in sel3 else 'no'} |")
    lines += ["", f"I = {I3:.4f}; rho = {rho3:.4f}; t_indirect = {t3:.4f} (t_v = {T_V}, b = {BASE})", "",
              "| k | paths | selected | I | rho | t_indirect |", "|---|---|---|---|---|---|"]
    for k in (1, 2, 3, 4):
        paths, sel, I, rho, tt = evaluate(k)
        lines.append(f"| {k} | {len(paths)} | {len(sel)} | {I:.4f} | {rho:.4f} | {tt:.4f} |")
    with open(os.path.join(HERE, "khop_example_results.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    d, *vals = build()
    d.save(os.path.join(HERE, "khop_worked_example.drawio"))
    write_md(*vals)
    print(open(os.path.join(HERE, "khop_example_results.md"), encoding="utf-8").read())
