---
name: plasma-cut
description: Use when designing steel or aluminium parts to cut on the CNC plasma table, preparing or checking DXFs for plasma CAM, or working on the plasma table build itself (projects/plasma-cutter).
---

# Plasma cutting

## The machine
The JD's Garage Gen 2.0 table that DW and Stefan are building lives in `projects/plasma-cutter/`, its own repo shared with Stefan.
- Cutting area 711 × 812 mm (28 × 32 in); ESP32 controller with open-source firmware; low-frequency-start cutter.
- Until the build log says it cuts, plasma parts go to a cutting service (SendCutSend / OSHCut take the same clean DXF), or onto the Shaper for aluminium ≤ 6 mm.
- The purchased plans are **never** committed or pasted anywhere public: they live in `projects/plasma-cutter/plans/` (git-ignored). You may read them there to help with the build.

## Designing a part for plasma
- Model as a plate: sketch the profile, extrude to `stock_t`; or use sheet metal (`sheet.flange` …) for bent parts, then `sheet.flat_pattern`.
- Rules of thumb (calibrate in `library/fits-and-fasteners.md` once the table runs):
  - smallest hole ≈ 1 × thickness, better 1.5 ×; smaller holes get drilled (model a centre-punch dot: a 1 mm circle on a layer named `ETCH`, or leave it to drilling);
  - web between holes and edges ≥ thickness;
  - inside corners get ≥ 1 mm radius; sharp outside corners round off by themselves;
  - nest parts ≥ 2 × kerf apart (≈ 3-5 mm);
  - text: bold, ≥ 15 mm tall in 3 mm steel, with stencil bridges inside letters such as O, A and B.
- Kerf (≈ 1.5 mm at 40-45 A) is compensated in CAM. **Never offset the drawing.**

## Export and check
`shaper.json`-style script, named `plasma.json` in the part folder:
```json
{"commands":[
 {"command":"sketch.export_dxf","params":{"sketch":"Plate","path":"plasma/plate.dxf"}},
 {"command":"sheet.export_dxf","params":{"body":"Bracket","path":"plasma/bracket.dxf","curves":"arcs","bend_lines":false}}
]}
```
Then check and clean (run on every DXF before CAM or a cutting service):
`uv run tools/plasma/check_dxf.py plasma/plate.dxf --thickness 3.2 --out plasma/plate.r12.dxf`
- Errors: open contours, near-miss gaps, larger than the table. Fix them in the model, not the DXF.
- Warnings: small holes, thin webs, skipped text. Decide, then say what you decided in the part README.
- The `.r12.dxf` has outlines on `OUTSIDE`, holes on `INSIDE`, which is what CAM wants for cut order (inside first) and lead-in side.
- CAM and post-processor: whatever the plans' firmware uses (recorded in `projects/plasma-cutter/decisions.md` #8). Ask before assuming.

## Safety
Plasma is a fire and fume process: `projects/plasma-cutter/safety.md`. If asked to plan cutting in the office maker space, bring it up.
