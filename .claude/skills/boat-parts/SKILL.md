---
name: boat-parts
description: Use when designing, printing or cutting anything for the boat - fittings, holders, brackets, instrument and electronics mounts, panels, backing plates - or anything that lives outdoors, in sun, salt or water.
---

# Boat parts

The boat environment changes the defaults. Apply these on top of `new-part`, `print-prep` and `shaper-cut`.

## Requirements to capture first (README)
- Where on the boat: cockpit/deck (UV, heat, spray), below deck (humid, may get wet), bilge/engine (heat, oil, immersion).
- Loads: static, shock (people grab it, sheets snap), and what happens if it fails (overboard? injury?). **Never** print safety-critical gear: lifelines, harness points, rigging, through-hulls below the waterline, steering. Say so plainly if asked.
- Measure on the boat: get the curvature of mounting surfaces (deck camber, cabin side) and photos.

## Design rules
- Material: ASA outdoors; PETG only below deck and out of the sun; no PLA on the boat. Shaper: marine ply (epoxy-sealed edges), HDPE/StarBoard, G10.
- Water: no pockets that hold water; add Ø4+ drain holes at the low points of any cup, tray or holder; slope tops.
- Fasteners: 316 stainless; holes for sealant beds; over-drill + epoxy-fill for deck cores (see `library/fits-and-fasteners.md`).
- Print: 4+ walls, 40 %+ infill, layers oriented across the bending load; fillet inside corners (≥ 2 mm) to stop cracking.
- Electronics: assume condensation. Use a conformal-coated board or a sealed box with a vent membrane, cable glands, drip loops; mount boxes connector-side down.
- Corners and edges people touch: R3+ rounds, no sharp edges near sheets and lines.

## Record
Log installs in the part README (where, date, what hardware, how it held up after a season).
