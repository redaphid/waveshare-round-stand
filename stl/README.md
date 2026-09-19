# Printable files

One folder per badge, plus the pod.

| folder | badge |
|---|---|
| **`small/`** | the **1.28** (ESP32-S3-LCD-1.28, SKU 26541) — Ø36.5, non-touch |
| **`large/`** | the **1.46** (ESP32-S3-Touch-LCD-1.46). Yours is the **cover glass** one — every file says which it is for |
| **`pod/`** | the monitor pod, which holds both (one large on top, two small) |

Print everything flat as exported, no supports, unless the row says otherwise.
Slicer settings and seating: [`../PRINTING.md`](../PRINTING.md). Masses are PETG
at 1.27 g/cm³.

## `small/` — the 1.28

| file | what it is | material |
|---|---|---|
| `Stand.stl` | desk stand. 5.0 mm groove, sized with the fit gauge. USB-C tab at the top | 4.6 g |
| `Stand - BOOT button.stl` | the stand plus a post behind the badge: press the screen → clicks **BOOT** (GPIO0, the user button) | 4.7 g |
| `Stand - RESET button.stl` | same, clicks **RESET** | 4.7 g |
| `Pod cup test.stl` | one pod cup on a desk base — **print before the pod**. Exported face-up: print as is, then stand it on its two feet. Badge **USB-C tab down**, then press the trim ring in | ~16 g |
| `Trim ring - small.stl` | presses into a pod cup (or the cup test) to hold the badge in. The pod needs **2** | 0.4 g |
| `Slot fit gauge.stl` | eight slots, 3.0 → 6.5 mm. Slot N has N dots under it; slot 1 is at the chamfered end | ~6 g |

**Button stands:** seat the badge **USB-C at the top**; the post is behind the
lower-right (BOOT) or lower-left (RESET) as you look at it. See `PRINTING.md`.

**Pod cup test — what to report:** does the badge drop onto the ledge without
force, does the tab clear its notch, does the ring press in and hold. Loose or
tight: say which.

## `large/` — the 1.46

The two 1.46 versions are **not** interchangeable: 12.30 mm vs 10.65 mm thick,
so the grooves differ by 1.65 mm. Not sure which you have? See "telling them
apart" in [`../BOARDS.md`](../BOARDS.md).

| file | what it is | material |
|---|---|---|
| `Stand - cover glass.stl` | desk stand, **yours** | 8.9 g |
| `Dock for straight cable - cover glass.stl` | taller stand with 27 mm under the rim, for a **straight** USB-C plug in the bottom port | 19.8 g |
| `Trim ring - large.stl` | presses into the pod's top cup. The pod needs **1** | 1.4 g |
| `Stand - no cover glass.stl` | desk stand for the other version | 8.2 g |
| `Dock for straight cable - no cover glass.stl` | dock for the other version | 17.9 g |

**Stand or dock?** A straight USB-C cable in the bottom port needs the dock —
the stand leaves ~5 mm under the rim and a plug body is ~24 mm. Right-angle
cable, battery, or port turned sideways: the stand is fine and half the plastic.
The dock's notch is open both ends, so the cable can leave front or back.

## `pod/` — the monitor pod

| file | what it is | qty |
|---|---|---|
| `Pod - right-angle cables.stl` | the pod, 12 mm between gauges — for right-angle USB-C cables (yours). 181 mm tall | 1 |
| `Pod - straight cables.stl` | the pod with 26 mm gaps for straight plugs. 209 mm tall | instead of the above |
| `Clip - fixed jaw.stl` | clamps to the monitor edge (8–32 mm) | **2** |
| `Clip - slider.stl` | the clip's sliding jaw, locked with an M3 × 12 | **2** |

Plus from the other folders: `large/Trim ring - large.stl` ×1 and
`small/Trim ring - small.stl` ×2. Details in [`../pod/README.md`](../pod/README.md).

## Rebuilding

`./build_all.sh` from the repo root regenerates every file here.
