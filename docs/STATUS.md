# Status, 2026-11-22

**Where everything stands.** The pocketwatch case and the telegraph key are
the focus; both are at least partly print-verified. Everything else is
either a concept or retired. Print evidence comes from
[PRINT-LOG.md](PRINT-LOG.md) or the owner's own words, never an agent's
summary.

## Designs

| family | built | printed | result | next step |
|---|---|---|---|---|
| **Pocketwatch case, USB-only** | yes | case and plate, 2026-10-13 and 10-14 | plate **proven**; case "a great fit", then too tight to pry off and USB-C slot too small | print the fixed case (pry notch, slot 2 mm bigger) |
| Pocketwatch case, battery (v2) | yes | case and plate, 2026-10-12 and 10-13 | plate **proven** ("great"); case "looking better", slot cut down | print the fixed case and the lid |
| **Telegraph key stand** | yes, 40° and 50° | 40° parts, by 2026-11-22 | "at least somewhat verified" (owner); no fit details | ask the owner which lean, the click travel, any fit problems; log it |
| Bore fit gauge | yes | 2026-10-13 | **proven**: ring 4 (1.15) fits | have contributors print it on their printers |
| Hoop stand | yes | base, hoop, plate, 2026-10-13 | case loose in the mortise; dimple melted | print the snap-tenon hoop and the 0.08 base |
| Pendant | yes | case and plate, 2026-10-14 and 10-15 | plate **proven** ("that pretty much worked"); bar over the tab too thin | print the case with the flat-top window |
| Kids case | yes | no | | first print; it replaced the kid button that failed |
| Battery pendant | yes | no | | first print |
| Wearable pendants | yes | no | | measure a 503035 cell before the 500 mAh one |
| Monitor gauge pod | yes | no | | print the cup test and trim rings first |
| 9 stand and clip concepts | yes | no | | concept art; nothing planned |
| Wedge desk stands | yes | 2026-09-18 and 09-20 | 2 **proven** | retired: "didn't protect the device enough" |

106 STLs in all: 7 proven, 6 printed, 6 printed and needing work, 87 never
printed. Per file: [stl/README.md](../stl/README.md). Per family:
[docs/models/](models/README.md).

**Old models were deleted, not archived** (2026-11-22): superseded, failed
and duplicate STLs, so a newcomer finds only current designs. **The last
commit with every one of them is `1580ce5`.** The list:
[archive/NOTE.md](../archive/NOTE.md).

## The owner's requirements (from 2026-10-03, still standing)

- **Pocketwatch look.** The USB-C plug at 12 o'clock is the crown, and any
  straight cable is the chain. No right-angle plug sizing.
- **The back engages the headers** to hold the badge in, and **pressing the
  screen clicks BOOT.** So the guides grip in x only, are open in y and free
  in z; the badge floats 0.7 mm; the back is fixed to the case, not the
  board.
- **Don't make him measure what a design can avoid.** He has little time.
- Print in **PLA** (since 2026-10-14).

## Branches

| branch | head | state |
|---|---|---|
| `main` | 1dfad6a | the catalog, every current design, old models deleted (PRs #2, #3) |
| `agents-for-contributors` | 29825bf | PR #4, open: AGENTS.md, `setup.sh`, contributor skills |
| `docs-state-of-things` | this branch | stacks on #4: README, `docs/`, per-model pages |
| `pocketwatch` | 1580ce5 | fully merged into `main`; safe to delete |
| `pocketwatch-v2` | 373f536 | local only, fully merged, stale v1 work; safe to remove |
| `coworker-kit` | 051ad54 | **parked.** One WIP commit: a pocketwatch CLI (`--battery TxWxL`, `--set NAME=VALUE`, `--name`), unreviewed and untested. It branched before the catalog existed, and its diff against `main` deletes about 14,000 lines. Do not merge it; port the CLI by hand if a second battery size is ever needed. |

## Loose ends

- **Telegraph print details.** The owner says it is at least partly
  verified; which lean, the click travel and the fits are not recorded.
- **USB-only case, battery case, pendant case, hoop:** each has a fix that
  has not been printed.
- **Hardware guesses:** the BOOT switch's position and height and the
  battery connector's position and size are unmeasured
  ([MEASUREMENTS.md](MEASUREMENTS.md#still-a-guess)). The photo-measured
  switch position used by the wedge stand differs from the pocketwatch guess
  by about 0.3 mm.
- **Kid button:** it failed "in a number of ways. For one, it didn't fit."
  Ask the owner what else went wrong before reusing any of it.
- **500 mAh cell size** is assumed from its code.
- **The owner's printer** has failed most prints since June 2026:
  [PRINTER-TROUBLE.md](PRINTER-TROUBLE.md).
- **Two board sizes in the code:** the retired wedge stands use the
  drawing's Ø36.5; the pocketwatch uses the measured Ø35.31. The stands are
  print-proven, so their geometry stays.
- The USB-C-down dock missed on print and was deleted ("We don't need to
  worry about the l-shaped cable anymore"); last in `1580ce5`.

## The board

`pocketwatch-schematics` is public, read-only, through
`https://draw.hypnodroid.com/view/pocketwatch-schematics/mcp`; editors use
the `/b/` address. Theme `architect-parchment`. The telegraph frames are now
generated from the CAD by
`pocketwatch/stands/hoop/board_schematics_telegraph.py`. A camera tour (the
present path `golden-path`) is being recorded. Details:
[BOARD.md](BOARD.md).

**Stale on the board (2026-11-22):** the print-results card calls the
USB-only case "proven", but PRINT-LOG has it needing work since 2026-10-14;
the telegraph fit cards say "not printed yet", but the owner reports a
print. The code and the print log win.
