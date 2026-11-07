---
name: front-panel
description: Use when designing a machined panel, plate or enclosure face to order from Front Panel Express (FPE / Schaeffer AG) - control panels, instrument faces, labelled covers, anodised or engraved aluminium - or when turning a SolidCraft part into something FPE can make.
---

# Front Panel Express panels

FPE machines, anodises and engraves aluminium and acrylic panels, ordered through their free
**Front Panel Designer** (FPD; installed: `/Applications/FrontDesign.app`, v6.3.5). FPD has a
JavaScript scripting interface, so the hub generates panels instead of drawing them by hand.

## Route
1. `cp -R templates/fpe-panel <part folder>` (in `projects/personal/...` or `projects/plasma-cutter/parts/...`).
2. Edit `panel.json` (format in the docstring of `tools/fpe/panel.py`). FPE conventions: mm, origin at the lower-left, seen from the front, features placed by their centre.
   - `drill` (with `thread`, `countersink`, `blind`), `rect` (rounded rectangular hole), `cavity` (circle/rect pocket with `depth`, `side: front|rear`), `contour` (free cut-out or pocket from a DXF), `text` (engraving, filled with an engrave colour).
   - Free shapes: draw them in a SolidCraft sketch and `sketch.export_dxf` (the template's `vent.json` does this). FPE needs closed, non-crossing contours.
   - Material / colour / thickness use FPD's constant names (`alu_elox` + `elox_black`, `acryl` + `acryl_clear`, thickness 1.5-10 mm). The generator checks every constant against FPD's `init.fpjs` and stops on a wrong name.
3. `./build.sh`: generates `fpe/<name>.fpjs`, checks the SolidCraft model's volume against the analytic one (it fails if a feature missed), saves `fpe/<name>.sc`, a front snapshot, and the DXF pair.
4. In FPD: **Edit > Scripts > Add** `fpe/<name>.fpjs` **> Start**. The panel appears and is saved as `fpe/<name>.fpd`. Check FPD's price and its manufacturability warnings, then **Order > Order current front panel**. Ordering is always the user's step.
5. Fit check: put `fpe/<name>.sc` (or its STEP) against the enclosure in SolidCraft before ordering.

## Fallback without scripts
`fpe/<name>-outline.dxf` → FPD **New front panel > Basic shape: Free shape from DXF file**, then
`fpe/<name>-cutouts.dxf` → **Insert free contour > Import** (reference point: origin of DXF file),
largest tool that fits. This route loses threads, countersinks, cavities and engravings (the
generator lists what it left out), so prefer the script.

## Status and limits (be honest about these)
- The generated scripts use only API calls and constants documented in FPD's scripting PDF and its bundled demos, but none has been **run** in FPD yet. The FPE scripting interface calls itself experimental. The first run of a new spec gets checked by eye in FPD before ordering.
- Reference points: holes, cavities and contours are placed by their centre (`grav_center` for contours). Text placement follows FPD's alignment. Confirm on the first run.
- Fonts: FPD's own (`fontspec` like `"century-outline:4mm"`); the SolidCraft model uses its default font, so engraved text in renders is approximate.
- FPE's own engraving, anodising and pricing live in FPD; the SolidCraft model is for fit and looks.
- Docs: https://docs.frontpanelexpress.com (scripting: Programming interface; DXF import guide PDF). Support: info@frontpanelexpress.com, (206) 768-0602.
