#!/usr/bin/env bash
# Make a repo-local .venv with the CAD stack and prove it imports. Safe to run again at any time.
# Linux, macOS, or Windows in Git Bash or WSL. Needs Python 3.11 or newer.
set -euo pipefail
cd "$(dirname "$0")"

ok_python() { "$1" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; }

venv_py() {
  for c in .venv/bin/python .venv/Scripts/python.exe; do [ -x "$c" ] && { echo "$c"; return; }; done
}

if [ -z "$(venv_py)" ] || ! ok_python "$(venv_py)"; then
  base=
  for c in "${PYTHON:-}" python3.14 python3.13 python3.12 python3.11 python3 python; do
    [ -n "$c" ] && command -v "$c" >/dev/null && ok_python "$c" && { base=$c; break; }
  done
  [ -n "$base" ] || {
    echo "Need Python 3.11 or newer. Install it (python.org, brew install python, or your distro's python3), then re-run ./setup.sh."
    exit 1
  }
  echo "== making .venv with $("$base" --version)"
  rm -rf .venv
  "$base" -m venv .venv
fi
PY=$(venv_py)

stamp=.venv/requirements.installed
if ! cmp -s requirements.txt "$stamp"; then
  echo "== installing requirements.txt"
  "$PY" -m pip install --quiet --upgrade pip
  "$PY" -m pip install --quiet -r requirements.txt
  cp requirements.txt "$stamp"
else
  echo "== requirements already installed"
fi

echo "== smoke test"
"$PY" - <<'PY'
import sys, tomllib
from importlib.metadata import version
import numpy, trimesh, manifold3d as m3, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot
cube = m3.Manifold.cube([10, 10, 10])
assert abs(cube.volume() - 1000) < 1e-6, "manifold3d cube volume"
print("  python " + sys.version.split()[0] + ", "
      + ", ".join(f"{p} {version(p)}" for p in ("numpy", "manifold3d", "trimesh", "matplotlib")))
PY
echo "== ready. Next: ./build_all.sh --no-render (about 2 min) or ./build_all.sh (with renders, about 6 min)"
