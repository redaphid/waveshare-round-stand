# AGENTS.md

Read this first. It is enough to set up, pick a print, change a model and find
what is still unknown. Every other doc is one level deeper.

## What this is

Printable cases and stands for **Waveshare's round ESP32-S3 display boards**,
mainly the **1.28" badge** (ESP32-S3-LCD-1.28, round PCB, USB-C on a tab at
12 o'clock). Every model is **parametric Python**: a build script holds the
numbers in a dataclass or a few constants, builds the solids with `manifold3d`,
**asserts what must be physically true** (fits, clearances, wall thickness,
the switch is the first thing touched), writes STLs under `stl/` and renders
PNGs. You change a number, rerun the script, read the checks, look at the
renders.

The owner prints on an Elegoo. **You probably do not.** Nothing here needs an
Elegoo; the clearances that depend on a printer are listed below with the
gauge or print that settles each.

## The three answers

| question | answer |
|---|---|
| **What do I print first?** | **1. `stl/fit-gauges/Pocketwatch - bore fit gauge.stl`** (about 10 min, bezel down). It sets the one clearance that decides whether the case fits on *your* printer. **2. The pocketwatch case:** `stl/pocketwatch/Pocketwatch USB-only - plate.stl` (print-proven) and `- case.stl`. Details below. |
| **The case is too tight; the glass will not seat?** | Use the **`tune-fit`** skill. The number is `Case.RAD_CLR` in `pocketwatch/build_pocketwatch.py` (1.15 per side today); step **+0.10 per side**. The **USB-only case** takes up to **about 1.25** (1.30 fails its watertight check). Past that, the plug-engagement geometry must change, not just the clearance. `RAD_CLR` is shared: the **telegraph and hoop have no headroom** and fail from 1.16, so change it on your branch for the case, or add a roomy-bore variant. Check: `./tools/py pocketwatch/build_pocketwatch_usb.py --no-render`, every line `[ok]`, then look at `pocketwatch/renders/usb-section-post.png`. Details in *Where the unknowns are*. |
| **How do I change a model?** | Find its row in `stl/catalog.toml` (it names the script and the class or constants to edit) → edit the number → `./tools/py <script>` → every check must print `[ok]` → look at its renders → `./tools/py build_catalog.py`. Worked example below. |
| **Where are the unknowns?** | Two kinds. **Printer clearances** (bore, plate, tenon, USB-C slot, telegraph pin) and **hardware guesses** (the switch and JST position and height, tagged `ph(...)` in `Badge`; `./tools/py pocketwatch/build_pocketwatch.py --no-render` lists them first). Table below. |

### What to print first, and why

1. **Bore fit gauge** (`stl/fit-gauges/Pocketwatch - bore fit gauge.stl`,
   built by `pocketwatch/build_bore_gauge.py`). Four rings, ring N has N dots,
   clearances `CLRS = [0.25, 0.55, 0.85, 1.15]` per side. Drop the badge in
   from the back, screen first. **The tightest ring where the glass sits flat
   on the lip is your `Case.RAD_CLR`** in `pocketwatch/build_pocketwatch.py`.
   On the owner's printer only ring 4 (1.15) fit, which is today's value. The
   gauge is read with the badge in hand. **No badge?** Print the gauge anyway
   and hand it to the owner with the case; he reads it, and you reprint only
   if his answer is not ring 4. Meanwhile, print the case as is.
2. **Pocketwatch case, USB-only** (featured #1: the simplest design and the one
   most likely to succeed). If your gauge said ring 4, print as is:
   - `stl/pocketwatch/Pocketwatch USB-only - plate.stl`: **proven** (print log
     2026-10-13). Flat back down, guides and post up.
   - `stl/pocketwatch/Pocketwatch USB-only - case.stl`: **needs-work, fix
     applied, unprinted since.** The 2026-10-14 print was too tight to pry the
     plate off and the USB-C opening was too small; the current file has a pry
     notch and a slot 2 mm bigger all round. Bezel down.
   - If your printer runs oversize, use `- plate (roomy).stl` (0.65 per side
     instead of 0.18; unprinted).
   If your gauge said a tighter ring (1 to 3), set `RAD_CLR` to it first (see
   *Change a model*). If even ring 4 is tight, see *the case is too tight*
   above: the gauge stops at 1.15, and the case has little room past it. To
   find out whether 1.25 is enough before printing a case, print a looser
   gauge: set `CLRS = [1.05, 1.15, 1.20, 1.25]` in `build_bore_gauge.py`
   (tried: builds watertight) and read it the same way.
3. **Telegraph key stand** (featured #2): the same case leaning back 40° in a
   hoop, with a brass-look key on the base that clicks BOOT. Status
   **printed** on the owner's word only (2026-11-22); fit details were never
   recorded. Print it after the case works. Parts and order: the `telegraph`
   rows in `stl/catalog.toml`.

The slot fit gauge (`stl/fit-gauges/Slot fit gauge.stl`) sets the groove of the
old wedge desk stands. Those are retired ("didn't protect the device
enough"), so skip it.

## Setup

Needs **Python 3.11+** and bash (Linux, macOS, or Windows in Git Bash or WSL).

```
./setup.sh                   # makes .venv/, installs requirements.txt, smoke-tests the imports
./build_all.sh --no-render   # every model and every check, about 2 min
./build_all.sh               # the same plus every render, about 6 min
```

- `setup.sh` is safe to rerun. It rebuilds `.venv` only if it is missing or
  too old, and reinstalls only when `requirements.txt` changed.
- **Run every script from the repo root** (they import by relative path).
- `./tools/py <script>` runs a script with the right interpreter: `$PYTHON`,
  else `.venv/`, else `~/.venvs/cad` (the owner's), else `python3`.
- No Python 3.11? macOS: `brew install python`. Windows: python.org installer,
  then run `./setup.sh` from Git Bash. Linux: your distro's `python3`, or `uv`.

## Repo map

| path | what |
|---|---|
| `stl/` | **every printable file**, by family. `stl/README.md` is the catalog for humans. |
| `stl/catalog.toml` | **source of truth** for the catalog: one row per STL with status, print log date, script and what to edit. `build_catalog.py` checks it against disk and writes `stl/README.md`. |
| `pocketwatch/build_pocketwatch.py` | **`Badge`** (what the board is, measured or `ph(...)` guessed) and **`Case`** (what we choose). Every pocketwatch design imports both. Also builds the battery case. |
| `pocketwatch/build_pocketwatch_usb.py` | the USB-only case and its back plates; `PLATE_DISC_CLR`, `PLATE_DISC_CLR_ROOMY` |
| `pocketwatch/build_bore_gauge.py` | the bore fit gauge; `CLRS` |
| `pocketwatch/stands/hoop/build_hoop.py` | the hoop stand; `Stand` (tilt, ring, tenon `FIT`) |
| `pocketwatch/stands/hoop/build_hoop_telegraph.py` | the telegraph key; `Key` (lever, pin, knob, lean) |
| `pocketwatch/stands/*`, `pendant/*`, `clips/*`, `styles/*` | other pocketwatch designs, one script each; most are concepts (never printed) |
| `pod/` | monitor gauge pod (concept) and the shared renderer `pod/render.py` |
| `build_stands.py`, `build_stand_*.py` | the retired wedge desk stands and docks; still built and checked |
| `build_fit_gauge.py` | the slot fit gauge |
| `check_stl.py`, `preview.py` | stdlib STL validator; desk-stand previews |
| `docs/PRINT-LOG.md` | what has actually been printed, newest first. **The only evidence for a status.** |
| `docs/DESIGN.md` | every design decision and what it replaced (dated; never edit old entries) |
| `docs/TOOLCHAIN.md` | renderer limits, the slicer CLI post-mortem |
| `docs/MEASUREMENTS.md` | every measured dimension: value, who, how, date, the constant that uses it |
| `docs/models/` | one page per model family (`pocketwatch-case.md`, `telegraph-key.md`, ...) |
| `docs/FOR-PRINTERS.md` | the contributor guide in prose: calibrate, what to print, settle dimensions |
| `docs/STATUS.md`, `docs/PRINTER-TROUBLE.md`, `docs/BOARD.md`, `docs/ELEGOO.md` | state of things; the owner's printer problems; the draw board; Elegoo-only notes |
| `BOARDS.md` | board dimensions and pin maps; the two 1.46 variants |
| `reference/` | Waveshare drawings and photos of the owner's hardware, with sources |
| `archive/NOTE.md` | what was deleted and the last commit that has it (`1580ce5`) |
| `tools/py` | the Python resolver above |
| `tools/elegoo/` | owner-only Elegoo slicer helpers; see `docs/ELEGOO.md` |
| `.claude/skills/` | step-by-step procedures; index below |

## The catalog

`stl/catalog.toml` lists every STL in five sections, in this order: **fit
gauges**, **featured** (the pocketwatch case, then the telegraph key),
**other current designs**, **concepts** (never printed), **earlier designs**
(retired: the wedge desk stands and docks, print-proven but they "didn't
protect the device enough"). Each part has a status:

| status | means |
|---|---|
| **proven** | printed and worked; a `docs/PRINT-LOG.md` entry says so |
| **printed** | came off a printer; result partial or unrecorded |
| **needs-work** | printed with a problem. `fixed = true` means the current file has the fix but nobody has printed it. |
| **failed** | printed and did not work |
| **unprinted** | never printed. A design that passes every check can still fail on a real printer. |

Pick by board (`1.28`, `1.46 cover glass`, `1.46 bare`) and status. Each
family row names its README and renders. Never call a part proven without a
print-log entry or the owner's own words.

## Change a model

1. Find the family in `stl/catalog.toml`. Its `script` is the file to run;
   its `edit` names the class or constants to change.
2. Edit one number. Most designs read `Badge` and `Case` from
   `pocketwatch/build_pocketwatch.py`, so a change there moves every
   pocketwatch design: rebuild them all with `./build_all.sh --no-render`.
3. Rebuild that family only: `./tools/py <script> --no-render` for the checks,
   then `./tools/py <script>` for the renders. A failed check prints `[FAIL]`
   and the script exits non-zero. **A failure is a finding: fix the geometry,
   never the check.**
4. **Look at the renders** (paths in the catalog row) before you say anything.
   Compare with `git diff --stat` and the previous PNG (`git show HEAD:<png>`).
5. `./tools/py build_catalog.py` (the README stays in step; `--check` fails if it
   is stale). New or renamed STL? Add or edit its row in `stl/catalog.toml`
   first.
6. If the change answers a print, the `docs/PRINT-LOG.md` entry comes first.
   If it is a design decision, add a dated entry to `docs/DESIGN.md`.

### Worked example: make the telegraph lever 2 mm longer

- **Where:** `pocketwatch/stands/hoop/build_hoop_telegraph.py`, class `Key`
  and the function `lever_geometry()`.
- **There is no length constant.** The script solves the lever. It puts the
  knob as far back as the hoop allows (`K_Y` in `lever_geometry()`: a
  fingertip `FINGER_R` + `FINGER_CLR` clear of the hoop, and the knob's foot
  ring `KNOB_RS` + `CLR` clear of it, whichever is further forward). Then it
  puts the pin so the knob arm is `RATIO` (2.0) times the nub arm. The run
  prints the result: `14. Key at rest (40 deg): ... nub arm 12.1, knob arm
  23.1 (ratio 2.00)`.
- **What does not work:** `FINGER_CLR` +2 changes nothing (the foot-ring
  term is the one that binds). `RATIO` 2.2 adds only 0.5 mm and fails the
  travel check (`knob travel to the click 2.4-3.3 mm`: 3.46).
- **What "2 mm longer" means here:** the knob sits 2 mm further forward.
  The pin follows so the ratio stays 2.0, so the lever grows about 2.2 mm
  from nub to knob and the feel of the click does not change.
- **What works:** two edits in that file.
  ```
  # in class Key, under RATIO:
      KNOB_FWD: float = 2.0     # knob this much further forward than the hoop requires
  # in lever_geometry(), the line that starts `K_Y = min(`, add `- k.KNOB_FWD` at its end:
      K_Y = min(front(k.FINGER_R, z_kb + k.KNOB_H + 0.5) - k.FINGER_CLR, front(k.KNOB_RS + k.CLR, z_kb) - 0.3) - k.KNOB_FWD
  ```
- **Check:** `./tools/py pocketwatch/stands/hoop/build_hoop_telegraph.py
  --no-render`. Tried: knob arm 23.1 → 24.6, nub arm 12.1 → 12.8 (pin to
  knob about 2.2 mm longer), ratio still 2.00, click still at 3.17 mm of knob
  travel, every check `[ok]` at 40° and 50°. Then run it without
  `--no-render` and look at `telegraph-section-pressed.png` and
  `telegraph-01-hero.png` in `pocketwatch/stands/hoop/renders/`: the knob is
  further in front of the hoop. Tried: the lever, base, knob and pin STLs
  change (both leans); the hoop-and-case STLs do not. The changed parts are
  no longer the printed ones: in `stl/catalog.toml`, family `telegraph`, set
  `status = "unprinted"` (and drop `log`) on the rows whose `file` ends in
  `- base (40 deg).stl`, `- lever (40 deg).stl`, `- knob.stl` and
  `- pin.stl` (the 50° rows already are). Then `./tools/py build_catalog.py`
  and a dated entry in `docs/DESIGN.md`.

## Where the unknowns are

**Printer clearances.** Each one depends on your printer. Settle each with the
gauge or the print named, then change the constant.

| what | file | constant (today) | settled by |
|---|---|---|---|
| case bore around the badge, per side | `pocketwatch/build_pocketwatch.py` | `Case.RAD_CLR` (1.15) | bore fit gauge (`CLRS` in `build_bore_gauge.py`); owner: only 1.15 fit, 0.85 did not. **Ceiling, measured against every check:** the USB-only case passes to 1.25 (1.30 fails watertight; 1.45 fails `plug shell engages the port >= 3.5` at 3.4). The constant is shared: the telegraph fails at 1.16 (watertight) and 1.17 (plug body hits the hoop), the hoop and wearable from 1.17, and at 1.25 nine scripts fail. |
| back plate in the case, per side | `pocketwatch/build_pocketwatch_usb.py` | `PLATE_DISC_CLR` (0.18), `PLATE_DISC_CLR_ROOMY` (0.65) | print the plate; one owner print came out ~1 mm large, the next fit |
| USB-C slot | `pocketwatch/build_pocketwatch.py` | `Case.RECESS_W` 9.4, `RECESS_T` 3.6, `RECESS_GROW` 2.0 | the case print: does your cable's plug enter? (10.0 x 4.3 was too tight; grown 2 mm all round, unprinted) |
| hoop tenon in the base mortise, per side | `pocketwatch/stands/hoop/build_hoop.py` | `Stand.FIT` (0.08) | hoop or telegraph base print (0.25 and 0.12 printed loose) |
| telegraph pin and knob | `pocketwatch/stands/hoop/build_hoop_telegraph.py` | `Key.PIN_CLR` 0.15, `HOLE_CLR` 0.10, `SOCK_CLR` 0.15 | telegraph print; never measured |
| snap bead of the battery plate | `pocketwatch/build_pocketwatch.py` | `Case.SNAP_INT` 0.30, `SNAP_CLR` 0.15 | battery case print |

**Hardware guesses.** Fields of `Badge` in `pocketwatch/build_pocketwatch.py`
declared with `ph(value, what)`. `./tools/py pocketwatch/build_pocketwatch.py
--no-render` prints them under `PLACEHOLDERS still in use`.
Measure them on a real badge with calipers (the `settle-dimensions` skill
says how) and replace `ph(x, ...)` with the plain number.

| what | fields (today) |
|---|---|
| BOOT/RESET switch position, from the back | `sw_x` ±11.1, `sw_y` -10.2 |
| switch height behind the PCB back | `sw_body_h` 1.4, `sw_cap_h` 2.0 |
| switch size | `sw_body` 3.5 square, `sw_cap_d` 1.8 |
| battery JST connector | `jst_x` -7.6, `jst_y` 8.5, `jst_w` 8.4, `jst_d` 4.0 |
| switch force (telegraph) | `Key.F_SW` 2.0 N |

Everything measured so far (disc 35.31, tab, PCB back 4.53, header tops 8.15,
header span 30.0, batteries) is in `docs/MEASUREMENTS.md` with who measured
it and how, and drawn in the board's **Measurements** frame.

## Conventions

- **STL layout:** `stl/fit-gauges/`, `stl/pocketwatch/**` (mirrors
  `pocketwatch/`), `stl/pod/`, `stl/small/` (1.28 wedge stands),
  `stl/large/` (1.46). A new family gets its own folder and a catalog row.
- **Plain-English file names** a person reads at a glance
  (`Pocketwatch USB-only - plate (roomy).stl`), no board codes.
- **1.46 parts say `cover glass` or `no cover glass`** in the name. The two
  1.46 boards differ by 2 mm; the name is the guard.
- **Superseded STLs leave the tree.** Git history keeps them; add a line to
  `archive/NOTE.md` naming the last commit that has them.
- Scripts write their own STLs; never hand-edit an STL.
- Units are mm; clearances are **per side** unless the name says otherwise.
- Docs are read on a phone: answer first, tables, bold keys.

## How to work here

1. **Render before you report.** Three of this project's real design errors
   were invisible in the numbers and obvious in a render. Look as a skeptic:
   is anything floating, buried, hidden, or below the desk?
2. **Assert physical truths**, not just watertightness: overlap between
   parts, clearance under a rim, a plug fitting a gap, strain in a flexure.
   Follow the `check(ok, label, margin)` pattern in `build_pocketwatch.py`.
3. **Log the print before changing a number.** `docs/PRINT-LOG.md` has the
   template. Then change one number.
4. **Get a photo of the real hardware before finalising a fit.** The drawing
   shows the board as sold, not as owned (the header pins were a photo
   discovery).
5. **One decision per message** to the owner, and prefer a design that
   removes the question.
6. **PLA by default** (E about 2500 MPa): anything that flexes on every
   press stays at or under 1% strain; snap-once at or under 1.5%.

## The draw board

A live, zoomable schematic of the pocketwatch and the telegraph, public
read-only: the guide, proven vs concept art, the measurements, and the open
guesses. Connect it to your Claude:

```
claude mcp add --transport http pocketwatch-board https://draw.hypnodroid.com/view/pocketwatch-schematics/mcp
```

That address is read-only and needs no sign-in. To draw on the board, ask
the owner to add you; editors use `/b/` in place of `/view/`, which needs a
signed-in, allowed account. **The board is documentation, not a source of
truth:** the code and `docs/PRINT-LOG.md` win when they disagree. The
`update-the-board` skill covers its frames, widgets and rules; `docs/BOARD.md`
has screenshots. Claude Code mod for draw: `claude plugin install draw
--marketplace redaphid/draw-mod`.

## Skills

In `.claude/skills/`. Claude Code loads them by description; other agents can
read the `SKILL.md` directly.

| skill | use it when |
|---|---|
| `start-here` | first session on a fresh clone |
| `print-a-part` | choosing what to print and how |
| `calibrate-my-printer` | printing the fit gauges and turning their result into constants |
| `change-a-model` | editing any design's numbers or shape |
| `tune-fit` | one clearance is too tight or loose on a real print |
| `settle-dimensions` | measuring a `ph(...)` guess with the owner |
| `after-a-print` | a part came off the printer: log it, decide the one change |
| `update-the-board` | the draw board must show a change |
| `debug-the-printer` | helping the owner with his printer's problems |
| `add-board` | a new round board |
| `measure-drawing` | a vendor drawing shows a feature but no number |
| `pod-iterate` | the monitor gauge pod (concept) |
| `rebuild-and-ship` | **owner only**: commit as the owner and mirror to his slicing folder |

## Owner vs contributor

| step | contributor | owner |
|---|---|---|
| setup, build, check, render | yes | yes |
| print, calibrate, change models, log prints | yes | yes |
| commit | your own git identity, on a branch; open a PR | commits as himself, pushes |
| board | read; draw if the owner grants edit | read and draw |
| slicer presets, the Windows slicing folder, the printer on his network | no | `CLAUDE.md`, section *Owner's workflow* |
| `rebuild-and-ship`, `tools/elegoo/` | no | yes |
