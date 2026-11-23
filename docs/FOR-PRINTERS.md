# For printers

You know printing better than the owner does. This page skips the basics and
gives you three things: **what to calibrate first, what to print, and which
numbers are still open.** No particular printer or slicer is assumed.

**The owner's numbers came from a 0.6 mm nozzle at 0.30 mm layers**, in PLA
for everything in the pocketwatch family. The clearances below are tuned to
that. Yours may differ, which is why the gauge comes first.

## 1. Calibrate: the bore fit gauge

Print [`stl/fit-gauges/Pocketwatch - bore fit gauge.stl`](<../stl/fit-gauges/Pocketwatch - bore fit gauge.stl>),
bezel down, about 10 minutes. Four rings, ring N has N dots.

Drop the badge in from the back, screen first, tab in the slot. **The
tightest ring where the glass sits flat on the lip is your bore clearance.**

| ring | per side | then |
|---|---|---|
| 1, 2 or 3 | 0.25, 0.55, 0.85 | set `Case.RAD_CLR` to it in `pocketwatch/build_pocketwatch.py`, then rebuild (below) |
| 4 | 1.15 | print the case as it is: that is today's value |

No badge yet? Print the gauge anyway and give it to the owner with the case.
He reads it; you reprint only if his answer is not ring 4. The
`calibrate-my-printer` skill has the details.

## 2. Print the pocketwatch case

All files print as exported, with no supports. Use PLA unless you have a
reason not to: the flexing parts are sized for PLA's stiffness.

| order | file (`stl/pocketwatch/`) | status | orientation |
|---|---|---|---|
| 1 | `Pocketwatch USB-only - plate.stl` | **proven** | flat back down |
| 2 | `Pocketwatch USB-only - case.stl` | fix applied, **unprinted since** | bezel down |

**Check after printing:** the plate snaps in and can be pried out at the
notch; a straight USB-C plug enters the slot at 12 o'clock; pressing the
screen clicks BOOT. If the plate is tight, print `- plate (roomy).stl`
(0.65 per side instead of 0.18).

## 3. Then the telegraph key stand

From `stl/pocketwatch/stands/hoop/`: the `(40 deg)` hoop and case, base and
lever, plus `- knob.stl` and `- pin.stl`, and the back plate
`Hoop stand - back plate (button).stl`. **Base at 100% infill**: it is the
ballast. The lever prints on its side. Its four fits (pin, posts, lever,
knob) have never been measured on a print: see
[docs/models/telegraph-key.md](models/telegraph-key.md).

Every other file, and its status: [stl/README.md](../stl/README.md).

## Which numbers are yours, which are the badge's

**Printer clearances.** They depend on your printer. Settle them with your
prints and change the constant.

| fit | file | constant (today, per side) | settled by |
|---|---|---|---|
| badge in the case bore | `pocketwatch/build_pocketwatch.py` | `Case.RAD_CLR` (1.15) | the bore fit gauge |
| plate in the case | `pocketwatch/build_pocketwatch_usb.py` | `PLATE_DISC_CLR` (0.18), `PLATE_DISC_CLR_ROOMY` (0.65) | the plate print |
| USB-C slot | `pocketwatch/build_pocketwatch.py` | `Case.RECESS_W` 9.4, `RECESS_T` 3.6, `RECESS_GROW` 2.0 | the case print and your cable |
| hoop tenon in the base | `pocketwatch/stands/hoop/build_hoop.py` | `Stand.FIT` (0.08) | the base print (0.25 and 0.12 were loose) |
| telegraph pin, posts, knob | `pocketwatch/stands/hoop/build_hoop_telegraph.py` | `Key.PIN_CLR` 0.15, `HOLE_CLR` 0.10, `CLR_X` 0.4, `SOCK_CLR` 0.15 | the telegraph print |
| battery plate snap | `pocketwatch/build_pocketwatch.py` | `Case.SNAP_INT` 0.30, `SNAP_CLR` 0.15 | the battery case print |

**Hardware guesses.** They depend on the badge, not your printer. Nobody has
measured them: the switch position and height, and the battery connector's
position and size. Every one, with how to measure it:
[docs/MEASUREMENTS.md](MEASUREMENTS.md#still-a-guess).

## Change a number

```
./setup.sh                                                     # once: makes .venv, Python 3.11+
./tools/py pocketwatch/build_pocketwatch_usb.py --no-render   # rebuild the USB-only case and plate, checks only
```

Every check prints `[ok]` or `[FAIL]`. A failure is a finding: fix the
geometry, not the check. Then run it without `--no-render` and look at the
renders in `pocketwatch/renders/`. [AGENTS.md](../AGENTS.md) has the full
setup and a worked example; the `change-a-model` and `tune-fit` skills walk
through it.

## Settle with Aaron

A short list to go through together, in this order:

- [ ] **Bore:** which gauge ring fits on your printer?
- [ ] **Plate:** does the default plate fit, or the roomy one?
- [ ] **USB-C:** does a straight plug from the cable he uses enter the slot?
- [ ] **BOOT:** does pressing the screen click it? If not, measure the switch
  position and height on his badge (the `settle-dimensions` skill).
- [ ] **Telegraph:** which lean did he print, and where does it click?
- [ ] **Material:** PLA, or something else for the parts he handles?

Write each result in [docs/PRINT-LOG.md](PRINT-LOG.md) before changing a
number (the `after-a-print` skill has the template), then open a PR.

## If something goes wrong on his printer

The owner's printer has failed most prints since June 2026. What is known
and what to try: [docs/PRINTER-TROUBLE.md](PRINTER-TROUBLE.md). The
`debug-the-printer` skill helps you work through it with him.
