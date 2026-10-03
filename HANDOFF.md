# Handoff (2026-10-03, paused for session limits)

**Read this first, then `CLAUDE.md`.** Repo: WSL `survivor` `~/Projects/waveshare-round-stand`, public on GitHub as `redaphid/waveshare-round-stand`. `D:\Projects\waveshare-round-stand` is a non-git mirror Aaron slices from.

## Where things stand

| branch | head | state |
|---|---|---|
| `main` | 02388f7 | stands, docks, pod. **No pocketwatch yet.** |
| `pocketwatch` | this commit | **pocketwatch v2, ready to test-print.** Not merged to main. |
| `coworker-kit` | 051ad54 | **WIP, unreviewed.** Pocketwatch CLI only. Worktree at `~/Projects/waveshare-round-stand-kit`. |
| `pocketwatch-v2` | 373f536 | stale v1. Worktree `~/Projects/waveshare-round-stand-v2`. Safe to remove. |

## Pocketwatch v2 (the thing Aaron is printing)

- `pocketwatch/build_pocketwatch.py` builds three parts: **case**, **plate**, **lid**. Ø52.3 × 23.4 mm, sized for his Makerfocus 1000 mAh LiPo (7.4 × 22.28 × 42.65).
- STLs are in `stl/pocketwatch/`, also copied to the D: mirror. Print order: **plate first** (smallest, tests the riskiest guesses), then case and lid. All three print with no supports, as exported.
- Every check passes: solid-overlap at rest and pressed, BOOT is the only contact when pressed, guide engagement, lip clears the display, snaps interfere, minimum walls, watertight, and **no unsupported overhang beyond a 4 mm bridge**. The overhang check was added after Aaron's slicer caught a floating 14 mm span over the USB-C recess. It's now a 45° arch.
- Design and assembly: `pocketwatch/README.md`.

**Measured** (Aaron's calipers, Miro board `uXjVHk7UnLA=`, photos in `reference/pictures/`): Ø35.31 envelope, 38.64 tab tip to far edge, tab 16.25 / 15.38, PCB back 4.53, header tops 8.15, JST top 7.64, port centre 5.0, headers 13.25 × 3.0 at a **30.0** outside span.

**Still guesses** (printed at the top of every build): switch position (±11.1, −10.2), switch height (housing 1.4, actuator 2.0), JST position and size. If the test print doesn't click, it's one of these.

## Requirements Aaron gave (don't lose these)

- Pocketwatch look. The USB-C plug at 12 o'clock is the crown, and **any straight cable** is the chain. No right-angle-plug sizing needed.
- **The back engages the headers** to seal it in, **and an arm clicks BOOT when the screen is pressed.** So the guides grip in x only, are open in y and free in z. The badge floats 0.7 mm, and the back is fixed to the case, not the board.
- Don't make him measure things a design can avoid. He has little time.

## Next: coworker kit (Aaron's latest ask)

Coworkers with printers and the same 1.28 board should be able to make their own cases (other batteries) and stands. Full spec is the brief that started `coworker-kit`:

1. `requirements.txt` + `setup.sh` (repo-local `.venv`; fall back to `~/.venvs/cad`).
2. Pocketwatch CLI: `--battery TxWxL` or a code like `402030`, `--set NAME=VALUE`, `--name NAME` → `stl/pocketwatch/NAME/`. **Started in 051ad54, unreviewed.** Test across 7.4x22.28x42.65, 401730, 402030, 503035, and a huge one.
3. `build_all.sh` builds the pocketwatch and link-checks the new docs.
4. `START-HERE.md` for coworkers. README pointer. A "your own battery" section in the pocketwatch README. In `CLAUDE.md`, move owner-only facts under an "Owner's workflow" heading.
5. Skills: `make-pocketwatch`, `make-stand`, `tune-fit`. Mark `rebuild-and-ship` and `after-a-print` owner-only.
6. Verify with a fresh clone, then `./setup.sh`, then a custom battery build. Then merge `pocketwatch` (+ kit) to `main`.

**Known inconsistency:** desk stands use Waveshare's drawing Ø36.5, the pocketwatch uses the measured Ø35.31. The stands are print-proven, so leave their geometry and just document it.

## Open loose ends

- No print result yet for pocketwatch v2. Log it in `docs/PRINT-LOG.md` when it comes.
- The USB-C-down dock (`stl/small/Dock for right-angle cable - USB-C down.stl`) missed on print. Its model used drawing numbers that the calipers later corrected. It's superseded by the pocketwatch direction, so it hasn't been fixed.
