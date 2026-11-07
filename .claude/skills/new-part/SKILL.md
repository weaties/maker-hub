---
name: new-part
description: Use when starting a new part, enclosure, bracket, jig, fixture, boat fitting or shop project in this hub, or when modeling any solid with SolidCraft (script or MCP). Covers where it goes, how to plan it, how to build and verify it.
---

# New part

## 1. Place it
- Pick the repo and area. DW's own parts go in `projects/personal/<area>/`, where the areas are `boat/`, `shop/` (maker-space furniture, jigs, fixtures), `electronics/` and `home/`. Parts for the plasma table go in `projects/plasma-cutter/parts/`. A big new project with other collaborators gets its own repo (`projects/README.md`); ask first.
- Folder name = part slug, kebab-case: `projects/personal/boat/winch-handle-holder/`.
- `cp -R templates/part <folder>` then rename `part.json` → `<slug>.json` (build.sh uses the folder name).
- Give it the next ID in its README (`EL-002`, `BT-001`, `SH-001`, `HM-001`, `PC-001` for the plasma table): `grep -rh "^# [A-Z][A-Z]-" projects/` shows the ones in use. Add it to that repo's README parts table.

## 2. Plan as numbers first (write it into the README)
- What it mates with, with **measured** dimensions (ask the user to measure; never guess a fit-critical dimension, and mark any number taken from a datasheet or memory as "unverified").
- Process (print / Shaper / both) and material, from `library/materials.md`; the boat rules are in the `boat-parts` skill.
- Parameters, the placement (centre on the origin so mirrors and patterns work), every feature, and the expected volume and bounding box.

## 3. Build
- The source of truth is the script `<slug>.json`: `{"commands":[...]}` of SolidCraft commands.
- Before writing commands read `tools/solidcraft/skills/solidcraft-modeling/SKILL.md` and its `reference.md` (plane axes, ids, traps). Look up one command with:
  `python3 -c "import json,subprocess;c={x['id']:x for x in json.loads(subprocess.check_output(['tools/bin/solidcraft-cli','commands']))};print(c['solid.hole']['params'])"`
  Never dump the full command list into context (570 commands, ~100 KB).
- Build in stages: write the script up to one stage, then `tools/bin/solidcraft-cli eval <slug>.json` and compare volume / bbox / face count with your hand numbers before adding the next stage. A cut that leaves the volume unchanged missed.
- Interactive alternative: the `solidcraft` MCP server (`.mcp.json`) runs a headless session with `batch`, `measure`, `screenshot`. When done, `timeline.export_script` writes the history back to `<slug>.json`.
- Name every feature and body. Put user-facing sizes in `parameters.add` with comments.
- Conventions from experience: pass `"fov":0` in any camera given to `file.export_view_dxf`; `sketch.text` bold needs an installed font (`"font":"Arial","bold":true`); PETG/ASA need `material.create`; `--section` takes `{"plane":{origin,normal}}`.

## 4. Verify and publish
- `./build.sh --fast`, then look at `out/snap-iso.png` (Read it). Add views that show the features that matter (`snapshot --camera`, `--section`, `--body Name:opacity=0.3`).
- Fill the README table, then log the version in the README Log.
- Commit in the **project's** repo, not the hub: `git -C projects/personal add <folder> && git -C projects/personal commit`. Push only when DW asks.
- Print parts: the `print-prep` skill. Shaper parts: the `shaper-cut` skill. Plasma parts: the `plasma-cut` skill. Drawings and renders: the `drawings-and-renders` skill.
