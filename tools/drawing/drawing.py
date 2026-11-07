# /// script
# requires-python = ">=3.11"
# dependencies = ["ezdxf>=1.3"]
# ///
"""Make dimensioned 2D drawing sheets (SVG, plus PDF/PNG when rsvg-convert exists) from a
SolidCraft design.

SolidCraft has no drafting workspace yet. It can export orthographic projections of the
visible bodies as DXF (`file.export_view_dxf`, hidden lines dashed). This tool asks the CLI for
those views, then lays them out on a sheet with a title block, dimensions and notes from a spec.

    uv run tools/drawing/drawing.py <part folder>/drawing.json

Spec (paths are relative to the spec file):

{
  "design": "part.sc",
  "out": "out/drawing",                  # -> out/drawing-<sheet>.svg (+ .pdf, .png)
  "title": "Pi 5 case", "part_no": "EL-001", "material": "PETG", "author": "DW",
  "sheets": [{
    "name": "base", "title": "Base", "size": "A3", "scale": 2,
    "hide": ["Lid"],                      # bodies hidden on this sheet
    "views": [
      {"name": "TOP",   "view": "top",   "at": [120, 110], "hidden": false},
      {"name": "FRONT", "view": "front", "at": [120, 200], "hidden": true}
    ],
    "dims": [
      # linear: a, b are view coordinates in model mm (x right, y up in that view).
      {"view": "TOP", "a": [-45.5, 31], "b": [45.5, 31], "dir": "h", "off": 8},
      {"view": "TOP", "a": [45.5, -31], "b": [45.5, 31], "dir": "v", "off": 8, "text": "62"},
      # note with an optional leader to a point
      {"view": "TOP", "note": "4x BOSS Ø6, PILOT Ø2.2", "at": [-30, 40], "to": [-39, 24.5]}
    ],
    "notes": ["GENERAL NOTE ONE", "..."], "notes_at": [15, 270],   # sheet mm
    # a view may also take "label_dy" (sheet mm) to push its name below dimensions
    "image": {"path": "out/snap.png", "at": [300, 30], "width": 100}   # optional picture
  }]
}

View coordinates: target is the world origin, so `top` is (x, y), `front` is (x, z),
`right` (from +X) is (y, z), `left` (from -X) is (-y, z), `back` is (-x, z), `bottom` is (x, -y).
"""

from __future__ import annotations

import base64
import json
import math
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import ezdxf

HUB = Path(__file__).resolve().parents[2]
CLI = HUB / "tools" / "bin" / "solidcraft-cli"

PI = math.pi
CAMERAS = {
    "front": (0.0, 0.0),
    "back": (PI, 0.0),
    "right": (-PI / 2, 0.0),
    "left": (PI / 2, 0.0),
    "top": (0.0, PI / 2),
    "bottom": (0.0, -PI / 2),
}
SHEETS = {"A4": (297, 210), "A3": (420, 297), "A2": (594, 420), "LETTER": (279.4, 215.9), "TABLOID": (431.8, 279.4)}

INK = "#1b1f24"
DIM = "#2556a3"
HID = "#7b8794"


def export_views(design: Path, sheet: dict, workdir: Path) -> dict[str, Path]:
    cmds = [{"command": "browser.visibility", "params": {"visible": False, "folder": "sketches"}}]
    if sheet.get("hide"):
        cmds.append({"command": "browser.visibility", "params": {"visible": False, "items": sheet["hide"]}})
    files = {}
    for v in sheet["views"]:
        yaw, pitch = CAMERAS[v["view"]]
        out = workdir / f"{sheet['name']}-{v['name']}.dxf"
        files[v["name"]] = out
        cmds.append({"command": "file.export_view_dxf", "params": {
            "camera": {"target": [0, 0, 0], "yaw": yaw, "pitch": pitch, "distance": 2000, "fov": 0},
            "hidden": "dashed" if v.get("hidden") else "omit",
            "tolerance": 0.01,
            "path": str(out)}})
    script = workdir / f"{sheet['name']}-views.json"
    script.write_text(json.dumps({"commands": cmds}))
    subprocess.run([str(CLI), "run", str(script), "--in", str(design), "--quiet"], check=True)
    return files


def read_segments(path: Path):
    doc = ezdxf.readfile(path)
    segs = []  # (x1, y1, x2, y2, hidden)
    for e in doc.modelspace():
        hidden = e.dxf.layer.upper() == "HIDDEN"
        if e.dxf.layer.upper() == "SKETCH":
            continue
        if e.dxftype() == "LINE":
            segs.append((e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y, hidden))
        elif e.dxftype() == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points()]
            if e.closed and pts:
                pts.append(pts[0])
            for (a, b) in zip(pts, pts[1:]):
                segs.append((a[0], a[1], b[0], b[1], hidden))
    return segs


class Sheet:
    def __init__(self, spec: dict, sheet: dict):
        self.spec, self.sheet = spec, sheet
        self.w, self.h = SHEETS[sheet.get("size", "A3").upper()]
        self.s = float(sheet.get("scale", 1))
        self.places = {v["name"]: v["at"] for v in sheet["views"]}
        self.out: list[str] = []

    def P(self, view: str, x: float, y: float):
        ox, oy = self.places[view]
        return ox + x * self.s, oy - y * self.s

    def add(self, s: str):
        self.out.append(s)

    # --- geometry -------------------------------------------------------------------------
    def view(self, name: str, segs, label_dy: float = 0):
        vis = []
        hid = []
        for x1, y1, x2, y2, hidden in segs:
            a, b = self.P(name, x1, y1), self.P(name, x2, y2)
            (hid if hidden else vis).append(f"M{a[0]:.3f} {a[1]:.3f}L{b[0]:.3f} {b[1]:.3f}")
        if hid:
            self.add(f'<path d="{"".join(hid)}" stroke="{HID}" stroke-width="0.18" stroke-dasharray="1.2 0.8" fill="none"/>')
        self.add(f'<path d="{"".join(vis)}" stroke="{INK}" stroke-width="0.35" fill="none" stroke-linecap="round"/>')
        xs = [c for s in segs for c in (s[0], s[2])]
        ys = [c for s in segs for c in (s[1], s[3])]
        if xs:
            lx, ly = self.P(name, (min(xs) + max(xs)) / 2, min(ys))
            self.add(self.text(lx, ly + 9 + label_dy, name, 3.2, "middle", bold=True))
            self.add(self.text(lx, ly + 13.5 + label_dy, f"SCALE {self.scale_label()}", 2.2, "middle", color=HID))

    def scale_label(self):
        return f"{self.s:g}:1" if self.s >= 1 else f"1:{1 / self.s:g}"

    def text(self, x, y, t, size=2.8, anchor="start", bold=False, color=INK, rotate=None):
        tr = f' transform="rotate({rotate} {x:.3f} {y:.3f})"' if rotate is not None else ""
        w = ' font-weight="700"' if bold else ""
        t = t.replace("&", "&amp;").replace("<", "&lt;")
        return (f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" text-anchor="{anchor}" fill="{color}"'
                f' font-family="Helvetica, Arial, sans-serif"{w}{tr}>{t}</text>')

    def arrow(self, x, y, ang):
        L, Wd = 2.6, 0.9
        c, s = math.cos(ang), math.sin(ang)
        p1 = (x - L * c + Wd * s, y - L * s - Wd * c)
        p2 = (x - L * c - Wd * s, y - L * s + Wd * c)
        return f'<path d="M{x:.3f} {y:.3f}L{p1[0]:.3f} {p1[1]:.3f}L{p2[0]:.3f} {p2[1]:.3f}Z" fill="{DIM}"/>'

    def dim(self, d: dict):
        v = d["view"]
        if "note" in d:
            x, y = self.P(v, *d["at"])
            if "to" in d:
                tx, ty = self.P(v, *d["to"])
                ang = math.atan2(ty - y, tx - x)
                self.add(f'<path d="M{x:.3f} {y:.3f}L{tx:.3f} {ty:.3f}" stroke="{DIM}" stroke-width="0.25"/>')
                self.add(self.arrow(tx, ty, ang))
            anchor = d.get("anchor", "start")
            for i, line in enumerate(d["note"].split("\n")):
                self.add(self.text(x + (1 if anchor == "start" else -1), y - 1 + i * 3.6, line, 2.6, anchor, color=DIM))
            return
        (ax, ay), (bx, by) = d["a"], d["b"]
        horiz = d.get("dir", "h") == "h"
        val = abs(bx - ax) if horiz else abs(by - ay)
        label = d.get("text", f"{val:.2f}".rstrip("0").rstrip("."))
        off = d.get("off", 8)  # sheet mm, sign picks the side (+ above / right)
        A, B = self.P(v, ax, ay), self.P(v, bx, by)
        gap, over = 1.2, 1.8
        if horiz:
            yline = (min(A[1], B[1]) - off) if off > 0 else (max(A[1], B[1]) - off)
            sgn = -1 if off > 0 else 1
            for X, Y in (A, B):
                self.add(f'<path d="M{X:.3f} {Y + sgn * gap:.3f}L{X:.3f} {yline + sgn * over:.3f}" stroke="{DIM}" stroke-width="0.18"/>')
            x1, x2 = sorted((A[0], B[0]))
            self.add(f'<path d="M{x1:.3f} {yline:.3f}L{x2:.3f} {yline:.3f}" stroke="{DIM}" stroke-width="0.25"/>')
            if x2 - x1 > 7:
                self.add(self.arrow(x1, yline, PI))
                self.add(self.arrow(x2, yline, 0))
                tx = (x1 + x2) / 2
            else:  # arrows outside, text beside
                self.add(self.arrow(x1, yline, 0))
                self.add(self.arrow(x2, yline, PI))
                tx = x2 + 2 + len(label) * 1.0
            self.add(self.text(tx, yline - 1, label, 2.8, "middle", color=DIM))
        else:
            xline = (max(A[0], B[0]) + off) if off > 0 else (min(A[0], B[0]) + off)
            sgn = 1 if off > 0 else -1
            for X, Y in (A, B):
                self.add(f'<path d="M{X + sgn * gap:.3f} {Y:.3f}L{xline + sgn * over:.3f} {Y:.3f}" stroke="{DIM}" stroke-width="0.18"/>')
            y1, y2 = sorted((A[1], B[1]))
            self.add(f'<path d="M{xline:.3f} {y1:.3f}L{xline:.3f} {y2:.3f}" stroke="{DIM}" stroke-width="0.25"/>')
            if y2 - y1 > 7:
                self.add(self.arrow(xline, y1, -PI / 2))
                self.add(self.arrow(xline, y2, PI / 2))
                ty = (y1 + y2) / 2
            else:
                self.add(self.arrow(xline, y1, PI / 2))
                self.add(self.arrow(xline, y2, -PI / 2))
                ty = y1 - 2 - len(label) * 1.0
            self.add(self.text(xline - 1, ty, label, 2.8, "middle", color=DIM, rotate=-90))

    # --- furniture ------------------------------------------------------------------------
    def frame(self, sheet_no: int, sheet_count: int):
        w, h, m = self.w, self.h, 10
        self.add(f'<rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}" fill="none" stroke="{INK}" stroke-width="0.6"/>')
        tb_w, tb_h = 150, 32
        x0, y0 = w - m - tb_w, h - m - tb_h
        self.add(f'<rect x="{x0}" y="{y0}" width="{tb_w}" height="{tb_h}" fill="#fff" stroke="{INK}" stroke-width="0.5"/>')
        for yy in (y0 + 14, y0 + 23):
            self.add(f'<path d="M{x0} {yy}L{x0 + tb_w} {yy}" stroke="{INK}" stroke-width="0.25"/>')
        for xx in (x0 + 50, x0 + 100):
            self.add(f'<path d="M{xx} {y0 + 14}L{xx} {y0 + tb_h}" stroke="{INK}" stroke-width="0.25"/>')
        sp, sh = self.spec, self.sheet
        self.add(self.text(x0 + 3, y0 + 6, sp.get("title", ""), 4.2, bold=True))
        self.add(self.text(x0 + 3, y0 + 11.5, sh.get("title", sh["name"]), 3.0, color="#444"))
        self.add(self.text(x0 + tb_w - 3, y0 + 6, sp.get("part_no", ""), 3.4, "end", bold=True))
        cells = [("MATERIAL", sh.get("material", sp.get("material", "—"))), ("SCALE", self.scale_label()),
                 ("SHEET", f"{sheet_no} / {sheet_count}"),
                 ("UNITS", "mm"), ("DRAWN", sp.get("author", "")), ("DATE", sp.get("date", date.today().isoformat()))]
        for i, (k, val) in enumerate(cells):
            cx = x0 + 3 + (i % 3) * 50
            cy = y0 + 17.5 + (i // 3) * 9
            self.add(self.text(cx, cy, k, 1.8, color=HID))
            self.add(self.text(cx, cy + 4, str(val), 2.8))
        self.add(self.text(m + 3, h - m - 3, "THIRD-ANGLE PROJECTION · DIMENSIONS IN mm · GENERAL TOL ±0.2 · "
                           "GENERATED FROM SOLIDCRAFT DESIGN, DO NOT EDIT BY HAND", 2.0, color=HID))
        nx, ny = sh.get("notes_at", [m + 5, m + 8])
        for i, line in enumerate(sh.get("notes", [])):
            self.add(self.text(nx, ny + i * 4.2, line, 2.6))

    def image(self, base: Path):
        img = self.sheet.get("image")
        if not img:
            return
        p = (base / img["path"])
        data = base64.b64encode(p.read_bytes()).decode()
        x, y = img["at"]
        raw = p.read_bytes()
        pw, ph = int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")  # PNG IHDR
        hh = img["width"] * ph / pw
        self.add(f'<image x="{x}" y="{y}" width="{img["width"]}" height="{hh:.2f}" xlink:href="data:image/png;base64,{data}"/>')

    def svg(self):
        body = "\n".join(self.out)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{self.w}mm" height="{self.h}mm" '
                f'viewBox="0 0 {self.w} {self.h}">\n<rect width="100%" height="100%" fill="#fff"/>\n{body}\n</svg>\n')


def main(spec_path: str):
    spec_file = Path(spec_path).resolve()
    base = spec_file.parent
    spec = json.loads(spec_file.read_text())
    design = base / spec["design"]
    out_stem = base / spec.get("out", "out/drawing")
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    have_rsvg = shutil.which("rsvg-convert")
    with tempfile.TemporaryDirectory() as tmp:
        for n, sh in enumerate(spec["sheets"], 1):
            files = export_views(design, sh, Path(tmp))
            S = Sheet(spec, sh)
            S.image(base)
            for v in sh["views"]:
                S.view(v["name"], read_segments(files[v["name"]]), v.get("label_dy", 0))
            for d in sh.get("dims", []):
                S.dim(d)
            S.frame(n, len(spec["sheets"]))
            svg = out_stem.with_name(f"{out_stem.name}-{sh['name']}.svg")
            svg.write_text(S.svg())
            print(svg)
            if have_rsvg:
                subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(svg.with_suffix(".pdf")), str(svg)], check=True)
                subprocess.run(["rsvg-convert", "-w", "2400", "-b", "white", "-o", str(svg.with_suffix(".png")), str(svg)], check=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
