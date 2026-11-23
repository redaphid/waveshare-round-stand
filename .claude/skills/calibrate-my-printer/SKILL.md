---
name: calibrate-my-printer
description: Turn a contributor's printer into numbers this repo uses. Print the bore fit gauge (and any other fit test), read the result, set the clearance constant it measures, rebuild the affected models, check, render and log. Use before the first case print on a new printer, or when someone says a case is too tight or too loose everywhere, or asks how to calibrate fit for his printer.
---

# Calibrate my printer

Printers differ by a few tenths of a millimetre in hole and boss size. The
pocketwatch was tuned on the owner's Elegoo (0.6 nozzle, PLA). This skill
moves the printer-dependent clearances to your printer.

## 1. The bore fit gauge (always)

- File: `stl/fit-gauges/Pocketwatch - bore fit gauge.stl` (from
  `pocketwatch/build_bore_gauge.py`). About 10 min. **Bezel down**, no
  supports, the same material and profile you will print the case in.
- Four rings, ring N has N dots. Per-side clearance `CLRS = [0.25, 0.55, 0.85, 1.15]`.
- Read it with the **badge in hand** (ESP32-S3-LCD-1.28). Drop it in from
  the back, screen first. The tightest ring where the glass **sits flat on
  the lip** without forcing is the answer. If he has no badge, the owner reads
  it: ask him to post the ring number.

| result | set `Case.RAD_CLR` in `pocketwatch/build_pocketwatch.py` to |
|---|---|
| ring 4 fits, ring 3 does not | 1.15 (today's value, no change) |
| ring 3 fits | 0.85 (or split the difference with ring 2 if 2 nearly fits) |
| ring 2 or ring 1 fits | that ring's value |
| no ring fits (ring 4 is tight) | print a looser gauge that stays under the ceiling: `CLRS = [1.05, 1.15, 1.20, 1.25]`, `./tools/py pocketwatch/build_bore_gauge.py`, print again. If 1.25 is still tight, clearance alone cannot fix it: the `tune-fit` skill, *Ceiling*. |

**The bore has a ceiling.** Measured against every check in the build:
the USB-only case passes up to `RAD_CLR` 1.25 (1.30 fails its watertight
check; 1.45 fails `plug shell engages the port >= 3.5` at 3.4). `RAD_CLR` is
shared, and the other designs allow less: the telegraph fails at 1.16, and
the hoop and wearable pendant from 1.17. Never offer a gauge ring above 1.25.

## 2. The other printer-dependent numbers

These have no gauge yet. Print the part and read it; the `tune-fit` skill
covers the change.

| part to print | constant | today | owner's history |
|---|---|---|---|
| `stl/pocketwatch/Pocketwatch USB-only - plate.stl` in the case | `PLATE_DISC_CLR` in `pocketwatch/build_pocketwatch_usb.py` | 0.18 | one print ~1 mm large, the next fit; `(roomy)` files use 0.65 |
| USB-C plug into the case slot | `Case.RECESS_GROW` (and `RECESS_W`, `RECESS_T`) | 2.0 | 10.0 x 4.3 was too tight |
| hoop or telegraph tenon into its base | `Stand.FIT` in `pocketwatch/stands/hoop/build_hoop.py` | 0.08 | 0.25 and 0.12 printed loose |
| telegraph pin in the lever and posts | `Key.PIN_CLR`, `Key.HOLE_CLR` | 0.15, 0.10 | never measured |

If he would rather print a gauge than a whole part, a new gauge is a good
contribution: copy `pocketwatch/build_bore_gauge.py`'s pattern (rings with
dot counts, one clearance each), add it to `stl/fit-gauges/` and a row in
`stl/catalog.toml` with `sets = "..."`.

## 3. Apply

1. Log first: an entry in `docs/PRINT-LOG.md` (template at its top) with his
   printer, nozzle, material, the gauge result in his words, and a photo if
   he has one.
2. Change the constant. `RAD_CLR` lives in the shared `Case`, so it moves
   every pocketwatch design: `./build_all.sh --no-render`. Every check must
   pass; a `[FAIL]` means the new clearance broke a wall or a snap, and that
   is worth telling the owner. Above 1.15 expect the telegraph, hoop and
   wearable to fail (see the ceiling above): keep the change on your branch
   for the case alone, or add a roomy-bore variant the way the `roomy`
   plates were added, and say so in the PR.
3. Render the case: `./tools/py pocketwatch/build_pocketwatch_usb.py` and look
   at `pocketwatch/renders/usb-section-post.png`: is the bore gap what you
   set?
4. `./tools/py build_catalog.py`, then commit on a branch with his own
   identity and open a PR that says: printer, gauge result, new value.

**A printer-specific value is not a correction of the owner's.** If his
printer and the owner's disagree, say so in the PR; the owner decides
whether the default changes or a variant (like the `roomy` plates) is added.
