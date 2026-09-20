# Waveshare round-board desk stands

Minimal angled stands for Waveshare's round ESP32-S3 display boards. One design,
three sizes: a tapered wedge with a groove angled 20° back from vertical, and a
cable notch cut straight through the middle so a USB-C lead runs *through* the
stand rather than over it. The board drops in rim-first — nothing clips, nothing
flexes, no fasteners.

![low stands](preview-stands.png)

| board | stand | groove | notch | screen top | material |
|---|---|---|---|---|---|
| ESP32-S3-LCD-1.28 (SKU 26541) | [`stl/small/Stand.stl`](stl/small/Stand.stl) | 5.4 × 5 mm | 13 mm | 41.6 mm | 4.6 g |
| ESP32-S3-Touch-LCD-1.46, cover glass | [`stl/large/Stand - cover glass.stl`](<stl/large/Stand - cover glass.stl>) | 13.1 × 8 mm | 14 mm | 50.6 mm | 8.9 g |
| ESP32-S3-Touch-LCD-1.46, bare | [`stl/large/Stand - no cover glass.stl`](<stl/large/Stand - no cover glass.stl>) | 11.5 × 8 mm | 14 mm | 48.5 mm | 8.2 g |

### Docks — for a straight USB-C cable in the bottom port

The low stands leave ~5 mm under the board rim. A straight USB-C plug body is
~20–25 mm, so with the 1.46's bottom port in use the board can't seat — it ends
up lying across the stand. The docks lift the board so the plug hangs straight
down through the notch and the cable turns out the back at desk level.

![docks](preview-docks.png)

| board | dock | clear under rim | screen top | material |
|---|---|---|---|---|
| ESP32-S3-Touch-LCD-1.46, cover glass | `large/Dock for straight cable - cover glass.stl` | **27.0 mm** | 72.6 mm | 19.8 g |
| ESP32-S3-Touch-LCD-1.46, bare | `large/Dock for straight cable - no cover glass.stl` | **26.9 mm** | 70.5 mm | 17.9 g |

Same groove, same notch (widened to 16 mm for plug bodies), ridge raised from
16 mm to 38 mm and the groove moved 3 mm back. Sized for a 24 mm plug body with
3 mm spare for the cable to turn. Because the board leans back, the plug leans
*forward* as it descends and lands about 6 mm in from the front edge; the notch
is open at both ends, so the cable runs out the front or 32 mm back along the
floor to exit behind. Twice the material of the low stand — the cost of holding
the board 27 mm off the desk.

Print flat on the base. No supports, no overhangs. Masses are PETG.

**1.28 with a button:** `stl/small/Stand - BOOT button.stl` adds a post behind the
badge's BOOT switch so pressing the screen clicks it (RESET twin too). Details
in [`PRINTING.md`](PRINTING.md#the-128-button-post-stands).

![BOOT post](renders/stand-1.28-BOOT-post-back.png)

**Printable files live in [`stl/`](stl/).**

## The pod — where this is heading

The stands were the warm-up. The goal is an **instrument cluster clipped to the
side of a monitor** with the look of a 2G DSM A-pillar gauge pod: cups, trim
rings, gauges canted toward you. That lives in [`pod/`](pod/) — its own README,
STLs, and renders. The stands and docks above stay as they are.

![pod](pod/renders/01-pod-gap12-front-quarter.png)

## Start here

- **[`PRINTING.md`](PRINTING.md)** — which file to print, slicer presets, plate
  orientation, how to seat each board, what the notch does and doesn't do.
- **[`BOARDS.md`](BOARDS.md)** — verified dimensions and pin maps for both
  boards, how the two sizes actually compare, and how to tell the two 1.46
  variants apart.
- **[`reference/`](reference/)** — Waveshare's own outline and pinout drawings,
  with source URLs in [`SOURCES.md`](reference/SOURCES.md).

## Three things worth knowing

1. **The 1.46 ships in two cover-glass options and they are different parts** —
   Ø44.77 / 12.30 mm thick with glass, Ø42.58 / 10.65 mm without. The grooves
   differ by 1.65 mm. Check yours before printing; see `BOARDS.md`.
2. **On the low stands the notch is a cable route, not a plug socket.** It
   leaves 4.1–5.4 mm under the board rim — fine for a bare lead or a
   right-angle plug, not a straight plug in the bottom port. **For a straight
   plug, print the dock.** See `PRINTING.md`.
3. **The two boards are closer in size than they look.** The 1.46's PCB is only
   6.1 mm wider than the 1.28's. What differs enormously is thickness — 1.6 mm
   of bare PCB rim versus a 12.3 mm stack.

## Why these aren't from Printables

Nothing there targets these boards. Searches surface models for the
**ESP32-S3-Touch-LCD-1.28** (a different outline from the non-touch 1.28) or for
the bare 1.28-inch LCD module. So these are built from Waveshare's outline
drawings instead — neither product page states its dimensions in text, they
exist only inside a diagram image.

## Design

A straight groove holding a round board is the plate-stand trick: the disc
contacts the groove on two lines and cannot rock. It buys three things over a
cradle or a tripod — no supports needed, no thin snap features to fatigue, and
because the board is round you can rotate it to put the connectors where you
want them.

The solid is three slabs stacked across the width: full wedge, base slab, full
wedge. The two outer slabs carry the groove; the middle one is just the floor,
which is what makes the notch. Because the slabs share their lower boundary
exactly, the exposed face at each internal boundary is one simple polygon, so
the mesh comes out watertight without needing a general polygon boolean.
`check_stl.py` proves that rather than assuming it.

## Files

| file | what it is |
|---|---|
| `build_stands.py` | generates all five STLs from one parameter table; prints a geometry report and asserts the board fits the base, the centre of mass stays centred, the notch floor clears the groove floor, a cable actually fits under the rim, and — for docks — that a straight plug does |
| `build_stand_button.py [BOOT\|RESET]` | the 1.28 stand with a switch post; manifold3d, in the `~/.venvs/cad` venv |
| `build_all.sh` | everything below, plus a docs link-check; run before any commit |
| `check_stl.py <f.stl>` | verifies watertightness, outward normals, no degenerate facets; exits non-zero on a problem |
| `preview.py` → `preview-stands.png`, `preview-docks.png` | side sections and front elevations per family, board drawn in place |
| `stand.scad` | same model, parametric, for tweaking in OpenSCAD; set `variant` at the top |
| `flatten_presets.py` | resolves an ElegooSlicer preset's `inherits` chain into one flat preset — see the automation note in `PRINTING.md` |
| `pod/` | the gauge pod + adjustable monitor clip — see [`pod/README.md`](pod/README.md) |
| `archive/` | superseded files, kept rather than deleted; see `archive/NOTE.md` |

## For whoever works on this next

- **[`CLAUDE.md`](CLAUDE.md)** — the agent brief: what's verified, conventions, how to work here
- **[`docs/DESIGN.md`](docs/DESIGN.md)** — every design decision and what it replaced
- **[`docs/TOOLCHAIN.md`](docs/TOOLCHAIN.md)** — the two pipelines, venv setup, renderer limits, the slicer-CLI post-mortem
- **[`docs/PRINT-LOG.md`](docs/PRINT-LOG.md)** — what has actually been printed
- **`.claude/skills/`** — `rebuild-and-ship`, `add-board`, `measure-drawing`, `after-a-print`, `pod-iterate`
- **`./build_all.sh`** — rebuild, validate, render, link-check, in one go

## Regenerating

```
./build_all.sh
```

Or piecemeal:

```
python3 build_stands.py
for f in stl/*/*.stl; do python3 check_stl.py "$f"; done
python3 preview.py
```

Pure standard library for the STL generator and validator; matplotlib only for
the previews.

## Licence

MIT — see [`LICENSE`](LICENSE).
