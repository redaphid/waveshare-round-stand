---
name: update-the-board
description: Keep the pocketwatch-schematics draw board in step with the repo - connect to it, find the frame a change affects, patch it without clobbering anyone, regenerate the CAD-cut schematics, use the board's custom widgets and board skills, and export screenshots for the docs. Use after any change to the pocketwatch case, the hoop or telegraph, a measurement, a print result, or when asked to show something on the board, connect the board, or refresh README images.
---

# Update the board

The board `pocketwatch-schematics` (theme `architect-parchment`) is the
zoomable guide to the pocketwatch and the telegraph: what is proven, what is
concept art, the measurements and the open guesses. **It is documentation,
not a source of truth.** The code and `docs/PRINT-LOG.md` win when they
disagree. `docs/BOARD.md` has screenshots of each part.

## Connect

```
claude mcp add --transport http pocketwatch-board https://draw.hypnodroid.com/b/pocketwatch-schematics/mcp
```
Sign in when asked. Anyone can read it. Writing needs the owner to grant
edit access; without it, do the steps up to *Patch* and send the owner the
change as a short list (frame id, old value, new value).

## Rules

- Name yourself (`name`) and pass that same agent name on every call.
- **Look before you read:** `screenshot` the board, then the frame, then
  `read` that frame only for exact ids and numbers. Never read the whole board.
- **Patch existing ids. Never `clear`, never redraw someone else's frame**:
  it erases manual edits.
- Draw pictures, not paragraphs: shapes to scale, labels of 1 to 3 words,
  numbers that match the code.
- `screenshot` what you changed and look for overlaps before you report.
- If a draw tool surprises you, report it with the `feedback` tool.

## Which frame a change touches

| change in the repo | frame(s) |
|---|---|
| a number in `Badge` or `Case` (bore, recess, plate, lid, battery, clearances) | **Measurements** frame: `fA` side section and legend (14 px/mm), `fB` front view and bore (8 px/mm), `fC`, `fD` |
| a battery | `fBat` "Batteries" |
| a guess measured, or a new guess | the guess cards in `wx-show` (`wx-guesses`), and `fD` |
| hoop stand geometry | `f-hoop`, `ms-side`, `ms-front`, `ms-rock` (regenerate, below) |
| telegraph geometry | `tg-overview`, `tg-side`, `tg-front`, `tg-lever`, `tg-fits` |
| a concept's geometry | `f-<name>` and `ms-<name>-*` (pedestal, hood, kickstand, scissor, sidepod, stalk, lowprofile, braun, te) |
| a fit tested on a print | `wx-fits`, `tg-fits` |
| a print result | `wx-prints`; the proven-vs-concept map `g-map` |
| status of the cleanup or handoff | `cleanup-status` |

The front door is `g-front` ("Start here"); the camera tour is the present
path `golden-path`.

## Regenerate the CAD-cut schematics

Flat, dimensioned sections cut from the same solids the build checks (the
owner asked for this style over traced renders). After a geometry change:
```
tools/py pocketwatch/stands/hoop/board_schematics.py /tmp/ops.json     # ms-side, ms-front, ms-rock
tools/py pocketwatch/board/<name>.py /tmp/ops-<name>.json              # a concept: braun, hood, kickstand, ...
```
Each writes one `put` op whose drafts keep the same ids, so `draw` with it
overwrites those shapes in place. The telegraph frames have no generator in
the repo: patch their labels from the summary lines the telegraph script
prints (`nub arm`, `knob arm`, `click at`).

## Board skills and widgets

List the board's own skills with `read({skills: true})` and read one with
`read({skill: "<name>"})`. They encode the board's conventions:

| board skill | does |
|---|---|
| `connect-from-claude` | add the MCP URL, then fly to `g-front` |
| `check-a-fit` | record a fit result as a fit-check card |
| `log-a-print` | record a print as a print-result card; needs a PRINT-LOG entry or the owner's words |
| `answer-a-guess` | replace a guess card with the measurement |
| `watch-the-printer` | refresh the printer-state card (owner's printer) |
| `refresh-schematics` | regenerate the CAD-cut frames (the commands above) |
| `export-readme-shots` | screenshot frames into README images |

Custom widgets: `fit-check`, `print-result`, `guess`, `printer-state`. The
live server may refuse them as `draw` widget ops; the board skill says how
to render them meanwhile. Built-in widgets (`status-card`, `skill-card`,
`progress-bar`, `bar-chart`) always work.

## Screenshots for the docs

Run `export-readme-shots`, or `screenshot` a frame yourself, and save it
under `docs/img/` with a plain name (`board-measurements.png`). Animations
are animated WebP, not GIF. Link the image from the doc that needs it.

## When the board is down or read-only

Say so in your report and list the frames that are now stale. Do not block
the repo change on the board.
