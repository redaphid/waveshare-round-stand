#!/usr/bin/env python3
"""
Scissor stand, fused to the USB-only pocketwatch case.

Two U-shaped legs (bails) hinge on lugs at about 4:30 and 7:30, one M3 screw per side.
Seen from the side, the two arms on each lug open like scissor blades: the FRONT bail
swings forward, the REAR bail swings back, and the case stands on the four feet in
between. Each blade opens until its upper end lands on a stop cast into a hood over the
pivot. Folded, both bails hang straight down in the plane of the case, no thicker than
the case, with the plug and cable running between their crossbars: they become a guard
for the plug in a pocket.

Why not the X in the plane of the back (the first sketch): two feet in a line give no
fore-aft footing, a third leg is needed anyway, and with the feet behind the plug a
cable pull tips it forward. This keeps the scissors and the sideways feet, turns the X
to face sideways, and puts a footing in front of the plug.

Badge frame (from build_pocketwatch.py): origin = glass centre, +y toward the USB-C tab,
+z backward. World: X right, Y toward the viewer, Z up, desk at Z = 0.

Run from the repo root: ~/.venvs/cad/bin/python pocketwatch/stands/scissor/build_scissor.py [--no-render]
"""
import sys, math
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pod")
import numpy as np, manifold3d as m3, trimesh
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)
from build_pocketwatch_usb import boot_hole_plate, PIN_D, BACK_CHAMFER, SHELL_LEN, MIN_PLUG_ENGAGE

STL = "stl/pocketwatch/stands/scissor/"
OUT = "pocketwatch/stands/scissor/renders/"

# ---- stand: what we choose ----------------------------------------------------------
LEAN = 20.0            # deg the face tips back from vertical, toward a seated viewer's eyes
A_FRONT = 12.0         # front bail swing cleared by the hood (+ GAP): its stop lands ~15 deg forward of the case axis
B_REAR = 51.0          # rear bail swing cleared by the hood: its stop lands ~55 deg back
PIV_Y, PIV_Z = 16.0, 4.0     # pivot, badge frame, at x = +-(lug)
GAP = 0.4              # every printed sliding gap
ARM_T = 2.4            # arm thickness along x
X_LUG = 21.3           # lug face; arms outboard of it
X_IN0 = X_LUG + GAP; X_IN1 = X_IN0 + ARM_T          # front bail arms (inner layer)
X_OUT0 = X_IN1 + GAP; X_OUT1 = X_OUT0 + ARM_T       # rear bail arms (outer layer)
R_END = 3.4            # arm's round end around the pivot
HOLE_ARM = 3.4         # M3 clearance through the arms
HOLE_TAP = 2.6         # M3 thread-forming hole in the lug
TAP_DEPTH = 7.0
SCREW_L, HEAD_D, HEAD_H = 12.0, 5.5, 3.0       # M3 x 12 socket head
CAP_R = 10.0           # hood over the pivot (carries the stops)
CHAMF = 0.6
PLUG_LEN, PLUG_W, PLUG_T = 22.0, 12.0, 8.0     # straight USB-C plug body outside the case
CABLE_D = 4.0
CABLE_CLEAR = 10.0     # plug end this high above the desk, so the cable can bend back
REAR_BAR_RISE = 13.0   # rear crossbar this far up the arm from the foot: the cable runs under it
PETG = 1.27e-3         # g/mm^3
BADGE_G, SCREW_G, PLUG_G = 20.0, 0.9, 4.0
MU = 0.5               # PETG foot on a desk, low end
PULL = 1.0             # N, cable
TIP_MIN = 20.0         # deg
MAX_STRAIN = 0.02


# ---- small helpers -------------------------------------------------------------------
def yz_prism(cs, x0, x1):
    """Extrude a CrossSection drawn in (y, z) along x from x0 to x1."""
    M = [[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]]
    return m3.Manifold.extrude(cs, x1 - x0).transform(M)


def yz_chamfered(pieces, x0, x1, c):
    M = [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]]
    return chamfered(pieces, x0, x1, c, c).transform(M)


def disc_at(r, y, z, n=96):
    return m3.CrossSection.circle(r, n).translate([y, z])


def rot2(cs, deg):
    """Rotate a (y, z) CrossSection about the pivot; +deg swings a downward arm backward (+z)."""
    return cs.translate([-PIV_Y, -PIV_Z]).rotate(deg).translate([PIV_Y, PIV_Z])


def rot3(m, deg):
    return m.translate([0, -PIV_Y, -PIV_Z]).rotate([deg, 0, 0]).translate([0, PIV_Y, PIV_Z])


def sweep2(pieces, a0, a1, step=2.0):
    """Area every convex piece covers while turning from a0 to a1 degrees (hull of neighbours)."""
    n = max(1, int(math.ceil(abs(a1 - a0) / step)))
    angs = np.linspace(a0, a1, n + 1)
    out = []
    for p in pieces:
        for i in range(n):
            out.append(m3.CrossSection.batch_hull([rot2(p, angs[i]), rot2(p, angs[i + 1])]))
    return m3.CrossSection.batch_boolean(out, m3.OpType.Add)


def Rx(d):
    t = math.radians(d); c, s = math.cos(t), math.sin(t)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Rz(d):
    t = math.radians(d); c, s = math.cos(t), math.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


W_ROT = Rx(LEAN) @ Rx(90) @ Rz(180)      # badge -> world rotation (crown down and forward)


def world(m, H):
    M = np.hstack([W_ROT, [[0], [0], [H]]])
    return m.transform(M.tolist())


def unworld(m, H):
    M = np.hstack([W_ROT.T, (-W_ROT.T @ np.array([0, 0, H]))[:, None]])
    return m.transform(M.tolist())


def wpt(p, H):
    return W_ROT @ np.asarray(p, float) + np.array([0, 0, H])


def tm_of(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))


def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def hull2d(pts):
    """Monotone chain convex hull, CCW."""
    pts = sorted(set(map(tuple, np.round(pts, 4))))
    if len(pts) < 3: return np.array(pts)
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0]-h[-2][0])*(p[1]-h[-2][1]) - (h[-1][1]-h[-2][1])*(p[0]-h[-2][0])) <= 0: h.pop()
            h.append(p)
        return h
    lo, up = half(pts), half(pts[::-1])
    return np.array(lo[:-1] + up[:-1])


def edge_margins(poly, q):
    """Signed distance from q to each edge of CCW polygon (positive inside), with each edge's outward normal."""
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        e = b - a; n = np.array([e[1], -e[0]]) / np.linalg.norm(e)    # outward for CCW
        out.append((-(q - a) @ n, n))
    return out


# ---- the arms: (y, z) outlines in the folded pose, right side -------------------------
def arm_pieces(which, y_end):
    """Convex pieces of one arm, folded (pointing +y from the pivot). Front arm: flat face on z=-1.0
    (its print bed) with a tang on that face above the pivot. Rear arm: flat face on z=11.0."""
    end = disc_at(R_END, PIV_Y, PIV_Z)
    if which == "front":
        tang = m3.CrossSection([[(PIV_Y - 6.0, -1.0), (PIV_Y, -1.0), (PIV_Y, 2.0), (PIV_Y - 4.5, 2.0)]])
        body = m3.CrossSection([[(PIV_Y, -1.0), (y_end, -1.0), (y_end, 4.0), (PIV_Y, PIV_Z + R_END)]])
    else:
        tang = m3.CrossSection([[(PIV_Y - 4.0, 11.0), (PIV_Y, 11.0), (PIV_Y, 8.0), (PIV_Y - 2.5, 8.0)]])
        body = m3.CrossSection([[(PIV_Y, PIV_Z - R_END), (y_end, 6.0), (y_end, 11.0), (PIV_Y, 11.0)]])
    return [m3.CrossSection.batch_hull([end, tang]), m3.CrossSection.batch_hull([end, body])]


def stop_angle(pieces, cap2d, sign, start):
    """Degrees the arm turns (in direction sign) before it first touches the cap."""
    hit = lambda a: (m3.CrossSection.batch_boolean([rot2(p, sign*a) for p in pieces], m3.OpType.Add) ^ cap2d).area() > 1e-3
    lo, hi = start, start + 20
    assert not hit(lo) and hit(hi), "stop not where expected"
    while hi - lo > 0.02:
        mid = (lo + hi)/2
        lo, hi = (mid, hi) if not hit(mid) else (lo, mid)
    return lo


# ---- the case: the USB-only case (copied build) plus two lugs and their hoods ------------
def build_case(b: Badge, c: Case):
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    STEP = 1.2
    R_REAR = R_BORE + STEP
    R_OUT = R_REAR + c.CASE_WALL
    FLOOR = b.hdr_top_z + c.FLOAT
    Z_CASE = FLOOR + c.PLATE_T
    bore_xy = feats[0].grown()
    pocket = circle(R_REAR) + bore_xy
    boss = (bore_xy.offset(c.CASE_WALL, Round) ^ rect(-40, 40, 10, 40)).hull()
    # a rounded ear around the pivot, run into the case and the crown boss
    lug = (m3.CrossSection.batch_hull([circle(6.6).translate([X_LUG - 6.6, PIV_Y]),
                                       m3.CrossSection.square([1, 1]).translate([12.0, 9.0])]) ^ rect(0, X_LUG, 0, 40))
    lugs = [lug, lug.mirror([1, 0])]

    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())
    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4

    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    shell = chamfered([circle(R_OUT), boss] + lugs, -c.LIP_T, Z_CASE, c.CHAMFER, BACK_CHAMFER)
    cavity = prism(bore_xy, 0.0, Z_CASE + 1) + prism(circle(R_REAR), FLOOR, Z_CASE + 1) + \
        window.translate([0, 0, -c.LIP_T - 0.01]) + groove_p + all_keep

    # plate: exactly as the USB-only build
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

    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_OUT, FLOOR=FLOOR, Z_CASE=Z_CASE, bh_p=bh_p,
               groove_r_p=groove_r_p, hdrs=hdrs, sw=sw, post_cyl=post_cyl)
    return feats, shell, cavity, plate, geo


def hood2d(Z_CASE, front_pcs, rear_pcs, a_front, b_rear):
    """The hood over each pivot, as three (y, z) outlines: the lug-side layer (clear of the front arm's
    swing), the outer layer (clear of the rear arm's swing) and the layer between (clear of both)."""
    raw = disc_at(CAP_R, PIV_Y, PIV_Z, 128) ^ rect(PIV_Y - CAP_R, PIV_Y + 1.5, -1.2, Z_CASE)
    near = disc_at(CAP_R + 4, PIV_Y, PIV_Z)
    fsw = sweep2([p ^ near for p in front_pcs], -a_front, 0.0).offset(GAP + 0.1, m3.JoinType.Round)
    rsw = sweep2([p ^ near for p in rear_pcs], 0.0, b_rear).offset(GAP + 0.1, m3.JoinType.Round)
    inner, outer = raw - fsw, raw - rsw
    return inner, outer, inner ^ outer


def hood3d(inner, outer, both):
    right = yz_prism(inner, X_LUG - 0.6, X_IN1) + yz_prism(both, X_IN1 - 0.01, X_OUT0 + 0.01) + \
        yz_prism(outer, X_OUT0, X_OUT1 - CHAMF) + yz_prism(outer.offset(-CHAMF, Round), X_OUT1 - CHAMF - 0.01, X_OUT1)   # softened outer edge
    return right + right.mirror([1, 0, 0])


def screw_holes(depth_from, depth_to, d):
    cyl = m3.Manifold.cylinder(depth_to - depth_from, d/2, d/2, 48).rotate([0, 90, 0]).translate([depth_from, PIV_Y, PIV_Z])
    return cyl + cyl.mirror([1, 0, 0])


def screws():
    shank = m3.Manifold.cylinder(SCREW_L, 1.5, 1.5, 32).rotate([0, 90, 0]).translate([X_OUT1 - SCREW_L, PIV_Y, PIV_Z])
    head = m3.Manifold.cylinder(HEAD_H, HEAD_D/2, HEAD_D/2, 32).rotate([0, 90, 0]).translate([X_OUT1, PIV_Y, PIV_Z])
    s = shank + head
    return s + s.mirror([1, 0, 0])


# ---- the bails ---------------------------------------------------------------------------
def build_bails(s_front, s_rear):
    yf, yr = PIV_Y + s_front, PIV_Y + s_rear
    fp, rp = arm_pieces("front", yf + 8), arm_pieces("rear", yr + 8)
    arm_f = yz_chamfered(fp, X_IN0, X_IN1, CHAMF)
    arm_r = yz_chamfered(rp, X_OUT0, X_OUT1, CHAMF)
    bar_f = chamfered([rect(-X_IN1 + 0.3, X_IN1 - 0.3, yf - 2.0, yf + 6.0)], -1.0, 2.4, CHAMF, CHAMF)
    ycb = yr - REAR_BAR_RISE
    bar_r = chamfered([rect(-X_OUT1 + 0.3, X_OUT1 - 0.3, ycb - 2.2, ycb + 2.2)], 7.6, 11.0, CHAMF, CHAMF)
    hole = screw_holes(X_IN0 - 1, X_OUT1 + 1, HOLE_ARM)
    front = (arm_f + arm_f.mirror([1, 0, 0]) + bar_f) - hole
    rear = (arm_r + arm_r.mirror([1, 0, 0]) + bar_r) - hole
    return front, rear, fp, rp


# ---- badge, plug and cable props -------------------------------------------------------
def props(b, c, boss_tip):
    plug = box(-PLUG_W/2, PLUG_W/2, boss_tip, boss_tip + PLUG_LEN, b.port_z - PLUG_T/2, b.port_z + PLUG_T/2)
    shell = box(-4.2, 4.2, b.tip_y - 3.0, boss_tip + 0.01, b.port_z - 1.3, b.port_z + 1.3)
    screen = m3.Manifold.cylinder(0.2, b.active_d/2, b.active_d/2, SEG).translate([0, 0, -0.25])
    return plug, shell, screen


def tube(points, r):
    s = [m3.Manifold.sphere(r, 24).translate(list(p)) for p in points]
    return union(m3.Manifold.batch_hull([s[i], s[i + 1]]) for i in range(len(s) - 1))


def cable_world(b, boss_tip, H, back=-75.0):
    """Cable as a tube in world: out of the plug along its axis, a bend, then back along the desk."""
    E = wpt([0, boss_tip + PLUG_LEN, b.port_z], H)
    d = W_ROT @ np.array([0, 1.0, 0])
    r = CABLE_D/2
    P1 = E + 4*d
    t = (P1[2] - r) / -d[2]
    C = P1 + t*d                           # where the plug axis meets cable-height
    P3 = np.array([0, C[1] - 12.0, r])
    bez = [(1-u)**2*P1 + 2*(1-u)*u*C + u**2*P3 for u in np.linspace(0, 1, 14)]
    pts = [E + 0.5*d] + bez + [np.array([0, back, r])]
    return tube(pts, r), pts


def cable_folded(b, boss_tip):
    r = CABLE_D/2
    return tube([[0, boss_tip + PLUG_LEN + 0.5, b.port_z], [0, boss_tip + PLUG_LEN + 60, b.port_z]], r)


# ---- assembly ------------------------------------------------------------------------------
def assemble(b, c):
    feats, shell, cavity, plate, geo = build_case(b, c)
    fp0, rp0 = arm_pieces("front", PIV_Y + 80), arm_pieces("rear", PIV_Y + 80)
    inner, outer, both = hood2d(geo["Z_CASE"], fp0, rp0, A_FRONT, B_REAR)
    af = stop_angle(fp0, inner, -1, A_FRONT)        # where each blade actually lands on its stop
    br = stop_angle(rp0, outer, +1, B_REAR)
    case = (shell + hood3d(inner, outer, both)) - cavity - screw_holes(X_LUG - TAP_DEPTH, X_LUG + 0.2, HOLE_TAP)
    boss_tip = bbox(case ^ box(-3, 3, 0, 40, -2, 12))[1, 1]
    H = CABLE_CLEAR - (W_ROT @ np.array([0, boss_tip + PLUG_LEN, b.port_z]))[2]
    Zp = wpt([0, PIV_Y, PIV_Z], H)[2]
    s_front = Zp / math.cos(math.radians(LEAN + af))
    s_rear = Zp / math.cos(math.radians(br - LEAN))
    front, rear, fp, rp = build_bails(s_front, s_rear)
    front, rear = desk_trim(front, -af, H), desk_trim(rear, br, H)
    plate_h, bx, by = boot_hole_plate(b, c, plate, geo)
    geo.update(af=af, br=br, H=H, Zp=Zp, s_front=s_front, s_rear=s_rear, boss_tip=boss_tip, fp=fp, rp=rp,
               hood=(inner, outer, both), boot=(bx, by))
    return feats, case, plate, plate_h, front, rear, geo


def desk_trim(m, a, H):
    """Cut a folded bail flat where the desk meets it once it is turned a degrees and stood up."""
    n_b = W_ROT.T @ np.array([0, 0, 1.0])              # world up, in the badge frame
    R = Rx(a); P = np.array([0, PIV_Y, PIV_Z])
    n_f = R.T @ n_b                                    # ... and in the folded bail's frame
    off = -H - n_b @ P + n_f @ P
    return m.trim_by_plane(n_f.tolist(), float(off))


def deployed(geo, front, rear):
    return rot3(front, -geo["af"]), rot3(rear, geo["br"])


# ---- checks for the stand ----------------------------------------------------------------
def stand_checks(b, c, feats, case, plate_h, front, rear, geo):
    af, br, H = geo["af"], geo["br"], geo["H"]
    plug, shell, screen = props(b, c, geo["boss_tip"])
    fr_d, re_d = deployed(geo, front, rear)

    print(f"\n7. Hinges: each blade swings its whole range clear of the case, then lands on its stop")
    for nm, m, sgn, nom, stop in (("front bail", front, -1, A_FRONT, af), ("rear bail", rear, 1, B_REAR, br)):
        worst, gmin = 0.0, 9.0
        for a in np.linspace(0, stop - 0.05, 14):
            worst = max(worst, (rot3(m, sgn*a) ^ case).volume())
        for a in np.linspace(0, nom, 10):
            gmin = min(gmin, rot3(m, sgn*a).min_gap(case, 2.0))
        check(worst < 1e-3 and gmin >= GAP - 0.06, f"{nm} swings 0..{stop:.1f} deg without touching case or hood",
              f"gap {gmin:.2f} over the first {nom:g} deg, then closes onto the stop")
    for nm, m, a in (("front bail", front, -(af + 1.5)), ("rear bail", rear, br + 1.5)):
        v = (rot3(m, a) ^ case).volume()
        check(v > 0.05, f"{nm} 1.5 deg past its stop runs into the hood (it is a stop)", f"{v:.2f} mm^3")
    check(abs(af - 15) < 3 and abs(br - 55) < 3, "stops land near 15 deg (front) and 55 deg (rear)", f"{af:.1f} / {br:.1f}")
    for fa, ra in ((0, 0), (-af, 0), (0, br), (-af, br)):
        f_, r_ = rot3(front, fa), rot3(rear, ra)
        v = (f_ ^ r_).volume(); g = f_.min_gap(r_, 2.0)
        check(v < 1e-3 and g >= GAP - 0.06, f"bails clear of each other, front {fa:+.0f} / rear {ra:+.0f} deg", f"gap {g:.2f}")
    print(f"     sliding gaps along x: lug face -> front arm {X_IN0 - X_LUG:.1f}, front -> rear arm {X_OUT0 - X_IN1:.1f}")

    for nm, cs in zip(("lug-side layer", "outer layer", "middle layer"), geo["hood"]):
        thin = (cs - cs.offset(-0.6, m3.JoinType.Miter, 2.0).offset(0.6, m3.JoinType.Miter, 2.0)).area()
        check(thin < 1.0, f"hood {nm}: nothing thinner than 1.2 (area an opening by 0.6 removes)", f"{thin:.2f} mm^2 (corner tips)")
    print("\n8. Pivot screws (M3 x %g socket head, thread-forming into the lug)" % SCREW_L)
    tip = X_OUT1 - SCREW_L
    check(tip >= X_LUG - TAP_DEPTH + 0.3, "screw tip stays inside the tapped hole", f"tip x {tip:.1f}, hole bottom {X_LUG - TAP_DEPTH:.1f}")
    check(X_LUG - tip >= 4.0, "thread engagement in the lug >= 4", f"{X_LUG - tip:.1f}")
    ring = screw_holes(X_LUG - TAP_DEPTH - 1.2, X_LUG - 0.5, HOLE_TAP + 2*1.2) - screw_holes(X_LUG - TAP_DEPTH - 2, X_LUG, HOLE_TAP)
    v = (ring - case).volume()
    check(v < 0.05, "1.2 mm of case all round the tapped holes (no break-out into the bore)", f"{v:.3f} mm^3 missing")
    wob = math.degrees(math.atan((HOLE_ARM - 3.0) / (2*X_IN0)))
    print(f"     wobble: a bail's two arms sit {2*X_IN0:.0f} apart on two screws, so 0.2 hole play tilts it {wob:.2f} deg")

    print("\n9. Folded: legs hang in the plane of the case, plug and cable between the crossbars")
    zc = bbox(case)
    for nm, m in (("front bail", front), ("rear bail", rear)):
        bb = bbox(m)
        check(bb[0, 2] >= zc[0, 2] - 1e-6 and bb[1, 2] <= zc[1, 2] + 1e-6, f"{nm} within the case thickness",
              f"z {bb[0, 2]:.2f}..{bb[1, 2]:.2f} vs case {zc[0, 2]:.2f}..{zc[1, 2]:.2f}")
    sc = screws()
    pk = bbox(case + front + rear + sc)
    geo["folded"] = pk[1] - pk[0]
    print(f"     folded package {pk[1, 0] - pk[0, 0]:.1f} wide (screw heads included) x {pk[1, 1] - pk[0, 1]:.1f} tall x "
          f"{zc[1, 2] - zc[0, 2]:.2f} thick")
    cf = cable_folded(b, geo["boss_tip"])
    for nm, m in (("front bail", front), ("rear bail", rear)):
        g = min(plug.min_gap(m, 5.0), cf.min_gap(m, 5.0))
        check((plug ^ m).volume() < 1e-3 and (cf ^ m).volume() < 1e-3 and g >= 0.5,
              f"plug + hanging cable clear of the folded {nm}", f"gap {g:.2f}")

    print("\n10. Deployed: plug, cable, screen and BOOT stylus clear")
    cw, pts = cable_world(b, geo["boss_tip"], H)
    geo["cable_pts"] = pts
    plug_w = world(plug, H)
    for nm, m in (("front bail", fr_d), ("rear bail", re_d)):
        mw = world(m, H)
        g1, g2 = plug_w.min_gap(mw, 8.0), cw.min_gap(mw, 8.0)
        check((plug_w ^ mw).volume() < 1e-3 and g1 >= 1.0, f"plug body clear of the {nm}", f"gap {g1:.2f}" if g1 < 8 else "gap > 8")
        check((cw ^ mw).volume() < 1e-3 and g2 >= 1.0, f"cable (bending back under the stand) clear of the {nm}", f"gap {g2:.2f}" if g2 < 8 else "gap > 8")
    g = cw.min_gap(world(case + sc, H), 8.0)
    check(g >= 0.5, "cable clear of the case lugs and screws", f"gap {g:.2f}")
    rb = world(re_d, H) ^ box(-8, 8, -200, 200, -10, 300)
    zbar = bbox(rb)[0, 2]
    check(zbar >= CABLE_D + 2.0, f"rear crossbar clears a {CABLE_D:g} mm cable on the desk", f"underside {zbar:.1f} above the desk")
    e = wpt([0, geo["boss_tip"] + PLUG_LEN, b.port_z], H)
    check(e[2] >= CABLE_CLEAR - 1e-6, "plug end above the desk (room for the cable to bend back)", f"{e[2]:.1f}")
    glass = m3.Manifold.cylinder(6.0, b.r + 1.0, b.r + 1.0, SEG).translate([0, 0, -6.0])
    g = min(glass.min_gap(m, 10.0) for m in (fr_d, re_d, front, rear))
    check(g > 2.0, "nothing near the screen, folded or deployed", f"gap {g:.1f}")
    bx, by = geo["boot"]
    top = b.pcb_back_z + b.sw_cap_h
    path = m3.Manifold.cylinder(geo["Z_CASE"] + 40 - top, PIN_D/2, PIN_D/2, 32).translate([bx, by, top])
    hit = sum((path ^ m).volume() for m in (front, rear, fr_d, re_d, case))
    check(hit < 1e-3, f"{PIN_D:g} mm BOOT stylus path (40 mm straight back) clear of case and legs, both poses", f"{hit:.4f} mm^3")
    far = wpt([bx, by, geo["Z_CASE"] + 40], H)
    check(far[2] > 5, "stylus path stays above the desk when standing", f"its far end is {far[2]:.0f} up")
    return plug, cw


def stability(b, c, case, plate_h, front, rear, plug, geo):
    H = geo["H"]
    fr_d, re_d = deployed(geo, front, rear)
    parts = {"case": case, "plate": plate_h, "front bail": fr_d, "rear bail": re_d}
    masses, cogs = [], []
    for nm, m in parts.items():
        t = tm_of(world(m, H))
        masses.append(t.volume*PETG); cogs.append(t.center_mass)
    masses += [BADGE_G, PLUG_G, 2*SCREW_G]
    cogs += [wpt([0, 0, 3.0], H), tm_of(world(plug, H)).center_mass, wpt([0, PIV_Y, PIV_Z], H)]
    masses, cogs = np.array(masses), np.array(cogs)
    M = masses.sum(); G = (masses[:, None]*cogs).sum(0)/M
    W = M*9.81e-3
    print(f"\n11. Stability: {M:.1f} g ({', '.join(f'{n} {m:.1f}' for n, m in zip(list(parts) + ['badge', 'plug', 'screws'], masses))})")
    print(f"     centre of mass {G[2]:.1f} above the desk, {G[1]:+.1f} fore-aft of the pivots")
    feet = []
    for m in (fr_d, re_d):
        v = np.asarray(world(m, H).to_mesh().vert_properties)[:, :3]
        feet.append(v[v[:, 2] < 0.02][:, :2])
    poly = hull2d(np.vstack(feet))
    geo["support"] = poly
    xs, ys = poly[:, 0], poly[:, 1]
    print(f"     footprint {xs.max() - xs.min():.1f} wide x {ys.max() - ys.min():.1f} deep (feet {ys.min():+.1f} .. {ys.max():+.1f} fore-aft)")
    name = lambda n: "forward" if n[1] > 0.7 else "backward" if n[1] < -0.7 else "sideways"
    worst = {}
    for d, n in edge_margins(poly, G[:2]):
        k = name(n); a = math.degrees(math.atan2(d, G[2]))
        if k not in worst or a < worst[k]: worst[k] = a
    for k, a in worst.items():
        check(a >= TIP_MIN, f"tips {k} only past {TIP_MIN:g} deg (weight alone)", f"{a:.1f} deg")

    # A cable pull acts at the plug end. Load cases: the cable's own directions as it leaves the plug
    # and lies back along the desk (no tipping allowed), then flat horizontal tugs (must slide first).
    E = wpt([0, geo["boss_tip"] + PLUG_LEN, b.port_z], H)
    axis = W_ROT @ np.array([0, 1.0, 0])
    def cop(F):
        V = W - F[2]                                   # total down load (F[2] < 0 is a downward pull)
        # a horizontal force F_h at height E_z shifts the centre of pressure by F_h*E_z/V
        q = (W*G[:2] + (-F[2])*E[:2] + F[:2]*E[2]) / V
        return q, V
    print(f"     {PULL:g} N cable pull at the plug end ({E[2]:.0f} up, {E[1]:+.0f} fore-aft):")
    for nm, d in (("down", [0, 0, -1]), ("along the plug, down-forward", axis), ("down and back 45 deg", [0, -0.7071, -0.7071]),
                  ("back along the desk, 20 deg down", [0, -0.94, -0.342])):
        F = PULL*np.asarray(d, float)/np.linalg.norm(d)
        q, V = cop(F)
        mar = min(m for m, n in edge_margins(poly, q))
        check(mar > 3.0, f"pull {nm}: does not tip", f"centre of pressure {mar:.1f} inside the footprint")
    for nm, d in (("back", [0, -1, 0]), ("forward", [0, 1, 0]), ("sideways", [1, 0, 0])):
        d = np.asarray(d, float)
        lo, hi = 0.0, 5.0
        for _ in range(40):
            mid = (lo + hi)/2
            q, V = cop(mid*d)
            lo, hi = (mid, hi) if min(m for m, n in edge_margins(poly, q)) > 0 else (lo, mid)
        slide = MU*W
        check(lo > slide, f"flat tug {nm}: slides ({slide:.2f} N) before it tips", f"tips at {lo:.2f} N")
    return G, M


def strength_checks(geo):
    print("\n12. Strength and print")
    # assembly: each U-bail's arms spring apart once to pass over the hoods onto the screws
    for nm, x0, L in (("front", X_IN0, geo["s_front"] - 4), ("rear", X_OUT0, geo["s_rear"] - REAR_BAR_RISE)):
        d = X_OUT1 + 0.2 - x0
        e = 3*d*ARM_T/(2*L**2)
        check(e < MAX_STRAIN, f"{nm} bail arms flex {d:.1f} to go on: bending strain < {MAX_STRAIN:.0%}", f"{e:.2%} (L {L:.0f})")
    # worst stop load: everything we allow (weight + 1 N pull) on one bail, levered at the foot
    F = 0.6 + PULL
    lever = geo["Zp"]*math.tan(math.radians(40))
    contact_r, face = 5.0, 2.4*5.0          # stops meet the blade face to face (see renders/hinge-*-stop.png)
    N = F*lever/contact_r
    print(f"     stop load (1.6 N on one bail, {lever:.0f} lever, contact r {contact_r:g}): {N:.1f} N on ~{face:.0f} mm^2 "
          f"= {N/face:.1f} MPa; PETG ~45 MPa in layers")
    print("     layers: arms print on edge, so every arm, tang and crossbar runs along its layers; hood fingers run along x in layers")


# ---- renders ----------------------------------------------------------------------------------
CASE_C, PLATE_C, LEG_C, STEEL = (0.40, 0.41, 0.44), (0.34, 0.35, 0.38), (0.60, 0.61, 0.64), (0.78, 0.78, 0.80)
GLASS, SCREEN, PLUG_C, CABLE_C, DESK = (0.06, 0.06, 0.07), (0.16, 0.46, 0.88), (0.86, 0.86, 0.88), (0.16, 0.16, 0.17), (0.90, 0.88, 0.84)
FRONT_LIGHT, SIDE_LIGHT = (0.45, 0.75, 0.55), (0.80, 0.35, 0.50)


def render(parts, path, elev=18, azim=-55, title="", light=(-0.45, -0.75, 0.5), zoom=1.0):
    """pod/render.py's painter's renderer plus back-face culling, so the far side of a flat plate
    can never be sorted over its near side."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from render import to_tris
    e, a = math.radians(elev), math.radians(azim)
    eye = np.array([math.cos(e)*math.cos(a), math.cos(e)*math.sin(a), math.sin(e)])
    fig = plt.figure(figsize=(9, 9), dpi=110); ax = fig.add_subplot(111, projection="3d")
    L = np.array(light, float); L /= np.linalg.norm(L)
    T_all, C_all, V_all = [], [], []
    for man, rgb in parts:
        T = to_tris(man)
        if len(T) == 0: continue
        V_all.append(T.reshape(-1, 3))
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
        keep = n @ eye > -0.02
        T, n = T[keep], n[keep]
        shade = 0.30 + 0.70*np.clip(n @ L, 0, 1) + 0.12*np.clip(n[:, 2], 0, 1)
        T_all.append(T); C_all.append(np.clip(np.array(rgb)[None, :]*shade[:, None], 0, 1))
    T = np.concatenate(T_all); C = np.concatenate(C_all)
    ax.add_collection3d(Poly3DCollection(T, facecolors=C, edgecolors=C, linewidths=0.3, zsort="average"))   # edges close AA seams
    V = np.concatenate(V_all); c = (V.max(0) + V.min(0))/2; r = (V.max(0) - V.min(0)).max()/2*1.02/zoom
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    if title: fig.suptitle(title, fontsize=11, y=0.93)
    fig.subplots_adjust(0, 0, 1, 1); fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)


def renders(b, c, feats, case, plate_h, front, rear, plug, cw, geo):
    H = geo["H"]
    R = lambda m, L=1.0: m.refine_to_length(L)
    disc = next(f for f in feats if f.name == "disc + tab").solid()
    _, shell, screen = props(b, c, geo["boss_tip"])
    fr_d, re_d = deployed(geo, front, rear)
    sc = screws()
    stand = [(case, CASE_C), (plate_h, PLATE_C), (fr_d, LEG_C), (re_d, LEG_C), (sc, STEEL), (disc, GLASS),
             (screen, SCREEN), (plug, PLUG_C), (shell, STEEL)]
    W = lambda items: [(R(world(m, H)), col) for m, col in items]
    desk = (box(-46, 46, -48, 52, -1.0, 0.0).refine_to_length(5.0), DESK)

    cw = R(cable_world(b, geo["boss_tip"], H, back=-46.0)[0])
    render(W(stand) + [(cw, CABLE_C), desk], OUT + "hero.png", elev=14, azim=58, light=FRONT_LIGHT,
           title="Scissor stand: two legs per lug open like scissor blades, plug and cable run between them")
    render(W(stand) + [(cw, CABLE_C)], OUT + "front.png", elev=6, azim=90, light=FRONT_LIGHT,
           title="As you see it from your chair: face tipped back 20 deg, USB-C at the bottom")

    cutw = lambda m: world(m, H).trim_by_plane([-1, 0, 0], 0.0)
    sec = [(R(cutw(m)), col) for m, col in stand] + [(cw.trim_by_plane([-1, 0, 0], 0.0), CABLE_C), desk]
    render([(m, col) for m, col in sec if not m.is_empty()], OUT + "side-section.png", elev=0, azim=0, light=SIDE_LIGHT,
           title=f"Section on the centre line: legs {LEAN + geo['af']:.0f} deg forward and {geo['br'] - LEAN:.0f} deg back, "
                 f"cable bends back under the rear crossbar")

    bx, by = geo["boot"]
    top = b.pcb_back_z + b.sw_cap_h
    pin = m3.Manifold.cylinder(geo["Z_CASE"] + 18 - top, PIN_D/2, PIN_D/2, 24).translate([bx, by, top])
    render(W(stand + [(pin, (0.85, 0.20, 0.18))]) + [(cw, CABLE_C), desk], OUT + "back.png", elev=22, azim=-118,
           title="From behind: press BOOT with a 2 mm pin (red) through the plate hole; nothing in the way")

    # hinge sections, in world: cut through each blade's layer on the badge's +x lug (world -X), seen from outside
    pv = wpt([X_OUT1, PIV_Y, PIV_Z], H)
    crop = box(pv[0] - 1, pv[0] + 30, pv[1] - 16, pv[1] + 16, pv[2] - 14, pv[2] + 14)
    for nm, xm, blade, other in (("front", (X_IN0 + X_IN1)/2, fr_d, re_d), ("rear", (X_OUT0 + X_OUT1)/2, re_d, fr_d)):
        cut = lambda m: world(m, H).trim_by_plane([1, 0, 0], -xm) ^ crop
        parts = [(cut(case), CASE_C), (cut(blade), (0.86, 0.55, 0.20)), (cut(disc), GLASS)]
        render([(R(m, 0.4), col) for m, col in parts if not m.is_empty()], OUT + f"hinge-{nm}-stop.png", elev=0, azim=180,
               light=(-0.8, 0.35, 0.5), title=f"Hinge cut through the {nm} blade (orange) on its stop: "
                                               f"{geo['af' if nm == 'front' else 'br']:.1f} deg open, screw hole at the pivot")
    up = lambda m: m.rotate([0, 0, 180]).rotate([90, 0, 0])          # badge -> upright world, for the folded pose
    cf = cable_folded(b, geo["boss_tip"])
    fold = [(case, CASE_C), (plate_h, PLATE_C), (front, LEG_C), (rear, LEG_C), (sc, STEEL), (disc, GLASS),
            (screen, SCREEN), (plug, PLUG_C), (shell, STEEL), (cf, CABLE_C)]
    fs = geo["folded"]
    render([(R(up(m)), col) for m, col in fold], OUT + "folded.png", elev=16, azim=62, light=FRONT_LIGHT,
           title=f"Folded for the pocket: {fs[0]:.0f} x {fs[1]:.0f} x {fs[2]:.1f} mm, legs guard the plug")

    lay, x = [], 0.0
    for m, col in ((front.translate([0, 0, 1.0]), LEG_C), (case.translate([0, 0, c.LIP_T]), CASE_C),
                   (plate_h.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]]), PLATE_C),
                   (rear.rotate([0, 180, 0]).translate([0, 0, 11.0]), LEG_C)):
        bb = bbox(m)
        lay.append((m.translate([x - bb[0, 0], -(bb[0, 1] + bb[1, 1])/2, 0]), col)); x += bb[1, 0] - bb[0, 0] + 8
    render([(R(m), col) for m, col in lay], OUT + "print-layout.png", elev=30, azim=-75,
           title="Print layout, as exported, no supports: front legs, case (bezel down), plate, rear legs")


# ---- main ------------------------------------------------------------------------------------
def main():
    import build_pocketwatch_usb as usb
    b, c = Badge(), Case()
    feats, case, plate, plate_h, front, rear, geo = assemble(b, c)
    print(f"Lean {LEAN:g} deg; front blade stops at {geo['af']:.1f} deg, rear at {geo['br']:.1f} deg "
          f"(legs {LEAN + geo['af']:.0f} deg forward / {geo['br'] - LEAN:.0f} deg back of vertical); "
          f"pivots {geo['Zp']:.1f} above the desk; glass centre {geo['H']:.1f} up")
    usb.run_checks(b, c, feats, case, plate, geo)            # badge, plate, snaps and port: same as the USB-only case
    usb.run_hole_checks(b, c, feats, case, plate_h, *geo["boot"], geo)
    plug, cw = stand_checks(b, c, feats, case, plate_h, front, rear, geo)
    stability(b, c, case, plate_h, front, rear, plug, geo)
    strength_checks(geo)
    print()
    export(case, STL + "Scissor stand - case.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(plate_h, STL + "Scissor stand - back plate (BOOT hole).stl",
           lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]]))
    export(front, STL + "Scissor stand - front legs.stl", lambda m: m.translate([0, 0, 1.0]))
    export(rear, STL + "Scissor stand - rear legs.stl", lambda m: m.rotate([0, 180, 0]).translate([0, 0, 11.0]))
    if "--no-render" not in sys.argv:
        renders(b, c, feats, case, plate_h, front, rear, plug, cw, geo)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
