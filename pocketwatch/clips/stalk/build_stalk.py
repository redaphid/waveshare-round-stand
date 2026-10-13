#!/usr/bin/env python3
"""
Stalk gauge: the USB-only pocketwatch fused into a 52 mm aftermarket gauge cup
that sits on a short, chunky stalk clamped to the SIDE bezel of a monitor.

  cup     the USB-only case (bore, lip, crown boss, plug slot) grown into a
          Ø52.4 cup -- the standard 2-1/16" gauge size -- with a 6 mm deep rim and
          a flat ear on each side. Ears are horizontal plates when mounted.
  ring    chrome trim ring + sun visor, slips onto the cup's chamfered rim.
  plate   the USB-only back plate with the BOOT access hole (unchanged design).
  clip    C-clamp: fixed 6 mm lip on the bezel front, spine on the monitor's side,
          rear leg with an M4 thumbscrew pushing a swivel pad onto the monitor back.
          A round pillar on the spine is the stalk; its top is a 24-tooth face.
  pad     swivel pad on the thumbscrew tip.
  knob x2 ribbed knob on an M4 hex-head bolt (joint) and on the M4 thumbscrew.

The pivot is a toothed face (a Hirth-style 24 x 15 deg detent) clamped by an M4 bolt,
not a ball and not a plain friction hinge: the teeth hold the aim positively, the
bolt only has to keep them meshed, and gravity acts ACROSS the vertical axis, so the
cup's weight never tries to turn the joint. Clipped to the bezel the gauge inherits
the monitor's tilt (already aimed at the eyes), so the one axis it needs is yaw:
turning the face in toward the user from the side of the screen.

World frame: the screen is the plane y=0, the user sits at -y, the monitor body is
y in [0, T], its right side edge is x=0 (monitor at x<0), z up. Mirror the clip in
the slicer for a left edge; the cup has an ear each side, so it serves both.

Run from the repo root with ~/.venvs/cad/bin/python. --no-render for checks only.
"""
import sys, math, os
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pod")
import numpy as np, manifold3d as m3, trimesh
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)
from build_pocketwatch_usb import BACK_CHAMFER, SHELL_LEN, MIN_PLUG_ENGAGE, BOOT_HOLE_D, PIN_D, boot_hole_plate

STL = "stl/pocketwatch/clips/stalk/"
OUT = "pocketwatch/clips/stalk/renders/"

# ---- cup (badge frame: origin = glass centre, +y = USB tab, +z = backward) ----
R_C = 26.2          # cup outer: Ø52.4, the 2-1/16" aftermarket gauge size; also just covers the crown boss corners
CUP_WALL = 2.4      # cup wall in front of the case
DEPTH = 6.0         # rim stands this far in front of the bezel lip's face
CUP_CHF = 1.6       # 45 deg front chamfer; the trim ring's cone sits on it
EAR_T = 6.0         # ear plate thickness (world vertical)
EAR_Y = 3.0         # ear's toothed face at badge y = +3 (world: 3 mm below the cup centre)
Z_AX = 2.0          # joint axis at this badge depth (about the cup's centre of mass)
R_D = 8.0           # pillar / ear disc radius around the axis
R_KNOB = 10.0       # knob radius
L_EAR = R_C + R_KNOB + 1.3       # cup centre to joint axis: the knob clears the cup wall
R_T = R_D - 0.6 - 0.8 - 0.3      # toothed face radius: inside the pillar-top boss's chamfer
# ---- trim ring + visor ----
RING_L = 2.5        # ring stands this far in front of the rim
RING_OVER = 0.8     # ring outer past the cup wall
SPIG, SPIG_W, SPIG_FIT = 3.0, 1.2, 0.05     # spigot into the cup bore; radial clearance (slip + a dot of CA)
VIS = 12.0          # visor reaches this far past the ring at 12 o'clock, zero at 3 and 9
VIS_W = 2.0
# ---- joint ----
TEETH = 24
TOOTH_A = math.pi / TEETH        # tooth height / radius for 45 deg flanks
M4_CLR, M4_D = 4.4, 4.0
NUT_AF, NUT_T = 7.3, 3.5         # M4 nut 7.0 AF x 3.2, with clearance
HEAD_AF, HEAD_T = 7.2, 2.8       # M4 hex-head bolt (DIN 933)
JOINT_BOLT = 20.0                # M4 x 20
NUT_Z = 9.0                      # joint nut trap: this far below the pillar top
# ---- clip ----
EDGE_MIN, EDGE_MAX = 8.0, 32.0
LIP = 6.0           # front lip reaches this far over the bezel (same as the pod clip)
JAW_T = 4.0         # front jaw thickness (y)
X_SP = 6.0          # spine thickness (x), outside the monitor's side
H = 40.0            # pillar top (toothed face) height; the cup centre is EAR_Y above it
H_BODY = H - 2.0    # the rest of the clip stops lower, so the ear only lands on the teeth
CH = 0.8
PAD_R, PAD_T, PAD_HOLE = 7.5, 5.0, 3.5      # swivel pad; the screw tip sits in a blind hole
X_S = -9.0          # thumbscrew axis x (behind the monitor)
Z_S = H_BODY / 2
RL_T = 10.0         # rear leg thickness (y)
Y_RL0 = EDGE_MAX + PAD_T + 1.0
Y_RL1 = Y_RL0 + RL_T
REAR_IN = -X_S + PAD_R + 1.0                 # rear leg reaches this far behind the monitor
CLAMP_SCREW = 40.0                            # M4 x 40
X_A = 11.0                                    # joint axis: the ear's far end (r <= 9.5) stays 1.5 off the monitor's side
RIM_PROUD = 8.0                               # trim ring face this far in front of the screen at aim 0
Z_RIM = -1.2 - DEPTH                          # Case.LIP_T = 1.2
Y_A = -RIM_PROUD + (RING_L - Z_RIM) + Z_AX    # world y of the axis
AIMS = (-15, 0, 15, 30, 45, 60)               # detent positions checked (deg, + turns the face toward the user)
# ---- physics (conservative) ----
G = 9.81e-3                       # N per gram
M_BADGE, M_PLUG = 20.0, 8.0       # g
RHO = 1.27e-3                     # PETG g/mm^3, counted SOLID (heavier than any real print)
CABLE_PULL = 1.0                  # N, any direction
MU = 0.30                         # PETG on PETG / on monitor plastic, dry
FINGER_T = 0.15                   # N m on a 20 mm knob: a gentle finger twist (people manage 0.3-0.5)
K_NUT = 0.20                      # torque coefficient, dry steel thread
CREEP = 0.30                      # PETG under a bolt relaxes; keep only 30 % of the preload
TILT_MAX = 20.0                   # monitor tilted back up to this (deg): tilts the yaw axis
INTERLAYER = 10.0                 # MPa, PETG layer-to-layer tensile, pessimistic


def teeth(R, z0, z1, ri=M4_CLR/2 + 0.6):
    """Solid under a 24-tooth face: z = z1 + r*tri(theta), 45 deg flanks, peaks at k*15 deg, for r in [ri, R];
    a flat land at z1 inside ri, where the bolt hole goes (a fan to the centre leaves slivers the hole pinches)."""
    n = 2 * TEETH
    a = np.arange(n) * 2 * np.pi / n
    t = np.where(np.arange(n) % 2 == 0, TOOTH_A, 0.0)
    ring = lambda r, z: np.c_[r*np.cos(a), r*np.sin(a), z]
    V = np.vstack([ring(ri, z1 + ri*t), ring(R, z1 + R*t), ring(R, np.full(n, z0)), ring(ri, np.full(n, z0))])
    T = []
    for i in range(n):
        j = (i + 1) % n
        it, ot, ob, ib = i, n + i, 2*n + i, 3*n + i
        jt, jo, jb, jib = j, n + j, 2*n + j, 3*n + j
        T += [(it, ot, jo), (it, jo, jt), (ob, jb, jo), (ob, jo, ot), (ib, jb, ob), (ib, jib, jb), (ib, it, jt), (ib, jt, jib)]
    ann = m3.Manifold(m3.Mesh(vert_properties=np.asarray(V, np.float32), tri_verts=np.asarray(T, np.uint32)))
    return ann + m3.Manifold.cylinder(z1 - z0 + 0.5, ri + 0.4, ri + 0.4, 96).translate([0, 0, z0 - 0.5])


def place(m, aim=0.0):
    """Badge frame -> world, cup on the clip, face turned `aim` degrees toward the user (-x)."""
    return m.rotate([-90, 0, 0]).translate([L_EAR, -Z_AX, H + EAR_Y]).rotate([0, 0, -aim]).translate([X_A, Y_A, 0])


def unplace(m):
    return m.translate([-X_A, -Y_A, 0]).translate([-L_EAR, Z_AX, -(H + EAR_Y)]).rotate([90, 0, 0])


def joint_teeth():
    """The toothed face in world, at the axis: the clip is below it, the ear above it."""
    return teeth(R_T, H - 1.5, H).translate([X_A, Y_A, 0])


def build_cup(b: Badge, c: Case, side=-1):
    """The USB-only build() from build_pocketwatch_usb.py, with the outline grown into the cup.
    side -1: ear on badge -x, for a monitor's RIGHT edge. +1: ear on +x, for a LEFT edge."""
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    STEP = 1.2
    R_REAR = R_BORE + STEP
    FLOOR = b.hdr_top_z + c.FLOAT
    Z_CASE = FLOOR + c.PLATE_T
    bore_xy = feats[0].grown()
    pocket = circle(R_REAR) + bore_xy
    boss = (bore_xy.offset(c.CASE_WALL, Round) ^ rect(-40, 40, 10, 40)).hull()
    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())

    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4

    # ears: flat plates at badge y in [EAR_Y - EAR_T, EAR_Y], square bottom on the bed, round top
    def ear(sx):
        # round end around the axis; below it a 45 deg chamfer down to the bed, not a square corner that
        # would swing out toward the monitor's side as the cup turns
        u45 = R_D / math.sqrt(2) - (Z_AX - R_D / math.sqrt(2) - Z_RIM)
        prof = (m3.CrossSection.circle(R_D, SEG).translate([-L_EAR, Z_AX]) +
                rect(-L_EAR - u45, -R_C + 1.0, Z_RIM, Z_AX)).hull()
        e = m3.Manifold.extrude(prof, EAR_T).rotate([90, 0, 0]).translate([0, EAR_Y, 0])
        return e if sx < 0 else e.mirror([1, 0, 0])
    tooth_b = unplace(joint_teeth())                       # toothed face of the -x ear, in badge frame
    bolt_b = m3.Manifold.cylinder(30, M4_CLR/2, M4_CLR/2, 48).rotate([90, 0, 0]).translate([-L_EAR, 15, Z_AX])

    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    cup = chamfered([circle(R_C)], Z_RIM, Z_CASE, CUP_CHF, BACK_CHAMFER) + chamfered([boss], -c.LIP_T, Z_CASE, c.CHAMFER, BACK_CHAMFER)
    cup += ear(side)
    cup -= (tooth_b + bolt_b) if side < 0 else (tooth_b + bolt_b).mirror([1, 0, 0])
    # the deep rim is a 45 deg cone down to the lip: printed face-down, a flat dial floor would be a
    # 7 mm overhang; the cone prints itself and reads as a sloped gauge bezel
    r_cb = R_C - CUP_WALL
    cone = m3.CrossSection([[(0, Z_RIM - 1), (r_cb + 1, Z_RIM - 1), (r_cb, Z_RIM), (r_cb - DEPTH, -c.LIP_T), (0, -c.LIP_T)]])
    cup -= m3.Manifold.revolve(cone, SEG).rotate([0, 0, 180/SEG])
    cup -= prism(bore_xy, 0.0, Z_CASE + 1)
    cup -= prism(circle(R_REAR), FLOOR, Z_CASE + 1)
    cup -= window.translate([0, 0, -c.LIP_T - 0.01])
    cup -= groove_p
    cup -= all_keep
    # plug body notch: the cup is bigger than the crown boss, so cut back to the boss face where the
    # 12 x 8 plug body lands. That keeps exactly the boss's 3.0 mm of wall in front of the port.
    boss_face = bbox(prism(boss, 0, 1))[1, 1]
    cup -= prism(rect(-PLUG_W/2 - 0.4, PLUG_W/2 + 0.4, boss_face, R_C + 1),
                 b.port_z - PLUG_T/2 - 0.4, Z_CASE + 1)

    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, m3.JoinType.Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    plate = prism(pocket.offset(-c.FIT_CLR - 0.03, Round), FLOOR, Z_CASE)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead_p
    plate += guides
    plate -= all_keep
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_cyl = m3.Manifold.cylinder(FLOOR + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([sw[c.BUTTON], b.sw_y, tip_z])
    plate += post_cyl - union(k for n, k in keep.items() if not n.startswith(c.BUTTON))

    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_C, FLOOR=FLOOR, Z_CASE=Z_CASE, bh_p=bh_p,
               groove_r_p=groove_r_p, hdrs=hdrs, sw=sw, post_cyl=post_cyl, boss_face=boss_face)
    return feats, cup, plate, geo


PLUG_W, PLUG_T, PLUG_L, CABLE_D = 12.0, 8.0, 22.0, 4.0     # straight USB-C plug body outside the case, then the cable


def plug_and_cable(b, geo, cable_len=70.0):
    """Badge frame. Body butts on the boss face; the cable leaves straight along +y (world: down)."""
    y0 = geo["boss_face"]
    body = prism(rect(-PLUG_W/2, PLUG_W/2, y0 + 0.02, y0 + PLUG_L), b.port_z - PLUG_T/2, b.port_z + PLUG_T/2)
    cable = m3.Manifold.cylinder(cable_len, CABLE_D/2, CABLE_D/2, 32).rotate([-90, 0, 0]).translate([0, y0 + PLUG_L, b.port_z])
    shell = prism(rect(-4.2, 4.2, b.tip_y - SHELL_LEN + 0.0, y0 + 0.02), b.port_z - 1.3, b.port_z + 1.3)
    return body, cable, shell


def trim_ring():
    """Badge frame. Spigot in the cup bore, cone on the cup's front chamfer, visor over 12 o'clock
    (world top = badge -y). Notched behind the rim where the ears are, which also keys the visor."""
    r_cb = R_C - CUP_WALL
    R_R = R_C + RING_OVER
    zf = Z_RIM - RING_L
    # spigot: a conical sleeve on the cup's 45 deg cone, SPIG_W thick normal to it
    rb = r_cb - SPIG - SPIG_FIT * math.sqrt(2)                       # sleeve outer at its back end
    prof = m3.CrossSection([[(rb - SPIG_W * math.sqrt(2), Z_RIM + SPIG), (rb, Z_RIM + SPIG),
                             (r_cb - SPIG_FIT * math.sqrt(2), Z_RIM), (R_C - CUP_CHF, Z_RIM), (R_C, Z_RIM + CUP_CHF),
                             (R_R, Z_RIM + CUP_CHF - RING_OVER), (R_R, zf), (r_cb - 1.0, zf)][::-1]])
    ring = m3.Manifold.revolve(prof, SEG)
    rv = R_R - 0.3                                                   # visor stands 0.3 inside the ring: reads as a separate lip
    tube = m3.Manifold.cylinder(VIS + 1, rv, rv, SEG) - m3.Manifold.cylinder(VIS + 3, rv - VIS_W, rv - VIS_W, SEG).translate([0, 0, -1])
    tube = tube.translate([0, 0, zf - VIS - 0.5])
    n = np.array([0.0, -VIS / rv, 1.0])
    visor = tube.trim_by_plane(list(n / np.linalg.norm(n)), zf / np.linalg.norm(n)).trim_by_plane([0, 0, -1], -(zf + 0.01))
    ring += visor
    for sx in (-1, 1):
        x0, x1 = sorted((sx*(R_C - 1.0 - 0.4), sx*(R_R + 2)))
        ring -= m3.Manifold.cube([x1 - x0, EAR_T + 0.8, 10]).translate([x0, EAR_Y - EAR_T - 0.4, Z_RIM - 0.01])
    return ring


# ---- clip, pad, knob (world frame) --------------------------------------------
def hexagon(af):
    """Flats normal to x."""
    return m3.CrossSection.circle(af / math.sqrt(3), 6).rotate(30)


def build_clip():
    pieces = [rect(-LIP, X_SP, -JAW_T, 0), rect(0, X_SP, -JAW_T, Y_RL1), rect(-REAR_IN, X_SP, Y_RL0, Y_RL1)]
    clip = chamfered(pieces, 0, H_BODY, CH, CH)
    pillar = (m3.CrossSection.circle(R_D, SEG).translate([X_A, Y_A]) + rect(0, X_SP, Y_A - R_D, Y_A + R_D)).hull()
    clip += chamfered([pillar], 0, H_BODY, CH, 0.0) + chamfered([m3.CrossSection.circle(R_D - 0.6, SEG).translate([X_A, Y_A])], H_BODY - 0.5, H, 0.0, CH)
    clip += joint_teeth()
    # joint: bolt hole down the pillar, M4 nut in a trap that opens to the back (+y)
    clip -= m3.Manifold.cylinder(NUT_Z + 9, M4_CLR/2, M4_CLR/2, 48).translate([X_A, Y_A, H - NUT_Z - 7])
    zn = H - NUT_Z
    clip -= prism(hexagon(NUT_AF) + rect(-NUT_AF/2, NUT_AF/2, 0, R_D + 5), zn, zn + NUT_T).translate([X_A, Y_A, 0])
    # thumbscrew: hole along y through the rear leg, nut dropped into a slot from the top
    clip -= m3.Manifold.cylinder(RL_T + 2, M4_CLR/2, M4_CLR/2, 48).rotate([-90, 0, 0]).translate([X_S, Y_RL0 - 1, Z_S])
    yn = Y_RL0 + (RL_T - NUT_T)/2
    clip -= m3.Manifold.cube([NUT_AF, NUT_T, H]).translate([X_S - NUT_AF/2, yn, Z_S - NUT_AF/math.sqrt(3) - 0.1])
    return clip


def build_pad():
    """World, for an edge of thickness T = 0 (translate by T). Front face on the monitor back."""
    p = chamfered([circle(PAD_R)], 0, PAD_T, 0.0, CH) - m3.Manifold.cylinder(PAD_HOLE + 1, 2.3, 2.3, 48).translate([0, 0, PAD_T - PAD_HOLE])
    return p.rotate([-90, 0, 0]).translate([X_S, 0, Z_S])


def build_knob():
    """Knob frame: bottom face (the head pocket) at z=0, top at z=10. Ribbed: 15 scallops."""
    k = chamfered([circle(R_KNOB)], 0, 10, 0.6, 1.2)
    k -= union(m3.Manifold.cylinder(12, 1.7, 1.7, 32).translate([R_KNOB + 0.6, 0, -1]).rotate([0, 0, i*24 + 0.37]) for i in range(15))   # off-phase: no shared vertices
    k -= prism(hexagon(HEAD_AF), -1, HEAD_T - 0.3)          # head stands 0.3 proud: it, not the knob, bears
    return k


def bolt(length, head=True):
    """Hex-head bolt, frame: under-head face at z=0, shank toward -z."""
    s = m3.Manifold.cylinder(length, M4_D/2, M4_D/2, 32).translate([0, 0, -length])
    return s + prism(hexagon(7.0), 0, HEAD_T) if head else s


def clip_hardware(T):
    """Pad, thumbscrew + knob, joint bolt + knob, nuts. World. Returns dict name -> solid."""
    tip = T + PAD_T - PAD_HOLE                  # screw tip sits at the bottom of the pad's blind hole
    head = tip + CLAMP_SCREW                    # under-head face
    to_y = lambda m: m.rotate([-90, 0, 0])      # bolt frame +z (head side) -> +y, shank toward the monitor
    knob = build_knob()
    hw = {
        "pad": build_pad().translate([0, T, 0]),
        "thumbscrew": to_y(bolt(CLAMP_SCREW)).translate([X_S, head, Z_S]),
        "clamp knob": to_y(knob.translate([0, 0, 0.3])).translate([X_S, head, Z_S]),
        "clamp nut": prism(hexagon(7.0), 0, 3.2).rotate([-90, 0, 0]).translate([X_S, Y_RL0 + (RL_T - 3.2)/2, Z_S]),
        "joint bolt": bolt(JOINT_BOLT).translate([X_A, Y_A, H + EAR_T]),
        "joint knob": knob.translate([X_A, Y_A, H + EAR_T + 0.3]),
        "joint nut": prism(hexagon(7.0), 0, 3.2).translate([X_A, Y_A, H - NUT_Z + 0.15]),
    }
    return hw, tip, head


# ---- checks ---------------------------------------------------------------------
def monitor(T, screen=True):
    """Monitor near its right edge: body, and the screen glass (x <= -LIP) as a thin layer on its face."""
    body = m3.Manifold.cube([140, T, 220]).translate([-140, 0, -90])
    glass = m3.Manifold.cube([140 - LIP, 0.4, 200]).translate([-140, -0.4, -80])
    return body, glass


def pocketwatch_checks(b, c, feats, cup, plate, geo):
    """Sections 1-4 of build_pocketwatch_usb.run_checks, against the cup."""
    static = {"cup": cup, "plate": plate}
    target = f"{c.BUTTON} actuator"
    print("\n1. At rest: no badge feature overlaps the cup or plate (min gap, mm)")
    for f in feats:
        s = f.solid()
        vol = sum((s ^ m).volume() for m in static.values())
        gaps = {k: s.min_gap(m, 3.0) for k, m in static.items()}
        k = min(gaps, key=gaps.get)
        check(vol < 1e-3, f"{f.name:26s} overlap {vol:.4f} mm^3", f"gap {gaps[k]:.2f} to {k}")
    print("\n2. Axial room before each feature touches anything (the switch must be first), and pressed")
    def overlaps(f, dz): return sum((f.solid(dz) ^ m).volume() for m in static.values()) > 1e-4
    for f in feats:
        lo, hi = 0.0, 2.0
        if not overlaps(f, hi):
            r = math.inf
        else:
            while hi - lo > 0.005:
                mid = (lo + hi)/2
                lo, hi = (mid, hi) if not overlaps(f, mid) else (lo, mid)
            r = lo
        if f.name == target:
            check(abs(r - c.REST_CLR) < 0.02, f"{f.name:26s} meets the post after REST_CLR", f"{r:.2f}")
        else:
            check(r > c.STROKE + 0.1, f"{f.name:26s} room > stroke {c.STROKE:.2f} + 0.1",
                  f"{r:.2f}" if r < math.inf else "nothing behind it")
    print(f"\n3. Header guides grip each header in x (>= {c.MIN_ENGAGE} deep)")
    i, o = c.HDR_CLR, c.HDR_CLR + c.GUIDE_WALL
    for h in geo["hdrs"]:
        x0, y0, x1, y1 = h.outline.bounds()
        for wn, w in {"-x wall": rect(x0 - o, x0 - i, y0, y1), "+x wall": rect(x1 + i, x1 + o, y0, y1)}.items():
            g = plate ^ prism(w, -5, geo["FLOOR"])
            eng = b.hdr_top_z - bbox(g)[0, 2] if not g.is_empty() else 0.0
            span = bbox(g)[1, 1] - bbox(g)[0, 1] if not g.is_empty() else 0.0
            check(eng >= c.MIN_ENGAGE and span >= 5.0, f"{h.name} {wn}", f"engages {eng:.2f} deep over {span:.1f} of y")
    print("\n4. Bezel lip, snap, walls")
    probe = m3.Manifold.cylinder(c.LIP_T + 2, (b.active_d + 1)/2, (b.active_d + 1)/2, SEG).translate([0, 0, -c.LIP_T - 1])
    check((probe ^ cup).volume() < 1e-4, f"window clears active display {b.active_d:.2f} + 1", f"window {2*(b.r - c.LIP_OVERLAP):.2f}")
    ring = prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0)
    check((ring ^ cup).volume() > 0.5, "lip overlaps the glass edge (retains it)", f"{c.LIP_OVERLAP:.2f} per side")
    check((cup ^ plate).volume() < 1e-3, "cup and plate do not overlap", f"{(cup ^ plate).volume():.4f} mm^3")
    s = (cup ^ plate.translate([0, 0, geo["bh_p"]])).volume()
    check(s > 1.0, "plate pulled back one bead height interferes (it snaps)", f"{s:.1f} mm^3")
    walls = {"cup wall behind the plate groove": R_C - geo["groove_r_p"], "bezel lip": c.LIP_T,
             "crown boss at the back rim": c.CASE_WALL - BACK_CHAMFER, "cup wall in front of the case": CUP_WALL,
             "step under the plate": geo["R_REAR"] - geo["R_BORE"], "trim ring spigot": SPIG_W, "visor": VIS_W,
             "ear plate": EAR_T}
    for nm, t in walls.items():
        check(t >= c.MIN_WALL - 1e-9, f"{nm} >= {c.MIN_WALL}", f"{t:.2f}")


def stalk_checks(b, c, feats, cup, cup_l, plate, plate_h, ring, clip, geo):
    P = {}
    print("\n5. USB-C plug path (badge frame, then mounted at every aim)")
    body, cable, shell = plug_and_cable(b, geo)
    wall = geo["boss_face"] - b.tip_y
    check(abs(wall - 2.97) < 0.05, "wall in front of the port is the USB-only case's, not thickened", f"{wall:.2f} mm")
    check(SHELL_LEN - wall >= MIN_PLUG_ENGAGE, f"plug shell engages the port >= {MIN_PLUG_ENGAGE}", f"{SHELL_LEN - wall:.2f} of {SHELL_LEN}")
    for nm, m in (("plug body", body), ("cable", cable), ("plug shell", shell)):
        v = sum((m ^ p).volume() for p in (cup, ring, plate_h))
        check(v < 1e-3, f"{nm} clear of cup, ring and plate", f"{v:.4f} mm^3")
    x, y = geo["sw"][c.BUTTON], b.sw_y
    top = b.pcb_back_z + b.sw_cap_h
    stylus = m3.Manifold.cylinder(geo["Z_CASE"] + 45 - (top - c.SW_TRAVEL), PIN_D/2, PIN_D/2, 32).translate([x, y, top - c.SW_TRAVEL])
    v = sum((stylus ^ p).volume() for p in (cup, ring, plate_h))
    check(v < 1e-3, f"Ø{PIN_D:g} stylus 45 mm straight in from behind reaches BOOT, clear of cup/ring/plate", f"{v:.4f} mm^3")
    print("\n6. Plate comes out the back (badge in from the back) with the cup on the clip")
    dz_free = geo["FLOOR"] - (min(bbox(plate)[0, 2], 99)) + 0.1
    worst = max((plate_h.translate([0, 0, dz]) ^ (cup + ring)).volume() for dz in np.linspace(geo["bh_p"] + 2.2, 40, 12))
    check(worst < 1e-3, "plate pulled straight back 3-40 mm meets nothing (snap bead released)", f"{worst:.4f} mm^3")

    print(f"\n7. Clip grip range {EDGE_MIN:g}-{EDGE_MAX:g} mm")
    for T in (EDGE_MIN, 20.0, EDGE_MAX):
        hw, tip, head = clip_hardware(T)
        mon, glass = monitor(T)
        fixed = clip + hw["pad"]
        v = (fixed ^ mon).volume()
        check(v < 1e-2, f"T={T:4.1f}: lip on the front, pad on the back, nothing inside the monitor", f"{v:.4f} mm^3")
        check(head >= Y_RL1 + 0.5, f"T={T:4.1f}: M4x{CLAMP_SCREW:g} thumbscrew reaches, head behind the leg", f"head {head - Y_RL1:.1f} mm off the leg")
        check(tip < Y_RL0 - 1 and T + PAD_T <= Y_RL0 - 0.5, f"T={T:4.1f}: thread through the whole nut, pad clear of the leg",
              f"tip {Y_RL0 - tip:.1f} in front of the leg, pad gap {Y_RL0 - T - PAD_T:.1f}")
        P[T] = (hw, mon, glass)
    check(LIP <= 6.0 + 1e-9, "front lip covers <= 6 mm of bezel (the pod clip's proven reach)", f"{LIP:g} mm")

    print(f"\n8. Every aim {AIMS} deg: teeth mesh, nothing collides, nothing near the screen")
    check(all(a % (360 / TEETH) == 0 for a in AIMS), f"aims are detent positions ({360/TEETH:g} deg teeth)", f"{TEETH} teeth")
    axis_keep = m3.Manifold.cylinder(200, R_D + 0.3, R_D + 0.3, 64).translate([X_A, Y_A, -50])
    core = m3.Manifold.cylinder(60, R_C - 1.2, R_C - 1.2, SEG)   # inside where the ear roots start.translate([0, 0, -30])
    d = ((cup ^ core) - (cup_l ^ core)).volume() + ((cup_l ^ core) - (cup ^ core)).volume()
    check(d < 0.01, "left-edge cup is the right-edge cup with the ear moved across", f"core differs by {d:.4f} mm^3")
    mx = lambda m: m.mirror([1, 0, 0])
    # a left-edge mount is the mirror image of a right-edge one, except the badge inside: check it as
    # mirror(left cup) against the right-hand clip, monitor and screw
    variants = (("R", cup, plate_h, stylus), ("L", mx(cup_l), mx(plate_h), mx(stylus)))
    hw0 = clip_hardware(EDGE_MIN)[0]
    for vn, cup_v, plate_v, stylus_v in variants:
        for a in AIMS:
            asm = {"cup": place(cup_v, a), "ring": place(ring, a), "plate": place(plate_v, a),
                   "plug": place(body + shell, a), "cable": place(cable, a), "stylus": place(stylus_v, a)}
            tm = (asm["cup"] ^ clip).volume()
            worst, rep_ = math.inf, []
            for T in (EDGE_MIN, EDGE_MAX):
                hw, mon, glass = P[T]
                fixed = [clip - axis_keep, hw["pad"], hw["thumbscrew"] + hw["clamp knob"], mon, glass]
                for an, am in asm.items():
                    am2 = am - axis_keep if an == "cup" else am
                    g = min(am2.min_gap(fm, 5.0) for fm in fixed)
                    need = 0.0 if an == "stylus" else 1.0
                    worst = min(worst, g - need)
                    if g < 5: rep_.append(f"{an} {g:.1f}")
            above = asm["cup"].trim_by_plane([0, 0, 1], H + EAR_T + 0.05)     # cup body beside the knob, not the ear under it
            jk = hw0["joint knob"].min_gap(above, 5.0)
            check(tm < 0.05 and worst > 0 and jk >= 0.5,
                  f"{vn} aim {a:+3d}: teeth seat, nothing hits clip/pad/screw/monitor/screen (T 8 & 32)",
                  f"teeth {tm:.3f} mm^3; knob {jk:.1f}; " + (", ".join(sorted(set(rep_))) or "all gaps > 5"))
    front = m3.Manifold.cube([200, 60, 300]).translate([-200 - LIP - 0.01, -60, -120])
    hw = P[EDGE_MAX][0]
    stuff = [clip] + list(hw.values()) + [place(m, a) for a in AIMS for m in (cup, mx(cup_l), ring, cable)]
    v = sum((m ^ front).volume() for m in stuff)
    check(v < 1e-6, f"nothing is in front of the screen (inboard of the {LIP:g} mm lip)", f"{v:.4f} mm^3")
    return P


def physics(cup, ring, plate, clip, geo, b):
    print("\n9. Loads: grip, joint, layer lines (all solid-PETG masses, preload derated for creep)")
    g_cup = (cup.volume() + ring.volume() + plate.volume()) * RHO
    g_hang = g_cup + M_BADGE + M_PLUG + 4.0                              # + bolt and knob
    g_clip = clip.volume() * RHO + 2 * 4.0 + 1.0
    W, Wc = g_hang * G, g_clip * G
    print(f"     hanging: cup+ring+plate {g_cup:.0f} g + badge {M_BADGE:g} + plug {M_PLUG:g} + bolt/knob 4 = {g_hang:.0f} g = {W:.2f} N;"
          f" clip {g_clip:.0f} g")
    F_nom = FINGER_T / (K_NUT * M4_D * 1e-3)
    F = F_nom * CREEP
    print(f"     M4 preload from {FINGER_T} N m on a 20 mm knob: {F_nom:.0f} N, counted as {F:.0f} N")
    d_cg = math.hypot(L_EAR, Z_AX)                                       # axis to cup centre, horizontal
    d_pl = math.hypot(L_EAR, b.port_z - Z_AX)                            # axis to where the cable leaves
    Ro, Ri = R_T, M4_CLR/2 + 0.6
    r_m = 2/3 * (Ro**3 - Ri**3) / (Ro**2 - Ri**2)
    T_slip = F * r_m * math.tan(math.radians(45) + math.atan(MU))        # N mm: lift the ear over a 45 deg tooth
    for a in (min(AIMS), 0, max(AIMS)):
        T_dist = CABLE_PULL * d_pl + W * d_cg * math.sin(math.radians(TILT_MAX)) * abs(math.cos(math.radians(a)))
        check(T_slip / T_dist >= 3, f"aim {a:+3d}: detent holds 1 N sideways pull + weight on a {TILT_MAX:g} deg tilted monitor",
              f"slip {T_slip:.0f} vs {T_dist:.0f} N mm, SF {T_slip/T_dist:.1f}")
    T_fric = MU * F * r_m
    T_worst = CABLE_PULL * d_pl + W * d_cg * math.sin(math.radians(TILT_MAX))
    tooth_h = R_T * TOOTH_A
    check(T_fric / T_worst >= 1.5, f"...even if the {tooth_h:.1f} mm teeth print mushy (3 layers) and act as flat friction",
          f"{T_fric:.0f} vs {T_worst:.0f} N mm, SF {T_fric/T_worst:.1f}")
    M_pry = W * d_cg + CABLE_PULL * d_pl
    check(F * Ro / M_pry >= 3, "bolt keeps the teeth meshed against weight + 1 N down on the cable (every aim)",
          f"{F*Ro:.0f} vs {M_pry:.0f} N mm, SF {F*Ro/M_pry:.1f}")
    print("     gravity acts across the vertical yaw axis: on a level monitor it puts zero torque on the joint at any aim")
    # clip on the side bezel
    slide = 2 * MU * F / (W + Wc + CABLE_PULL)
    check(slide >= 3, "clip does not slide down the bezel (two friction faces)", f"SF {slide:.1f}")
    x_cg = X_A + L_EAR + LIP/2                                            # lever about the lip strip's centre
    M_roll = W * x_cg + CABLE_PULL * x_cg + Wc * (X_SP + LIP) / 2
    resist = MU * F * (H_BODY / 4) + MU * F * (2/3) * PAD_R
    resist_spine = MU * F * (H_BODY / 2 + math.hypot(-X_S, Z_S))          # pivoting on the spine's lower corner
    check(resist / M_roll >= 2, "clip does not twist in the screen plane (friction only, spine ignored)",
          f"{resist:.0f} vs {M_roll:.0f} N mm, SF {resist/M_roll:.1f}")
    check(resist_spine / M_roll >= 3, "...with the spine bearing on the monitor's side (as clipped)",
          f"{resist_spine:.0f} vs {M_roll:.0f} N mm, SF {resist_spine/M_roll:.1f}")
    # layer lines. Clip prints standing up (z): jaws bend in-layer; the pillar bends ACROSS layers.
    Z_p = math.pi * (2*R_D)**3 / 32
    s_p = (M_pry + CABLE_PULL * H) / Z_p
    check(INTERLAYER / s_p >= 10, "pillar bending across the clip's layers (the one cross-layer section)",
          f"{s_p:.2f} MPa vs {INTERLAYER:g}, SF {INTERLAYER/s_p:.0f}")
    A_sh = math.pi * (NUT_AF / math.cos(math.radians(30))) * (NUT_Z - NUT_T)
    s_n = F_nom / A_sh
    check(INTERLAYER / 2 / s_n >= 2, "joint nut cannot pull up through the pillar top at FULL preload",
          f"{s_n:.2f} MPa shear vs {INTERLAYER/2:g}, SF {INTERLAYER/2/s_n:.1f}")
    s_e = (W * R_C + CABLE_PULL * R_C) / ((Z_RIM * -1 + Z_AX) * EAR_T**2 / 6)
    print(f"  [info] ear root bends in-layer (cup prints face-down, ears are vertical plates): {s_e:.2f} MPa")
    rear = F_nom * (-X_S + X_SP / 2) / (H_BODY * RL_T**2 / 6)
    print(f"  [info] rear leg at FULL clamp {F_nom:.0f} N bends in-layer: {rear:.1f} MPa (PETG ~45)")


def main():
    b, c = Badge(), Case()
    os.makedirs(STL, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    feats, cup, plate, geo = build_cup(b, c)
    cup_l = build_cup(b, c, +1)[1]
    plate_h, bx, by = boot_hole_plate(b, c, plate, geo)
    ring = trim_ring()
    clip = build_clip()
    sz = bbox(cup)[1] - bbox(cup)[0]
    print(f"Cup Ø{2*R_C:.1f}, {sz[2]:.1f} deep, {sz[0]:.1f} across the ears; axis {L_EAR:.1f} from the cup centre; "
          f"clip {EDGE_MIN:g}-{EDGE_MAX:g} mm, pillar top {H:g}")
    pocketwatch_checks(b, c, feats, cup, plate, geo)
    P = stalk_checks(b, c, feats, cup, cup_l, plate, plate_h, ring, clip, geo)
    physics(cup, ring, plate, clip, geo, b)
    print("\n10. Print files: watertight, no supports, in print orientation")
    export(cup, STL + "Stalk gauge - cup (right edge of monitor).stl", lambda m: m.translate([0, 0, -Z_RIM]))
    export(cup_l, STL + "Stalk gauge - cup (left edge of monitor).stl", lambda m: m.translate([0, 0, -Z_RIM]))
    flip = lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]])
    export(plate_h, STL + "Stalk gauge - back plate (BOOT hole).stl", flip)
    export(ring, STL + "Stalk gauge - trim ring and visor.stl", lambda m: m.rotate([180, 0, 0]).translate([0, 0, Z_RIM + SPIG]))
    export(clip, STL + "Stalk gauge - clip (right edge of monitor).stl", lambda m: m)
    export(clip.mirror([1, 0, 0]), STL + "Stalk gauge - clip (left edge of monitor).stl", lambda m: m)
    export(build_pad().translate([-X_S, 0, -Z_S]).rotate([90, 0, 0]), STL + "Stalk gauge - clamp pad.stl", lambda m: m)
    export(build_knob(), STL + "Stalk gauge - knob (print 2).stl", lambda m: m.rotate([180, 0, 0]).translate([0, 0, 10]))
    if "--no-render" not in sys.argv:
        renders(b, c, feats, cup, plate_h, ring, clip, geo, P)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


CUP_C, RING_C, CLIP_C, RED, STEEL, MON_C, GLASS_C = ((0.34, 0.35, 0.38), (0.88, 0.89, 0.92), (0.24, 0.25, 0.28),
    (0.86, 0.12, 0.09), (0.70, 0.72, 0.75), (0.11, 0.11, 0.12), (0.05, 0.08, 0.16))


def dial(b):
    """A gauge face drawn on the glass (badge frame): dark disc, white ticks, red needle. 12 o'clock = badge -y."""
    face = prism(circle(b.active_d/2), -0.25, 0.0)
    ticks = []
    for i in range(11):
        a = math.radians(-135 + 27*i)
        long = i % 5 == 0
        t = m3.Manifold.cube([0.9 if long else 0.6, 4.5 if long else 2.6, 0.2]).translate([-0.45 if long else -0.3, -14.6, -0.45])
        ticks.append(t.rotate([0, 0, math.degrees(a)]))
    needle = m3.Manifold.cube([1.0, 12.5, 0.2]).translate([-0.5, -12.5, -0.65]).rotate([0, 0, 50])
    hub = m3.Manifold.cylinder(0.3, 1.6, 1.6, 32).translate([0, 0, -0.8])
    return [(face, (0.03, 0.05, 0.10)), (union(ticks), (0.95, 0.95, 0.92)), (needle + hub, (0.95, 0.30, 0.10))]


def renders(b, c, feats, cup, plate_h, ring, clip, geo, P):
    R = lambda m, L=1.5: m.refine_to_length(L)
    body, cable, shell = plug_and_cable(b, geo)
    badge = [f.solid() for f in feats if f.name == "disc + tab"][0]

    def gauge(aim, cable_len=70.0):
        cab = plug_and_cable(b, geo, cable_len)[1]
        parts = [(cup, CUP_C), (plate_h, CUP_C), (ring, RING_C), (badge, (0.08, 0.08, 0.09)), (body, (0.78, 0.78, 0.80)),
                 (cab, (0.06, 0.06, 0.07)), (shell, STEEL)] + dial(b)
        return [(place(m, aim), col) for m, col in parts]

    def mount(T, with_monitor=True):
        hw = clip_hardware(T)[0]
        mon, glass = monitor(T)
        box = m3.Manifold.cube([75, 200, 150]).translate([-75, -10, -40])
        out = [(mon ^ box, MON_C), (glass ^ box, GLASS_C)] if with_monitor else []
        return out + [(clip, CLIP_C), (hw["pad"], (0.15, 0.15, 0.15)),
                      (hw["thumbscrew"] + hw["joint bolt"], STEEL), (hw["clamp knob"] + hw["joint knob"], RED)]
    scene = lambda T, aim: [(R(m, 2.5 if col in (MON_C, GLASS_C) else 1.5), col) for m, col in mount(T) + gauge(aim)]

    render(scene(20.0, 30), OUT + "01-hero.png", elev=20, azim=-142, zoom=1.15,
           title="Stalk gauge on a 20 mm monitor edge, turned 30° toward you: 52 mm cup, chrome ring and visor, red knobs")
    render(scene(20.0, 30), OUT + "02-front-as-you-see-it.png", elev=4, azim=-120, zoom=1.2,
           title="As you see it from your chair, 30° off to the left (aim 30). Plug and cable drop beside the monitor")

    # side section through the cup centre, aim 0, looking from outboard (+x)
    cx = X_A + L_EAR
    light = lambda col: (0.58, 0.59, 0.63) if col == CUP_C else (0.45, 0.46, 0.50) if col == CLIP_C else col
    cut = [(R(m.trim_by_plane([1, 0, 0], cx), 1.0), light(col)) for m, col in gauge(0, 12.0)]
    stylus = place(m3.Manifold.cylinder(40, PIN_D/2, PIN_D/2, 24).translate([geo["sw"][c.BUTTON], b.sw_y, b.pcb_back_z + b.sw_cap_h - c.SW_TRAVEL]), 0)
    render([(m, col) for m, col in cut if not m.is_empty()], OUT + "03-section-side.png", elev=0, azim=180, zoom=1.1,
           title="Side section through the cup centre, you are on the right: glass on the bezel lip, 45° cone rim,\n"
                 "chrome ring + visor, plate snapped in flush at the back, USB-C plug and cable straight down")
    # section through the joint axis, looking from the front
    crop = m3.Manifold.cube([95, 200, 70]).translate([-8, -100, 12])
    hw = clip_hardware(20.0)[0]
    cut = [(R((m ^ crop).trim_by_plane([0, 1, 0], Y_A), 0.8), light(col)) for m, col in
           mount(20.0, False) + gauge(0)[:3] + [(hw["joint nut"], (0.45, 0.47, 0.50))]]
    render([(m, col) for m, col in cut if not m.is_empty()], OUT + "04-section-joint.png", elev=0, azim=-90, zoom=1.0,
           title="Section through the pivot: ear's 24 teeth on the pillar's, M4 bolt from the red knob into a trapped nut")
    # the joint pulled apart: teeth on the pillar, matching teeth under the ear
    up = lambda m, dz: m.translate([0, 0, dz])
    crop = m3.Manifold.cube([130, 120, 120]).translate([-25, -50, 18])
    ex = [(clip, CLIP_C), (up(hw["joint nut"], 0), STEEL)] + \
         [(up(m, 24).translate([0, 0, 0]), col) for m, col in [(place(cup, -15), (0.50, 0.51, 0.55)), (place(ring, -15), RING_C)]] + \
         [(up(hw["joint bolt"], 48), STEEL), (up(hw["joint knob"], 48), RED)]
    render([(R(m ^ crop, 0.6), col) for m, col in ex], OUT + "04b-joint-apart.png", elev=40, azim=-112, zoom=1.25,
           title="The pivot, pulled apart: 24 teeth on the pillar mesh with 24 under the ear every 15°.\n"
                 "Loosen the red knob 2 turns, turn the cup, tighten.")
    # back view, BOOT stylus going in
    render(scene(20.0, 30) + [(R(place(m3.Manifold.cylinder(40, PIN_D/2, PIN_D/2, 24).translate(
               [geo["sw"][c.BUTTON], b.sw_y, b.pcb_back_z + b.sw_cap_h - c.SW_TRAVEL]), 30)), (0.10, 0.75, 0.30))],
           OUT + "05-back-boot.png", elev=18, azim=62, zoom=1.15,
           title="From behind: back plate flush, a Ø2 pin (green) straight into the BOOT hole. Nothing in the way")
    # top view: aim range on a 32 mm edge
    mon, glass = monitor(EDGE_MAX)
    hw = clip_hardware(EDGE_MAX)[0]
    top = [(R(mon ^ m3.Manifold.cube([60, 200, 300]).translate([-60, -10, -100]), 3.0), MON_C), (R(clip), CLIP_C),
           (R(hw["pad"]), (0.15, 0.15, 0.15)), (R(hw["thumbscrew"]), STEEL), (R(hw["clamp knob"] + hw["joint knob"]), RED)]
    for aim, col in ((-15, (0.55, 0.56, 0.60)), (30, CUP_C), (60, (0.20, 0.45, 0.80))):
        top += [(R(place(cup + ring, aim)), col)]
    render(top, OUT + "06-aim-range-top.png", elev=88, azim=-90, zoom=1.0,
           title=f"From above, 32 mm edge: aim -15° (light), 30° (grey), 60° (blue). Detents every {360/TEETH:g}°")
    # print layout
    lay = [(cup.translate([0, 0, -Z_RIM]).translate([-60, 35, 0]), CUP_C),
           (ring.rotate([180, 0, 0]).translate([0, 0, Z_RIM + SPIG]).translate([5, 35, 0]), RING_C),
           (plate_h.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]]).translate([60, 35, 0]), CUP_C),
           (clip.translate([-55, -60, 0]), CLIP_C),
           (build_pad().translate([-X_S, 0, -Z_S]).rotate([90, 0, 0]).translate([5, -40, 0]), (0.15, 0.15, 0.15)),
           (build_knob().rotate([180, 0, 0]).translate([0, 0, 10]).translate([35, -40, 0]), RED),
           (build_knob().rotate([180, 0, 0]).translate([0, 0, 10]).translate([62, -40, 0]), RED)]
    bed = m3.Manifold.cube([200, 190, 0.4]).translate([-100, -95, -0.4])
    render([(R(bed, 6.0), (0.85, 0.85, 0.82))] + [(R(m), col) for m, col in lay], OUT + "07-print-layout.png", elev=48, azim=-62,
           title="Print layout, all as exported, no supports: cup face-down, ring visor-up, plate, clip standing, pad, 2 knobs")




if __name__ == "__main__":
    main()
