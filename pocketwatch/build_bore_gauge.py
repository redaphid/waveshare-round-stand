#!/usr/bin/env python3
"""
Bore fit gauge for the pocketwatch: the front of the case only (bezel lip, badge
bore, USB-C tab slot), as four rings with the bore at RAD_CLR 0.25 / 0.55 /
0.85 / 1.15 per side.

Pocketwatch v2 printed with the badge stuck on the plate step, ~10 mm behind the
bezel instead of on the lip. Either the bore printed too small (calipers read
35.31, Waveshare's drawing says 36.5) or the tab missed its slot. Drop the badge
in from the back, screen first, tab in the slot: the tightest ring that lets the
glass sit flat on the lip is the RAD_CLR to use.

Ring N has N dots on its back rim at 6 o'clock. Ring 1 is today's case.
Run with ~/.venvs/cad/bin/python from the repo root.
"""
import sys
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3, trimesh
from build_pocketwatch import Badge, Case, disc_and_tab, chamfered, prism, circle, union, SEG
from render import render

CLRS = [0.25, 0.55, 0.85, 1.15]
WALL, PITCH, DOT_R, DOT_DEEP = 2.4, 48.0, 0.5, 0.6

b, c = Badge(), Case()
z1 = b.pcb_back_z + 0.6                       # deep enough to hold the disc; headers stick out the back
rings = []
for i, clr in enumerate(CLRS):
    bore = disc_and_tab(b).offset(clr, m3.JoinType.Miter, 4.0)
    ring = chamfered([circle(b.r + clr + WALL)], -c.LIP_T, z1, c.CHAMFER, 0.0)
    ring += prism(bore.offset(WALL, m3.JoinType.Miter, 4.0), -c.LIP_T, z1)     # wall around the tab slot too
    ring -= prism(bore, 0.0, z1 + 1)
    ring -= m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG) \
        .translate([0, 0, -c.LIP_T - 0.01])
    r_dot = b.r + clr + WALL/2
    for k in range(i + 1):
        a = np.radians(-90 + (k - i/2) * 9)
        ring -= m3.Manifold.cylinder(DOT_DEEP + 1, DOT_R, DOT_R, 16) \
            .translate([r_dot*np.cos(a), r_dot*np.sin(a), z1 - DOT_DEEP])
    # the badge must drop onto the lip: disc + tab, shrunk by nothing, clear of the ring at rest
    badge = prism(disc_and_tab(b), 0.0, b.pcb_back_z)
    assert (badge ^ ring).volume() < 1e-3, f"ring {i+1}: badge overlaps the ring"
    assert (prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0) ^ ring).volume() > 0.5, \
        f"ring {i+1}: lip does not retain the glass"
    print(f"  ring {i+1}: RAD_CLR {clr:.2f}  bore Ø{2*(b.r + clr):.2f}  tab slot {b.tab_w_root + 2*clr:.2f} wide")
    rings.append(ring.translate([i*PITCH, 0, 0]))

gauge = union(rings).translate([0, 0, c.LIP_T])       # bezel face down, like the case
name = "stl/pocketwatch/Pocketwatch - bore fit gauge.stl"
m = gauge.to_mesh()
tm = trimesh.Trimesh(vertices=np.asarray(m.vert_properties)[:, :3], faces=np.asarray(m.tri_verts))
tm.export(name)
assert tm.is_watertight, f"{name} not watertight"
ext = tm.extents
print(f"{name}: {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, {gauge.volume()/1000:.2f} cm^3, watertight")
if "--no-render" not in sys.argv:
    render([(gauge.refine_to_length(1.0), (0.82, 0.66, 0.32))], "pocketwatch/renders/bore-gauge.png", elev=50, azim=-80,
           title="Bore fit gauge, as printed: rings 1-4 (N dots), bore Ø35.8 / 36.4 / 37.0 / 37.6")
