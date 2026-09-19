---
name: rebuild-and-ship
description: Rebuild every part of waveshare-round-stand, validate meshes, re-render, link-check docs, then commit, push and mirror to the Windows folder. Use after any change to geometry, parameters, or docs in this repo.
---

# Rebuild and ship

Run from the repo root (`~/Projects/waveshare-round-stand`).

1. `./build_all.sh` — stops on the first failure. Fix, re-run.
2. **Open the renders and look as a skeptic** before writing anything:
   `preview-stands.png`, `preview-docks.png`, `renders/*.png`,
   `pod/renders/*.png`. Ask of each: does the board sit where the numbers
   say? Is anything hidden, floating, buried, below the desk? Three real
   errors in this project were invisible in reports and obvious in renders.
3. If a number changed because of a print, `docs/PRINT-LOG.md` gets its entry
   **first**; if a design choice changed, `docs/DESIGN.md` gets a new dated
   entry (never edit old ones).
4. Commit as Aaron and push:
   ```
   git add -A
   git -c user.name="Aaron Herres" -c user.email="iam@hypnodroid.com" commit -F - <<'MSG'
   <what changed and why, in prose; the "why" is the useful part>

   Co-Authored-By: <the attribution line this session specifies>
   MSG
   git push origin main
   ```
5. Mirror to Windows — he slices from there:
   ```
   S=~/Projects/waveshare-round-stand; D=/mnt/d/Projects/waveshare-round-stand
   for f in "$D"/*; do b=$(basename "$f"); [ -f "$f" ] && [ ! -e "$S/$b" ] && [ ! -e "$S/archive/$b" ] && echo "NOT MINE: $b"; done
   ```
   Anything printed as NOT MINE is his (`stand.3mf` always is) — leave it.
   Then `cp` the tree over: `*.md *.py *.sh *.scad preview-*.png LICENSE`,
   `stl/`, `renders/`, `reference/`, `archive/`, `pod/` (py, md, `stl/`,
   `renders/`). Verify with `md5sum` that STLs match.
6. Tell him: what to print, one decision if there is one, and what is still
   unprinted. Terse — he reads on a phone.

Never delete a superseded STL or render: `mv` to `archive/` and add a line to
`archive/NOTE.md`.
