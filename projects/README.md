# projects/

Each folder here is its **own git repo**, cloned into the hub so its build scripts find the tools
(they look for `.maker-hub` above them). The hub repo ignores everything here but this file.

| Folder | Repo | Who | What |
|---|---|---|---|
| `personal/` | `weaties/maker-projects` (private) | DW | boat, shop, electronics, home parts |
| `plasma-cutter/` | `weaties/plasma-cutter` (private) | DW, Stefan | the JD's Garage CNC plasma table build |

`tools/clone-projects.sh` clones whichever of these you have access to.
New big project with its own collaborators: `mkdir projects/<name>`, `git init`, and add a row here and in the script.
