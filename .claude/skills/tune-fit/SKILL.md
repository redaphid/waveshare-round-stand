---
name: tune-fit
description: Fix one fit on a real print of a waveshare-round-stand part - tight or loose bore, plate, tenon, pin, knob or USB-C slot. Maps the symptom to the one clearance constant, changes it by a measured step, rebuilds only the affected family, checks, renders, compares and logs. Use when a printed part is too tight, too loose, will not snap, rattles, or a plug will not go in.
---

# Tune a fit

One symptom, one constant, one step. Log the print **before** changing the
number (`docs/PRINT-LOG.md`, template at its top).

## 1. Symptom to constant

| symptom | constant | file | rebuild |
|---|---|---|---|
| badge will not drop into the case, or rattles | `Case.RAD_CLR` | `pocketwatch/build_pocketwatch.py` | `./build_all.sh --no-render` (shared) |
| plate will not go in, or falls out | `PLATE_DISC_CLR` (`_ROOMY` for the roomy files) | `pocketwatch/build_pocketwatch_usb.py` | that script, then the stands that use the plate: `./build_all.sh --no-render` |
| plate will not snap, or snaps loose (battery case) | `Case.SNAP_INT`, `Case.SNAP_CLR` | `pocketwatch/build_pocketwatch.py` | `./build_all.sh --no-render` |
| USB-C plug will not enter | `Case.RECESS_GROW` (whole slot), `RECESS_W`, `RECESS_T` | `pocketwatch/build_pocketwatch.py` | `./build_all.sh --no-render` |
| hoop tenon loose or tight in the base | `Stand.FIT` | `pocketwatch/stands/hoop/build_hoop.py` | `build_hoop.py` and `build_hoop_telegraph.py` |
| telegraph lever binds or wobbles on the pin | `Key.PIN_CLR` (lever bore), `Key.HOLE_CLR` (posts) | `pocketwatch/stands/hoop/build_hoop_telegraph.py` | that script |
| telegraph knob will not seat, or falls off | `Key.SOCK_CLR`, `Key.PEG_BARB` | same | that script |
| telegraph does not click, or clicks too early | `Key.G` (nub gap at rest) | same | that script; watch `knob travel to the click` |

Clearances are **per side**. A bore that is 0.2 mm tight on the diameter
needs +0.1 per side.

## 2. Step size

Measure if you can (calipers on the printed hole and the mating part); the
change is half the diametral interference or gap. Without a measurement:
tight → +0.10 per side; loose → -0.05 per side. Say which and why. History,
so you do not repeat it: `RAD_CLR` 0.85 did not fit, 1.15 did; `Stand.FIT`
0.25 and 0.12 printed loose, now 0.08; plate 0.18 fit after one print came
out ~1 mm large.

## 3. Rebuild, check, render, compare

Follow `change-a-model` steps 2 to 5: baseline output, edit, rebuild the
family, every check `[ok]`, render, compare with the committed PNG, update
the catalog status of every STL that changed.

## 4. Printer-specific or universal?

If the misfit is his printer's (it runs oversize or undersize everywhere),
do not change the owner's default. Add a variant the way the `roomy` plates
were added (a second constant and a second STL with the variant in its
name), or keep the change on his branch and say so in the PR. If both
printers agree, change the default.
