#!/usr/bin/env bash
# Rebuild every part, validate every mesh, re-render, link-check the docs.
# Run from the repo root before any commit that touches geometry or docs.
set -euo pipefail
cd "$(dirname "$0")"
CAD=~/.venvs/cad/bin/python
[ -x "$CAD" ] || { echo "no CAD venv -- see docs/TOOLCHAIN.md"; exit 1; }

echo "== stands + docks (system python) =="
python3 build_stands.py | grep -E "===|checks|Error" || true
for f in stl/*_stand.stl stl/*DOCK*.stl; do python3 check_stl.py "$f" | tail -1 | sed "s|^|  $(basename "$f"): |"; done
python3 preview.py

echo "== button-post stands (venv) =="
for b in BOOT RESET; do "$CAD" build_stand_button.py "$b" | grep -E "stl/|assert|Error"; done

echo "== fit gauge (venv) =="
"$CAD" build_fit_gauge.py | grep -E "stl/"

echo "== pod (venv) =="
"$CAD" pod/build_pod.py    | grep -vE "^wrote"
"$CAD" pod/build_pod.py 26 | grep -E "^pod"
"$CAD" pod/build_cup_stand.py | grep -E "^cup-stand"
# pod/README links pod/stl/ -- keep it in step with the live stl/ copies
cp stl/pod-gap*.stl stl/clip-*.stl stl/trim-ring-*.stl stl/cup-stand-*.stl pod/stl/

echo "== docs: relative links and images =="
python3 - <<'PY'
import re, os, sys
docs = ["README.md","PRINTING.md","BOARDS.md","CLAUDE.md","stl/README.md","pod/README.md",
        "reference/SOURCES.md","archive/NOTE.md","docs/DESIGN.md","docs/TOOLCHAIN.md","docs/PRINT-LOG.md"]
bad = 0
for doc in docs:
    if not os.path.exists(doc): print("  missing doc", doc); bad += 1; continue
    base = os.path.dirname(doc)
    for m in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)', open(doc).read()):
        t = m.group(1)
        if t.startswith("http"): continue
        if not os.path.exists(os.path.normpath(os.path.join(base, t.split('#')[0]))):
            print(f"  BROKEN {doc} -> {t}"); bad += 1
print(f"  {bad} broken"); sys.exit(1 if bad else 0)
PY
rm -rf __pycache__ pod/__pycache__
echo "== OK. Now LOOK at renders/, preview-*.png and pod/renders/ before you report. =="
