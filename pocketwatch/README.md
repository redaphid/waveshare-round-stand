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

Rebuild: `~/.venvs/cad/bin/python pocketwatch/build_pocketwatch.py` from the repo root. Add `--no-render` for a fast check run.
