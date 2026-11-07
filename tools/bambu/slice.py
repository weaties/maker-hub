#!/usr/bin/env python3
"""Slice a part's print/*.3mf for a Bambu Lab printer, headless, with Bambu Studio's own CLI.

    tools/bambu/slice.py <part-folder>                 # uses <part>/slice.json
    tools/bambu/slice.py print/foo-base.3mf --material PETG --set wall_loops=4
    tools/bambu/slice.py --list-printers               # what this Bambu Studio knows
    tools/bambu/slice.py --whoami                      # the printer this machine slices for

Writes print/<stem>.<printer>.gcode.3mf (open it in Bambu Studio or Bambu Handy and press Print,
or copy it to the printer's SD card) and prints time, filament grams and layers per plate.

The printer comes from, in order: --printer, $BAMBU_PRINTER, ~/.config/maker-hub/bambu.json
{"printer": "Bambu Lab P1S 0.4 nozzle"}, then the printer last selected in Bambu Studio on this
Mac. So each person slices for their own machine from the same part folder.

Bambu Studio's CLI does not follow the "inherits" chain of its system presets (a filament comes
out as PLA with 0 g), so this flattens machine, process and filament presets first.
"""
import argparse, glob, json, os, re, subprocess, sys, tempfile, zipfile
from pathlib import Path

APP = Path(os.environ.get("BAMBU_STUDIO_APP", "/Applications/BambuStudio.app"))
EXE = APP / "Contents/MacOS/BambuStudio"
PROFILES = APP / "Contents/Resources/profiles/BBL"
STUDIO_CONF = Path.home() / "Library/Application Support/BambuStudio/BambuStudio.conf"
USER_CONF = Path.home() / ".config/maker-hub/bambu.json"

# material key (library/materials.md) -> Bambu filament preset base names, best first
MATERIALS = {
    "PLA": ["Bambu PLA Basic", "Generic PLA"],
    "PETG": ["Bambu PETG HF", "Bambu PETG Basic", "Generic PETG"],
    "ASA": ["Bambu ASA", "Generic ASA"],
    "ABS": ["Bambu ABS", "Generic ABS"],
    "TPU": ["Bambu TPU 95A HF", "Bambu TPU 95A", "Generic TPU"],
    "PA-CF": ["Bambu PA6-CF", "Bambu PAHT-CF", "Generic PA-CF"],
    "PETG-CF": ["Bambu PETG-CF", "Generic PETG-CF"],
}


def die(msg):
    sys.exit(f"slice: {msg}")


def index_presets():
    if not EXE.exists():
        die(f"Bambu Studio not found at {APP} (set BAMBU_STUDIO_APP)")
    idx = {}
    for f in glob.glob(str(PROFILES / "*/*.json")):
        try:
            d = json.load(open(f))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(d, dict) and "name" in d:
            idx.setdefault(d["name"], d)
    return idx


def flatten(idx, name, seen=()):
    if name not in idx:
        die(f"no Bambu preset named {name!r}")
    if name in seen:
        die(f"preset inheritance loop at {name!r}")
    own = idx[name]
    out = flatten(idx, own["inherits"], seen + (name,)) if own.get("inherits") else {}
    for inc in own.get("include", []):
        out.update({k: v for k, v in idx[inc].items() if k not in ("name", "instantiation")})
    out.update({k: v for k, v in own.items() if k not in ("inherits", "include")})
    return out


def printers(idx):
    return sorted(n for n, d in idx.items()
                  if d.get("type") == "machine" and d.get("instantiation") == "true")


def studio_selection():
    """The printer/process last picked in Bambu Studio's GUI. Reads only the 'presets' block."""
    try:
        return json.load(open(STUDIO_CONF)).get("presets", {})
    except (OSError, json.JSONDecodeError):
        return {}


def pick_printer(arg):
    if arg:
        return arg, "--printer"
    if os.environ.get("BAMBU_PRINTER"):
        return os.environ["BAMBU_PRINTER"], "$BAMBU_PRINTER"
    if USER_CONF.exists():
        p = json.load(open(USER_CONF)).get("printer")
        if p:
            return p, str(USER_CONF)
    p = studio_selection().get("machine")
    if p:
        return p, "Bambu Studio's selected printer"
    die("no printer: pass --printer, or pick one in Bambu Studio once, or write "
        f'{USER_CONF} {{"printer": "Bambu Lab P1S 0.4 nozzle"}}  (see --list-printers)')


def compatible(idx, kind, printer):
    """Instantiable presets of a kind whose compatible_printers lists this printer."""
    return [n for n, d in idx.items() if d.get("type") == kind and d.get("instantiation") == "true"
            and printer in d.get("compatible_printers", [])]


def pick_process(idx, printer, layer):
    """'<layer>mm Standard' for this printer; else the Standard preset nearest that layer height
    (bigger nozzles have no 0.20 mm preset)."""
    std = [n for n in compatible(idx, "process", printer) if re.match(r"[\d.]+mm Standard @", n)]
    if not std:
        die(f"no Standard process preset for {printer}; pass --process")
    return min(std, key=lambda n: (abs(float(n.split("mm")[0]) - layer), len(n)))


def pick_filament(idx, material, printer):
    bases = MATERIALS.get(material.upper())
    if bases is None:
        return material  # a full preset name
    names = compatible(idx, "filament", printer)
    for base in bases:
        hits = [n for n in names if n.startswith(base + " @")]
        if hits:
            return sorted(hits, key=len)[0]
    die(f"no Bambu filament preset for {material} on {printer}; pass --filament '<preset name>'")


def apply_sets(cfg, sets):
    for s in sets:
        k, _, v = s.partition("=")
        if k not in cfg:
            die(f"--set {k}: not a setting in these presets")
        cfg[k] = [v] * len(cfg[k]) if isinstance(cfg[k], list) else v


def short(printer):
    return re.sub(r"[^a-z0-9.]+", "-", printer.lower().removeprefix("bambu lab ")).strip("-").replace("-nozzle", "")


def summarise(gcode3mf):
    with zipfile.ZipFile(gcode3mf) as z:
        g = z.read("Metadata/plate_1.gcode").decode(errors="replace")
    get = lambda pat: (re.search(pat, g) or [None, "?"])[1]
    return {
        "time": get(r"total estimated time: ([^\n]+)"),
        "grams": get(r"total filament weight \[g\] : ([\d.]+)"),
        "layers": get(r"total layer number: (\d+)"),
        "height": get(r"max_z_height: ([\d.]+)"),
        "filament": get(r"; filament_type = ([^\n]+)"),
        "nozzle_temp": get(r"; nozzle_temperature = ([^\n]+)"),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*", help="part folder (with slice.json) or .3mf files")
    ap.add_argument("--printer", help="Bambu machine preset, e.g. 'Bambu Lab A1 0.4 nozzle'")
    ap.add_argument("--process", help="process preset (default: <layer>mm Standard for the printer)")
    ap.add_argument("--material", help="PLA, PETG, ASA, ABS, TPU, PA-CF, PETG-CF (default from slice.json, else PLA)")
    ap.add_argument("--filament", help="exact filament preset name (overrides --material)")
    ap.add_argument("--plate", help="build plate, e.g. 'Textured PEI Plate', 'Cool Plate', 'Engineering Plate' "
                    "(default: slice.json, ~/.config/maker-hub/bambu.json, then the printer's default)")
    ap.add_argument("--layer", type=float, help="layer height, default 0.20")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="override a slicer setting, e.g. wall_loops=4 sparse_infill_density=40%%")
    ap.add_argument("--outdir", help="default: next to each .3mf")
    ap.add_argument("--open", action="store_true", help="open the sliced files in Bambu Studio")
    ap.add_argument("--list-printers", action="store_true")
    ap.add_argument("--whoami", action="store_true", help="show which printer and presets would be used")
    a = ap.parse_args()

    idx = index_presets()
    if a.list_printers:
        print("\n".join(printers(idx)))
        return

    spec, files, base = {}, [], Path.cwd()
    for i in a.inputs:
        p = Path(i)
        if p.is_dir():
            base = p
            if (p / "slice.json").exists():
                spec = json.load(open(p / "slice.json"))
                files += [p / f for f in spec.get("plates", [])]
            else:
                files += sorted(p.glob("print/*.3mf"))
            files = [f for f in files if not f.name.endswith(".gcode.3mf")]
        else:
            files.append(p)
    if not files and not a.whoami:
        die("nothing to slice (give a part folder or .3mf files)")

    printer, why = pick_printer(a.printer)
    machine = flatten(idx, printer)
    layer = a.layer or float(spec.get("layer", 0.2))
    process_name = a.process or spec.get("process") or pick_process(idx, printer, layer)
    material = a.material or spec.get("material", "PLA")
    filament_name = a.filament or pick_filament(idx, material, printer)
    process, filament = flatten(idx, process_name), flatten(idx, filament_name)
    user = json.load(open(USER_CONF)) if USER_CONF.exists() else {}
    plate = (a.plate or spec.get("plate") or user.get("plate")
             or idx.get(machine["printer_model"], {}).get("default_bed_type") or "Textured PEI Plate")
    process["curr_bed_type"] = plate
    sets = [f"{k}={v}" for k, v in spec.get("settings", {}).items()] + a.set
    apply_sets(process, [s for s in sets if s.partition("=")[0] in process])
    apply_sets(filament, [s for s in sets if s.partition("=")[0] in filament and s.partition("=")[0] not in process])
    unknown = [s for s in sets if s.partition("=")[0] not in process and s.partition("=")[0] not in filament]
    apply_sets(machine, unknown)

    print(f"printer  {printer}   ({why})\nprocess  {process_name}\nfilament {filament_name}\nplate    {plate}"
          + (f"\nsettings {' '.join(sets)}" if sets else ""))
    if a.whoami:
        return

    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for kind, cfg in (("machine", machine), ("process", process), ("filament", filament)):
            f = Path(tmp) / f"{kind}.json"
            json.dump(cfg, open(f, "w"), indent=1)
            paths.append(f)
        results = []
        for src in files:
            if not src.exists():
                die(f"{src} not found (run the part's build.sh first)")
            outdir = Path(a.outdir) if a.outdir else src.parent
            out = outdir / f"{src.stem}.{short(printer)}.gcode.3mf"
            work = Path(tmp) / src.stem
            work.mkdir()
            cmd = [str(EXE), "--debug", "1", "--slice", "0", "--arrange", "1", "--orient", "0",
                   "--outputdir", str(work), "--export-3mf", "out.gcode.3mf",
                   "--load-settings", f"{paths[0]};{paths[1]}", "--load-filaments", str(paths[2]), str(src.resolve())]
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=work)
            res = {}
            if (work / "result.json").exists():
                res = json.load(open(work / "result.json"))
            if r.returncode != 0 or res.get("return_code", 1) != 0 or not (work / "out.gcode.3mf").exists():
                tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-8:])
                die(f"Bambu Studio failed on {src.name}: {res.get('error_string', '')}\n{tail}")
            outdir.mkdir(parents=True, exist_ok=True)
            (work / "out.gcode.3mf").replace(out)
            s = summarise(out)
            warn = " ".join(p.get("warning_message", "") for p in res.get("sliced_plates", [])).strip()
            results.append(out)
            print(f"\n{out}\n  {s['time']}, {s['grams']} g {s['filament']}, {s['layers']} layers, "
                  f"{s['height']} mm tall, nozzle {s['nozzle_temp']} °C" + (f"\n  warning: {warn}" if warn else ""))
            if s["grams"] in ("?", "0.00") or s["filament"].split(";")[0] != filament.get("filament_type", ["?"])[0]:
                die(f"{out.name}: filament didn't load properly ({s['filament']}, {s['grams']} g); check the presets")
    if a.open and results:
        subprocess.run(["open", "-a", str(APP), *map(str, results)])


if __name__ == "__main__":
    main()
