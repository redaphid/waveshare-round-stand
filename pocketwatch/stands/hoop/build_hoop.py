#!/usr/bin/env python3
"""
Watch-stand hoop: the USB-only pocketwatch case fused into a gimbal ring, on a turned base.

  hoop + case  ONE flat print, bezel down. An open ring around the case, joined to it by two
               trunnion spokes at 3 and 9 o'clock, ball finials either side of the crown, and a
               neck at 6 o'clock that ends in a tenon. Every member lies in the print plane, so
               every bending stress runs along the layers, never across them.
  base         a two-tier round plinth, flat on the bed. A slanted mortise holds the tenon at
               20 degrees back. Two snap arms on the tenon click into notches: no screw.
               A keyhole groove at the back grips the cable at desk height.
  plate        the existing USB-only BOOT-hole plate, unchanged: it snaps into the case back.

Crown UP: the plug rises out of the crown and the cable loops back over and down behind,
like a watch hanging by its bow. The display needs no firmware rotation this way up.

Badge frame as in build_pocketwatch.py (origin = glass face centre, +y to the USB tab,
+z backward). World: z up, the viewer at -Y. Run from the repo root with
~/.venvs/cad/bin/python pocketwatch/stands/hoop/build_hoop.py [--no-render]
"""
import sys, dataclasses, math
from dataclasses import dataclass
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3, trimesh
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)
import build_pocketwatch_usb as U
import render as render_mod      # pod/render.py, on the path via build_pocketwatch


class _Seamless(render_mod.Poly3DCollection):
    """pod/render.py's collection, with each triangle's edge drawn in its own colour: the anti-aliased seams
    between thousands of small triangles otherwise show as a dark star on big flat faces."""
    def __init__(self, *a, **k):
        k["edgecolors"] = k.get("facecolors"); k["linewidths"] = 0.25
        super().__init__(*a, **k)


render_mod.Poly3DCollection = _Seamless

STL = "stl/pocketwatch/stands/hoop/"
OUT = "pocketwatch/stands/hoop/renders/"
PETG = 1.27e-3                  # g/mm^3
G = 9.81e-3                     # N per gram


@dataclass(frozen=True)
class Stand:
    TILT: float = 20.0          # face leans back this far from vertical
    GAP: float = 3.0            # air between the case and the ring
    RW: float = 4.5             # ring, radial (in-plane: the load direction for every push on the plug)
    HD: float = 7.0             # ring depth = its print height (out-of-plane)
    EDGE: float = 0.6           # 45-degree chamfer on every hoop edge
    FILLET: float = 1.0         # in-plane fillet where members meet
    PIVOT_R: float = 4.6        # trunnion bosses on the ring at 3 and 9
    PIVOT_H: float = 9.0
    SPOKE_W: float = 6.0
    FIN_R: float = 3.4          # ball finials either side of the crown
    NECK_TOP: float = 8.0       # neck width under the ring
    NECK_BOT: float = 15.0      # neck width at the base
    NECK_H: float = 4.0         # base top to the lowest point of the ring
    BASE_R: float = 38.0        # lower tier
    BASE_T: float = 5.0
    TIER_R: float = 19.0        # upper tier, carries the mortise
    TIER_T: float = 13.0
    MORT_D: float = 11.5        # mortise depth, vertical: the snap arms need the length
    FIT: float = 0.12           # tenon in mortise, per side: 0.25 printed loose, the leaned walls are ~0.1 proud
    TANG_T: float = 1.5         # snap arm thickness (in-plane, along the layers)
    TANG_GAP: float = 2.0       # slot beside each arm: how far it can flex inward
    TANG_L: float = 10.5        # slot length up the neck from the tenon's bottom end
    BARB_H: float = 0.45        # barb height on each arm's outer face
    BARB_Y: float = 2.2         # barb crest above the tenon's bottom end
    BARB_RAMP: float = 2.6      # gentle lead-in length, so the tenon snaps in with a firm push
    BARB_BACK: float = 0.16     # the back face is nearly square (~70 deg): it holds a 20 N plug pull
    PETG_E: float = 1500.0      # MPa, along the layers
    BASE_SHIFT: float = 3.0     # base centre behind the neck, toward the leaning watch
    CABLE_D: float = 4.0        # typical USB-C cable; the keyhole grips 3.5-4.5
    KEY_D: float = 4.2
    KEY_MOUTH: float = 3.2
    KEY_ENTRY: float = 10.0     # open drop-in length before the keyhole narrows
    PLUG_W: float = 12.0        # straight plug body outside the crown
    PLUG_T: float = 8.0
    PLUG_L: float = 22.0
    FINGER: float = 5.0         # room each side of the plug body to grip it
    STYLUS_L: float = 40.0      # straight run behind the BOOT hole that must be free
    # loads
    BADGE_G: float = 20.0
    PLUG_G: float = 6.0         # plug + the cable it carries
    PULL_N: float = 1.0
    PUSH_N: float = 20.0        # USB-C insertion force, worst case of the 5-20 N spec
    BOOT_N: float = 3.0         # stylus on the BOOT switch
    PETG_MPA: float = 45.0      # in-plane (along-layer) tensile strength
    MIN_SF: float = 2.0
    MIN_TIP: float = 20.0
    MIN_SECTION: float = 3.0


# ---- the case, fused: build() from build_pocketwatch_usb.py with the stand added before the cuts ----
def build(b: Badge, c: Case, extra=None):
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
    case = chamfered([circle(R_OUT), boss], -c.LIP_T, Z_CASE, c.CHAMFER, U.BACK_CHAMFER)
    if extra is not None:
        case += extra                                     # the stand, fused before any cavity is cut
    case -= prism(bore_xy, 0.0, Z_CASE + 1)
    case -= prism(circle(R_REAR), FLOOR, Z_CASE + 1)
    case -= window.translate([0, 0, -c.LIP_T - 0.01])
    case -= groove_p
    case -= all_keep
    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, m3.JoinType.Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    plate = prism(pocket.offset(-0.18, Round), FLOOR, Z_CASE)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead_p
    plate += guides
    plate -= all_keep
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_cyl = m3.Manifold.cylinder(FLOOR + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([sw[c.BUTTON], b.sw_y, tip_z])
    plate += post_cyl - union(k for n, k in keep.items() if not n.startswith(c.BUTTON))

    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_OUT, FLOOR=FLOOR, Z_CASE=Z_CASE, bh_p=bh_p,
               groove_r_p=groove_r_p, hdrs=hdrs, sw=sw, post_cyl=post_cyl, boss=boss, bore_xy=bore_xy)
    return feats, case, plate, geo


# ---- placement: badge frame <-> world ---------------------------------------
class Frame:
    """Badge +x -> world -X (the viewer's left), badge +y (crown) -> up and back, badge +z -> back and down."""
    def __init__(self, tilt, H0):
        S, C = math.sin(math.radians(tilt)), math.cos(math.radians(tilt))
        self.S, self.C, self.H0 = S, C, H0
        self.R = np.array([[-1, 0, 0], [0, S, C], [0, C, -S]], float)
        self.t = np.array([0, 0, H0], float)

    def W(self, m):
        return m.transform(np.hstack([self.R, self.t[:, None]]))

    def pt(self, p):
        return self.R @ np.asarray(p, float) + self.t

    def vec(self, v):
        return self.R @ np.asarray(v, float)

    def up_b(self):
        """World +z in the badge frame (the normal of every horizontal plane)."""
        return self.R.T @ np.array([0, 0, 1.0])


# ---- 2D helpers -------------------------------------------------------------
def wedge(a0, a1, r=120):
    a = np.radians(np.linspace(a0, a1, 96))
    return m3.CrossSection([np.vstack([[0, 0], np.c_[r*np.cos(a), r*np.sin(a)]])])


def disc(r, x, y, n=96):
    return m3.CrossSection.circle(r, n).translate([x, y])


def polar(r, deg):
    return r*math.cos(math.radians(deg)), r*math.sin(math.radians(deg))


def arc_band(a0, a1, rc, w0, w1=None, n=120):
    """A band along radius rc from angle a0 to a1 (degrees), width w0 tapering to w1, round ends."""
    w1 = w0 if w1 is None else w1
    t = np.linspace(0, 1, n)
    a = np.radians(a0 + (a1 - a0)*t)
    w = w0 + (w1 - w0)*t
    outer = np.c_[(rc + w/2)*np.cos(a), (rc + w/2)*np.sin(a)]
    inner = np.c_[(rc - w/2)*np.cos(a), (rc - w/2)*np.sin(a)][::-1]
    band = m3.CrossSection([np.vstack([outer, inner])])
    if band.area() < 0: band = m3.CrossSection([np.vstack([outer, inner])[::-1]])
    return band + disc(w0/2, *polar(rc, a0)) + disc(w1/2, *polar(rc, a1))


def slab(cs, z0, z1, ch, steps=3):
    """Prism of any (non-convex) region with a 45-degree chamfer of ch on both faces, built as steps of
    ch/steps (0.2 mm: finer than a 0.3 layer, so it prints as the chamfer). Manifold's minkowski_sum
    leaves non-manifold edges on shapes like this one."""
    h = ch/steps
    out = [prism(cs, z0 + (steps - 1)*h, z1 - (steps - 1)*h)]
    for k in range(steps - 1):
        g = cs.offset(-(ch - (k + 1)*h), Round).simplify(0.01)
        out += [prism(g, z0 + k*h, z0 + (k + 1)*h), prism(g, z1 - (k + 1)*h, z1 - k*h)]
    return union(out)


# ---- the two silhouettes ----------------------------------------------------
def ring_radii(s, geo):
    R_HI = geo["R_OUT"] + s.GAP
    R_HO = R_HI + s.RW
    return R_HI, R_HO, (R_HI + R_HO)/2


def open_angle(s, geo, body):
    """Smallest opening each side of 12 o'clock that keeps the finials GAP clear of the crown boss."""
    _, _, Rc = ring_radii(s, geo)
    keep = body.offset(s.GAP - 0.05, Round)
    for half in np.arange(15.0, 70.0, 0.5):
        tips = union_cs([disc(s.FIN_R, *polar(Rc + s.FIN_R - s.RW/2, 90 + sg*half)) for sg in (-1, 1)])
        if ((arc_band(90 + half, 450 - half, Rc, s.RW) + tips) ^ keep).area() < 1e-6:
            return half
    raise RuntimeError("no opening clears the crown")


def silhouette(s, geo, kind):
    """2D outline of the stand in the badge plane (outside the case), and its member list for the beam check."""
    R_OUT = geo["R_OUT"]
    R_HI, R_HO, Rc = ring_radii(s, geo)
    body = circle(R_OUT) + geo["boss"]
    # neck: a trumpet flare from the ring down to the tier top (y_t), then straight on as the tenon
    y0, y1 = -R_HO + 1.5, geo["y_t"]
    t = np.linspace(0, 1, 13)
    half = s.NECK_TOP/2 + (s.NECK_BOT/2 - s.NECK_TOP/2)*t**2
    side = list(zip(half, y0 + (y1 - y0)*t))
    pts = side + [(s.NECK_BOT/2, y1 - 30)] + [(-s.NECK_BOT/2, y1 - 30)] + [(-x, y) for x, y in reversed(side)]
    neck = m3.CrossSection([pts[::-1]])
    if neck.area() <= 0: neck = m3.CrossSection([pts])
    if kind == "hoop":
        half = open_angle(s, geo, body)
        ring = arc_band(90 + half, 450 - half, Rc, s.RW)
        fins = union_cs([disc(s.FIN_R, *polar(Rc + s.FIN_R - s.RW/2, 90 + sg*half)) for sg in (-1, 1)])
        spokes = rect(R_OUT - 1.0, Rc, -s.SPOKE_W/2, s.SPOKE_W/2) + rect(-Rc, -R_OUT + 1.0, -s.SPOKE_W/2, s.SPOKE_W/2)
        pivots = [disc(s.PIVOT_R, sg*Rc, 0) for sg in (-1, 1)]
        flat = ring + fins + spokes + neck
        info = dict(half=half, pivots=pivots, Rc=Rc, arm_w=s.RW, lever=Rc, sides=2)
    else:   # crescent: one tapering arm from the neck round the viewer's left side, into the case at 2 o'clock
        a0, a1 = -90.0, 36.0
        ring = arc_band(a0, a1, Rc + 1.0, 8.0, 3.6)
        spoke_a = a1
        tx, ty = polar(R_OUT - 1.0, spoke_a)
        ox, oy = polar(Rc + 1.0, spoke_a)
        d = np.array([ox - tx, oy - ty]); d /= np.linalg.norm(d); nrm = np.array([-d[1], d[0]])*s.SPOKE_W/2
        tie = m3.CrossSection([[tuple(np.array([tx, ty]) - nrm), tuple(np.array([ox, oy]) - nrm),
                                tuple(np.array([ox, oy]) + nrm), tuple(np.array([tx, ty]) + nrm)]])
        if tie.area() < 0: tie = m3.CrossSection([list(reversed(tie.to_polygons()[0]))])
        pivots = [disc(s.PIVOT_R, ox, oy)]
        flat = ring + tie + neck
        w_at_0 = 8.0 + (3.6 - 8.0)*(0 - a0)/(a1 - a0)
        info = dict(half=None, pivots=pivots, Rc=Rc + 1.0, arm_w=w_at_0, lever=Rc + 1.0, sides=1)
    # fillet against the case shrunk 0.6, so the stand's outline near the case is buried in its wall instead
    # of lying on its surface (coincident faces break the union)
    f = s.FILLET
    # simplify: offsets leave vertices < 1e-8 apart, which an STL writer merges into non-manifold edges
    cs = (body.offset(-0.6, Round) + flat).offset(f, Round).offset(-f, Round).simplify(0.01)
    return cs, body, info


def union_cs(parts):
    out = parts[0]
    for p in parts[1:]: out = out + p
    return out


def stand_solids(s, c, geo, F, kind):
    """The stand in the badge frame (to fuse into the case) and the base in the world frame."""
    cs, body, info = silhouette(s, geo, kind)
    Z0 = -c.LIP_T
    hoop = slab(cs, Z0, Z0 + s.HD, s.EDGE)
    for p in info["pivots"]:
        hoop += chamfered([p], Z0, Z0 + s.PIVOT_H, s.EDGE, s.EDGE)
    hoop -= prism((circle(geo["R_OUT"]) + geo["boss"]).offset(-1.2, Round), Z0 - 1, Z0 + 20)
    # tenon: trimmed flat at the mortise floor (a world-horizontal plane), with two snap arms
    floor = s.TIER_T - s.MORT_D
    n = F.up_b()
    zm = Z0 + s.HD/2
    y_bot = (floor - F.H0 + F.S*zm)/F.C               # where the axis x=0, z=zm meets the floor plane
    tenon_nb = hoop.trim_by_plane(list(n), floor - F.H0)
    X0 = s.NECK_BOT/2
    yb = y_bot + s.BARB_Y
    def poly(pts):
        q = m3.CrossSection([pts])
        return q if q.area() > 0 else m3.CrossSection([pts[::-1]])
    barbs_cs = union_cs([poly([(sg*X0, yb - s.BARB_RAMP), (sg*(X0 + s.BARB_H), yb - 0.2),
                               (sg*(X0 + s.BARB_H), yb + 0.3), (sg*X0, yb + 0.3 + s.BARB_BACK)]) for sg in (-1, 1)])
    slots_cs = union_cs([rect(*sorted((sg*(X0 - s.TANG_T - s.TANG_GAP), sg*(X0 - s.TANG_T))), y_bot - 25, y_bot + s.TANG_L)
                         for sg in (-1, 1)])
    hoop = (hoop + prism(barbs_cs, Z0, Z0 + s.HD)).trim_by_plane(list(n), floor - F.H0)
    hoop -= prism(slots_cs, Z0 - 1, Z0 + s.HD + 1)

    base = chamfered([circle(s.BASE_R)], 0, s.BASE_T, 0.6, 1.5) + chamfered([circle(s.TIER_R)], 0, s.TIER_T, 0, 1.2)
    base = base.translate([0, geo["Yb"], 0])
    # mortise: the tenon's own section, grown by FIT, slid down its own plane (the insertion direction)
    # straight-sided up past the tier top, so the flare above never narrows the way out
    neck_cs = (cs ^ rect(-40, 40, -200, -ring_radii(s, geo)[1] + 0.5)) + rect(-s.NECK_BOT/2, s.NECK_BOT/2, -200, geo["y_t"] + 4)
    neck_cs = neck_cs + barbs_cs                       # the barbs get their notch, grown by FIT with the rest
    mort_b = prism(neck_cs.offset(s.FIT, m3.JoinType.Miter), Z0 - s.FIT, Z0 + s.HD + s.FIT)
    mort = F.W(mort_b).trim_by_plane([0, 0, 1], floor)
    base -= mort
    # cable keyhole at the back, centred on x = 0, along +Y to the rim
    yk0 = geo["Yb"] + s.TIER_R - 3.0
    zk = s.BASE_T - 0.4 - s.KEY_D/2
    key2 = disc(s.KEY_D/2, 0, zk, 48) + rect(-s.KEY_MOUTH/2, s.KEY_MOUTH/2, zk, s.TIER_T + 1)
    key = orient_keyhole(key2, yk0, geo["Yb"] + s.BASE_R + 5)
    # where the cable drops in from above: open to the full keyhole width, so it lies in without forcing
    key += orient_keyhole(disc(s.KEY_D/2, 0, zk, 48) + rect(-s.KEY_D/2, s.KEY_D/2, zk, s.TIER_T + 1), yk0 - 2.0, yk0 + s.KEY_ENTRY)
    base -= key
    screw = dict(y_bot=y_bot, zm=zm)
    return hoop, base, info, screw, dict(zk=zk, yk0=yk0, key=key, mort=mort, tenon_nb=tenon_nb)


def orient_keyhole(cs_xz, y0, y1):
    """Extrude a section drawn in (x, z) along world +Y from y0 to y1."""
    m = m3.Manifold.extrude(cs_xz, y1 - y0)                    # section in xy, length along +z
    T = np.array([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]], float)   # (x, y, z) -> (x, z + y0, y)
    return m.transform(T)


# ---- checks -----------------------------------------------------------------
def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))


def tip_angles(s, F, masses, contact_xy, contact_r, pull_pt, pull_dirs_deg):
    """Tilt each way until the weight (and a 1 N horizontal pull on the cable where it leaves the base)
    balances. Returns the smallest angle and its direction."""
    Wt = sum(m for m, _ in masses)*G
    com = sum(m*np.asarray(p) for m, p in masses)/sum(m for m, _ in masses)
    worst = (90.0, None, None)
    for phi in np.arange(0, 360, 2.5):
        u = np.array([math.cos(math.radians(phi)), math.sin(math.radians(phi))])
        s_max = u @ contact_xy + contact_r
        a = s_max - u @ com[:2]
        P = 0.0
        diff = (phi - pull_dirs_deg + 180) % 360 - 180
        if abs(diff) <= 90.0 + 1e-9: P = s.PULL_N
        ap = s_max - u @ pull_pt[:2]
        th = math.degrees(math.atan2(Wt*a - P*pull_pt[2], Wt*com[2] + P*ap))
        if th < worst[0]: worst = (th, phi, P)
    return worst, com, Wt


def run_stand_checks(s, b, c, feats, case, plate_h, base, geo, F, info, screw, extra, cable, plug, keyinfo):
    Z0 = -c.LIP_T
    print("\n7. Stand: what has to stay clear")
    tipb = 23.95
    plug_b = prism(rect(-s.PLUG_W/2, s.PLUG_W/2, tipb, tipb + s.PLUG_L), b.port_z - s.PLUG_T/2, b.port_z + s.PLUG_T/2)
    v = (F.W(plug_b) ^ (F.W(case) + base)).volume()
    check(v < 1e-3, f"plug body {s.PLUG_W:g} x {s.PLUG_T:g} x {s.PLUG_L:g} clear of hoop and base", f"{v:.4f} mm^3")
    fing = prism(rect(-s.PLUG_W/2 - s.FINGER, s.PLUG_W/2 + s.FINGER, tipb + 4, tipb + s.PLUG_L),
                 b.port_z - s.PLUG_T/2 - 2, b.port_z + s.PLUG_T/2 + 2)
    v = (fing ^ case).volume()
    gap = plug_b.min_gap(case - prism(rect(-30, 30, -60, tipb), -5, 30), 30)
    check(v < 1e-3, f"finger room {s.FINGER:g} mm each side of the plug body", f"nearest finial {gap:.1f} mm from the plug")
    v = (cable ^ (F.W(case) + base)).volume()
    check(v < 0.5, "cable loop clear of hoop and base (sits in the keyhole)", f"{v:.3f} mm^3")
    # BOOT stylus: straight in along -z from STYLUS_L behind the back face
    x, y = geo["sw"][c.BUTTON], b.sw_y
    top = b.pcb_back_z + b.sw_cap_h
    pin = m3.Manifold.cylinder(geo["Z_CASE"] + s.STYLUS_L - top, U.PIN_D/2, U.PIN_D/2, 48).translate([x, y, top])
    hit = (F.W(pin) ^ (F.W(case + plate_h) + base)).volume() + (F.W(pin) ^ cable).volume()
    end = F.pt([x, y, geo["Z_CASE"] + s.STYLUS_L])
    check(hit < 1e-3, f"BOOT: Ø{U.PIN_D:g} stylus runs {s.STYLUS_L:g} mm straight in from behind",
          f"its far end {end[2]:.0f} mm above the desk, {abs(end[0]):.0f} mm beside the cable")
    # plate out and badge in, along the badge axis
    disc_tab = next(f for f in feats if f.name == "disc + tab")
    stand = case - prism(circle(geo["R_OUT"]) + geo["boss"], -5, 40)
    path = prism(disc_tab.outline, 0, geo["Z_CASE"] + 30)
    v = (F.W(path) ^ base).volume() + (path ^ stand).volume()
    check(v < 1e-3, "badge goes in from the back past the hoop and base, 30 mm of path", f"{v:.4f} mm^3")
    path = prism(plate_h.project(), geo["Z_CASE"], geo["Z_CASE"] + 25)
    v = (F.W(path) ^ base).volume() + (path ^ case).volume()
    check(v < 1e-3, "plate comes straight out the back: nothing behind it for 25 mm", f"{v:.4f} mm^3")
    glass_front = prism(circle(b.r), -30, 0)
    v = (glass_front ^ (case - prism(circle(geo["R_OUT"]) + geo["boss"], -5, 40))).volume()
    check(v < 1e-3, "nothing of the stand in front of the glass", f"{v:.4f} mm^3")

    print("\n8. Joint: tenon, mortise, M3")
    hw = F.W(case)
    v = (hw ^ base).volume()
    check(v < 1e-2, "hoop and base do not overlap", f"{v:.4f} mm^3")
    seat = (hw.translate([0, 0, -0.05]) ^ base).volume()
    check(seat > 1.0, "tenon bottoms on the mortise floor (sets the height)", f"{seat:.1f} mm^3 at 0.05 down")
    out_dir = F.vec([0, 1, 0])
    stuck = max((F.W(keyinfo["tenon_nb"].translate([0, t, 0])) ^ base).volume() for t in np.arange(0.25, s.MORT_D/F.C + 1.0, 0.25))
    check(stuck < 1e-3, "tenon (barbs flexed in) slides straight in and out along the neck", f"{stuck:.4f} mm^3 in the way")
    side = (hw.translate([s.FIT + 0.05, 0, 0]) ^ base).volume()
    check(side > 1.0, f"tenon located sideways within {s.FIT + 0.05:.2f}", f"{side:.1f} mm^3 at {s.FIT + 0.05:.2f} over")
    # snap: two arms bending in the print plane (along the layers), a barb on each outer face
    h_def = s.BARB_H - s.FIT                              # each arm is pushed in this far while the barb passes the straight mortise
    L_eff = s.TANG_L - s.BARB_Y
    eps = 3*s.TANG_T*h_def/(2*L_eff**2)
    check(eps <= 0.02, "snap arm strain <= 2% while the barbs pass", f"{eps*100:.2f}% over {L_eff:.1f} mm, deflecting {h_def:.2f}")
    check(h_def >= 0.15, "barb overlaps the straight mortise by >= 0.15 (it really snaps)", f"{h_def:.2f}")
    check(s.TANG_T >= c.MIN_WALL and s.TANG_GAP >= c.MIN_WALL, "arm and slot widths >= min wall", f"arm {s.TANG_T:g}, slot {s.TANG_GAP:g}")
    k = 3*s.PETG_E*(s.HD*s.TANG_T**3/12)/L_eff**3        # N/mm per arm
    ramp = math.atan(s.BARB_H/(s.BARB_RAMP - 0.2))
    back = math.atan(s.BARB_BACK/s.BARB_H)
    f_in, f_out = 2*k*h_def*math.tan(ramp), 2*k*h_def/math.tan(back)
    check(f_in <= 30.0, "push to snap the hoop in (two arms, no friction) <= 30 N", f"{f_in:.1f} N, ramp {math.degrees(ramp):.0f} deg")
    check(f_out >= s.PUSH_N, f"pull to unsnap (back face {math.degrees(back):.0f} deg off square) >= a {s.PUSH_N:g} N plug pull", f"{f_out:.0f} N")
    slot_top = screw["y_bot"] + s.TANG_L
    gap = -ring_radii(s, geo)[0] - slot_top
    check(gap >= c.MIN_WALL, f"slots stop short of the gap inside the ring by >= {c.MIN_WALL}", f"{gap:.2f}")
    above_tier = (s.MORT_D/F.C) - s.TANG_L
    check(above_tier >= 0.5, "slots end inside the mortise, never open above the tier", f"{above_tier:.1f} mm to spare")
    worst_wall = 99.0
    for z in (s.TIER_T - s.MORT_D + 0.3, s.TIER_T - 0.6):
        hole = keyinfo["mort"].slice(z)
        tier = circle(s.TIER_R - 1.2).translate([0, geo["Yb"]])   # inside the top chamfer
        for wl in np.arange(0.2, 30.0, 0.1):
            if (hole - tier.offset(-wl, Round)).area() > 1e-3:
                worst_wall = min(worst_wall, wl - 0.1); break
    check(worst_wall >= c.MIN_WALL, f"tier wall round the mortise >= {c.MIN_WALL}", f"{worst_wall:.1f} (inside the chamfer)")
    floor_t = s.TIER_T - s.MORT_D
    check(floor_t >= c.MIN_WALL, f"floor under the mortise >= {c.MIN_WALL}", f"{floor_t:.1f}")

    print(f"\n9. Strength: bending along the layers, min section >= {s.MIN_SECTION:g} in the load direction")
    Rc, w, sides = info["lever"], info["arm_w"], info["sides"]
    check(w >= s.MIN_SECTION and s.HD >= s.MIN_SECTION, f"ring section {w:.1f} in-plane x {s.HD:g} deep",
          "in-plane takes the plug push, depth takes the cable and BOOT")
    sec = lambda wi, de: de*wi**2/6
    M_push = s.PUSH_N/sides*Rc
    sig = M_push/sec(w, s.HD)
    check(s.PETG_MPA/sig >= s.MIN_SF, f"{s.PUSH_N:g} N plug push, arm as a cantilever from the neck",
          f"M {M_push:.0f} N.mm, {sig:.1f} MPa, SF {s.PETG_MPA/sig:.1f}")
    reach = (23.95 + s.PLUG_L) + ring_radii(s, geo)[1]
    M_pull = s.PULL_N*reach/sides
    sig2 = M_pull/sec(s.HD, w)
    check(s.PETG_MPA/sig2 >= s.MIN_SF, f"{s.PULL_N:g} N backward on the plug end, out of plane",
          f"M {M_pull:.0f} N.mm, {sig2:.1f} MPa, SF {s.PETG_MPA/sig2:.0f}")
    nw = s.NECK_TOP
    M_neck = s.PULL_N*reach + s.BOOT_N*(F.H0 - s.TIER_T)
    sig4 = M_neck/sec(s.HD, nw)
    check(nw >= s.MIN_SECTION and s.PETG_MPA/sig4 >= s.MIN_SF,
          f"neck {nw:g} x {s.HD:g}: cable pull + BOOT press together, out of plane",
          f"M {M_neck:.0f} N.mm, {sig4:.1f} MPa, SF {s.PETG_MPA/sig4:.0f}")
    I = w*s.HD**3/12
    defl = (s.BOOT_N/sides)*Rc**3/(3*2000*I)
    check(defl < 0.1, f"{s.BOOT_N:g} N on BOOT from behind: hoop gives", f"{defl*1000:.0f} um (beam, E 2 GPa)")
    # layer lines: every horizontal slice of the stand outside the case is the same region, i.e. it is a pure
    # extrusion in print orientation, so no member's axis has a component across the layers.
    stand_only = extra - prism(circle(geo["R_OUT"] + 0.5) + geo["boss"].offset(0.5, Round), Z0 - 1, 40)
    stand_only = stand_only - prism(rect(-60, 60, -200, -ring_radii(s, geo)[1] - 1), Z0 - 1, 40)   # tenon is trimmed by a slanted plane
    stand_only = stand_only - union(prism(p.offset(0.6, Round), Z0 - 1, 40) for p in info["pivots"])
    areas = [stand_only.slice(z).area() for z in np.linspace(Z0 + s.EDGE + 0.05, Z0 + s.HD - s.EDGE - 0.05, 9)]
    check(max(areas) - min(areas) < 0.01*max(areas), "stand is a straight extrusion in print: layers run along every member",
          f"slice area {min(areas):.0f}..{max(areas):.0f} mm^2")


def stability(s, b, c, F, case, plate_h, base, geo, cable_exit):
    print("\n10. Stability: tilt until it tips, 1 N horizontal pull on the cable where it leaves the base")
    parts = {"hoop + case": (F.W(case), PETG), "plate": (F.W(plate_h), PETG), "base (100% infill)": (base, PETG)}
    masses = []
    for nm, (m, rho) in parts.items():
        tmm = to_tm(m)
        g = m.volume()*rho
        masses.append((g, tmm.center_mass))
        print(f"      {nm:22s} {g:5.1f} g at height {tmm.center_mass[2]:5.1f}")
    masses.append((s.BADGE_G, F.pt([0, 0, 2.5])))
    masses.append((s.PLUG_G, F.pt([0, 23.95 + s.PLUG_L/2, b.port_z])))
    print(f"      {'badge':22s} {s.BADGE_G:5.1f} g;  plug + cable {s.PLUG_G:.1f} g")
    worst, com, Wt = tip_angles(s, F, masses, np.array([0, geo["Yb"]]), s.BASE_R - 0.6, cable_exit, 90.0)
    print(f"      total {Wt/G:.0f} g, centre of mass X {com[0]:+.1f} Y {com[1] - geo['Yb']:+.1f} from the base centre, "
          f"{com[2]:.1f} high")
    check(worst[0] >= s.MIN_TIP, f"tip angle >= {s.MIN_TIP:g} every way, with the pull where it hurts",
          f"worst {worst[0]:.1f} deg toward {worst[1]:.0f} deg (pull {worst[2]:g} N)")
    nop = tip_angles(Stand(**{**s.__dict__, "PULL_N": 0.0}), F, masses, np.array([0, geo["Yb"]]), s.BASE_R - 0.6, cable_exit, 90.0)[0]
    print(f"      without the pull: worst {nop[0]:.1f} deg")
    # the base is the ballast: the lightest base that still gives MIN_TIP
    lo, hi = 0.0, 1.0
    for _ in range(30):
        k = (lo + hi)/2
        mk = [(g*k if i == 2 else g, p) for i, (g, p) in enumerate(masses)]
        th = tip_angles(s, F, mk, np.array([0, geo["Yb"]]), s.BASE_R - 0.6, cable_exit, 90.0)[0][0]
        lo, hi = (lo, k) if th >= s.MIN_TIP else (k, hi)
    print(f"      the base must weigh >= {masses[2][0]*hi:.0f} g ({100*hi:.0f}% of solid): print it at 100% infill")
    return com, masses


# ---- cable and plug for renders and the clearance check ---------------------
def tube(pts, r):
    sph = [m3.Manifold.sphere(r, 20).translate(list(p)) for p in pts]
    return union(m3.Manifold.batch_hull([a, q]) for a, q in zip(sph[:-1], sph[1:]))


def bezier(P, n=40):
    t = np.linspace(0, 1, n)[:, None]
    return ((1-t)**3)*P[0] + 3*((1-t)**2)*t*P[1] + 3*(1-t)*t*t*P[2] + t**3*P[3]


def cable_and_plug(s, b, F, geo, keyinfo):
    tipb = 23.95
    body = prism(rect(-s.PLUG_W/2, s.PLUG_W/2, tipb, tipb + s.PLUG_L).offset(-1.5, Round).offset(1.5, Round),
                 b.port_z - s.PLUG_T/2, b.port_z + s.PLUG_T/2)
    shell = prism(rect(-4.2, 4.2, b.tip_y - (U.SHELL_LEN - (tipb - b.tip_y)), tipb).offset(-0.6, Round).offset(0.6, Round),
                  b.port_z - 1.3, b.port_z + 1.3)
    boot = prism(rect(-3.5, 3.5, tipb + s.PLUG_L - 0.5, tipb + s.PLUG_L + 7).offset(-1.2, Round).offset(1.2, Round),
                 b.port_z - 2.6, b.port_z + 2.6)
    E = F.pt([0, tipb + s.PLUG_L + 6, b.port_z]); d0 = F.vec([0, 1, 0])
    zk, yk0 = keyinfo["zk"], keyinfo["yk0"]
    Q = np.array([0, yk0 + 3.0, zk])
    P = [E, E + 26*d0, Q + np.array([0, 20, 52.0]), Q + np.array([0, 0, 10])]
    pts = list(bezier(P, 46))
    pts += list(bezier([Q + np.array([0, 0, 10]), Q + np.array([0, 0, 3]), Q, Q + np.array([0, 7, 0])], 10))[1:]
    rim = geo["Yb"] + s.BASE_R
    pts += [np.array([0, rim, zk]), np.array([0, rim + 8, max(zk - 1.0, s.CABLE_D/2)]),
            np.array([0, rim + 30, s.CABLE_D/2])]
    cable = tube(pts, s.CABLE_D/2 - 0.1)
    return F.W(body), F.W(shell), F.W(boot), cable, np.array([0, rim, zk])


def dial(b):
    """A gauge face on the glass for the renders only: ticks, hands, a hub."""
    z0, z1 = -0.12, -0.02
    ticks = []
    for k in range(12):
        L, w = (2.6, 0.9) if k % 3 == 0 else (1.5, 0.55)
        r1 = 15.6
        t = rect(-w/2, w/2, r1 - L, r1).rotate(30*k)
        ticks.append(prism(t, z0, z1))
    hour = prism(rect(-0.7, 0.7, -1.5, 8.0).rotate(-60), z0, z1)
    minute = prism(rect(-0.5, 0.5, -2.0, 12.5).rotate(150), z0, z1)
    sec_ = prism(rect(-0.22, 0.22, -3.0, 13.5).rotate(-155), z0 - 0.02, z1 - 0.02)
    hub = prism(circle(1.4), z0 - 0.04, z1)
    return union(ticks), hour + minute, sec_, hub


def renders(s, b, c, feats, case, plate_h, base, geo, F, cable, plug, alt):
    rf = lambda m, L=1.0: m.refine_to_length(L)
    brass, plate_c, dark, white, red, steel, walnut, black, cream = (
        (0.84, 0.67, 0.33), (0.66, 0.50, 0.24), (0.07, 0.07, 0.09), (0.95, 0.95, 0.90), (0.88, 0.22, 0.18),
        (0.75, 0.77, 0.80), (0.36, 0.22, 0.13), (0.15, 0.15, 0.16), (0.96, 0.92, 0.80))
    disc_tab = next(f for f in feats if f.name == "disc + tab").solid()
    ticks, hands, sec_, hub = dial(b)
    body, shell, boot = plug
    face = [(rf(F.W(disc_tab)), dark), (rf(F.W(ticks), 0.6), cream), (rf(F.W(hands), 0.6), cream),
            (rf(F.W(sec_), 0.6), red), (rf(F.W(hub), 0.6), brass)]
    gear = [(rf(body), black), (rf(shell, 0.6), steel), (rf(boot), black), (rf(cable, 1.5), black)]
    whole = [(rf(F.W(case)), brass), (rf(F.W(plate_h)), plate_c), (rf(base, 1.6), walnut)] + face + gear
    H = f"{bbox(F.W(case) + base + body)[1, 2]:.0f}"

    render(whole, OUT + "01-hero.png", elev=14, azim=-58, zoom=1.2,
           title=f"Watch-stand hoop: case fused into a gimbal ring, crown up, cable as the chain  ({H} mm to the plug top)")
    render(whole, OUT + "02-front.png", elev=4, azim=-90, zoom=1.1, title="As you see it: face 20 deg back, crown up, no firmware flip")

    # back: BOOT stylus in the hole
    x, y = geo["sw"][c.BUTTON], b.sw_y
    top = b.pcb_back_z + b.sw_cap_h
    pin = m3.Manifold.cylinder(geo["Z_CASE"] + 22 - top, U.PIN_D/2, U.PIN_D/2, 32).translate([x, y, top])
    knob = m3.Manifold.cylinder(14, 3.0, 3.0, 32).translate([x, y, geo["Z_CASE"] + 22])
    render([(rf(F.W(case)), brass), (rf(F.W(plate_h)), plate_c), (rf(base, 1.6), walnut), (rf(F.W(pin), 0.8), red),
            (rf(F.W(knob), 0.8), red)] + gear,
           OUT + "03-back-boot.png", elev=30, azim=62, zoom=1.15, light=(0.45, 0.75, 0.5),
           title="From behind: plate free, a Ø2 pin goes straight into the BOOT hole (red), clear of the cable")

    # section on x = 0 (crown, plug, tenon, screw)
    parts = [(F.W(case), brass), (F.W(plate_h), plate_c), (base, walnut), (F.W(disc_tab), dark),
             (body, black), (shell, steel), (boot, black), (cable, black)]
    for f in feats:
        if f.name.startswith(("header", "JST")): parts.append((F.W(f.solid()), white))
    cut = []
    for m, col in parts:
        m = m.trim_by_plane([1, 0, 0], 0.0)
        if not m.is_empty(): cut.append((rf(m, 1.0), col))
    render(cut, OUT + "04-section.png", elev=0, azim=180, zoom=1.05,
           title="Section on the centre line: plug into the crown, 20 deg lean, snap arms and barbs in the mortise")

    # print layout: hoop+case bezel down, plate flat, base flat
    hb = bbox(case)
    lay_h = case.translate([0, 0, c.LIP_T])
    pl = plate_h.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]])
    lay = [(rf(lay_h), brass), (rf(pl.translate([62, 4, 0])), plate_c),
           (rf(base.translate([0, -geo["Yb"], 0]).translate([0, -96, 0]), 1.6), walnut)]
    render(lay, OUT + "05-print-layout.png", elev=38, azim=-70, zoom=1.1,
           title="Print: hoop + case bezel down, plate flat, base flat (100% infill). No supports, no screw.")

    # alternate silhouette
    ac, abase = alt
    render([(rf(F.W(ac)), brass), (rf(F.W(plate_h)), plate_c), (rf(abase, 1.6), walnut)] + face + gear,
           OUT + "06-alternate-crescent.png", elev=14, azim=-58, zoom=1.2,
           title="Alternate: crescent cantilever arm (not built: one arm carries it all, SF 2.2 vs 3.9)")

    # exploded along the assembly moves: hoop up its neck, badge and plate out the back, M3 below
    up = F.vec([0, 1, 0]); back = F.vec([0, 0, 1])
    mv = lambda m, v: m.translate(list(v))
    hoop_up = 34*up
    ex = [(rf(mv(F.W(case), hoop_up)), brass), (rf(mv(F.W(disc_tab), hoop_up + 26*back)), dark),
          (rf(mv(F.W(plate_h), hoop_up + 46*back)), plate_c), (rf(base, 1.6), walnut)]
    for f in feats:
        if f.name.startswith(("header", "JST", "BOOT", "RESET")):
            ex.append((rf(mv(F.W(f.solid()), hoop_up + 26*back), 0.8), white))
    render(ex, OUT + "07-exploded.png", elev=10, azim=150, zoom=1.0, light=(0.45, 0.75, 0.5),
           title="Assembly: badge in from the back, plate snaps on; hoop pushes down its neck until the arms click")


s_screw = {}


def main():
    s, b, c = Stand(), Badge(), Case()
    # pass 1: the bare case gives R_OUT and the boss; the stand is drawn around them
    feats, case0, plate0, geo = build(b, c)
    R_HI, R_HO, Rc = ring_radii(s, geo)
    S, C = math.sin(math.radians(s.TILT)), math.cos(math.radians(s.TILT))
    Z0 = -c.LIP_T
    H0 = s.TIER_T + s.NECK_H + C*R_HO + S*(Z0 + s.HD)        # lowest ring edge sits NECK_H above the tier
    F = Frame(s.TILT, H0)
    geo["Yb"] = 0.0
    built = {}
    for kind in ("hoop", "crescent"):
        geo_k = dict(geo)
        # base centre under the watch's centre of mass, near enough; refined below
        zm = Z0 + s.HD/2                                      # neck mid-plane meets the tier top here
        geo_k["y_t"] = (s.TIER_T - F.H0 + F.S*zm)/F.C
        geo_k["Yb"] = F.pt([0, geo_k["y_t"], zm])[1] + s.BASE_SHIFT
        extra, base, info, screw, keyinfo = stand_solids(s, c, geo_k, F, kind)
        built[kind] = (extra, base, info, screw, keyinfo, geo_k)

    extra, base, info, screw, keyinfo, geo = built["hoop"]
    s_screw.update(screw)
    feats, case, plate, geo2 = build(b, c, extra)
    geo.update({k: v for k, v in geo2.items()})
    plate_h, x, y = U.boot_hole_plate(b, c, plate, geo)

    print(f"Hoop: case Ø{2*geo['R_OUT']:.1f}, ring {2*R_HI:.1f}-{2*R_HO:.1f}, open {2*info['half']:.0f} deg over the crown; "
          f"tilt {s.TILT:g}; base Ø{2*s.BASE_R:g}")
    print("\n--- the case, fused (checks from build_pocketwatch_usb.py) ---")
    run_case_checks(b, c, feats, case, plate, geo)
    U.run_hole_checks(b, c, feats, case, plate_h, x, y, geo)

    body, shell, boot, cable, cable_exit = cable_and_plug(s, b, F, geo, keyinfo)
    run_stand_checks(s, b, c, feats, case, plate_h, base, geo, F, info, screw, extra, cable, (body, shell, boot), keyinfo)
    stability(s, b, c, F, case, plate_h, base, geo, cable_exit)

    # the alternate, for comparison only
    a_extra, a_base, a_info, _, _, _ = built["crescent"]
    _, a_case, _, _ = build(b, c, a_extra)
    print("\n11. Silhouettes compared (beam estimate, same section rule)")
    for nm, inf in (("hoop", info), ("crescent", a_info)):
        sec = s.HD*inf["arm_w"]**2/6
        sig = s.PUSH_N/inf["sides"]*inf["lever"]/sec
        print(f"      {nm:9s} arms {inf['sides']}, arm {inf['arm_w']:.1f} x {s.HD:g}, lever {inf['lever']:.1f}: "
              f"{s.PUSH_N:g} N push -> {sig:.1f} MPa, SF {s.PETG_MPA/sig:.1f}")

    print()
    export(case, STL + "Hoop stand - hoop and case.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(base, STL + "Hoop stand - base.stl", lambda m: m)
    # a roomier mortise (0.12 is the default; 0.25 printed loose with the screw design), for a printer that runs tight
    for fit, tag in ((0.18, "roomier"),):
        s2 = dataclasses.replace(s, FIT=fit)
        _, base2, _, _, ki2 = stand_solids(s2, c, built["hoop"][5], F, "hoop")
        hw = F.W(case)
        check((hw ^ base2).volume() < 1e-2, f"base ({tag}): hoop and base do not overlap", f"fit {fit}")
        stuck = max((F.W(ki2["tenon_nb"].translate([0, t, 0])) ^ base2).volume() for t in np.arange(0.25, s.MORT_D/F.C + 1.0, 0.25))
        check(stuck < 1e-3, f"base ({tag}): tenon still slides straight in", f"{stuck:.4f} mm^3 in the way at {fit} per side")
        export(base2, STL + f"Hoop stand - base ({tag}, {fit:g}).stl", lambda m: m)
    flip = lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]])
    export(plate_h, STL + "Hoop stand - back plate (BOOT hole).stl", flip)
    # the same back plate with a push-the-plastic BOOT flexure instead of the hole (checks run in build_pocketwatch_usb.py)
    for clr, tag in ((U.PLATE_DISC_CLR, "button"), (U.PLATE_DISC_CLR_ROOMY, "button, roomy")):
        _, _, plate_b, _ = U.build(b, c, clr, button=True)
        export(plate_b, STL + f"Hoop stand - back plate ({tag}).stl", flip)
    tot = bbox(F.W(case) + base + body)
    print(f"\nStanding: {tot[1, 0] - tot[0, 0]:.0f} wide x {tot[1, 1] - tot[0, 1]:.0f} deep x {tot[1, 2]:.0f} tall to the plug top")
    if "--no-render" not in sys.argv:
        renders(s, b, c, feats, case, plate_h, base, geo, F, cable, (body, shell, boot), (a_case, a_base))
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


def run_case_checks(b, c, feats, case, plate, geo):
    """U.run_checks, except the wall in front of the port is measured on the crown itself (the hoop's
    finials may reach higher than the boss tip)."""
    crown = case ^ prism(rect(-5, 5, b.tip_y - 1, 60), b.port_z - 3, b.port_z + 3)
    wall = bbox(crown)[1, 1]
    orig = U.bbox
    U.bbox = lambda m: (np.array([[0, 0, 0], [0, wall, bbox(m)[1, 2]]]) if m is case else orig(m))
    try:
        U.run_checks(b, c, feats, case, plate, geo)
    finally:
        U.bbox = orig


if __name__ == "__main__":
    main()
