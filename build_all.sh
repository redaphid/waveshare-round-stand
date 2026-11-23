#!/usr/bin/env bash
# Rebuild every part, run every check, re-render, link-check the docs.
# Run from the repo root before any commit that touches geometry or docs.
#   ./build_all.sh              everything, with renders (about 6 min)
#   ./build_all.sh --no-render  everything except the pocketwatch renders (about 2 min)
set -euo pipefail
cd "$(dirname "$0")"
PY=$(tools/py --which)
"$PY" -c "import manifold3d, trimesh, numpy, matplotlib, tomllib" 2>/dev/null \
  || { echo "CAD stack missing for $PY: run ./setup.sh"; exit 1; }
RENDER=
[ "${1:-}" = --no-render ] && RENDER=--no-render

echo "== desk stands + docks (retired designs, still checked) =="
"$PY" build_stands.py | grep -E "===|checks|Error" || true
for f in stl/small/Stand.stl stl/large/Stand*.stl stl/large/Dock*.stl; do "$PY" check_stl.py "$f" | tail -1 | sed "s|^|  $(basename "$f"): |"; done
"$PY" preview.py

echo "== button-post stands =="
for b in BOOT RESET; do "$PY" build_stand_button.py "$b" | grep -E "stl/|assert|Error"; done

echo "== slot fit gauge =="
"$PY" build_fit_gauge.py | grep -E "stl/"

echo "== pod =="
"$PY" pod/build_pod.py    | grep -vE "^wrote"
"$PY" pod/build_pod.py 26 | grep -E "^pod"
"$PY" pod/build_cup_stand.py | grep -E "^Pod cup test"

echo "== pocketwatch family: every pocketwatch/**/build_*.py ${RENDER:+(no renders)} =="
for s in $(find pocketwatch -name 'build_*.py' | sort); do
  if out=$("$PY" "$s" $RENDER 2>&1); then
    printf '  ok    %-56s %3d checks\n' "$s" "$(grep -c '\[ok\]' <<<"$out" || true)"
  else
    grep -E '\[FAIL\]' <<<"$out" || tail -15 <<<"$out"
    echo "  FAIL  $s"; exit 1
  fi
done

echo "== catalog: every STL has a row in stl/catalog.toml; regenerate stl/README.md =="
"$PY" build_catalog.py

echo "== docs: links, images and backticked paths in every tracked *.md =="
"$PY" check_docs.py
find . -name __pycache__ -not -path "./.venv/*" -prune -exec rm -rf {} +
echo "== OK. Now LOOK at the renders of what you changed before you report. =="
