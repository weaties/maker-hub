---
name: print-prep
description: Use when preparing a SolidCraft part for 3D printing - orientation, print files, sending to Bambu Studio or Cura, material and settings choices, and recording test-fit results.
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
3. **Send to the slicer.** Installed: Bambu Studio (`bambu`) and UltiMaker Cura (`cura`). `open -a "BambuStudio" print/<file>.3mf` opens it. In a live MCP session, `file.send_to_slicer {"slicer":"bambu","bodies":[...]}`.
4. **Settings** (tell the user; they slice): material from `library/materials.md`; 0.2 mm layers; 3 walls (4+ for boat/load parts); 15 % infill (40 %+ for load); supports only where the model needs them, and say where.
5. **Close the loop.** After the user prints, ask how it fit and record it in the part README Log (`2026-11-08 v1 printed PETG, lid tight -> lip_clr 0.3→0.4`). If it's a general lesson (a clearance, an insert size), update `library/fits-and-fasteners.md`.
