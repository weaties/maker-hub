---
name: drawings-and-renders
description: Use when the user wants pictures, renders, section views, dimensioned drawings, PDFs or a shareable page of a part in this hub.
---

# Drawings and renders

All commands run from the hub root against a built `.sc`. Always Read the image you made before showing it.

## Pictures
- Quick shaded view: `tools/bin/solidcraft-cli snapshot X.sc --out out/a.png --view iso|front|top|right... --width 1400 --height 900 --no-grid --no-axes`
- Custom camera: `--camera '{"target":[x,y,z],"yaw":r,"pitch":r,"distance":mm}'` (radians; yaw 0 looks from -Y, π/2 from -X, π from +Y, -π/2 from +X; pitch π/2 is straight down; ortho height = 0.8 × distance).
- See inside: `--body 'Lid:opacity=0.25'` (0 hides it); section: `--section '{"plane":{"origin":[0,24.5,0],"normal":[0,1,0]}}'`. The section removes the side the normal points to, so put the camera on that side.
- Path-traced render: `render X.sc --out out/render.png --width 1600 --height 1000 --progressive --samples 128 --overwrite` (~40 s). Colours come from `appearance.assign` in the script. It frames the home view by default. For another angle, render a small script instead of the `.sc`:
  `{"commands":[{"command":"doc.open","params":{"path":"<abs path>/X.sc"}},{"command":"render.camera.set","params":{"camera":{"target":[0,0,14],"yaw":2.5,"pitch":0.45,"distance":170,"fov":0.5}}}]}`
  (`fov` > 0 gives perspective). A named setup saved in the design also works with `--setup NAME`.

## Dimensioned drawings
SolidCraft has no drawing workspace yet (on its roadmap). `tools/drawing/drawing.py` fills the gap: it exports orthographic views with `file.export_view_dxf` and lays them out with dimensions, notes, an optional picture and a title block.
- Spec: `drawing.json` in the part folder; the format is in the script docstring, and `projects/personal/electronics/pi5-case/drawing.json` is a full example (two A3 sheets at 2:1).
- `uv run tools/drawing/drawing.py <part folder>/drawing.json` → `out/drawing-<sheet>.svg|pdf|png`.
- Dimension points are model mm in that view's coordinates: top (x, y), front (x, z), right (y, z), left (-y, z). `off` is in sheet mm; its sign picks the side.
- Layout loop: generate, Read the PNG, fix overlaps, repeat. Keep dims off the part outline and labels below dims (`label_dy`).

## Sharing
For a page to look at or share, publish an Artifact with the renders and drawings embedded (base64 PNG / inline SVG). The Pi 5 case page is the pattern to follow.
