# Toolchain

Setup is in [AGENTS.md](../AGENTS.md#setup): `./setup.sh` makes `.venv/`
from `requirements.txt` (Python 3.11+), and `./tools/py <script>` runs a
script with the right interpreter. This page covers the two geometry
pipelines and the renderer's limits.

## 1. Pure standard library: wedge stands, docks, validator, previews

`build_stands.py`, `check_stl.py`, `preview.py`. Standard library only;
`preview.py` also needs matplotlib.

- Geometry is one 2D profile per stand, extruded; the notch is three slabs
  sharing a lower boundary so each internal face is a simple polygon.
  Ear-clipping triangulation, binary STL out.
- `check_stl.py <f>`: every directed edge used exactly once and paired, signed
  volume positive (normals outward), no zero-area facets. Exits non-zero on a
  problem, so chain it in scripts.
- Limit: anything that varies along the extrusion. Don't fight it; use
  pipeline 2.

## 2. manifold3d: everything else

Every pocketwatch design, the pod, the button-post stand, and their renders.

```
./tools/py pocketwatch/build_pocketwatch_usb.py --no-render
./tools/py pod/build_pod.py          # gap12 (default)
./tools/py pod/build_pod.py 26       # straight-plug variant
./tools/py build_stand_button.py BOOT
```

- `manifold3d` does robust booleans (`+ - ^`), `hull`, extrude, rotate,
  translate. **No fillets.** Check `.genus()` and trimesh `is_watertight` after
  every union; a failed boolean is silent.
- `manifold3d` has no `__version__`. Cylinders build along +Z from z=0; rotate
  them into place. When the sign of a rotation matters, **check numerically**
  (see `along_perp()` in `build_stand_button.py`) rather than trusting it.
- `pod/render.py`: headless matplotlib, no GL. **All solids go into one
  depth-sorted `Poly3DCollection`**: per-solid collections draw in layers and
  hide interior parts (a v1 bug). Painter's algorithm still gets
  interpenetrating meshes slightly wrong; that's cosmetic. Key light plus a
  sky term for shading.
- Sectioned views: subtract a box (`man - boxat(...)`) or intersect
  (`man ^ box`) and render the result. Cheap and very informative.

## Validating a build

`./build_all.sh` builds and checks every model, renders, and runs
`check_docs.py` (every link and backticked path in every tracked Markdown
file must exist). `--no-render` skips the slow renders.

Then **open the renders**. A clean report is necessary, not sufficient.

## Measuring from a vendor drawing

Waveshare states dimensions only inside images. Procedure that worked twice
(`reference/esp32-s3-lcd-1.28-switch-positions.png` is the output):

1. `curl` the wiki page, `grep -oE '/w/upload/[^"]*\.(jpg|png)'`, pull the
   candidates, view them. The outline drawing is usually `…-003.jpg` or
   `…-introduction-04.jpg`. Save it under `reference/` and cite it in
   `reference/SOURCES.md`.
2. Read the dimensioned drawing directly (the Read tool shows images).
3. For features the drawing doesn't dimension: threshold the PCB colour to fit
   the disc, use one known dimension (R 18.25) for the px→mm scale, find the
   feature blobs by colour + size + radius band, `scipy.ndimage.label`. Save an
   overlay with the fit circle and a mm grid so the number can be checked by
   eye later. ±0.5 mm is realistic.

The `measure-drawing` skill has the full procedure. Numbers measured on real
hardware beat drawing numbers: [MEASUREMENTS.md](MEASUREMENTS.md).

## Printer and slicer

Nothing here depends on a printer or slicer. The owner's Elegoo, his
presets and the headless-slicing post-mortem (`tools/elegoo/`) are in
[ELEGOO.md](ELEGOO.md).
