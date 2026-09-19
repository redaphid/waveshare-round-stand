# Toolchain

Two pipelines. Know which you're in before you type `python`.

## 1. Pure standard library — stands, docks, validator, previews

`build_stands.py`, `check_stl.py`, `preview.py`. **System `python3`** (3.14).
`preview.py` needs matplotlib, which the system python has. Nothing else.

- Geometry is one 2D profile per stand, extruded; the notch is three slabs
  sharing a lower boundary so each internal face is a simple polygon.
  Ear-clipping triangulation, binary STL out.
- `check_stl.py <f>`: every directed edge used exactly once and paired, signed
  volume positive (normals outward), no zero-area facets. Exits non-zero on a
  problem — chain it in scripts.
- Limit: anything that varies along the extrusion. Don't fight it; use pipeline 2.

## 2. manifold3d — pod, clip, rings, button post

`pod/build_pod.py`, `build_stand_button.py`, `pod/render.py`. **Venv python:**

```
~/.venvs/cad/bin/python pod/build_pod.py          # gap12 (default)
~/.venvs/cad/bin/python pod/build_pod.py 26       # straight-plug variant
~/.venvs/cad/bin/python build_stand_button.py BOOT
```

Rebuild the venv from scratch if it's gone:

```
python3 -m venv ~/.venvs/cad
~/.venvs/cad/bin/pip install manifold3d trimesh numpy matplotlib
```

Don't try `pip install --user` — PEP 668 blocks it on this box, and there's no
sudo. No OpenSCAD installed either (`stand.scad` is for Aaron's own machine).

- `manifold3d` does robust booleans (`+ - ^`), `hull`, extrude, rotate,
  translate. **No fillets.** Check `.genus()` and trimesh `is_watertight` after
  every union; a failed boolean is silent.
- `manifold3d` has no `__version__`. Cylinders build along +Z from z=0; rotate
  them into place. When the sign of a rotation matters, **check numerically**
  (see `along_perp()` in `build_stand_button.py`) rather than trusting it.
- `pod/render.py`: headless matplotlib, no GL. **All solids go into one
  depth-sorted `Poly3DCollection`** — per-solid collections draw in layers and
  hide interior parts (v1 bug). Painter's algorithm still gets interpenetrating
  meshes slightly wrong; that's cosmetic. Key light + sky term for shading.
- Sectioned views: subtract a box (`man - boxat(...)`) or intersect (`man ^ box`)
  and render the result. Cheap and very informative.

## Validating a build

`./build_all.sh` does all of this; by hand:

```
python3 build_stands.py && for f in stl/*.stl; do python3 check_stl.py "$f"; done
python3 preview.py
~/.venvs/cad/bin/python pod/build_pod.py && ~/.venvs/cad/bin/python pod/build_pod.py 26
~/.venvs/cad/bin/python build_stand_button.py BOOT && ... RESET
python3 - <<'PY'   # relative links + images resolve
...
PY
```

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

System python has numpy, scipy, PIL, matplotlib for this.

## Printer and slicer

- **Elegoo Centauri Carbon 2**, 0.6 nozzle, `10.0.4.1`. Reached through the
  `soul` MCP: `centauri__get_status`, `centauri__print_history`,
  `centauri__upload_file`, `centauri__start_print`. Errors like *":1883 (CC2/MQTT)
  is closed and :3030 (CC1/SDCP) did not answer"* mean it's powered off, not
  misconfigured — ask before assuming.
- **ElegooSlicer 1.5.3.5** (OrcaSlicer 2.4.2 fork), Windows:
  `D:\tools\ElegooSlicer\elegoo-slicer.exe`. User presets:
  `C:\Users\hypnodroid\AppData\Roaming\ElegooSlicer\user\default\{machine,process,filament}\`.
  System presets: `D:\tools\ElegooSlicer\resources\profiles\Elegoo\`.
- Presets matching his last successful print: printer **`Elegoo Centauri Carbon
  2 0.6 nozzle`**, process **`0.30mm Standard @Elegoo CC2 0.6 nozzle - Copy`**,
  filament **`PRUSA Strontium`** → inherits `Elegoo PETG PRO @ECC2`, **260 °C /
  85 °C, PETG**. Textured plate.

### Headless slicing — post-mortem, so nobody repeats it

Goal was `elegoo-slicer.exe --load-settings … --slice 0` from WSL. Findings:

1. The exe swallows stdout; `--help` prints nothing. Redirect to a file.
2. User preset JSONs have no `type` field → *"unknown config type"*. Adding
   `"type": "process"` etc. fixes that; removing `from` breaks it (*"from
   unsupported"*) — keep `"from": "User"`.
3. The CLI does **not** resolve a preset's `inherits` chain when handed a
   standalone file, so parent-only settings vanish and validation fails
   (*"Relative extruder addressing requires … G92 E0"*). `flatten_presets.py`
   walks and merges the chain. **Scope the index to the Elegoo vendor dir** —
   names like `fdm_machine_common` exist in every vendor and a global index
   resolves to another printer. Globbing all 11k vendor JSONs over `/mnt/d`
   also takes minutes.
4. With fully flattened presets it exits **239 with no output even at
   `--debug 5`**. Not solved. Aaron said drop it; he slices in the GUI.

If it ever matters again: the next thing to try is `--datadir` pointing at the
AppData folder with presets referenced **by name**, or exporting a `.3mf` project
from the GUI (his `stand.3mf` has a full `Metadata/project_settings.config`) and
slicing that.

## WSL notes

- `/mnt/d` and `/mnt/c` are 9P mounts — slow for recursive globs; fine for
  copying a few files.
- Windows executables run from WSL (`./elegoo-slicer.exe`) but want Windows
  paths (`D:\…`) in their arguments.
- `/usr/bin/node` is broken on this box; use `~/.local/node22/bin`. Not needed
  for this project.
