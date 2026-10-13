# AGENTS.md

Project rules live in `CLAUDE.md`. This file holds one extra rule.

## Keep the pocketwatch whiteboard current

The pocketwatch schematic board is the project's intro for anyone new:
**https://draw.hypnodroid.com/b/pocketwatch-schematics** (draw MCP, board name
`pocketwatch-schematics`, theme `architect-parchment`).

Update it in the same session as any change that alters what it shows, before
you report the work done:

| change | board part to update |
|---|---|
| any number in `Badge` or `Case` in `pocketwatch/build_pocketwatch.py` (bore, recess, plate, lid, battery, clearances) | **A** side section and legend, **B** front view labels |
| a part added, removed or renamed; print orientation or order; assembly steps | **C** parts and print |
| a guess replaced by a measurement, or a new guess or open question | **D** guesses and open questions |
| a print result, a branch change, a handoff | the **STATUS** note |

How:

1. `open` the board by name, then `read` it so you edit what is there, not what
   you remember.
2. `patch` the existing ids (`leg`, `lblrec`, `tc`, `td`, `status`, `rec`,
   `bore`, and so on). Do not `clear` and redraw, which loses anyone's manual edits.
3. If geometry moved, resize the shapes to match. Scale is 14 px/mm in A and
   8 px/mm in B, and the numbers in the labels must match the code.
4. Take a `screenshot` if a browser has the board open. Look for overlapping labels.
5. Update the STATUS date.

The board is documentation, not a source of truth. The code and
`docs/PRINT-LOG.md` win if they disagree with it. If the draw MCP is down, say so
in your report and leave a line in `HANDOFF.md` that the board is stale.

Measured schematics (frames S, R, V for the hoop stand) come from the CAD, not by hand:
`~/.venvs/cad/bin/python pocketwatch/stands/hoop/board_schematics.py /tmp/ops.json` writes draw ops cut from
the same solids the build checks. Re-run it after a geometry change and `put` the ops (same ids, so it overwrites).
Prefer this flat, dimensioned style over traced 3D renders: Aaron asked for it (2026-10-13).
