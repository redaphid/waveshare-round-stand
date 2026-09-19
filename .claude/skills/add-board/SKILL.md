---
name: add-board
description: Add a new Waveshare (or similar) round display board to waveshare-round-stand — find and archive its outline drawing, extract verified dimensions, add it to the stand generator and/or the pod, build, render, document. Use when Aaron mentions a board that isn't in BOARDS.md.
---

# Add a board

## 1. Get the drawing, not the spec sheet

Waveshare states outline dimensions **only inside an image**. Page text will
say "see dimensions image"; WebFetch will report "not stated". Do this instead:

```
curl -sL "https://www.waveshare.com/wiki/<BOARD>" -o /tmp/w.html
grep -oE '/w/upload/[^"'"'"' ]*\.(jpg|png)' /tmp/w.html | grep -viE 'thumb|logo|demo|thonny|arduino' | sort -u
```
Pull candidates named `…-00N.jpg` or `…-introduction-0N.jpg`; **view them**.
The dimensioned outline is the one with `Unit:mm`. Also grab the pinout image.
If the wiki URL 404s, search — variants share one wiki page (the 1.46 lives at
`…-1.46B`).

Save as `reference/<board>-outline.jpg` (+ `-pinout.jpg`), add rows to
`reference/SOURCES.md` with the exact upload URL.

## 2. Extract, then cross-check

Read off: outside Ø (or W×H), **thickness of the whole stack**, active display
Ø, PCB Ø if the front element overhangs it, every connector's position and the
**direction it fires** (radial? which edge?), mounting holes, buttons.

Cross-checks that caught errors here:
- screen Ø ratio between two boards should equal the ratio of their inch names
  (36.96/32.4 = 1.46/1.28 = 1.141)
- "thickness" — is it the bare PCB rim or the assembled stack? Say which.
- does the board ship in **variants** (cover glass / bare)? Waveshare often puts
  both on one wiki page with two drawings. Build for both if you can't tell.

For features the drawing doesn't dimension (switches), use the
`measure-drawing` skill.

## 3. Ask for a photo of his actual board

Before finalising anything that must fit: header pins fitted? standoffs?
cover glass? The drawing shows the part as sold.

## 4. Add it

- **Stand:** new entry in `BOARDS` in `build_stands.py` — `board_d`, `thick`
  (what the groove grips), `screen_d`, and base numbers scaled from the nearest
  existing entry. `stl` name carries the board and its Ø:
  `stl/<board>_board-<Ø>mm_stand.stl`. The asserts will tell you if the base is
  too shallow or the CoM is off.
- **Pod:** new dict in `GAUGES` in `pod/build_pod.py` — `d`, `seat_t` (what
  rests on the shoulder), `bore_r` (what the back of the board needs to pass
  through — check standoffs/buttons), `screen`, `stack`. A trim ring is
  generated automatically.
- Add a row to `BOARDS.md` (dimensions + pin map) and to the tables in
  `stl/README.md`, `PRINTING.md`, `README.md`.

## 5. Ship

`rebuild-and-ship` skill. Look at the previews with the new board drawn in.
