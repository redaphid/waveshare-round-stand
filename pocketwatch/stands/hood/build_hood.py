#!/usr/bin/env python3
"""
Hood stand: the USB-only pocketwatch case fused into a hooded gauge cup (the 2G DSM
A-pillar pod look) on a desk pillar with a coin-weighted oval base. One printed body plus
the BOOT-hole back plate from build_pocketwatch_usb.py.

  CUP    the case's bore, counterbore, snap groove, lip and USB-C slot, unchanged, inside
         a deep cup. In front of the lip a stepped bezel (straight risers, PHI cones) opens
         to the hood. The cup is cut by one oblique plane, so its top runs further forward
         than its bottom, and on the shipped "brow" variant the top of the cup also sweeps
         up into a solid brow. The same plane is the front of the pillar and of the base,
         and it is the print bed: the whole stand prints standing on its front face.
  PILLAR a U channel under the cup, open at the back. The straight USB-C plug drops into
         it from the crown (6 o'clock); the plug goes in from under the base along its own
         axis, and the cable bends back (BEND_R) into a tunnel under the base.
  BASE   oval plinth with two coin wells behind the pillar (5 US quarters each).
  PLATE  boot_hole_plate() from build_pocketwatch_usb.py, snapped into the back as before.

Variants (Hood): BROW is shipped; SCOOP (plain round cup) and COWL (brow with the opening
flared up under it) are built, checked and rendered as alternates.

Frames. Badge frame as in build_pocketwatch.py (origin glass centre, +y crown, +z back).
World: X right as the user sees it, Y away from the user, Z up. The badge crown points
down, the face tilts back ALPHA so it looks up at the eye. Print: the front plane on the bed.

Run with ~/.venvs/cad/bin/python from the repo root. --no-render for a fast check run.
"""
import sys, math, tempfile
sys.path.insert(0, "pocketwatch")
from dataclasses import dataclass
import numpy as np, manifold3d as m3, trimesh
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render, revolve)
from build_pocketwatch_usb import boot_hole_plate, PIN_D, SHELL_LEN, MIN_PLUG_ENGAGE, BACK_CHAMFER

STL = "stl/pocketwatch/stands/hood/"
PNG = "pocketwatch/stands/hood/renders/"
SCRATCH = tempfile.gettempdir() + "/hood-"   # the alternate's STL exists only for its print check

# straight USB-C plug and cable (brief: overmold ~22 long, 12 x 8)
PLUG_W, PLUG_T, PLUG_L, PLUG_CLR = 12.0, 8.0, 22.0, 0.5
SHELL_W, SHELL_T = 8.4, 2.6
CABLE_D, BEND_R = 4.5, 10.0
WITHDRAW = 7.2                # shell out of the 2.95 wall + 3.7 port, then it can leave sideways
STYLUS_L = 40.0               # a SIM tool / paperclip reaches in this far from the actuator
PETG, FILL = 1.27, 0.75       # g/cm^3; effective fill of a walls-heavy print (for mass, not COM)
BADGE_G, PLUG_G = 20.0, 8.0
COIN_D, COIN_T, COIN_G = 24.26, 1.75, 5.67   # US quarter
PULL_N, TIP_MIN = 1.0, 20.0


@dataclass(frozen=True)
class Hood:
    name: str
    BETA: float          # front plane vs face (deg): the hood's top runs 2 R tan(BETA) further than its bottom
    BROW: float = 0.0    # cowl: the hood's top raised this far above a round cup (0 = round)
    FLARE: bool = True   # ... and the opening under it flares up too (False: round opening, solid brow)
    ALPHA: float = 30.0  # face tilted back from vertical: looks up at an eye ~35 deg above the desk
    R_CO: float = 26.0   # cup outer radius
    R_F: float = 22.4    # bezel opening at the hood
    PHI: float = 33.0    # bezel cone half-angle from the axis. PHI + BETA <= 45 or it droops in print
    LAND: float = 1.0
    BAND_R: float = 1.6  # bezel band round the rim: proud of the cup
    BAND_L: float = 3.0  # ... and this long before its 45 deg chamfer    # straight bore in front of the last step, at the cup's bottom
    # stand, world frame
    T_B: float = 11.0    # base slab
    W_B: float = 34.0    # oval base: half-width
    L_B: float = 42.0    # ... half-length
    Y_B: float = -3.0    # ... centre (the face centre is at Y 0)
    Y_WELL: float = 10.0 # coin well centres
    W0: float = 16.0     # pillar half-width at the base
    W1: float = 13.0     # pillar half-width under the cup
    D0: float = 30.0     # pillar depth behind the front plane, at the base
    D1: float = 16.0     # ... under the cup
    WALL: float = 2.4    # pillar side walls and front fairing
    COINS: int = 5       # per well


BROW = Hood("brow", BETA=12.0, BROW=8.0, FLARE=False)   # shipped: round gauge face, solid brow over it
SCOOP = Hood("scoop", BETA=12.0)                        # alternate: plain round cup, oblique cut
COWL = Hood("cowl", BETA=12.0, BROW=10.0)               # alternate: brow with the opening flared up under it


# ---- frames ----------------------------------------------------------------
def to_world(h, Hc):
    return lambda m: m.rotate([-(90 + h.ALPHA), 0, 0]).translate([0, 0, Hc])


def to_badge(h, Hc):
    return lambda m: m.translate([0, 0, -Hc]).rotate([90 + h.ALPHA, 0, 0])


def wpt(h, Hc, p):
    """badge-frame point -> world point"""
    a = math.radians(h.ALPHA); s, c = math.sin(a), math.cos(a)
    x, y, z = p
    return np.array([x, -s*y + c*z, Hc - c*y - s*z])


def wvec(h, v):
    return wpt(h, 0.0, v)


# ---- the pod, badge frame --------------------------------------------------
def case_voids(b, c):
    """build() from build_pocketwatch_usb.py with the outside taken away: everything the case cuts,
    plus the plate. The pod's outside replaces the Ø43.6 case shell."""
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
    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())

    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4

    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    voids = union([prism(bore_xy, 0.0, Z_CASE + 1), prism(circle(R_REAR), FLOOR, Z_CASE + 1),
                   window.translate([0, 0, -c.LIP_T - 0.01]), groove_p, all_keep])

    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, m3.JoinType.Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    plate = prism(pocket.offset(-c.FIT_CLR - 0.03, Round), FLOOR, Z_CASE)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01)
    plate_nobead = plate + guides
    plate = plate_nobead + bead_p
    plate -= all_keep
    plate_nobead -= all_keep
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_cyl = m3.Manifold.cylinder(FLOOR + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([sw[c.BUTTON], b.sw_y, tip_z])
    plate += post_cyl - union(k for n, k in keep.items() if not n.startswith(c.BUTTON))
    boss_tip = bbox(prism(boss, 0, 1))[1, 1]
    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_OUT, FLOOR=FLOOR, Z_CASE=Z_CASE, bh_p=bh_p,
               groove_r_p=groove_r_p, hdrs=hdrs, sw=sw, post_cyl=post_cyl, boss_tip=boss_tip, bead=bead_p, pocket=pocket)
    return feats, voids, plate, plate_nobead, geo


def bezel_profile(b, c, h):
    """Stepped bezel in front of the lip: (r, z) corners, front-going. Risers are straight, treads
    are PHI cones (a flat tread would face the bed). Ends at R_F."""
    t = math.tan(math.radians(h.PHI))
    r, z = b.r - c.LIP_OVERLAP + c.LIP_BEVEL + 0.05, -c.LIP_T + 0.05
    pts = [(r, z)]
    for kind, v in (("riser", 0.6), ("cone", 18.9), ("riser", 0.6), ("cone", 20.6), ("riser", 0.6), ("cone", h.R_F)):
        if kind == "riser": z -= v
        else: z -= (v - r)/t; r = v
        pts.append((r, z))
    return pts


def oval(r, brow):
    """round below, raised `brow` at the top (badge -y is up in use)"""
    return circle(r) if brow <= 0 else (circle(r) + circle(r).translate([0, -brow])).hull()


def bezel_void(b, c, h):
    """One revolved profile (separate rings would share vertex circles and pinch on export)."""
    pts = bezel_profile(b, c, h)
    rf, zf = pts[-1]
    t = math.tan(math.radians(h.PHI))
    if h.BROW > 0 and h.FLARE:     # the cowl's opening flares up into the brow at PHI, then runs straight
        prof = [(0, pts[0][1])] + pts + [(0, zf)]
        dz = h.BROW/t
        flare = m3.Manifold.batch_hull([prism(circle(rf - 0.15), zf + 0.19, zf + 0.2),
                                        prism(oval(rf, h.BROW), zf - dz - 0.01, zf - dz),
                                        prism(oval(rf, h.BROW), -150, -149.99)])
    else:
        prof = [(0, pts[0][1])] + pts + [(rf, -150), (0, -150)]
        flare = None
    void = revolve(m3.CrossSection([[(r, z) for r, z in prof[::-1]]]))   # CCW in (r, z)
    return (void + flare if flare else void), zf


def front_plane(h, zf):
    """kept side n.p >= d0 (badge frame). Passes LAND in front of the last step at the bottom."""
    bt = math.radians(h.BETA)
    n = np.array([0.0, -math.sin(bt), math.cos(bt)])
    d0 = math.cos(bt)*(zf - h.LAND) - math.sin(bt)*h.R_F
    return n, d0


def plug_solids(b, geo, at=0.0):
    """shell, overmold, in the badge frame, `at` mm out along the plug axis"""
    y0 = geo["boss_tip"]
    shell = prism(rect(-SHELL_W/2, SHELL_W/2, y0 - SHELL_LEN, y0), b.port_z - SHELL_T/2, b.port_z + SHELL_T/2)
    body = prism(rect(-PLUG_W/2, PLUG_W/2, y0, y0 + PLUG_L), b.port_z - PLUG_T/2, b.port_z + PLUG_T/2)
    return shell.translate([0, at, 0]), body.translate([0, at, 0])


def build(h: Hood, b=Badge(), c=Case()):
    feats, voids, plate, plate_nobead, geo = case_voids(b, c)
    Z_CASE = geo["Z_CASE"]
    bez, zf = bezel_void(b, c, h)
    nP, d0 = front_plane(h, zf)

    cup = chamfered([circle(h.R_CO)], -150, Z_CASE, 0, BACK_CHAMFER)
    if h.BROW > 0:     # cowl: round at the back, the top sweeps up into a brow over the hood (PHI, as the inside)
        dz = h.BROW/math.tan(math.radians(h.PHI))
        cup = m3.Manifold.batch_hull([chamfered([circle(h.R_CO)], zf + 1, Z_CASE, 0, BACK_CHAMFER),
                                      prism(oval(h.R_CO, h.BROW), -150, zf - dz + 1)])
    # the plug's overmold reaches the boss face: nothing of the cup in front of the 3.0 mm wall
    y0 = geo["boss_tip"]
    plug_keep = prism(rect(-PLUG_W/2 - PLUG_CLR, PLUG_W/2 + PLUG_CLR, y0, y0 + PLUG_L + WITHDRAW + 2),
                      b.port_z - PLUG_T/2 - PLUG_CLR, Z_CASE + 1)      # out through the cup's back, not into the base

    # height: the plug's end, bent back at BEND_R, lays the cable on the desk in the tunnel under the base
    a = math.radians(h.ALPHA)
    end_b = np.array([0, y0 + PLUG_L, b.port_z])
    z_rest = CABLE_D/2 + 0.05
    Hc = z_rest + BEND_R*(1 + math.sin(a)) - wpt(h, 0.0, end_b)[2]
    W = to_world(h, Hc)
    nPw = wvec(h, nP)
    dPw = d0 + float(nPw @ np.array([0, 0, Hc]))
    yP = lambda Z: (dPw - nPw[2]*Z)/nPw[1]          # front plane at height Z

    # cable: straight out of the plug, a BEND_R arc back, then along the tunnel
    E = wpt(h, Hc, end_b)
    Cb = E + BEND_R*np.array([0, math.cos(a), -math.sin(a)])
    path = [E - wvec(h, [0, 6, 0])]
    for th in np.linspace(math.pi - a, 1.5*math.pi, 14):
        path.append(Cb + BEND_R*np.array([0, math.cos(th), math.sin(th)]))
    path.append(np.array([0, (h.Y_B + h.L_B) + 25, z_rest]))

    # pillar: a U channel with rounded corners, front on the plane, open at the back
    Zt = Hc - 0.55*h.R_CO
    rr = 3.0
    slab = lambda w, y0_, y1_, z, r=rr: prism(rect(-w + r, w - r, y0_ + r, y1_ - r).offset(r, Round), z, z + 0.01)
    cup_w = W(cup)
    # the neck takes the curve of the cup's underside, so the cup grows out of it
    under = cup_w.trim_by_plane(list(nPw), dPw) ^ m3.Manifold.cube([2*h.W1, 400, Zt + 8]).translate([-h.W1, -200, 0])
    pillar = m3.Manifold.batch_hull([slab(h.W0, yP(0) - 0.3, yP(0) + h.D0, 0.0), under])
    # keep the back open: the plate and badge come straight out behind the cup
    behind = prism(geo["pocket"].offset(1.5, Round), Z_CASE - 0.01, Z_CASE + 60)
    pillar -= W(behind)
    tf = h.WALL/nPw[1]
    zt2 = Zt + 12
    w2 = h.W1 + (h.W1 - h.W0)/Zt*12
    bay = m3.Manifold.batch_hull([slab(h.W0 - h.WALL, yP(h.T_B) + tf, 200, h.T_B, 1.0),
                                  slab(w2 - h.WALL, yP(zt2) + tf, 200, zt2, 1.0)])
    base_xs = circle(1.0).scale([h.W_B, h.L_B]).translate([0, h.Y_B])          # oval plinth, front cut by the plane
    base = chamfered([base_xs], 0, h.T_B, 0, 2.0)
    # coin wells, pointed toward +Y: that end is the ceiling when the front plane is on the bed
    rw = COIN_D/2 + 0.35
    well_xs = (circle(rw) + m3.CrossSection.square([0.5, 0.5], True).translate([0, rw*math.sqrt(2) - 0.25])).hull()
    x_well = rw + CABLE_D/2 + 0.4 + 1.6
    y_well = h.Y_WELL
    wells = union(prism(well_xs.translate([sx*x_well, y_well]), h.T_B - h.COINS*COIN_T - 0.6, h.T_B + 1) for sx in (-1, 1))
    # the plug goes in from underneath, straight up its own axis through a slot in the base; the cable
    # then lies on the desk in a tunnel under the base and leaves at the back
    hw = CABLE_D/2 + 0.4
    hx, zb1 = PLUG_W/2 + PLUG_CLR, b.port_z + PLUG_T/2 + PLUG_CLR
    axial = m3.Manifold.batch_hull([          # gabled behind: that wall is a ceiling on the bed, 13 wide
        prism(rect(-hx, hx, y0, y0 + PLUG_L + 80), b.port_z - PLUG_T/2 - PLUG_CLR, zb1),
        prism(rect(-0.05, 0.05, y0 + PLUG_L + 2, y0 + PLUG_L + 80), zb1, zb1 + hx)])
    tunnel = prism(rect(-hw, hw, Cb[1] - BEND_R, (h.Y_B + h.L_B) + 1), -1, CABLE_D + 0.8)
    cable_cut = tube(path[1:-1], CABLE_D/2 + 0.4, 16)

    # bezel band round the rim, built on the bed plane: 45 deg chamfer behind it, so it prints
    rot = [90 + h.ALPHA - h.BETA, 0, 0]
    cup_r = cup_w.rotate(rot)
    sl = lambda dz: cup_r.slice(dPw + dz)
    band = m3.Manifold.batch_hull([prism(sl(0.01).offset(h.BAND_R, Round), dPw - 1, dPw + h.BAND_L),
                                   prism(sl(h.BAND_L + h.BAND_R + 0.1).offset(-0.1, Round), dPw + h.BAND_L + h.BAND_R + 0.09, dPw + h.BAND_L + h.BAND_R + 0.1)])   # just inside: no shared vertices
    band = band.rotate([-rot[0], 0, 0])

    body = cup_w + band + (pillar - (bay - cup_w)) + base
    body -= W(union([voids, bez, plug_keep]))
    body -= union([wells, W(axial), tunnel, cable_cut])
    body = body.trim_by_plane(list(nPw), dPw).trim_by_plane([0, 0, 1], 0.0)

    geo.update(Hc=Hc, nPw=nPw, dPw=dPw, yP=yP, path=path, zf=zf, nP=nP, d0=d0, wells=wells,
               y_well=y_well, Zt=Zt, plug_keep=plug_keep)
    return feats, body, plate, plate_nobead, geo


# ---- checks ----------------------------------------------------------------
def tube(path, r, seg=24):
    s = m3.Manifold.sphere(r, seg)
    return union(m3.Manifold.batch_hull([s.translate(list(p0)), s.translate(list(p1))]) for p0, p1 in zip(path, path[1:]))


def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))


def run_checks(h, b, c, feats, body, plate, plate_nobead, plate_h, geo):
    B = to_badge(h, geo["Hc"])
    pod = B(body)                      # the stand, in the badge frame
    static = {"pod": pod, "plate": plate_h}          # the shipped plate: BOOT hole, no post
    badge_feats = [f for f in feats if not f.name.startswith("plug")]

    print("\n1. At rest: no badge feature overlaps the pod or the BOOT-hole plate (min gap, mm)")
    for f in feats:
        s = f.solid()
        vol = sum((s ^ m).volume() for m in static.values())
        gaps = {k: s.min_gap(m, 3.0) for k, m in static.items()}
        k = min(gaps, key=gaps.get)
        check(vol < 1e-3, f"{f.name:26s} overlap {vol:.4f} mm^3", f"gap {gaps[k]:.2f} to {k}")

    print("\n2. The stylus pushes the badge forward onto the lip; behind it the badge floats, then stops on the plate")
    def overlaps(dz): return sum((f.solid(dz) ^ m).volume() for f in badge_feats for m in static.values()) > 1e-4
    lo, hi = 0.0, 3.0
    while hi - lo > 0.005:
        mid = (lo + hi)/2
        lo, hi = (mid, hi) if not overlaps(mid) else (lo, mid)
    check(c.SW_TRAVEL < lo <= c.FLOAT + 0.05, f"badge float behind the lip: > switch travel, <= FLOAT {c.FLOAT}", f"{lo:.2f}")

    print("\n3. Bezel lip and hood")
    probe = m3.Manifold.cylinder(c.LIP_T + 2, (b.active_d + 1)/2, (b.active_d + 1)/2, SEG).translate([0, 0, -c.LIP_T - 1])
    check((probe ^ pod).volume() < 1e-4, f"window clears active display {b.active_d:.2f} + 1", f"window {2*(b.r - c.LIP_OVERLAP):.2f}")
    ring = prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0)
    check((ring ^ pod).volume() > 0.5, "lip overlaps the glass edge (retains it)", f"{c.LIP_OVERLAP:.2f} per side")
    r_win = b.r - c.LIP_OVERLAP
    beam = prism(circle(r_win - 0.02), -300, -0.01)
    check((beam ^ pod).volume() < 1e-4, "hood and bezel stay out of the window's straight-ahead view", f"Ø{2*r_win:.2f} beam, 300 mm")
    # how far off-axis the whole active area stays visible: top edge vs hood lip, bottom vs bezel
    sl = pod.trim_by_plane([1, 0, 0], -0.5).trim_by_plane([-1, 0, 0], -0.5)
    v = np.asarray(sl.to_mesh().vert_properties)[:, :3]
    ra = b.active_d/2
    up = v[(v[:, 1] < -ra) & (v[:, 2] < -0.5)]
    dn = v[(v[:, 1] > ra) & (v[:, 2] < -0.5)]
    ang_up = min(math.degrees(math.atan2(-p[1] - ra, -p[2])) for p in up)
    ang_dn = min(math.degrees(math.atan2(p[1] - ra, -p[2])) for p in dn)
    hood_len = -bbox(pod)[0, 2]
    check(ang_up >= 15, "whole display visible from >= 15 deg above the axis (hood)", f"{ang_up:.1f} deg, hood {hood_len:.1f} in front of the glass")
    check(ang_dn >= 15, "whole display visible from >= 15 deg below the axis (bezel)", f"{ang_dn:.1f} deg")
    eye = math.degrees(math.atan2(400, 550))
    check(abs(eye - h.ALPHA) < min(ang_up, ang_dn), "eye 400 up / 550 back sees the whole display",
          f"eye {eye:.0f} deg above the desk, face normal {h.ALPHA:.0f}")

    print("\n4. Plate, snap, walls")
    check((pod ^ plate_h).volume() < 1e-3, "pod and plate do not overlap", f"{(pod ^ plate_h).volume():.4f} mm^3")
    s = (pod ^ plate_h.translate([0, 0, geo["bh_p"]])).volume()
    check(s > 1.0, "plate pulled back one bead height interferes (it snaps)", f"{s:.1f} mm^3")
    check(abs(bbox(plate_h)[1, 2] - geo["Z_CASE"]) < 1e-3, "plate flush with the pod back", f"z {geo['Z_CASE']:.2f}")
    walls = {"wall behind the plate groove": h.R_CO - geo["groove_r_p"], "bezel lip": c.LIP_T,
             "hood wall": h.R_CO - h.R_F, "pillar walls / fairing": h.WALL, "base under the coin wells": h.T_B - h.COINS*COIN_T - 0.6,
             "step under the plate": geo["R_REAR"] - geo["R_BORE"]}
    for nm, t in walls.items():
        check(t >= c.MIN_WALL - 1e-9, f"{nm} >= {c.MIN_WALL}", f"{t:.2f}")

    print("\n5. Assembly paths, everything fused")
    T = geo["Z_CASE"] + b.hdr_top_z + 6
    worst = max(sum((f.solid(t) ^ pod).volume() for f in badge_feats) for t in np.arange(0, T, 0.5))
    check(worst < 1e-3, f"badge goes in from the back: {T:.0f} mm straight path clear", f"worst {worst:.4f} mm^3")
    pn = plate_nobead
    worst = max((pn.translate([0, 0, t]) ^ pod).volume() for t in np.arange(0, 25, 0.5))
    check(worst < 1e-3, "plate (bead aside) comes straight out the back, 25 mm clear", f"worst {worst:.4f} mm^3")
    bead_hits = (geo["bead"] ^ pod).volume()
    check(bead_hits < 1e-3, "bead sits in its groove at rest", f"{bead_hits:.4f} mm^3")
    x, y = geo["sw"][c.BUTTON], b.sw_y
    top = b.pcb_back_z + b.sw_cap_h
    pin = lambda dz: m3.Manifold.cylinder(STYLUS_L, PIN_D/2, PIN_D/2, 48).translate([x, y, top - dz])
    for dz, label in ((0.0, "at rest"), (c.SW_TRAVEL, f"pressed {c.SW_TRAVEL:.2f}")):
        hit = (pin(dz) ^ pod).volume() + (pin(dz) ^ plate_h).volume()
        check(hit < 1e-3, f"Ø{PIN_D:g} stylus, {STYLUS_L:.0f} long, {label}: clear of pod and plate", f"{hit:.4f} mm^3")
    act = next(f for f in feats if f.name == f"{c.BUTTON} actuator")
    v = (pin(c.SW_TRAVEL) ^ act.solid()).volume()
    check(v > 1e-3, f"stylus pressed {c.SW_TRAVEL:.2f} reaches the actuator", f"{v:.3f} mm^3")

    print("\n6. USB-C plug and cable")
    shell, plug = plug_solids(b, geo)
    wall = geo["boss_tip"] - b.tip_y
    check(SHELL_LEN - wall >= MIN_PLUG_ENGAGE, f"shell engages the port >= {MIN_PLUG_ENGAGE}",
          f"{SHELL_LEN - wall:.2f} of {SHELL_LEN}, {wall:.2f} wall in front of the port (unchanged)")
    hit = (shell ^ pod).volume() + (plug ^ pod).volume()
    check(hit < 1e-3, f"plug in: shell and {PLUG_W:g}x{PLUG_T:g}x{PLUG_L:g} overmold touch nothing", f"{hit:.4f} mm^3, gap {plug.min_gap(pod, 3):.2f}")
    a = math.radians(h.ALPHA)
    hits = max(((sh + pl) ^ pod).volume() for sh, pl in [plug_solids(b, geo, at) for at in np.arange(0, 70, 1.0)])
    lowest = wpt(h, geo["Hc"], [0, geo["boss_tip"] + PLUG_L + 70, b.port_z])[2]
    check(hits < 1e-3, "plug goes in from under the base, straight up its axis: 70 mm clear",
          f"{hits:.4f} mm^3, plug end {lowest:.0f} mm below the desk at the start")
    W_ = to_world(h, geo["Hc"])
    gapf = min(W_(sh + pl).min_gap(body, 3) for sh, pl in [plug_solids(b, geo, at) for at in np.arange(1, 70, 4)])
    check(gapf >= 0.3, "and keeps >= 0.3 off the fairing and base on the way", f"{gapf:.2f}")
    cab = tube(geo["path"], CABLE_D/2 - 0.15)
    hit = (cab ^ body).volume()
    check(hit < 0.05, f"Ø{CABLE_D:g} cable: {BEND_R:g} mm bend back into the groove, nothing in the way", f"{hit:.3f} mm^3")


def stability(h, b, body, plate, geo):
    print("\n7. Stability on the desk (world frame)")
    W = to_world(h, geo["Hc"])
    tm = to_tm(body)
    m_body = tm.volume/1000*PETG*FILL
    m_plate = plate.volume()/1000*PETG*FILL
    masses = [(m_body, tm.center_mass), (m_plate, to_tm(W(plate)).center_mass),
              (BADGE_G, wpt(h, geo["Hc"], [0, 0, 2.5])),
              (PLUG_G, wpt(h, geo["Hc"], [0, geo["boss_tip"] + PLUG_L/2, b.port_z]))]
    cw = bbox(geo["wells"])
    coins = [(2*h.COINS*COIN_G, np.array([0, geo['y_well'], h.T_B - 0.6 - h.COINS*COIN_T/2]))]
    foot = body.slice(0.05).hull()
    poly = np.asarray(foot.to_polygons()[0])
    exit_pt = np.array([0, bbox(body)[1, 1], CABLE_D/2])
    for label, ms in (("empty", masses), (f"{2*h.COINS} quarters in the wells", masses + coins)):
        M = sum(m for m, _ in ms)
        com = sum(m*np.asarray(p) for m, p in ms)/M
        Wn = M/1000*9.81
        worst_free, worst_pull, f_tip = 90.0, 90.0, math.inf
        for i in range(len(poly)):
            p0, p1 = poly[i], poly[(i + 1) % len(poly)]
            e = (p1 - p0)/np.linalg.norm(p1 - p0)
            out = np.array([e[1], -e[0]])                  # outward normal (CCW polygon)
            d = float((p0 - com[:2]) @ out)
            worst_free = min(worst_free, math.degrees(math.atan2(d, com[2])))
            # 1 N at the cable exit, any direction within 90 deg of straight back, up to 30 deg elevation
            r = exit_pt - np.array([p0[0], p0[1], 0])
            axis = np.array([e[0], e[1], 0])
            mmax = max(float(np.cross(r, PULL_N*np.array([math.sin(az)*math.cos(el), math.cos(az)*math.cos(el), math.sin(el)])) @ axis)
                       for az in np.radians(np.arange(-90, 91, 10)) for el in np.radians((0, 15, 30)))   # > 0 tips outward
            net = Wn*d - mmax
            worst_pull = min(worst_pull, math.degrees(math.atan2(net, Wn*com[2])))
            if mmax > 0: f_tip = min(f_tip, PULL_N*Wn*d/mmax)
        print(f"  {label}: {M:.0f} g (PETG at {FILL:.0%} of solid), COM {com[0]:+.1f} {com[1]:+.1f} {com[2]:.1f}; "
              f"tips over at {f_tip:.2f} N on the cable")
        check(worst_free >= TIP_MIN, f"{label}: tip angle >= {TIP_MIN:g} deg every direction", f"{worst_free:.1f} deg")
        if label == "empty":
            print(f"  [info] {label}: with {PULL_N:g} N on the cable{'':33s} {worst_pull:.1f} deg (negative = tips): load the wells")
        else:
            check(worst_pull >= TIP_MIN, f"{label}: still >= {TIP_MIN:g} deg with {PULL_N:g} N on the cable", f"{worst_pull:.1f} deg")
    return m_body


# ---- renders ---------------------------------------------------------------
GREY, TRIM, DARK, SCREEN, STEEL, CABLE, BRASS, GREEN, VIOLET, MON = (
    (0.56, 0.58, 0.63), (0.78, 0.78, 0.76), (0.08, 0.08, 0.09), (0.15, 0.48, 0.90), (0.72, 0.74, 0.78),
    (0.12, 0.12, 0.13), (0.82, 0.66, 0.32), (0.25, 0.70, 0.35), (0.62, 0.30, 0.80), (0.55, 0.45, 0.35))


def scene(h, b, c, feats, plate, geo, with_cable=True):
    W = to_world(h, geo["Hc"])
    fs = {f.name: f.solid() for f in feats if not f.name.startswith("plug")}
    out = [(W(fs["disc + tab"]), DARK),
           (W(m3.Manifold.cylinder(0.25, b.active_d/2, b.active_d/2, SEG).translate([0, 0, -0.3])), SCREEN),
           (W(plate), (0.45, 0.47, 0.52))]
    out += [(W(s), GREEN if n.startswith(c.BUTTON) else (0.93, 0.93, 0.88)) for n, s in fs.items() if n != "disc + tab"]
    if with_cable:
        shell, plug = plug_solids(b, geo)
        out += [(W(shell), STEEL), (W(plug), CABLE), (tube(geo["path"], CABLE_D/2), CABLE)]
    return out


def renders(h, b, c, feats, body, plate, geo, tag=""):
    R = lambda m: m.refine_to_length(2.0)
    sc = scene(h, b, c, feats, plate, geo)
    pre = PNG + (f"{tag}-" if tag else "")
    render([(R(body), GREY)] + [(R(m), col) for m, col in sc],
           pre + "hero.png", elev=16, azim=-48,
           title=f"Hood stand ({h.name}): 1.28 badge in a hooded cup on a pillar; straight USB-C hidden inside")
    if tag:
        return
    render([(R(body), GREY)] + [(R(m), col) for m, col in sc], pre + "front-as-seen.png", elev=h.ALPHA + 6, azim=-90,
           title=f"As you see it: eye {h.ALPHA + 6:.0f} deg above the desk, face tilted back {h.ALPHA:.0f} deg")
    # side section through the plug axis
    cut = []
    for m, col in [(body, GREY)] + sc:
        m = m.trim_by_plane([1, 0, 0], 0.0)
        if not m.is_empty(): cut.append((R(m), col))
    render(cut, pre + "section.png", elev=0, azim=180,
           title="Centre section: lip, bezel steps, brow; the plug drops into the pillar, the cable runs out under the base")
    # back: plate on, stylus in the BOOT hole
    Wd = to_world(h, geo["Hc"])
    x, y = geo["sw"][c.BUTTON], b.sw_y
    top = b.pcb_back_z + b.sw_cap_h
    stylus = Wd(m3.Manifold.cylinder(STYLUS_L, PIN_D/2, PIN_D/2, 32).translate([x, y, top]))
    handle = Wd(m3.Manifold.cylinder(14, 4, 4, 32).translate([x, y, top + STYLUS_L - 2]))
    render([(R(body), GREY), (R(Wd(geo["plate_h"])).refine_to_length(1.0), (0.86, 0.62, 0.30)), (stylus, STEEL), (handle, (0.85, 0.30, 0.20))] +
           [(R(m), col) for m, col in sc if col in (CABLE, STEEL)],
           pre + "back-boot.png", elev=28, azim=118,
           title="From behind: back plate (orange) snapped in flush, stylus straight into the BOOT hole")
    # print layout: as it sits on the bed, plus the plate
    P = lambda m: m.rotate([90 + h.ALPHA - h.BETA, 0, 0])
    pb = P(body); z0 = bbox(pb)[0, 2]
    pb = pb.translate([0, 0, -z0])
    flip = geo["plate_h"].rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]])
    fb = bbox(pb)
    flip = flip.translate([fb[1, 0] + 30, (fb[0, 1] + fb[1, 1])/2, 0])
    foot = prism(pb.slice(0.15), -0.6, 0.0)          # what touches the bed
    render([(R(pb), GREY), (R(flip), (0.86, 0.62, 0.30)), (foot, (0.85, 0.30, 0.20))], pre + "print-layout.png", elev=30, azim=-35,
           title="Print as placed: the stand on its front face (first layer in red), the plate flat. No supports")
    # exploded from the back
    E, lift = 30.0, np.array([0, 0, 18.0])          # out the back along the axis, then up off the base
    ex = [(R(body), GREY), (R(Wd(plate.translate([0, 0, 2*E])).translate(list(2*lift))), (0.86, 0.62, 0.30))]
    ex += [(R(Wd(f.solid().translate([0, 0, E])).translate(list(lift))), DARK if f.name == "disc + tab" else (0.93, 0.93, 0.88))
           for f in feats if not f.name.startswith("plug")]
    render(ex, pre + "exploded.png", elev=22, azim=128, title="Exploded from the back: stand, badge (screen first), plate")


def main():
    b, c = Badge(), Case()
    variants = [BROW, SCOOP, COWL]
    final = BROW
    for h in variants:
        print(f"\n===== hood: {h.name} =====")
        feats, body, plate, plate_nobead, geo = build(h, b, c)
        plate_h, _, _ = boot_hole_plate(b, c, plate, geo)
        geo["plate_h"] = plate_h
        sz = bbox(body)[1] - bbox(body)[0]
        print(f"stand {sz[0]:.0f} wide x {sz[1]:.0f} deep x {sz[2]:.0f} tall; face centre {geo['Hc']:.1f} up, tilted {h.ALPHA:.0f}; "
              f"front plane {h.BETA:.0f} deg to the face")
        if h is final:
            run_checks(h, b, c, feats, body, plate, plate_nobead, plate_h, geo)
            stability(h, b, body, plate, geo)
            print()
            export(body, STL + "Hood stand.stl",
                   lambda m: (lambda r: r.translate([0, 0, -bbox(r)[0, 2]]))(m.rotate([90 + h.ALPHA - h.BETA, 0, 0])))
            export(plate_h, STL + "Hood stand - back plate (BOOT hole).stl",
                   lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]]))
            if "--no-render" not in sys.argv:
                renders(h, b, c, feats, body, plate, geo)
        else:
            # alternate: every check runs and prints, but it is not shipped, so its results don't fail the build
            n = len(FAILS)
            run_checks(h, b, c, feats, body, plate, plate_nobead, plate_h, geo)
            stability(h, b, body, plate, geo)
            print()
            export(body, SCRATCH + f"alt-{h.name}.stl",
                   lambda m: (lambda r: r.translate([0, 0, -bbox(r)[0, 2]]))(m.rotate([90 + h.ALPHA - h.BETA, 0, 0])))
            if len(FAILS) > n:
                print(f"  ({h.name}: {len(FAILS) - n} check(s) failed; alternate only)")
            del FAILS[n:]
            if "--no-render" not in sys.argv:
                renders(h, b, c, feats, body, plate, geo, tag=f"alt-{h.name}")
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
