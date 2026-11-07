# Working with upstream SolidCraft

`tools/solidcraft` is a clone of **weaties/solidcraft** (a fork of tangency-labs/solidcraft):
`origin` = the fork, `upstream` = tangency-labs. `tools/update-solidcraft.sh` keeps it at the
installed release tag so its docs and skills match the binary.

## Feeding things back
- **Bugs or gaps found while modelling here:** follow upstream's `skills/solidcraft-reporting/SKILL.md`
  (minimal script, run twice, search all issues), draft below, and **file only after DW approves**:
  `gh issue create -R tangency-labs/solidcraft --label bug --title "…" --body-file <draft>.md`
- **Code contributions:** upstream's rules are strict and worth reading first (`AGENTS.md`,
  `CONTRIBUTING.md`, `skills/solidcraft-contributing`). Clean-room, so no GPL code (not even reading it);
  claim work with a draft PR; one topic per PR; `cargo xtask ci` before every commit.
  Needs a Rust toolchain (`rustup`, not installed yet). Work on a branch off `upstream/main`:
  ```sh
  cd tools/solidcraft
  git fetch upstream && git switch -c fix/<topic> upstream/main
  # … change, cargo xtask ci …
  git push -u origin fix/<topic> && gh pr create -R tangency-labs/solidcraft --draft
  git checkout v<installed version>      # back to the pinned docs when done
  ```
- Hub-side workarounds for upstream gaps (like `tools/drawing/drawing.py` until SolidCraft's
  Drawings milestone lands) stay in the hub; delete them once upstream covers it.

## Drafts (not filed)

| Draft | Status | Search done |
|---|---|---|
| [view-dxf-fov.md](view-dxf-fov.md): `file.export_view_dxf` rejects a camera without `fov` | ready for review | 2026-11-07, no match |
| PETG / ASA as built-in materials | better as a comment on #12982 (user material libraries) | 2026-11-07 |
