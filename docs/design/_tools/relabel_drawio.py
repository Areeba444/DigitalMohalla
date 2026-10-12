"""Replace text inside the labels of a hand-drawn .drawio file (uncompressed XML), keeping its geometry.

Used during integration to bring hand-drawn diagrams in line with the baseline without redrawing them:

    python _tools/relabel_drawio.py FILE.drawio REPLACEMENTS.json

REPLACEMENTS.json is a list of [old, new] pairs. Each `old` must occur in at least one label (the
unescaped `value` attribute); the run fails and changes nothing if any pair matches no label.
"""
import json
import sys
import xml.etree.ElementTree as ET


def relabel(path, pairs):
    tree = ET.parse(path)
    cells = [c for c in tree.getroot().iter() if c.get("value") is not None]
    hits = [0] * len(pairs)
    for c in cells:
        v = c.get("value")
        for i, (old, new) in enumerate(pairs):
            if old in v:
                v = v.replace(old, new)
                hits[i] += 1
        c.set("value", v)
    missing = [pairs[i][0] for i, h in enumerate(hits) if h == 0]
    if missing:
        raise SystemExit(f"{path}: not found: {missing}")
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=False)
    return sum(hits)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    n = relabel(sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8")))
    print(f"{sys.argv[1]}: {n} label replacements")
