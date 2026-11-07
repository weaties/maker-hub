#!/usr/bin/env bash
# Front Panel Express panel: panel.json -> fpe/<name>.fpjs (run in Front Panel Designer),
# SolidCraft model (checked against the analytic volume), DXF pair, pictures.
set -euo pipefail
cd "$(dirname "$0")"
find_hub() { local d="$PWD"; while [[ "$d" != / ]]; do [[ -f "$d/.maker-hub" ]] && { echo "$d"; return; }; d="$(dirname "$d")"; done
  echo "build.sh: no .maker-hub above $PWD; clone this repo into <hub>/projects/ or set MAKER_HUB" >&2; return 1; }
HUB="${MAKER_HUB:-$(find_hub)}"; SC="$HUB/tools/bin/solidcraft-cli"
NAME="$(python3 -c 'import json;print(json.load(open("panel.json"))["name"])')"
mkdir -p out
[[ -f vent.json ]] && "$SC" run vent.json --quiet          # free contours drawn in SolidCraft -> DXF

echo "== check: model without engraving vs analytic volume"
expected="$(uv run -q "$HUB/tools/fpe/panel.py" panel.json --no-text | python3 -c 'import json,sys;print(json.load(sys.stdin)["expected_volume_mm3_without_text"])')"
"$SC" eval "fpe/$NAME.solidcraft.json" --json-out out/measure.json
python3 - "$expected" <<'PY'
import json,sys
exp=float(sys.argv[1]); b=json.load(open("out/measure.json"))["bodies"][0]
dev=abs(b["volume_mm3"]-exp)/exp*100
print(f"  model {b['volume_mm3']:.1f} mm3, analytic {exp:.1f} mm3, {dev:.3f} % apart, closed={b['closed']}")
sys.exit(0 if dev < 0.1 and b["closed"] else "volume mismatch: a feature missed or failed")
PY

echo "== generate (with engraving)"
uv run -q "$HUB/tools/fpe/panel.py" panel.json >/dev/null
"$SC" run "fpe/$NAME.solidcraft.json" --save "fpe/$NAME.sc" --quiet
"$SC" snapshot "fpe/$NAME.sc" --out out/panel-front.png --view top --width 1400 --height 860 --no-grid --no-axes >/dev/null
for f in outline cutouts; do uv run -q "$HUB/tools/plasma/check_dxf.py" "fpe/$NAME-$f.dxf" --thickness 1 --table 2000x2000 >/dev/null \
  || { echo "fpe/$NAME-$f.dxf has open contours or gaps"; exit 1; }; done
echo "== done: open fpe/$NAME.fpjs in Front Panel Designer (Edit > Scripts > Add > Start)"
