# Maker hub

The tooling home for all of DW's modelling and fabrication: 3D-printed parts, Shaper Origin cuts, the
CNC plasma table (built with Stefan), the maker space being set up in the office, and parts for the boat.
CAD is **SolidCraft** (open-source, headless CLI + MCP), driven by scripts, so every part rebuilds from text.

## Repos: this hub holds tools, not projects
| Path | Repo | Notes |
|---|---|---|
| `.` | `weaties/maker-hub` | tools, skills, templates, library, this file |
| `projects/personal/` | `weaties/maker-projects` (private) | DW's parts: `boat/ shop/ electronics/ home/` |
| `projects/plasma-cutter/` | `weaties/plasma-cutter` (private, shared with Stefan) | JD's Garage Gen 2.0 table build |
| `tools/solidcraft/` | `weaties/solidcraft` fork; `upstream` = tangency-labs | pinned at the installed tag; see `docs/upstream/` |

The hub's git ignores `projects/*`. **Commit project work in the project's own repo** (`git -C projects/<name> …`).
A new project with its own collaborators gets its own repo; see `projects/README.md`. Parts go in the existing repo.

## Layout
```
projects/<repo>/<area>/<slug>/   one folder per part (plasma-cutter: parts/<slug>/)
  <slug>.json                SOURCE OF TRUTH: SolidCraft command script
  build.sh                   regenerates everything below (finds the hub via .maker-hub)
  <slug>.sc / .step          design (opens in the app) / neutral CAD
  print.json  -> print/      oriented 3MF per body
  shaper.json -> shaper/     DXF + Shaper SVG
  plasma.json -> plasma/     DXF + checked R12 DXF
  drawing.json -> out/       dimensioned sheets (svg/pdf/png)
  out/                       renders, snapshots, measurements
  README.md                  ID, status, requirements, measured mating dims, log
templates/part/              copy to start a part
library/                     fits-and-fasteners.md, materials.md (calibrated numbers live here)
tools/bin/solidcraft-cli     SolidCraft CLI (gitignored; tools/update-solidcraft.sh installs/updates)
tools/drawing/drawing.py     view DXFs -> dimensioned drawing sheets
tools/shaper/to_shaper_svg.py DXF -> Shaper Origin SVG (cut types by fill/stroke)
tools/plasma/check_dxf.py    DXF checks for plasma (open contours, gaps, table size, small holes) + R12 copy
tools/dxf/dxfloops.py        shared loop/hole detection for the 2D tools
tools/clone-projects.sh      clone/pull the project repos into projects/
docs/upstream/               how to report to / contribute to SolidCraft; drafted issues
```

## Skills (read the one that fits before starting)
| Task | Skill |
|---|---|
| Any new part, or modelling in SolidCraft | `new-part` |
| Getting a part onto the printer | `print-prep` |
| Anything for the Shaper Origin | `shaper-cut` |
| Plasma parts, DXFs for plasma, or the plasma table build | `plasma-cut` |
| Renders, sections, drawings, a page to share | `drawings-and-renders` |
| Anything for the boat or outdoors | `boat-parts` |

SolidCraft's own agent docs: `tools/solidcraft/skills/solidcraft-modeling/SKILL.md` + `reference.md`
(command shapes, plane axes, traps), `solidcraft-editing` (changing a design), `solidcraft-mechanisms`
(assemblies), `solidcraft-reporting` (bug reports), `docs/mcp.md` (MCP tools, camera conventions).
Their contribution rules (clean-room, draft-PR claims, `cargo xtask ci`) apply only when changing SolidCraft itself.

## Rules
- **Scripts are the source.** Edit `<slug>.json`, run `./build.sh` (`--fast` skips the ~40 s render). Don't hand-edit `.sc`, exports or `out/`. Interactive MCP work gets written back with `timeline.export_script`.
- **Verify with numbers.** After each build stage compare `eval` volume / bbox / face count with a hand calculation; then Read a snapshot. "It ran" is not verification.
- **Fit-critical dimensions are measured, not remembered.** Mark datasheet or from-memory values "unverified" in the README until a test print or cut confirms them.
- **Close the loop.** Log each print/cut/install outcome in the part README; general lessons (clearances, insert sizes, real plywood thickness, plasma cut charts) go into `library/`.
- **Paid plans stay out of git.** JD's Garage plans live in `projects/plasma-cutter/plans/` (ignored). Never commit, paste or publish them or files derived from them.
- **Upstream:** a SolidCraft bug or gap gets a minimal repro and a draft in `docs/upstream/`; file it only when DW says so.
- Units are mm. Centre parts on the origin. Name every feature and body; user-facing sizes are parameters with comments.
- SolidCraft is pre-1.0 (v0.30.1 here). After `tools/update-solidcraft.sh`, rebuild a known part and check its volumes are unchanged before trusting the new version.

## Machines and software (fill in as the shop grows)
- Printer: Bambu Lab (Bambu Studio installed; model: _TBD_). UltiMaker Cura also installed.
- Shaper Origin: _TBD_ (generation; bits on hand: 1/4" & 1/8" assumed).
- CNC plasma table: being built (JD's Garage Gen 2.0, 711 × 812 mm, ESP32). Not cutting yet; see `projects/plasma-cutter/README.md`.
- SolidCraft desktop app: not installed (DMG from the GitHub releases). With it running, `solidcraft-cli mcp --connect` lets Claude drive the visible app.
- Collaborator: Stefan (plasma table). GitHub handle: _TBD_.
