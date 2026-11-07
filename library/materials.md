# Materials

## Filament (FDM)
| Material | Density g/cm³ | Use | Avoid |
|---|---|---|---|
| PLA | 1.24 | jigs, fixtures, prototypes, indoor shop items | heat (>50 °C, cars, cockpits, sun), long-term load |
| PETG | 1.27 | general functional parts, electronics cases indoors, drawers | strong UV long term |
| ASA | 1.07 | **anything outdoors / on the boat**: UV- and heat-stable | needs enclosure, fumes |
| ABS | 1.04 | heat resistance indoors | UV, warping |
| TPU 95A | 1.21 | gaskets, bumpers, grips, cable strain relief | precision fits |
| PA-CF / PETG-CF | ~1.2-1.3 | stiff brackets, clamps | abrasive: hardened nozzle |

SolidCraft has no built-in PETG or ASA: scripts add them with
`material.create {"name":"PETG","density_g_cm3":1.27}` before `material.assign`.

Boat rule: **ASA (or PETG under deck, out of sun) and 316 hardware**, 4+ walls, 40 %+ infill for
anything that takes load, drain holes in anything that can hold water.

## Sheet goods (Shaper Origin)
Measure every sheet with calipers: plywood is rarely its nominal thickness. Record the actual
thickness in the part's parameters (`stock_t`) so slots and dados fit.
| Material | Nominal | Typical actual | Notes |
|---|---|---|---|
| Baltic birch | 18 mm / 3/4" | 17.5 – 18.3 | shop furniture, jigs |
| Baltic birch | 12 mm / 1/2" | 11.7 – 12.2 | drawers, boxes |
| Baltic birch | 6 mm / 1/4" | 5.5 – 6.2 | backs, templates |
| Marine ply (BS1088) | 12 / 18 mm | measure | boat parts, epoxy-coat cut edges |
| MDF | 18 mm | 18.0 | templates, paint-grade only, never wet |
| HDPE / StarBoard | 1/2" | 12.7 | marine panels, cutting boards: single-flute O-flute bit |
| G10 / FR4 | 3 – 6 mm | | backing plates: carbide, dust extraction + respirator |
| Aluminium 6061 | ≤ 6 mm | | shallow passes, lubricant, single-flute |
