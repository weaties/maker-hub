---
name: print-prep
description: Use when preparing a SolidCraft part for 3D printing - orientation, print files, slicing headless for a Bambu Lab printer (any model), sending to Bambu Studio or Cura, material and settings choices, and recording test-fit results.
---

# Print prep

1. **Orientation.** Each body gets its own oriented export. Flat face down, the fewest overhangs > 45°, layer lines across the load (layers split under tension). Lids and plates print face down.
2. **Write `print.json`** in the part folder (runs on the built `.sc` without saving it):
   ```json
   {"commands":[
    {"command":"file.export_3mf","params":{"path":"print/<slug>-base.3mf","bodies":["Base"],"quality":"fine"}},
    {"command":"solid.move","params":{"bodies":["Lid"],"axis":[1,0,0],"angle":"180 deg"}},
    {"command":"solid.move","params":{"bodies":["Lid"],"translate":[0,0,"<top z of the lid before the flip>"]}},
    {"command":"file.export_3mf","params":{"path":"print/<slug>-lid.3mf","bodies":["Lid"],"quality":"fine"}},
    {"command":"inspect.measure","params":{"bodies":["Lid"]}}
   ]}
   ```
   Run with `--results` once and check the moved body's bbox min z is 0.
   `body.print_face` (saved in the design) orients bodies automatically, but only for `file.send_to_slicer`.
3. **Slice for Bambu Lab: `slice.json` + `tools/bambu/slice.py`.** Bambu Studio's own CLI slices
   headless, so a part folder goes straight to a print job:
   ```json
   {"material": "PETG", "plates": ["print/<slug>-base.3mf", "print/<slug>-lid.3mf"],
    "settings": {"wall_loops": "3", "sparse_infill_density": "15%"}}
   ```
   `build.sh` runs it when `print.json` exists (or run `tools/bambu/slice.py <part-folder>`). It writes
   `print/<file>.<printer>.gcode.3mf` and prints time, grams, layers and height per plate.
   - **Printer:** `--printer`, `$BAMBU_PRINTER`, `~/.config/maker-hub/bambu.json` (`{"printer": "…", "plate": "…"}`),
     else whatever was last selected in Bambu Studio on that Mac. DW's is a **Bambu Lab X2D 0.4 nozzle**.
     Each person slices for their own printer from the same folder, which is why `*.gcode.3mf` is git-ignored.
     `--whoami` shows the choice; `--list-printers` the names.
   - **Presets:** `<0.20>mm Standard` process and the Bambu filament for `material` (PLA, PETG → PETG HF, ASA,
     ABS, TPU, PA-CF, PETG-CF), chosen by each preset's `compatible_printers`. `--filament`/`--process` take
     exact names; `settings` / `--set key=value` override anything (`enable_support=1`, `wall_loops=4`).
     The tool flattens Bambu's `inherits` chains itself: the CLI doesn't, and silently slices as PLA with 0 g.
   - **Check the numbers:** grams ≈ part volume × density (PETG ~1.25 g/cm³) × a bit less for infill;
     height = model height to the layer. The tool fails if the filament didn't load (0 g / wrong type).
   - **Print:** `--open` (or `open -a BambuStudio print/<file>.gcode.3mf`), check the preview, press
     Print → send to the printer. Or copy the file to the printer's SD/USB. Sending straight to the printer
     from the CLI is not wired up (it needs the printer's access code; do it from Studio).
   - Cura (installed too) still takes the plain `print/*.3mf`. In a live MCP session
     `file.send_to_slicer {"slicer":"bambu","bodies":[...]}` opens bodies in Studio unsliced.
4. **Settings** (put them in `slice.json`, tell the user why): material from `library/materials.md`;
   0.2 mm layers; 3 walls (4+ for boat/load parts); 15 % infill (40 %+ for load); supports only where the
   model needs them, and say where.
5. **Close the loop.** After the user prints, ask how it fit and record it in the part README Log (`2026-11-08 v1 printed PETG, lid tight -> lip_clr 0.3→0.4`). If it's a general lesson (a clearance, an insert size), update `library/fits-and-fasteners.md`.
