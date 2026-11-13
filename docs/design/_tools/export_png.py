"""Exports a PNG next to every current .drawio file of the design set, so large diagrams can be read without draw.io.

    python _tools/export_png.py                 (from docs/design; all diagrams, archive_v1/ skipped)
    python _tools/export_png.py 05_class_model  (one folder)

Needs draw.io desktop (https://github.com/jgraph/drawio-desktop). The .drawio file stays the source: never edit a PNG,
change the generator, run it, then run this script. Each page is exported at scale 2 with a white background, so text
stays sharp when zoomed, then reduced to a 256-colour palette without dithering when Pillow is installed (about a
quarter of the size; diagrams use few colours, so nothing visible is lost). A one-page diagram gives <name>.png; a
diagram with pages gives <name>_p1.png, <name>_p2.png ...
Very large pages are exported at a smaller scale (draw.io stops drawing above about 30 million pixels; every PNG is
checked for this and re-exported smaller if cut off), and those pages also get a vector PDF beside the PNG.
A PNG with no .drawio beside it any more is reported, not deleted.
"""
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SCALE = 2.0
MAX_AREA = 28e6            # px: draw.io stops rendering very large pages part-way, so big pages get a smaller scale
PDF_BELOW = 1.5            # pages exported below this scale also get a vector PDF, sharp at any zoom
CANDIDATES = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "draw.io", "draw.io.exe"),
    r"C:\Program Files\draw.io\draw.io.exe",
    "/Applications/draw.io.app/Contents/MacOS/draw.io",
    shutil.which("drawio") or "",
    shutil.which("draw.io") or "",
]


def drawio_exe() -> str:
    for c in CANDIDATES:
        if c and os.path.exists(c):
            return c
    sys.exit("draw.io desktop not found; install it or add 'drawio' to PATH")


def diagrams(start: str):
    for dp, dirs, files in os.walk(start):
        dirs[:] = sorted(d for d in dirs if d != "archive_v1" and not d.startswith((".", "_")))
        for f in sorted(files):
            if f.endswith(".drawio"):
                yield os.path.join(dp, f)


def compress(path: str) -> None:
    try:
        from PIL import Image
    except ImportError:                     # optional: the full-colour PNG is kept
        return
    with Image.open(path) as im:
        q = im.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q.save(path, optimize=True)


def pages(path: str) -> int:
    return len(ET.parse(path).getroot().findall("diagram")) or 1


def scale_for(path: str, page: int) -> float:
    model = ET.parse(path).getroot().findall("diagram")[page - 1].find("mxGraphModel")
    w = float(model.get("pageWidth", 0) or 0) if model is not None else 0
    h = float(model.get("pageHeight", 0) or 0) if model is not None else 0
    return min(SCALE, (MAX_AREA / (w * h)) ** 0.5) if w and h else SCALE


def truncated(path: str) -> bool:
    """True when draw.io stopped drawing before the bottom of the page (content ends well above the image bottom)."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return False
    with Image.open(path) as im:
        box = ImageOps.invert(im.convert("L").point(lambda v: 255 if v > 200 else 0)).getbbox()
        return box is None or box[3] < im.height - 60


def export(exe, path, page, out, fmt, scale):
    return subprocess.run([exe, "--export", "--format", fmt, "--scale", f"{scale:.2f}", "--border", "20",
                           "--page-index", str(page), "--output", out, path], capture_output=True, text=True, timeout=300)


def main() -> int:
    exe = drawio_exe()
    start = os.path.join(ROOT, sys.argv[1]) if len(sys.argv) > 1 else ROOT
    made, failed, expected = 0, [], set()
    for path in diagrams(start):
        n = pages(path)
        base = path[:-len(".drawio")]
        for p in range(1, n + 1):
            out = f"{base}.png" if n == 1 else f"{base}_p{p}.png"
            expected.add(os.path.normcase(out))
            s = scale_for(path, p)
            r = export(exe, path, p, out, "png", s)
            while not r.returncode and os.path.exists(out) and truncated(out) and s > 0.8:
                s *= 0.8                                    # retry smaller until the whole page is drawn
                r = export(exe, path, p, out, "png", s)
            if r.returncode or not os.path.exists(out) or truncated(out):
                failed.append(f"{os.path.relpath(path, ROOT)} page {p}: {(r.stderr or r.stdout).strip()[:200] or 'truncated'}")
                continue
            compress(out)
            made += 1
            if s < PDF_BELOW:                               # big page: add a vector copy for zooming
                pdf = out[:-4] + ".pdf"
                export(exe, path, p, pdf, "pdf", 1.0)
                print(f"  {os.path.relpath(out, ROOT)}: scale {s:.2f}; vector copy {os.path.basename(pdf)}")
    stale = [os.path.relpath(os.path.join(dp, f), ROOT) for dp, _, fs in os.walk(start) if "archive_v1" not in dp
             for f in fs if f.endswith(".png") and f[:-4].rsplit("_p", 1)[0] + ".drawio" in fs
             and os.path.normcase(os.path.join(dp, f)) not in expected]
    print(f"{made} PNG pages written")
    for s in stale:
        print(f"  stale PNG (its diagram has fewer pages now): {s}")
    for f in failed:
        print(f"  FAILED {f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
