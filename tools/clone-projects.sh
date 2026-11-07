#!/usr/bin/env bash
# Clone (or pull) the project repos into projects/. Skips the ones you can't access.
set -uo pipefail
HUB="$(cd "$(dirname "$0")/.." && pwd)"
REPOS=(
  "personal       weaties/maker-projects"
  "plasma-cutter  weaties/plasma-cutter"
)
for row in "${REPOS[@]}"; do
  read -r dir repo <<<"$row"
  dest="$HUB/projects/$dir"
  if [[ -d "$dest/.git" ]]; then
    echo "== $dir: pull"; git -C "$dest" pull --ff-only
  elif gh repo view "$repo" >/dev/null 2>&1; then
    echo "== $dir: clone $repo"; gh repo clone "$repo" "$dest"
  else
    echo "== $dir: no access to $repo, skipped"
  fi
done
