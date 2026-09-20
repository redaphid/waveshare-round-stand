# Print log

What has actually come off the printer, and what happened. **Add an entry
before changing any number in response to a print.** Newest first.

Template:

```
## YYYY-MM-DD — <part> (<file>)
- material / presets:
- result:
- fit numbers to change (if any):
- photo:
```

---

## 2026-09-20 — 1.28 BOOT button stand, 5.4 mm groove (`small/Stand - BOOT button.stl`)
- material / presets: black filament — not the usual blue; presets not stated
- result: **the badge seats.** Two photos. Side-on: rim fully down in the
  groove, a little slack in front of the glass, badge leaning back. From
  behind: the post stands on the lower-left switch (BOOT, seen from the back);
  the pad looks perhaps ~1 mm inboard of the switch centre, but the shot is
  blurred and the post is nearer the lens than the switch, so not trusted.
  The column printed with a rough, leaning top (a Ø4 column alone at 0.6 mm).
- **then he pressed it: no click.** "the bottom white plastic around the button
  itself is pushed up against the back wall, so the arm can't reach." Third
  photo, side-on in his hand. Measured the switches off his own back-view photo
  rather than guessing again: they are at r **15.5**, only **2.7 mm in from the
  rim** — the drawing said r 12.2. So the housing sits **below** the groove's
  rear lip and cannot enter a 5.4 mm groove at all; the badge was propped proud
  and shoved forward, which is also why the post could not reach.
- also seen: H1/H2 are fitted with tall female sockets. The pod's 1.28 cups
  already relieve for them (`hdr`, ~8.5 off the PCB) — no change.
- fit numbers to change: not a fit number — a design fault. 1.28 gains
  `rear_lip = 3.0` (the groove's rear wall stops short of the ridge so the
  switch housings clear, and the pivot drops so a press has travel),
  `width` 26 → 30 (the switches are at |x| 11.45; the post needs shoulder), and
  `SWITCH` in `build_stand_button.py` is now the measured pair. Details in
  DESIGN.md.
- photo: sent in chat 2026-09-20 (black print on the bamboo desk; side view, and from behind).

## 2026-09-20 — 1.28 button-post stand, 5.0 mm groove (`small/Stand - … button.stl`)
- material / presets: presumed the usual (PETG, ECC2 0.6 / 0.30 mm)
- result: **"just barely too narrow."** The gauge's 5.0 slot took the badge but
  the stand's 5.0 groove does not: the groove leans 20°, so its walls print as
  0.3 mm stair-steps that each reach ~0.1 mm into the slot, which the gauge's
  slots do not have.
- his worry: once the slot is wide enough the badge will sink and the post
  won't reach the button. Height is set by the groove *floor*, not its width —
  but the post was placed from the groove centre with no check that the badge
  can rock far enough to click. Checked, see fit numbers.
- fit numbers to change: 1.28 `gap` 5.0 → **5.4**. Button pad re-placed from the
  groove's front wall (was: from its centre) — press travel at the switch
  0.10 mm at the old 5.0 → **0.8 mm**, now asserted. Details in DESIGN.md.
- photo: none

## 2026-09-18 — fit gauge (`small/Slot fit gauge.stl`)
- material / presets: presumed the usual (PETG, ECC2 0.6 / 0.30 mm)
- result: **printed.** Photo from behind: the 1.28 stands seated in the **5th
  slot from the narrow end = 5.0 mm** (read by counting walls; the dots weren't
  visible). The back of the board is bare — **no case**. The thickness at the
  rim is the round display module on the front of the PCB, which reaches
  almost to the PCB edge. The earlier "case" reading was wrong.
- fit numbers to change: 1.28 `gap` 2.7 → **5.0**, `thick` 1.6 → **4.7**
  (PCB + module, estimated between the 4.5 slot and the 5.0 slot; sets where
  the button post lands).
- photo: sent in chat 2026-09-18 (blue gauge on the bamboo desk, board seen from behind).

## 2026-09-18 — 1.28 button-post stand, second report (photo)
- result: **still too narrow.** Photo: the badge rests *on top of* the groove,
  it does not enter it. *(Read at the time as a case — wrong, see the gauge
  entry above: it is the display module.)* Seen in the photo: black
  glass, white serrated gasket, a dark bezel ring, a dark back plate, and white
  button nubs sticking out of the rim. The rim is several mm thick, not the
  1.6 mm bare PCB the stand was designed for. The 2.4 → 2.7 widening was
  solving the wrong problem.
- fit numbers to change: unknown until measured. Printed
  `stl/small/Slot fit gauge.stl` requested to get the real width.
- also: the case changes where BOOT/RESET are reached from — the post may be
  landing on a button nub rather than behind the switch. Not redesigned yet.
- photo: sent in chat 2026-09-18 (blue print, badge held above it, seen edge-on).

## 2026-09-18 — 1.28 button-post stand (`…1.28_board-36.5mm_stand_*-post.stl`)
- material / presets: not stated
- result: **printed.** The groove the badge lays in is slightly too small.
- fit numbers to change: groove 2.4 → **2.7 mm** (board 1.6 + 1.1 fit, was
  + 0.8). Shared with the plain 1.28 stand, which gets the same change.
- photo: none

## 2026-09-18 — 1.46 cover-glass low stand (`…coverglass_board-44.77mm_stand.stl`)
- material / presets: PETG (`PRUSA Strontium`), ECC2 0.6 / 0.30 mm, textured plate
- result: **printed and photographed.** Board seats in the groove and stands
  cleanly with no cable. With his straight USB-C cable plugged into the bottom
  port the board cannot seat — it ends up lying across the stand (5 mm under
  the rim vs a ~24 mm plug body). This was the documented limitation; he wanted
  it fixed, not documented → **docks** added the same day.
- fit numbers: none reported for the groove itself — it fit.
- photo: sent in chat 2026-09-18 (light-blue print on a bamboo desk, next to a
  keyboard; second photo with the cable in and the display showing CYBER-PUCK).

## Not yet printed
- 1.28 low stand, 1.46 bare stand, both docks, the other button-post stand
- pod, trim rings, clips — **print the rings and clips first** (10 min) to
  check the press fit and tongue clearance before committing ~40 g to the pod
