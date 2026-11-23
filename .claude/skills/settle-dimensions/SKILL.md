---
name: settle-dimensions
description: Settle the open dimensions of waveshare-round-stand with the owner, one decision at a time - the ph() hardware guesses on the 1.28 badge (switch position and height, JST connector) and the printer clearances. Says how to measure each with calipers, where the number goes in code, how to rebuild and check, how to log it and mark it on the draw board. Use when someone says "let's nail down the dimensions", "what still needs measuring", has calipers and the badge in hand, or a build prints a PLACEHOLDER list.
---

# Settle the dimensions

The record of what is measured is `docs/MEASUREMENTS.md` (value, who, how,
date, the constant that uses it) and the board's **Measurements** frame. The
guesses are the `ph(value, what)` fields of `Badge` in
`pocketwatch/build_pocketwatch.py`, and that script lists them first.

## 1. Get the list

```
./tools/py pocketwatch/build_pocketwatch.py --no-render | head -12
```
It prints `PLACEHOLDERS still in use` and one line per guess. Undo the files
it rewrote if you only wanted the list: `git checkout -- stl pocketwatch`.
Then read the *Where the unknowns are* tables in `AGENTS.md`. Ask the owner
which matters most to him **now**. Default order, by how much a wrong guess
costs: switch position, switch height, then the JST (only the battery cases
use it), then printer clearances (`calibrate-my-printer` covers those).

## 2. One decision per message

Ask for one measurement, say how to take it, say what it changes. Wait. Do
not send the whole table. If a design can make the number not matter (a
bigger post, a slot instead of a hole), offer that instead of the
measurement.

## 3. How to measure each (badge frame)

Origin: centre of the round disc, on the glass face. **+y toward the USB-C
tab** (12 o'clock). **+x to the right seen from the back.** +z from the glass
into the case. All in mm. Lay the badge **face down** and work from the back.

| field | what | how |
|---|---|---|
| `sw_x`, `sw_y` | BOOT actuator centre (BOOT is at -x, RESET at +x, mirrored) | calipers from the disc edge to the actuator centre, along x and along y; centre = edge distance minus 17.65 (half of `disc_d` 35.31). Or a photo square-on with a ruler in frame. Cross-check: `reference/esp32-s3-lcd-1.28-switch-positions.png` puts them at r ≈ 12.5 from Waveshare's drawing. |
| `sw_body_h` | switch housing top, above the PCB back | caliper depth rod from the housing top down to the PCB |
| `sw_cap_h` | actuator top, above the PCB back | the same, to the actuator top. Today the post stops `REST_CLR` 0.20 short of it; 0.3 of error decides whether it clicks. |
| `sw_body`, `sw_cap_d` | housing square, actuator diameter | calipers across |
| `jst_x`, `jst_y`, `jst_w`, `jst_d` | battery JST: centre and footprint | edge distances as for the switch; width along x, depth along y, including the latch |
| `Key.F_SW` | switch actuation force | press with a kitchen scale under the badge; or keep the 2.0 N guess |

A photo of the back with calipers in frame is evidence; ask for one and save
it under `reference/pictures/` with a line in `reference/SOURCES.md`.

## 4. Put it in the code

Replace the guess with a plain number and a comment that says who measured
it and when:
```
sw_x: float = 11.4               # owner's calipers, 2026-11-30
```
(was `sw_x: float = ph(11.1, "...")`). Then `./build_all.sh --no-render`:
every check must pass. A new `[FAIL]` means a design assumed the guess;
that is a finding to show the owner. Look at the section renders of the
USB-only case (`pocketwatch/renders/usb-section-post.png`).

## 5. Log and show it

- `docs/MEASUREMENTS.md`: the value, who, how, date, file and constant.
  Move it from *guess* to *measured*.
- Draw board: the board skill `answer-a-guess` replaces a guess card with
  the measurement (see `update-the-board`). Without edit access, tell the
  owner which guess to retire.
- Commit on a branch, PR titled with the dimension.
