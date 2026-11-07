---
name: shaper-cut
description: Use when making anything to cut on the Shaper Origin (plywood, HDPE, G10, aluminium) - shop furniture, jigs, templates, boat panels and backing plates - or when converting a SolidCraft sketch, flat pattern or view to a Shaper SVG.
---

# Shaper Origin cuts

## Model for the router
- Parameters first: `stock_t` (the **measured** sheet thickness, never nominal), `bit_d` (default 1/4" = 6.35 mm; 1/8" = 3.175 for detail).
- Inside corners can't be sharper than the bit radius. For slot-together joints, add dog-bone or T-bone reliefs (a circle of `bit_d` at each inside corner) so the mating square corner seats.
- Slot widths = `stock_t + 0.2` (snug) to `+ 0.4` (easy assembly with finish).
- Keep parts ≥ `bit_d` apart on a sheet; leave ~20 mm from sheet edges.

## Export
Each cut profile lives in a sketch (or a sheet-metal flat pattern). Write `shaper.json` in the part folder:
```json
{"commands":[
 {"command":"sketch.export_dxf","params":{"sketch":"SidePanel","path":"shaper/side-panel.dxf"}}
]}
```
Other sources: `sheet.export_dxf {"body":..., "path":...}` (flat patterns, use `bend_lines:false`), `file.export_view_dxf` (a projected outline, camera `fov:0`).

Then convert (build.sh does both steps when `shaper.json` exists):
`uv run tools/shaper/to_shaper_svg.py shaper/side-panel.dxf --depth 18.3`
- Outer loop → exterior cut (black fill); holes → interior cut (white fill); open chains → on-line cut (grey stroke); islands in holes → exterior again.
- DXF layers named `POCKET*` → pocket (grey fill), `GUIDE*` / `HIDDEN` / `BEND*` → guide (blue, not cut), `ETCH*` / `ENGRAVE*` / `ONLINE*` → on-line. Pockets need their own sketch, so export it and rename the layer, or pass `--layer-map <LAYER>=pocket`.
- `--depth` writes `shaper:cutDepth` so Origin pre-fills it. Through cuts: stock + 0.5 mm, on a spoilboard.
- Render the SVG to check it (`rsvg-convert -w 800 -b white x.shaper.svg -o /tmp/x.png`, then Read it): black body, white holes.

## Hand-off to the user
Copy `shaper/*.shaper.svg` to Shaper Hub / a USB stick. Tell them the bit, depth and passes (≤ bit diameter per pass in ply; ≤ 1/4 bit diameter in aluminium), and to cut interior features before exterior ones so the part stays held. For boat parts in marine ply, seal the cut edges with epoxy.
