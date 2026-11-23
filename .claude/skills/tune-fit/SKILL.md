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
| glass will not seat, badge will not drop into the case, or rattles | `Case.RAD_CLR` | `pocketwatch/build_pocketwatch.py` | `./tools/py pocketwatch/build_pocketwatch_usb.py --no-render`, then `./build_all.sh --no-render` (shared; see *Ceiling*) |
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

### Ceiling: the case bore

The USB-only case and the telegraph take **two steps, +0.20 per side:
`RAD_CLR` 1.15 → 1.35**. Past 1.35 the USB-C plug engages the port less than
3.5 mm, and clearance cannot fix that. Measured against every check, in
0.01 steps:

| `RAD_CLR` | what fails | why |
|---|---|---|
| 1.15 to 1.20 | nothing | |
| 1.21 | pedestal (watertight) | a mesh pinch at this one value |
| 1.22, 1.23 | lowprofile (watertight) | a mesh pinch at these two values |
| 1.24 and up | pendant, kids case | the bar above the glass drops under 3.5 |
| 1.32 and up | scissor, te | screw and peg holes come within 1.2 of the bore |
| 1.35 | sidepod, braun | plug engagement reads 3.50, under 3.5 after rounding |
| 1.36 and up | every design that checks plug engagement | plug engagement under 3.5 |

The hoop, telegraph, battery case, wearable and gauge pass every check to
1.45. The hoop and telegraph hold the same crown as the USB-only case and
have no engagement check of their own, so treat 1.35 as their ceiling too.

`RAD_CLR` is shared: set it for the design you print, rebuild everything,
and keep the change on your branch, or add a roomy-bore variant (like the
`roomy` plates). Past 1.35, the plug-engagement geometry (the crown boss and
the USB-C recess in `Case`) must change, which is a design change to agree
with the owner.

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
