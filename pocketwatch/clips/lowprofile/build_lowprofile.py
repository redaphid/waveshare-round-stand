#!/usr/bin/env python3
"""
Lowprofile: the USB-only pocketwatch case fused into a small gauge-pod housing that
hangs at a monitor's top corner on a tool-free spring clip.

Three printed parts (plus the stock BOOT-hole back plate):
  HOUSING  the case (bore, lip, crown boss, USB-C slot, plate groove: copied from
           build_pocketwatch_usb.build()) inside a hooded body: a 2.4 mm conical cowl
           in front of the glass, a flat chamfered brow on top, a ribbed spine down
           the side that bears on the monitor's side face, and a shoe that rests on
           the clip with a dovetail ridge under it. Canted 15 degrees toward you.
  CLIP     one flat part per edge-thickness band (S 8-16, M 16-24, L 24-32 mm):
           a deck over the monitor top, a 2 mm front lip on the bezel, and a
           flexure leaf down the back whose tip nub presses the monitor. It prints
           lying on its top face, so the leaf bends in the print plane.
  PLATE    the USB-only BOOT-hole back plate (pressed from behind with a pin).

Why a corner: the deck carries the weight on the monitor top and the spine bears
on the side face, so gravity and the cable seat it; the clamp only has to stop it
walking sideways (friction, checked below with a safety factor).

Use frame (for checks and renders): the monitor's top-right corner is the origin.
+x outboard (to the right, away from the screen), +y backward (into the monitor),
+z up. The monitor occupies x<0, 0<y<T, z<0. You sit at -y.
Badge frame (= the housing's print frame): see build_pocketwatch.py. +y toward
the USB-C tab, which points DOWN in use (rotate the display 180 in firmware).

Run from the repo root:  ~/.venvs/cad/bin/python pocketwatch/clips/lowprofile/build_lowprofile.py [--no-render]
"""
import sys, math
from dataclasses import dataclass
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)
from build_pocketwatch_usb import run_checks as usb_fit_checks, boot_hole_plate, run_hole_checks, BACK_CHAMFER, PIN_D

HERE = "pocketwatch/clips/lowprofile/"
STL = "stl/pocketwatch/clips/lowprofile/"
OUT = HERE + "renders/"
Miter = m3.JoinType.Miter
RIDGE_BACK = 1.0   # ridge (and the groove's stop) ends this far in front of the back face
RIDGE_Z0 = 0.3     # the dovetail ridge starts one layer off the bed (flush, it pinches the mesh)



@dataclass(frozen=True)
class Mount:
    PHI: float = -15.0         # cant about z: the face turns 15 degrees toward you (inboard)
    HOOD_D: float = 2.4        # conical cowl in front of the bezel lip, 45 degrees
    HOOD_TOP: float = 2.4      # body above the case outline (the brow)
    HOOD_CH: float = 8.0       # the hood's outboard top corner, cut at 45 degrees
    BROW_CH: tuple = (2.0, 3.0)  # brow front-top chamfer: 2.0 down x 3.0 back (34 deg from vertical in print)
    DECK_T: float = 3.6        # clip deck over the monitor top
    BROW_T: float = 3.0        # shoe on the deck; brow top = DECK_T + BROW_T above the monitor
    B: float = 14.0            # shoe / clip saddle width inboard of the corner
    SPINE_GAP: float = 5.0     # monitor side face to the cowl's inboard edge, at the front
    BEAR_Y0: float = 1.0       # spine's bearing band starts this far behind the monitor's front face
    BEAR_D: float = 5.5        # ... and is this deep (must sit inside the thinnest edge, 8 mm)
    SPINE_BOT: float = -38.0   # spine bottom (z): the lower it bears, the less side force
    RIB_W: float = 1.2
    RIB_D: float = 0.9
    RIB_PITCH: float = 3.0
    DT_N: float = 5.0          # dovetail neck (at the deck top)
    DT_D: float = 2.0          # dovetail depth; 45-degree flanks, base = N + 2D
    DT_FIT: float = 0.15       # per side
    CLIP_END: float = -0.3     # clip stops short of the monitor side plane, so the spine bears on the monitor
    LIP_W: float = 2.4         # front lip thickness (y)
    LIP_REACH: float = 2.0     # how far the lip comes down the front bezel
    BEZEL_MIN: float = 2.5     # thinnest top bezel this is drawn for
    REACH: float = 12.4        # leaf / nub depth down the back of the monitor
    LEAF_T: float = 2.4        # flexure thickness (bends through this, in the print plane)
    LEAF_L: float = 54.0       # flexure free length
    NUB_N: float = 4.0         # tip nub stands this far in front of the leaf
    NUB_W: float = 6.0
    HORN: float = 13.5         # 45-degree lead-in horn past the nub (slide-on ramp and finger tab)
    SLOT: float = 0.6          # leaf to deck: moving part, printed flat (>= 0.4)
    DELTA0: float = 5.0        # leaf preload at the thin end of each band
    ROOT_MARGIN: float = 3.0   # leaf root behind the thickest edge of the band
    E: float = 1800.0          # MPa, printed PETG along the extrusion (bulk ~2000; +-25%)
    MU: float = 0.30           # felt pad on plastic (static); TPU strip ~0.6
    MU_TPU: float = 0.60
    BADGE_G: float = 20.0      # badge mass (brief)
    PETG: float = 1.27         # g/cm^3, solid (overestimates the load: conservative)
    CABLE_N: float = 1.0
    STRAIN_MAX: float = 0.02
    SF_MIN: float = 2.0


SIZES = {"S": (8.0, 16.0), "M": (16.0, 24.0), "L": (24.0, 32.0)}
CL = math.cos(math.radians(Mount.PHI)); SL = math.sin(math.radians(Mount.PHI))


def poly(pts):
    """CrossSection from one polygon, whatever its winding."""
    a = sum(x0*y1 - x1*y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return m3.CrossSection([pts if a > 0 else pts[::-1]])


def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def mat(R, t):
    return [[R[0][0], R[0][1], R[0][2], t[0]], [R[1][0], R[1][1], R[1][2], t[1]], [R[2][0], R[2][1], R[2][2], t[2]]]


class Frame:
    """badge -> use: X = cos*x - sin*z + xc ; Y = sin*x + cos*z + yc ; Z = -y + zc."""
    def __init__(self, xc, yc, zc):
        self.t = np.array([xc, yc, zc])
        self.R = np.array([[CL, 0, -SL], [SL, 0, CL], [0, -1, 0]])

    def use(self, m):   return m.transform(mat(self.R, self.t))
    def badge(self, m): return m.transform(mat(self.R.T, -self.R.T @ self.t))
    def pt(self, p):    return self.R @ np.asarray(p, float) + self.t
    def axis(self):     return self.R @ np.array([0, 0, 1.0])   # badge +z (backward along the case axis)


# ---- the case, copied from build_pocketwatch_usb.build() with the outer solid swapped for the housing body ----
def build_housing(b: Badge, c: Case, m: Mount):
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

    # placement: cowl's inboard edge SPINE_GAP from the side face at the front; spine's bearing band starts BEAR_Y0
    # behind the monitor's front face; brow top DECK_T + BROW_T above the monitor top
    z_front = -c.LIP_T - m.HOOD_D
    xc = m.SPINE_GAP - (CL*(-R_OUT) - SL*z_front)
    xb0 = (0 - xc + SL*z_front)/CL                      # badge x where the bed plane meets x_use = 0
    yc = m.BEAR_Y0 - (SL*xb0 + CL*z_front)
    zc = m.DECK_T + m.BROW_T - m.HOOD_TOP - R_OUT
    F = Frame(xc, yc, zc)
    y_top = zc - (m.DECK_T + m.BROW_T)                  # badge y of the brow top (use z = DECK_T + BROW_T)
    y_shoe = zc - m.DECK_T                              # shoe underside (use z = DECK_T)
    y_sbot = zc - m.SPINE_BOT
    z_bear = z_front + m.BEAR_D/CL                      # where the bearing band ends (badge z)
    x_in = -(xc - SL*z_bear)/CL                         # spine's inboard profile edge: x_use = 0 at z_bear
    x_far = (-m.B - xc + SL*Z_CASE)/CL - 3.0            # shoe reaches past x_use = -B over the whole depth

    # body profile: D-hood around the case, shoe over the monitor, spine down the inboard side, crown boss
    hood = poly([(-R_OUT, 0), (-R_OUT, y_top + 3.5), (-R_OUT + 3.5, y_top), (R_OUT - m.HOOD_CH, y_top),
                 (R_OUT, y_top + m.HOOD_CH), (R_OUT, 0)]) + circle(R_OUT)
    hood = (hood + rect(x_far, R_OUT - m.HOOD_CH - 1.0, y_top, y_shoe + 1.0)).hull()   # one convex piece: brow, shoe, hood
    # the shoe's underside is made by the K cut below (z_use = DECK_T), never by a profile edge on the same plane
    s45 = R_OUT*math.sqrt(0.5)                          # the spine's bottom runs off the case at 45 degrees, tangent
    spine = poly([(x_in - 1, y_shoe - 0.5), (-s45, y_shoe - 0.5), (-s45, s45),
                  (-s45 - (y_sbot - s45), y_sbot), (x_in - 1, y_sbot)])
    # flat underside from the spine's foot, tangent into the round: hull of the case circle and a point just inside
    # the spine's corner (a touch smaller circle and an inset point, so no two pieces share an edge)
    cx0 = -s45 - (y_sbot - s45)
    belly = (circle(R_OUT - 0.4) + rect(cx0 - 0.8, cx0 - 0.5, y_sbot - 0.6, y_sbot - 0.3)).hull()
    body = chamfered([hood, spine, belly, boss], z_front, Z_CASE, 0.8, BACK_CHAMFER)

    # keep: below the deck top only outboard of the side face; above it, the shoe may reach inboard to -B
    K = box(0, 400, -400, 400, -400, 400) + box(-m.B, 400, -400, 400, m.DECK_T, 400)
    body = body ^ F.badge(K)
    # below the shoe nothing reaches inboard of the spine's face: x_use = 0 for the bearing band, then the canted
    # plane x_b = x_in, which turns away from the monitor behind it
    body = body ^ (box(x_in, 400, -400, 400, -400, 400) + box(-400, 400, -400, y_shoe, -400, 400))

    # chamfered brow: cut the front-top edge (in print: the bed edge, sloping 34 deg from vertical)
    a, d = m.BROW_CH
    p1, p2 = np.array([y_top + a, z_front]), np.array([y_top, z_front + d])
    q1, q2 = p1 - 0.5*(p2 - p1), p2 + 0.5*(p2 - p1)                  # the chamfer line, run well past both faces
    wedge = poly([tuple(q1), tuple(q2), (y_top - 10, q2[1]), (y_top - 10, z_front - 10), (q1[0], z_front - 10)])
    body -= _yz_wedge(wedge)

    # dovetail ridge under the shoe, along use y (the slide direction), between the bed and back planes
    x_dt = (m.CLIP_END - m.B)/2
    tz = poly([(x_dt - m.DT_N/2, m.DECK_T + 0.6), (x_dt - m.DT_N/2, m.DECK_T),
                           (x_dt - m.DT_N/2 - m.DT_D, m.DECK_T - m.DT_D), (x_dt + m.DT_N/2 + m.DT_D, m.DECK_T - m.DT_D),
                           (x_dt + m.DT_N/2, m.DECK_T), (x_dt + m.DT_N/2, m.DECK_T + 0.6)])
    ridge_use = along_y(tz, -200, 200)
    slab = box(-400, 400, -400, 400, z_front + RIDGE_Z0, Z_CASE - RIDGE_BACK)   # one layer off the bed
    ridge = F.badge(ridge_use) ^ slab
    k = z_front + RIDGE_Z0 - y_shoe              # 45-degree front end: in print the ridge grows out of the shoe wall
    ridge -= _yz_wedge(poly([(y_shoe - 5, y_shoe - 5 + k), (y_shoe + 10, y_shoe + 10 + k),
                             (y_shoe + 10, z_front - 20), (y_shoe - 5, z_front - 20)]))
    body += ridge

    # ribs: horizontal grooves across the spine's front face (bridged channels at the bed in print)
    ribs = []
    yy = y_shoe + 2.5
    while yy + m.RIB_W < y_sbot - 3:
        ribs.append(prism(rect(x_in - 3, -R_OUT - 1.2, yy, yy + m.RIB_W), z_front - 1, z_front + m.RIB_D))
        yy += m.RIB_PITCH
    body -= union(ribs)

    # cowl: 45-degree cone from the lip's window out to the bed plane
    r_w = b.r - c.LIP_OVERLAP + c.LIP_BEVEL
    cone = m3.Manifold.cylinder(m.HOOD_D + 0.02, r_w + m.HOOD_D + 0.01, r_w - 0.01, SEG).translate([0, 0, z_front - 0.01])
    body -= cone

    # the case's own cuts (verbatim from build_pocketwatch_usb.build)
    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())
    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4
    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    case = body
    case -= prism(bore_xy, 0.0, Z_CASE + 1)
    case -= prism(circle(R_REAR), FLOOR, Z_CASE + 1)
    case -= window.translate([0, 0, -c.LIP_T - 0.01])
    case -= groove_p
    case -= all_keep
    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    plate = prism(pocket.offset(-c.FIT_CLR - 0.03, Round), FLOOR, Z_CASE)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead_p
    plate += guides
    plate -= all_keep
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_cyl = m3.Manifold.cylinder(FLOOR + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([sw[c.BUTTON], b.sw_y, tip_z])
    plate += post_cyl - union(k for n, k in keep.items() if not n.startswith(c.BUTTON))

    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_OUT, FLOOR=FLOOR, Z_CASE=Z_CASE, bh_p=bh_p,
               groove_r_p=groove_r_p, hdrs=hdrs, sw=sw, post_cyl=post_cyl, z_front=z_front, F=F,
               pocket=pocket, x_dt=x_dt, tz=tz, boss=boss, bore_xy=bore_xy, y_sbot=y_sbot, boss_tip=boss.bounds()[3])
    return feats, case, plate, geo


def _yz_wedge(cs):
    """A CrossSection drawn in (badge y, badge z), extruded along badge x through everything."""
    w = m3.Manifold.extrude(cs, 400).translate([0, 0, -200])          # (y, z, x) as (X, Y, Z)
    return w.transform([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]])    # X<-Z(x), Y<-X(y), Z<-Y(z)


def along_y(cs_xz, y0, y1):
    """A CrossSection drawn in (use x, use z), extruded along use y from y0 to y1."""
    w = m3.Manifold.extrude(cs_xz, y1 - y0)                            # (x, z, -y)
    return w.transform([[1, 0, 0, 0], [0, 0, -1, y1], [0, 1, 0, 0]])


# ---- the clip ------------------------------------------------------------------
class Leaf:
    """The flexure in plan. Front face runs from the root R0 (behind the thickest edge of the band) to the tip
    Pt (NUB_N behind the nub face). Deflected by d (mm, along its normal) it follows the cantilever curve
    y = d (3s^2 - s^3)/2, and the nub + horn ride the tip rigidly."""
    def __init__(self, m: Mount, t_lo, t_hi):
        self.m = m
        self.y_rest = t_lo - m.DELTA0                    # nub face, unloaded
        self.y_root = t_hi + m.ROOT_MARGIN
        y_tf = self.y_rest + m.NUB_N
        dy = self.y_root - y_tf
        self.R0 = np.array([-m.B, self.y_root])
        self.Pt = np.array([-m.B - math.sqrt(m.LEAF_L**2 - dy**2), y_tf])
        self.u = (self.Pt - self.R0)/m.LEAF_L
        self.n = np.array([self.u[1], -self.u[0]])       # normal, pointing backward (+y)
        self.alpha = math.asin(dy/m.LEAF_L)

    def front(self, s, d):
        L = self.m.LEAF_L
        return self.R0 + s*L*self.u + d*(3*s**2 - s**3)/2*self.n

    def normal(self, s, d):
        slope = d/self.m.LEAF_L*(3*s - 1.5*s**2)
        tang = self.u + slope*self.n
        tang /= np.linalg.norm(tang)
        return np.array([tang[1], -tang[0]])

    def plan(self, d):
        ss = np.linspace(-0.12, 1.0, 60)
        f = [self.front(s, d) for s in ss]
        bk = [p + self.m.LEAF_T*self.normal(s, d) for p, s in zip(f, ss)]
        return poly([tuple(p) for p in f] + [tuple(p) for p in bk[::-1]])

    def tip_xform(self, d):
        th = math.atan(1.5*d/self.m.LEAF_L)
        return self.Pt, self.front(1.0, d), -math.degrees(th)   # rotate about the old tip, move to the new

    def strain(self, d):
        return 3*self.m.LEAF_T*d/(2*self.m.LEAF_L**2)

    def k(self):     # N/mm along the leaf normal
        m = self.m
        I = (m.DECK_T + m.REACH)*m.LEAF_T**3/12
        return 3*m.E*I/m.LEAF_L**3


def tip_plan(m: Mount, lf: Leaf, d):
    """Nub (contact face at y_rest) and the 45-degree horn, in plan, riding the deflected tip."""
    x0, yr = lf.Pt[0], lf.y_rest
    nub = poly([(x0, yr), (x0 + m.NUB_W, yr), (x0 + m.NUB_W, lf.Pt[1] + m.NUB_W*math.tan(lf.alpha) + 1.2),
                (x0, lf.Pt[1] + 1.2)]).offset(-0.8, Round).offset(0.8, Round)
    H = m.HORN
    horn = poly([(x0 + 1.0, yr), (x0 - H, yr + H), (x0 - H + 2.6, yr + H + 2.6), (x0 + 2.6, lf.Pt[1] + 1.0)])
    p0, p1, deg = lf.tip_xform(d)
    return (nub + horn).translate([-p0[0], -p0[1]]).rotate(deg).translate([p1[0], p1[1]]), (p0, p1, deg)


def build_clip(m: Mount, size, d=0.0, geo=None):
    """One clip in the use frame, its leaf deflected d mm (0 = as printed). Built as three stacked plan bands
    (unions done in 2D, so no two pieces share a face): leaf/nub depth, lip depth, deck."""
    t_lo, t_hi = SIZES[size]
    lf = Leaf(m, t_lo, t_hi)
    x_end = m.CLIP_END
    back = lf.y_root + m.LEAF_T + 3.0
    x_lip0 = lf.Pt[0] - 2.0
    root = rect(-m.B, x_end, lf.y_root, back)

    def flex_plan(dd):
        leaf = (root + lf.plan(dd)).offset(2.5, Round).offset(-2.5, Round) ^ rect(-500, x_end, -500, 500)
        tp, xf = tip_plan(m, lf, dd)
        return leaf + tp, leaf - root, tp, xf

    tall_d, leaf_d, tip_d, (p0, p1, deg) = flex_plan(d)
    tall_0, _, _, _ = flex_plan(0.0)
    behind = poly([tuple(lf.R0), tuple(lf.R0 + 200*lf.u), tuple(lf.R0 + 200*lf.u + 200*lf.n), tuple(lf.R0 + 200*lf.n)])
    strip = (rect(x_lip0, -m.B + 0.5, -m.LIP_W, back) - (tall_0 + behind).offset(m.SLOT, Miter)) + \
        rect(-m.B, x_end, -m.LIP_W, back)
    lip = rect(x_lip0, x_end, -m.LIP_W, 0.0)
    clip = union([prism(tall_d, -m.REACH, -m.LIP_REACH), prism(tall_d + lip, -m.LIP_REACH, 0.0),
                  prism(tall_d + lip + strip, 0.0, m.DECK_T)])
    r = m.LIP_REACH
    clip -= along_x(poly([(-0.8, -r - 0.01), (0.01, -r - 0.01), (0.01, -r + 0.8)]))       # lip lead-in
    yr = lf.y_rest
    lead = along_x(poly([(yr - 1.0, -m.REACH - 0.01), (yr + 2.0, -m.REACH - 0.01), (yr - 1.0, -m.REACH + 3.0)]))
    lead ^= prism(rect(lf.Pt[0] - 0.5, lf.Pt[0] + m.NUB_W + 0.5, -500, 500), -100, 100)
    clip -= lead.translate([-p0[0], -p0[1], 0]).rotate([0, 0, deg]).translate([p1[0], p1[1], 0])  # nub lead-in
    if geo is not None:     # dovetail groove: the housing's ridge, grown by DT_FIT, open to the front, closed at the back
        groove = along_y(geo["tz"].offset(m.DT_FIT, Miter), -60, 300)
        groove ^= geo["F"].use(box(-400, 400, -400, 400, geo["z_front"] - 80, geo["Z_CASE"] - RIDGE_BACK + m.DT_FIT))
        clip -= groove
    clip = clip.simplify(1e-4)       # stacked bands leave sliver triangles that trimesh's vertex merge would pinch
    far = box(-500, -m.B - 6, -500, 500, -500, 500)        # moving parts, away from the root
    flex = clip ^ (prism(tall_d, -50, 50) ^ far)
    tip = clip ^ prism(tip_d, -50, 50)
    fixed = clip - prism(tall_d.offset(0.05, Miter), -50, 50)
    return dict(fixed=fixed, flex=flex, tip=tip, leaf=flex - prism(tip_d.offset(0.3, Miter), -50, 50), all=clip), lf


def solve_deflection(m, lf, T):
    """Leaf deflection d (along its normal) that puts the nub face on a monitor back at y = T."""
    x0, yr = lf.Pt[0], lf.y_rest
    corners = [np.array([x0 + 0.8, yr]), np.array([x0 + m.NUB_W - 0.8, yr])]
    def face_y(d):
        p0, p1, deg = lf.tip_xform(d)
        a = math.radians(deg)
        Rm = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        return min((p1 + Rm @ (q - p0))[1] for q in corners)
    lo, hi = -5.0, 25.0
    for _ in range(60):
        mid = (lo + hi)/2
        lo, hi = (mid, hi) if face_y(mid) < T else (lo, mid)
    return lo


def along_x(cs_yz):
    """A CrossSection drawn in (use y, use z), extruded along use x through everything."""
    w = m3.Manifold.extrude(cs_yz, 1000)                                                  # (y, z, x)
    return w.transform([[0, 0, 1, -500], [1, 0, 0, 0], [0, 1, 0, 0]])


# ---- scene: monitor, plug, cable, stylus -----------------------------------------
def monitor(T):
    return box(-260, 0, 0, T, -160, 0)


def screen_zone(m):
    """Everything in front of the screen: below/inboard of the thinnest bezel, out to 80 mm in front."""
    return box(-260, -m.BEZEL_MIN, -80, 0.0, -160, -m.BEZEL_MIN)


def plug_and_cable(b, geo):
    """Straight USB-C plug: 6.65 shell in the slot, then a 12 x 8 x 22 body and the cable (badge frame -> use)."""
    tip = geo["boss_tip"]
    body = box(-6, 6, tip + 0.2, tip + 22.2, b.port_z - 4, b.port_z + 4)
    cable = m3.Manifold.cylinder(40, 2.2, 2.2, 32).rotate([-90, 0, 0]).translate([0, tip + 22.2, b.port_z])
    shell = box(-4.2, 4.2, b.tip_y, tip + 0.2, b.port_z - 1.3, b.port_z + 1.3)
    F = geo["F"]
    return F.use(shell), F.use(body), F.use(cable)


def stylus(b, c, geo):
    """A 2 mm pin from 0.25 into the BOOT actuator out to 40 mm behind the back face (badge frame -> use)."""
    x, y = geo["sw"][c.BUTTON], b.sw_y
    z0 = b.pcb_back_z + b.sw_cap_h - c.SW_TRAVEL
    return geo["F"].use(m3.Manifold.cylinder(geo["Z_CASE"] + 40 - z0, PIN_D/2, PIN_D/2, 32).translate([x, y, z0]))


def mass_props(man, density):
    import trimesh
    mm = man.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts))
    return tm.volume/1000*density, tm.center_mass


def run_mount_checks(b, c, m, case, plate_h, geo):
    F = geo["F"]
    H = F.use(case)
    P = F.use(plate_h)
    shell, pbody, cable = plug_and_cable(b, geo)
    pin = stylus(b, c, geo)
    res = {}

    print("\n7. Mirror for the left side: the case core is symmetric in x, so mirroring the housing in the slicer is safe")
    core = case ^ prism(circle(geo["R_OUT"] - 0.05), -c.LIP_T, geo["Z_CASE"])
    diff = (core - core.mirror([1, 0, 0])).volume()/core.surface_area()      # mean thickness of what differs
    check(diff < 0.01, "case core vs its mirror image (facet phase only)", f"mean difference {1000*diff:.2f} um")

    r_w = b.r - c.LIP_OVERLAP + c.LIP_BEVEL
    rim = geo["R_OUT"] - 0.8 - (r_w + m.HOOD_D)
    check(rim >= c.MIN_WALL, f"cowl rim on the bed (after the 0.8 chamfer) >= {c.MIN_WALL}", f"{rim:.2f}")
    under = m.DECK_T - m.DT_D - m.DT_FIT
    check(under >= c.MIN_WALL, f"clip deck under the dovetail groove >= {c.MIN_WALL}", f"{under:.2f}")
    check(m.LEAF_T >= 1.2 and m.DECK_T + m.REACH >= 2.4, "flexure section >= 2.4 x 1.2, bending in the print plane",
          f"{m.LEAF_T} (bends) x {m.DECK_T + m.REACH:.1f} (layers stack this way)")

    print("\n8. Housing vs the monitor corner (all edge thicknesses)")
    sl = H ^ box(0, 0.05, -50, 50, -100, 0)
    sb = bbox(sl)
    area = sl.volume()/0.05
    check(area > 40, "spine bears on the side face (x = 0) over an area", f"{area:.0f} mm^2, z {sb[0,2]:.1f}..{sb[1,2]:.1f}")
    check(sb[0, 1] >= 0.5 and sb[1, 1] <= SIZES['S'][0] - 0.5, "bearing band lies on the thinnest (8 mm) edge",
          f"y {sb[0,1]:.1f}..{sb[1,1]:.1f}")
    res["z_bear"] = sb[0, 2]
    for T in (8.0, 16.0, 24.0, 32.0):
        v = (H ^ monitor(T)).volume()
        check(v < 1e-3, f"housing clear of a {T:.0f} mm monitor", f"{v:.4f} mm^3")
    scr = screen_zone(m)
    v = (H ^ scr).volume() + (P ^ scr).volume()
    check(v < 1e-3, "housing + plate: nothing in front of the screen", f"{v:.4f} mm^3")
    check(m.LIP_REACH + 0.4 <= m.BEZEL_MIN, f"front lip reach {m.LIP_REACH} + 0.4 <= thinnest bezel {m.BEZEL_MIN}",
          f"margin {m.BEZEL_MIN - m.LIP_REACH:.1f}")

    print("\n9. Clip bands: flexure strain, clamp force, clearances, housing fit (per size, thin / mid / thick edge)")
    res["N"] = {}
    for size, (t_lo, t_hi) in SIZES.items():
        _, lf = build_clip(m, size, 0.0, geo)
        print(f"  {size}: {t_lo:.0f}-{t_hi:.0f} mm  leaf {m.LEAF_T} x {m.DECK_T + m.REACH:.1f} x L {m.LEAF_L}, "
              f"angle {math.degrees(lf.alpha):.1f} deg, k {lf.k():.2f} N/mm")
        for T in (t_lo, (t_lo + t_hi)/2, t_hi):
            d = solve_deflection(m, lf, T)
            parts, _ = build_clip(m, size, d, geo)
            eps = lf.strain(d)
            Nn = lf.k()*d*math.cos(lf.alpha)
            res["N"][(size, T)] = Nn
            mon = monitor(T)
            g_leaf = parts["leaf"].min_gap(mon, 3.0)
            v_tip = (parts["tip"] ^ mon).volume()
            v_fix = (parts["fixed"] ^ mon).volume()
            v_slot = (parts["flex"] ^ parts["fixed"]).volume()
            v_h = (H ^ parts["all"]).volume()
            v_s = (parts["all"] ^ scr).volume()
            ok = eps <= m.STRAIN_MAX and g_leaf >= 0.3 and v_tip < 2.0 and v_fix < 1e-3 and v_h < 1e-2 and v_s < 1e-3 and v_slot < 0.2
            check(ok, f"{size} on {T:4.1f}: d {d:5.2f}, strain {100*eps:4.2f}%, clamp {Nn:4.1f} N",
                  f"leaf gap {g_leaf:.2f}, tip {v_tip:.2f}, fixed {v_fix:.3f}, housing {v_h:.3f}, slot {v_slot:.3f}, screen {v_s:.3f}")
        d_open = (t_hi + 0.5) - lf.y_rest
        check(lf.strain(d_open/math.cos(lf.alpha)) < m.STRAIN_MAX, f"{size} opened 0.5 past its band: strain < 2%",
              f"{100*lf.strain(d_open/math.cos(lf.alpha)):.2f}%  (PETG yields ~4%)")

    print("\n10. Dovetail: locks up / sideways, slides off forward, stops at the back")
    parts, lf = build_clip(m, "M", solve_deflection(m, Leaf(m, *SIZES["M"]), 20.0), geo)
    C = parts["all"]
    for nm, dv, want in (("lifted 0.5", [0, 0, 0.5], True), ("pushed outboard 0.5", [0.5, 0, 0], True),
                         ("pulled inboard 0.5", [-0.5, 0, 0], True), ("pushed back 0.3", [0, 0.3, 0], True),
                         ("slid forward 45 (off)", [0, -45, 0], False)):
        v = (H.translate(dv) ^ C).volume()
        check((v > 0.5) == want, f"housing {nm}: {'blocked' if want else 'free'}", f"{v:.2f} mm^3 overlap")
    worst = max(((H.translate([0, -s, 0]) ^ (C + monitor(20.0))).volume(), s) for s in np.arange(0.0, 45.0, 3.0))
    check(worst[0] < 1e-2, "housing slides on along y without touching the monitor or clip", f"max {worst[0]:.3f} mm^3 at {worst[1]:.0f}")
    xd = geo["x_dt"]
    foot = (H ^ box(-m.B, m.CLIP_END, -100, 100, m.DECK_T, m.DECK_T + 0.3)) - box(xd - m.DT_N/2 - 0.6, xd + m.DT_N/2 + 0.6, -100, 100, 0, 10)
    under = foot.translate([0, 0, -0.3]) - C
    check(under.volume() < 0.3*1.0, "shoe sits on the clip deck (beside the groove mouth, inboard of the clip end)",
          f"{foot.volume()/0.3:.0f} mm^2 of shoe, {under.volume()/0.3:.2f} mm^2 unsupported")

    print("\n11. Plug path and BOOT access")
    for nm, s in (("plug shell", shell), ("plug body", pbody), ("cable", cable)):
        v = sum((s ^ x).volume() for x in (C, monitor(32.0), monitor(8.0))) + (0 if nm == "plug shell" else (s ^ H).volume())
        check(v < 1e-3, f"{nm} clear of housing, clip and monitor", f"{v:.4f} mm^3")
    v = (shell ^ H).volume()
    check(v < 0.05, "plug shell enters the slot (only the slot wall at the shell's corners)", f"{v:.4f} mm^3")
    v = sum((pin ^ x).volume() for x in (C, monitor(32.0), H, P))
    check(v < 1e-3, "2 mm pin from 40 mm behind reaches BOOT past housing, plate, clip, monitor", f"{v:.4f} mm^3")
    out = F.use(prism(geo["pocket"].offset(0.2, Round), geo["Z_CASE"] + 0.01, geo["Z_CASE"] + 40))
    v = sum((out ^ x).volume() for x in (C, monitor(32.0), H))
    check(v < 1e-3, "back plate pulls straight out (nothing behind it)", f"{v:.4f} mm^3")

    print("\n12. It stays put: weight + 1 N cable, friction safety factor (felt pads)")
    mh, cgh = mass_props(H + P, m.PETG)
    mc, cgc = mass_props(C, m.PETG)
    badge_cg = F.pt([0, 0, 2.5])
    W = (mh + m.BADGE_G)*9.81e-3
    xg = (mh*cgh[0] + m.BADGE_G*badge_cg[0])/(mh + m.BADGE_G)
    pb = bbox(pbody)
    xp, yp = (pb[0, 0] + pb[1, 0])/2, (pb[0, 1] + pb[1, 1])/2
    M = W*xg + m.CABLE_N*xp
    lever = -res["z_bear"]
    Nside = M/lever
    Nmin = min(res["N"].values())
    cap = 2*m.MU*Nmin
    sf = cap/Nside
    print(f"  housing + plate {mh:.1f} g (solid), badge {m.BADGE_G:.0f} g, clip {mc:.1f} g; gauge CG x {xg:.1f}, plug x {xp:.1f}")
    print(f"  moment about the corner {M:.1f} N mm -> spine side force {Nside:.2f} N at {lever:.1f} mm down")
    check(sf >= m.SF_MIN, f"friction 2 x mu {m.MU} x clamp {Nmin:.2f} N (weakest band end) vs side force",
          f"SF {sf:.2f} (TPU mu {m.MU_TPU}: {2*m.MU_TPU*Nmin/Nside:.2f})")
    ycg = ((mh*cgh[1] + m.BADGE_G*badge_cg[1]) + mc*cgc[1])/(mh + m.BADGE_G + mc)
    check(0.5 < ycg < SIZES["S"][0] - 0.5 and 0.5 < yp < SIZES["S"][0] - 0.5,
          "weight and cable land over the monitor top (no tipping fore/aft)", f"CG y {ycg:.1f}, plug y {yp:.1f}, edge 0..8")
    check(True, "vertical load: deck on the monitor top, a seat, not friction", f"{W + m.CABLE_N:.2f} N")
    res.update(mh=mh, mc=mc, Nside=Nside, sf=sf, Nmin=Nmin)
    return res


# ---- renders ----------------------------------------------------------------------
BODY, CLIPC, MON, SCREEN, DARK, GLASS, WHITE, NEEDLE, PLUG, CABLE, PLATE, PIN = (
    (0.30, 0.31, 0.34), (0.86, 0.40, 0.16), (0.12, 0.12, 0.14), (0.05, 0.07, 0.12), (0.08, 0.08, 0.09),
    (0.06, 0.16, 0.30), (0.95, 0.95, 0.92), (1.00, 0.35, 0.10), (0.62, 0.64, 0.66), (0.20, 0.20, 0.22),
    (0.42, 0.43, 0.47), (0.85, 0.80, 0.25))


LIGHT = {BODY: (0.60, 0.62, 0.67), PLATE: (0.80, 0.68, 0.40), MON: (0.20, 0.20, 0.23)}   # section colours


def gauge_face(b, geo):
    """Badge, its glass, and a drawn gauge face (display rotated 180 in firmware: the face reads upright)."""
    F = geo["F"]
    r = b.active_d/2
    disc = F.use(prism(b_disc(b), 0.0, b.pcb_back_z))
    glass = m3.Manifold.cylinder(0.3, r, r, 96).translate([0, 0, -0.32])
    ticks = []
    for i in range(11):                                   # 270-degree sweep, ticks every 27 degrees
        a = math.radians(225 - 27*i)
        t = rect(-0.45, 0.45, r - 3.2 if i % 5 == 0 else r - 2.2, r - 0.8).rotate(math.degrees(a) - 90)
        ticks.append(prism(t, -0.42, -0.30))
    needle = prism(poly([(-0.7, -2.0), (0.7, -2.0), (0.2, r - 3.6), (-0.2, r - 3.6)]).rotate(-35), -0.5, -0.30)
    hub = m3.Manifold.cylinder(0.25, 1.6, 1.6, 32).translate([0, 0, -0.55])
    # badge frame +y is DOWN in use; draw the face upright by flipping it 180 about the axis
    up = lambda x: F.use(x.rotate([0, 0, 180]))
    return [(disc, DARK), (up(glass), GLASS), (up(union(ticks)), WHITE), (up(needle), NEEDLE), (up(hub), WHITE)]


def b_disc(b):
    from build_pocketwatch import disc_and_tab
    return disc_and_tab(b)


def R(x, L=1.0):
    return x.refine_to_length(L)


def renders(b, c, m, case, plate_h, geo):
    F = geo["F"]
    H, P = F.use(case), F.use(plate_h)
    shell, pbody, cable = plug_and_cable(b, geo)
    face = gauge_face(b, geo)
    plug = [(R(shell), PLUG), (R(pbody), PLUG), (R(cable, 2.0), CABLE)]

    def scene(size, T, extra=(), crop=None):
        lf = Leaf(m, *SIZES[size])
        parts, _ = build_clip(m, size, solve_deflection(m, lf, T), geo)
        mon = monitor(T) ^ box(-95, 0, 0, T, -75, 0)
        scr = box(-95, -m.BEZEL_MIN, -0.2, 0.0, -75, -m.BEZEL_MIN) ^ mon.translate([0, -0.2, 0])
        mon -= box(-200, -m.BEZEL_MIN, -1, 0.05, -200, -m.BEZEL_MIN)
        items = [(mon, MON), (scr, SCREEN), (parts["all"], CLIPC), (H, BODY), (P, PLATE)] + face + list(extra)
        if crop is not None:
            items = [(x ^ crop, col) for x, col in items]
        return [(R(x, 2.0 if x.volume() > 5e4 else 1.0), col) for x, col in items if not x.is_empty()]

    render(scene("S", 12.0) + plug, OUT + "01-hero.png", elev=20, azim=-128, zoom=1.15,
           title="Lowprofile on a 12 mm thin-bezel monitor (S clip): hangs at the top-right corner, cable straight down")
    render(scene("S", 12.0) + plug, OUT + "02-front-as-you-see-it.png", elev=4, azim=-108, zoom=1.3,
           title="From your seat: gauge canted 15 deg toward you, 2 mm lip on the bezel, screen untouched")
    render(scene("M", 20.0) + plug, OUT + "03-quarter-20mm.png", elev=24, azim=-52, zoom=1.3,
           title="M clip on a 20 mm edge: deck on top, spine on the side face, leaf down the back")

    # side section through the dovetail (yz plane), M clip on 20 mm
    x = geo["x_dt"]
    cut = []
    for man, col in scene("M", 20.0, crop=box(x, 80, -8, 36, -16, 9))[:5]:      # monitor, clip, housing, plate
        man = man.trim_by_plane([1, 0, 0], x)
        if not man.is_empty(): cut.append((man.refine_to_length(0.5), LIGHT.get(col, col)))
    render(cut, OUT + "04-section-dovetail.png", elev=0, azim=180, zoom=1.35,
           title=f"Section at x={x:.1f}, M clip on a 20 mm edge (black): grey dovetail ridge in the orange deck's groove,\n"
                 "front lip on the bezel (right), root block behind the monitor (left). You sit to the right.")

    # section through the gauge centre, horizontal, seen from above
    zc = F.t[2]
    cut = []
    for man, col in scene("S", 12.0, crop=box(-30, 60, -20, 40, -80, 20)):
        man = man.trim_by_plane([0, 0, -1], -zc)
        if not man.is_empty(): cut.append((man.refine_to_length(0.7), LIGHT.get(col, col)))
    render(cut, OUT + "05-section-plan.png", elev=89, azim=-90, zoom=1.35,
           title="Plan section at the gauge centre (monitor left, you below): 15 deg cant,\nspine flat on the side face, badge (black) in the bore, BOOT-hole plate (tan) flush at the back")

    # the flexure: clip plan at both ends of the S band, plus rest
    tiles, notes = [], []
    lf = Leaf(m, *SIZES["S"])
    for i, T in enumerate((None, 8.0, 16.0)):
        d = 0.0 if T is None else solve_deflection(m, lf, T)
        parts, _ = build_clip(m, "S", d, geo)
        sh = [0, -48*i, 0]
        tiles.append((R(parts["all"].translate(sh)), CLIPC))
        if T is not None:
            tiles.append((R(monitor(T) ^ box(-82, 0, 0, T, -3, 0), 2.0).translate(sh), (0.55, 0.56, 0.60)))
            notes.append(f"{T:.0f} mm: tip {d:.1f}, {lf.k()*d*math.cos(lf.alpha):.1f} N, {100*lf.strain(d):.1f}%")
    render(tiles, OUT + "06-flexure-plan.png", elev=89, azim=-90, zoom=1.2,
           title="S clip from above (grey = monitor top): as printed | " + " | ".join(notes))

    # back: BOOT pin path
    pin = stylus(b, c, geo)
    render(scene("S", 12.0, extra=[(pin, PIN)]) + plug, OUT + "07-back-boot.png", elev=18, azim=62, zoom=1.4,
           title="From behind: BOOT plate flush, yellow 2 mm pin goes straight in to the button")

    # print layout: everything as it sits on the bed
    def at(man, x0, y0):           # put a part's bbox corner at (x0, y0) on the bed
        bb = bbox(man)
        return man.translate([x0 - bb[0, 0], y0 - bb[0, 1], -bb[0, 2]])
    lay = [(R(at(to_print_housing(case, geo), 10, 150)), BODY), (R(at(to_print_plate(plate_h, geo), 10, 95)), PLATE)]
    y0 = 10
    for size in SIZES:
        parts, _ = build_clip(m, size, 0.0, geo)
        cp = at(to_print_clip(parts["all"], m), 95, y0)
        lay.append((R(cp), CLIPC))
        y0 += bbox(cp)[1, 1] - bbox(cp)[0, 1] + 8
    frame = box(0, 256, 0, 256, -0.6, -0.01) - box(2, 254, 2, 254, -1, 1)
    lay.append((R(frame, 4.0), (0.55, 0.55, 0.55)))
    render(lay, OUT + "08-print-layout.png", elev=48, azim=-62, zoom=1.0,
           title="Print layout on the 256 mm bed: housing face down, plate flat, clips S/M/L top-down. No supports.")


def to_print_housing(case, geo):
    return case.translate([0, 0, -geo["z_front"]])


def to_print_clip(clip, m):
    return clip.rotate([180, 0, 0]).translate([0, 0, m.DECK_T])


def to_print_plate(plate, geo):
    return plate.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]])


def main():
    b, c, m = Badge(), Case(), Mount()
    feats, case, plate, geo = build_housing(b, c, m)
    F = geo["F"]
    hb = bbox(F.use(case))
    print(f"Housing: case Ø{2*geo['R_OUT']:.1f} in a hooded body, {hb[1,0]-hb[0,0]:.1f} wide x "
          f"{hb[1,2]-hb[0,2]:.1f} tall, gauge centre ({F.t[0]:.1f}, {F.t[1]:.1f}, {F.t[2]:.1f}) from the corner, cant {-m.PHI:.0f} deg")
    print("\nBadge fit (the USB-only case checks, run on this housing):")
    usb_fit_checks(b, c, feats, case, plate, geo)
    plate_h, x, y = boot_hole_plate(b, c, plate, geo)
    run_hole_checks(b, c, feats, case, plate_h, x, y, geo)
    res = run_mount_checks(b, c, m, case, plate_h, geo)

    print("\n13. Print files (watertight, no supports)")
    export(case, STL + "Lowprofile - housing.stl", lambda q: to_print_housing(q, geo))
    export(plate_h, STL + "Lowprofile - back plate (BOOT hole).stl", lambda q: to_print_plate(q, geo))
    for size, (lo, hi) in SIZES.items():
        parts, _ = build_clip(m, size, 0.0, geo)
        export(parts["all"], STL + f"Lowprofile - clip {size} ({lo:.0f}-{hi:.0f} mm edge).stl", lambda q: to_print_clip(q, m))
    if "--no-render" not in sys.argv:
        renders(b, c, m, case, plate_h, geo)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
