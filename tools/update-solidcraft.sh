#!/usr/bin/env bash
# Install or update the SolidCraft CLI (tools/bin) and the source clone (tools/solidcraft, for its
# docs and agent skills). Verifies the release checksum before installing.
#   tools/update-solidcraft.sh            latest release
#   tools/update-solidcraft.sh v0.30.1    a specific release
set -euo pipefail
HUB="$(cd "$(dirname "$0")/.." && pwd)"
REPO=tangency-labs/solidcraft
TAG="${1:-$(gh release view -R "$REPO" --json tagName -q .tagName)}"
VER="${TAG#v}"
ASSET="solidcraft-cli-${VER}-macos-universal.zip"

current="$("$HUB/tools/bin/solidcraft-cli" --version 2>/dev/null | awk '{print $2}' || true)"
echo "installed: ${current:-none}   target: $VER"

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
gh release download "$TAG" -R "$REPO" -p "$ASSET" -p SHA256SUMS.txt -D "$tmp"
( cd "$tmp" && grep " $ASSET\$" SHA256SUMS.txt | shasum -a 256 -c - )
unzip -q -o "$tmp/$ASSET" -d "$tmp/x"
mkdir -p "$HUB/tools/bin"
cp "$tmp"/x/*/solidcraft-cli "$tmp"/x/*/solvecraft-cli "$HUB/tools/bin/"
"$HUB/tools/bin/solidcraft-cli" --version

# Source: checked out at the release tag so its docs/skills match the binary. If you have a fork of
# SolidCraft (or ask for one with SOLIDCRAFT_FORK=1) it's origin and tangency-labs is upstream, ready for
# contributions; otherwise it's a plain clone of tangency-labs. Contribution branches are left alone.
SRC="$HUB/tools/solidcraft"
if [[ ! -d "$SRC/.git" ]]; then
  FORK="$(gh api user -q .login)/solidcraft"
  if gh repo view "$FORK" >/dev/null 2>&1 || { [[ "${SOLIDCRAFT_FORK:-}" == 1 ]] && gh repo fork "$REPO" --clone=false --default-branch-only; }; then
    git clone --depth 50 "https://github.com/$FORK.git" "$SRC"
    git -C "$SRC" remote add upstream "https://github.com/$REPO.git"
  else
    git clone --depth 50 "https://github.com/$REPO.git" "$SRC"
    git -C "$SRC" remote add upstream "https://github.com/$REPO.git"
  fi
fi
git -C "$SRC" fetch --depth 50 --tags upstream
if [[ -n "$(git -C "$SRC" status --porcelain)" ]] || git -C "$SRC" symbolic-ref -q HEAD >/dev/null; then
  echo "tools/solidcraft has local changes or a branch checked out (contribution work?): not switching it."
  echo "  When done: git -C tools/solidcraft checkout $TAG"
else
  git -C "$SRC" checkout -q "$TAG"
fi
echo "source at: $(git -C "$SRC" describe --tags --always)"
echo "Release notes: gh release view $TAG -R $REPO"
echo "Next: rebuild a project (./build.sh) and compare its measured volumes before trusting the update."
