---
name: change-a-model
description: Change the geometry of any waveshare-round-stand model - find its build script and the dataclass or constants that drive it, edit, rebuild only that family, read the checks, render, compare before and after, update the catalog and log the decision. Use whenever someone wants a part bigger, smaller, longer, thicker, at another angle, for another battery or cable, or asks "how do I edit the model", "where is this dimension", "make X 2 mm longer".
---

# Change a model

Every STL is written by a Python script; never edit an STL. The numbers live
in frozen dataclasses (`Badge`, `Case`, `Stand`, `Key`, ...) or module
constants at the top of the script.

## 1. Find the source

```
grep -n -A4 '"<part or family name>"' stl/catalog.toml
```
The family's `script` is the file to run and its `edit` names what to change
(a part row can override both). Then read the script's docstring and the
dataclass: each field has a comment saying what it is and why it has that
value. Shared numbers:

| what | where | used by |
|---|---|---|
| the board itself (measured, or `ph(...)` guesses) | `Badge`, `pocketwatch/build_pocketwatch.py` | every pocketwatch design |
| case choices: bore, lip, walls, USB-C slot, snaps, plate | `Case`, same file | every pocketwatch design |
| USB-only plate fit | `PLATE_DISC_CLR`, `pocketwatch/build_pocketwatch_usb.py` | USB-only case and every stand built on it |
| hoop, tenon, snap arms | `Stand`, `pocketwatch/stands/hoop/build_hoop.py` | hoop, telegraph |
| telegraph lever, pin, knob, lean | `Key`, `pocketwatch/stands/hoop/build_hoop_telegraph.py` | telegraph |

Some values are **solved, not set** (the telegraph lever length, the hoop
height). Read the function that computes them before you look for a
constant; AGENTS.md has a worked example for the lever.

## 2. Baseline, then edit

```
./tools/py <script> --no-render > /tmp/before.txt
```
Change **one** thing. If it is in `Badge` or `Case`, every pocketwatch design
moves: you will run `./build_all.sh --no-render` at step 3 instead.

## 3. Rebuild and read the checks

```
./tools/py <script> --no-render > /tmp/after.txt; echo rc=$?
diff <(grep -v '\[ok\]' /tmp/before.txt) <(grep -v '\[ok\]' /tmp/after.txt)
```
- `rc=0` and no `[FAIL]` lines, or stop. A failed check is a physical
  problem (a wall too thin, a snap that will crack, a part that collides).
  **Fix the geometry, never loosen the check.** If the check itself is
  wrong, say why in the PR.
- The diff shows the summary lines that moved (arm lengths, forces, travel,
  clearances). Say which moved and by how much.
- Adding a new physical rule? Use `check(ok, label, margin)` from
  `build_pocketwatch.py`: the label states what must be true, the margin
  shows by how much.

## 4. Render and look

`./tools/py <script>` (no flag) writes the PNGs listed in the catalog row's
`renders`. Open each one and compare with the committed version
(`git show HEAD:<png> > /tmp/old.png`). Ask: is anything floating, buried,
colliding, hidden behind another part, or below the desk? Do not report a
change you have not looked at.

## 5. Catalog, status, log

- `git status --short stl/` lists the STLs that changed. A changed file is
  no longer the one that was printed: set its row's `status` to `unprinted`
  (or keep `needs-work` with `fixed = true` if this is the requested fix) in
  `stl/catalog.toml`.
- New, renamed or removed STL: edit `stl/catalog.toml` to match. Removed
  files leave the tree; add a line to `archive/NOTE.md` naming the last
  commit that has them.
- `./tools/py build_catalog.py` regenerates `stl/README.md`;
  `./tools/py build_catalog.py --check` must pass.
- A design decision gets a dated entry in `docs/DESIGN.md` (new entry; never
  edit old ones). A change made because of a print: the `docs/PRINT-LOG.md`
  entry comes first.
- If the change alters what the draw board shows, use `update-the-board`
  (or tell the owner it is stale).

## 6. Hand off

Commit on a branch with your own git identity, push, open a PR. The body
says: what changed, which numbers, the checks that moved, the renders to look
at, and which STLs now need a print. Family pages in `docs/models/` describe
each design in depth.
