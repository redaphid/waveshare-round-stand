#!/usr/bin/env python3
"""
Groove fit gauge: one bar, eight slots 3.0 .. 6.5 mm wide in 0.5 steps.

Slide the badge's rim into each slot; the narrowest one it drops into freely is
the groove width to use (`gap` in build_stands.py). Printed on the same
printer/nozzle/filament as the stand, so print shrinkage is already in the
answer.

Slot N (1 = narrowest, at the end with the chamfered corner) has N dots
punched in the front face under it.

Run with ~/.venvs/cad/bin/python.
"""
import sys, numpy as np, manifold3d as m3, trimesh
sys.path.insert(0, "pod"); from render import render

WIDTHS = [3.0 + 0.5*i for i in range(8)]
DEPTH, WALL, BAR_D, BAR_H = 6.0, 2.4, 12.0, 12.0
DOT_R, DOT_DEEP = 0.45, 0.6

L = WALL + sum(w + WALL for w in WIDTHS)
bar = m3.Manifold.cube([L, BAR_D, BAR_H])
bar -= m3.Manifold.cube([4, 4, BAR_H + 2]).rotate([0, 0, 45]).translate([0, -2.83, -1])   # chamfer: slot-1 end

x, centres = WALL, []
for i, w in enumerate(WIDTHS):
    bar -= m3.Manifold.cube([w, BAR_D + 2, DEPTH + 1]).translate([x, -1, BAR_H - DEPTH])
    centres.append(x + w/2)
    # N dots on the front face (y=0) under the slot, stacked vertically in pairs
    for k in range(i + 1):
        dx = (k % 2 - 0.5) * 1.3 if i else 0
        dz = 1.2 + (k // 2) * 1.1
        bar -= (m3.Manifold.cylinder(DOT_DEEP + 1, DOT_R, circular_segments=16)
                .rotate([-90, 0, 0]).translate([x + w/2 + dx, -1, dz]))
    x += w + WALL

floor = BAR_H - DEPTH
assert floor >= 3.0, f"slot floor only {floor} mm"
assert 1.2 + (len(WIDTHS)-1)//2 * 1.1 + DOT_R < floor, "dots run into the slots"

name = "stl/fit-gauge_groove-3.0-to-6.5mm.stl"
m = bar.to_mesh(); tm = trimesh.Trimesh(vertices=np.asarray(m.vert_properties)[:, :3], faces=np.asarray(m.tri_verts))
tm.export(name)
print(f"{name}: {L:.1f} x {BAR_D} x {BAR_H} mm, {bar.volume()/1000:.2f} cm^3, watertight {tm.is_watertight}")
print("slots: " + "  ".join(f"{i+1}:{w:.1f}" for i, w in enumerate(WIDTHS)))
render([(bar, (0.62, 0.64, 0.68))], "renders/fit-gauge.png", elev=25, azim=-70,
       title="groove fit gauge — slots 3.0 → 6.5 mm; N dots under slot N")
