"""Minimal draw.io (mxGraph) writer with a layout checker.

Every diagram generator in this repository builds its figure through this module, so that:
  * the output is a plain, uncompressed .drawio file that diagrams.net / draw.io desktop opens and edits;
  * edges carry explicit exit/entry points and waypoints, so the rendered route is exactly the route
    the checker sees (no automatic routing surprises);
  * check() reports any edge segment that passes through a shape it does not connect, and any edge
    label that overlaps a shape or another label.

Coordinates are absolute page coordinates. Child cells (class rows, lifeline activations, states
inside a composite) are written relative to their parent, as draw.io expects, but callers always
pass absolute coordinates.
"""
from __future__ import annotations

import html
import math
import re
import xml.etree.ElementTree as ET

FONT = "Helvetica"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def text_width(s: str, size: float = 11, bold: bool = False) -> float:
    """Rough width of a plain-text line in Helvetica (good enough for overlap checks)."""
    plain = re.sub(r"<[^>]+>", "", s)
    plain = html.unescape(plain)
    w = 0.0
    for ch in plain:
        if ch in "il.,:;|'!()[]{}":
            w += 0.30
        elif ch in "mwMW@%":
            w += 0.86
        elif ch.isupper() or ch in "_#&":
            w += 0.66
        elif ch == " ":
            w += 0.28
        else:
            w += 0.54
    return w * size * (1.07 if bold else 1.0)


class Diagram:
    def __init__(self, name: str, width: int, height: int, grid: bool = True):
        self.name = name
        self.width, self.height = width, height
        self.grid = grid
        self.cells: list[dict] = []
        self.by_id: dict[str, dict] = {}
        self._n = 0

    # ------------------------------------------------------------------ ids
    def _id(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    # ------------------------------------------------------------------ vertices
    def node(self, label: str, x: float, y: float, w: float, h: float, style: str, *, id: str | None = None,
             parent: str | None = None, check: bool = True, label_box: tuple | None = None) -> str:
        """Add a vertex. x, y are absolute; parent (if given) must already exist."""
        cid = id or self._id("v")
        if cid in self.by_id:
            raise ValueError(f"duplicate id {cid}")
        c = dict(kind="v", id=cid, label=label, x=x, y=y, w=w, h=h, style=style, parent=parent, check=check)
        self.cells.append(c)
        self.by_id[cid] = c
        return cid

    def text(self, label: str, x: float, y: float, w: float, h: float, *, size: float = 11, align: str = "left",
             valign: str = "top", bold: bool = False, italic: bool = False, color: str = "#1d1d1d",
             extra: str = "", id: str | None = None, check: bool = True, parent: str | None = None) -> str:
        fs = (1 if bold else 0) + (2 if italic else 0)
        style = (f"text;html=1;whiteSpace=wrap;align={align};verticalAlign={valign};fontSize={size};"
                 f"fontStyle={fs};fontColor={color};spacing=2;overflow=visible;{extra}")
        return self.node(label, x, y, w, h, style, id=id, check=check, parent=parent)

    # ------------------------------------------------------------------ edges
    def edge(self, src: str | None, tgt: str | None, label: str = "", *, style: str = "",
             exit: tuple[float, float] | None = None, entry: tuple[float, float] | None = None,
             points: list[tuple[float, float]] | None = None, label_x: float = 0.0,
             label_dx: float = 0.0, label_dy: float = 0.0, src_pt: tuple | None = None,
             tgt_pt: tuple | None = None, id: str | None = None, check: bool = True,
             label_size: float = 10.5, label_w: float | None = None) -> str:
        """Add an edge.

        exit / entry are (fx, fy) fractions of the source / target bounding box (0..1).
        src_pt / tgt_pt are absolute points used when there is no source / target cell.
        label_x is draw.io's relative label position (-1 = source end, 0 = middle, 1 = target end);
        label_dx / label_dy shift the label from that point.
        """
        cid = id or self._id("e")
        full = style
        if exit is not None:
            full += f";exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;exitPerimeter=0"
        if entry is not None:
            full += f";entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;entryPerimeter=0"
        c = dict(kind="e", id=cid, src=src, tgt=tgt, label=label, style=full.strip(";"), exit=exit, entry=entry,
                 points=list(points or []), label_x=label_x, label_dx=label_dx, label_dy=label_dy,
                 src_pt=src_pt, tgt_pt=tgt_pt, check=check, label_size=label_size, label_w=label_w)
        self.cells.append(c)
        self.by_id[cid] = c
        return cid

    # ------------------------------------------------------------------ geometry helpers
    def box(self, cid: str) -> tuple[float, float, float, float]:
        c = self.by_id[cid]
        return c["x"], c["y"], c["x"] + c["w"], c["y"] + c["h"]

    def _port(self, cid: str, frac, toward) -> tuple[float, float]:
        c = self.by_id[cid]
        if frac is not None:
            return c["x"] + frac[0] * c["w"], c["y"] + frac[1] * c["h"]
        # draw.io default: perimeter point on the line from the centre towards the next point
        cx, cy = c["x"] + c["w"] / 2, c["y"] + c["h"] / 2
        tx, ty = toward
        dx, dy = tx - cx, ty - cy
        if dx == 0 and dy == 0:
            return cx, cy
        sx = (c["w"] / 2) / abs(dx) if dx else math.inf
        sy = (c["h"] / 2) / abs(dy) if dy else math.inf
        s = min(sx, sy)
        return cx + dx * s, cy + dy * s

    def route(self, e: dict) -> list[tuple[float, float]]:
        pts = e["points"]
        if e["src"]:
            sc = self.by_id[e["src"]]
            nxt = pts[0] if pts else (e["tgt_pt"] or self._centre(e["tgt"]))
            p0 = self._port(e["src"], e["exit"], nxt)
        else:
            p0 = e["src_pt"]
        if e["tgt"]:
            prv = pts[-1] if pts else p0
            p1 = self._port(e["tgt"], e["entry"], prv)
        else:
            p1 = e["tgt_pt"]
        return [p0, *pts, p1]

    def _centre(self, cid):
        c = self.by_id[cid]
        return c["x"] + c["w"] / 2, c["y"] + c["h"] / 2

    def label_box(self, e: dict):
        if not e["label"]:
            return None
        r = self.route(e)
        seglens = [math.dist(a, b) for a, b in zip(r, r[1:])]
        total = sum(seglens) or 1
        target = (e["label_x"] + 1) / 2 * total
        acc = 0.0
        px, py = r[0]
        for (a, b), L in zip(zip(r, r[1:]), seglens):
            if acc + L >= target and L > 0:
                t = (target - acc) / L
                px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                break
            acc += L
        else:
            px, py = r[-1]
        px += e["label_dx"]
        py += e["label_dy"]
        lines = re.split(r"<br\s*/?>|\n", e["label"])
        w = e["label_w"] or max(text_width(l, e["label_size"]) for l in lines) + 6
        h = len(lines) * (e["label_size"] * 1.25) + 2
        return px - w / 2, py - h / 2, px + w / 2, py + h / 2

    # ------------------------------------------------------------------ checks
    @staticmethod
    def _seg_hits_rect(p, q, r) -> bool:
        (x1, y1), (x2, y2) = p, q
        rx1, ry1, rx2, ry2 = r
        dx, dy = x2 - x1, y2 - y1
        t0, t1 = 0.0, 1.0
        for pp, qq in ((-dx, x1 - rx1), (dx, rx2 - x1), (-dy, y1 - ry1), (dy, ry2 - y1)):
            if pp == 0:
                if qq < 0:
                    return False
            else:
                t = qq / pp
                if pp < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
                if t0 > t1:
                    return False
        return t1 - t0 > 1e-6

    @staticmethod
    def _overlap(a, b, pad=0.0) -> bool:
        return a[0] < b[2] - pad and b[0] < a[2] - pad and a[1] < b[3] - pad and b[1] < a[3] - pad

    def _ancestors(self, cid):
        out = set()
        c = self.by_id.get(cid)
        while c and c.get("parent"):
            out.add(c["parent"])
            c = self.by_id.get(c["parent"])
        return out

    def check(self, shrink: float = 2.0) -> list[str]:
        """Return a list of layout problems (empty list = clean)."""
        problems = []
        verts = [c for c in self.cells if c["kind"] == "v" and c["check"]]
        edges = [c for c in self.cells if c["kind"] == "e" and c["check"]]
        # 1. edge segments through unrelated vertices
        for e in edges:
            ends = {e["src"], e["tgt"]} - {None}
            skip = set(ends)
            for end in ends:
                skip |= self._ancestors(end)
            r = self.route(e)
            for v in verts:
                if v["id"] in skip:
                    continue
                if any(v["id"] in self._ancestors(end) for end in ends):
                    continue
                if v.get("pass_through"):
                    continue
                vb = self.box(v["id"])
                if v.get("container") and all(vb[0] <= px <= vb[2] and vb[1] <= py <= vb[3] for px, py in self.route(e)):
                    continue                     # edge drawn entirely inside a container does not cross it
                vb = (vb[0] + shrink, vb[1] + shrink, vb[2] - shrink, vb[3] - shrink)
                for p, q in zip(r, r[1:]):
                    if self._seg_hits_rect(p, q, vb):
                        problems.append(f"edge {e['id']} ({e['label'][:30]!r}) crosses {v['id']} ({v['label'][:30]!r})")
                        break
        # 2. labels over vertices and over other labels
        lbs = [(e, self.label_box(e)) for e in edges if e["label"]]
        for e, lb in lbs:
            for v in verts:
                if (v.get("container") and not v.get("label_block")) or v.get("no_label_check"):
                    continue
                if self._overlap(lb, self.box(v["id"]), pad=1):
                    problems.append(f"label of {e['id']} ({e['label'][:30]!r}) overlaps {v['id']} ({v['label'][:30]!r})")
        for i in range(len(lbs)):
            for j in range(i + 1, len(lbs)):
                if self._overlap(lbs[i][1], lbs[j][1], pad=1):
                    problems.append(f"labels overlap: {lbs[i][0]['id']} {lbs[i][0]['label'][:25]!r} / "
                                    f"{lbs[j][0]['id']} {lbs[j][0]['label'][:25]!r}")
        # 3. vertices overlapping (siblings only, ignoring containers/text marked unchecked)
        for i in range(len(verts)):
            for j in range(i + 1, len(verts)):
                a, b = verts[i], verts[j]
                if a["id"] in self._ancestors(b["id"]) or b["id"] in self._ancestors(a["id"]):
                    continue
                ba, bb = self.box(a["id"]), self.box(b["id"])
                if (a.get("container") and ba[0] <= bb[0] and ba[1] <= bb[1] and bb[2] <= ba[2] and bb[3] <= ba[3]) or                    (b.get("container") and bb[0] <= ba[0] and bb[1] <= ba[1] and ba[2] <= bb[2] and ba[3] <= bb[3]):
                    continue                     # fully inside a container: placement, not overlap
                if self._overlap(self.box(a["id"]), self.box(b["id"]), pad=1):
                    problems.append(f"shapes overlap: {a['id']} {a['label'][:25]!r} / {b['id']} {b['label'][:25]!r}")
        # 4. everything on the page
        for c in verts:
            x1, y1, x2, y2 = self.box(c["id"])
            if x1 < 0 or y1 < 0 or x2 > self.width or y2 > self.height:
                problems.append(f"{c['id']} {c['label'][:25]!r} is outside the page")
        return problems

    def mark_container(self, cid: str, pass_through: bool = False):
        """Mark a vertex as a container; pass_through=True lets edges cross its border (e.g. a subsystem)."""
        self.by_id[cid]["container"] = True
        self.by_id[cid]["pass_through"] = pass_through

    # ------------------------------------------------------------------ output
    def xml(self) -> str:
        mxfile = ET.Element("mxfile", host="Electron", agent="Digital Mohalla design generator", version="24.7.17",
                            type="device")
        dg = ET.SubElement(mxfile, "diagram", id=re.sub(r"\W", "_", self.name)[:40], name=self.name)
        model = ET.SubElement(dg, "mxGraphModel", dx="1400", dy="900", grid="1" if self.grid else "0", gridSize="10",
                              guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1",
                              pageWidth=str(self.width), pageHeight=str(self.height), math="0", shadow="0",
                              background="#FFFFFF")
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")
        for c in self.cells:
            parent = c.get("parent") or "1"
            if c["kind"] == "v":
                cell = ET.SubElement(root, "mxCell", id=c["id"], value=c["label"], style=c["style"], vertex="1",
                                     parent=parent)
                x, y = c["x"], c["y"]
                if c.get("parent"):
                    p = self.by_id[c["parent"]]
                    x, y = x - p["x"], y - p["y"]
                ET.SubElement(cell, "mxGeometry", x=_f(x), y=_f(y), width=_f(c["w"]), height=_f(c["h"]),
                              **{"as": "geometry"})
            else:
                attrs = dict(id=c["id"], value=c["label"], style=c["style"], edge="1", parent="1")
                if c["src"]:
                    attrs["source"] = c["src"]
                if c["tgt"]:
                    attrs["target"] = c["tgt"]
                cell = ET.SubElement(root, "mxCell", **attrs)
                geo_attrs = {"relative": "1", "as": "geometry"}
                if c["label_x"]:
                    geo_attrs["x"] = _f(c["label_x"])
                geo = ET.SubElement(cell, "mxGeometry", **geo_attrs)
                if c["src_pt"]:
                    ET.SubElement(geo, "mxPoint", x=_f(c["src_pt"][0]), y=_f(c["src_pt"][1]), **{"as": "sourcePoint"})
                if c["tgt_pt"]:
                    ET.SubElement(geo, "mxPoint", x=_f(c["tgt_pt"][0]), y=_f(c["tgt_pt"][1]), **{"as": "targetPoint"})
                if c["points"]:
                    arr = ET.SubElement(geo, "Array", **{"as": "points"})
                    for px, py in c["points"]:
                        ET.SubElement(arr, "mxPoint", x=_f(px), y=_f(py))
                if c["label_dx"] or c["label_dy"]:
                    ET.SubElement(geo, "mxPoint", x=_f(c["label_dx"]), y=_f(c["label_dy"]), **{"as": "offset"})
        ET.indent(mxfile, space="  ")
        return ET.tostring(mxfile, encoding="unicode")

    def save(self, path: str, strict: bool = True) -> list[str]:
        problems = self.check()
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(self.xml())
        # round-trip parse to prove the file is well-formed and every edge end exists
        tree = ET.parse(path)
        ids = {c.get("id") for c in tree.iter("mxCell")}
        for c in tree.iter("mxCell"):
            for k in ("source", "target", "parent"):
                if c.get(k) and c.get(k) not in ids:
                    raise ValueError(f"{path}: {c.get('id')} has dangling {k}={c.get(k)}")
        print(f"{path}: {sum(1 for c in self.cells if c['kind'] == 'v')} shapes, "
              f"{sum(1 for c in self.cells if c['kind'] == 'e')} edges, {len(problems)} layout problems")
        for p in problems:
            print("   ", p)
        if strict and problems:
            raise SystemExit(f"layout problems in {path}")
        return problems


def save_pages(path: str, diagrams: list, strict: bool = True) -> list[str]:
    """Write several Diagram objects as the pages of one .drawio file; every page is layout-checked."""
    problems = []
    mxfile = ET.Element("mxfile", host="Electron", agent="Digital Mohalla design generator", version="24.7.17",
                        type="device", pages=str(len(diagrams)))
    for d in diagrams:
        page_problems = [f"[{d.name}] {p}" for p in d.check()]
        problems += page_problems
        page = ET.fromstring(d.xml()).find("diagram")
        page.set("id", f"p{len(mxfile)}_" + page.get("id"))
        mxfile.append(page)
    ET.indent(mxfile, space="  ")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(ET.tostring(mxfile, encoding="unicode"))
    ET.parse(path)
    print(f"{path}: {len(diagrams)} pages, {sum(len(d.cells) for d in diagrams)} cells, {len(problems)} layout problems")
    for p in problems:
        print("   ", p)
    if strict and problems:
        raise SystemExit(f"layout problems in {path}")
    return problems


def _f(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}"


# ---------------------------------------------------------------------- shared styles
def style(**kw) -> str:
    return ";".join(f"{k}={v}" for k, v in kw.items()) + ";"


EDGE_BASE = "html=1;rounded=0;fontSize=10.5;labelBackgroundColor=#FFFFFF;fontColor=#1d1d1d;endSize=8;"
