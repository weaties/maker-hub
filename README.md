# Maker hub

Tooling for parts, jigs, shop furniture, boat fittings and a CNC plasma table, modelled in
[SolidCraft](https://github.com/tangency-labs/solidcraft) as text scripts and built into print
files, Shaper Origin SVGs, plasma DXFs, drawings and renders.

The projects live in their own repos, cloned into `projects/`:

| Folder | Repo | What |
|---|---|---|
| `projects/personal/` | weaties/maker-projects (private) | boat, shop, electronics, home parts |
| `projects/plasma-cutter/` | weaties/plasma-cutter (private) | JD's Garage Gen 2.0 CNC plasma table |

## Set up on a new machine
```sh
git clone git@github.com:weaties/maker-hub.git ~/src/solidcraft && cd ~/src/solidcraft
tools/update-solidcraft.sh      # SolidCraft CLI (checksum-verified) + source clone of the fork
tools/clone-projects.sh         # the project repos you have access to
```
Needs macOS, `gh`, `uv`, and `rsvg-convert` (`brew install librsvg`, for PDF/PNG drawings).

## Use
```sh
cp -R templates/part projects/personal/shop/my-jig && mv projects/personal/shop/my-jig/{part,my-jig}.json
projects/personal/shop/my-jig/build.sh       # model -> .sc, .step, print/, out/
```
Or ask Claude ("new part for the boat: a holder for the winch handle"); it follows `CLAUDE.md`
and the skills in `.claude/skills/`.

| Tool | Does |
|---|---|
| `tools/drawing/drawing.py` | dimensioned drawing sheets from a SolidCraft design (until SolidCraft ships drawings) |
| `tools/shaper/to_shaper_svg.py` | DXF to Shaper Origin SVG with cut types |
| `tools/plasma/check_dxf.py` | checks a DXF for plasma CAM and writes a clean R12 copy |
| `tools/fpe/panel.py` | Front Panel Express: panel spec to an FPD script, a SolidCraft model and DXFs |
| `tools/update-solidcraft.sh` | installs or updates SolidCraft |

Contributing back to SolidCraft: [docs/upstream/](docs/upstream/).
