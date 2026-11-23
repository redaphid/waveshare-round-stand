---
name: add-board
description: Add a new Waveshare (or similar) round display board to waveshare-round-stand - find and save its outline drawing, extract verified dimensions, add it to the generators, build, render, document. Use when someone mentions a board that is not in BOARDS.md.
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
If the wiki URL 404s, search: variants share one wiki page (the 1.46 lives at
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
- "thickness": is it the bare PCB rim or the assembled stack? Say which.
- does the board ship in **variants** (cover glass / bare)? Waveshare often puts
  both on one wiki page with two drawings. Build for both if you can't tell.

For features the drawing doesn't dimension (switches), use the
`measure-drawing` skill.

## 3. Ask for a photo of the actual board

Before finalising anything that must fit: header pins fitted? standoffs?
cover glass? The drawing shows the part as sold.

## 4. Add it

- **Stand:** new entry in `BOARDS` in `build_stands.py`: `board_d`, `thick`
  (what the groove grips), `screen_d`, and base numbers scaled from the nearest
  existing entry. `stl` goes in the badge's size folder with
  a plain-English name: `stl/<small|large|new>/Stand.stl` (see *Conventions* in
  `AGENTS.md`; variants of one size say which in the name). The asserts will tell you if the base is
  too shallow or the CoM is off. The wedge desk stands are retired. A
  pocketwatch-style case is the current direction, but its scripts build
  `Badge()` with the 1.28's defaults (`pocketwatch/build_pocketwatch.py`):
  a second board means passing its own `Badge(...)` values through, a design
  change to agree with the owner first.
- **Pod:** new dict in `GAUGES` in `pod/build_pod.py`: `d`, `seat_t` (what
  rests on the shoulder), `bore_r` (what the back of the board needs to pass
  through; check standoffs and buttons), `screen`, `stack`. A trim ring is
  generated automatically.
- Add a row to `BOARDS.md` (dimensions + pin map) and a row per new STL in
  `stl/catalog.toml` (with `board` set); `./tools/py build_catalog.py`
  regenerates `stl/README.md`.

## 5. Ship

`./build_all.sh`, look at the previews with the new board drawn in, then a
PR (the owner uses `rebuild-and-ship`).
