#!/usr/bin/env python3
"""
Braun family: a desk STAND and a monitor CLIP for the slim USB-only pocketwatch case (1.28 badge).

One body, two products. The body is a 54 x 90 block: a 54 square holding the round face and a
36 x 54 grille field beside it. The USB-C plug lies flat inside the body behind the grille, in a
trough open at the back, and the cable leaves out the back the way a Braun clock's cord does.
  STAND  the block on its long edge (landscape, crown pointing left, display rotated 90 in firmware).
         The trough turns down to the base, so the cable leaves at desk level.
  CLIP   the block on its short edge (portrait, crown down, display rotated 180), hung on the right
         edge of a monitor by a flat-printed C clamp that slides into a dovetail in the body's back.
         An M4 screw with a printed knob closes the rear pad onto the monitor: 8 to 32 mm.
One orange part: a 1.2 x 1.2 ring pressed into the face around the window, the same on both.

The case is the USB-only case from build_pocketwatch_usb.py, fused into the block: same bore, plate
counterbore, snap groove, tab pocket and 9.6 x 4.3 slot with 3.0 mm of wall in front of the port.
Changed: the bezel lip is 2.4 (was 1.2) with a 1.8 conical window, so the face is one flat plane
that prints on the bed and the orange ring groove keeps 1.2 of material over the tab pocket.
BOOT: the BOOT-hole plate, pressed from behind through the well with a 2 mm stylus.

Badge frame (as in build_pocketwatch.py): origin = glass centre, +y toward the USB-C tab, +x right
seen from the back, +z backward. World frame: X right as you look at it, Y away from you, Z up.

Run from the repo root:  ~/.venvs/cad/bin/python pocketwatch/styles/braun/build_braun.py [--no-render]
"""
import sys, math
from dataclasses import replace
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3, trimesh
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)
from build_pocketwatch_usb import boot_hole_plate, SHELL_LEN, MIN_PLUG_ENGAGE, PIN_D

STL = "stl/pocketwatch/styles/braun/"
PNG = "pocketwatch/styles/braun/renders/"

# ---- the module: every size is a multiple or a plain fraction of M --------------------------
M = 6.0
FACE = 9*M                         # 54: the face square, badge centre at its centre
GRILLE_L = 6*M                     # 36: the grille field beside (stand) / below (clip) the face
DEPTH = {"stand": 6*M, "clip": 4*M}
CORNER_R = M/2                     # every corner of the block outline
EDGE_CH = 0.6                      # every front and back edge
LIP_T, LIP_BEVEL = 0.4*M, 0.3*M    # bezel lip 2.4 in front of the glass, window opens 1.8 toward you
PITCH, HOLE_D, HOLE_DEPTH = M/2, M/3, 1.2     # grille: 9 x 15 blind holes
RING_R0, RING_W, RING_H = 21.0, 0.2*M, 0.2*M  # orange ring: inner radius, 1.2 wide (2 lines), 1.2 tall (4 layers)
RING_INT, RING_CLR = 0.10, 0.15    # ring stretched 0.10 over the groove's inner wall; 0.15 free outside
WELL_CLR = M/2                     # well behind the plate = plate outline + 3, room to pry the plate out
TROUGH_HALF, TROUGH_Z0 = 6.6, 0.5  # plug trough: 13.2 wide, floor 0.5 behind the glass plane
PLUG_W, PLUG_T, PLUG_L = 12.0, 8.0, 22.0      # straight USB-C plug overmould
SHELL_W, SHELL_T = 8.4, 2.6                   # its metal shell (SHELL_LEN 6.65 long)
CABLE_D, BEND_R = 4.0, 8.0
BADGE_G = 20.0                     # grams

# PETG and print settings used for masses and stresses
RHO, WALLS_MM, INFILL = 1.27e-3, 1.2, 0.15    # g/mm^3, 2 x 0.6 perimeters, 15 % infill
INFILL_STAND = 0.30               # the stand body is printed at 30 % so it is heavy enough
PETG_YIELD = 45.0                  # MPa, along the layers
MU = 0.3                           # PETG on a plastic monitor shell

# ---- the clip: world frame, monitor's right edge at X=0, screen plane Y=0 ----------------------
CZ0, CZ1 = -45.0, -27.0            # clamp height 18 = 3M, top at the groove's closed end
CZ = (CZ0 + CZ1)/2
SPINE_X = 5.8                      # spine 0..5.8; the body's left face sits at X=6
LIP_REACH, JAW_T = 6.0, 3.0        # front lip over the bezel (same 6 mm as the pod clip)
JAW_Y0, JAW_Y1 = 37.0, 46.0        # rear jaw, 9 thick to hold the nut slot
SCREW_X = -4.2                     # inside the lip's reach, so the two clamp forces line up
EDGE_MIN, EDGE_MAX = 8.0, 32.0
PAD_D, PAD_T, PAD_HOLE, PAD_HOLE_DEPTH = 8.0, 4.0, 3.4, 3.0
M4_CLR, M4_LEN, M4_NUT_AF, M4_NUT_T, M4_HEAD_AF, M4_HEAD_T = 4.4, 40.0, 7.0, 3.2, 7.0, 2.8
NUT_Y0 = 39.75
KNOB_D, KNOB_H = 3*M, 1.5*M
BAR_X1, BAR_Y0, BAR_Y1 = 26.0, 15.2, 21.2
TAIL_XC, TAIL_ROOT, TAIL_DEPTH, TAIL_CLR = 16.0, 8.0, 3.0, 0.2
KNOB_TORQUE = 72.0                 # N mm: 8 N at the rim of an 18 mm knob, finger tight
SCREW_K = 0.2                      # torque coefficient, dry steel nut

# ---- frames -------------------------------------------------------------------------------------
def _mat(A, t): return np.hstack([np.array(A, float), np.array(t, float)[:, None]])
# stand: crown (+y) points left, badge +x points down, base on Z=0, block centred on X=0, face at Y=0
STAND_A, STAND_T = [[0, -1, 0], [0, 0, 1], [-1, 0, 0]], [GRILLE_L/2, LIP_T, FACE/2]
# clip: crown down, block's left face at X=6, face 9 mm in front of the screen plane, block top Z=27
CLIP_A, CLIP_T = [[1, 0, 0], [0, 0, 1], [0, -1, 0]], [FACE/2 + 6.0, -6.6, 0.0]
FRAMES = {"stand": (STAND_A, STAND_T), "clip": (CLIP_A, CLIP_T)}


def to_world(m, v):
    A, t = FRAMES[v]
    return m.transform(_mat(A, t))


def to_badge(m, v):
    A, t = FRAMES[v]
    Ai = np.array(A, float).T
    return m.transform(_mat(Ai, -Ai @ np.array(t, float)))


def pt_world(p, v):
    A, t = FRAMES[v]
    return np.array(A, float) @ np.array(p, float) + np.array(t, float)


def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def tube(points, r, seg=20):
    """A cable: capsules between consecutive points."""
    s = m3.Manifold.sphere(r, seg)
    return union(m3.Manifold.batch_hull([s.translate(list(p0)), s.translate(list(p1))])
                 for p0, p1 in zip(points[:-1], points[1:]))


def arc(c, u, w, r, n=8):
    """Quarter arc around centre c from c - r*w (heading u) to c + r*u (heading w)... as points."""
    c, u, w = (np.array(a, float) for a in (c, u, w))
    return [c + r*(math.sin(a)*u - math.cos(a)*w) for a in np.linspace(0, math.pi/2, n)]


def rounded(cs, r):
    """Round the convex corners only (a concave fillet would grow into whatever the part sits against)."""
    return cs.offset(-r, Round).offset(r, Round)


# ---- the body -----------------------------------------------------------------------------------
def build(b, c, variant):
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    R_REAR = R_BORE + 1.2                         # plate counterbore, as the USB case
    FLOOR = b.hdr_top_z + c.FLOAT
    Z_CASE = FLOOR + c.PLATE_T                    # plate back face
    bore_xy = feats[0].grown()
    pocket = circle(R_REAR) + bore_xy
    boss_tip = bore_xy.bounds()[3] + c.CASE_WALL  # the USB case's crown boss tip: 3.0 in front of the port
    front, back = -c.LIP_T, -c.LIP_T + DEPTH[variant]
    half, y_end = FACE/2, FACE/2 + GRILLE_L
    plug_end = boss_tip + PLUG_L

    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    keep["plug (metal shell)"] = keep["plug (metal shell)"] ^ box(-30, 30, 0, boss_tip + 0.5, -10, 20)
    all_keep = union(keep.values())

    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4

    outline = rounded(rect(-half, half, -half, y_end), CORNER_R)
    body = chamfered([outline], front, back, EDGE_CH, EDGE_CH)
    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    well_xy = pocket.offset(WELL_CLR, Round)
    cut = {
        "bore + tab pocket": prism(bore_xy, 0.0, Z_CASE + 0.01),
        "plate counterbore": prism(circle(R_REAR), FLOOR, Z_CASE + 0.01),
        "well": prism(well_xy, Z_CASE, back + 1),
        "window": window.translate([0, 0, front - 0.01]),
        "snap groove": groove_p,
        "badge keepouts": all_keep,
        "ring groove": prism(circle(RING_R0 + RING_W + RING_CLR) - circle(RING_R0), front - 1, front + RING_H),
    }
    hole = m3.Manifold.cylinder(HOLE_DEPTH + 1, HOLE_D/2, HOLE_D/2, 24)
    gy = half + GRILLE_L/2
    cut["grille"] = union(hole.translate([j*PITCH, gy + i*PITCH, front - 1]) for i in range(-4, 5) for j in range(-7, 8))
    if variant == "stand":     # trough to 6 short of the end, then a leg down (+x) to the base, open at the back
        cut["trough"] = prism(rect(-TROUGH_HALF, TROUGH_HALF, boss_tip, y_end - M), TROUGH_Z0, back + 1) + \
                        prism(rect(-TROUGH_HALF, half + 1, plug_end, y_end - M), TROUGH_Z0, back + 1)
    else:                      # straight out of the bottom; open at the back
        cut["trough"] = prism(rect(-TROUGH_HALF, TROUGH_HALF, boss_tip, y_end + 1), TROUGH_Z0, back + 1)
        cut["dovetail"] = to_badge(dovetail_groove(), "clip")
    body -= union(cut.values())

    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, m3.JoinType.Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    plate_xy = pocket.offset(-c.FIT_CLR - 0.03, Round)
    plate = prism(plate_xy, FLOOR, Z_CASE)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead_p
    plate += guides
    plate -= all_keep
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_cyl = m3.Manifold.cylinder(FLOOR + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([sw[c.BUTTON], b.sw_y, tip_z])
    plate += post_cyl - union(k for n, k in keep.items() if not n.startswith(c.BUTTON))
    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, FLOOR=FLOOR, Z_CASE=Z_CASE, bh_p=bh_p, groove_r_p=groove_r_p,
               sw=sw, post_cyl=post_cyl, boss_tip=boss_tip, front=front, back=back, plug_end=plug_end,
               y_end=y_end, bore_xy=bore_xy, plate_xy=plate_xy, well_xy=well_xy, cut=cut, hdrs=hdrs)
    plate_h, _, _ = boot_hole_plate(b, c, plate, geo)
    return feats, body, plate_h, geo


def orange_ring():
    return prism(circle(RING_R0 + RING_W) - circle(RING_R0 - RING_INT), 0.0, RING_H)


def plug_and_cable(geo, variant):
    """Badge frame. Shell into the port, overmould in the trough, then the cable out the back."""
    t, pe = geo["boss_tip"], geo["plug_end"]
    shell = prism(rect(-SHELL_W/2, SHELL_W/2, t - SHELL_LEN, t), 5.0 - SHELL_T/2, 5.0 + SHELL_T/2)
    mould = prism(rect(-PLUG_W/2, PLUG_W/2, t, pe), 5.0 - PLUG_T/2, 5.0 + PLUG_T/2)
    r, back = CABLE_D/2, geo["back"]
    if variant == "stand":   # turn down (+x) to desk level, then out the back along the desk
        x_desk = FACE/2 - r
        pts = [(0, pe, 5)] + arc((BEND_R, pe, 5), (0, 1, 0), (1, 0, 0), BEND_R)[1:]
        pts += arc((x_desk - 6, pe + BEND_R, 11), (1, 0, 0), (0, 0, 1), 6)
        pts += [(x_desk, pe + BEND_R, back + 45)]
    else:                    # turn backward, out of the open trough, then hang down behind the body
        pts = [(0, pe, 5)] + arc((0, pe, 5 + BEND_R), (0, 1, 0), (0, 0, 1), BEND_R)[1:]
        zb = back + 4
        pts += arc((0, pe + 2*BEND_R, zb - BEND_R + 0.0), (0, 0, 1), (0, 1, 0), BEND_R)
        pts += [(0, pe + 45, zb)]
    cable = tube([np.array(p, float) for p in pts], r)
    return shell, mould, cable, pts


# ---- the clip's clamp, knob, pad: world frame -----------------------------------------------------
def tail_profile(grow=0.0):
    xc, h, d = TAIL_XC, TAIL_ROOT/2, TAIL_DEPTH
    y_root = DEPTH["clip"] - LIP_T + CLIP_T[1]        # body back face in world Y (15)
    cs = m3.CrossSection([[(xc - h, BAR_Y0 + 0.5), (xc - h, y_root), (xc - h - d, y_root - d),
                           (xc + h + d, y_root - d), (xc + h, y_root), (xc + h, BAR_Y0 + 0.5)]])
    return cs.offset(grow, m3.JoinType.Miter, 4.0) if grow else cs


def dovetail_groove():
    """World frame. Open at the bottom of the body, closed at Z=CZ1 where the clamp's top rests."""
    zb = -(FACE/2 + GRILLE_L) - 1
    return prism(tail_profile(TAIL_CLR) + rect(TAIL_XC - TAIL_ROOT/2 - TAIL_CLR, TAIL_XC + TAIL_ROOT/2 + TAIL_CLR,
                                                    BAR_Y0 - 0.5, BAR_Y0 + 2), zb, CZ1)


def clamp():
    c_xy = rect(0, SPINE_X, -JAW_T, JAW_Y1) + rect(-LIP_REACH, 0.01, -JAW_T, 0) + rect(-12, 0.01, JAW_Y0, JAW_Y1) + \
           rect(SPINE_X - 0.01, BAR_X1, BAR_Y0, BAR_Y1)
    c_xy = rounded(c_xy, 1.0) - rect(-50, 0, 0, JAW_Y0)          # nothing of it inside the monitor's edge
    cl = prism(c_xy, CZ0, CZ1) + prism(tail_profile(), CZ0, CZ1)
    nut = box(SCREW_X - (M4_NUT_AF + 0.3)/2, SCREW_X + (M4_NUT_AF + 0.3)/2, NUT_Y0, NUT_Y0 + M4_NUT_T + 0.3,
              CZ - M4_NUT_AF/math.sqrt(3) - 0.1, CZ1 + 1)
    hole = m3.Manifold.cylinder(JAW_Y1 - JAW_Y0 + 2, M4_CLR/2, M4_CLR/2, 32).rotate([-90, 0, 0]).translate([SCREW_X, JAW_Y0 - 1, CZ])
    return cl - nut - hole


def knob():
    """Print frame: back on the bed, hex pocket for the M4 head open at the top. Fine flutes, Braun style."""
    k = m3.Manifold.cylinder(KNOB_H, KNOB_D/2, KNOB_D/2, 96)
    k -= union(m3.Manifold.cylinder(KNOB_H + 2, 0.6, 0.6, 12).translate([KNOB_D/2*math.cos(a), KNOB_D/2*math.sin(a), -1])
               for a in np.linspace(0, 2*math.pi, 24, endpoint=False))
    k -= m3.Manifold.cylinder(M4_HEAD_T + 0.2 + 1, (M4_HEAD_AF + 0.1)/math.sqrt(3), (M4_HEAD_AF + 0.1)/math.sqrt(3), 6) \
        .translate([0, 0, KNOB_H - M4_HEAD_T - 0.2])
    ch = 0.6                                          # 45 degrees top and bottom
    k ^= m3.Manifold.batch_hull([m3.Manifold.cylinder(KNOB_H - 2*ch, KNOB_D/2, KNOB_D/2, 96).translate([0, 0, ch]),
                                 m3.Manifold.cylinder(KNOB_H, KNOB_D/2 - ch, KNOB_D/2 - ch, 96)])
    return k


def pad():
    p = m3.Manifold.cylinder(PAD_T, PAD_D/2, PAD_D/2, 64)
    return p - m3.Manifold.cylinder(PAD_HOLE_DEPTH + 1, PAD_HOLE/2, PAD_HOLE/2, 32).translate([0, 0, PAD_T - PAD_HOLE_DEPTH])


def clamp_set(t):
    """Pad, screw, nut, knob placed (world) for a monitor edge t thick."""
    pd = pad().rotate([-90, 0, 0])                    # hole side toward +y (the screw)
    pd = pd.translate([SCREW_X, t, CZ])               # rotate(-90 about x): z -> y, spans y 0..PAD_T
    tip = t + PAD_T - PAD_HOLE_DEPTH
    head0 = tip + M4_LEN
    screw = m3.Manifold.cylinder(M4_LEN, 2.0, 2.0, 24).rotate([-90, 0, 0]).translate([SCREW_X, tip, CZ])
    screw += m3.Manifold.cylinder(M4_HEAD_T, M4_HEAD_AF/math.sqrt(3), M4_HEAD_AF/math.sqrt(3), 6).rotate([-90, 0, 0]) \
        .translate([SCREW_X, head0, CZ])
    nut = (m3.Manifold.cylinder(M4_NUT_T, M4_NUT_AF/math.sqrt(3), M4_NUT_AF/math.sqrt(3), 6).rotate([0, 0, 30])
           - m3.Manifold.cylinder(M4_NUT_T + 1, 2.0, 2.0, 24).translate([0, 0, -0.5])) \
        .rotate([-90, 0, 0]).translate([SCREW_X, NUT_Y0 + 0.15, CZ])
    kb = knob().rotate([90, 0, 0])                    # pocket (top, +z) now faces -y
    kb = kb.translate([SCREW_X, head0 + KNOB_H, CZ])  # pocket face flush with the head's underside
    return dict(pad=pd, screw=screw, nut=nut, knob=kb, tip=tip, head=head0)


# ---- checks -------------------------------------------------------------------------------------
def grams(m, infill=None):
    """Printed mass: perimeters over the whole surface, sparse infill inside."""
    infill = INFILL if infill is None else infill
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    shell = min(tm.volume, tm.area/2*WALLS_MM)
    return RHO*(shell + infill*(tm.volume - shell)), np.array(tm.center_mass)


def vol(a, b_):
    return (a ^ b_).volume()


def body_checks(b, c, v, feats, body, plate_h, geo, ring):
    print(f"\n[{v}] 1. At rest: no badge feature overlaps the body or the plate")
    for f in feats:
        if f.name.startswith("plug"): continue        # a 40 mm stand-in; the real plug is checked in 4
        s = f.solid()
        ov = vol(s, body) + vol(s, plate_h)
        gap = min(s.min_gap(body, 3.0), s.min_gap(plate_h, 3.0))
        check(ov < 1e-3, f"{f.name:26s} overlap {ov:.4f} mm^3", f"gap {gap:.2f}")

    print(f"\n[{v}] 2. Bezel: one flat face, glass behind a {c.LIP_T:.1f} lip")
    probe = m3.Manifold.cylinder(c.LIP_T + 2, (b.active_d + 1)/2, (b.active_d + 1)/2, SEG).translate([0, 0, -c.LIP_T - 1])
    win_d = 2*(b.r - c.LIP_OVERLAP)
    check(vol(probe, body) < 1e-4, f"window clears active display {b.active_d:.2f} + 1", f"window {win_d:.2f}, margin {win_d - b.active_d - 1:.2f}")
    lipring = prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0)
    check(vol(lipring, body) > 0.5, "lip overlaps the glass edge (retains it)", f"{c.LIP_OVERLAP:.2f} per side")
    edge = math.degrees(math.atan2(b.r - c.LIP_OVERLAP + c.LIP_BEVEL - b.active_d/2, c.LIP_T))
    check(edge >= 45, "edge pixels visible from >= 45 degrees off axis", f"{edge:.0f} degrees")

    print(f"\n[{v}] 3. Back plate (BOOT-hole plate): snaps, flush with the well floor, goes in and out through the well")
    check(vol(body, plate_h) < 1e-3, "body and plate do not overlap", f"{vol(body, plate_h):.4f} mm^3")
    sn = vol(body, plate_h.translate([0, 0, geo["bh_p"]]))
    check(sn > 1.0, "plate pulled back one bead height interferes (it snaps)", f"{sn:.1f} mm^3")
    check(abs(bbox(plate_h)[1, 2] - geo["Z_CASE"]) < 1e-3, "plate back is the well floor", f"z {geo['Z_CASE']:.2f}, well {geo['back'] - geo['Z_CASE']:.2f} deep")
    room = prism(geo["plate_xy"].offset(2.0, Round), geo["Z_CASE"], geo["back"]) - geo["cut"]["well"]
    check(room.volume() < 1e-3, "plate + 2 mm all round passes through the well (pry room)", f"well = plate outline + {WELL_CLR + c.FIT_CLR:.2f}")

    print(f"\n[{v}] 4. USB-C: the case's 3.0 wall in front of the port is untouched, plug and cable path clear")
    wall = geo["boss_tip"] - b.tip_y
    check(wall <= 3.0 + 0.01, "wall in front of the port not thickened", f"{wall:.2f}")
    check(SHELL_LEN - wall >= MIN_PLUG_ENGAGE, f"shell engages the port >= {MIN_PLUG_ENGAGE}", f"{SHELL_LEN - wall:.2f} of {SHELL_LEN}")
    shell, mould, cable, _ = plug_and_cable(geo, v)
    slot = prism(rect(-SHELL_W/2, SHELL_W/2, b.tip_y, geo["boss_tip"]), 5 - SHELL_T/2, 5 + SHELL_T/2)
    for nm, s in (("metal shell through the slot", slot), (f"overmould {PLUG_W:g} x {PLUG_T:g} x {PLUG_L:g}", mould),
                  (f"cable Ø{CABLE_D:g}, bends R{BEND_R:g}", cable)):
        check(vol(s, body) < 1e-3, f"{nm} clear of the body", f"gap {s.min_gap(body, 5.0):.2f}")

    print(f"\n[{v}] 5. BOOT from behind: a Ø{PIN_D:g} stylus through the well and the plate hole")
    x, y = geo["sw"][c.BUTTON], b.sw_y
    top = b.pcb_back_z + b.sw_cap_h
    pin = lambda dz: m3.Manifold.cylinder(geo["back"] + 10 - (top - dz), PIN_D/2, PIN_D/2, 48).translate([x, y, top - dz])
    for dz, label in ((0.0, "at rest"), (c.SW_TRAVEL, f"pressed {c.SW_TRAVEL:.2f}")):
        hit = vol(pin(dz), body) + vol(pin(dz), plate_h)
        check(hit < 1e-3, f"stylus {label} touches neither body nor plate", f"{hit:.4f} mm^3")
    act = next(f for f in feats if f.name == f"{c.BUTTON} actuator")
    check(vol(pin(c.SW_TRAVEL), act.solid()) > 1e-3, "stylus pressed reaches the actuator", f"{geo['back'] - top:.1f} mm from the back face")

    print(f"\n[{v}] 6. Orange ring and walls")
    rg = ring.translate([0, 0, geo["front"]])
    grip = vol(rg, body)
    outer = rg - prism(circle(RING_R0 + 0.01), -10, 10)
    check(grip > 5.0 and vol(outer, body) < 1e-3, f"ring grips the inner wall only ({RING_INT} interference)", f"{grip:.1f} mm^3")
    check(RING_INT/RING_R0 < 0.02, "ring hoop strain < 2 %", f"{100*RING_INT/RING_R0:.2f} %")
    wfront = b.r - c.LIP_OVERLAP + c.LIP_BEVEL
    check(RING_R0 - wfront >= 1.2, "ring clear of the window bevel", f"{RING_R0 - wfront:.2f} of flat face between")
    walls = {"over the tab pocket, behind the ring groove": 0.0 - (geo["front"] + RING_H),
             "behind the grille holes, in front of the trough": TROUGH_Z0 - (geo["front"] + HOLE_DEPTH),
             "block side beside the well": FACE/2 - max(abs(geo["well_xy"].bounds()[0]), geo["well_xy"].bounds()[2]),
             "block side beside the ring groove": FACE/2 - (RING_R0 + RING_W + RING_CLR),
             "trough floor to the face": TROUGH_Z0 - geo["front"]}
    if v == "clip":
        g = geo["cut"]["dovetail"]
        walls["dovetail to the well"] = g.min_gap(geo["cut"]["well"], 5.0)
        walls["dovetail to the trough"] = g.min_gap(geo["cut"]["trough"], 5.0)
        walls["dovetail to the block side"] = FACE/2 - abs(TAIL_XC - CLIP_T[0]) - TAIL_ROOT/2 - TAIL_DEPTH - TAIL_CLR*1.5
    for nm, t in walls.items():
        check(t >= c.MIN_WALL - 1e-6, f"wall {nm} >= {c.MIN_WALL}", f"{t:.2f}")


def rot(e, th):
    e = e/np.linalg.norm(e); K = np.array([[0, -e[2], e[1]], [e[2], 0, -e[0]], [-e[1], e[0], 0]])
    return np.eye(3) + math.sin(th)*K + (1 - math.cos(th))*K @ K


def tip_angle(poly, com, W, P, F):
    """Smallest tilt about any edge of the support polygon at which weight + pull stop holding it."""
    out = []
    for i in range(len(poly)):
        A = np.array([*poly[i], 0.0]); B = np.array([*poly[(i + 1) % len(poly)], 0.0])
        e = (B - A)/np.linalg.norm(B - A)
        if np.linalg.norm(B - A) < 0.5: continue
        th = 0.0
        while th < 60.0:
            R = rot(e, math.radians(th))
            tau = np.cross(R @ (com - A), [0, 0, -W]) @ e + np.cross(R @ (P - A), F) @ e
            if tau >= 0: break
            th += 0.25
        out.append((th, A, B))
    return min(out, key=lambda o: o[0])


def stand_checks(b, c, body, plate_h, ring, geo):
    print(f"\n[stand] 7. Stability: tilt to tip about every edge of the footprint (body at {INFILL_STAND*100:.0f} % infill)")
    bw = to_world(body, "stand")
    badge_c = pt_world((0, 0, b.pcb_back_z/2), "stand")
    exit_pt = pt_world((FACE/2 - CABLE_D/2, geo["plug_end"] + BEND_R, geo["back"]), "stand")
    poly = np.array(bw.slice(0.15).hull().to_polygons()[0])
    check(exit_pt[2] < 3.0, "cable leaves the body at desk level, out the back", f"exit {exit_pt[2]:.1f} above the desk")
    res = {}
    for infill in (INFILL_STAND, INFILL):
        parts = [grams(bw, infill), grams(to_world(plate_h, "stand")), grams(to_world(ring.translate([0, 0, geo["front"]]), "stand"))]
        mass = sum(p[0] for p in parts) + BADGE_G
        com = (sum(p[0]*p[1] for p in parts) + BADGE_G*badge_c)/mass
        W = mass*9.81e-3
        th0 = tip_angle(poly, com, W, exit_pt, np.zeros(3))[0]
        pull = lambda azs: min((tip_angle(poly, com, W, exit_pt, np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0]))[0], a)
                               for a in azs)
        cone = min(pull(range(60, 121, 5)), (tip_angle(poly, com, W, exit_pt, np.array([0, 0, -1.0]))[0], "down"))
        res[infill] = (mass, com, th0, cone, pull(range(0, 360, 15)))
    mass, com, th0, cone, anyway = res[INFILL_STAND]
    print(f"  mass {mass:.0f} g (badge {BADGE_G:g} g), centre of mass {com[2]:.1f} above the desk, {com[1]:.1f} behind the face")
    check(th0 >= 20, "tip angle, weight only", f"{th0:.1f} degrees")
    check(cone[0] >= 20, "tip angle with 1 N on the cable, along it (back +-30 deg) or down",
          f"{cone[0]:.1f} degrees (worst: azimuth {cone[1]})")
    print(f"  info: a 1 N pull at the exit in ANY horizontal direction tips it after {anyway[0]:.1f} degrees (azimuth {anyway[1]})")
    m15 = res[INFILL]
    print(f"  info: at {INFILL*100:.0f} % infill: {m15[0]:.0f} g, weight only {m15[2]:.1f}, along the cable {m15[3][0]:.1f} degrees")
    return mass, com


def clip_checks(body_w, ring_w, plate_w, geo, b):
    print("\n[clip] 7. Monitor clamp: range, grip, screen, strength")
    cl = clamp()
    sets = {t: clamp_set(t) for t in (EDGE_MIN, 20.0, EDGE_MAX)}
    lo, hi = sets[EDGE_MIN], sets[EDGE_MAX]
    check(hi["tip"] <= NUT_Y0, f"at {EDGE_MAX:g} mm the screw still passes the whole nut", f"tip {hi['tip']:.1f} <= nut {NUT_Y0:.1f}")
    check(lo["head"] >= JAW_Y1, f"at {EDGE_MIN:g} mm the head is still behind the jaw (M4 x {M4_LEN:g})", f"{lo['head'] - JAW_Y1:.1f} to spare")
    check(EDGE_MAX + PAD_T <= JAW_Y0 - 0.5, f"at {EDGE_MAX:g} mm the pad clears the jaw", f"{JAW_Y0 - EDGE_MAX - PAD_T:.1f}")
    for t, s in sets.items():
        mon = box(-150, 0, 0, t, -140, 60)
        hits = {n: vol(mon, m) for n, m in (("body", body_w), ("ring", ring_w), ("plate", plate_w), ("clamp", cl),
                                            ("knob", s["knob"]), ("screw", s["screw"]), ("nut", s["nut"]))}
        check(sum(hits.values()) < 1e-3, f"{t:4.0f} mm edge: nothing enters the monitor", f"{sum(hits.values()):.4f} mm^3")
        touch = s["pad"].min_gap(mon, 1.0) < 0.01 and cl.min_gap(mon, 1.0) < 0.01
        check(touch, f"{t:4.0f} mm edge: pad and front lip both bear on it", "")
        others = [cl, s["knob"], s["nut"], body_w, ring_w, plate_w]      # the screw threads into the pad on purpose
        ov = sum(vol(s["pad"], m) for m in others) + vol(s["knob"], cl) + vol(s["screw"], body_w)
        check(ov < 1e-3, f"{t:4.0f} mm edge: pad, screw, knob collide with nothing", f"{ov:.4f} mm^3")
    front = box(-200, 200, -50, 0, -200, 200)
    reach = min(bbox((m ^ front))[0, 0] for m in (cl, body_w, ring_w) if not (m ^ front).is_empty())
    check(reach >= -LIP_REACH - 1e-6, f"in front of the screen only the lip, and only {LIP_REACH:g} over the bezel", f"reaches X {reach:.2f}")
    check(bbox(body_w)[0, 0] >= 0, "the gauge body sits beside the monitor, not over it", f"X >= {bbox(body_w)[0, 0]:.1f}")
    check(vol(cl, body_w) < 1e-3, "clamp and body do not overlap (0.2 dovetail clearance)", f"{vol(cl, body_w):.4f} mm^3")
    for d, nm in (((0, -0.5, 0), "forward"), ((-0.5, 0, 0), "toward the monitor"), ((0.5, 0, 0), "away"),
                  ((0, 0, -0.5), "down")):
        check(vol(cl, body_w.translate(list(d))) > 0.5, f"dovetail holds the body: 0.5 mm {nm} collides", "")

    # mass and loads
    parts = [grams(m) for m in (body_w, ring_w, plate_w, cl, sets[20.0]["knob"], sets[20.0]["pad"])]
    badge_c = pt_world((0, 0, b.pcb_back_z/2), "clip")
    mass = sum(p[0] for p in parts) + BADGE_G + 5.0               # + M4 x 40 screw and nut
    com = (sum(p[0]*p[1] for p in parts) + BADGE_G*badge_c + 5.0*np.array([SCREW_X, 50, CZ]))/(mass)
    W = mass*9.81e-3
    F = KNOB_TORQUE/(SCREW_K*4.0)
    cap = 2*MU*F
    print(f"  mass {mass:.0f} g, centre of mass X {com[0]:.1f} (outboard of the edge), clamp force {F:.0f} N "
          f"({KNOB_TORQUE:g} N mm on the knob, K {SCREW_K})")
    check(cap/(W + 1.0) >= 3, "friction grip vs weight + 1 N pull (two faces, mu 0.3)", f"safety factor {cap/(W + 1.0):.0f}")
    x_cable = CLIP_T[0]
    m_droop = W*com[0] + 1.0*x_cable
    m_hold = cap*(CZ1 - CZ0)/2                                    # jaw friction couple against the spine's top on the edge
    check(m_hold/m_droop >= 3, "droop moment: outboard weight + pull vs jaw couple", f"safety factor {m_hold/m_droop:.1f}")
    sp = F*(SPINE_X/2 - SCREW_X)/((CZ1 - CZ0)*SPINE_X**2/6)
    lip = F*(-SCREW_X)/((CZ1 - CZ0)*JAW_T**2/6)
    check(PETG_YIELD/sp >= 3, "spine bending stress, along the layers (clamp printed flat)", f"{sp:.1f} MPa, SF {PETG_YIELD/sp:.1f}")
    check(PETG_YIELD/lip >= 2.5, "front lip root bending, along the layers", f"{lip:.1f} MPa, SF {PETG_YIELD/lip:.1f}")
    return mass, com, sets


def main():
    b = Badge()
    c = replace(Case(), LIP_T=LIP_T, LIP_BEVEL=LIP_BEVEL)
    ring = orange_ring()
    out = {}
    for v in ("stand", "clip"):
        feats, body, plate_h, geo = build(b, c, v)
        sz = bbox(to_world(body, v)); sz = sz[1] - sz[0]
        print(f"\n===== {v.upper()}: body {sz[0]:.1f} x {sz[1]:.1f} x {sz[2]:.1f} mm (X x Y x Z, world)")
        body_checks(b, c, v, feats, body, plate_h, geo, ring)
        out[v] = (feats, body, plate_h, geo)
    out["stand_m"] = stand_checks(b, c, out["stand"][1], out["stand"][2], ring, out["stand"][3])
    fc, bc, pc, gc = out["clip"]
    out["clip_m"] = clip_checks(to_world(bc, "clip"), to_world(ring.translate([0, 0, gc["front"]]), "clip"),
                                to_world(pc, "clip"), gc, b)
    _, _, cable, _ = plug_and_cable(gc, "clip")
    check(vol(to_world(cable, "clip"), clamp()) < 1e-3, "[clip] cable clear of the clamp", "")

    print("\n8. Exports: watertight, no supports (print orientation)")
    flip = lambda g: (lambda m: m.rotate([0, 180, 0]).translate([0, 0, g["Z_CASE"]]))
    export(out["stand"][1], STL + "Braun stand - body.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(bc, STL + "Braun clip - body.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(clamp(), STL + "Braun clip - clamp.stl", lambda m: m.translate([0, 0, -CZ0]))
    export(knob(), STL + "Braun clip - knob.stl", lambda m: m)
    export(pad(), STL + "Braun clip - pad.stl", lambda m: m)
    export(ring, STL + "Braun - orange ring.stl", lambda m: m)
    export(pc, STL + "Braun - back plate (BOOT hole).stl", flip(gc))
    if "--no-render" not in sys.argv:
        renders(b, c, out, ring)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


OFF_WHITE, PLATE_C, CLAMP_C, ORANGE = (0.93, 0.92, 0.88), (0.86, 0.85, 0.81), (0.84, 0.84, 0.82), (0.96, 0.43, 0.10)
GLASS, WHITE, MOULD, SHELL, CABLE_C = (0.06, 0.06, 0.07), (0.97, 0.97, 0.95), (0.20, 0.20, 0.21), (0.72, 0.74, 0.77), (0.16, 0.16, 0.17)
BACKLIGHT = (0.45, 0.75, 0.5)
BEZEL_C, SCREEN_C, STEEL = (0.17, 0.17, 0.19), (0.07, 0.09, 0.14), (0.62, 0.64, 0.67)


def dial(v):
    """A Braun clock on the display, at 10:10, so the renders read as a clock. World frame, in front of the glass."""
    cx, cy, cz = pt_world((0, 0, 0), v)
    y = cy - 0.35
    parts = []
    for i in range(12):
        L = 3.6 if i % 3 == 0 else 2.4
        w = 1.1 if i % 3 == 0 else 0.7
        parts.append(box(-w/2, w/2, -0.15, 0.15, 14.6 - L, 14.6).rotate([0, 30*i, 0]))
    parts.append(box(-0.9, 0.9, -0.15, 0.15, -1.5, 8.5).rotate([0, 305, 0]))     # hour
    parts.append(box(-0.6, 0.6, -0.15, 0.15, -1.5, 12.8).rotate([0, 60, 0]))     # minute
    parts.append(m3.Manifold.cylinder(0.3, 1.4, 1.4, 24).rotate([90, 0, 0]).translate([0, 0.15, 0]))
    return union(parts).translate([cx, y, cz])


def scene(b, c, v, feats, body, plate_h, geo, ring, back=False):
    """back=True fills the blind grille holes: invisible from behind, and the painter's sort lets them show through."""
    W = lambda m: to_world(m, v)
    if back:
        body = body + (geo["cut"]["grille"] ^ prism(rect(-FACE/2, FACE/2, FACE/2, geo["y_end"]), geo["front"] + 0.3, geo["front"] + HOLE_DEPTH))
    shell, mould, cable, _ = plug_and_cable(geo, v)
    disc = next(f for f in feats if f.name == "disc + tab").solid()
    sc = [(W(body), OFF_WHITE), (W(ring.translate([0, 0, geo["front"]])), ORANGE), (W(plate_h), PLATE_C),
          (W(disc), GLASS), (dial(v), WHITE), (W(shell), SHELL), (W(mould), MOULD), (W(cable), CABLE_C)]
    if back:   # the face parts cannot be seen from behind; left in, the painter's sort ghosts them through the body
        sc[1], sc[4] = (sc[1][0], OFF_WHITE), (m3.Manifold(), WHITE)
    return sc


def R(parts, path, refine=1.2, **kw):
    render([(m.refine_to_length(refine), col) for m, col in parts if not m.is_empty()], path, **kw)


def renders(b, c, out, ring):
    # ---------------- stand
    feats, body, plate_h, geo = out["stand"]
    S = scene(b, c, "stand", feats, body, plate_h, geo, ring)
    R(S, PNG + "stand-hero.png", elev=16, azim=-58, zoom=1.25, title="Braun stand: 90 x 54 x 36, one orange ring, cord out the back at desk level")
    R(S, PNG + "stand-front.png", elev=0, azim=-90, zoom=1.3, title="Stand, as you see it (display rotated 90 degrees in firmware)")
    xf = pt_world((0, 0, 0), "stand")[0]
    R([(m.trim_by_plane([1, 0, 0], xf), col) for m, col in S], PNG + "stand-section-side.png", elev=0, azim=180, zoom=1.25,
      title="Stand cut through the face centre: 2.4 lip, glass, badge, plate in the well floor, 36 deep")
    zf = pt_world((0, 0, 0), "stand")[2]
    R([(m.trim_by_plane([0, 0, -1], -zf), col) for m, col in S], PNG + "stand-section-plug.png", elev=89, azim=-90, zoom=1.3,
      title="Stand cut at the plug axis, from above: shell through the 3.0 wall, plug in the trough, cable down and out")
    pin_x, pin_y = geo["sw"][c.BUTTON], b.sw_y
    top = b.pcb_back_z + b.sw_cap_h
    stylus = m3.Manifold.cylinder(geo["back"] + 30 - top, PIN_D/2, PIN_D/2, 24).translate([pin_x, pin_y, top])
    SB = scene(b, c, "stand", feats, body, plate_h, geo, ring, back=True)
    R(SB + [(to_world(stylus, "stand"), STEEL)], PNG + "stand-back.png", elev=14, azim=100, light=BACKLIGHT,
      title="Stand from behind: plate in the well, BOOT pressed through its hole with a 2 mm stylus")
    pr = [(body.translate([0, 0, c.LIP_T]), OFF_WHITE),
          (ring.translate([FACE/2 + 30, -10, 0]), ORANGE),
          (plate_h.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]]).translate([FACE/2 + 30, 40, 0]), PLATE_C)]
    R(pr, PNG + "stand-print-layout.png", elev=40, azim=-60,
      title="Stand, print layout: body face down, ring flat (orange), plate flat. No supports")

    # ---------------- clip
    feats, body, plate_h, geo = out["clip"]
    S = scene(b, c, "clip", feats, body, plate_h, geo, ring)
    t = 20.0
    cs = clamp_set(t)
    CL = [(clamp(), CLAMP_C), (cs["knob"], CLAMP_C), (cs["pad"], CLAMP_C), (cs["screw"], STEEL), (cs["nut"], STEEL)]
    mon = [(box(-60, 0, 0, t, -105, 45), BEZEL_C), (box(-60, -8, -0.4, 0.01, -97, 37), SCREEN_C)]
    R(mon + CL + S, PNG + "clip-hero.png", elev=14, azim=-52,
      title=f"Braun clip on a {t:.0f} mm monitor edge: 54 x 90 x 24, the same face, crown down, cable down the back")
    R(mon + CL + S, PNG + "clip-front.png", elev=0, azim=-90, title="Clip, as you see it: nothing over the screen but a 6 mm lip on the bezel")
    crop = box(-32, 62, -20, 62, -80, CZ)
    R([(m ^ crop, col) for m, col in mon + CL + S], PNG + "clip-section-clamp.png", elev=89, azim=-90,
      title="Clip cut through the screw, from above: lip on the bezel, pad on the back, dovetail into the body")
    zf = pt_world((0, 0, 0), "clip")[2]
    xf = pt_world((0, 0, 0), "clip")[0]
    R([(m.trim_by_plane([1, 0, 0], xf), col) for m, col in mon + CL + S], PNG + "clip-section-side.png", elev=0, azim=180, zoom=1.3,
      title="Clip cut through the face centre: badge, plate, plug in the trough, cable out the back")
    stylus = m3.Manifold.cylinder(geo["back"] + 30 - (b.pcb_back_z + b.sw_cap_h), PIN_D/2, PIN_D/2, 24) \
        .translate([geo["sw"][c.BUTTON], b.sw_y, b.pcb_back_z + b.sw_cap_h])
    SB = scene(b, c, "clip", feats, body, plate_h, geo, ring, back=True)
    R(mon + CL + SB + [(to_world(stylus, "clip"), STEEL)], PNG + "clip-back.png", elev=16, azim=52, light=BACKLIGHT,
      title="Clip from behind: knob, BOOT through the plate with a 2 mm stylus, cable down the back")
    dz = -45.0
    cl_parts = [(clamp(), CLAMP_C), (cs["pad"].translate([0, -12, 0]), CLAMP_C), (cs["nut"].translate([0, 0, 16]), STEEL),
                (cs["screw"].translate([0, 22, 0]), STEEL), (cs["knob"].translate([0, 34, 0]), CLAMP_C)]
    ex = [(SB[0][0], OFF_WHITE), (SB[3][0], GLASS), (SB[1][0].translate([0, -28, 0]), ORANGE),
          (SB[2][0].translate([0, 34, 0]), PLATE_C)] + [(m.translate([0, 0, dz]), col) for m, col in cl_parts]
    R(ex, PNG + "clip-exploded.png", elev=20, azim=38, light=BACKLIGHT,
      title="Clip exploded, from behind: plate, ring; clamp slides up into the dovetail; pad, nut, M4 x 40, knob")
    pr = [(body.translate([0, 0, c.LIP_T]), OFF_WHITE), (clamp().translate([60, -10, -CZ0]), CLAMP_C),
          (knob().translate([75, 50, 0]), CLAMP_C), (pad().translate([95, 50, 0]), CLAMP_C), (ring.translate([0, -40, 0]), ORANGE)]
    R(pr, PNG + "clip-print-layout.png", elev=40, azim=-60,
      title="Clip, print layout: body face down, clamp flat, knob pocket up, pad, ring. No supports")

    # ---------------- family
    st = scene(b, c, "stand", out["stand"][0], out["stand"][1], out["stand"][2], out["stand"][3], ring)
    cp = scene(b, c, "clip", out["clip"][0], out["clip"][1], out["clip"][2], out["clip"][3], ring)
    shift = lambda m: m.translate([-FACE/2 - 6 + 90, 0, 63])
    R(st + [(shift(m), col) for m, col in cp[:5]], PNG + "family.png", elev=10, azim=-62, zoom=1.2,
      title="One family: the stand and the clip body share the face, the grille, the module")


if __name__ == "__main__":
    main()
