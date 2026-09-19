# waveshare-round-stand — working notes for agents

Read this first. It is the project-specific layer; Aaron's general rules live in
his vault (`kb/procedures/working-with-aaron-read-first.md`) and still apply.

## What this is

Printable mounts for Waveshare's round ESP32-S3 display boards, for Aaron's
desk. Three families, all live:

| family | where | built by | python |
|---|---|---|---|
| desk stands + docks (5 STLs) | `stl/` | `build_stands.py` | system `python3` |
| 1.28 stand with a button post (2 STLs) | `stl/` | `build_stand_button.py` | `~/.venvs/cad/bin/python` |
| gauge pod + clip + trim rings | `pod/` | `pod/build_pod.py` | `~/.venvs/cad/bin/python` |

The **pod is the goal** — an instrument cluster clipped to the side of his
monitor with the look of a 2G DSM A-pillar gauge pod. The stands were how he
found out what he wanted. Keep them; don't grow them.

`./build_all.sh` rebuilds everything, validates every mesh, re-renders, and
link-checks the docs. Run it before any commit that touches geometry.

## Hardware facts (verified — do not re-derive)

Full tables in `BOARDS.md`. The ones that change designs:

- **1.28** (SKU 26541, non-touch): round PCB **Ø36.5**, 1.6 PCB but **~4.7 thick at the rim**
  with the display module (fit gauge, 09-18) — the groove is 5.0. USB-C on the
  flat top chord. BOOT lower-left / RESET lower-right *seen from the back*, at
  r ≈ 12.5 mm — positions measured, overlay in `reference/`.
- **1.46 Touch** ships in two parts: **cover glass Ø44.77 / 12.30 thick** or
  **bare, PCB Ø42.58 / 10.65 thick**. Aaron's is **cover glass** and **has
  header pins fitted**, protruding from the back. Its USB-C is on the bottom
  edge and fires **downward**.
- Aaron has **right-angle USB-C cables** (bought 2026-09-18). Pod default is
  `gap12` because of that.
- Printer: **Elegoo Centauri Carbon 2, 0.6 nozzle**, at `10.0.4.1` (reach it via
  the `soul` MCP `centauri__*` tools; it is often powered off). Slicer:
  **ElegooSlicer** on Windows, `D:\tools\ElegooSlicer\elegoo-slicer.exe`.
  Presets that match his last good print: printer `Elegoo Centauri Carbon 2
  0.6 nozzle`, process `0.30mm Standard @Elegoo CC2 0.6 nozzle - Copy`,
  filament `PRUSA Strontium` = **PETG 260/85**, not PLA.
- **He slices in the GUI.** The CLI does not work headlessly — see
  `docs/TOOLCHAIN.md` before spending time on it again.

## Conventions

- **STLs: `stl/small/` = 1.28, `stl/large/` = 1.46, `stl/pod/` = the pod.**
  Plain-English file names he can read at a glance (`Stand - BOOT button.stl`),
  no board codes. Every `large/` file says **cover glass** or **no cover glass** —
  the two 1.46s are not interchangeable; the name is the guard. New size →
  new folder, and add it to `SIZE` in `pod/build_pod.py`.
- **Never delete generated assets.** Move them to `archive/` and add a line to
  `archive/NOTE.md`.
- **Windows mirror:** `D:\Projects\waveshare-round-stand` (`/mnt/d/...`). Copy
  the tree there after every push — he slices from it. **`stand.3mf` in that
  folder is his**, saved from ElegooSlicer. Never overwrite or move it. Before
  any bulk copy, list what's there that the repo doesn't have.
- Commit as Aaron (`Aaron Herres <iam@hypnodroid.com>`), end the message with
  whatever `Co-Authored-By` line the session specifies, **push after every
  meaningful commit**.
- Docs are for him on a phone: tables, bold keys, answer first.

## How to work here

1. **Render before you report.** Every geometry change → `build_all.sh` →
   *look at the PNGs as a skeptic* before writing a word. Three of the
   project's real design errors were invisible in numbers and obvious in a
   render (a box with holes; gauges hidden by draw order; nothing retaining the
   gauges).
2. **Assert what must be physically true**, not just watertightness: overlap
   between a post and its body, clearance under a rim, a plug fitting in a gap.
   `build_stands.py` and `build_stand_button.py` show the pattern.
3. **Ask for a photo of the real hardware** before finalising anything that has
   to fit it. The drawing shows the part as sold, not as he owns it (the header
   pins were a photo discovery).
4. **A documented limitation is a spec, not a deliverable.** "A straight plug
   won't fit" became the dock the same day.
5. **One decision per message**, and prefer a design that removes the question
   (an adjustable clip beat asking for a monitor measurement).
6. New board? Follow `.claude/skills/add-board/SKILL.md`. New print result?
   Log it in `docs/PRINT-LOG.md` first, then change numbers.

## Where things are

- `docs/DESIGN.md` — every design decision and what it replaced
- `docs/TOOLCHAIN.md` — the two pipelines, venv setup, renderer limits, slicer CLI post-mortem
- `docs/PRINT-LOG.md` — what has actually been printed and how it went
- `PRINTING.md` — user-facing print guide (presets, orientation, seating, fit)
- `BOARDS.md` — dimensions, pin maps, how the two 1.46s differ
- `reference/` — Waveshare's drawings, saved locally, with sources
- `.claude/skills/` — repeatable procedures; invoke them rather than re-deriving
