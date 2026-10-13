# Pocketwatch case (1.28 badge)

**Ø52.3 × 23.4 mm. Three parts. Sized for the Makerfocus 1000 mAh LiPo (7.4 × 22.28 × 42.65).**

| print | file | orientation | supports |
|---|---|---|---|
| **case** | `stl/pocketwatch/Pocketwatch - case.stl` | bezel face down, as exported | none |
| **plate** | `stl/pocketwatch/Pocketwatch - plate.stl` | flat back down, guides and post up, as exported | none |
| **lid** | `stl/pocketwatch/Pocketwatch - lid.stl` | flat, as exported | none |

## Assembly, in order

1. **Badge** into the case from the back, screen first, USB-C tab into the slot at 12 o'clock.
2. **Battery plug** through the square hole in the plate, then into the badge's JST.
3. **Plate** onto the step behind the badge, header sockets into the two guides. Press until it snaps.
4. **Battery** into the chamber, wire end toward 12 o'clock, wire laid in the channel on the plate.
5. **Lid** pressed in until it snaps.
6. Any straight USB-C cable into the recess at 12 o'clock. The cable is the chain.

**Press the screen to click BOOT.** The badge floats 0.7 mm. At rest the glass sits on the bezel lip. A press slides it 0.2 mm onto a post on the plate, then 0.25 more clicks BOOT. Every other part still has 0.25 mm of room at that point.

## Still guesses (the build prints these on every run)

| what | value | risk if wrong |
|---|---|---|
| switch position | (±11.1, −10.2) | post misses BOOT. The Ø3 post forgives ~±0.6 |
| switch height | housing 1.4, actuator 2.0 | no click, or a held-down button |
| JST position / size | (−7.6, 8.5), 8.4 × 4.0 | plate rubs the JST |

Measured and trusted: Ø35.31 envelope, 38.64 tip to far edge, tab 16.25 / 15.38, PCB back 4.53, header tops 8.15, JST top 7.64, port centre 5.0, headers 13.25 × 3.0 at a 30.0 outside span.

Headers' y position is not measured, and the design doesn't need it. The guides grip in x only and are open in y. The round board in the bore plus the tab in its slot locate y and rotation.

## Bore fit gauge (print this before the case)

v2's badge stopped on the plate step instead of reaching the bezel lip. `stl/pocketwatch/Pocketwatch - bore fit gauge.stl` is the front of the case only, as four rings. Print it bezel down, about 10 minutes.

| ring | dots | bore | `RAD_CLR` |
|---|---|---|---|
| 1 | 1 | Ø35.8 | 0.25 (v2) |
| 2 | 2 | Ø36.4 | 0.55 |
| 3 | 3 | Ø37.0 | 0.85 |
| 4 | 4 | Ø37.6 | 1.15 |

**Result (10-13): ring 4 fits; `RAD_CLR` is now 1.15.** Drop the badge in from the back, screen first, tab in the slot. **The tightest ring where the glass sits flat on the lip** is the `RAD_CLR` to use. Rebuild: `~/.venvs/cad/bin/python pocketwatch/build_bore_gauge.py`.

Rebuild: `~/.venvs/cad/bin/python pocketwatch/build_pocketwatch.py` from the repo root. Add `--no-render` for a fast check run.

## USB-only variant (no battery)

**Ø43.6 × 12.5 mm, two parts, powered only through the USB-C cable.** Same badge, bore, header grips and BOOT post as the battery case; no chamber, no lid.

| print | file | orientation | supports |
|---|---|---|---|
| **case** | `stl/pocketwatch/Pocketwatch USB-only - case.stl` | bezel face down, as exported | none |
| **plate** | `stl/pocketwatch/Pocketwatch USB-only - plate.stl` | flat back down, guides and post up, as exported | none |

Assembly: badge in from the back, screen first, tab in the 12 o'clock opening; plate snaps in flush with the back. The USB-C opening is the tab pocket cut right through the back face, so there is no roof to bridge and the cable leaves straight out. Shares `Badge` and `Case` with the battery build, so `RAD_CLR` 1.15 applies here too.

Rebuild: `~/.venvs/cad/bin/python pocketwatch/build_pocketwatch_usb.py` from the repo root. Add `--no-render` for a fast check run. Not yet printed.
