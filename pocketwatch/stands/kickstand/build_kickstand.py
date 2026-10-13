#!/usr/bin/env python3
"""
Kickstand pocketwatch: the USB-only case is its own desk stand.

The back of the case is a hunter-style lid hinged at 12 o'clock, right behind the crown.
Folded, it lies flush in a shallow well over the plate and the case is a plain puck.
Swung open, it is the leg: the case leans back on a flat heel at 6 o'clock and the
lid's straight foot. A printed stub in an arc groove is the hard stop at the open
angle; a flexure finger on the lid clicks a bump into a dimple at closed and at open.

Crown at 12 (the badge's own orientation, no firmware rotation): the plug stands up
out of the crown like a watch's bow, the cable loops back over the top, runs down
behind the leg and is held in a notch in its foot, so a tug on the cable acts at
desk level.

Four printed parts: case, plate (the BOOT-hole plate), leg, pin.
Badge frame as in build_pocketwatch.py: origin = glass face centre, +y to the USB-C
tab, +x right seen from the BACK, +z backward. The leg rotates about an x axis at
(Y_H, Z_H); phi > 0 swings its foot backward (+z).

Run from the repo root:  ~/.venvs/cad/bin/python pocketwatch/stands/kickstand/build_kickstand.py
"""
import sys, math, os
from dataclasses import dataclass
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3, trimesh
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)

Miter = m3.JoinType.Miter
HERE = "pocketwatch/stands/kickstand/"
STL = "stl/pocketwatch/stands/kickstand/"
OUT = HERE + "renders/"


@dataclass(frozen=True)
class Kick:
    BACK_CHAMFER: float = 0.6
    BOOT_HOLE_D: float = 3.4       # through the plate and, folded, the leg
    STYLUS_D: float = 2.0
    SHELL_LEN: float = 6.65        # USB-C plug metal shell
    MIN_PLUG_ENGAGE: float = 3.5
    PLUG_W: float = 12.0           # straight plug body outside the case
    PLUG_T: float = 8.0
    PLUG_L: float = 22.0
    CABLE_D: float = 4.0
    # leg (the lid)
    LEG_T: float = 2.4
    G: float = 0.4                 # leg to plate, leg to well wall: moving-part clearance
    RIM_G: float = 0.7             # leg edge to well wall: G + the leg's 0.2 axial play + its swing-out creep
    AX_CLR: float = 0.2            # barrel end to cheek, per side (0.4 total play)
    Y_H: float = 17.5              # hinge axis
    Z_H: float = 10.2
    R_B: float = 2.5               # barrel radius
    PIN_D: float = 2.2             # printed pin
    BORE_CLR: float = 0.2          # barrel bore around the pin, radial (0.4 diametral)
    Y_CB: float = 13.5             # above this the case keeps its full wall: the hinge cheeks
    Y_SH: float = 11.0             # the leg's shoulders slope from here at the neck down to SH_RIM at the
    SH_RIM: float = 6.0            # rim: low enough near the cheeks and the well wall that they swing clear
    X_CHEEK: float = 9.1           # cheek inner faces at +-this
    Y_FOOT: float = -14.5          # the leg's straight foot, folded
    PHI_S: float = 42.0            # groove end; the stub reaches it GROOVE_CLR later (phi_open())
    # detent finger (+x side) and stop stub (-x side), both at (v, w) in the leg: v down the leg
    # from the axis, w behind the axis (case frame +z)
    FING_W: float = 1.2            # finger width in the bending direction (x)
    SLOT_W: float = 0.8
    V_ROOT: float = 8.0            # finger root, measured down the leg from the axis
    BUMP_VW: tuple = (1.5, 2.1)
    BUMP_H: float = 0.7            # bump height off the finger face
    BUMP_R: float = 0.8            # base radius (45 degree flank, 0.1 tip)
    DIMPLE_D: float = 0.5
    STUB_VW: tuple = (1.5, 2.1)
    STUB_R: float = 0.8
    STUB_L: float = 0.8
    GROOVE_CLR: float = 0.25
    GROOVE_D: float = 1.0
    # heel, foot, cable notch
    HEEL_W: float = 16.0           # flat at 6 o'clock: the case's side of the stance
    NOTCH_W: float = 4.6           # cable notch in the foot (cable up to ~4.4)
    NOTCH_L: float = 10.0
    # masses and loads
    BADGE_G: float = 20.0
    PETG: float = 1.27             # g/cm^3
    FILL: float = 0.85             # walls dominate these thin parts
    CABLE_N: float = 1.0
    MU: float = 0.4                # PETG on a desk


# ---- helpers ----------------------------------------------------------------
def phi_open(k: Kick):
    """Where the stub actually stops: it travels GROOVE_CLR along its arc past PHI_S."""
    return k.PHI_S + math.degrees(k.GROOVE_CLR / math.hypot(*k.STUB_VW))


def bump_at(phi, k: Kick, xb, dx):
    yb, zb = vw_point(k.BUMP_VW, phi, k)
    return cyl_x(xb + dx - 0.5, xb + dx + 0.001, yb, zb, k.BUMP_R) + \
        cone_x(xb + dx, +1, yb, zb, k.BUMP_R, k.BUMP_R - k.BUMP_H, k.BUMP_H)


def yz_prism(cs, x0, x1):
    """A 2D section in the (y, z) plane, extruded along x from x0 to x1."""
    m = m3.Manifold.extrude(cs, x1 - x0)
    return m.transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])


def rot_yz(cs, phi, k: Kick):
    """Open a 2D (y, z) section by phi about the hinge axis (foot goes +z)."""
    return cs.translate([-k.Y_H, -k.Z_H]).rotate(-phi).translate([k.Y_H, k.Z_H])


def open_leg(m, phi, k: Kick, dx=0.0):
    return m.translate([0, -k.Y_H, -k.Z_H]).rotate([-phi, 0, 0]).translate([dx, k.Y_H, k.Z_H])


def vw_point(vw, phi, k: Kick):
    """(y, z) of a point at (v, w) in the leg, opened by phi."""
    v, w = vw
    p = math.radians(phi)
    return (k.Y_H - v*math.cos(p) + w*math.sin(p), k.Z_H + v*math.sin(p) + w*math.cos(p))


def cone_x(x0, dirn, y, z, r0, r1, h):
    """Truncated cone along x starting at x0, pointing dirn (+1/-1)."""
    c = m3.Manifold.cylinder(h, r0, r1, 48)              # along +z
    c = c.rotate([0, 90, 0]) if dirn > 0 else c.rotate([0, -90, 0])
    return c.translate([x0, y, z])


def cyl_x(x0, x1, y, z, r, n=48):
    return m3.Manifold.cylinder(x1 - x0, r, r, n).rotate([0, 90, 0]).translate([x0, y, z])


# ---- the leg ------------------------------------------------------------------
def leg_parts(b: Badge, c: Case, k: Kick, geo):
    """The leg in its folded pose. Returns (rigid leg with stub, bump, outline, yz profile of the hinge end)."""
    Z_PL, Z_BACK, R_REAR = geo["Z_PL"], geo["Z_BACK"], geo["R_REAR"]
    z0 = Z_PL + k.G
    xb = k.X_CHEEK - k.AX_CLR                                   # barrel ends at +-xb
    xr = R_REAR - k.RIM_G
    slope = (k.Y_SH - k.SH_RIM)/(xr - xb)
    # (the slope's top corners sit 1 mm inside the neck, so no vertex lands on the neck's edge)
    keep = m3.CrossSection([[(-40, k.Y_FOOT), (40, k.Y_FOOT), (40, k.SH_RIM - (40 - xr)*slope),
                             (xb - 1, k.Y_SH + slope), (-xb + 1, k.Y_SH + slope), (-40, k.SH_RIM - (40 - xr)*slope)]])
    disc = circle(xr) ^ keep
    neck = rect(-xb, xb, k.Y_SH - 1, k.Y_H)
    outline = disc + neck
    # barrel: a circle about the axis, hulled down to the back face so it prints standing on it.
    # The leg is ONE prism of its footprint, minus whatever lies outside the (y, z) profile of slab + barrel:
    # building it as a union of slab and barrel leaves coincident faces that do not export watertight.
    zmin = k.Z_H - k.R_B - 1
    prof = m3.CrossSection.hull(circle(k.R_B).translate([k.Y_H, k.Z_H]) +
                                rect(k.Y_H - k.R_B - 0.5, k.Y_H + 0.4, Z_BACK - 0.01, Z_BACK + 2))
    keep_yz = prof + rect(-40, k.Y_H, z0, Z_BACK + 2)
    foot_xy = disc + rect(-xb, xb, k.Y_SH - 1, k.Y_H + k.R_B + 1)
    leg = prism(foot_xy, zmin, Z_BACK) - yz_prism(rect(-40, 40, zmin - 1, Z_BACK + 1) - keep_yz, -25, 25)
    # bore for the pin, teardrop toward the case front (up when printed)
    rb = k.PIN_D/2 + k.BORE_CLR
    bore = m3.CrossSection.hull_points([tuple(p) for p in circle(rb).translate([k.Y_H, k.Z_H]).to_polygons()[0]] +
                                       [(k.Y_H, k.Z_H - rb*math.sqrt(2))])
    leg -= yz_prism(bore, -20, 20)
    # detent finger on +x: slots either side, free from the top of the barrel down to V_ROOT
    y_root = k.Y_H - k.V_ROOT
    fx1 = xb - 0.02                     # finger's outer face, a hair inside the neck's side (no shared face)
    fx0 = fx1 - k.FING_W
    leg -= prism(rect(fx0 - k.SLOT_W, fx0, y_root, k.Y_H + 5), 0, 20)
    leg -= prism(rect(fx1, xb + k.SLOT_W, y_root, k.Y_H + 5), 0, 20)
    # BOOT hole, aligned with the plate's when folded
    leg -= m3.Manifold.cylinder(10, k.BOOT_HOLE_D/2, k.BOOT_HOLE_D/2, 48).translate([geo["boot"][0], geo["boot"][1], z0 - 1])
    # cable notch in the middle of the foot
    notch = rect(-k.NOTCH_W/2, k.NOTCH_W/2, k.Y_FOOT - 1, k.Y_FOOT + k.NOTCH_L - k.NOTCH_W/2) + \
        m3.CrossSection.circle(k.NOTCH_W/2, 48).translate([0, k.Y_FOOT + k.NOTCH_L - k.NOTCH_W/2])
    leg -= prism(notch, 0, 20)
    # stop stub on the -x barrel end
    ys, zs = vw_point(k.STUB_VW, 0, k)
    stub = cyl_x(-xb - k.STUB_L, -xb + 0.5, ys, zs, k.STUB_R)        # rooted 0.5 into the barrel
    leg += stub
    # detent bump on the +x finger end: 45 degree cone
    bump = bump_at(0, k, xb, 0.0)
    # hinge-end profile (for the case cavity sweep): barrel profile + slab near the axis
    hinge_prof = (prof ^ rect(-40, 40, 0, Z_BACK)) + rect(k.Y_H - 12, k.Y_H, z0, Z_BACK)
    return leg, bump, outline, hinge_prof, xb


# ---- case, plate, leg, pin ----------------------------------------------------
def build(b: Badge, c: Case, k: Kick):
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    R_REAR = R_BORE + 1.2
    R_OUT = R_REAR + c.CASE_WALL
    FLOOR = b.hdr_top_z + c.FLOAT
    Z_PL = FLOOR + c.PLATE_T                     # plate back face
    Z_BACK = Z_PL + k.G + k.LEG_T                # case back = folded leg's back
    bore_xy = feats[0].grown()
    well_xy = circle(R_REAR) ^ rect(-40, 40, -40, k.Y_CB)
    boss = (bore_xy.offset(c.CASE_WALL, Round) ^ rect(-40, 40, 10, 40)).hull()
    hw = k.HEEL_W/2
    # round case + heel flat as ONE convex outline (two overlapping pieces share edges and leave slivers)
    body_xy = m3.CrossSection.hull_points([tuple(p) for p in circle(R_OUT).to_polygons()[0]] + [(-hw, -R_OUT), (hw, -R_OUT)])
    heel = body_xy
    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_OUT, FLOOR=FLOOR, Z_PL=Z_PL, Z_BACK=Z_BACK,
               boot=(sw[c.BUTTON], b.sw_y), sw=sw)

    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())
    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4

    leg, bump, leg_xy, hinge_prof, xb = leg_parts(b, c, k, geo)

    # hinge cavity: the hinge end of the leg (grown G) swept from closed to past the stop,
    # plus a straight drop-in path from the back so the leg goes in folded
    grown = hinge_prof.offset(k.G, Round)
    sweep = m3.CrossSection.batch_boolean([rot_yz(grown, a, k) for a in np.arange(-2, k.PHI_S + 6.01, 1.0)],
                                          m3.OpType.Add)
    drop = rect(k.Y_CB, k.Y_H + k.R_B + k.G, k.Z_H - k.R_B - k.G, Z_BACK + 1)
    cavity = yz_prism(sweep + drop, -k.X_CHEEK, k.X_CHEEK) ^ prism(rect(-40, 40, k.Y_CB, 40), -5, 40)

    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    case = chamfered([body_xy, boss], -c.LIP_T, Z_BACK, c.CHAMFER, k.BACK_CHAMFER)
    case -= prism(bore_xy, 0.0, Z_BACK + 1)
    case -= prism(well_xy, FLOOR, Z_BACK + 1)
    case -= window.translate([0, 0, -c.LIP_T - 0.01])
    case -= groove_p
    case -= all_keep
    case -= cavity
    # pin holes straight through both cheeks
    case -= cyl_x(-30, 30, k.Y_H, k.Z_H, k.PIN_D/2)
    # stop groove in the -x cheek: the stub's arc from closed to PHI_S, and a drop-in slot to the back
    ys, zs = vw_point(k.STUB_VW, 0, k)
    sr = k.STUB_R + k.GROOVE_CLR
    arc = m3.CrossSection.batch_boolean([circle(sr).translate(list(vw_point(k.STUB_VW, a, k)))
                                         for a in np.arange(0, k.PHI_S + 0.01, 1.0)], m3.OpType.Add)
    arc += m3.CrossSection.hull(circle(sr).translate([ys, zs]) + circle(sr).translate([ys, Z_BACK + 2]))
    case -= yz_prism(arc, -k.X_CHEEK - k.GROOVE_D, -k.X_CHEEK + 0.01)
    geo.update(groove_xy=arc)
    # detent dimples in the +x cheek: the bump's own cone (leg pushed to -x), 0.07 bigger all round, closed and open
    for a in (0.0, phi_open(k)):
        yb, zb = vw_point(k.BUMP_VW, a, k)
        case -= cone_x(xb - k.AX_CLR - 0.01, +1, yb, zb, k.BUMP_R + 0.07, k.BUMP_R + 0.07 - k.BUMP_H - 0.1, k.BUMP_H + 0.1)

    # plate: the BOOT-hole plate, cut off below the hinge cheeks
    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    top = rect(-40, 40, -40, k.Y_CB - c.FIT_CLR)
    pocket = (well_xy + bore_xy) ^ rect(-40, 40, -40, k.Y_CB)
    plate = prism(pocket.offset(-c.FIT_CLR - 0.03, Round) ^ top, FLOOR, Z_PL)
    plate += prism((skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round)) ^ top, skirt_front, FLOOR + 0.01)
    plate += bead_p ^ prism(top, -5, 40)
    plate += guides
    plate -= all_keep
    x, y = geo["boot"]
    plate -= m3.Manifold.cylinder(Z_BACK + 1 - (b.pcb_back_z + 1.0), k.BOOT_HOLE_D/2, k.BOOT_HOLE_D/2, 64) \
        .translate([x, y, b.pcb_back_z + 1.0])
    plate -= cavity

    # pin: from cheek face to cheek face of the outer wall at the axis, 0.3 short each end
    xo = math.sqrt(R_OUT**2 - k.Y_H**2) - 0.3
    pin = cyl_x(-xo, xo, k.Y_H, k.Z_H, k.PIN_D/2)

    geo.update(zb_p=zb_p, bh_p=bh_p, groove_r_p=groove_r_p, hdrs=hdrs, bore_xy=bore_xy, leg_xy=leg_xy, xb=xb, xo=xo,
               cavity=cavity, heel=heel)
    return feats, case, plate, leg, bump, pin, geo


# ---- standing on the desk ---------------------------------------------------------
def _cross(u, v): return u[0]*v[1] - u[1]*v[0]


def hull2d(P):
    P = sorted(set(map(tuple, np.round(P, 4))))
    def half(pts):
        h = []
        for p in pts:
            while len(h) >= 2 and _cross(np.subtract(h[-1], h[-2]), np.subtract(p, h[-2])) <= 0: h.pop()
            h.append(p)
        return h
    lo, up = half(P), half(P[::-1])
    return np.array(lo[:-1] + up[:-1])                    # counter-clockwise


def verts(m):
    return np.asarray(m.to_mesh().vert_properties)[:, :3]


def stance(b, c, k, feats, case, plate, leg, pin, geo, phi):
    """Rest the assembly (leg open phi) on a desk. Returns the case-frame -> world rotation (degrees about x),
    the z lift, the CoM in world, the total mass, and the parts' masses."""
    legp = open_leg(leg, phi, k)
    parts = {"case": case, "plate": plate, "leg": legp, "pin": open_leg(pin, 0, k)}
    mass = {n: m.volume()/1000*k.PETG*k.FILL for n, m in parts.items()}
    disc = feats[0].solid()
    mass["badge"] = k.BADGE_G
    com = sum(mass[n]*_centroid(parts[n]) for n in parts)
    com = (com + k.BADGE_G*_centroid(disc)) / sum(mass.values())
    P = np.vstack([verts(case)[:, 1:], verts(legp)[:, 1:]])
    H = hull2d(P)
    best = None
    for i in range(len(H)):
        a, e = H[i], H[(i + 1) % len(H)]
        d = e - a; L = np.linalg.norm(d); d /= L
        n = np.array([d[1], -d[0]])                       # outward for a CCW hull
        t = np.dot(com[1:] - a, d)
        if 0 < t < L and n[0] < -0.3 and n[1] > 0.05:      # tilted back onto the leg, not upright on the heel
            best = n if best is None or n[0] < best[0] else best
    beta = math.degrees(math.atan2(-best[0], -best[1]))
    world = lambda m: m.rotate([beta, 0, 0])
    z0 = min(bbox(world(case))[0, 2], bbox(world(legp))[0, 2])
    W = lambda m: world(m).translate([0, 0, -z0])
    cw = _rot_pt(com, beta) - [0, 0, z0]
    return dict(beta=beta, z0=z0, W=W, com=cw, mass=mass, legp=legp, lean=beta - 90.0, parts=parts)


def _centroid_all(st):
    """Case-frame centre of mass of the standing assembly."""
    return _rot_pt(st["com"] + [0, 0, st["z0"]], -st["beta"])


def _centroid(m):
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    return np.array(tm.center_mass)


def _rot_pt(p, beta):
    a = math.radians(beta)
    return np.array([p[0], p[1]*math.cos(a) - p[2]*math.sin(a), p[1]*math.sin(a) + p[2]*math.cos(a)])


def support(st, k):
    """Points of case and leg within 0.05 of the desk, as a CCW polygon in (x, y)."""
    pts = np.vstack([verts(st["W"](st["parts"]["case"])), verts(st["W"](st["legp"]))])
    low = pts[pts[:, 2] < 0.05][:, :2]
    return hull2d(low)


def tip_angle(poly, com, wt, F=None, at=None):
    """Smallest tilt about any support edge at which the body tips, with weight wt (N) at com and an optional
    force F (N, world vector) at point `at`. Returns [(edge midpoint, angle deg)]."""
    out = []
    for i in range(len(poly)):
        a, e = poly[i], poly[(i + 1) % len(poly)]
        d = (e - a)/np.linalg.norm(e - a)
        inward = np.array([-d[1], d[0]])                   # CCW polygon: interior on the left
        def sh(p): return np.dot(p[:2] - a, inward), p[2]
        s_g, h_g = sh(com)
        if F is not None:
            s_n, h_n = sh(at); F_s, F_h = np.dot(F[:2], inward), F[2]
        ang = None
        for al in np.arange(0, 90.01, 0.1):
            r = math.radians(al)
            rot = lambda s, h: (s*math.cos(r) - h*math.sin(r), s*math.sin(r) + h*math.cos(r))
            tau = -wt*rot(s_g, h_g)[0]
            if F is not None:
                sn, hn = rot(s_n, h_n)
                tau += sn*F_h - hn*F_s
            if tau >= 0:
                ang = al; break
        out.append(((a + e)/2, 90.0 if ang is None else ang))
    return out


# ---- plug and cable -------------------------------------------------------------------
def tube(pts, r):
    s = [m3.Manifold.sphere(r, 20).translate(list(p)) for p in pts]
    return union(m3.Manifold.batch_hull([s[i], s[i + 1]]) for i in range(len(s) - 1))


def leg_pt(vw_y, w, phi, k: Kick):
    """Case-frame point of the leg at folded y = vw_y, depth z = w (absolute), opened phi, x = 0."""
    return np.array([0.0, *vw_point((k.Y_H - vw_y, w - k.Z_H), phi, k)])


def plug_and_cable(b, c, k, case, geo, phi, st):
    """The straight plug standing up out of the crown, the cable looping back over the top and down
    behind the leg into the foot notch, then along the desk. Returns (shell, body, cable, notch point,
    cable direction past the notch) in the case frame."""
    tip = bbox(case)[1, 1]
    shell = prism(rect(-c.RECESS_W/2 + c.XY_CLR + 0.2, c.RECESS_W/2 - c.XY_CLR - 0.2, b.tip_y, tip + 0.01),
                  b.port_z - 1.3, b.port_z + 1.3)
    body = prism(rect(-k.PLUG_W/2, k.PLUG_W/2, tip, tip + k.PLUG_L), b.port_z - k.PLUG_T/2, b.port_z + k.PLUG_T/2)
    r = k.CABLE_D/2
    y1, RC = tip + k.PLUG_L + 3.0, 9.0
    pts = [np.array([0, tip + k.PLUG_L - 1, b.port_z])]
    for t in np.linspace(0, math.pi, 13):
        pts.append(np.array([0, y1 + RC*math.sin(t), b.port_z + RC - RC*math.cos(t)]))
    zback = geo["Z_BACK"] + r + 0.3                       # just behind the leg's back face
    pts.append(leg_pt(k.Y_FOOT + k.NOTCH_L + 6, zback, phi, k))
    pts.append(leg_pt(k.Y_FOOT + k.NOTCH_L - 1.0, zback, phi, k))
    notch = leg_pt(k.Y_FOOT + 2.5, geo["Z_PL"] + k.G + k.LEG_T/2, phi, k)
    pts.append(notch)
    # past the foot: down to the desk and away behind the stand, in world terms
    nw = _rot_pt(notch, st["beta"]) - [0, 0, st["z0"]]
    back = np.array([0, -1.0, 0])                           # world: the screen faces +y, so behind is -y
    touch = np.array([0, nw[1] - 4.0, r])
    far = touch + 40*back
    to_case = lambda p: _rot_pt(np.asarray(p) + [0, 0, st["z0"]], -st["beta"])
    pts += [to_case(touch), to_case(far)]
    cable = tube(pts, r)
    return shell, body, cable, notch, back


# ---- checks ------------------------------------------------------------------
def first_contact(f, lo, hi, tol=0.02):
    """Smallest value in [lo, hi] at which f(value) is True (f False at lo), by bisection."""
    if not f(hi): return math.inf
    while hi - lo > tol:
        mid = (lo + hi)/2
        lo, hi = (mid, hi) if not f(mid) else (lo, mid)
    return hi


def run_checks(b, c, k, feats, case, plate, leg, bump, pin, geo):
    static = {"case": case, "plate": plate}
    ov = lambda a, m: (a ^ m).volume()
    xb = geo["xb"]
    po = phi_open(k)
    stub_free = leg                                        # leg incl. stub, without the compliant bump

    print("\n1. The badge at rest touches nothing (min gap, mm); the USB-only case's fit is unchanged")
    for f in feats:
        s = f.solid()
        vol = sum(ov(s, m) for m in static.values()) + ov(s, leg)
        gaps = {n: s.min_gap(m, 3.0) for n, m in {**static, "leg": leg}.items()}
        n = min(gaps, key=gaps.get)
        check(vol < 1e-3, f"{f.name:26s} overlap {vol:.4f} mm^3", f"gap {gaps[n]:.2f} to {n}")
    for f in feats:                                        # badge pushed back its full float
        if f.name.startswith("plug"): continue
        g = f.solid(c.FLOAT).min_gap(leg, 3.0)
        if g < 3.0:
            check(g > 0.1, f"{f.name:26s} pushed back {c.FLOAT} still clears the leg", f"gap {g:.2f}")
    i, o = c.HDR_CLR, c.HDR_CLR + c.GUIDE_WALL
    for h in geo["hdrs"]:
        x0, y0, x1, y1 = h.outline.bounds()
        for wn, w in {"-x wall": rect(x0 - o, x0 - i, y0, y1), "+x wall": rect(x1 + i, x1 + o, y0, y1)}.items():
            g = plate ^ prism(w, -5, geo["FLOOR"])
            eng = b.hdr_top_z - bbox(g)[0, 2] if not g.is_empty() else 0.0
            span = bbox(g)[1, 1] - bbox(g)[0, 1] if not g.is_empty() else 0.0
            check(eng >= c.MIN_ENGAGE and span >= 5.0, f"{h.name} guide {wn}", f"engages {eng:.2f} deep over {span:.1f} of y")
    ring = prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0)
    check(ov(ring, case) > 0.5, "bezel lip overlaps the glass edge", f"{c.LIP_OVERLAP:.2f} per side")
    probe = m3.Manifold.cylinder(c.LIP_T + 2, (b.active_d + 1)/2, (b.active_d + 1)/2, SEG).translate([0, 0, -c.LIP_T - 1])
    check(ov(probe, case) < 1e-4, "window clears the active display + 1", f"window {2*(b.r - c.LIP_OVERLAP):.2f}")
    wall = bbox(case)[1, 1] - b.tip_y
    check(abs(wall - 2.95) < 0.1 and k.SHELL_LEN - wall >= k.MIN_PLUG_ENGAGE,
          "crown wall in front of the port unchanged; plug shell engages", f"{wall:.2f} wall, {k.SHELL_LEN - wall:.1f} engaged")
    check(ov(case, plate) < 1e-3, "case and plate do not overlap", f"{ov(case, plate):.4f} mm^3")
    s = ov(case, plate.translate([0, 0, geo["bh_p"]]))
    check(s > 1.0, "plate pulled back one bead height interferes (it snaps)", f"{s:.1f} mm^3")

    print("\n2. Hinge: pin, barrel, cheeks")
    rb = k.PIN_D/2 + k.BORE_CLR
    check(k.R_B - rb >= c.MIN_WALL, "barrel wall around the bore >= 1.2", f"{k.R_B - rb:.2f}")
    check(2*k.BORE_CLR >= 0.4 - 1e-9, "barrel bore clearance around the pin >= 0.4 (diametral)", f"{2*k.BORE_CLR:.2f}")
    y_top = k.Y_H + k.PIN_D/2
    cheek = math.sqrt(geo["R_OUT"]**2 - y_top**2) - k.X_CHEEK
    check(cheek >= 1.2, "cheek beside the pin hole >= 1.2 (thinnest, top of hole)", f"{cheek:.2f}")
    check(k.Y_H - k.PIN_D/2 - k.Y_CB >= 1.2, "cheek below the pin hole >= 1.2", f"{k.Y_H - k.PIN_D/2 - k.Y_CB:.2f}")
    check(ov(pin, leg) < 1e-3, "pin clears the barrel bore", f"{pin.min_gap(leg, 1.0):.2f} gap")
    held = geo["xo"] - k.X_CHEEK
    check(ov(pin, case) < 1e-3 and held >= 2.0, "pin runs through both cheeks (holes = pin size: a press fit)",
          f"{held:.1f} mm in each cheek")
    # the barrel ends ride the cheek faces by design (0.2 play each side); everything else must keep clear
    ends = yz_prism(rect(-40, 40, -40, 40), -xb - 2, -xb + 0.4) + yz_prism(rect(-40, 40, -40, 40), xb - 0.4, xb + 2)
    core = stub_free - (ends ^ prism(rect(-40, 40, k.Y_SH - 1, 40), -40, 40))
    for dx in (-k.AX_CLR + 0.01, 0.0, +k.AX_CLR - 0.01):
        worst = (math.inf, None)
        for a in np.arange(0, po - 1.0, 1.0):
            lp = open_leg(stub_free, a, k, dx)
            if sum(ov(lp, m) for m in (case, plate, pin)) > 1e-3: worst = (-1, a); break
            g = min(open_leg(core, a, k, dx).min_gap(m, 2.0) for m in (case, plate))
            if g < worst[0]: worst = (g, a)
        check(worst[0] >= 0.25, f"leg (x play {dx:+.2f}) swings 0..{po - 1:.0f} deg, >= 0.25 clear (barrel ends aside)",
              f"closest {worst[0]:.2f} at {worst[1]:.0f} deg" if worst[0] > 0 else f"hits at {worst[1]:.0f} deg")
    dxs = -k.AX_CLR + 0.05
    stop = first_contact(lambda a: ov(open_leg(stub_free, a, k, dxs), case) > 1e-4, po - 3, po + 15)
    bare = leg - cyl_x(-xb - k.STUB_L - 1, -xb + 0.02, *vw_point(k.STUB_VW, 0, k), k.STUB_R + 0.05)
    nxt = first_contact(lambda a: ov(open_leg(bare, a, k), case) > 1e-4, po - 3, 90.0, 0.1)
    check(abs(stop - po) < 1.0 and nxt > stop + 2, "hard stop: the stub meets the groove end, nothing else touches",
          f"stops at {stop:.1f} deg (designed {po:.1f}); without the stub the next contact is at {nxt:.1f}")
    e_min = k.STUB_L - 2*k.AX_CLR
    check(e_min >= 0.4, "stub stays >= 0.4 into its groove at any axial play", f"{k.STUB_L:.1f} - {2*k.AX_CLR:.1f} = {e_min:.1f}")
    ins = [t for t in np.arange(0.5, 20.01, 0.5) if ov(stub_free.translate([-k.AX_CLR, 0, t]), case) > 1e-3]
    check(not ins, "leg drops into the cheeks from behind, folded (then the pin goes in)",
          "clear for 20 mm" if not ins else f"blocked at {ins[0]:.1f}")

    print("\n3. Detent: flexure finger, bump into a dimple at closed and at open")
    dims = {}
    for a, nm in ((0.0, "closed"), (po, "open")):
        bp = bump_at(a, k, xb, -k.AX_CLR)
        v = ov(bp, case)
        past = ov(bp, yz_prism(rect(-40, 40, -40, 40), k.X_CHEEK, 40))
        check(v < 1e-4 and past > 1e-3, f"{nm}: bump sits in its dimple, {k.BUMP_H - 2*k.AX_CLR:.1f} past the cheek face",
              f"{past:.3f} mm^3 in the dimple, {v:.4f} interference")
    # between the dimples the bump rides the cheek face: finger deflection = bump past the face
    delta = k.BUMP_H - 2*k.AX_CLR
    mid = ov(bump_at(po/2, k, xb, -k.AX_CLR), case)
    L = k.V_ROOT - k.BUMP_VW[0]
    E, I = 2000.0, k.LEG_T*k.FING_W**3/12
    strain = 3*k.FING_W*delta/(2*L**2)
    P = 3*E*I*delta/L**3
    T = P*math.tan(math.radians(45) + math.atan(0.3))*math.hypot(*k.BUMP_VW)
    check(mid > 1e-3, "half way: the bump presses the cheek (the finger must bend)", f"{mid:.3f} mm^3")
    check(k.FING_W >= 1.2 and k.LEG_T >= 2.4, "finger section >= 2.4 x 1.2, bending in the layer plane",
          f"{k.LEG_T} x {k.FING_W}, printed flat")
    check(strain < 0.02, f"finger strain at {delta:.1f} mm deflection < 2% (cantilever {L:.1f} long)", f"{100*strain:.2f}%")
    leg_m = leg.volume()/1000*k.PETG*k.FILL
    hold = leg_m*9.81e-3*abs(k.Y_H - k.Y_FOOT)/2
    check(T > 5*hold, "detent torque > 5x the leg's own weight about the hinge (stays shut in a pocket)",
          f"{T:.1f} vs {hold:.2f} N.mm (finger {P:.1f} N)")
    dims.update(strain=strain, P=P, T=T, stop=stop)
    return dims


def run_stand_checks(b, c, k, feats, case, plate, leg, bump, pin, geo, stop):
    ov = lambda a, m: (a ^ m).volume()
    st = stance(b, c, k, feats, case, plate, leg, pin, geo, stop)
    wt = sum(st["mass"].values())*9.81e-3
    poly = support(st, k)
    com = st["com"]
    print(f"\n4. Standing (leg open {stop:.1f} deg): lean {st['lean']:.1f} deg back from vertical, "
          f"{sum(st['mass'].values()):.1f} g, centre of mass {com[2]:.1f} up")
    ys = poly[:, 1]
    front = poly[ys > ys.mean()]; rear = poly[ys < ys.mean()]
    fw, rw = np.ptp(front[:, 0]), np.ptp(rear[:, 0])
    check(fw > 10 and rw > 10, "stands on two lines: the heel flat and the leg's foot",
          f"heel {fw:.1f} wide, foot {rw:.1f} wide, {np.ptp(ys):.1f} deep")
    # why not the 15-25 deg the brief asked for: the case stands on its heel's BACK edge, and the badge makes
    # it front-heavy, so the forward margin is set by the lean alone (independent of the leg)
    cc = _centroid_all(st)
    heel_back = np.array([0.0, -geo["R_OUT"], geo["Z_BACK"] - k.BACK_CHAMFER])
    row = []
    for lean in (15, 20, 25, 30, 35, 40, round(st["lean"], 1)):
        p, q = _rot_pt(cc, 90 + lean), _rot_pt(heel_back, 90 + lean)
        row.append(f"{lean:g}:{math.degrees(math.atan2(q[1] - p[1], p[2] - q[2])):.0f}")
    print("  forward tip margin by lean (deg lean : deg margin)  " + "  ".join(row))
    names = lambda m: "sideways" if abs(m[0]) > 4 else "forward" if m[1] > com[1] else "backward"
    for mid, a in tip_angle(poly, com, wt):
        check(a >= 20, f"tips {names(mid):9s} only past {20} deg (weight only)", f"{a:.1f} deg")
    shell, body, cable, notch, back = plug_and_cable(b, c, k, case, geo, stop, st)
    nw = _rot_pt(notch, st["beta"]) - [0, 0, st["z0"]]
    for lbl, F in (("1 N along the cable, back over the desk", k.CABLE_N*back),
                   ("1 N straight down (cable over the desk edge)", np.array([0, 0, -k.CABLE_N]))):
        worst = min(tip_angle(poly, com, wt, F, nw), key=lambda t: t[1])
        check(worst[1] >= 15, f"with {lbl}: every edge >= 15 deg", f"worst {worst[1]:.1f} deg ({names(worst[0])})")
    # a tug in any horizontal direction at the notch: force that would tip it, vs the force that slides it
    ftip = math.inf
    for i in range(len(poly)):
        a, e = poly[i], poly[(i + 1) % len(poly)]
        d = (e - a)/np.linalg.norm(e - a); inward = np.array([-d[1], d[0]])
        s_g = np.dot(com[:2] - a, inward)
        ftip = min(ftip, wt*s_g/max(nw[2], 1e-6))       # worst case: the pull points straight out over this edge
    check(ftip > k.MU*wt, "a tug at the notch, any direction: it slides before it tips",
          f"tips at {ftip:.2f} N, slides at {k.MU*wt:.2f} N (notch {nw[2]:.1f} mm up)")
    check(ftip >= k.CABLE_N, "...and 1 N sideways at the notch would not tip it even if it could not slide",
          f"{ftip:.2f} N")

    print("\n5. Plug and cable path (straight plug 12 x 8 x 22, cable Ø4)")
    legp = st["legp"]
    for nm, m in (("shell", shell), ("plug body", body), ("cable", cable)):
        v = sum(ov(m, p) for p in (case, plate, legp))
        g = min(m.min_gap(p, 5.0) for p in (case, legp))
        check(v < 1e-3, f"{nm:9s} touches no part, stand open", f"gap {g:.2f}")
    check(ov(body, leg) < 1e-3, "plug body clears the leg folded too", f"{body.min_gap(leg, 5.0):.2f}")
    check(cable.min_gap(legp, 1.0) < 0.6, "cable lies in the foot notch (held sideways)",
          f"{cable.min_gap(legp, 1.0):.2f} to the notch walls")

    print("\n6. BOOT from behind: Ø2 stylus through the plate (and, folded, the leg)")
    x, y = geo["boot"]
    top = b.pcb_back_z + b.sw_cap_h
    pinr = lambda dz: m3.Manifold.cylinder(geo["Z_BACK"] + 45 - (top - dz), k.STYLUS_D/2, k.STYLUS_D/2, 32) \
        .translate([x, y, top - dz])
    for lbl, lg in (("folded", leg), ("open", legp)):
        for dz in (0.0, c.SW_TRAVEL):
            hit = sum(ov(pinr(dz), m) for m in (case, plate, lg, pin))
            check(hit < 1e-3, f"stylus {lbl}, {'pressed' if dz else 'at rest'}: 45 mm straight path clear",
                  f"{min(pinr(dz).min_gap(m, 5.0) for m in (plate, lg)):.2f} gap")
    act = next(f for f in feats if f.name == f"{c.BUTTON} actuator")
    check(ov(pinr(c.SW_TRAVEL), act.solid()) > 1e-3, f"stylus pressed {c.SW_TRAVEL} reaches the actuator",
          f"{geo['Z_BACK'] - top:.1f} mm deep from the back folded, {geo['Z_PL'] - top:.1f} open")

    print("\n7. Taking it apart")
    # the bead must climb out of its groove and past the bore lip to the counterbore: that is the snap
    unsnap = geo["FLOOR"] - (geo["zb_p"] - geo["bh_p"]/2) + 0.1
    hits = [t for t in np.arange(unsnap, 16.01, 0.5) if ov(plate.translate([0, 0, t]), case) > 1e-3]
    check(not hits, f"leg off: once unsnapped ({unsnap:.1f} mm) the plate slides straight out the back",
          "clear to 16 mm" if not hits else f"hits at {hits[0]:.1f}")
    free = first_contact(lambda t: ov(plate.translate([0, 0, t]), legp) > 1e-3, 0.0, 25.0, 0.1)
    check(free > unsnap + 1, "leg open: the plate unsnaps without touching the leg",
          f"{free:.1f} mm straight pull available, {unsnap:.1f} needed")
    return st, poly, shell, body, cable, nw, wt


# ---- output -------------------------------------------------------------------
def print_parts(c, k, case, plate, leg, bump, pin, geo):
    """Each part in its print orientation, flat face on the bed."""
    pin_flat = pin ^ prism(rect(-40, 40, -40, 40), k.Z_H - k.PIN_D/2 + 0.25, 40)
    return {
        "Kickstand - case.stl": case.translate([0, 0, c.LIP_T]),                                  # bezel down
        "Kickstand - back plate (BOOT hole).stl": plate.rotate([0, 180, 0]).translate([0, 0, geo["Z_PL"]]),
        "Kickstand - leg.stl": (leg + bump).rotate([0, 180, 0]).translate([0, 0, geo["Z_BACK"]]),  # back face down
        "Kickstand - hinge pin.stl": pin_flat.translate([0, -k.Y_H, -(k.Z_H - k.PIN_D/2 + 0.25)]),  # on its flat
    }


def main():
    b, c, k = Badge(), Case(), Kick()
    feats, case, plate, leg, bump, pin, geo = build(b, c, k)
    size = bbox(case)[1] - bbox(case)[0]
    print(f"Kickstand case Ø{2*geo['R_OUT']:.1f} x {size[2]:.2f} thick folded (USB-only case 12.45 + the leg's well), "
          f"{size[1]:.1f} tall with the crown; hinge axis y {k.Y_H}, z {k.Z_H}; leg stops at {phi_open(k):.1f} deg")
    dims = run_checks(b, c, k, feats, case, plate, leg, bump, pin, geo)
    st, poly, shell, body, cable, nw, wt = run_stand_checks(b, c, k, feats, case, plate, leg, bump, pin, geo, dims["stop"])
    print("\n8. Print files (every overhang <= 45 deg or a bridge <= 10 mm)")
    os.makedirs(STL, exist_ok=True)
    for name, m in print_parts(c, k, case, plate, leg, bump, pin, geo).items():
        export(m, STL + name, lambda m: m)
    if "--no-render" not in sys.argv:
        renders(b, c, k, feats, case, plate, leg, bump, pin, geo, dims, st, poly, shell, body, cable)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


def renders(b, c, k, feats, case, plate, leg, bump, pin, geo, dims, st, poly, shell, body, cable):
    os.makedirs(OUT, exist_ok=True)
    R = lambda m, L=1.0: m.refine_to_length(L)
    brass, leg_c, plate_c, steel = (0.82, 0.66, 0.32), (0.72, 0.55, 0.25), (0.62, 0.47, 0.22), (0.62, 0.64, 0.68)
    dark, blue, white, plug_c, cab, desk_c, red = ((0.09, 0.09, 0.10), (0.10, 0.32, 0.72), (0.92, 0.94, 0.96),
        (0.22, 0.22, 0.24), (0.10, 0.10, 0.11), (0.86, 0.84, 0.80), (0.85, 0.15, 0.12))
    po, W = dims["stop"], st["W"]
    legp = open_leg(leg + bump, po, k)
    disc = feats[0].solid()
    # a gauge face on the glass, so the renders read as a display
    face = m3.Manifold.cylinder(0.8, b.active_d/2, b.active_d/2, 120).translate([0, 0, -1.0])
    ticks = union(m3.Manifold.cube([0.7, 2.4, 0.1], True).translate([0, b.active_d/2 - 2.0, -1.05]).rotate([0, 0, a])
                  for a in range(-135, 136, 27))
    needle = m3.Manifold.cube([0.9, 11.0, 0.1], True).translate([0, 4.5, -1.08]).rotate([0, 0, -40])
    hub = m3.Manifold.cylinder(0.1, 1.4, 1.4, 32).translate([0, 0, -1.12])
    glass = [(face, blue), (ticks, white), (needle, (0.95, 0.55, 0.15)), (hub, white)]
    desk = prism(rect(-42, 42, -62, 42), -1.6, -0.01)
    stand = [(case, brass), (plate, plate_c), (legp, leg_c), (pin, steel), (disc, dark),
             (shell, steel), (body, plug_c), (cable, cab)] + glass
    T = lambda parts, extra=(): [(R(W(m)), col) for m, col in parts] + list(extra)

    render(T(stand, [(R(desk, 2.5), desk_c)]), OUT + "01-hero.png", elev=18, azim=28, zoom=1.2,
           title=f"Kickstand pocketwatch on the desk: leg open {po:.0f} deg, case leans back {st['lean']:.0f} deg")
    render(T(stand), OUT + "02-front-as-seen.png", elev=32, azim=90, zoom=1.25,
           title="What you see from your chair: crown and plug at 12, cable looped over the top")
    # side section through the middle
    cut = [(R(W(m).trim_by_plane([1, 0, 0], 0.0)), col) for m, col in stand if not W(m).trim_by_plane([1, 0, 0], 0.0).is_empty()]
    render(cut + [(R(desk.trim_by_plane([1, 0, 0], 0.0), 2.5), desk_c)], OUT + "03-side-section.png", elev=0, azim=180,
           zoom=1.1, title="Section at the centre: heel and foot on the desk, hinge at 12, cable through the foot notch")
    # back: folded, stylus through leg + plate onto BOOT
    x, y = geo["boot"]
    top = b.pcb_back_z + b.sw_cap_h
    stylus = m3.Manifold.cylinder(30, k.STYLUS_D/2, k.STYLUS_D/2, 32).translate([x, y, top])
    D = lambda m: R(m.rotate([90, 0, 0]))
    back = [(case, brass), (plate, plate_c), (leg + bump, leg_c), (pin, steel), (stylus, red)]
    render([(D(m), col) for m, col in back], OUT + "04-back-boot.png", elev=-28, azim=-62, zoom=1.2,
           title="Folded, from the back: a Ø2 stylus (red) goes through the leg and plate onto BOOT")
    back_open = [(case, brass), (plate, plate_c), (open_leg(leg + bump, po, k), leg_c), (pin, steel), (stylus, red)]
    render([(D(m), col) for m, col in back_open], OUT + "05-back-open-boot.png", elev=-15, azim=-120, zoom=1.1,
           title="Open: the plate's BOOT hole is clear of the leg")
    # folded puck, front 3/4: the pocketwatch
    puck = [(case, brass), (plate, plate_c), (leg + bump, leg_c), (pin, steel), (disc, dark)] + glass
    render([(D(m), col) for m, col in puck], OUT + "06-folded-puck.png", elev=18, azim=62, zoom=1.25,
           title=f"Folded: a Ø{2*geo['R_OUT']:.1f} x {geo['Z_BACK'] + c.LIP_T:.1f} puck, the leg flush in the back")
    # hinge detail: case top from behind (leg removed), and the leg's hinge end lifted off
    box = m3.Manifold.cube([30, 14, 30]).translate([-15, 11, -5])
    hd = [(case ^ box, brass), (plate ^ box, plate_c), ((leg + bump).translate([0, 0, 14]) ^ box.translate([0, 0, 14]), leg_c),
          (pin.translate([0, 0, 28]), steel)]
    render([(D(m), col) for m, col in hd], OUT + "07-hinge-detail.png", elev=35, azim=-62, zoom=1.0,
           title="Hinge, exploded: pin through both cheeks and the barrel; the split-off finger (right) carries the bump")
    # the two cheeks' inner faces side by side: stop groove + drop-in slot (-x), dimples (+x), pin holes
    cb = lambda x0, x1: m3.Manifold.cube([x1 - x0, 9.5, 8.5]).translate([x0, 13.2, 6.5])
    right = case ^ cb(k.X_CHEEK - 0.1, 14)
    left = (case ^ cb(-14, -k.X_CHEEK + 0.1)).rotate([0, 180, 0]).translate([0, 0, 33])
    render([(D(right), brass), (D(left), brass)], OUT + "07b-cheek-faces.png", elev=10, azim=180, zoom=1.0,
           light=(0.9, -0.2, 0.4), title="Inside faces of the hinge cheeks. Left (+x): 2 detent dimples. Right (-x): stop groove + drop-in slot")
    # print layout
    lay, xo = [], -60.0
    for name, m in print_parts(c, k, case, plate, leg, bump, pin, geo).items():
        bb = bbox(m)
        lay.append((R(m.translate([xo - bb[0, 0], -bb[:, 1].mean(), 0])), brass if "case" in name else
                    plate_c if "plate" in name else leg_c if "leg" in name else steel))
        xo += bb[1, 0] - bb[0, 0] + 8
    render(lay, OUT + "08-print-layout.png", elev=40, azim=-75, zoom=1.45,
           title="Print layout: case bezel down, plate back down, leg back down, pin on its flat. No supports")


if __name__ == "__main__":
    main()
