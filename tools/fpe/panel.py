# /// script
# requires-python = ">=3.11"
# dependencies = ["ezdxf>=1.3"]
# ///
"""Front Panel Express panels from one spec: an FPD script, a SolidCraft model, and DXFs.

    uv run tools/fpe/panel.py <part>/panel.json [--no-text]

From `panel.json` (format below) it writes, next to the spec in `fpe/`:
  <name>.fpjs            Front Panel Designer script (Edit > Scripts > Add, then Start). It builds the
                         panel from FPE's own elements (drill holes with threads/countersinks,
                         rectangular holes, cavities with depth, free contours, engravings), so FPE
                         prices and machines it natively, then saves <name>.fpd next to it.
                         Order from FPD (Order > Order current front panel).
  <name>.solidcraft.json SolidCraft script of the same panel: for fit checks against an enclosure,
                         renders and drawings. Engraved text is a 0.2 mm deboss, for looks only.
  <name>-outline.dxf     the two-file DXF route from FPE's DXF import guide, for when you'd rather
  <name>-cutouts.dxf     not run a script: outline -> "Free shape from DXF file", cutouts -> Free
                         contour import. Through-features only (no cavities, threads or text).
  expected volume        printed, so the build can check the SolidCraft model (--no-text leaves text out).

Coordinates follow FPE: mm, origin at the panel's lower-left corner, x right, y up, seen from the
front. Holes, cut-outs, cavities and contours are placed by their centre.

{
  "name": "control-panel",              # file names; letters, digits, - and _
  "title": "Plasma control box front",  # FPD panel name
  "width": 160, "height": 90, "thickness": 3,       # thickness: 1.5 2 2.5 3 4 5 6 8 10
  "material": "alu_elox", "color": "elox_black",    # FPD constants (see init.fpjs / the API PDF)
  "corner_radius": 3,
  "remark": "Please deburr edges.",                  # manufacturing remark
  "engrave_color": "engrave_pure_white",             # default for text
  "elements": [
    {"type": "drill", "name": "estop", "x": 35, "y": 50, "d": 22.5},
    {"type": "drill", "name": "m1", "x": 6, "y": 6, "d": 3.4, "countersink": "M3"},
    {"type": "drill", "name": "stud", "x": 20, "y": 6, "d": 2.5, "thread": "M3", "blind": 2},
    {"type": "rect", "name": "power", "x": 80, "y": 52, "w": 19.2, "h": 12.9, "r": 0.5},
    {"type": "cavity", "name": "recess", "shape": "rect", "x": 40, "y": 78, "w": 50, "h": 10, "r": 1, "depth": 0.5, "side": "front"},
    {"type": "cavity", "name": "boss", "shape": "circle", "x": 140, "y": 20, "d": 12, "depth": 1.5, "side": "rear"},
    {"type": "contour", "name": "vent", "dxf": "vent.dxf", "x": 80, "y": 20, "depth": null},
    {"type": "text", "name": "lbl", "x": 35, "y": 34, "text": "E-STOP", "size": 4, "align": "center",
     "font": null, "color": null}                    # font: FPD fontspec like "century-outline:4mm"
  ]
}
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import ezdxf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dxf"))
import dxfloops  # noqa: E402

FPD_INIT = Path("/Applications/FrontDesign.app/Contents/Resources/Scripts/init.fpjs")
THICKNESSES = {1.5: "thick_1_5mm", 2: "thick_2mm", 2.5: "thick_2_5mm", 3: "thick_3mm", 4: "thick_4mm",
               5: "thick_5mm", 6: "thick_6mm", 8: "thick_8mm", 10: "thick_10mm"}
# DIN 74 A countersinks, 90 deg: (through hole, cone diameter)
SINKS = {"M2": (2.4, 4.6), "M2.5": (2.9, 5.7), "M3": (3.4, 6.5), "M3.5": (3.9, 7.6), "M4": (4.5, 8.6),
         "M5": (5.5, 10.4), "M6": (6.6, 12.4)}
LOOKS = {  # rough render colours for the SolidCraft model
    "elox_natural": "#c8cacc", "elox_black": "#26282b", "elox_gold": "#c9a54a", "elox_red": "#9b2a2a",
    "elox_blue": "#2e5a96", "elox_green": "#3d7a4a", "elox_dark_bronze": "#4a3a2a", "elox_medium_bronze": "#7a5f3e",
    "acryl_clear": "#dde6ea", "acryl_red": "#b02a2a", "pcoat_black": "#1d1d1f", "pcoat_traffic_white": "#f1f0ea",
}


def die(msg):
    sys.exit(f"panel.py: {msg}")


def known_constants() -> set[str] | None:
    if not FPD_INIT.exists():
        return None
    return set(re.findall(r"^\s*const\s+([A-Za-z0-9_]+)\s*=", FPD_INIT.read_text(errors="ignore"), re.M))


def const_name(kind: str, value: str) -> str:
    """FPD constant for a thread/countersink size like 'M3' or 'M2.5'."""
    v = value.upper().replace(".", "_")  # "M2.5" -> "M2_5"
    return {"thread": f"thread_{v}", "sink": f"sink_74A_{v}"}[kind]


def js_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def num(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


# ---------------------------------------------------------------- Front Panel Designer script
def fpjs(spec: dict, base: Path, out_dir: Path, spec_name: str = "panel.json") -> str:
    t = THICKNESSES.get(spec["thickness"]) or die(f"thickness must be one of {sorted(THICKNESSES)}")
    L = [f"// Generated by maker-hub tools/fpe/panel.py from {spec_name}. Edit the spec, not this file.",
         "// Run in Front Panel Designer: Edit > Scripts > Add (this file) > Start.",
         f"var fp = new Frontpanel({js_str(spec.get('title', spec['name']))}, {t}, {num(spec['width'])}, {num(spec['height'])}, "
         f"{spec['material']}, {spec['color']});"]
    r = spec.get("corner_radius", 0)
    if r:
        L.append(f"fp.SetCornerRadii({num(r)}, {num(r)}, {num(r)}, {num(r)});")
    if spec.get("remark"):
        L.append(f"fp.SetRemark({js_str(spec['remark'])});")
    L.append("AddFrontpanel(fp);")
    for e in spec["elements"]:
        n = js_str(e["name"])
        x, y = num(e["x"]), num(e["y"])
        k = e["type"]
        if k == "drill":
            expr = f"new DrillHole({n}, {num(e['d'])})"
            if e.get("thread"):
                expr += f".SetThreading({const_name('thread', e['thread'])})"
            if e.get("countersink"):
                expr += f".SetCountersink({const_name('sink', e['countersink'])})"
            if e.get("blind"):
                expr += f".SetBlindHole({num(e['blind'])})"
        elif k == "rect":
            expr = f"new RectHole({n}, {num(e['w'])}, {num(e['h'])}, {num(e.get('r', 0))})"
        elif k == "cavity":
            if e["shape"] == "circle":
                expr = f"new Cavity({n}).MakeCircular({num(e['d'])}, {num(e['depth'])})"
            else:
                expr = f"new Cavity({n}).MakeRectangular({num(e['w'])}, {num(e['h'])}, {num(e['depth'])}, {num(e.get('r', 0))})"
            if e.get("side") == "rear":
                expr += ".PutOnReverseSide()"
        elif k == "contour":
            dxf = (base / e["dxf"]).resolve()
            as_cav = 1 if e.get("depth") else 0
            expr = f"new DxfContour({n}, {js_str(str(dxf))}, grav_center, 100, {as_cav})"
            if e.get("depth"):
                expr += f".SetDepth({num(e['depth'])})"
        elif k == "text":
            expr = f"new TextEngraving({n}, {js_str(e['text'])})"
            expr += f".SetAlignment(align_{e.get('align', 'center')}).SetTextSize({num(e['size'])})"
            if e.get("font"):
                expr += f".SetFont({js_str(e['font'])})"
            color = e.get("color") or spec.get("engrave_color")
            if color:
                expr += f".SetColor({color})"
        else:
            die(f"unknown element type {k!r}")
        L.append(f"fp.AddElement({expr}, {x}, {y});")
    fpd = (out_dir / f"{spec['name']}.fpd").resolve()
    L += [f"SaveFrontpanel(fp, {js_str(str(fpd))}, true);",
          f"Print({js_str('Built ' + spec['name'] + ' and saved ' + fpd.name + chr(10))});"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- SolidCraft model
def front_surface(spec: dict, x: float, y: float) -> float:
    """Height of the front face at (x, y): the panel top, or the floor of the deepest front cavity there."""
    z = spec["thickness"]
    for e in spec["elements"]:
        if e["type"] != "cavity" or e.get("side", "front") != "front":
            continue
        if e["shape"] == "circle":
            inside = math.hypot(x - e["x"], y - e["y"]) < e["d"] / 2
        else:
            inside = abs(x - e["x"]) < e["w"] / 2 and abs(y - e["y"]) < e["h"] / 2
        if inside:
            z = min(z, spec["thickness"] - e["depth"])
    return z


def solidcraft(spec: dict, base: Path, with_text: bool) -> tuple[dict, float]:
    W, H, T = spec["width"], spec["height"], spec["thickness"]
    r = spec.get("corner_radius", 0)
    C = [{"command": "solid.box", "params": {"length": W, "width": H, "height": T,
                                              "center": [W / 2, H / 2, T / 2], "body_name": "Panel", "name": "Plate"}}]
    vol = W * H * T
    if r:
        C.append({"command": "solid.fillet", "params": {"edges": [[0, 0, T / 2], [W, 0, T / 2], [W, H, T / 2], [0, H, T / 2]],
                                                        "radius": r, "name": "Corners"}})
        vol -= 4 * r * r * (1 - math.pi / 4) * T

    def rect_sketch(name, x, y, w, h, rr, z):
        C.append({"command": "sketch.create", "params": {"plane": "XY", "offset": z, "name": name}})
        p0, p1 = [x - w / 2, y - h / 2], [x + w / 2, y + h / 2]
        if rr:
            C.append({"command": "sketch.rectangle.rounded", "params": {"p0": p0, "p1": p1, "radius": rr}})
        else:
            C.append({"command": "sketch.rectangle.two_point", "params": {"p0": p0, "p1": p1}})
        C.append({"command": "sketch.finish", "params": {}})

    def rr_area(w, h, rr):
        return w * h - (4 - math.pi) * rr * rr

    # Order matters for speed: SolidCraft's deboss slows down with every feature already on the
    # body (16 s per label on the finished example panel, 0.6 s on the bare plate). Cut cavities
    # first (text may sit on their floor), engrave, then drill and cut everything else.
    rank = {"cavity": 0, "text": 1}
    for e in sorted(spec["elements"], key=lambda e: rank.get(e["type"], 2)):
        k, x, y, nm = e["type"], e["x"], e["y"], e["name"]
        if k == "drill":
            d = e["d"]
            if e.get("countersink"):
                hole, cone = SINKS.get(e["countersink"]) or die(f"no countersink size for {e['countersink']}")
                C.append({"command": "solid.hole", "params": {"position": [x, y, T], "diameter": d, "type": "countersink",
                                                              "cs_diameter": cone, "cs_angle": 90, "name": nm}})
                h_cs = (cone - d) / 2
                R, rr = cone / 2, d / 2
                vol -= math.pi * rr * rr * T + (math.pi * h_cs / 3 * (R * R + R * rr + rr * rr) - math.pi * rr * rr * h_cs)
            else:
                depth = e.get("blind") or T
                C.append({"command": "solid.cylinder", "params": {"diameter": d, "height": depth + 1,
                                                                  "base": [x, y, T - depth], "operation": "cut", "name": nm}})
                vol -= math.pi * d * d / 4 * depth
        elif k == "rect":
            rect_sketch(nm + "_sk", x, y, e["w"], e["h"], e.get("r", 0), 0)
            C.append({"command": "solid.extrude", "params": {"through_all": True, "operation": "cut", "name": nm}})
            vol -= rr_area(e["w"], e["h"], e.get("r", 0)) * T
        elif k == "cavity":
            front = e.get("side", "front") == "front"
            z = T if front else 0
            dirn = "negative" if front else "positive"
            dep = e["depth"]
            if e["shape"] == "circle":
                C += [{"command": "sketch.create", "params": {"plane": "XY", "offset": z, "name": nm + "_sk"}},
                      {"command": "sketch.circle.center", "params": {"center": [x, y], "radius": e["d"] / 2}},
                      {"command": "sketch.finish", "params": {}}]
                area = math.pi * e["d"] ** 2 / 4
            else:
                rect_sketch(nm + "_sk", x, y, e["w"], e["h"], e.get("r", 0), z)
                area = rr_area(e["w"], e["h"], e.get("r", 0))
            C.append({"command": "solid.extrude", "params": {"distance": dep, "direction": dirn, "operation": "cut", "name": nm}})
            vol -= area * dep
        elif k == "contour":
            dxf = (base / e["dxf"]).resolve()
            dep = e.get("depth")
            C += [{"command": "sketch.create", "params": {"plane": "XY", "offset": T if dep else 0, "name": nm + "_sk"}},
                  {"command": "sketch.insert_dxf", "params": {"path": str(dxf), "at": [x, y], "align": "center"}},
                  {"command": "sketch.finish", "params": {}}]
            C.append({"command": "solid.extrude", "params": ({"distance": dep, "direction": "negative"} if dep else {"through_all": True})
                      | {"operation": "cut", "name": nm}})
            by_layer, _ = dxfloops.read_paths(dxf)
            loops = dxfloops.classify([(c, "") for c in dxfloops.chain([p for ps in by_layer.values() for p in ps]) if c.is_closed])
            area = sum((-1 if lp.is_hole else 1) * lp.area for lp in loops)
            vol -= area * (dep or T)
        elif k == "text":
            if not with_text:
                continue
            align = e.get("align", "center")
            z = front_surface(spec, x, y)  # text inside a front cavity sits on the cavity floor
            C += [{"command": "sketch.create", "params": {"plane": "XY", "offset": z, "name": nm + "_sk"}},
                  {"command": "sketch.text", "params": {"text": e["text"], "at": [x, y], "height": e["size"], "align": align}},
                  {"command": "sketch.finish", "params": {}},
                  {"command": "solid.emboss", "params": {"sketch": nm + "_sk", "depth": 0.2, "mode": "deboss",
                                                         "targets": ["Panel"], "face": [x, y, z]}}]
    look = LOOKS.get(spec["color"], "#9aa3ad")
    C.append({"command": "material.assign", "params": {"bodies": ["Panel"],
                                                        "material": "Polycarbonate" if spec["material"] == "acryl" else "Aluminum"}})
    C.append({"command": "appearance.assign", "params": {"bodies": ["Panel"], "color": look,
                                                          "pbr": {"metallic": 0.0 if spec["material"] == "acryl" else 0.6, "roughness": 0.45, "dielectric_ior": 1.5}}})
    return {"commands": C}, vol


# ---------------------------------------------------------------- DXF pair (FPE's DXF import route)
def rounded_rect(msp, x0, y0, x1, y1, r):
    if r <= 0:
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True)
        return
    msp.add_line((x0 + r, y0), (x1 - r, y0)); msp.add_arc((x1 - r, y0 + r), r, 270, 360)
    msp.add_line((x1, y0 + r), (x1, y1 - r)); msp.add_arc((x1 - r, y1 - r), r, 0, 90)
    msp.add_line((x1 - r, y1), (x0 + r, y1)); msp.add_arc((x0 + r, y1 - r), r, 90, 180)
    msp.add_line((x0, y1 - r), (x0, y0 + r)); msp.add_arc((x0 + r, y0 + r), r, 180, 270)


def dxf_pair(spec: dict, base: Path, out_dir: Path) -> list[str]:
    skipped = []
    o = ezdxf.new("R2010"); o.units = ezdxf.units.MM
    rounded_rect(o.modelspace(), 0, 0, spec["width"], spec["height"], spec.get("corner_radius", 0))
    o.saveas(out_dir / f"{spec['name']}-outline.dxf")
    c = ezdxf.new("R2010"); c.units = ezdxf.units.MM
    m = c.modelspace()
    for e in spec["elements"]:
        k = e["type"]
        if k == "drill" and not e.get("blind"):
            m.add_circle((e["x"], e["y"]), e["d"] / 2)
            if e.get("thread") or e.get("countersink"):
                skipped.append(f"{e['name']}: thread/countersink (add in FPD)")
        elif k == "rect":
            rounded_rect(m, e["x"] - e["w"] / 2, e["y"] - e["h"] / 2, e["x"] + e["w"] / 2, e["y"] + e["h"] / 2, e.get("r", 0))
        elif k == "contour" and not e.get("depth"):
            src = base / e["dxf"]
            by_layer, _ = dxfloops.read_paths(src)
            chains = dxfloops.chain([p for ps in by_layer.values() for p in ps])
            pts = [(v.x, v.y) for ch in chains for v in ch.flattening(0.01)]
            cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
            cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
            for ch in chains:
                poly = [(v.x - cx + e["x"], v.y - cy + e["y"]) for v in ch.flattening(0.01)]
                m.add_lwpolyline(poly, close=ch.is_closed)
        else:
            skipped.append(f"{e['name']}: {k}{' (blind)' if e.get('blind') else ''}{' (cavity)' if e.get('depth') else ''}")
    c.saveas(out_dir / f"{spec['name']}-cutouts.dxf")
    return skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument("--no-text", action="store_true", help="leave engraved text out of the SolidCraft model")
    a = ap.parse_args()
    spec_file = a.spec.resolve()
    base = spec_file.parent
    spec = json.loads(spec_file.read_text())
    if not re.fullmatch(r"[A-Za-z0-9_-]+", spec["name"]):
        die("name: letters, digits, - and _ only")
    names = [e["name"] for e in spec["elements"]]
    if len(names) != len(set(names)):
        die("element names must be unique (FPD finds elements by name)")
    out_dir = base / "fpe"
    out_dir.mkdir(exist_ok=True)

    script = fpjs(spec, base, out_dir, f"{base.name}/{spec_file.name}")
    known = known_constants()
    if known is not None:
        used = set(re.findall(r"\b((?:thick|alu|acryl|elox|pcoat|engrave|thread|sink|align|grav)_[A-Za-z0-9_]*|acryl)\b", script))
        missing = sorted(u for u in used if u not in known)
        if missing:
            die(f"not FPD constants (checked against {FPD_INIT}): {', '.join(missing)}")
    (out_dir / f"{spec['name']}.fpjs").write_text(script)

    sc, vol = solidcraft(spec, base, not a.no_text)
    (out_dir / f"{spec['name']}.solidcraft.json").write_text(json.dumps(sc, indent=1))
    skipped = dxf_pair(spec, base, out_dir)

    print(json.dumps({"fpjs": str(out_dir / f"{spec['name']}.fpjs"),
                      "solidcraft": str(out_dir / f"{spec['name']}.solidcraft.json"),
                      "dxf": [f"{spec['name']}-outline.dxf", f"{spec['name']}-cutouts.dxf"],
                      "dxf_not_included": skipped,
                      "expected_volume_mm3_without_text": round(vol, 1),
                      "constants_checked": known is not None}, indent=1))


if __name__ == "__main__":
    main()
