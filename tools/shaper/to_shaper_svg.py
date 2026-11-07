# /// script
# requires-python = ">=3.11"
# dependencies = ["ezdxf>=1.3"]
# ///
"""Convert a DXF (a SolidCraft sketch, flat pattern or view) into an SVG that Shaper Origin
reads with the right cut types.

    uv run tools/shaper/to_shaper_svg.py part.dxf [-o part.shaper.svg] [--depth 6.35] [--layer-map POCKET=pocket ...]

Shaper's convention (shapertools.com, "SVG cut types"):
  exterior cut   closed path, black fill,  black stroke  -> cut on the outside of the line
  interior cut   closed path, white fill,  black stroke  -> cut on the inside (holes)
  on-line cut    open path,   no fill,     grey stroke   -> cut on the line
  pocket         closed path, grey fill,   no stroke     -> clear the area
  guide          blue stroke                              -> reference only, never cut

Closed loops are classified by nesting: the outermost loop is an exterior cut, a loop inside it is
an interior cut, an island inside a hole is exterior again. Open chains become on-line cuts.
Layers override that: a layer whose name contains POCKET, GUIDE, ONLINE / ETCH / ENGRAVE, is
pocket, guide or on-line (extend with --layer-map NAME=type). Layers HIDDEN, BEND* and
construction layers become guides, so nothing you did not mean to cut is cut.

--depth writes shaper:cutDepth on every cut (mm) so Origin pre-fills the depth.
Output is in millimetres, 1:1, Y up as in CAD.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ezdxf import path as ezpath

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dxf"))
import dxfloops  # noqa: E402

COLORS = {
    "exterior": 'fill="#000000" stroke="#000000"',
    "interior": 'fill="#FFFFFF" stroke="#000000"',
    "online": 'fill="none" stroke="#7F7F7F"',
    "pocket": 'fill="#7F7F7F" stroke="none"',
    "guide": 'fill="none" stroke="#0068FF"',
}
DEFAULT_LAYER_MAP = {
    "POCKET": "pocket", "GUIDE": "guide", "ONLINE": "online", "ETCH": "online", "ENGRAVE": "online",
    "HIDDEN": "guide", "BEND": "guide", "CONSTRUCTION": "guide", "BEND_NOTES": "guide",
}


def layer_kind(layer: str, mapping: dict[str, str]) -> str | None:
    up = layer.upper()
    for key, kind in mapping.items():
        if key in up:
            return kind
    return None


def svg_d(p: ezpath.Path, ox: float, top: float) -> str:
    def P(v):
        return f"{v.x - ox:.4f} {top - v.y:.4f}"
    parts = [f"M{P(p.start)}"]
    for cmd in p.commands():
        if cmd.type == ezpath.Command.LINE_TO:
            parts.append(f"L{P(cmd.end)}")
        elif cmd.type == ezpath.Command.CURVE3_TO:
            parts.append(f"Q{P(cmd.ctrl)} {P(cmd.end)}")
        elif cmd.type == ezpath.Command.CURVE4_TO:
            parts.append(f"C{P(cmd.ctrl1)} {P(cmd.ctrl2)} {P(cmd.end)}")
        elif cmd.type == ezpath.Command.MOVE_TO:
            parts.append(f"M{P(cmd.end)}")
    if p.is_closed:
        parts.append("Z")
    return "".join(parts)


def convert(src: Path, dst: Path, depth: float | None, mapping: dict[str, str]) -> dict:
    by_layer, _skipped = dxfloops.read_paths(src)
    by_kind: dict[str | None, list[ezpath.Path]] = {}
    for layer, paths in by_layer.items():
        by_kind.setdefault(layer_kind(layer, mapping), []).extend(paths)

    items = []  # (kind, path)
    for forced, paths in by_kind.items():
        chains = dxfloops.chain(paths)
        if forced:
            items += [(forced, c) for c in chains]
            continue
        items += [("online", c) for c in chains if not c.is_closed]
        loops = dxfloops.classify([(c, "") for c in chains if c.is_closed])
        items += [("interior" if lp.is_hole else "exterior", lp.path) for lp in loops]

    allpts = [v for _, p in items for v in p.flattening(0.1)]
    if not allpts:
        raise SystemExit(f"{src}: no geometry found")
    minx = min(v.x for v in allpts); maxx = max(v.x for v in allpts)
    miny = min(v.y for v in allpts); maxy = max(v.y for v in allpts)
    pad = 1.0
    ox, top = minx - pad, maxy + pad
    w, h = (maxx - minx) + 2 * pad, (maxy - miny) + 2 * pad

    order = {"exterior": 0, "pocket": 1, "interior": 2, "online": 3, "guide": 4}
    items.sort(key=lambda kp: (order[kp[0]], -dxfloops.polygon(kp[1])[0] if kp[1].is_closed else 0))
    cut_depth = f' shaper:cutDepth="{depth:g}mm"' if depth is not None else ""
    lines = []
    counts: dict[str, int] = {}
    for kind, p in items:
        counts[kind] = counts.get(kind, 0) + 1
        extra = cut_depth if kind != "guide" else ""
        lines.append(f'  <path d="{svg_d(p, ox, top)}" {COLORS[kind]} stroke-width="0.2"{extra}/>')
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:shaper="http://www.shapertools.com/namespaces/shaper" '
           f'width="{w:.3f}mm" height="{h:.3f}mm" viewBox="0 0 {w:.3f} {h:.3f}">\n'
           + "\n".join(lines) + "\n</svg>\n")
    dst.write_text(svg)
    return {"out": str(dst), "size_mm": [round(w - 2 * pad, 3), round(h - 2 * pad, 3)], "counts": counts}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--depth", type=float, help="cut depth in mm, written as shaper:cutDepth")
    ap.add_argument("--layer-map", nargs="*", default=[], metavar="LAYER=kind")
    a = ap.parse_args()
    mapping = dict(DEFAULT_LAYER_MAP)
    for item in a.layer_map:
        k, v = item.split("=", 1)
        assert v in COLORS, f"kind must be one of {list(COLORS)}"
        mapping[k.upper()] = v
    out = a.out or a.dxf.with_suffix(".shaper.svg")
    print(convert(a.dxf, out, a.depth, mapping))


if __name__ == "__main__":
    main()
