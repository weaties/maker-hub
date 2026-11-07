# /// script
# requires-python = ">=3.11"
# dependencies = ["ezdxf>=1.3"]
# ///
"""Check a DXF before plasma CAM, and write a clean R12 copy CAM programs read reliably.

    uv run tools/plasma/check_dxf.py part.dxf --thickness 3.2 [--table 711x812] [--out part.plasma.dxf]

Checks (errors make the exit status 1):
  ERROR  open contours          plasma cuts closed profiles; an open chain is usually a missing segment
  ERROR  near-miss gaps         two ends 0.01-0.5 mm apart: drawn to meet but don't
  ERROR  larger than the table  outer profile bigger than the cutting area (default JD's Garage
                                Gen 2.0: 28 x 32 in = 711 x 812 mm)
  WARN   small holes            hole narrower than --min-hole x thickness (default 1.0): a plasma
                                hole that small comes out tapered and undersize; drill it instead
  WARN   narrow webs / slots    distance between a hole and the outline, or a slot width, under the
                                thickness: it will burn through or warp
  WARN   text / blocks          TEXT, MTEXT and INSERT are skipped: explode text to outlines first
  INFO   kerf                   reminder: CAM applies kerf compensation (~1.5 mm at 40-45 A); never offset by hand

The clean copy (`--out`): R12 (AC1009), one closed POLYLINE per profile, curves flattened within
0.05 mm (far below the ~1.5 mm kerf; turn on arc fitting in CAM if the controller stutters on short
segments), outer profiles on layer OUTSIDE and holes on layer INSIDE so CAM can pick cut order and
lead-in side by layer.
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path

import ezdxf
from ezdxf import path as ezpath

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dxf"))
import dxfloops  # noqa: E402

TABLE_DEFAULT = "711x812"


def gaps(chains: list[ezpath.Path], tol=dxfloops.TOL, near=0.5):
    """Open-chain ends that nearly meet another open end."""
    ends = []
    for i, c in enumerate(chains):
        if not c.is_closed:
            ends += [(i, c.start), (i, c.end)]
    out = []
    for a in range(len(ends)):
        for b in range(a + 1, len(ends)):
            (ia, pa), (ib, pb) = ends[a], ends[b]
            d = pa.distance(pb)
            if tol < d <= near and not (ia == ib and len(chains[ia]) <= 1):
                out.append(((pa.x, pa.y), d))
    return out


def seg_dist(p, a, b) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def min_dist(hole, outline) -> float:
    """Smallest distance from the hole's outline to the other outline's edges (flattened at 0.05 mm)."""
    pts = hole[:: max(1, len(hole) // 200)]
    segs = list(zip(outline, outline[1:] + outline[:1]))
    return min(seg_dist(p, a, b) for p in pts for a, b in segs)


def write_r12(loops, open_chains, dst: Path):
    logging.getLogger("ezdxf").setLevel(logging.ERROR)  # R12 has no units header; mm is implied
    doc = ezdxf.new("R12")
    for name, color in (("OUTSIDE", 7), ("INSIDE", 1), ("OPEN", 2)):
        doc.layers.add(name, color=color)
    msp = doc.modelspace()
    items = [(("INSIDE" if lp.is_hole else "OUTSIDE"), lp.path) for lp in loops]
    items += [("OPEN", c) for c in open_chains]
    for layer, p in items:
        pts = [(v.x, v.y) for v in p.flattening(0.05)]
        if p.is_closed and len(pts) > 1 and math.dist(pts[0], pts[-1]) < 1e-6:
            pts = pts[:-1]
        msp.add_polyline2d(pts, close=p.is_closed, dxfattribs={"layer": layer})
    doc.saveas(dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf", type=Path)
    ap.add_argument("--thickness", type=float, required=True, help="material thickness, mm")
    ap.add_argument("--table", default=TABLE_DEFAULT, help="cutting area WxH in mm (default %(default)s)")
    ap.add_argument("--min-hole", type=float, default=1.0, help="smallest hole as a multiple of thickness")
    ap.add_argument("--out", type=Path, help="write a clean R12 copy here")
    a = ap.parse_args()

    by_layer, skipped = dxfloops.read_paths(a.dxf)
    paths = [p for ps in by_layer.values() for p in ps]
    chains = dxfloops.chain(paths)
    open_chains = [c for c in chains if not c.is_closed]
    loops = dxfloops.classify([(c, "") for c in chains if c.is_closed])
    errors, warns = [], []

    if open_chains:
        errors.append(f"{len(open_chains)} open contour(s): first starts at "
                      f"({open_chains[0].start.x:.2f}, {open_chains[0].start.y:.2f})")
    for (x, y), d in gaps(chains)[:10]:
        errors.append(f"gap of {d:.3f} mm near ({x:.2f}, {y:.2f})")

    tw, th = (float(v) for v in a.table.lower().split("x"))
    outers = [lp for lp in loops if not lp.is_hole]
    for lp in outers:
        x0, y0, x1, y1 = lp.bbox
        w, h = x1 - x0, y1 - y0
        if not ((w <= tw and h <= th) or (w <= th and h <= tw)):
            errors.append(f"part {w:.0f} x {h:.0f} mm is larger than the {tw:.0f} x {th:.0f} mm table")

    t = a.thickness
    for lp in loops:
        if not lp.is_hole:
            continue
        x0, y0, x1, y1 = lp.bbox
        narrow = min(x1 - x0, y1 - y0)
        where = f"at ({(x0 + x1) / 2:.1f}, {(y0 + y1) / 2:.1f})"
        if narrow < a.min_hole * t:
            warns.append(f"hole/slot {narrow:.2f} mm wide {where} is under {a.min_hole:g} x {t:g} mm: drill or enlarge")
        parent = min((o for o in loops if o.depth == lp.depth - 1 and dxfloops.inside(lp.poly[0], o.poly)),
                     key=lambda o: o.area, default=None)
        if parent is not None:
            web = min_dist(lp.poly, parent.poly)
            if web < t:
                warns.append(f"web of {web:.2f} mm between the hole {where} and the outline (< {t:g} mm thickness)")
    if skipped:
        kinds = sorted(set(skipped))
        warns.append(f"skipped {len(skipped)} entities ({', '.join(kinds)}): explode text/blocks to outlines")

    print(f"{a.dxf.name}: {len(outers)} part outline(s), {sum(lp.is_hole for lp in loops)} hole(s), "
          f"{len(open_chains)} open chain(s); thickness {t:g} mm, table {tw:.0f} x {th:.0f} mm")
    for e in errors:
        print("  ERROR", e)
    for w in warns:
        print("  WARN ", w)
    print("  INFO  kerf compensation belongs in CAM (about 1.5 mm at 40-45 A); don't offset the drawing")
    if a.out:
        write_r12(loops, open_chains, a.out)
        print(f"  wrote {a.out} (R12: OUTSIDE / INSIDE / OPEN layers)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
