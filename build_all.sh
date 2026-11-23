#!/usr/bin/env bash
# Rebuild every part, validate every mesh, re-render, link-check the docs.
# Run from the repo root before any commit that touches geometry or docs.
set -euo pipefail
cd "$(dirname "$0")"
CAD=~/.venvs/cad/bin/python
[ -x "$CAD" ] || { echo "no CAD venv -- see docs/TOOLCHAIN.md"; exit 1; }

echo "== stands + docks (system python) =="
python3 build_stands.py | grep -E "===|checks|Error" || true
for f in stl/small/Stand.stl stl/large/Stand*.stl stl/large/Dock*.stl; do python3 check_stl.py "$f" | tail -1 | sed "s|^|  $(basename "$f"): |"; done
python3 preview.py

echo "== button-post stands (venv) =="
for b in BOOT RESET; do "$CAD" build_stand_button.py "$b" | grep -E "stl/|assert|Error"; done

echo "== fit gauge (venv) =="
"$CAD" build_fit_gauge.py | grep -E "stl/"

echo "== pod (venv) =="
"$CAD" pod/build_pod.py    | grep -vE "^wrote"
"$CAD" pod/build_pod.py 26 | grep -E "^pod"
"$CAD" pod/build_cup_stand.py | grep -E "^Pod cup test"

echo "== catalog: every STL has a row in stl/catalog.toml; regenerate stl/README.md =="
python3 build_catalog.py

echo "== docs: links, images and backticked paths in every tracked *.md =="
python3 check_docs.py
rm -rf __pycache__ pod/__pycache__
echo "== OK. Now LOOK at renders/, preview-*.png and pod/renders/ before you report. =="
