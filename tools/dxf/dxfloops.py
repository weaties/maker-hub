"""Shared DXF geometry helpers for the hub's 2D tools (Shaper SVG, plasma checks).

Reads a DXF's cut geometry as ezdxf Paths, joins open pieces into chains, and classifies
closed loops as outer profiles or holes by nesting. Import from a uv script with:

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dxf"))
    import dxfloops
"""

from __future__ import annotations

from dataclasses import dataclass, field

import ezdxf
from ezdxf import path as ezpath

TOL = 0.01  # mm: ends closer than this are the same point
SKIP_TYPES = ("TEXT", "MTEXT", "DIMENSION", "INSERT", "POINT", "HATCH", "ATTRIB", "ATTDEF")


@dataclass
class Loop:
    path: ezpath.Path
    layer: str
    area: float = 0.0
    poly: list[tuple[float, float]] = field(default_factory=list)
    depth: int = 0  # nesting: 0 outer profile, 1 hole, 2 island in a hole, ...

    @property
    def is_hole(self) -> bool:
        return self.depth % 2 == 1

    @property
    def bbox(self):
        xs = [p[0] for p in self.poly]
        ys = [p[1] for p in self.poly]
        return min(xs), min(ys), max(xs), max(ys)


def read_paths(src) -> tuple[dict[str, list[ezpath.Path]], list[str]]:
    """Paths grouped by layer, plus the entity types that were skipped (text, blocks, ...)."""
    doc = ezdxf.readfile(src)
    by_layer: dict[str, list[ezpath.Path]] = {}
    skipped: list[str] = []
    for e in doc.modelspace():
        if e.dxftype() in SKIP_TYPES:
            skipped.append(e.dxftype())
            continue
        try:
            p = ezpath.make_path(e)
        except (TypeError, ValueError):
            skipped.append(e.dxftype())
            continue
        if len(p) == 0:
            continue
        by_layer.setdefault(e.dxf.layer, []).append(p)
    return by_layer, skipped


def joined(a: ezpath.Path, b: ezpath.Path) -> ezpath.Path:
    out = a.clone()
    out.append_path(b)
    return out


def chain(paths: list[ezpath.Path], tol: float = TOL) -> list[ezpath.Path]:
    """Join open paths whose ends meet into longer paths, closed when they come back."""
    done, open_ = [], []
    for p in paths:
        (done if p.is_closed else open_).append(p)
    while open_:
        cur = open_.pop()
        grown = True
        while grown and not cur.is_closed:
            grown = False
            for i, q in enumerate(open_):
                if cur.end.isclose(q.start, abs_tol=tol):
                    cur = joined(cur, q)
                elif cur.end.isclose(q.end, abs_tol=tol):
                    cur = joined(cur, q.reversed())
                elif cur.start.isclose(q.end, abs_tol=tol):
                    cur = joined(q, cur)
                elif cur.start.isclose(q.start, abs_tol=tol):
                    cur = joined(q.reversed(), cur)
                else:
                    continue
                open_.pop(i)
                grown = True
                break
            if len(cur) > 0 and cur.start.isclose(cur.end, abs_tol=tol):
                cur.close()
        done.append(cur)
    return done


def polygon(p: ezpath.Path, distance: float = 0.05) -> tuple[float, list[tuple[float, float]]]:
    """Unsigned area and the flattened outline."""
    pts = [(v.x, v.y) for v in p.flattening(distance)]
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2, pts


def inside(pt, poly) -> bool:
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def classify(closed: list[tuple[ezpath.Path, str]]) -> list[Loop]:
    """Nesting depth of each closed loop among the others."""
    loops = []
    for p, layer in closed:
        a, poly = polygon(p)
        loops.append(Loop(p, layer, a, poly))
    for i, lp in enumerate(loops):
        probe = lp.poly[0]
        lp.depth = sum(1 for j, other in enumerate(loops)
                       if j != i and other.area > lp.area and inside(probe, other.poly))
    return loops
