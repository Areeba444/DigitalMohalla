"""Shared helpers for the iteration 2 sequence diagrams (g), (h) and (i).

Same notation as design step A9 (generate_sequence_b.py): actors and lifelines from the component diagram,
synchronous calls with filled arrows, returns dashed, planned (not yet built) messages grey, combined
fragments as UML frames. Coordinates are absolute; every message is layout-checked by drawio.py.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import EDGE_BASE, Diagram  # noqa: E402,F401

TOP, HEAD = 80, 56
SYNC = EDGE_BASE + "endArrow=block;endFill=1;strokeColor=#1D1D1D;fontSize=10.5;"
ASYNC = EDGE_BASE + "endArrow=open;endFill=0;strokeColor=#1D1D1D;fontSize=10.5;"
RET = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#46535F;fontColor=#33404D;fontSize=10.5;"
FAIL = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#B00020;fontColor=#B00020;fontSize=10.5;"

# lifeline fills by owner (component diagram colours): S1 blue, S2 orange, S3 purple, shared grey
F_S1, F_S2, F_S3, F_SH = "#E3EEF9", "#FDEBDD", "#EFE6F6", "#F2F2F2"


class Seq:
    def __init__(self, d: Diagram, lifelines: list, bottom: float):
        self.d, self.n = d, 0
        self.X = {k: x for k, _, x, _ in lifelines}
        self.y = TOP + HEAD + 30
        for k, label, x, colour in lifelines:
            if colour is None:      # actor
                d.node(label, x - 40, TOP, 80, bottom - TOP, "shape=umlLifeline;participant=umlActor;"
                       "perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;verticalAlign=top;"
                       f"spacingTop=36;size={HEAD - 14};fontSize=11;fontStyle=1;", check=False, id=f"ll_{k}")
            else:
                d.node(label, x - 82, TOP, 164, bottom - TOP, "shape=umlLifeline;perimeter=lifelinePerimeter;"
                       f"whiteSpace=wrap;html=1;container=0;collapsible=0;size={HEAD};fontSize=11;"
                       f"fillColor={colour};strokeColor=#46535F;", check=False, id=f"ll_{k}")

    def msg(self, a, b, text, style=SYNC, step=30, number=True, dx=0):
        self.n += number
        label = (f"<b>{self.n}</b> " if number else "") + text
        x1, x2 = self.X[a], self.X[b]
        off = 5 if x2 > x1 else -5
        self.d.edge(None, None, label, style=style, src_pt=(x1 + off, self.y), tgt_pt=(x2 - off, self.y),
                    label_dy=-9, label_dx=dx, check=True)
        self.y += step

    def self_msg(self, a, text, step=40, dx=None):
        self.n += 1
        x = self.X[a] + 5
        self.d.edge(None, None, f"<b>{self.n}</b> {text}", style=SYNC, src_pt=(x, self.y),
                    tgt_pt=(x, self.y + 18), points=[(x + 30, self.y), (x + 30, self.y + 18)], check=True)
        e = self.d.cells[-1]
        e["label_x"] = 0
        e["label_dx"] = dx if dx is not None else 12 + len(text) * 2.6
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
            d.text(f"<b>{text}</b>", x0 + 52 if k == 0 else x0 + 8, gy - 16 if k == 0 else gy - 4, 900, 18,
                   size=10.5, color="#33404D", check=False)

    def heading(self, text, x=30):
        self.d.text(text, x, self.y - 14, 900, 18, size=12, color="#1F4E79", check=False)
        self.y += 34

    def note(self, text, x, w, h=34, colour="#FFF8E1"):
        self.d.node(text, x, self.y - 6, w, h, "shape=note;size=10;whiteSpace=wrap;html=1;fontSize=10;align=left;"
                    f"spacingLeft=6;fillColor={colour};strokeColor=#B26A00;", check=False)
        self.y += h + 6
