# Printing these

## Pick the right file

First: **how will you power it?** That decides stand vs. dock.

| powering the 1.46 by… | print |
|---|---|
| straight USB-C cable in the bottom port | the **DOCK** |
| right-angle USB-C cable, battery, or port turned to the side | the low **stand** |

| board | low stand | dock |
|---|---|---|
| ESP32-S3-LCD-1.28 (SKU 26541) | [`…1.28_board-36.5mm_stand.stl`](stl/esp32-s3-lcd-1.28_board-36.5mm_stand.stl) | — (port is on the top chord) |
| ESP32-S3-Touch-LCD-1.46, **with** cover glass | [`…coverglass_board-44.77mm_stand.stl`](stl/esp32-s3-touch-lcd-1.46-coverglass_board-44.77mm_stand.stl) | [`…coverglass_board-44.77mm_DOCK-straight-plug.stl`](stl/esp32-s3-touch-lcd-1.46-coverglass_board-44.77mm_DOCK-straight-plug.stl) |
| ESP32-S3-Touch-LCD-1.46, **no** cover glass | [`…bare_board-42.58mm_stand.stl`](stl/esp32-s3-touch-lcd-1.46-bare_board-42.58mm_stand.stl) | [`…bare_board-42.58mm_DOCK-straight-plug.stl`](stl/esp32-s3-touch-lcd-1.46-bare_board-42.58mm_DOCK-straight-plug.stl) |

If you're unsure which 1.46 you have, see the "telling them apart" note in
[`BOARDS.md`](BOARDS.md). Printing the wrong one gives you a groove 1.65 mm out
— the glass version won't fit the bare stand at all.

## Slicer settings

Slice in the ElegooSlicer GUI with the same trio as the last successful print on
the machine (`ECC2_0.6_strontium-small-bear-2-WORKING-5x_PRUSA Strontium_0.3`):

| | preset |
|---|---|
| printer | `Elegoo Centauri Carbon 2 0.6 nozzle` |
| process | `0.30mm Standard @Elegoo CC2 0.6 nozzle - Copy` |
| filament | `PRUSA Strontium` |

`PRUSA Strontium` inherits `Elegoo PETG PRO @ECC2` — **PETG, 260 °C nozzle,
85 °C bed**, despite the name. Masses quoted below assume PETG at 1.27 g/cm³.

Nothing exotic is needed: 2 walls and 15 % infill (the process default) is
plenty. No supports. No brim needed — the base is flat and wide.

## Orientation on the plate

Print **flat on the base**, exactly as the STL is oriented (base on Z = 0).
Every face is either a vertical wall or an upward slope; there are no overhangs
anywhere, and the groove is a top-down cut. Do not stand them on end.

| stand | footprint | height | material |
|---|---|---|---|
| 1.28 | 26 × 27 mm | 12 mm | 3.6 cm³ ≈ **4.6 g** |
| 1.46 cover glass | 30 × 36 mm | 16 mm | 7.0 cm³ ≈ **8.9 g** |
| 1.46 bare | 29 × 35 mm | 16 mm | 6.5 cm³ ≈ **8.2 g** |
| 1.46 cover glass **dock** | 30 × 38 mm | 38 mm | 15.6 cm³ ≈ **19.8 g** |
| 1.46 bare **dock** | 29 × 37 mm | 38 mm | 14.1 cm³ ≈ **17.9 g** |

All five fit on the plate together with room to spare.

## The cable notch — what it does and doesn't do

Every stand has a notch cut straight through the middle of the ridge, front to
back, so a USB-C lead can run through the stand instead of draping over it. It
also sheds roughly a third of the material.

**On the low stands** the clearance under the rim is:

| stand | notch width | clear space under the board rim |
|---|---|---|
| 1.28 | 13 mm | **4.10 mm** |
| 1.46 cover glass | 14 mm | **5.36 mm** |
| 1.46 bare | 14 mm | **5.30 mm** |

**On the low stands that is a cable route, not a plug socket.** It takes a bare
lead or a right-angle USB-C plug. It will *not* take a straight plug pushed in
at bottom-dead-centre: the connector fires radially outward, so a straight plug
needs ~20–25 mm of run below the rim before the cable can turn — and there's
5 mm. That's exactly the failure you see when the board ends up lying across
the stand with a cable in it.

**The docks fix this by lifting the board.** Ridge 38 mm instead of 16, notch
widened to 16 mm for plug bodies, leaving **27 mm** under the rim — a 24 mm plug
body plus 3 mm for the cable to start its turn. The plug hangs down through
the notch — leaning forward as it goes, since the board leans back — and its
tip lands about 6 mm in from the front edge. The notch is open both ends: run
the cable out the front, or 32 mm back along the floor to exit behind. Cost:
roughly twice the material, and the screen sits ~72 mm off the desk instead
of ~50.

So, four ways to power these:

0. **Straight USB-C lead in the bottom port → print the dock.** Nothing to
   rotate, nothing to buy.

1. **Right-angle USB-C lead**, connector at the bottom, head sitting in the
   notch and the cable running out the back. Tidiest option.
2. **Rotate the board** so the connector sits clear of the groove entirely. The
   groove wraps about ±50° either side of bottom-dead-centre, so anything past
   roughly 4 or 8 o'clock is in free air and takes a straight plug. Then drop
   the slack into the notch. The display rotates in software (LVGL).
3. **Battery.** Both boards have a battery connector — the 1.28 an MX1.25 2-pin,
   the 1.46 a BAT pin on the header — so neither has to be tethered at all.

Board-specific notes:

- **1.28** — USB-C sits on the flat chord. Chord at the top is its natural
  orientation and needs no notch at all; chord at the bottom puts the connector
  into the notch, which is what the notch is there for.
- **1.46** — USB-C is on the bottom edge and plugs in downward, so this board is
  the one that actually needs the notch. Seated naturally, use a right-angle
  lead; otherwise rotate per option 2.

Because the board is unsupported across the notch it sinks about 1.2 mm lower
than it otherwise would, which is accounted for in the numbers above and
actually *increases* groove engagement slightly.

## The 1.28 button-post stands

`…1.28…_stand_BOOT-post.stl` and `…_RESET-post.stl` are the plain 1.28 stand
with one addition: a Ø3.2 pad on a Ø4 column, standing 3.6 mm out of the right
(BOOT) or left (RESET) shoulder, exactly behind that switch on the badge's back.

**How it clicks.** The badge leans back in its groove, resting on the groove's
rear lip 5 mm up its rim. The switch is 7.7 mm up — 2.7 mm above that lip — and
the pad sits 0.2 mm off its cap. Press anywhere near the top of the screen and
the badge tries to rotate about the lip; the switch is the softest thing in the
load path, so it is what compresses. Because the switch is so close to the
pivot, a push at the top is levered **~11×** onto it: a light tap does it. The
badge's own weight puts ~30 gf on the pad — well under the ~160 gf a tactile
switch needs — so it doesn't self-press.

**Seat it USB-C chord up.** The badge is round and rotates freely, and the post
only works in one orientation: chord at the top puts BOOT at the lower right and
RESET at the lower left, as you look at the screen.

Which switch: **BOOT is GPIO0**, the one firmware reads as a user button. RESET
reboots the board — useful, but not for tapping.

Switch positions were measured off Waveshare's outline drawing —
`reference/esp32-s3-lcd-1.28-switch-positions.png` shows the fit. The Ø3.2 pad
is there to forgive ±1 mm of that measurement. If the first print misses, the
two numbers are `SWITCH` and `REST_CLR` in `build_stand_button.py`
(`~/.venvs/cad/bin/python build_stand_button.py BOOT`).

## If your board has header pins fitted

Waveshare's drawing shows a bare board, but these commonly ship with (or get
fitted with) a 2×10 header whose pins protrude several mm out of the **back**.
Those pins stick out perpendicular to the board, straight at the stand.

Where the header sits when you seat the board decides whether it fits. Measured
against the cover-glass stand, clearance by header position — angle measured
from bottom-dead-centre, where the USB-C sits:

| header at | 5 mm pins | 8 mm pins | 11 mm pins |
|---|---|---|---|
| 0° (bottom, over the notch) | 7.8 mm | 6.8 mm | 5.8 mm |
| 20° | **clash** | **clash** | 0.5 mm |
| 40° | **clash** | **clash** | 0.2 mm |
| 50° | **clash** | 0.2 mm | 2.2 mm |
| 60° | 1.0 mm | 3.0 mm | 4.8 mm |
| 75° | 5.5 mm | 7.5 mm | 9.5 mm |
| 90° (side) | 11.5 mm | 13.5 mm | 19.7 mm |
| 180° (top) | 29.2 mm | 30.0 mm | 29.0 mm |

**Keep the header out of the 20°–50° band either side of bottom.** That arc is
where the groove and its shoulders are, and pins there have nowhere to go.
Bottom-dead-centre is fine because the notch removes the ridge; past about 60°
the board has risen clear of the stand entirely.

In the board's natural orientation — USB-C at the bottom — the header lands
around 75–90°, which clears comfortably. The trap is a *partial* rotation: turn
the board 30° or so to angle the USB-C and you walk the header straight into
the shoulder.

**The docks are far more forgiving here.** Their rear ramp drops 32 mm over
~10 mm of depth, so it falls away from the pins fast; measured against the
cover-glass dock, nothing clashes at any angle — worst case is 0.8 mm at 40°
with 5 mm pins, and 8 mm pins clear by 8 mm+ everywhere.

## If the fit is wrong

`fit` — the slop added to the board's thickness — is 0.8 mm on all three, and is
the only number likely to need touching. A 0.6 mm nozzle tends to come out
slightly undersized, which is why it starts generous.

Edit the relevant entry in `build_stands.py` (`gap = <thickness> + <fit>`), then:

```
python3 build_stands.py
python3 check_stl.py stl/esp32-s3-touch-lcd-1.46-coverglass_board-44.77mm_stand.stl
```

- rattles → drop to 0.5
- won't seat, or the ridge creaks → go to 1.0

`check_stl.py` exits non-zero if the mesh came out unwatertight, so it is worth
running before every slice.

## Automating the slice — unfinished

Driving `elegoo-slicer.exe` headless from WSL was attempted and abandoned. Two
obstacles were solved and are captured in `flatten_presets.py`:

1. ElegooSlicer's user presets omit the `type` field the CLI demands, and it
   also rejects a preset with no `from` field.
2. The CLI does not resolve a preset's `inherits` chain when the preset is
   handed to it as a standalone file, so parent-only settings (`layer_gcode`,
   `use_relative_e_distances`, …) silently vanish and slicing dies on a
   validation error. `flatten_presets.py` walks and merges the chain, scoped to
   the Elegoo vendor — a global index is wrong, because names like
   `fdm_machine_common` are reused across vendors and resolve to another
   printer's preset.

A third failure was not solved: with fully flattened presets the CLI exits 239
and prints no diagnostic at all, even at `--debug 5`. Slicing in the GUI is the
supported path for now.
