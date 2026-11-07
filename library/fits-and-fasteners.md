# Fits and fasteners

Starting values for FDM (0.4 mm nozzle) and Shaper work. **Calibrate**: when a print or cut
proves a number wrong, fix it here with the date and what was tested, so every later part benefits.

## Printed fit clearances (per side)
| Fit | Clearance | Use |
|---|---|---|
| Press / interference | 0.0 – 0.05 | bearings, magnets (test first) |
| Snug / friction lid | 0.2 – 0.3 | lids, lips (Pi 5 case uses 0.3) |
| Sliding | 0.3 – 0.4 | drawers, sliders |
| Loose / print-in-place | 0.5+ | hinges printed assembled |

Holes print undersize by ~0.1-0.2 mm on diameter; horizontal holes also go oval. Model a vertical
hole +0.2 on diameter, or drill to size.

## Screws into plastic
| Thread | Self-tap pilot | Clearance (normal) | Heat-set insert hole* | Head counterbore |
|---|---|---|---|---|
| M2 | 1.6 | 2.4 | 3.2 | Ø4.0 × 2.2 |
| M2.5 | 2.2 | 2.9 | 3.6 | Ø5.0 × 2.7 |
| M3 | 2.6 | 3.4 | 4.0 – 4.2 | Ø6.0 × 3.2 |
| M4 | 3.4 | 4.5 | 5.6 | Ø8.0 × 4.2 |
| M5 | 4.3 | 5.5 | 6.4 | Ø9.5 × 5.2 |
| #8 wood | 2.8 (soft) / 3.2 (hard) | 4.5 | — | — |
| #10 wood | 3.2 / 3.6 | 5.0 | — | — |
| 1/4-20 | — | 6.8 | 8.0 (insert) | Ø11 × 6.5 |

*Insert holes vary by brand; check the insert's datasheet and record the brand here.

Bosses: OD ≈ 2.2-2.5 × screw diameter; walls around a heat-set insert ≥ 1.6 mm.

## Marine hardware
- Use **316 stainless** fasteners above and below deck; 304 rusts. Never mix with aluminium without isolation (Tef-Gel / nylon washers).
- Through-deck: oversize the hole, fill with epoxy, redrill (core isolation), bed with butyl or polysulfide sealant (not silicone; and not 5200 unless it's never coming off).
- Backing plates: spread load ≥ 3× the fastener spacing; G10/FR4, aluminium, or 18 mm marine ply (Shaper-cut).
