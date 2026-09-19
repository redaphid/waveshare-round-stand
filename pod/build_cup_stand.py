#!/usr/bin/env python3
"""
Cup stand: ONE 1.28 pod cup on a desk base, leaning back like the stands.

A test of the pod's cup logic at ~1/4 of the pod's plastic: the cup is
build_pod.cup() verbatim -- same pocket, shoulder, bore, bezel and plug-drop
slot -- so if the badge seats and the trim ring presses in here, it will in
the pod. It is also a usable desk stand afterwards.

Exported FACE-UP (cup axis vertical) so the pocket and shoulder print as true
circles with no support. Turn it over onto the flat base to use it.

Run with ~/.venvs/cad/bin/python.   Args: [gauge name prefix, default 1.28]
"""
import sys, math, numpy as np, manifold3d as m3
import build_pod as bp
from build_pod import boxat, export, along_y, cyl
from render import render

LEAN     = 20.0    # badge leans back this far from vertical, same as the stands
BASE_W   = 30.0    # base width across the badge (X)
BASE_CLR = 3.0     # base floor sits this far below the cup's lowest point

key = sys.argv[1] if len(sys.argv) > 1 else "1.28"
g = next(g for g in bp.GAUGES if g["name"].startswith(key))
solid, cuts, r_in, depth = bp.cup(g)
r_tube = g["d"]/2 + bp.FIT + bp.CUP_WALL
y_back = bp.CUP_Y0 + bp.CUP_PROUD + bp.CUP_EMBED

# base block in the cup's frame: under the cup, full cup length, reaching well below the desk line
block = boxat(-BASE_W/2, BASE_W/2, bp.CUP_Y0, y_back, -r_tube - 40, 0)

def bbox(m):
    b = np.array(m.bounding_box()); return b[:3], b[3:]

def pt(m_fn, p):
    """Where point p lands under transform m_fn (a tiny cube's centre)."""
    lo, hi = bbox(m_fn(m3.Manifold.cube([0.02]*3, center=True).translate(list(p))))
    return (lo + hi) / 2

# Tilt the face up by LEAN: a point out in front of the face (-Y) must rise. Found by probing.
LEAN_RX = next(a for a in (LEAN, -LEAN) if pt(lambda m: m.rotate([a, 0, 0]), (0, -10, 0))[2] > 0)
def lean(m): return m.rotate([LEAN_RX, 0, 0])

cup_d, block_d = lean(solid), lean(block)
z_low = np.asarray(cup_d.to_mesh().vert_properties)[:, 2].min()
z_desk = z_low - BASE_CLR
desk_half = boxat(-200, 200, -200, 200, z_desk, 200)
stand = ((cup_d + (block_d ^ desk_half)) - lean(cuts)).translate([0, 0, -z_desk])

# ---- physical checks ------------------------------------------------------
v = np.asarray(stand.to_mesh().vert_properties)[:, :3]
assert abs(v[:, 2].min()) < 1e-6
foot = v[v[:, 2] < 0.05]
ymin, ymax = foot[:, 1].min(), foot[:, 1].max()
# badge + cup dominate the mass; their centre is the pocket centre. It must sit over the foot.
com_y = pt(lambda m: lean(m).translate([0, 0, -z_desk]), (0, bp.CUP_Y0 + depth/2, 0))[1]
assert ymin + 2 < com_y < ymax - 2, f"tips over: COM y={com_y:.1f}, foot {ymin:.1f}..{ymax:.1f}"
assert r_in - g["bore_r"] > 1.0, "shoulder too narrow to seat on"

# ---- export face-up -------------------------------------------------------
# undo the lean, then turn the face (-Y) to +Z; verify the pocket opening ends up on top
unl = stand.translate([0, 0, z_desk])
for a in (LEAN, -LEAN):
    cand = unl.rotate([a, 0, 0])
    if abs(bbox(cand)[0][1] - bp.CUP_Y0) < 0.05: unl = cand; break
else: raise SystemExit("could not undo the lean")
for a in (90, -90):
    cand = unl.rotate([a, 0, 0])
    probe = along_y(cyl(0.1, 0.1)).translate([0, bp.CUP_Y0, 0]).rotate([a, 0, 0])   # a point on the face
    if bbox(probe)[0][2] >= bbox(cand)[1][2] - 0.5: printable = cand; break
else: raise SystemExit("could not turn the face up")
printable = printable.translate([0, 0, -bbox(printable)[0][2]])

name = f"{bp.SIZE[key]}/Pod cup test"
export(name, printable)
print(f"  pocket Ø{2*r_in:.2f} x {depth:.1f} deep (seat {g['seat_t']} + ring {bp.RING_L}); shoulder "
      f"{r_in - g['bore_r']:.2f} wide; bore Ø{2*g['bore_r']:.1f}; leans {LEAN:.0f}°; foot {ymax - ymin:.1f} mm deep; "
      f"trim ring: stl/{bp.ring_name(g)}.stl")

# ---- render in use: badge seated, ring pressed in --------------------------
seat_back = bp.CUP_Y0 + depth
board  = along_y(cyl(g["seat_t"], g["d"]/2)).translate([0, seat_back - g["seat_t"], 0])
screen = along_y(cyl(0.5, g["screen"]/2)).translate([0, seat_back - g["seat_t"] - 0.5, 0])
ring   = along_y(bp.trim_ring(dict(r_in=r_in, g=g))).translate([0, bp.CUP_Y0, 0])
place  = lambda m: lean(m).translate([0, 0, -z_desk])
grey, dark, blue, ringc = (0.62, 0.64, 0.68), (0.05, 0.05, 0.06), (0.15, 0.48, 0.90), (0.80, 0.80, 0.78)
render([(stand, grey), (place(board), dark), (place(screen), blue), (place(ring), ringc)],
       f"renders/cup-stand-{key}-in-use.png", elev=14, azim=-60,
       title=f"{key} pod cup on a desk base — badge seated, trim ring flush. The pod's cup, verbatim.")
render([(stand, grey)], f"renders/cup-stand-{key}-empty-front.png", elev=20, azim=-90,
       title="Empty cup, straight on: shoulder ring, tab notch at the bottom (into the plug slot), header reliefs left and right")
render([(printable, grey)], f"renders/cup-stand-{key}-as-printed.png", elev=30, azim=-60,
       title="As exported: face up, shoulder and pocket print as true circles, no supports")
