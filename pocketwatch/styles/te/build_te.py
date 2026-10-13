#!/usr/bin/env python3
"""
TE family: a desk STAND and a monitor CLIP for the slim USB-only pocketwatch case,
drawn as two accessories of one product line (Teenage Engineering cues: a strict
4 mm grid, rounded-square slabs with crisp chamfered edges, light-grey body, one
orange accent printed as separate small parts, visible hex screws, a dot-grid
grille, tiny dot-matrix numerals).

Both products share one HEAD: a 56 x 56 slab face with the pocketwatch case fused
into it (bezel lip, bore, plate counterbore + snap groove, crown boss, USB-C slot),
an orange trim ring around the display, and a screwed-on BACK COVER whose flexure
tongue carries an oversized orange BOOT cap. Below the head both products have the
same 56 x 32 PLUG BAY: the straight plug hangs in it, seen through a dot grille.

  STAND  the slab leans back 15 deg on a foot block, four orange feet.
  CLIP   the slab gets a spine and a 6 mm front lip on its monitor side; a sliding
         rear jaw with a flexure finger, locked by an M3 screw under an orange knob.

Frames: badge frame = build_pocketwatch's (origin on the glass centre, +y toward the
USB tab, +z backward). The crown is DOWN in both products (display rotated 180 deg
in firmware), so world X = badge x, world Z (up) = -badge y, world Y (back) = badge z.

Run from the repo root:  ~/.venvs/cad/bin/python pocketwatch/styles/te/build_te.py [--no-render]
"""
import sys, math, os
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pod")
import numpy as np, manifold3d as m3, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)

STL = "stl/pocketwatch/styles/te/"
PNG = "pocketwatch/styles/te/renders/"
Miter = m3.JoinType.Miter

# ---- the grid ------------------------------------------------------------------------
M = 4.0                    # module: every plan dimension below is a whole number of these, or half
HW = 7*M                   # head half width: 56 = 14 M
Y_TOP, Y_BOT = -7*M, 15*M  # slab face spans y -28..60: 88 = 22 M (head 14 M + plug bay 8 M)
R_SLAB = 3*M               # plan corner radius 12
EDGE_C = 0.6               # crisp chamfer on every face edge
COVER_HALF, COVER_R = 6*M, 2*M     # back cover 48 x 48, r 8
COVER_T = 2.4
FIT = 0.2                  # cover in its pocket, per side
SCREW_XY = 19.0            # cover screws at (+-19, +-19)
SCREW_TAP, SCREW_CLR, SCREW_L, HEAD_D, HEAD_H = 2.8, 3.4, 12.0, 5.5, 3.0      # M3 x 12 socket head
RING_OUT, RING_IN, RING_T = 6*M, 17.4, 1.2          # orange ring ON the face, around the window
PEG_D, PEG_L, PEG_R = 2.4, 2.0, 21.5                # its four press pegs, on r 21.5 at 45/135/225/315 deg
PRESS = 0.10               # press-fit parts are this much under their hole, radially (pod's RING_PRESS)
DEBOSS = 0.6               # graphics depth: two 0.3 layers
PX = 1.0                   # dot-matrix pixel: strokes 1.0 wide for a 0.6 nozzle

# plug: straight USB-C, shell 8.4 x 2.6 x 6.65, overmould 12 x 8 x 22, cable 4
SHELL_W, SHELL_T, SHELL_L = 8.4, 2.6, 6.65
PLUG_W, PLUG_T, PLUG_L, CABLE_D = 12.0, 8.0, 22.0, 4.0
BAY_CLR = 0.8
GRILLE_D = 2.0

# BOOT: orange cap on a flexure tongue in the back cover; its stem goes through the plate to the switch
G = 0.30                   # stem tip behind the actuator at rest
OVERTRAVEL = 0.35          # cap rim stops this far past the click
STEM_D, TIP_D = 3.0, 2.0   # stem, and the tip that passes the header envelope
BOOT_HOLE = STEM_D + 0.8   # plate hole: 0.4 radial clearance on the moving stem
PAD_D, TONGUE_W, TONGUE_T, TONGUE_L, SLOT = 6.0, 5.0, 1.2, 11.0, 1.0
CAP_D, CAP_T, CAP_BOSS_D = 3*M, 2.4, 5.0
CBORE_D, CBORE_DEPTH = 7.0, 1.2       # counterbore in the plate's back face for the pad's travel
HEX_INTERF = 0.05          # hex hole across flats under the stem diameter
E_PETG, STRAIN_MAX = 2000.0, 0.02
SW_FORCE = 1.6             # N, a typical 160 gf tact switch at full travel

# stand
TILT = 15.0                # display leans back
FOOT_Z, FOOT_TOP_Y = 42.0, 9*M        # foot block behind the slab, badge z up to 38, from y 36 down
FEET_D, FEET_PROUD, FEET_IN = 2*M, 1.5, 2.0
BEND_R = 8.0               # cable bend radius in the bay
STAND_FEET = [(-22.0, 5.0), (22.0, 5.0), (-22.0, 39.5), (22.0, 39.5)]   # world X, Y behind the front-bottom edge

# clip (world: monitor right edge at X=0, its front at Y=0, back at Y=edge)
EDGE_MIN, EDGE_MAX = 8.0, 32.0
LIP, LIP_T = 6.0, 3.0      # front lip over the bezel (the approved pod clip's 6 mm)
SPINE_W = 14.0             # X 0..14; the head slab starts at X=14
OX, OY = SPINE_W + HW, -LIP_T - (-1.2)            # badge -> clip world offsets (front face at Y=-3)
Y_END = 46.0               # spine depth
ZT = -Y_TOP                # top of everything, world Z 28
TOP_WALL = 4.0
CH_X0, CH_X1, CH_H = -1.0, 11.0, 20.6               # tongue channel, open toward the monitor
ZC = ZT - TOP_WALL - CH_H/2
CLR = 0.4                  # moving-part clearance
SCREW_X, SCREW_DY = 5.5, 9.0                        # lock screw in the tongue, behind the pad plane
REACH, ROOT, FINGER_T, GAP, PAD_W, PAD_H = 20.0, 3.0, 1.8, 1.0, 4.0, 0.6
JAW_BODY_T, TONGUE_LEN = 3.0, 16.0
KNOB_D, KNOB_H = 4*M, 6.0
MU, CABLE_PULL, BADGE_G, FILL = 0.3, 1.0, 20.0, 0.40   # PETG on a plastic bezel; 1 N; badge; printed solid fraction


# ---- small helpers ----------------------------------------------------------------------
def rrect(x0, x1, y0, y1, r, r_bot=None):
    """Rounded rectangle; r at y0 corners, r_bot at y1 corners (badge y1 = the bottom when crown down)."""
    rb = r if r_bot is None else r_bot
    cs = [circle(r).translate([x0 + r, y0 + r]), circle(r).translate([x1 - r, y0 + r]),
          circle(rb).translate([x0 + rb, y1 - rb]), circle(rb).translate([x1 - rb, y1 - rb])]
    return m3.CrossSection.batch_hull(cs)


def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_z(x, y, z0, z1, d, seg=64):
    return m3.Manifold.cylinder(z1 - z0, d/2, d/2, seg).translate([x, y, z0])


def hex_cs(af):
    r = af/2/math.cos(math.pi/6)
    return m3.CrossSection([[(r*math.cos(a), r*math.sin(a)) for a in np.arange(6)*math.pi/3 + math.pi/6]])


FONT = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"], "B": ["110", "101", "110", "101", "110"],
    "O": ["111", "101", "101", "101", "111"], "T": ["111", "010", "010", "010", "010"],
    "v": ["00100", "00100", "11111", "01110", "00100"], ">": ["00100", "00110", "11111", "00110", "00100"],
    "^": ["00100", "01110", "11111", "00100", "00100"], ".": ["0", "0", "0", "0", "1"],
}


def text_cs(s, px=PX):
    """Dot-matrix type in viewer coordinates (u right, v up), bottom-left at the origin."""
    sq, cx = [], 0.0
    for ch in s:
        rows = FONT[ch]
        for r, row in enumerate(rows):
            for k, bit in enumerate(row):
                if bit == "1":   # grown a hair so diagonal neighbours overlap instead of pinching
                    sq.append(rect(cx + k*px - 0.03, cx + (k + 1)*px + 0.03, (4 - r)*px - 0.03, (5 - r)*px + 0.03))
        cx += (len(rows[0]) + 1)*px
    return m3.CrossSection.batch_boolean(sq, m3.OpType.Add), cx - px


def on_front(cs, u, v):   # viewer at the front: badge x = u, badge y = -v
    return cs.translate([u, v]).mirror([0, 1])


def on_back(cs, u, v):    # viewer at the back: badge x = -u, badge y = -v
    return cs.translate([u, v]).rotate(180)


def to_mesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))


# ---- the pocketwatch case, copied from build_pocketwatch_usb.build() as cuts --------------
def head_core(b: Badge, c: Case):
    """The USB-only case's cuts, plate, and geometry, without its outer shell: the slab is the shell."""
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    R_REAR = R_BORE + 1.2
    R_OUT = R_REAR + c.CASE_WALL
    FLOOR = b.hdr_top_z + c.FLOAT
    Z_CASE = FLOOR + c.PLATE_T
    bore_xy = feats[0].grown()
    pocket = circle(R_REAR) + bore_xy
    boss = (bore_xy.offset(c.CASE_WALL, Round) ^ rect(-40, 40, 10, 40)).hull()
    boss_tip = boss.bounds()[3]
    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())
    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4
    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    cuts = [prism(bore_xy, 0.0, Z_CASE + 1), prism(circle(R_REAR), FLOOR, Z_CASE + 1),
            window.translate([0, 0, -c.LIP_T - 0.01]), groove_p, all_keep]

    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    plate_xy = pocket.offset(-c.FIT_CLR - 0.03, Round)
    plate = prism(plate_xy, FLOOR, Z_CASE)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead_p
    plate += guides
    plate -= all_keep
    bx, by = sw[c.BUTTON], b.sw_y
    # the plate's BOOT hole (build_pocketwatch_usb's, widened for a 3.0 stem) and a counterbore for the pad
    plate -= cyl_z(bx, by, b.pcb_back_z + 1.0, Z_CASE + 1, BOOT_HOLE)
    plate -= cyl_z(bx, by, Z_CASE - CBORE_DEPTH, Z_CASE + 1, CBORE_D)
    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_OUT, FLOOR=FLOOR, Z_CASE=Z_CASE, Z_BACK=Z_CASE + COVER_T,
               bh_p=bh_p, groove_r_p=groove_r_p, hdrs=hdrs, sw=sw, bx=bx, by=by, boss_tip=boss_tip,
               plate_xy=plate_xy, keep=keep, bore_xy=bore_xy)
    return feats, union(cuts), plate, geo


def head_parts(b, c, geo):
    """Everything the stand and the clip share behind/around the case: cuts in the slab, and the cover,
    cap and ring. Returns (cuts, cover, cover_fixed, tongue_moving, cap, ring)."""
    Z_CASE, Z_BACK, bx, by = geo["Z_CASE"], geo["Z_BACK"], geo["bx"], geo["by"]
    cover_xy = rrect(-COVER_HALF, COVER_HALF, -COVER_HALF, COVER_HALF, COVER_R)
    pocket_xy = cover_xy.offset(FIT, Round)
    screws = [(sx*SCREW_XY, sy*SCREW_XY) for sx in (-1, 1) for sy in (-1, 1)]
    tap_z0 = Z_BACK - SCREW_L - 0.6
    cuts = [prism(pocket_xy, Z_CASE, Z_BACK + 50)]
    cuts += [cyl_z(x, y, tap_z0, Z_CASE + 0.01, SCREW_TAP, 32) for x, y in screws]
    # plug bay: from the boss tip (the 3.0 wall in front of the port stays as the case had it) down
    bay_x = PLUG_W/2 + BAY_CLR
    bay_z0 = b.port_z - PLUG_T/2 - BAY_CLR
    cuts.append(box(-bay_x, bay_x, geo["boss_tip"], 200, bay_z0, 200))
    # trim ring sits on the face; four hex holes take its pegs, clear of the bore and the tab pocket
    pegs = [(PEG_R*math.cos(math.radians(a)), PEG_R*math.sin(math.radians(a))) for a in (45, 135, 225, 315)]
    cuts += [prism(hex_cs(PEG_D).translate([x, y]), -c.LIP_T - 1, -c.LIP_T + PEG_L + 0.2) for x, y in pegs]
    geo["pegs"] = pegs
    # dot grille through the bay's front wall: 3 x 8 on the 4 mm grid
    grille = [(gx, gy) for gx in (-M, 0, M) for gy in np.arange(7*M, 14*M + 0.1, M)]
    cuts += [cyl_z(x, y, -c.LIP_T - 1, bay_z0 + 0.5, GRILLE_D, 24) for x, y in grille]
    geo.update(bay_x=bay_x, bay_z0=bay_z0, screws=screws, grille=grille, tap_z0=tap_z0)

    # ---- back cover: flexure tongue + pad, screw holes, BOOT legend
    cover = prism(cover_xy, Z_CASE, Z_BACK)
    cover = chamfered([cover_xy], Z_CASE, Z_BACK, 0.0, EDGE_C)
    cover -= prism(geo["plate_xy"].offset(0.3, Round), Z_CASE - 1, Z_CASE + 0.3)       # never sits on the plate
    for x, y in screws:
        cover -= cyl_z(x, y, Z_CASE - 1, Z_BACK + 1, SCREW_CLR, 32)
    tongue_xy = rect(bx - TONGUE_W/2, bx + TONGUE_W/2, by - TONGUE_L, by)
    pad_xy = circle(PAD_D/2).translate([bx, by])
    lever = tongue_xy + pad_xy
    root = rect(-100, 100, by - TONGUE_L, 100)
    slot = (lever.offset(SLOT, Round) - lever) ^ root
    cover -= prism(slot, Z_CASE - 1, Z_BACK + 1)
    cover -= prism(tongue_xy - pad_xy, Z_CASE - 1, Z_BACK - TONGUE_T)                       # thin the tongue
    cover -= prism(hex_cs(STEM_D - HEX_INTERF).translate([bx, by]), Z_CASE - 1, Z_BACK + 1)
    legend, lw = text_cs("BOOT")
    arrow, aw = text_cs(">")
    # legend reads from the back, left of the cap (seen from the back the cap is at u = -bx)
    u_cap, v_cap = -bx, -by
    back_gfx = on_back(legend, u_cap - CAP_D/2 - 2 - lw - aw - 1.0, v_cap - 2.5) + \
        on_back(arrow, u_cap - CAP_D/2 - 1.5 - aw, v_cap - 2.5)
    cover -= prism(back_gfx, Z_BACK - DEBOSS, Z_BACK + 1)
    geo["back_gfx"] = back_gfx
    moving_xy = lever ^ root
    tongue_moving = cover ^ prism(moving_xy, Z_CASE - 1, Z_BACK + 1)
    cover_fixed = cover - prism(moving_xy.offset(0.01, Round), Z_CASE - 1, Z_BACK + 1)

    # ---- orange cap: disc, seat boss on the pad, stem through the pad and the plate to the switch
    stop = G + c.SW_TRAVEL + OVERTRAVEL
    tip_z = b.pcb_back_z + b.sw_cap_h + G
    neck_z = geo["FLOOR"] + stop + 0.1                         # Ø3 part never reaches the header envelope
    cap = chamfered([circle(CAP_D/2).translate([bx, by])], Z_BACK + stop, Z_BACK + stop + CAP_T, 0.0, EDGE_C)
    cap += cyl_z(bx, by, Z_BACK, Z_BACK + stop + 0.01, CAP_BOSS_D)
    cap += cyl_z(bx, by, neck_z, Z_BACK + 0.01, STEM_D, 48)
    cap += m3.Manifold.cylinder(0.5, TIP_D/2, STEM_D/2, 48).translate([bx, by, neck_z - 0.5])
    cap += cyl_z(bx, by, tip_z, neck_z - 0.49, TIP_D, 48)
    geo.update(stop=stop, tip_z=tip_z, neck_z=neck_z, moving_xy=moving_xy)

    # ---- orange trim ring: a flat 1.2 annulus on the face, round pegs pressed into hex holes
    z_f = -c.LIP_T
    ring = chamfered([circle(RING_OUT)], z_f - RING_T, z_f, EDGE_C, 0.0) - prism(circle(RING_IN), z_f - 5, z_f + 1)
    ring -= m3.Manifold.cylinder(0.31, RING_IN + 0.3, RING_IN, SEG).translate([0, 0, z_f - RING_T - 0.01])
    ring += union(cyl_z(x, y, z_f - 0.01, z_f + PEG_L, PEG_D + HEX_INTERF, 32) for x, y in geo["pegs"])
    return union(cuts), cover, cover_fixed, tongue_moving, cap, ring


# ---- STAND ------------------------------------------------------------------------------
def rx(a):
    a = math.radians(a); ca, sa = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])


class StandFrame:
    ROT = -(90.0 + TILT)

    def __init__(self, c):
        p0 = np.array([0.0, Y_BOT, -c.LIP_T])               # front-bottom edge of the face
        self.t = -rx(self.ROT) @ p0 + np.array([0, 0, FEET_PROUD])

    def world(self, m): return m.rotate([self.ROT, 0, 0]).translate(list(self.t))
    def badge(self, m): return m.translate(list(-self.t)).rotate([-self.ROT, 0, 0])
    def pt(self, p): return rx(self.ROT) @ np.asarray(p, float) + self.t


def build_stand(b, c, geo, head_cuts):
    F = StandFrame(c)
    Z_BACK = geo["Z_BACK"]
    slab = chamfered([rrect(-HW, HW, Y_TOP, Y_BOT + 12, R_SLAB, 2.0)], -c.LIP_T, Z_BACK, EDGE_C, EDGE_C)
    foot = chamfered([rrect(-HW, HW, FOOT_TOP_Y, Y_BOT + 12, M, 2.0)], Z_BACK - 1, FOOT_Z, 0.0, EDGE_C)
    desk = F.badge(box(-200, 200, -200, 200, FEET_PROUD, 300))
    body = (slab + foot) ^ desk
    body -= head_cuts
    # feet: blind holes up from the bottom face, along world Z
    feet_w = [cyl_z(x, y, -5, FEET_PROUD + FEET_IN, FEET_D, 48) for x, y in STAND_FEET]
    body -= F.badge(union(feet_w))
    foot_part = chamfered([circle(FEET_D/2 - PRESS)], 0.0, FEET_PROUD + FEET_IN - 0.05, EDGE_C, 0.0)
    feet_world = [foot_part.translate([x, y, 0]) for x, y in STAND_FEET]
    # front: "01" bottom-left, and the joint line between the head module and the bay module
    t01, w01 = text_cs("01")
    gfx = on_front(t01, -HW + 5, -Y_BOT + 5) + joint_h(-HW + 3, HW - 3)
    body -= prism(gfx, -c.LIP_T - 1, -c.LIP_T + DEBOSS)
    geo["gfx_stand"] = gfx
    return F, body, foot_part, feet_world


JOINT_Y, JOINT_W = 26.0, 1.0      # head / bay module joint, just under the ring


def joint_h(x0, x1):
    """Horizontal joint line at JOINT_Y, broken where the grille column passes."""
    gx = M + GRILLE_D/2 + 2.0
    return rect(x0, -gx, JOINT_Y - JOINT_W/2, JOINT_Y + JOINT_W/2) + rect(gx, x1, JOINT_Y - JOINT_W/2, JOINT_Y + JOINT_W/2)


def cable_path_stand(b, F, geo):
    """Plug end, straight on, then a BEND_R arc turning back to run along the desk at cable height."""
    d0 = rx(F.ROT) @ np.array([0, 1.0, 0])                     # plug axis in the world (down, a little forward)
    p0 = F.pt([0, geo["boss_tip"] + PLUG_L, b.port_z])
    zc = CABLE_D/2
    a0 = math.atan2(d0[2], d0[1])                               # heading in the (Y, Z) plane
    turn = (2*math.pi - (a0 % (2*math.pi)))                     # CCW to heading 0 (backward)
    nrm = np.array([math.cos(a0 + math.pi/2), math.sin(a0 + math.pi/2)])   # toward the bend centre
    # centre C = P1 + R*n; the arc ends at C - (0, R); P1 = p0 + s*d0, so solve P1z + R*n_z - R = zc
    s1 = (p0[2] + BEND_R*nrm[1] - BEND_R - zc) / -d0[2]
    pts = [p0, p0 + s1*d0]
    P1 = pts[-1]
    C = np.array([P1[1], P1[2]]) + BEND_R*nrm
    for k in range(1, 13):
        a = a0 + turn*k/12
        q = C - BEND_R*np.array([math.cos(a + math.pi/2), math.sin(a + math.pi/2)])
        pts.append(np.array([0.0, q[0], q[1]]))
    pts.append(pts[-1] + np.array([0, 60.0, 0]))
    return pts, s1


def tube(pts, d):
    s = [m3.Manifold.sphere(d/2, 24).translate(list(p)) for p in pts]
    return union(m3.Manifold.batch_hull([s[i], s[i + 1]]) for i in range(len(s) - 1))


# ---- CLIP -------------------------------------------------------------------------------
def clip_world(m): return m.rotate([-90, 0, 0]).translate([OX, OY, 0])
def clip_badge(m): return m.translate([-OX, -OY, 0]).rotate([90, 0, 0])


def extrude_yz(poly, x0, x1):
    """A (Y, Z) polygon extruded along world X."""
    area2 = sum(poly[i][0]*poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0]*poly[i][1] for i in range(len(poly)))
    cs = m3.CrossSection([[(y, z) for y, z in (poly if area2 > 0 else poly[::-1])]])
    return m3.Manifold.extrude(cs, x1 - x0).transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])


def build_clip(b, c, geo, head_cuts):
    Z_BACK = geo["Z_BACK"]
    yb = Z_BACK + OY                                           # world Y of the slab's back face
    # front: one rounded rectangle across lip + spine + head (badge x -48..28)
    face_xy = rrect(-OX - LIP, HW, Y_TOP, Y_BOT, R_SLAB)
    slab = chamfered([face_xy], -c.LIP_T, Z_BACK, EDGE_C, EDGE_C)
    slab -= box(-OX - LIP - 5, -OX, -100, 100, -c.LIP_T + LIP_T, 100)       # the lip is only LIP_T thick
    # spine behind the slab, world; bottom chamfered at 45 deg so it prints and sheds weight
    zb = ZC - CH_H/2 - 6.0
    poly = [(yb - 1, ZT), (Y_END, ZT), (Y_END, zb), (yb - 1, zb - (Y_END - yb + 1))]
    spine = extrude_yz(poly, 0.0, SPINE_W)
    spine = spine ^ box(0, SPINE_W, -100, 100, -100, ZT)
    # crisp: chamfer the spine's two long back edges with a hull trick (cut 45-deg wedges)
    for xe in (0.0, SPINE_W):
        wedge = box(-EDGE_C, EDGE_C, -EDGE_C, EDGE_C, -200, 200).rotate([0, 0, 45]).translate([xe, Y_END, 0])
        spine -= wedge
    body = slab + clip_badge(spine)
    body -= head_cuts
    # channel, lock slot, perforations (world), then into the badge frame
    cuts = [box(CH_X0, CH_X1, EDGE_MIN - 0.5, Y_END + 1, ZC - CH_H/2, ZC + CH_H/2)]
    s0, s1 = EDGE_MIN + SCREW_DY, EDGE_MAX + SCREW_DY
    slot_cs = m3.CrossSection.batch_hull([circle(SCREW_CLR/2).translate([SCREW_X, s0]),
                                          circle(SCREW_CLR/2).translate([SCREW_X, s1])])
    cuts.append(prism(slot_cs, ZC + CH_H/2 - 0.1, ZT + 1))
    holes = []
    for yy in np.arange(4*M, Y_END - 3, 1.5*M):
        for zz in np.arange(ZC - CH_H/2 - 2.4 - 2.0, -60, -1.5*M):
            zbot = zb - (Y_END - yy)              # spine bottom at this Y (45 deg line)
            if zz - 2.0 - 2.0 >= zbot and yy - 2 - 1.6 >= yb:
                holes.append((yy, zz))
    for yy, zz in holes:
        cuts.append(m3.Manifold.cylinder(SPINE_W + 2, 2.0, 2.0, 32).rotate([0, 90, 0]).translate([-1, yy, zz]))
    body -= clip_badge(union(cuts))
    # front: "02" bottom of the strip, an arrow up to the knob, the module joints, and a tick where
    # the monitor's edge sits (top and bottom of the strip)
    t02, w02 = text_cs("02")
    arrow, aw = text_cs("^")
    xk = SCREW_X - OX                                           # knob, badge x
    gfx = on_front(t02, -OX - LIP + 5, -Y_BOT + 5) + on_front(arrow, xk - aw/2, -Y_TOP - 12)
    gfx += joint_h(-HW + JOINT_W/2, HW - 3)
    gfx += rect(-HW - JOINT_W/2, -HW + JOINT_W/2, Y_TOP + 3, Y_BOT - 3)
    gfx += rect(-OX - JOINT_W/2, -OX + JOINT_W/2, Y_TOP + 2, Y_TOP + 7) + rect(-OX - JOINT_W/2, -OX + JOINT_W/2, Y_BOT - 7, Y_BOT - 2)
    body -= prism(gfx, -c.LIP_T - 1, -c.LIP_T + DEBOSS)
    geo["gfx_clip"] = gfx
    geo.update(clip_holes=holes, clip_zb=zb, clip_yb=yb)
    return body


def slider_at(e):
    """Rear jaw in the world, pad face at Y = e (the monitor's back). Prism along Z."""
    z0, z1 = ZC - CH_H/2 + CLR, ZC + CH_H/2 - CLR
    y0 = e + PAD_H
    jaw = box(-REACH, -CLR, y0, y0 + FINGER_T + GAP + JAW_BODY_T, z0, z1)
    jaw -= box(-REACH - 1, -ROOT, y0 + FINGER_T, y0 + FINGER_T + GAP, z0 - 1, z1 + 1)     # the flex gap
    jaw += box(-REACH, -REACH + PAD_W, e, y0 + 0.01, z0, z1)                              # contact pad
    tongue = box(-CLR - 0.2, CH_X1 - CLR, y0, e + TONGUE_LEN, z0, z1)
    s = jaw + tongue
    s -= cyl_z(SCREW_X, e + SCREW_DY, z0 + 1.2, z1 + 1, SCREW_TAP, 32)
    return s


def finger_xy(e):
    z0, z1 = ZC - CH_H/2 + CLR, ZC + CH_H/2 - CLR
    return box(-REACH, -ROOT, e, e + PAD_H + FINGER_T, z0, z1)


def knob_at(e):
    k = chamfered([circle(KNOB_D/2)], ZT, ZT + KNOB_H, 0.0, EDGE_C)
    for i in range(18):                                     # flutes for a dry thumb
        a = 2*math.pi*i/18
        k -= cyl_z(KNOB_D/2*math.cos(a) + 0.35*math.cos(a), KNOB_D/2*math.sin(a) + 0.35*math.sin(a),
                   ZT - 1, ZT + KNOB_H + 1, 1.6, 16)
    k -= cyl_z(0, 0, ZT - 1, ZT + HEAD_H, HEAD_D + 0.1, 48)   # socket head presses in from below, flush
    k -= box(-0.5, 0.5, KNOB_D/2 - 3.0, KNOB_D/2 + 1, ZT + KNOB_H - DEBOSS, ZT + KNOB_H + 1)   # index line
    return k.translate([SCREW_X, e + SCREW_DY, 0])


def screw_at(e):
    s = cyl_z(SCREW_X, e + SCREW_DY, ZT, ZT + HEAD_H, HEAD_D, 32)
    return s + cyl_z(SCREW_X, e + SCREW_DY, ZT - (SCREW_L - 0.0), ZT + 0.01, 3.0, 24)


def finger_force(d):
    L = REACH - PAD_W/2 - ROOT
    w = CH_H - 2*CLR
    return E_PETG*w*FINGER_T**3*d/(4*L**3), 3*FINGER_T*d/(2*L**2), L, w


# ---- checks ------------------------------------------------------------------------------
def head_checks(tag, b, c, feats, body, plate, cover, cover_fixed, tongue, cap, ring, geo):
    stop, bx, by = geo["stop"], geo["bx"], geo["by"]
    static = {"body": body, "plate": plate, "cover": cover, "cap": cap, "ring": ring}
    print(f"\n[{tag}] 1. Badge at rest: no feature overlaps any part (min gap, mm)")
    for f in feats:
        s = f.solid()
        vol = sum((s ^ m).volume() for m in static.values())
        gaps = {k: s.min_gap(m, 3.0) for k, m in static.items()}
        k = min(gaps, key=gaps.get)
        check(vol < 1e-3, f"{f.name:26s} overlap {vol:.4f} mm^3", f"gap {gaps[k]:.2f} to {k}")

    print(f"\n[{tag}] 2. BOOT: cap on a flexure, stem through the plate onto the actuator")
    target = f"{c.BUTTON} actuator"
    act = next(f for f in feats if f.name == target)
    def hits(f, dz): return sum((f.solid(dz) ^ m).volume() for m in static.values()) > 1e-4
    for f in feats:
        lo, hi = 0.0, 2.0
        if not hits(f, hi):
            r = math.inf
        else:
            while hi - lo > 0.005:
                mid = (lo + hi)/2
                lo, hi = (mid, hi) if not hits(f, mid) else (lo, mid)
            r = lo
        if f.name == target:
            check(abs(r - G) < 0.02, f"{f.name:26s} meets the stem tip after G = {G}", f"{r:.2f}")
        else:
            check(r > G + 0.1, f"{f.name:26s} room behind it > G + 0.1", f"{r:.2f}" if r < math.inf else "nothing behind it")
    click = G + c.SW_TRAVEL
    check(click >= 0.5, "cap travel to the click >= 0.5", f"{click:.2f} = gap {G} + switch {c.SW_TRAVEL}")
    others = {"body": body, "plate": plate, "cover (fixed)": cover_fixed, "ring": ring}
    for d, label in ((click, "at the click"), (stop - 0.02, "just short of the stop")):
        cm = cap.translate([0, 0, -d]); tm = tongue.translate([0, 0, -d])
        hit = sum((cm ^ m).volume() + (tm ^ m).volume() for m in others.values())
        check(hit < 1e-3, f"cap + tongue pushed {d:.2f} ({label}) clear the body, plate, cover", f"{hit:.4f} mm^3")
        bad = [f.name for f in feats if f.name != target and (cm ^ f.solid()).volume() > 1e-4]
        check(not bad, f"stem pushed {d:.2f} touches no badge feature but BOOT", ", ".join(bad) or "none")
    v = (cap.translate([0, 0, -click]) ^ act.solid()).volume()
    check(v > 1e-3, f"stem pushed {click:.2f} reaches the actuator by its full travel", f"{v:.3f} mm^3 overlap")
    v0 = (cap.translate([0, 0, -(G - 0.02)]) ^ act.solid()).volume()
    check(v0 < 1e-4, f"stem pushed {G - 0.02:.2f} not yet touching it (no preload at rest)", f"{v0:.4f} mm^3")
    s1 = (cap.translate([0, 0, -(stop + 0.02)]) ^ cover_fixed).volume()
    check(s1 > 1e-3, f"cap rim lands on the cover at {stop:.2f} (hard stop)", f"{s1:.3f} mm^3 past it")
    gap_tip = min(f.solid().min_gap(cap, 2.0) for f in feats if f.name != target)
    check(gap_tip > 0.05, "stem tip clears the header envelope and switch body", f"min gap {gap_tip:.2f}")
    check((BOOT_HOLE - STEM_D)/2 >= 0.4 - 1e-9,"stem in the plate hole: radial clearance >= 0.4", f"{(BOOT_HOLE - STEM_D)/2:.2f}")
    L = TONGUE_L
    eps = 3*TONGUE_T*stop/(2*L**2)
    k = E_PETG*TONGUE_W*TONGUE_T**3/(4*L**3)
    check(TONGUE_W >= 2.4 and TONGUE_T >= 1.2, "flexure section >= 2.4 x 1.2, bends in the print plane",
          f"{TONGUE_W} x {TONGUE_T}, L {L}")
    check(eps < STRAIN_MAX, f"flexure strain at the stop < {STRAIN_MAX:.0%}", f"{eps:.2%}")
    print(f"  [info] tongue rate {k:.1f} N/mm: {k*click:.1f} N at the click, plus the switch's own ~1.6 N")
    # print error in the stack (cover seat, pad, cap boss, stem) moves the tip. Too long: the tongue and the
    # switch share the interference, so BOOT is only held down (boot loader at power-up!) once the switch
    # gets SW_TRAVEL of it. Too short: the click must still come before the rim stop.
    k_sw = SW_FORCE/c.SW_TRAVEL
    held = c.SW_TRAVEL*(1 + k_sw/k) + G
    check(held >= 0.5, "stem may print this much too LONG before BOOT is held at rest", f"{held:.2f} mm")
    check(stop - click >= 0.3, "stem may print this much too SHORT and still click", f"{stop - click:.2f} mm")
    depth = geo["Z_BACK"] - (b.pcb_back_z + b.sw_cap_h)
    print(f"  [info] stem {STEM_D} into a hex {STEM_D - HEX_INTERF:.2f} AF (press); actuator {depth:.1f} below the cover face")

    print(f"\n[{tag}] 3. Header guides grip each header in x at rest (>= {c.MIN_ENGAGE} deep)")
    i, o = c.HDR_CLR, c.HDR_CLR + c.GUIDE_WALL
    for h in geo["hdrs"]:
        x0, y0, x1, y1 = h.outline.bounds()
        for wn, w in {"-x wall": rect(x0 - o, x0 - i, y0, y1), "+x wall": rect(x1 + i, x1 + o, y0, y1)}.items():
            g = plate ^ prism(w, -5, geo["FLOOR"])
            eng = b.hdr_top_z - bbox(g)[0, 2] if not g.is_empty() else 0.0
            span = bbox(g)[1, 1] - bbox(g)[0, 1] if not g.is_empty() else 0.0
            check(eng >= c.MIN_ENGAGE and span >= 5.0, f"{h.name} {wn}", f"engages {eng:.2f} deep over {span:.1f} of y")

    print(f"\n[{tag}] 4. Bezel lip, snap, cover, walls")
    probe = m3.Manifold.cylinder(c.LIP_T + 4, (b.active_d + 1)/2, (b.active_d + 1)/2, SEG).translate([0, 0, -c.LIP_T - 3])
    check(sum((probe ^ m).volume() for m in (body, ring)) < 1e-4, "window and ring clear the active display + 1",
          f"ring Ø{2*RING_IN:.1f} vs window Ø{2*(b.r - c.LIP_OVERLAP + c.LIP_BEVEL):.2f}")
    ring_lip = prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0)
    check((ring_lip ^ body).volume() > 0.5, "lip overlaps the glass edge (retains it)", f"{c.LIP_OVERLAP:.2f} per side")
    check(c.LIP_T >= 1.2, "nothing in front of the glass but the lip and the ring", f"lip {c.LIP_T}")
    for n1, m1, n2, m2 in (("body", body, "plate", plate), ("body", body, "cover", cover), ("plate", plate, "cover", cover),
                           ("plate", plate, "cap", cap), ("body", body, "cap", cap)):
        v = (m1 ^ m2).volume()
        check(v < 1e-3, f"{n1} and {n2} do not overlap", f"{v:.4f} mm^3")
    press = prism(circle(STEM_D/2 + 0.01).translate([bx, by]), geo["Z_CASE"], geo["Z_BACK"] + 0.01)
    v = ((cover ^ cap) - press).volume()
    vp = (cover ^ cap).volume()
    check(v < 1e-3, "cover and cap touch only in the stem's hex press fit", f"press {vp:.3f} mm^3, elsewhere {v:.4f}")
    vp = (body ^ ring).volume()
    v_out = sum(((body ^ ring) ^ cyl_z(x, y, -5, 5, PEG_D + 0.2, 32)).volume() for x, y in geo["pegs"])
    check(vp - v_out < 1e-3, "body and ring touch only in the four peg press fits", f"press {v_out:.3f} mm^3")
    s = (body ^ plate.translate([0, 0, geo["bh_p"]])).volume()
    check(s > 1.0, "plate pulled back one bead height interferes (it snaps)", f"{s:.1f} mm^3")
    check(abs(bbox(cover)[1, 2] - geo["Z_BACK"]) < 1e-6, "cover flush with the slab back", f"z {geo['Z_BACK']:.2f}")
    wall = geo["boss_tip"] - b.tip_y
    check(abs(wall - 2.95) < 0.05, "wall in front of the port is the case's (never thickened)", f"{wall:.2f}")
    check(SHELL_L - wall >= 3.5, "plug shell engages the port >= 3.5", f"{SHELL_L - wall:.2f} of {SHELL_L}")
    holes = union(prism(hex_cs(PEG_D).translate([x, y]).offset(c.MIN_WALL, Round), -c.LIP_T, -c.LIP_T + PEG_L + 0.2)
                  for x, y in geo["pegs"])
    v = (holes ^ prism(geo["bore_xy"], 0.0, 20)).volume()
    check(v < 1e-3, "ring peg holes keep >= 1.2 from the bore and tab pocket",
          f"{PEG_R - PEG_D/2/math.cos(math.pi/6) - geo['R_BORE']:.2f} to the bore")
    check(geo["bay_z0"] + c.LIP_T >= c.MIN_WALL, "bay front wall (behind the grille)", f"{geo['bay_z0'] + c.LIP_T:.2f}")
    sk = min(math.hypot(x, y) for x, y in geo["screws"]) - SCREW_TAP/2 - geo["R_REAR"]
    check(sk >= c.MIN_WALL, "screw holes clear of the plate counterbore", f"{sk:.2f}")
    sr = min(math.dist(s, p) for s in geo["screws"] for p in geo["pegs"]) - SCREW_TAP/2 - PEG_D/2/math.cos(math.pi/6)
    check(sr >= c.MIN_WALL, "screw holes clear of the ring peg holes", f"{sr:.2f}")
    check(geo["tap_z0"] + c.LIP_T >= c.MIN_WALL, "front skin under the screw holes", f"{geo['tap_z0'] + c.LIP_T:.2f}")
    cov_t = COVER_T - 0.3
    check(cov_t >= c.MIN_WALL, "cover over the plate", f"{cov_t:.2f}")


def plug_solids(b, geo):
    tip = geo["boss_tip"]
    shell = box(-SHELL_W/2, SHELL_W/2, tip - SHELL_L, tip, b.port_z - SHELL_T/2, b.port_z + SHELL_T/2)
    body = box(-PLUG_W/2, PLUG_W/2, tip, tip + PLUG_L, b.port_z - PLUG_T/2, b.port_z + PLUG_T/2)
    return shell, body


def plug_checks(tag, b, geo, parts, cable):
    print(f"\n[{tag}] 5. Plug path: shell in the slot, overmould in the bay, cable out")
    shell, pbody = plug_solids(b, geo)
    out = shell ^ prism(rect(-50, 50, b.tip_y, 100), -50, 50)              # the part of the shell outside the port
    for nm, s in (("shell (outside the port)", out), ("overmould 12 x 8 x 22", pbody), ("cable", cable)):
        vol = sum((s ^ m).volume() for m in parts.values())
        gaps = {k: s.min_gap(m, 4.0) for k, m in parts.items()}
        k = min(gaps, key=gaps.get)
        check(vol < 1e-3, f"{nm:26s} clear", f"overlap {vol:.4f}, gap {gaps[k]:.2f} to {k}")
    # before it is pushed home, the whole plug (shell + overmould) sits in the bay, shell tip at the boss
    pre_in = (shell + pbody).translate([0, SHELL_L, 0])
    vol = sum((pre_in ^ m).volume() for m in parts.values())
    check(vol < 1e-3, "whole plug fits in the bay before it is pushed onto the port",
          f"{SHELL_L + PLUG_L:.2f} long, overlap {vol:.4f}")


# ---- stability (stand) ---------------------------------------------------------------------
def mass_props(parts):
    """parts: [(world manifold or None, grams if fixed, point)] -> total grams, CG (world)."""
    m_tot, mom = 0.0, np.zeros(3)
    for man, grams, pt in parts:
        if man is not None:
            tm = to_mesh(man)
            grams = tm.volume/1000*1.27*FILL
            pt = tm.center_mass
        m_tot += grams; mom += grams*np.asarray(pt)
    return m_tot, mom/m_tot


def convex_hull(pts):
    """Andrew's monotone chain; CCW, no repeated end point."""
    P = sorted(set(map(tuple, pts)))
    cross = lambda o, a, b: (a[0] - o[0])*(b[1] - o[1]) - (a[1] - o[1])*(b[0] - o[0])
    lo, hi = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return [np.array(p) for p in lo[:-1] + hi[:-1]]


def tip_angle(cg, mass_g, hull, P, F_dir, F_mag):
    """Largest desk tilt (deg) before tipping, for the worst tilt direction, with the cable force.
    hull: support polygon, CCW."""
    W = mass_g/1000*9.81
    def stable(alpha, phi):
        g = W*np.array([math.sin(alpha)*math.cos(phi), math.sin(alpha)*math.sin(phi), -math.cos(alpha)])
        Fc = F_mag*np.asarray(F_dir)
        Ft = g + Fc
        Mt = np.cross(cg, g) + np.cross(P, Fc)
        if Ft[2] >= 0: return False
        p = np.array([-Mt[1]/Ft[2], Mt[0]/Ft[2]])
        for i in range(len(hull)):
            a, bb = hull[i], hull[(i + 1) % len(hull)]
            e = bb - a; n = np.array([e[1], -e[0]])
            if (p - a) @ n > 0: return False          # outside this edge (hull is CCW, n points out)
        return True
    worst = (90.0, None)
    for phi in np.radians(np.arange(0, 360, 10)):
        lo, hi = 0.0, math.radians(60)
        if not stable(0.0, phi): return 0.0, math.degrees(phi)
        while hi - lo > 1e-3:
            mid = (lo + hi)/2
            lo, hi = (mid, hi) if stable(mid, phi) else (lo, mid)
        if math.degrees(lo) < worst[0]: worst = (math.degrees(lo), math.degrees(phi))
    return worst


# ---- renders -----------------------------------------------------------------------------
GREY, GREY_D, ORANGE, BLACK, SCREEN, STEEL, DARK, DESK, MON, SCRN, CABLE = (
    (0.84, 0.85, 0.86), (0.70, 0.71, 0.73), (0.98, 0.40, 0.08), (0.07, 0.07, 0.08), (0.10, 0.14, 0.24),
    (0.72, 0.73, 0.76), (0.20, 0.20, 0.22), (0.93, 0.92, 0.89), (0.12, 0.12, 0.14), (0.16, 0.20, 0.30),
    (0.14, 0.14, 0.15))
INK = (0.42, 0.43, 0.45)
R = lambda m: m.refine_to_length(1.5)


def badge_visual(b, c, feats):
    disc = feats[0].solid()
    screen = prism(circle(b.active_d/2), -0.02, 0.0)
    return [(disc, BLACK), (screen.translate([0, 0, -0.01]), SCREEN)]


def main():
    b, c = Badge(), Case()
    os.makedirs(STL, exist_ok=True); os.makedirs(PNG, exist_ok=True)
    feats, case_cuts, plate, geo = head_core(b, c)
    head_cuts, cover, cover_fixed, tongue, cap, ring = head_parts(b, c, geo)
    cuts = case_cuts + head_cuts
    print(f"Grid {M:g} mm. Head {2*HW:g} x {2*HW:g}, slab face {2*HW:g} x {Y_BOT - Y_TOP:g}; "
          f"boss tip y {geo['boss_tip']:.2f}; back face z {geo['Z_BACK']:.2f}")

    # ================= STAND =================
    F, sbody, foot_part, feet_w = build_stand(b, c, geo, cuts)
    head_checks("stand", b, c, feats, sbody, plate, cover, cover_fixed, tongue, cap, ring, geo)
    pts, s1 = cable_path_stand(b, F, geo)
    cable_w = tube(pts, CABLE_D)
    feet_b = [F.badge(f) for f in feet_w]
    parts = {"body": sbody, "cover": cover, "cap": cap, "feet": union(feet_b)}
    plug_checks("stand", b, geo, parts, F.badge(cable_w))
    check(s1 >= 0, "cable turns back within the bay (straight run before the bend >= 0)", f"{s1:.1f} mm, bend R {BEND_R}")

    print("\n[stand] 6. Stability: tip angle with the badge and a 1 N cable pull at the exit")
    world_parts = [(F.world(sbody), 0, 0), (F.world(cover), 0, 0), (F.world(plate), 0, 0), (F.world(cap), 0, 0),
                   (F.world(ring), 0, 0)] + [(f, 0, 0) for f in feet_w] + [(None, BADGE_G, F.pt([0, 0, 2.5]))]
    mass, cg = mass_props(world_parts)
    feet_xy = []
    for x, y in STAND_FEET:
        for a in np.linspace(0, 2*math.pi, 12, endpoint=False):
            feet_xy.append((x + (FEET_D/2 - PRESS)*math.cos(a), y + (FEET_D/2 - PRESS)*math.sin(a)))
    hull = convex_hull(feet_xy)
    wb = bbox(F.world(sbody))
    exit_y = bbox(F.world(sbody) ^ box(-200, 200, -200, 200, -1, FEET_PROUD + 0.5))[1, 1]   # back edge at the desk
    P = np.array([0.0, exit_y, CABLE_D/2])
    worst = (90.0, None, None)
    # the cable lies on the desk, so it pulls along the desk, in any direction
    dirs = [(math.cos(a), math.sin(a), 0.0) for a in np.radians(np.arange(0, 360, 15))]
    for dvec in dirs:
        ang, phi = tip_angle(cg, mass, hull, P, dvec, CABLE_PULL)
        if ang < worst[0]: worst = (ang, phi, dvec)
    free, _ = tip_angle(cg, mass, hull, P, (0, 1, 0), 0.0)
    up30 = min(tip_angle(cg, mass, hull, P, (math.cos(a)*0.866, math.sin(a)*0.866, 0.5), CABLE_PULL)[0]
               for a in np.radians(np.arange(0, 360, 15)))
    print(f"  [info] mass ~{mass:.0f} g incl. the {BADGE_G:g} g badge, parts at {FILL:.0%} solid; CG at X {cg[0]:.1f}, "
          f"Y {cg[1]:.1f}, Z {cg[2]:.1f} mm; footprint {wb[1,0]-wb[0,0]:.0f} x {wb[1,1]-wb[0,1]:.0f}")
    check(free >= 20.0, "tip angle, no cable, worst direction >= 20 deg", f"{free:.1f} deg")
    check(worst[0] >= 20.0, "tip angle with 1 N cable pull, worst pull and tilt >= 20 deg",
          f"{worst[0]:.1f} deg (tilt toward {worst[1]:.0f} deg, pull {np.round(worst[2], 2).tolist()})")
    h_desk = (F.world(sbody) ^ box(-200, 200, -200, 200, -10, FEET_PROUD - 0.01)).volume()
    check(h_desk < 1e-3, "only the feet touch the desk", f"body below the feet {h_desk:.4f} mm^3")
    print(f"  [info] a 1 N pull 30 deg UP (cable to a raised port) leaves {up30:.1f} deg; sliding: friction "
          f"{0.3*mass/1000*9.81:.2f} N on PETG feet vs a 1 N pull -- see README")

    # ================= CLIP =================
    cbody = build_clip(b, c, geo, cuts)
    head_checks("clip", b, c, feats, cbody, plate, cover, cover_fixed, tongue, cap, ring, geo)
    shell, pbody = plug_solids(b, geo)
    cab_c = tube([np.array([0, geo["boss_tip"] + PLUG_L, b.port_z]), np.array([0, geo["boss_tip"] + PLUG_L + 60, b.port_z])], CABLE_D)
    plug_checks("clip", b, geo, {"body": cbody, "cover": cover, "cap": cap}, cab_c)

    print("\n[clip] 6. Grip: monitor edge range, nothing on the screen, clamp force")
    cw = clip_world(cbody)
    for e in (EDGE_MIN, 20.0, EDGE_MAX):
        mon = box(-300, 0, 0, e, -300, 300)
        sl, kn, sc = slider_at(e), knob_at(e), screw_at(e)
        v = sum((mon ^ m).volume() for m in (cw, sl, kn, sc))
        vb = sum((cw ^ m).volume() for m in (sl, kn)) + (sl ^ kn).volume()
        pad_gap = mon.min_gap(sl, 1.0)
        tongue_in = (sl ^ box(CH_X0, CH_X1, -100, Y_END, ZC - 20, ZC + 20)).volume()/(sl ^ box(-0.2, CH_X1, -100, 200, -100, 100)).volume()
        screw_ok = (sc ^ cw).volume()
        check(v < 1e-3 and vb < 1e-3 and pad_gap < 0.01, f"edge {e:4.1f}: jaws on the monitor, slider and knob clear the body",
              f"monitor overlap {v:.4f}, parts {vb:.4f}, pad gap {pad_gap:.2f}")
        check(screw_ok < 1e-3, f"edge {e:4.1f}: lock screw runs in the slot", f"{screw_ok:.4f} mm^3")
        check(tongue_in > 0.8, f"edge {e:4.1f}: tongue inside the channel", f"{tongue_in:.0%}")
    screen = box(-300, -LIP - 0.01, -50, -0.01, -300, 300)
    v = sum((screen ^ m).volume() for m in (cw, slider_at(20.0)))
    check(v < 1e-3, f"nothing in front of the monitor beyond the {LIP:g} mm lip (screen untouched)", f"{v:.4f} mm^3")
    check(bbox(cw)[0, 0] >= -LIP - 1e-6, "lip reach from the monitor edge", f"{-bbox(cw)[0, 0]:.1f} mm")
    Fc, eps, L, w = finger_force(GAP)
    Fh, _, _, _ = finger_force(GAP/2)
    check(FINGER_T >= 1.2 and w >= 2.4, "finger section >= 2.4 x 1.2, bends in the print plane", f"{w:.1f} x {FINGER_T}, L {L:.1f}")
    check(eps < STRAIN_MAX, f"finger strain with the gap closed < {STRAIN_MAX:.0%}", f"{eps:.2%}")
    cm = clip_world(cbody)
    cmass, ccg = mass_props([(cm, 0, 0), (clip_world(cover), 0, 0), (clip_world(plate), 0, 0),
                             (slider_at(20.0), 0, 0), (knob_at(20.0), 0, 0), (None, BADGE_G, [OX, 0, 0])])
    Wc = cmass/1000*9.81
    load = Wc + CABLE_PULL                                  # cable hangs straight down from the plug, X = OX
    # the off-edge load turns the clip in the screen plane; the spine's foot bears on the monitor's side
    # face, and the jaws' friction must carry that side force as well as the load itself
    moment = Wc*ccg[0] + CABLE_PULL*OX
    lever = (ZT + ZC)/2 - bbox(cw)[0, 2]                    # jaw centre to the spine's bottom
    Ne = moment/lever
    need = math.hypot(load, Ne)
    sf_half, sf_full = 2*MU*Fh/need, 2*MU*Fc/need
    print(f"  [info] clip ~{cmass:.0f} g with badge, CG {ccg[0]:.0f} mm out from the edge; load {load:.2f} N; "
          f"side reaction {Ne:.2f} N; friction needed {need:.2f} N")
    check(sf_half >= 2.0, "grip safety factor, gap half closed (0.5 mm) >= 2", f"{sf_half:.1f} ({Fh:.1f} N clamp, mu {MU})")
    print(f"  [info] gap closed (1.0 mm): {Fc:.1f} N clamp, safety factor {sf_full:.1f}")

    # ================= export =================
    print()
    flip = lambda zt: (lambda m: m.rotate([180, 0, 0]).translate([0, 0, zt]))
    up = lambda m: m.translate([0, 0, -bbox(m)[0, 2]])
    export(sbody, STL + "TE stand - body.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(cbody, STL + "TE clip - body.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(slider_at(EDGE_MIN), STL + "TE clip - rear jaw.stl", up)
    export(knob_at(EDGE_MIN), STL + "TE clip - knob (orange).stl", lambda m: up(m.rotate([180, 0, 0])))
    export(foot_part, STL + "TE stand - foot (orange, print 4).stl", up)
    export(plate, STL + "TE - back plate.stl", lambda m: up(m.rotate([180, 0, 0])))
    export(cover, STL + "TE - back cover.stl", lambda m: up(m.rotate([180, 0, 0])))
    export(cap, STL + "TE - BOOT cap (orange).stl", lambda m: up(m.rotate([180, 0, 0])))
    export(ring, STL + "TE - trim ring (orange).stl", up)

    if "--no-render" not in sys.argv:
        renders(b, c, feats, geo, F, sbody, cbody, plate, cover, cover_fixed, tongue, cap, ring, feet_w, cable_w, pts)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


def render2(parts, path, elev=18, azim=-55, title="", zoom=1.0, light=None, center=None, figsize=(9, 9)):
    """pod/render.py, plus: edges drawn in the face colour (no seams on big flat faces), a key light
    that follows the camera (back views are lit too), zoom, and an optional fixed centre."""
    fig = plt.figure(figsize=figsize, dpi=110); ax = fig.add_subplot(111, projection="3d")
    ea, aa = math.radians(elev), math.radians(azim)
    cam = np.array([math.cos(ea)*math.cos(aa), math.cos(ea)*math.sin(aa), math.sin(ea)])
    side = np.array([-math.sin(aa), math.cos(aa), 0.0])
    L = np.array(light, float) if light is not None else cam + 0.55*side*-1 + np.array([0, 0, 0.9])
    L /= np.linalg.norm(L)
    T_all, C_all = [], []
    for man, rgb in parts:
        mm = man.to_mesh()
        v = np.asarray(mm.vert_properties)[:, :3]; f = np.asarray(mm.tri_verts)
        if len(f) == 0: continue
        T = v[f]
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
        shade = 0.34 + 0.62*np.clip(n @ L, 0, 1) + 0.10*np.clip(n[:, 2], 0, 1)
        T_all.append(T); C_all.append(np.clip(np.array(rgb)[None, :]*shade[:, None], 0, 1))
    T = np.concatenate(T_all); C = np.concatenate(C_all)
    pc = Poly3DCollection(T, facecolors=C, edgecolors=C, linewidths=0.35, zsort="average")
    ax.add_collection3d(pc)
    V = T.reshape(-1, 3)
    cc = (V.max(0) + V.min(0))/2 if center is None else np.asarray(center, float)
    r = (V.max(0) - V.min(0)).max()/2*1.02/zoom
    ax.set_xlim(cc[0] - r, cc[0] + r); ax.set_ylim(cc[1] - r, cc[1] + r); ax.set_zlim(cc[2] - r, cc[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    if title: fig.suptitle(title, fontsize=11, y=0.95)
    fig.subplots_adjust(0, 0, 1, 1); fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


def ink(cs, z_floor, back=False):
    """Display only: the shadow at the bottom of a deboss, so the graphics read in a render."""
    return prism(cs, z_floor, z_floor + 0.3) if back else prism(cs, z_floor - 0.3, z_floor)


def renders(b, c, feats, geo, F, sbody, cbody, plate, cover, cover_fixed, tongue, cap, ring, feet_w, cable_w, pts):
    shell, pbody = plug_solids(b, geo)
    Zb = geo["Z_BACK"]
    screws = union(cyl_z(x, y, Zb, Zb + HEAD_H, HEAD_D, 24) -
                   prism(hex_cs(2.5).translate([x, y]), Zb + HEAD_H - 1.5, Zb + HEAD_H + 1) for x, y in geo["screws"])
    head = [(cover, GREY), (cap, ORANGE), (ring, ORANGE), (shell, STEEL), (pbody, DARK), (screws, DARK),
            (ink(geo["back_gfx"], Zb - DEBOSS, back=True), INK)] + badge_visual(b, c, feats)
    W = lambda L: [(R(m), col) for m, col in L]
    ff = -c.LIP_T + DEBOSS

    # ===== stand
    st = [(F.world(m), col) for m, col in [(sbody, GREY), (ink(geo["gfx_stand"], ff), INK)] + head] + \
         [(f, ORANGE) for f in feet_w] + [(cable_w, CABLE)]
    desk = box(-55, 55, -25, 95, -2, 0)
    render2(W(st + [(desk, DESK)]), PNG + "stand-hero.png", elev=16, azim=-58, zoom=1.45, center=[0, 25, 40],
            title="TE stand 01: 15 deg lean, orange ring, the plug hangs behind a dot grille")
    render2(W(st), PNG + "stand-front.png", elev=3, azim=-90, zoom=1.0,
            title="Stand from the front: 56 x 88 face on a 4 mm grid; ring, grille, joint line, '01'")
    render2(W(st + [(desk, DESK)]), PNG + "stand-back.png", elev=22, azim=128, zoom=1.35, center=[0, 25, 40],
            title="From behind: four M3 hex screws, BOOT cap on its flexure tongue, cable out between the cheeks")

    def sect(xc, path, title, crop=None, frame=F.world, zoom=1.0, azim=180, cap_d=0.0, cable=True):
        L = [(sbody if frame == F.world else cbody, GREY), (plate, GREY_D), (cover_fixed, GREY),
             (tongue.translate([0, 0, -cap_d]), GREY), (cap.translate([0, 0, -cap_d]), ORANGE), (ring, ORANGE),
             (shell, STEEL), (pbody, DARK)]
        L += [(f.solid(), BLACK if f.name == "disc + tab" else (0.20, 0.62, 0.30) if f.name == "BOOT actuator"
               else (0.55, 0.78, 0.58) if f.name.startswith("BOOT") else (0.93, 0.93, 0.88))
              for f in feats if not f.name.startswith("plug")]
        out = []
        for m, col in L:
            m = frame(m).trim_by_plane([1, 0, 0], xc)
            if crop is not None: m = m ^ crop
            if not m.is_empty(): out.append((R(m), col))
        if cable:
            cab = cable_w.trim_by_plane([1, 0, 0], xc)
            if not cab.is_empty(): out.append((R(cab), CABLE))
        render2(out, path, elev=0, azim=azim, title=title, zoom=zoom, light=(-1, 0.2, 0.5),
                figsize=(9, 9) if crop is None else (9, 7))
    sect(0.0, PNG + "stand-section.png", "Stand cut down the middle: 3.0 wall + slot, plug in the bay, cable bends out the back")
    # BOOT detail in the head frame (crown down, upright), at rest and at the click
    Hf = lambda m: m.rotate([-90, 0, 0])
    bx, by = geo["bx"], geo["by"]
    crop = box(bx - 0.01, bx + 4, 2.5, Zb + geo["stop"] + CAP_T + 1.5, -by - 9, -by + 9)
    click = G + c.SW_TRAVEL
    sect(bx, PNG + "boot-rest.png", f"BOOT at rest (cut at x {bx:+.1f}): stem tip {G} behind the switch (green), cap rim "
         f"{geo['stop']:.2f} off the cover", crop, Hf, 1.0, cable=False)
    sect(bx, PNG + "boot-pressed.png", f"BOOT pressed {click:.2f}: switch clicked, tongue flexed, rim still "
         f"{geo['stop'] - click:.2f} from its stop", crop, Hf, 1.0, cap_d=click, cable=False)

    # ===== clip
    e = 20.0
    cw = clip_world(cbody)
    sl, kn = slider_at(e), knob_at(e)
    mon = box(-95, 0, 0, e, -135, 70)
    bez = 9.0
    scr = box(-95, -bez, -0.4, 0.0, -125, 70)
    zp = -(geo["boss_tip"] + PLUG_L)                       # plug end, world Z
    yp = b.port_z + OY
    cab = tube([np.array([OX, yp, zp]), np.array([OX, yp, zp - 20]), np.array([OX, yp + 6, zp - 34]),
                np.array([OX, yp + 26, zp - 44]), np.array([OX, yp + 50, zp - 50])], CABLE_D)
    cl = [(cw, GREY), (ink(geo["gfx_clip"], ff).rotate([-90, 0, 0]).translate([OX, OY, 0]), INK), (sl, GREY_D),
          (kn, ORANGE)] + [(clip_world(m), col) for m, col in head]
    render2(W(cl + [(cab, CABLE), (mon, MON), (scr, SCRN)]), PNG + "clip-hero.png", elev=14, azim=-52, zoom=1.55,
            center=[10, 10, -10], title="TE clip 02 on a 20 mm monitor edge: 6 mm lip on the bezel, orange lock knob")
    render2(W(cl + [(cab, CABLE), (mon, MON), (scr, SCRN)]), PNG + "clip-front.png", elev=2, azim=-90, zoom=1.5,
            center=[10, 0, -15], title="Clip from your chair: the face sits 3 mm proud, the screen is untouched")
    mon_b = box(-45, 0, 0, e, -95, 45)
    render2(W(cl + [(cab, CABLE), (mon_b, MON)]), PNG + "clip-back.png", elev=24, azim=58, zoom=1.2,
            title="Clip from behind: rear jaw + flex finger on the monitor back, lock knob, BOOT cap")
    cut = box(-200, 200, -200, 200, ZC - 2, ZC)
    monc = box(-30, 0, 0, e, ZC - 2, ZC)
    sc = screw_at(e)
    render2(W([(cw ^ cut, GREY), (sl ^ cut, GREY_D), (monc, MON), (sc ^ cut, STEEL)]), PNG + "clip-section.png",
            elev=89, azim=-90, zoom=1.0, light=(0.2, -0.3, 1.0), figsize=(11, 8),
            title="Clip cut through the tongue, seen from above: lip, channel, lock screw, flex finger and its 1.0 gap")
    # exploded head, front to back along the viewing axis (upright, crown down)
    E = 14.0
    ex = [(ring.translate([0, 0, -E]), ORANGE), (sbody, GREY)] + \
         [(m.translate([0, 0, 1.4*E]), col) for m, col in badge_visual(b, c, feats)] + \
         [(f.solid().translate([0, 0, 1.4*E]), (0.93, 0.93, 0.88)) for f in feats if f.name.startswith(("header", "JST", "RESET", "BOOT", "USB"))] + \
         [(plate.translate([0, 0, 2.6*E]), GREY_D), (cover.translate([0, 0, 3.6*E]), GREY), (screws.translate([0, 0, 4.4*E]), DARK),
          (cap.translate([0, 0, 4.6*E]), ORANGE)]
    render2(W([(F.world(m), col) for m, col in ex]), PNG + "exploded.png", elev=14, azim=-152, zoom=1.0,
            title="Assembly, front to back: ring (pegs), body, badge, plate (snaps), cover (4 x M3), cap (presses into the tongue)")
    # family + print layout
    chunk = box(-28, 0, -200, 200, -75, 45)
    fam = [(m.translate([-100, -10, 0]), col) for m, col in st + [(box(-45, 45, -20, 70, -2, 0), DESK)]] + \
          [(m.translate([20, 0, 45]), col) for m, col in cl + [(mon ^ chunk, MON), (scr ^ chunk, SCRN)]]
    render2(W(fam), PNG + "family.png", elev=12, azim=-66, zoom=1.2,
            title="One family: 01 stand and 02 clip share the head, ring, cover, cap and the grille bay")
    lay = []
    def place(m, col, dx, dy):
        lay.append((m.translate([-bbox(m)[0, 0] + dx, -bbox(m)[0, 1] + dy, -bbox(m)[0, 2]]), col))
    place(sbody.translate([0, 0, c.LIP_T]), GREY, 0, 0)
    place(cbody.translate([0, 0, c.LIP_T]), GREY, 64, 0)
    place(slider_at(EDGE_MIN), GREY_D, 150, 0)
    place(cover.rotate([180, 0, 0]), GREY, 150, 36)
    place(plate.rotate([180, 0, 0]), GREY_D, 150, 92)
    place(ring, ORANGE, 205, 0)
    place(cap.rotate([180, 0, 0]), ORANGE, 205, 56)
    place(knob_at(EDGE_MIN).rotate([180, 0, 0]), ORANGE, 222, 54)
    foot = chamfered([circle(FEET_D/2 - PRESS)], 0, FEET_PROUD + FEET_IN - 0.05, EDGE_C, 0)
    for i in range(4):
        place(foot, ORANGE, 205 + 11*i, 78)
    render2(W(lay), PNG + "print-layout.png", elev=50, azim=-72, zoom=1.15,
            title="Print layout as exported, no supports: grey PETG (left), orange PETG (right)")


if __name__ == "__main__":
    main()
