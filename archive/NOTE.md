Superseded scripts and renders, kept for reference.

**No STLs live here any more.** On 2026-11-22 every old, superseded, failed or
duplicate model was deleted so a newcomer only finds current designs in
`stl/`. Git history keeps them all. **The last commit that has every one of
them is `1580ce5`**: `git show "1580ce5:<path>" > old.stl`, or
`git checkout 1580ce5 -- archive/` to get the whole folder back.

## Deleted models (2026-11-22)

| was at | what it was | replaced by |
|---|---|---|
| `archive/esp32-s3-touch-lcd-146-stand.stl` | first 1.46 stand, before the two cover-glass options were known | `stl/large/Stand - cover glass.stl` |
| `archive/pre-stl-dir_*.stl` (3) | the three first desk stands, before `stl/` existed | `stl/small/`, `stl/large/` |
| `archive/old-filenames-2026-09-18/` (22) | stands, docks, pod, clips, rings and the slot gauge under their pre-09-18 names | the same parts in `stl/` with readable names |
| `archive/pod-stl-duplicates/` (7) | the old `pod/stl/` copies that went stale | `stl/pod/` |
| `archive/fit-test_pod-cup-1.28.stl`, `-1.46.stl` | bare pocket rings (09-18), never shipped | `stl/pod/Pod cup test - small.stl` |
| `archive/Pocketwatch - back (v1, wrong header span).stl` | pocketwatch v1 back (10-03), guides miss the real 30.0 headers | `stl/pocketwatch/Pocketwatch - plate.stl` |
| `archive/hoop-screw-v1/*.stl` (4) | hoop stand with an M3 screw joint; its 0.25 mortise printed loose | the snap-arm hoop in `stl/pocketwatch/stands/hoop/` |
| `archive/pendant-v1 (14.0 x 8.3 USB-C slot)/` (4) | pendant printed 2026-10-14; plug overmolds did not fit the slot | `stl/pocketwatch/pendant/` (port sticks out) |
| `archive/pendant-v2 (USB-C out, round window)/` | pendant case printed 2026-10-15; bar over the USB-C tab too thin | `stl/pocketwatch/pendant/Pendant - case.stl` |
| `stl/pocketwatch/stands/hoop/Hoop stand - base (snug, 0.12).stl`, `- base (medium, 0.18).stl` | screw-joint bases no script wrote any more; byte-identical to the `hoop-screw-v1` copies | `Hoop stand - base.stl` and its `looser` / `roomier` variants |
| `stl/pocketwatch/stands/hoop/Hoop stand - back plate (BOOT hole, roomy).stl` | a stale 10-13 copy no script wrote any more | `stl/pocketwatch/Pocketwatch USB-only - plate (BOOT hole, roomy).stl` |
| `stl/pocketwatch/stands/hoop/Hoop stand front-BOOT - base.stl`, `- rocker.stl` | front-BOOT rocker, printed 2026-10-13 | the telegraph key, `Hoop stand telegraph - *.stl` |
| `stl/pocketwatch/pendant/Pendant - kid button.stl` | twist-lock button; failed its print 2026-10-14 | `stl/pocketwatch/pendant/kids-case/` |
| `stl/pocketwatch/stands/pedestal/Pedestal (alternate, wedge) - body.stl` | the losing alternate pedestal shape | `Pedestal - body.stl` |
| `stl/small/Dock for right-angle cable - USB-C down.stl` | 1.28 dock for an L-shaped cable, badge turned over; missed on print, and the L-shaped cable was dropped | nothing: the pocketwatch stands |

## Deleted scripts and renders (2026-11-22)

All of these are byte-identical in `1580ce5`.

| was at | what it was |
|---|---|
| `build_stand_usbdown.py`, `renders/stand-1.28-usbdown-side.png`, `-back.png` | the USB-C-down dock's solid-overlap checks and renders; its `"1.28-usbdown"` entry left `build_stands.py` too |
| `pocketwatch/pendant/renders/twist-lock.png`, `kid-underside.png`, `section-boot-rest.png`, `section-boot-pressed.png` | renders of the failed kid button; `build_pendant.py` no longer draws it |
| `pocketwatch/stands/hoop/renders/frontboot-*.png` (6) | renders of the replaced front-BOOT rocker; `build_hoop_frontboot.py` no longer renders |
| `renders/01*`, `02-pod*`, `03*`, `04-assembly-*`, `05-trim*` (14 pod renders) | a second copy of `pod/renders/`; `pod/build_pod.py` now writes to `pod/renders/`, the copy `pod/README.md` links |

## Kept here

- `gen_stand.py`: 1.28-only generator, superseded by `build_stands.py`, which
  reproduces its output exactly.
- `hoop-screw-v1/`: the screw-joint hoop stand's script and README.
- `preview-side.png`, `preview-both.png`, `preview-all_pre-docks.png`: early
  stand previews, superseded by `preview-stands.png` and `preview-docks.png`.
- `fit-test-pod-cups.png`: render of the deleted bare pocket rings.
- `cup-stand-1.28-section.png`: a section cut through the plug slot that showed
  no wall. Replaced by `renders/cup-stand-1.28-empty-front.png`.
