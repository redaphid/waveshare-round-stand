---
name: rebuild-and-ship
description: OWNER ONLY (Aaron's own sessions). Rebuild every part, look at the renders, commit as the owner, push, and mirror the tree to his Windows slicing folder. Use after a geometry or docs change in the owner's checkout. A contributor uses change-a-model and opens a PR instead.
---

# Rebuild and ship (owner only)

**If you are not working in Aaron's checkout for Aaron, stop.** Use
`change-a-model` and open a PR. The paths below exist only on his machines;
`CLAUDE.md` (section *Owner's workflow*) has the facts.

1. `./build_all.sh`. It stops on the first failure. Fix, rerun.
2. **Open the renders of what changed and look as a skeptic** before writing
   anything: does the badge sit where the numbers say? Is anything hidden,
   floating, buried, below the desk?
3. A number changed because of a print: `docs/PRINT-LOG.md` gets its entry
   **first**. A design choice changed: a new dated entry in `docs/DESIGN.md`.
4. Commit as the owner and push:
   ```
   git add -A
   git -c user.name="Aaron Herres" -c user.email="iam@hypnodroid.com" commit -F - <<'MSG'
   <what changed and why, in prose; the "why" is the useful part>

   Co-Authored-By: <the attribution line this session specifies>
   MSG
   git push
   ```
5. Mirror to Windows after a merge (he slices from there):
   ```
   S=~/Projects/waveshare-round-stand; D=/mnt/d/Projects/waveshare-round-stand
   for f in "$D"/*; do b=$(basename "$f"); [ -f "$f" ] && [ ! -e "$S/$b" ] && echo "NOT MINE: $b"; done
   ```
   Anything printed as NOT MINE is his (`stand.3mf` always is): leave it.
   Then copy the tracked tree over and verify with `md5sum` that the STLs
   match.
6. Tell him: what to print, one decision if there is one, what is still
   unprinted. Terse; he reads on a phone.

Superseded STLs leave the tree: `git rm` them and add a line to
`archive/NOTE.md` naming the last commit that has them.
