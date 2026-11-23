---
name: print-a-part
description: Help someone choose a part from the waveshare-round-stand catalog and print it on his own printer - which file, which board, its status and evidence, orientation, supports, what is risky about an unprinted design, and what to tell the owner afterwards. Use when asked what to print, "which file do I print", "how do I print the case or the telegraph", or before slicing any STL from this repo.
---

# Print a part

The catalog is `stl/catalog.toml` (human view: `stl/README.md`). Read the
family's rows there; do not guess a part's status from its file name.

## 1. Choose

Lead with the featured models, in this order:

1. **Pocketwatch case, USB-only** (`pocketwatch` family): `Pocketwatch
   USB-only - plate.stl` (proven) + `- case.stl` (needs-work, fix applied,
   unprinted). Simplest and most likely to succeed. **Print the bore fit
   gauge first** if his printer has not been calibrated (the
   `calibrate-my-printer` skill).
2. **Telegraph key stand** (`telegraph` family): the USB-only case fused into
   a hoop leaning 40°, plus base, lever, knob and pin, and the button back
   plate (`also =` in its catalog row). Status **printed** on the owner's word
   only; nothing about its fit is recorded. Print it after the case.

For anything else, filter rows by `board` (the owner's badge is the 1.28) and
`status`. Read the family's `about`, `note` and `readme` before printing.

## 2. Say what the status means for this print

| status | tell him |
|---|---|
| proven | the owner printed it and it worked (cite the `log` date in `docs/PRINT-LOG.md`) |
| printed | it came off a printer; the result is partial or unrecorded |
| needs-work, `fixed = true` | the last print had a problem; this file has the fix; **his print is the first test of it** |
| unprinted | it passes every check in the script but nobody has printed it. Expect one iteration. |

## 3. Print settings

- **Orientation:** the part's `print` field (for example `bezel down`, `flat
  back down, guides and post up`, `on its side, as exported`). Orient it
  that way in the slicer; do not assume the STL is already on that face.
- **Supports:** none. The pocketwatch parts are checked for bridges up to
  `BRIDGE_MAX` = 10 mm and no unsupported overhangs; if his slicer wants
  supports somewhere, that is worth reporting.
- **Material:** PLA unless the family says otherwise. The flexures (snap
  arms, the telegraph's hairpin and blade, the button plate's tab) are sized
  for PLA's stiffness; PETG will feel softer.
- **Infill:** the slicer default, except where `print` says (the telegraph
  base: 100 %, it is the ballast).
- Layer height and nozzle: his choice. The owner prints 0.30 mm layers on a
  0.6 mm nozzle; finer is fine.

## 4. After the print

Use the `after-a-print` skill: log it in `docs/PRINT-LOG.md` first (part,
file, printer, material, result in his words, a photo), then decide the one
number to change, if any. Tell the owner, in one message: what was printed,
what fit, what did not, and the one decision you need from him.
