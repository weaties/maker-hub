#!/usr/bin/env bash
# Rebuild this part from NAME.json. ./build.sh [--fast]  (--fast skips the path-traced render)
set -euo pipefail
cd "$(dirname "$0")"
find_hub() { local d="$PWD"; while [[ "$d" != / ]]; do [[ -f "$d/.maker-hub" ]] && { echo "$d"; return; }; d="$(dirname "$d")"; done
  echo "build.sh: no .maker-hub above $PWD; clone this repo into <hub>/projects/ or set MAKER_HUB" >&2; return 1; }
HUB="${MAKER_HUB:-$(find_hub)}"; SC="$HUB/tools/bin/solidcraft-cli"
NAME="$(basename "$PWD")"
mkdir -p out print
"$SC" run "$NAME.json" --save "$NAME.sc" --out "$NAME.step" --quiet
"$SC" eval "$NAME.sc" --json-out out/measure.json
python3 -c "
import json; d=json.load(open('out/measure.json'))
for b in d['bodies']: print(f'  {b[\"name\"]:12} {b.get(\"volume_mm3\",0):10.1f} mm3 {b.get(\"mass_g\",0):7.1f} g faces={b[\"faces\"]} closed={b[\"closed\"]}')"
[[ -f print.json ]] && "$SC" run print.json --in "$NAME.sc" --quiet
"$SC" snapshot "$NAME.sc" --out out/snap-iso.png --view iso --width 1200 --height 800 --no-grid --no-axes >/dev/null
[[ "${1:-}" != "--fast" ]] && "$SC" render "$NAME.sc" --out out/render.png --width 1600 --height 1000 --progressive --samples 128 --overwrite >/dev/null
# Bambu Lab: slice print/*.3mf for this Mac's printer (material/settings from slice.json; skipped
# without Bambu Studio or with NO_SLICE=1)
[[ -f print.json && -z "${NO_SLICE:-}" && -d "${BAMBU_STUDIO_APP:-/Applications/BambuStudio.app}" ]] && "$HUB/tools/bambu/slice.py" .
[[ -f drawing.json ]] && uv run -q "$HUB/tools/drawing/drawing.py" drawing.json
[[ -f shaper.json ]] && "$SC" run shaper.json --in "$NAME.sc" --quiet && for f in shaper/*.dxf; do uv run -q "$HUB/tools/shaper/to_shaper_svg.py" "$f"; done
if [[ -f plasma.json ]]; then
  : "${PLASMA_T:?set PLASMA_T to the plate thickness in mm, e.g. PLASMA_T=3.2 ./build.sh}"
  mkdir -p plasma && "$SC" run plasma.json --in "$NAME.sc" --quiet
  for f in plasma/*.dxf; do [[ "$f" == *.r12.dxf ]] && continue
    uv run -q "$HUB/tools/plasma/check_dxf.py" "$f" --thickness "$PLASMA_T" --out "${f%.dxf}.r12.dxf"; done
fi
echo done
