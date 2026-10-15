#!/usr/bin/env python3
"""
Battery pendant for the 1.28 badge: the v2 pocketwatch (cell behind the plate, snapped lid) with the pendant's USB-C
port sticking out at 12 o'clock and the kids case's BOOT flap moved one layer out, into the lid. Three printed parts.

  case   v2's case: bezel lip, badge bore, step, battery chamber, lid groove. At 12 o'clock a notch through everything
         in front of the plate's back face lets a plug's overmold seat on the port; the chamber wall arches over it.
         Two ribs on the chamber wall hold the cell's turn. The low one is the flap's stop, the tall one keys the lid.
  plate  v2's plate (sits on the step, snaps into the bore, grips the headers) with a slot for the pole, notches for
         the ribs and for the plug. The cell's lead runs in a channel in its back face to the JST hole.
  lid    v2's lid, holding the cell, with a flap cut into it beside the cell. A pole under the flap reaches past the
         cell, through the plate, to BOOT. Pressed at its outer end, a foot lands on the low rib after the click.

The cell is turned TILT so its long edge clears the pole. Its half-diagonal circle, so the case, is unchanged.
The flap frame runs along the cell's long edge with the root at +x, as the kids case's badge frame does, so the
kids-case flap model and bend apply unchanged.

Run from the repo root with ~/.venvs/cad/bin/python. --no-render for a fast check run.
"""
import sys, math
sys.path[:0] = ["pocketwatch", "pocketwatch/pendant", "pocketwatch/pendant/kids-case"]
from dataclasses import dataclass
import numpy as np, manifold3d as m3
import build_pocketwatch as V2
import build_pocketwatch_usb as U
import build_kids_case as K
from build_pocketwatch import (Badge, Case, Round, SEG, BRIDGE_MAX, snap, chamfered, circle, rect, prism, union, bbox, check,
                               FAILS, export, render)
from build_pendant import Pendant, MAT, sector, run_pry_checks

OUT = "pocketwatch/pendant/battery/renders/"
STL = "stl/pocketwatch/pendant/battery/"
LAYER = 0.3
LID_CLR_ROOMY = 0.60        # the roomy plate's 0.47 looser, less a little so the bead's foot stays inside the disc


@dataclass(frozen=True)
class Battery:
    F_W: float = 8.0            # flap width and thickness: the kids case's
    F_ROOT: float = 9.0         # root, in the flap frame: along the cell's edge from its middle
    F_T: float = 1.2
    FOOT_BACK: float = 2.4      # the foot stops this short of the tip, as on the kids case
    LEDGE_D: float = 2.0        # ribs: depth in from the chamber wall
    KEY_X: float = 16.0         # the key rib, from here (flap frame) to the cell's corner
    OM_W: float = 15.0          # the plug overmold the 12 o'clock notch is cut for, centred on the port
    OM_T: float = 12.0
    LEAD_W: float = 2.2         # the cell's lead: two wires side by side
    LEAD_T: float = 1.0


@dataclass(frozen=True)
class Frame:
    """The flap frame: +x along the cell's long edge toward the flap root, +y out from the cell toward BOOT."""
    psi: float                  # deg, the frame's +x in the badge frame

    def b(self, s):
        return s.rotate(self.psi) if isinstance(s, m3.CrossSection) else s.rotate([0, 0, self.psi])

    def l(self, s):
        return s.rotate(-self.psi) if isinstance(s, m3.CrossSection) else s.rotate([0, 0, -self.psi])

    def pt_b(self, v, sgn=1):
        a = math.radians(sgn*self.psi)
        return np.array([v[0]*math.cos(a) - v[1]*math.sin(a), v[0]*math.sin(a) + v[1]*math.cos(a)])

    def pt_l(self, v):
        return self.pt_b(v, -1)

    @property
    def ux(self):
        return self.pt_b((1.0, 0.0))


def cell_gap(c, pt, tilt):
    """Distance from a point to the cell's footprint, the cell turned tilt deg."""
    q = Frame(90 + tilt).pt_l(pt)
    return math.hypot(max(abs(q[0]) - c.BATT_L/2, 0), max(abs(q[1]) - c.BATT_W/2, 0))


def least_tilt(b, c):
    """The least turn (deg, CCW seen from the back) that keeps the pole's channel MIN_WALL + BAY_CLR off the cell."""
    need = c.POST_D/2 + c.XY_CLR + c.MIN_WALL + c.BAY_CLR
    boot = (-b.sw_x, b.sw_y)
    lo, hi = 0.0, 45.0
    while hi - lo > 1e-4:
        mid = (lo + hi)/2
        lo, hi = (mid, hi) if cell_gap(c, boot, mid) < need else (lo, mid)
    return hi, need


def free_state(f, yc, r_edge, m, P, at):
    """The flap bent by P alone at `at` from the root, nothing under it: the switch's air gap before it is touched."""
    s = np.linspace(0, m["d_tip"], 2401)
    EI = MAT.E*np.maximum(K.chord(f, yc, r_edge, f.F_ROOT - s), 1e-3)*f.F_T**3/12
    cum = lambda v: np.concatenate([[0.0], np.cumsum((v[1:] + v[:-1])/2*np.diff(s))])
    slope = cum(P*np.clip(at - s, 0, None)/EI)
    return dict(s=s, slope=slope, defl=cum(slope))


def swings(f, c, cs, g_stop, yc, r_edge, lever):
    """How far the pole's tip has swung toward the root (the flap's slope at the pole x its length) at the touch, the
    click, the stop and the worst stop (foot late, any E)."""
    m = cs["nom"]["m"]
    sl = lambda st: float(np.interp(m["a"], st["s"], st["slope"]))*lever
    touch = free_state(f, yc, r_edge, m, c.REST_CLR/m["fad"], m["d"])
    return dict(touch=sl(touch), click=sl(m["press"](m["P_click"], m["d"], g_stop)), stop=sl(cs["nom"]["land"]["nom"]),
                worst=max(sl(v["land"]["late"]) for v in cs.values()), touch_state=touch)


# ---- the design: everything the clearances do not change ---------------------
def v2_case(b, c, feats, geo):
    """v2's case, with the pendant's fix: the window turned a quarter segment off the bore's vertices, or one pinches."""
    R_BORE, R_REAR, FLOOR, Z_CASE = geo["R_BORE"], geo["R_REAR"], geo["FLOOR"], geo["Z_CASE"]
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    groove_p = snap(c, R_BORE, zb_p)[1]
    groove_l = snap(c, R_REAR, geo["lid_z0"] + c.LID_T/2)[1]
    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    case = chamfered([circle(geo["R_OUT"])], -c.LIP_T, Z_CASE, c.CHAMFER, c.CHAMFER)
    case -= prism(feats[0].grown(), 0.0, FLOOR + 1)
    case -= prism(circle(R_REAR), FLOOR, Z_CASE + 1)
    case -= window.rotate([0, 0, 90/SEG]).translate([0, 0, -c.LIP_T - 0.01])
    case -= groove_p + groove_l
    case -= union(k.keepout(c.FLOAT) for k in feats)
    return case


def design(b, c, p, bt):
    feats, _, _, _, battery, geo = V2.build(b, c)
    case = v2_case(b, c, feats, geo)
    R_REAR, FLOOR, lid_z0 = geo["R_REAR"], geo["FLOOR"], geo["lid_z0"]
    tilt, need = least_tilt(b, c)
    F = Frame(90 + tilt)
    boot = np.array([-b.sw_x, b.sw_y])
    boot_l = F.pt_l(boot)
    r_lid = R_REAR - c.FIT_CLR                                       # the model uses the nominal lid, as the kids case
    z_back = lid_z0 + c.LID_T
    z_under, z_ax = z_back - bt.F_T, z_back - bt.F_T/2
    lever = z_ax - geo["tip_z"]
    n_lo = boot_l[1] - c.POST_D/2 - c.MIN_WALL                        # MIN_WALL of flap beside the pole on the cell side
    yc = n_lo + bt.F_W/2
    x_tip = K.tip_x(K.Flap(F_W=bt.F_W, F_ROOT=bt.F_ROOT, F_T=bt.F_T), yc, r_lid, c.MIN_WALL)
    f = K.Flap(F_W=bt.F_W, F_ROOT=bt.F_ROOT, F_T=bt.F_T, FOOT_X=x_tip + bt.FOOT_BACK)
    # the pole swings toward the root as the flap bends: it stands back from BOOT by the middle of its swing from the
    # touch to the worst stop, so the switch stays under the pole all the way
    delta = 0.0
    for _ in range(5):
        g_stop, cs = K.flap_cases(f, p, c, boot_l[0] - delta, yc, r_lid)
        sw = swings(f, c, cs, g_stop, yc, r_lid, lever)
        delta = (sw["touch"] + sw["worst"])/2
    px = boot_l[0] - delta
    g_stop = K.flap_cases(f, p, c, px, yc, r_lid)[0]
    # the ledge on a layer line of the case as printed (bezel down, LIP_T up), at least one layer under the foot
    z_ledge = LAYER*math.floor((z_under - g_stop - LAYER + c.LIP_T)/LAYER + 1e-9) - c.LIP_T
    g_stop, cs = K.flap_cases(f, p, c, px, yc, r_lid, z_under - z_ledge)
    sw = swings(f, c, cs, g_stop, yc, r_lid, lever)
    pole_c = F.pt_b((px, boot_l[1]))
    swept = union(k.keepout(c.FLOAT) if k.name == "disc + tab" else
                  m3.Manifold.batch_hull([k.keepout(c.FLOAT), k.keepout(c.FLOAT).translate([*(-sw["worst"]*F.ux), 0])])
                  for k in feats if not k.name.startswith(c.BUTTON))
    R_LEDGE = R_REAR - bt.LEDGE_D
    y_flat = b.tip_y - c.RAD_CLR - p.PORT_OUT
    return dict(feats=feats, case_v2=case, geo=geo, cell=battery.rotate([0, 0, tilt]), tilt=tilt, need=need, F=F, f=f,
                boot=boot, boot_l=boot_l, yc=yc, px=px, delta=delta, pole_c=pole_c, g_stop=g_stop, cs=cs,
                sw=sw, z_ledge=z_ledge, z_back=z_back, z_under=z_under, z_ax=z_ax, lever=lever, r_lid=r_lid,
                swept=swept, R_LEDGE=R_LEDGE, y_flat=y_flat, lid_z0=lid_z0, FLOOR=FLOOR, R_REAR=R_REAR,
                R_OUT=geo["R_OUT"], Z_CASE=geo["Z_CASE"], jst_l=F.pt_l((b.jst_x, b.jst_y)))


def flap_cut(c, D, r_disc):
    """The lid's flap in the badge frame: the strip region (sel), the slits and wedges (holes), and the flap itself."""
    F, f, yc = D["F"], D["f"], D["yc"]
    gap = U.TAB_GAP
    y_lo, y_hi = yc - f.F_W/2, yc + f.F_W/2
    slit = lambda y0: rect(-60, f.F_ROOT, y0, y0 + gap) + m3.CrossSection.circle(gap/2, 24).translate([f.F_ROOT, y0 + gap/2])
    holes = slit(y_lo - gap) + slit(y_hi)
    for y_e, sgn in K.slit_sides(f, yc):
        if (x_w := K.wedge_x(r_disc, y_e, sgn, c.MIN_WALL)) is not None:
            holes += rect(-60, x_w, *sorted((y_e, y_e + sgn*(c.MIN_WALL + 0.35))))
    sel = rect(-60, f.F_ROOT, y_lo - gap/2, y_hi + gap/2)
    root = rect(f.F_ROOT - 1, f.F_ROOT + gap/2 - 0.02, y_lo - gap/2, y_hi + gap/2)   # corners inside the slits' round ends, or they pinch
    holes, sel, root = F.b(holes), F.b(sel), F.b(root)
    return sel, holes, root, (circle(r_disc) ^ sel) - holes


def foot_xy(D, flap):
    f = D["f"]
    return (flap.offset(-0.05, Round) ^ D["F"].b(rect(f.FOOT_X, 60, -60, 60))) - circle(D["R_LEDGE"] + f.FOOT_IN)


def ribs(c, bt, D):
    """The two ribs on the chamber wall, BAY_CLR off the cell's long edge: the low one (the flap's stop) under the
    foot and the tip, the tall one (the lid's key) at the cell's other end. They hold the cell's turn between them."""
    F, f = D["F"], D["f"]
    ring = circle(D["geo"]["groove_r_l"] + 0.1) - circle(D["R_LEDGE"])     # out past the lid groove: no sliver of it left
    off_cell = F.b(rect(-60, 60, c.BATT_W/2 + c.BAY_CLR, 60))
    foot = F.l(foot_xy(D, flap_cut(c, D, D["r_lid"])[3]))
    low = ring ^ off_cell ^ F.b(rect(-60, foot.bounds()[2] + 1.0, -60, 60))
    key = ring ^ off_cell ^ F.b(rect(bt.KEY_X, 60, -60, 60))
    return low, key


def notch12(b, c, p, bt, D):
    """The 12 o'clock notch: everything above y_flat, OM_W + 2 PORT_OUT wide, up to PORT_OUT over the overmold, with a
    45 deg roof whose flat span is a bridge under BRIDGE_MAX. Returns the solid, its half-width and its roof's top."""
    hw = bt.OM_W/2 + p.PORT_OUT
    z_s = b.port_z + bt.OM_T/2 + p.PORT_OUT
    wf = BRIDGE_MAX/2 - 0.5
    prof = m3.CrossSection([[(-hw, -10), (hw, -10), (hw, z_s), (wf, z_s + hw - wf), (-wf, z_s + hw - wf), (-hw, z_s)]])
    L = D["R_OUT"] + 5 - D["y_flat"]
    solid = m3.Manifold.extrude(prof, L).transform(np.array([[1, 0, 0, 0], [0, 0, 1, D["y_flat"]], [0, 1, 0, 0]], float))
    return solid, hw, z_s + hw - wf


def scoop_xy(D, flap):
    """The back rim over the foot, lowered to the lid's back face, so a thumb on the flap's outer end is not held off
    it by the rim."""
    pts = np.concatenate([np.asarray(poly) for poly in foot_xy(D, flap).to_polygons()])
    ang = np.arctan2(pts[:, 1], pts[:, 0])
    mid = math.atan2(np.mean(np.sin(ang)), np.mean(np.cos(ang)))
    rel = np.angle(np.exp(1j*(ang - mid)))
    pad = 1.0/D["R_REAR"]
    return sector(D["R_REAR"] - 1.0, D["R_OUT"] + 1.0, mid + rel.min() - pad, mid + rel.max() + pad)


def build_case(b, c, p, bt, D):
    f = D["f"]
    case = D["case_v2"]
    notch, hw, z_roof = notch12(b, c, p, bt, D)
    case -= notch
    pry = U.pry_cut(D["R_REAR"] - 1.3, D["R_OUT"], D["lid_z0"], D["Z_CASE"], p.PRY_DEG)
    case -= pry
    case -= prism(scoop_xy(D, flap_cut(c, D, D["r_lid"])[3]), D["z_back"], D["Z_CASE"] + 1)
    low_xy, key_xy = ribs(c, bt, D)
    low = prism(low_xy, D["FLOOR"] - 0.3, D["z_ledge"])
    low -= prism(D["F"].b(rect(-60, f.FOOT_X - 0.3, -60, 60)), D["z_ledge"] - f.RELIEF, D["z_ledge"] + 1)   # the tip never lands first
    key = prism(key_xy, D["FLOOR"] - 0.3, D["Z_CASE"])
    case += low + key
    D.update(notch=notch, hw=hw, z_roof=z_roof, pry=pry, low=low, key=key, low_xy=low_xy, key_xy=key_xy)
    return case


def build_plate(b, c, D, clr):
    """v2's plate, rebuilt with the post replaced by a slot the pole swings in, the lead channel along the turned
    cell, the rib notches and the 12 o'clock notch."""
    feats, geo, F = D["feats"], D["geo"], D["F"]
    R_BORE, R_REAR, FLOOR = geo["R_BORE"], geo["R_REAR"], geo["FLOOR"]
    z1 = FLOOR + c.PLATE_T
    skirt_xy = feats[0].grown().offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2     # as v2
    bead_p, _, bh_p, _ = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, m3.JoinType.Miter), 0.0, FLOOR + 0.01) for h in geo["hdrs"])
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    plate = prism(circle(R_REAR - clr), FLOOR, z1)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead_p
    plate += guides
    plate -= union(k.keepout(c.FLOAT) for k in feats)
    plate -= prism(m3.CrossSection.square([c.LEAD_HOLE]*2, True).translate([b.jst_x, b.jst_y]), FLOOR - 1, z1 + 1)
    jx, jy = D["jst_l"]
    plate -= prism(F.b(rect(jx, R_REAR + 1, jy - c.LEAD_CH_W/2, jy + c.LEAD_CH_W/2)), z1 - c.LEAD_CH_D, z1 + 1)
    r_s = c.POST_D/2 + c.XY_CLR
    slot = (circle(r_s).translate(D["pole_c"]) + circle(r_s).translate(D["pole_c"] + D["sw"]["worst"]*F.ux)).hull()
    plate -= prism(slot, -1, z1 + 1)
    plate -= prism((D["low_xy"] + D["key_xy"]).offset(c.FIT_CLR, m3.JoinType.Miter, 4.0), FLOOR - 1, z1 + 1)
    plate -= prism(rect(-D["hw"], D["hw"], D["y_flat"], 60), -1, z1 + 1)
    return plate


def build_lid(b, c, D, clr):
    """v2's lid with the flap: cut free by two slits, thinned from the cell side, no bead; the pole under it, stood
    back delta from BOOT; the foot under its outer end; a notch round the key rib."""
    geo, f = D["geo"], D["f"]
    lid_z0, z_back, z_under = D["lid_z0"], D["z_back"], D["z_under"]
    r_disc = D["R_REAR"] - clr
    sel, holes, root, flap = flap_cut(c, D, r_disc)
    bead, _, _, _ = snap(c, D["R_REAR"], lid_z0 + c.LID_T/2)
    lid = prism(circle(r_disc), lid_z0, z_back) + (bead - prism(sel, lid_z0 - 1, z_back + 1))
    lid -= prism(holes, lid_z0 - 1, z_back + 1)
    lid -= prism(sel + root, lid_z0 - 1, z_under)
    lid -= prism(D["key_xy"].offset(clr, m3.JoinType.Miter, 4.0), lid_z0 - 1, z_back + 1)
    tip_z = geo["tip_z"]
    pole_cyl = m3.Manifold.cylinder(z_under + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([*D["pole_c"], tip_z])
    pole = pole_cyl - D["swept"]
    foot = prism(foot_xy(D, flap), D["z_ledge"] + D["g_stop"], z_under + 0.01)
    lid += pole + foot
    return lid, dict(sel=sel, flap_xy=flap, pole=pole, foot=foot)


def build(b, c, p, bt):
    D = design(b, c, p, bt)
    case = build_case(b, c, p, bt, D)
    plate = build_plate(b, c, D, c.FIT_CLR)
    lid, L = build_lid(b, c, D, c.FIT_CLR)
    D.update(**L)
    return D, case, plate, lid


# ---- bent states -------------------------------------------------------------
def flap_solid(D, lid):
    """The part of the lid that moves: the flap with its pole and foot, off the root by 0.3."""
    return lid ^ prism(D["sel"] ^ D["F"].b(rect(-60, D["f"].F_ROOT - 0.3, -60, 60)), -5, 50)


def bend_b(D, m, st):
    """K.bend in the flap frame, back to the badge frame."""
    return D["F"].b(K.bend(dict(z_ax=D["z_ax"]), D["f"], D["F"].l(m), st))


def states(D, p):
    s = K.states(dict(cs=D["cs"], g_stop=D["g_stop"]), p)
    s["touch"] = D["sw"]["touch_state"]
    return s


def forgiveness(face, centre, r_act):
    """How far the switch could be off its drawn place (any direction) and still sit wholly under the pole's face.
    Negative: part of it is already out from under."""
    lo, hi = -r_act, 2.0
    inside = lambda r: (m3.CrossSection.circle(r_act + r, 64).translate(centre) - face).area() < 1e-4
    if not inside(lo + 1e-3):
        return -r_act
    while hi - lo > 0.005:
        mid = (lo + hi)/2
        lo, hi = (mid, hi) if inside(mid) else (lo, mid)
    return lo


def lead_path(b, c, bt, D):
    """The cell's lead as a solid: out of the cell's end at mid-height, down the end gap into the plate's channel,
    along it to the JST hole and down onto the JST."""
    F, geo = D["F"], D["geo"]
    jx, jy = D["jst_l"]
    z1 = geo["FLOOR"] + c.PLATE_T
    z_ch = z1 - c.LEAD_CH_D + 0.05
    x0 = c.BATT_L/2 + c.BAY_CLR + 0.05
    batt_z0 = geo["FLOOR"] + c.PLATE_T + c.BAY_CLR
    w = rect(-60, 60, jy - bt.LEAD_W/2, jy + bt.LEAD_W/2)
    riser = prism(F.b(w ^ rect(x0, x0 + bt.LEAD_T, -60, 60)), z_ch, batt_z0 + c.BATT_T/2)
    run = prism(F.b(w ^ rect(jx, x0 + bt.LEAD_T, -60, 60)), z_ch, z_ch + bt.LEAD_T)
    drop = prism(m3.CrossSection.square([bt.LEAD_W]*2, True).translate([b.jst_x, b.jst_y]), b.jst_top_z + 0.05, z_ch + bt.LEAD_T)
    return riser + run + drop


# ---- checks ------------------------------------------------------------------
def run_battery_checks(b, c, p, bt, D, case, plate, lid, lid_r, plate_r):
    F, f, geo = D["F"], D["f"], D["geo"]
    W, cell = c.MIN_WALL, D["cell"]
    FLOOR, lid_z0, z_back = D["FLOOR"], D["lid_z0"], D["z_back"]
    flap_s = flap_solid(D, lid)
    fixed = lid - prism(D["sel"], -5, 50)
    st = states(D, p)
    flap_t = bend_b(D, flap_s, st["stop"])
    act = next(k for k in D["feats"] if k.name == f"{c.BUTTON} actuator")
    others = [k for k in D["feats"] if k.name != f"{c.BUTTON} actuator"]
    cell_xy = cell.slice(geo["FLOOR"] + c.PLATE_T + c.BAY_CLR + 1.0)

    print(f"\n6. The cell, turned {D['tilt']:.2f} deg so its long edge clears the pole")
    g = cell_gap(c, D["boot"], D["tilt"])
    check(g >= D["need"] - 1e-6, f"pole channel (Ø{c.POST_D:g} + {c.XY_CLR}) >= MIN_WALL + BAY_CLR off the cell", f"axis {g:.2f} from the cell")
    check(cell_gap(c, D["boot"], D["tilt"] - 0.05) < D["need"], "and that is the least turn that does it", f"{D['tilt'] - 0.05:.2f} deg is short")
    check(cell_gap(c, D["pole_c"], D["tilt"]) >= D["need"] - 1e-6, "the pole, stood back along the cell's edge, keeps it", f"{cell_gap(c, D['pole_c'], D['tilt']):.2f}")
    R_cell = 0.5*math.hypot(c.BATT_W, c.BATT_L)
    check(abs(D["R_REAR"] - R_cell - c.BAY_CLR) < 1e-6, "chamber = the cell's half-diagonal + BAY_CLR, as v2 (the turn costs nothing)", f"Ø{2*D['R_REAR']:.2f}")
    for nm, m in (("case and its ribs", case), ("plate", plate), ("lid", lid), ("lid, flap at the stop", fixed + flap_t),
                  ("lid, flap at the stop, foot late", fixed + bend_b(D, flap_s, st["late"]))):
        g = cell.min_gap(m, 3.0)
        check((cell ^ m).volume() < 1e-3 and g >= c.BAY_CLR - 0.01, f"cell >= BAY_CLR off the {nm}", f"gap {g:.2f}")
    moving = D["flap_xy"] + D["pole"].project() + D["foot"].project()
    v = (moving ^ cell_xy.offset(c.BAY_CLR, Round)).area()
    check(v < 1e-4, "the flap, pole and foot are never over the cell (plan, BAY_CLR)", f"{v:.4f} mm^2")
    for deg in (-1.0, 1.0):
        v = (cell.rotate([0, 0, deg]) ^ case).volume()
        check(v > 1e-2, f"turned {deg:+g} deg more, the cell runs into a rib (the ribs hold the turn)", f"{v:.3f} mm^3")
    for deg in (-1.0, 1.0):
        v = (lid.rotate([0, 0, deg]) ^ case).volume()
        check(v > 1e-2, f"turned {deg:+g} deg, the lid runs into the key rib (the pole finds its slot)", f"{v:.3f} mm^3")
    step = circle(D["R_REAR"] - 0.5) - geo["bore_xy"].offset(0.5, Round)
    z_pf = bbox(plate ^ prism(step, -5, 50))[0, 2]
    check(abs(z_pf - FLOOR) < 1e-3 and (plate.translate([0, 0, -0.05]) ^ case).volume() > 1e-2,
          "plate sits flush on the step", f"front face z {z_pf:.2f}")
    check(abs(bbox(flap_s)[1, 2] - z_back) < 1e-3, "flap's back face flush with the lid's", f"z {bbox(flap_s)[1, 2]:.2f}")
    lead = lead_path(b, c, bt, D)
    for nm, m in (("case", case), ("plate", plate), ("lid", lid), ("lid, flap pressed", fixed + flap_t), ("cell", cell)):
        v, g = (lead ^ m).volume(), lead.min_gap(m, 3.0)
        check(v < 1e-3, f"the lead's path is open past the {nm}", f"gap {g:.2f}")
    g = lead.min_gap(lid, 6.0)
    check(g >= 3.0, "the lead stays clear of the lid: nothing pinches it", f"{g:.2f} under it")

    print(f"\n7. Port: the overmold ({bt.OM_W:g} x {bt.OM_T:g}) on the pushed-down port, and the hood over it")
    mouth = b.tip_y - c.RAD_CLR
    box = lambda T: prism(rect(-bt.OM_W/2, bt.OM_W/2, mouth, mouth + 25), b.port_z - T/2, b.port_z + T/2)
    parts = {"case": case, "plate": plate, "lid": lid, "lid, flap pressed": fixed + flap_t}
    for nm, m in parts.items():
        v, g = (box(bt.OM_T) ^ m).volume(), box(bt.OM_T).min_gap(m, 5)
        check(v < 1e-3 and g >= p.PORT_OUT - 0.01, f"overmold clears the {nm} by >= PORT_OUT", f"gap {g:.2f}")
    fits = lambda T, ms, g0: all((box(T) ^ m).volume() < 1e-3 and box(T).min_gap(m, 5) >= g0 for m in ms)
    def largest(ms, g0):
        lo, hi = bt.OM_T, 30.0
        while hi - lo > 0.01:
            mid = (lo + hi)/2
            lo, hi = (mid, hi) if fits(mid, ms, g0) else (lo, mid)
        return lo
    T_parts = largest(parts.values(), p.PORT_OUT - 0.01)
    T_cell = largest(list(parts.values()) + [cell], 0.0)
    g = box(bt.OM_T).min_gap(cell, 5)
    print(f"      largest {bt.OM_W:g}-wide overmold: {T_parts:.2f} thick keeps PORT_OUT off every part; "
          f"{T_cell:.2f} touches the cell's corner (a {bt.OM_T:g} one is {g:.2f} under it)")
    ring = prism(circle(D["R_OUT"] - c.CHAMFER - 0.1) - circle(D["R_REAR"] + 0.05), D["z_roof"] + 0.05, D["z_roof"] + 0.15)
    v = (ring - case).volume()
    check(v < 1e-3, "behind the notch's roof the chamber wall is a full ring (the hood)",
          f"from z {D['z_roof']:.2f}, {D['z_roof'] - (FLOOR + c.PLATE_T):.2f} behind the plate's back face")
    check(c.CASE_WALL >= W, f"hood wall >= {W}", f"{c.CASE_WALL:.2f}")

    print(f"\n8. Flap: {f.F_W:g} wide, root {f.F_ROOT:g} along the cell's edge, {f.F_T:g} thick, slits {U.TAB_GAP}")
    check(f.F_T >= W - 1e-9, f"flap >= {W} thick", f"{f.F_T:g}")
    face = F.l(lid.slice(z_back - 0.15))
    thinnest = K.thinnest_beside_slits(face, f, D["yc"], W, -D["r_lid"])
    check(thinnest >= W - 0.02, f"lid beside each slit >= {W} wide wherever it continues", f"{thinnest:.2f}")
    foot_h = D["z_under"] - D["z_ledge"] - D["g_stop"]
    check(foot_h >= LAYER - 1e-6, f"foot at least a layer ({LAYER}) tall", f"{foot_h:.2f}")
    check(bt.LEDGE_D >= W, f"ribs >= {W} deep", f"{bt.LEDGE_D:g}")
    h1 = next(h for h in geo["hdrs"] if h.name.startswith("header H1"))
    x0, y0, x1, y1 = h1.outline.bounds()
    i, o = c.HDR_CLR, c.HDR_CLR + c.GUIDE_WALL
    for wn, w in {"-x wall": rect(x0 - o, x0 - i, y0, y1), "+x wall": rect(x1 + i, x1 + o, y0, y1)}.items():
        g = plate ^ prism(w, -5, FLOOR)
        span = bbox(g)[1, 1] - bbox(g)[0, 1] if not g.is_empty() else 0.0
        check(span >= 5.0, f"H1 {wn} beside the pole slot grips >= 5 of y", f"{span:.1f}")

    print(f"\n9. Pressed at the foot, the flap bent as the model has it (pole down {c.STROKE:.2f}, foot down {D['g_stop']:.2f})")
    g = bend_b(D, flap_s - D["pole"], st["click"]).min_gap(case, 3.0)
    check(g > 0.05, "at the click neither the foot nor the far tip has landed", f"{g:.2f} to go")
    foot_s = bend_b(D, D["foot"], st["stop"])
    v, g = (foot_s ^ case).volume(), foot_s.min_gap(case, 1.0)
    check(v < 2e-2 and g < 0.02, "at the stop the foot sits on the low rib", f"gap {g:.3f}, overlap {v:.4f} mm^3")
    v = (bend_b(D, D["pole"], st["stop"]) ^ act.solid()).volume()
    check(v > 1e-3, f"at the stop the pole has reached the {c.BUTTON} actuator", f"{v:.3f} mm^3")
    tip = flap_s ^ prism(F.b(rect(-60, f.FOOT_X - 0.05, -60, 60)), -5, 50)
    for tag, nm in (("stop", ""), ("late", f", foot {p.TOL} late")):
        body = bend_b(D, flap_s - D["foot"] - tip, st[tag])
        g = body.min_gap(case, 2.0)
        check((body ^ case).volume() < 1e-3 and g > 0.05, f"nothing but the foot and the far tip reaches the case{nm}", f"gap {g:.2f}")
        tb = bend_b(D, tip, st[tag])
        v, g = (tb ^ case).volume(), tb.min_gap(case, 1.0)
        check(v < 2e-2, f"the far tip rests on the rib at most (a second stop){nm}",
              f"gap {g:.2f}, overlap {v:.4f} mm^3, tip takes {st[tag]['T']:.1f} N")
    for tag in ("click", "stop", "late"):
        fl = bend_b(D, flap_s, st[tag])
        for k in others:
            g = fl.min_gap(k.solid(), 3.0)
            if g < 3.0 or tag == "stop":
                check((fl ^ k.solid()).volume() < 1e-3 and g > 0.05, f"at the {tag} the flap and pole clear {k.name}", f"gap {g:.2f}")
        for nm, m in (("plate (the pole in its slot)", plate), ("fixed lid", fixed)):
            g = fl.min_gap(m, 2.0)
            check((fl ^ m).volume() < 1e-3 and g > 0.05, f"at the {tag} the flap clears the {nm}", f"gap {g:.2f}")

    print(f"\n10. The pole: {c.POST_D:g} across, {D['lever']:.1f} below the flap's middle; it tips with the flap")
    sw = D["sw"]
    print(f"      tip swung toward the root: touch {sw['touch']:.2f}, click {sw['click']:.2f}, stop {sw['stop']:.2f}, "
          f"worst stop {sw['worst']:.2f}; drawn {D['delta']:.2f} back from {c.BUTTON} toward the tip")
    z_top = b.pcb_back_z + b.sw_cap_h
    r_act = b.sw_cap_d/2
    fg, cover = {}, {}
    for tag, dz in (("touch", 0.0), ("click", c.SW_TRAVEL), ("stop", c.SW_TRAVEL), ("late", c.SW_TRAVEL)):
        face = bend_b(D, D["pole"], st[tag]).slice(z_top - dz + 0.1)
        fg[tag] = (forgiveness(face, D["boot"], r_act), forgiveness(face, D["boot"], 0.0))
        cover[tag] = (face ^ m3.CrossSection.circle(r_act, 64).translate(D["boot"])).area()/(math.pi*r_act**2)
        print(f"      at the {tag:5s}: {100*cover[tag]:3.0f}% of the actuator under the pole; whole of it covered if "
              f"{c.BUTTON} is up to {fg[tag][0]:+.2f} off, its centre if up to {fg[tag][1]:.2f} off")
    check(cover["click"] >= 0.95, "at the click >= 95% of the actuator is under the pole", f"{100*cover['click']:.1f}%")
    check(min(cover.values()) >= 0.75, "from the touch to the worst stop >= 75% of it is (H1's keepout bites the rest)",
          f"{100*min(cover.values()):.0f}%")

    print(f"\n11. Forces and strains: {MAT.NAME}, E {MAT.E:g} +-{100*MAT.E_TOL:g}%, flexing parts <= {100*MAT.FLEX_MAX:g}%")
    s_safe = K.force_checks(f, p, c, D["cs"], D["g_stop"], lambda s: f"{s:.1f} from the root")
    m = D["cs"]["nom"]["m"]
    g_sl = D["z_under"] - D["z_ledge"] - LAYER*round(foot_h/LAYER)
    R_sl = max(v["m"]["press"](p.F_PRESS, m["d"], g_sl)["R"] for v in D["cs"].values())
    print(f"      the ledge sits on a layer line; the foot as sliced at {LAYER} layers lands {g_sl:.2f} over it; switch force on the stop then <= {R_sl:.1f} N")

    lid_pry = dict(R_BORE=D["R_REAR"] - 1.3, FLOOR=lid_z0, R_OUT=D["R_OUT"], pry=D["pry"])
    run_pry_checks(12, c, p, case, {"lid": (lid, D["R_REAR"] - c.FIT_CLR), "roomy lid": (lid_r, D["R_REAR"] - LID_CLR_ROOMY)},
                   lid_pry, part="lid")
    for nm, m in (("low rib", D["low"]), ("key rib", D["key"]), ("flap", prism(D["flap_xy"], lid_z0 - 1, z_back + 1)),
                  ("lead", lead)):
        g = D["pry"].min_gap(m, 10.0)
        check(g >= W, f"notch keeps >= {W} off the {nm}", f"{g:.2f}")
    blade = prism(rect(D["R_REAR"] - 0.95, D["R_OUT"] + 3, -1.5, 1.5).rotate(p.PRY_DEG), lid_z0 - 0.6, lid_z0 - 0.1)
    g = blade.min_gap(cell, 5.0)
    check((blade ^ cell).volume() < 1e-3, "the blade under the lid misses the cell", f"gap {g:.2f}")
    return dict(s_safe=s_safe, T_parts=T_parts, T_cell=T_cell, fg=fg, foot_h=foot_h, g_sl=g_sl, R_sl=R_sl)


# ---- renders -----------------------------------------------------------------
def renders(b, c, p, bt, D, case, plate, lid):
    Dv = lambda m: m.rotate([90, 0, 0]).refine_to_length(1.0)        # badge +y up, glass toward the viewer at azim 90
    shell, back_c, lid_c, dark, white, green, violet, red, steel, grey = ((0.30, 0.62, 0.78), (0.20, 0.45, 0.62),
        (0.24, 0.52, 0.70), (0.10, 0.10, 0.11), (0.95, 0.95, 0.90), (0.25, 0.70, 0.35), (0.62, 0.30, 0.80),
        (0.85, 0.25, 0.20), (0.62, 0.64, 0.68), (0.35, 0.35, 0.38))
    F, f = D["F"], D["f"]
    fs = {k.name: k.solid() for k in D["feats"] if not k.name.startswith("plug")}
    colour = lambda n: dark if n == "disc + tab" else green if n.startswith(c.BUTTON) else white
    flap_s = flap_solid(D, lid)
    fixed = lid - prism(D["sel"], -5, 50)
    flap_np = flap_s - D["pole"] - D["foot"]
    ribs_ = D["low"] + D["key"]
    case_nr = case - ribs_
    render([(Dv(case_nr), shell), (Dv(ribs_), red), (Dv(fixed), lid_c), (Dv(flap_np), violet)], OUT + "back.png", elev=20, azim=-90,
           title="From the back: the lid with the BOOT flap (violet); press its outer end, in the dip in the rim")
    render([(Dv(case_nr), shell), (Dv(ribs_), red), (Dv(plate), back_c), (Dv(D["cell"]), steel), (Dv(D["pole"]), green)],
           OUT + "lid-off.png", elev=0, azim=-90,
           title=f"Lid off: the cell turned {D['tilt']:.1f} deg, held by the two ribs (red); the lid's pole (green) passes beside it")
    render([(Dv(fixed), lid_c), (Dv(flap_np), violet), (Dv(D["pole"]), green), (Dv(D["foot"]), red)], OUT + "lid-underside.png",
           elev=30, azim=60, light=(0.35, 0.8, 0.45), title="Lid from the cell side: the pole (green) and the foot (red) under the flap")

    st = states(D, p)
    # a section in the flap frame, along the flap through the pole and the foot, looking from the cell's side
    y0 = D["boot_l"][1] - 0.6
    L = lambda m: F.l(m)
    def section(pressed, path, title, box):
        sw_ = (lambda m: bend_b(D, m, st["stop"])) if pressed else (lambda m: m)
        a = fs[f"{c.BUTTON} actuator"]
        a = a.trim_by_plane([0, 0, -1], -(b.pcb_back_z + b.sw_cap_h - c.SW_TRAVEL)) if pressed else a
        parts = [(case, shell), (plate, back_c), (fixed, lid_c), (sw_(flap_np), violet), (sw_(D["pole"]), green),
                 (sw_(D["foot"]), red), (a, green), (D["cell"], steel)] + \
                [(s, colour(n)) for n, s in fs.items() if not n.endswith("actuator")]
        cut = []
        for m, col in parts:
            m = (L(m).trim_by_plane([0, 1, 0], y0) ^ box).refine_to_length(0.6)
            if not m.is_empty(): cut.append((m, col))
        render(cut, path, elev=0, azim=-90, title=title, figsize=(13, 7), zoom=1.7)
    full = m3.Manifold.cube([36, 12, 18]).translate([-25, y0, 4.0])
    tipbox = m3.Manifold.cube([9, 12, 6.5]).translate([D["px"] - 4.5, y0, 3.5])
    rest_t = f"at rest: pole {c.REST_CLR} over BOOT, foot (red) {D['g_stop']:.2f} over the low rib"
    press_t = f"pressed at the foot to the stop: foot on the rib, pole {c.STROKE:.2f} down on BOOT (bent as modelled)"
    section(False, OUT + "section-rest.png", f"Section along the flap through the pole, {rest_t}", full)
    section(True, OUT + "section-pressed.png", f"Same section, {press_t}", full)
    section(False, OUT + "section-tip-rest.png", f"The pole's tip at rest, {D['delta']:.2f} back from BOOT toward the flap's tip (left)", tipbox)
    section(True, OUT + "section-tip-pressed.png", f"At the stop: the pole has tipped {D['sw']['stop']:.2f} toward the root (right), BOOT still under it", tipbox)

    mouth = b.tip_y - c.RAD_CLR
    plug = prism(rect(-bt.OM_W/2, bt.OM_W/2, mouth, mouth + 12), b.port_z - bt.OM_T/2, b.port_z + bt.OM_T/2)
    plug += prism(rect(-4.2, 4.2, mouth - 6.5, mouth), b.port_z - 1.25, b.port_z + 1.25)
    pale = (0.80, 0.80, 0.78)
    fs_dn = {n: s.translate([0, -c.RAD_CLR, 0]) for n, s in fs.items()}       # the board pushed down by the plug
    top = [(case, shell), (plate, back_c), (lid, lid_c), (D["cell"], steel), (plug, pale)] + \
          [(s, (0.72, 0.74, 0.78) if n == "USB-C receptacle" else colour(n)) for n, s in fs_dn.items()]
    crop = prism(rect(-17, 17, D["y_flat"] - 10, 50), -10, 30)
    render([(Dv(m ^ crop), col) for m, col in top], OUT + "port-plug.png", elev=30, azim=-55, light=(0.3, -0.8, 0.5),
           title=f"12 o'clock: a {bt.OM_W:g} x {bt.OM_T:g} overmold (pale) on the port, the board pushed down; the chamber wall hoods it")
    cut = []
    for m, col in top:
        m = (m.trim_by_plane([-1, 0, 0], 0.0) ^ prism(rect(-30, 30, 8, 40), -3, 25)).refine_to_length(0.6)
        if not m.is_empty(): cut.append((m, col))
    render(cut, OUT + "port-section.png", elev=0, azim=0, figsize=(11, 8), zoom=1.3, light=(0.9, -0.3, 0.4),
           title=f"Section on the centre line, 12 o'clock to the right, back up: the overmold under the hood (from z {D['z_roof']:.1f}) and the cell's corner")

    lay = [(case.translate([0, 0, c.LIP_T]), shell, -30), (lid.rotate([0, 180, 0]).translate([0, 0, D["z_back"]]), lid_c, 30),
           (plate.rotate([0, 180, 0]).translate([0, 0, D["FLOOR"] + c.PLATE_T]), back_c, 88)]
    render([(m.translate([dx, 0, 0]).refine_to_length(1.5), col) for m, col, dx in lay], OUT + "print-layout.png",
           elev=30, azim=-70, title="Print as exported, no supports: case bezel down, lid and plate back face down (lid beside the case)",
           figsize=(13, 8), zoom=1.5)
    E = 26.0
    ex = [(case_nr, shell), (ribs_, red), (D["cell"].translate([0, 0, 2.2*E]), steel), (plate.translate([0, 0, 1.6*E]), back_c),
          (fixed.translate([0, 0, 3.0*E]), lid_c), (flap_np.translate([0, 0, 3.0*E]), violet),
          (D["pole"].translate([0, 0, 3.0*E]), green), (D["foot"].translate([0, 0, 3.0*E]), red)] + \
         [(s.translate([0, 0, 0.8*E]), colour(n)) for n, s in fs.items()]
    render([(Dv(m), col) for m, col in ex], OUT + "exploded.png", elev=14, azim=-32, figsize=(9, 12),
           title="Exploded from the back: case, badge, plate, cell, lid with the BOOT flap")


# ---- main --------------------------------------------------------------------
def main():
    b, c, p, bt = Badge(), Case(), Pendant(), Battery()
    D, case, plate, lid = build(b, c, p, bt)
    plate_r = build_plate(b, c, D, U.PLATE_DISC_CLR_ROOMY)
    lid_r, _ = build_lid(b, c, D, LID_CLR_ROOMY)
    m = D["cs"]["nom"]["m"]
    asm = bbox(case + plate + lid)
    mass = {k: s.volume()*MAT.RHO for k, s in (("case", case), ("plate", plate), ("lid", lid))}
    print(f"Battery pendant Ø{2*D['R_OUT']:.2f} x {asm[1, 2] - asm[0, 2]:.2f}; cell turned {D['tilt']:.2f} deg; flap {D['f'].F_W:g} wide, "
          f"{D['f'].F_T:g} thick; foot {D['g_stop']:.2f} over the rib; click {m['P_click']:.2f} N at the foot; "
          + ", ".join(f"{k} {g:.1f} g" for k, g in mass.items()) + " (solid)")
    V2.run_checks(b, c, D["feats"], case, plate, lid, D["cell"], D["geo"], recess=False)
    run_battery_checks(b, c, p, bt, D, case, plate, lid, lid_r, plate_r)
    print()
    export(case, STL + "Battery pendant - case.stl", lambda m_: m_.translate([0, 0, c.LIP_T]))
    flip = lambda z: (lambda m_: m_.rotate([0, 180, 0]).translate([0, 0, z]))
    export(plate, STL + "Battery pendant - plate.stl", flip(D["FLOOR"] + c.PLATE_T))
    export(plate_r, STL + "Battery pendant - plate (roomy).stl", flip(D["FLOOR"] + c.PLATE_T))
    export(lid, STL + "Battery pendant - lid (flap).stl", flip(D["z_back"]))
    export(lid_r, STL + "Battery pendant - lid (flap, roomy).stl", flip(D["z_back"]))
    if "--no-render" not in sys.argv:
        renders(b, c, p, bt, D, case, plate, lid)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
