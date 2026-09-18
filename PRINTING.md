# Printing these

## Pick the right file

| board | file |
|---|---|
| ESP32-S3-LCD-1.28 (SKU 26541) | `esp32-s3-lcd-128-stand.stl` |
| ESP32-S3-Touch-LCD-1.46, **with** cover glass | `esp32-s3-touch-lcd-146-stand-coverglass.stl` |
| ESP32-S3-Touch-LCD-1.46, **no** cover glass | `esp32-s3-touch-lcd-146-stand-bare.stl` |

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

All three fit on the plate together with room to spare.

## The cable notch — what it does and doesn't do

Every stand has a notch cut straight through the middle of the ridge, front to
back, so a USB-C lead can run through the stand instead of draping over it. It
also sheds roughly a third of the material.

| stand | notch width | clear space under the board rim |
|---|---|---|
| 1.28 | 13 mm | **4.10 mm** |
| 1.46 cover glass | 14 mm | **5.36 mm** |
| 1.46 bare | 14 mm | **5.30 mm** |

**It is a cable route, not a plug socket.** That clearance takes a bare lead or a
right-angle USB-C plug. It will *not* take a straight plug pushed in at
bottom-dead-centre, and no notch can: the connector fires radially outward, so
at the bottom of a board leaning 20° a straight plug needs about 20 mm of run
before it clears — and the desk is in the way. Making that work would mean a
stand roughly twice as tall, which defeats the point.

So, three ways to power these:

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

## If the fit is wrong

`fit` — the slop added to the board's thickness — is 0.8 mm on all three, and is
the only number likely to need touching. A 0.6 mm nozzle tends to come out
slightly undersized, which is why it starts generous.

Edit the relevant entry in `build_stands.py` (`gap = <thickness> + <fit>`), then:

```
python3 build_stands.py
python3 check_stl.py esp32-s3-touch-lcd-146-stand-coverglass.stl
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
