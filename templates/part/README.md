# <ID> · <Part name>

One paragraph: what it is, where it goes, why it exists.

| | |
|---|---|
| Status | idea / designed / printed v1 / installed |
| Process | 3D print · Shaper Origin · plasma |
| Material | |
| Fasteners / hardware | |
| Key dims | |

## Requirements
- Fits: (what it mates with, measured dims, measured with what)
- Loads / environment: (indoor, cockpit, under deck, sun, salt water…)

## Files
- `<name>.json`: source of truth (SolidCraft script). `./build.sh` regenerates everything else.
- `print.json` (optional) → `print/`: oriented print files (3MF, any slicer)
- `slice.json` (optional): material and slicer settings; `build.sh` then writes
  `print/*.<printer>.gcode.3mf` ready to print on a Bambu Lab (sliced for your own printer, not committed)
- `shaper.json` (optional) → `shaper/`: DXF + Shaper SVG
- `plasma.json` (optional) → `plasma/`: DXF + checked R12 DXF (`PLASMA_T=<mm> ./build.sh`)
- `drawing.json` (optional) → `out/drawing-*.svg|pdf`

## Log
- YYYY-MM-DD: v1 designed.
