---
name: pod-iterate
description: Iterate the gauge pod / monitor clip in waveshare-round-stand — change a parameter in pod/build_pod.py, rebuild with the CAD venv, render, check the specific things that have gone wrong before. Use for any pod, clip, or trim-ring change.
---

# Iterate the pod

```
~/.venvs/cad/bin/python pod/build_pod.py        # gap12 — the default, right-angle cables
~/.venvs/cad/bin/python pod/build_pod.py 26     # straight-plug variant
```
Both run every time (`build_all.sh` does). Venv missing → `docs/TOOLCHAIN.md`.

## Frame (don't re-derive)
You sit at −Y looking +Y. Screen = XZ plane at y=0. Pod on the monitor's
**right** edge (+X), Z up. Cups face −Y, canted `CANT` about Z toward you.
Spine on the monitor side (x from `BB_X0`), cups cantilevered outboard. Rail on
the spine's −X face → clip socket on the clip's +X face. Wiring channel down
the spine's **back**.

## Things that have gone wrong — check each render for them
- **Gauges invisible** → renderer regression; all parts must be one
  `Poly3DCollection` (`pod/render.py`).
- **Pod faces away from the user** → rail/channel on the wrong faces.
- **Nothing retains a gauge** → the trim ring must be flush with the cup face
  and `RING_PRESS` > 0.
- **1.46 won't seat** → its shoulder must grip the *glass* (seat_t 1.3) and
  `bore_r` ≥ 21.29+0.25 so standoffs pass.
- **Plug doesn't fit the gap** → `GAP` 12 needs a right-angle head ≤ ~9 mm
  deep; drop slot 16 wide; pass-through into the channel present.
- **Clip wall too thin** → `SPINE_X` − 10 − `DOVE_D` ≥ 4 (tongue channel ends at
  x=10; socket is `DOVE_D` deep from the outer face).
- **Pod rocks on the clip** → two clips, spaced; never one.
- **Tall/heavy** → `MARGIN`, `CUP_PROUD`, `BB_W/BB_D`. Volume is model volume;
  printed mass at 15 % infill is ~40 %.

## Renders to look at, in order
`01-pod-gap12-front-quarter` (does it read as a pod?), `02-…-back` (channel,
rail, pass-throughs), `03b-clip-section` (tongue in channel, lock slot,
socket, wall thicknesses), `04-assembly-gap12-edge-20mm` (two clips, pod
against the monitor, cups 6 mm proud), `05-trim-ring-detail`.

Then `rebuild-and-ship`.
