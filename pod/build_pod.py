#!/usr/bin/env python3
"""
Gauge pod for Waveshare round displays, clipped to the side of a monitor.

The look of a 2G DSM A-pillar pod -- cylindrical cups with trim rings, gauges
canted toward you, stacked on a spine -- adapted to a flat monitor edge.

Parts:  POD (cups + spine + full-height dovetail rail)
        TRIM RING per gauge (press-fit, retains the gauge, hides the PCB edge)
        CLIP x2 (fixed jaw + sliding jaw on a tongue, M3 lock from the top)

Axes: you sit at -Y looking toward +Y. The screen is the XZ plane at y=0.
The pod hangs on the monitor's RIGHT edge (+X). Z is up.

Run with ~/.venvs/cad/bin/python.
"""
import math, sys, numpy as np, manifold3d as m3, trimesh
from render import render

# ------------------------------------------------------------------ gauges
# seat_t : what rests on the shoulder (1.46 -> its glass, which overhangs the PCB; 1.28 -> the PCB)
# bore_r : rear bore radius. 1.46: snug on the Ø42.58 PCB so the stack passes through and the
#          three M2 standoffs clear. 1.28: past its BOOT/RESET buttons (~r15), inside the PCB rim.
GAUGES = [                                   # top to bottom
    dict(name="1.46 cover glass", d=44.77, seat_t=1.3, bore_r=21.29+0.25, screen=36.96, stack=12.3),
    dict(name="1.28",             d=36.50, seat_t=1.6, bore_r=16.5,       screen=32.40, stack=1.6),
    dict(name="1.28",             d=36.50, seat_t=1.6, bore_r=16.5,       screen=32.40, stack=1.6),
]
FIT       = 0.35   # radial clearance in the pocket
CANT      = 15.0   # degrees the faces turn toward you (about Z)
CUP_WALL  = 3.0
CUP_PROUD = 14.0   # cups stand this far in front of the spine
CUP_EMBED = 8.0    # and reach this far back into it
BEZEL, BEZEL_L = 1.5, 2.5
RING_L    = 3.0    # trim ring depth; ring face sits flush with the cup face
RING_PRESS= 0.10   # ring outer radius under the pocket radius
RING_OVER = 1.5    # ring covers this much beyond the active screen
GAP       = float(sys.argv[1]) if len(sys.argv) > 1 else 26.0   # rim-to-rim; 26 = straight plug, 12 = right-angle
BB_W, BB_D = 22.0, 18.0
CHAN_W, CHAN_D = 12.0, 8.0
POD_PROUD = 6.0    # cup faces stand this far in front of the screen plane when mounted

DOVE_W, DOVE_D, DOVE_ANG = 16.0, 6.0, 60.0

EDGE_MIN, EDGE_MAX = 8.0, 32.0
FRONT_LIP, JAW_T, JAW_H = 6.0, 3.0, 45.0
SPINE_X, TONGUE_L, TONGUE_H = 20.0, 18.0, 20.0   # 20 leaves 4 mm between tongue channel and socket root
M3_CLR, M3_TAP = 3.4, 2.8
SOCK_Y = BB_D/2 + (CUP_PROUD - POD_PROUD)     # dovetail socket centre along the clip

def cyl(h, r, seg=128): return m3.Manifold.cylinder(h, r, circular_segments=seg)
def boxat(x0, x1, y0, y1, z0, z1): return m3.Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0, y0, z0])
def along_y(m): return m.rotate([-90, 0, 0])
def cant(m, z): return m.rotate([0, 0, -CANT]).translate([0, 0, z])

def dovetail(h, male=True, clr=0.0):
    tip_half = DOVE_W/2 - DOVE_D/math.tan(math.radians(DOVE_ANG))
    root, tip, d = DOVE_W/2 + clr, tip_half + clr, DOVE_D + clr
    poly = [[-root, 0], [root, 0], [tip, d], [-tip, d]] if male else [[-tip, 0], [tip, 0], [root, d], [-root, d]]
    return m3.Manifold.extrude(m3.CrossSection([poly]), h).translate([0, 0, -h/2])

def r_outer(g): return g["d"]/2 + FIT + CUP_WALL + BEZEL       # bezel outer radius
R_MAX  = max(r_outer(g) for g in GAUGES)
BB_X0  = -R_MAX
BB_Y0  = 0.0
CUP_Y0 = BB_Y0 - CUP_PROUD
MARGIN = 5.0
body_h = sum(2*r_outer(g) for g in GAUGES) + GAP*(len(GAUGES)-1) + 2*MARGIN

def pod():
    solid = boxat(BB_X0, BB_X0 + BB_W, BB_Y0, BB_Y0 + BB_D, -body_h/2, body_h/2)
    cuts, cups = None, []
    z = body_h/2 - MARGIN
    for g in GAUGES:
        ro = r_outer(g); z -= ro
        r_in, r_tube = g["d"]/2 + FIT, g["d"]/2 + FIT + CUP_WALL
        cup_L  = CUP_PROUD + CUP_EMBED
        depth  = g["seat_t"] + RING_L                              # pocket: seat + ring, ring face flush
        tube   = along_y(cyl(cup_L, r_tube)).translate([0, CUP_Y0, 0])
        bezel  = along_y(cyl(BEZEL_L, ro)).translate([0, CUP_Y0, 0])
        pocket = along_y(cyl(depth + 1, r_in)).translate([0, CUP_Y0 - 1, 0])
        bore   = along_y(cyl(cup_L + BB_D + 2, g["bore_r"], 96)).translate([0, CUP_Y0 - 1, 0])
        slot   = boxat(-5.5, 5.5, CUP_Y0 - 1, BB_Y0 + BB_D + 1, -r_tube - 9, -g["bore_r"] + 2)   # USB-C drop
        solid += cant(tube + bezel, z)
        c = cant(pocket + bore + slot, z); cuts = c if cuts is None else cuts + c
        cups.append(dict(z=z, r_in=r_in, depth=depth, g=g))
        z -= ro + GAP
    cx0 = BB_X0 + (BB_W - CHAN_W)/2
    cuts += boxat(cx0, cx0 + CHAN_W, BB_Y0 + BB_D - CHAN_D, BB_Y0 + BB_D + 1, -body_h/2 + 4, body_h/2 - 4)
    body = solid - cuts
    rail = dovetail(body_h - 8, male=True).rotate([0, 0, 90]).translate([BB_X0 + 0.01, BB_Y0 + BB_D/2, 0])
    return body + rail, cups

def trim_ring(c):
    g = c["g"]
    ring = cyl(RING_L, c["r_in"] - RING_PRESS) - cyl(RING_L + 2, g["screen"]/2 + RING_OVER).translate([0, 0, -1])
    return ring

def clip():
    spine_y1 = EDGE_MAX + TONGUE_L + 3
    fixed  = boxat(0, SPINE_X, -JAW_T, spine_y1, -JAW_H/2, JAW_H/2)
    fixed += boxat(-FRONT_LIP, SPINE_X, -JAW_T, 0, -JAW_H/2, JAW_H/2)
    fixed -= boxat(2, 10, EDGE_MIN - 0.5, spine_y1 + 1, -TONGUE_H/2 - 0.3, TONGUE_H/2 + 0.3)
    fixed -= boxat(-1, 2.5, EDGE_MIN - 0.5, spine_y1 + 1, -TONGUE_H/2 - 0.3, TONGUE_H/2 + 0.3)
    fixed -= boxat(6 - M3_CLR/2, 6 + M3_CLR/2, EDGE_MIN + 8, EDGE_MAX + 8 + M3_CLR, 0, JAW_H/2 + 1)
    fixed -= dovetail(JAW_H + 2, male=False, clr=0.25).rotate([0, 0, 90]).translate([SPINE_X + 0.01, SOCK_Y, 0])
    y = EDGE_MAX
    slider  = boxat(-FRONT_LIP, 2, y, y + JAW_T, -JAW_H/2, JAW_H/2)
    slider += boxat(-FRONT_LIP, 10, y, y + JAW_T, -TONGUE_H/2, TONGUE_H/2)
    slider += boxat(2.3, 9.7, y, y + TONGUE_L, -TONGUE_H/2 + 0.3, TONGUE_H/2 - 0.3)
    slider -= cyl(TONGUE_H + 2, M3_TAP/2).translate([6, y + 8, -TONGUE_H/2 - 1])
    return fixed, slider

def slider_set_to(s, edge_t): return s.translate([0, edge_t - EDGE_MAX, 0])

def export(name, man):
    m = man.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(m.vert_properties)[:, :3], faces=np.asarray(m.tri_verts))
    tm.export(f"stl/{name}.stl"); sz = tm.bounds[1] - tm.bounds[0]
    print(f"{name:26s} {man.volume()/1000:6.1f} cm^3  genus {man.genus():2d}  watertight {str(tm.is_watertight):5s} "
          f"{sz[0]:.0f}x{sz[1]:.0f}x{sz[2]:.0f} mm")
    return tm

if __name__ == "__main__":
    tag = f"gap{GAP:.0f}"
    P, cups = pod(); F, S = clip()
    export(f"pod-{tag}", P); export("clip-fixed", F); export("clip-slider", S)
    rings = {}
    for i, c in enumerate(cups):
        key = f"trim-ring-{c['g']['name'].split()[0]}"
        if key not in rings: rings[key] = export(key, trim_ring(c))
    print(f"pod {body_h:.0f} mm tall, cups {POD_PROUD:.0f} mm proud of the screen, {GAP:.0f} mm gaps")

    # scene bits
    pucks, ring_parts = [], []
    for c in cups:
        g, z = c["g"], c["z"]
        seat_back = CUP_Y0 + c["depth"]                      # shoulder face
        glass = along_y(cyl(g["seat_t"], g["d"]/2)).translate([0, seat_back - g["seat_t"], 0])
        stack = along_y(cyl(max(g["stack"] - g["seat_t"], 1.0), g["bore_r"] - 0.3)).translate([0, seat_back, 0])
        face  = along_y(cyl(0.5, g["screen"]/2)).translate([0, seat_back - g["seat_t"] - 0.5, 0])
        ring  = along_y(trim_ring(c)).translate([0, CUP_Y0, 0])
        pucks += [(cant(glass, z), (0.05, 0.05, 0.06)), (cant(stack, z), (0.10, 0.12, 0.30)), (cant(face, z), (0.15, 0.48, 0.90))]
        ring_parts.append((cant(ring, z), (0.80, 0.80, 0.78)))

    body, fixed_c, slider_c, mon = (0.60, 0.62, 0.66), (0.42, 0.44, 0.48), (0.90, 0.42, 0.22), (0.13, 0.13, 0.15)
    render([(P, body)] + pucks + ring_parts, f"renders/01-pod-{tag}-front-quarter.png", elev=8, azim=-58,
           title=f"Pod v3 — {GAP:.0f} mm gaps ({'straight' if GAP>=24 else 'right-angle'} USB-C), trim rings, {CANT:.0f}° cant · {body_h:.0f} mm tall")
    render([(P, body)] + pucks + ring_parts, f"renders/01b-pod-{tag}-front.png", elev=0, azim=-90,
           title=f"Pod v3 — straight on, {GAP:.0f} mm gaps")
    if GAP >= 24:   # the shared parts only need rendering once
        render([(P, body)], "renders/02-pod-back-and-rail.png", elev=16, azim=128,
               title="Pod v3 from behind — wiring channel down the spine, full-height dovetail rail on the monitor side")
        render([(F, fixed_c), (S.translate([0, 12, 0]), slider_c)], "renders/03-clip-exploded.png", elev=28, azim=140,
               title=f"Clip v3, slider pulled out — edge {EDGE_MIN:.0f}–{EDGE_MAX:.0f} mm, M3 lock in the top slot. Print two.")
        cutter = boxat(-20, 40, -10, 80, -40, 0)
        render([(F - cutter, fixed_c), (slider_set_to(S, 20.0) - cutter, slider_c)], "renders/03b-clip-section.png",
               elev=88, azim=-90, title="Clip v3 sectioned at mid-height, set to 20 mm — looking down: tongue in channel, lock slot, dovetail socket at right")
        top = cups[0]["z"]; crop = boxat(-40, 40, -40, 40, top - 40, top + 40)
        render([(m ^ crop, c) for m, c in ring_parts] + [(P ^ crop, (0.60, 0.62, 0.66))] + [(m ^ crop, c) for m, c in pucks],
               "renders/05-trim-ring-detail.png", elev=22, azim=-50,
               title="Top cup — gauge seated on the shoulder, trim ring pressed in flush (retains it, hides the PCB edge)")
    shift = [SPINE_X - BB_X0 - 0.25, SOCK_Y - (BB_Y0 + BB_D/2), 0]
    for edge_t in (10.0, 20.0, 30.0):
        monitor = boxat(-90, 0, 0, edge_t, -body_h/2 - 20, body_h/2 + 20)
        clips = []
        for zc in (body_h/2 - 45, -body_h/2 + 45):
            clips += [(F.translate([0, 0, zc]), fixed_c), (slider_set_to(S, edge_t).translate([0, 0, zc]), slider_c)]
        render([(monitor, mon)] + clips + [(P.translate(shift), body)] +
               [(m.translate(shift), c) for m, c in pucks + ring_parts],
               f"renders/04-assembly-{tag}-edge-{edge_t:.0f}mm.png", elev=10, azim=-64,
               title=f"Pod on two clips, {edge_t:.0f} mm monitor edge (dark slab), {GAP:.0f} mm gaps — you sit bottom-left")
