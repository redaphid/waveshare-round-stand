#!/usr/bin/env python3
"""
Pendant for the 1.28 badge: the USB-only pocketwatch with nothing extra. Three printed parts.

  case        one plain circle that wraps the USB-C tab, cut off flat at 12 o'clock below the port:
              the USB-C receptacle stands PORT_OUT past the flat even with the board pushed fully
              down, so any cable's overmold seats on the port and touches nothing. The back plate and
              kid button stop at the same flat. Walls MIN_WALL: the rim is a hollow ring (a channel
              open at the back) instead of solid plastic.
  back plate  the USB-only button plate (U-slot flexure tab, post over BOOT), with a longer
              tab (TAB_L) so the kid button can push it partway along: past the click the tab
              bends instead of crushing the switch.
  kid button  optional. A disc over the whole back that rocks on two fulcrum pads at the top.
              Press anywhere below them: a nub pushes the tab, BOOT clicks, then two wings beside
              the nub land on the plate (the stop: the tab is pushed a fixed H, however hard the
              press). A ring of pads on the case wall is the backup stop. Fingers snap under a
              ledge in the rim channel.

Badge, Case, features and snap come from build_pocketwatch.py, the plate from
build_pocketwatch_usb.py, so badge or fit changes apply here too.

battery: pass (T, W, L) in mm (thickness, across x, along y) to grow a battery pocket between
the button plate and the kid button. Only `Stack` and the pocket cut depend on it.

Run with ~/.venvs/cad/bin/python from the repo root. --no-render for a fast check run,
--battery T,W,L for the battery-pocket variant (not exported).
"""
import sys, math
from contextlib import contextmanager
from dataclasses import dataclass
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3
import build_pocketwatch_usb as U
from build_pocketwatch import (Badge, Case, Round, SEG, snap, chamfered, circle, rect, prism, union, bbox,
                               revolve, check, FAILS, export, render)

OUT = "pocketwatch/pendant/renders/"
STL = "stl/pocketwatch/pendant/"


@dataclass(frozen=True)
class Material:
    """What Aaron prints. Every force and strain check reads these, at E x (1 +- E_TOL)."""
    NAME: str = "PLA"
    E: float = 2500.0            # MPa, along the layers
    E_TOL: float = 0.25
    FLEX_MAX: float = 0.010      # strain, worst case, for anything that flexes in use (tab, disc, snap)
    ONCE_MAX: float = 0.015      # strain, features that flex once
    INTERLAYER: float = 10.0     # MPa across the layers: pessimistic, PLA is brittle
    STRENGTH: float = 45.0       # MPa along the layers (one-off abuse loads)
    RHO: float = 1.24e-3         # g/mm^3, counted solid (a real print with infill is lighter)

    @property
    def E_lo(self): return self.E*(1 - self.E_TOL)

    @property
    def E_hi(self): return self.E*(1 + self.E_TOL)


MAT = Material()


@dataclass(frozen=True)
class Pendant:
    PORT_OUT: float = 0.5       # least the receptacle mouth stands past every part with the board pushed fully down
    FLAT_SOFT: float = 1.5      # radius where the flat meets the circle
    FRONT_R: float = 2.0        # outer front edge round
    BACK_R: float = 0.6         # outer back edge round (the rim is only MIN_WALL thick)
    TAB_L: float = 21.0         # button-plate flexure, root to post (USB-only plate: 12)
    TAB_R: float = 2.2          # half-width at the post (the plate edge is close there)
    TAB_W: float = 8.0          # full width past the neck: wider = less strain to click
    TAB_NECK: float = 3.0       # narrow this far from the post, then ...
    TAB_TAPER: float = 7.0      # ... full width from here on
    TAB_T: float = 1.2          # tab thickness (thinned from the badge side)
    # kid button
    K_T: float = 2.0            # disc thickness
    K_GAP: float = 1.4          # disc underside above the plate back face: > the ring pads' drop at 6 o'clock
    K_CLR: float = 0.2          # disc outline inside the case outline
    K_FACE_R: float = 1.0       # face edge round
    NUB_A: float = 17.0         # nub on the tab, this far from the tab root
    NUB_D: float = 3.0
    NUB_G: float = 0.15         # nub tip above the tab at rest
    SPARE: float = 0.14         # tab pushed this far past the click when the wings land (nominal)
    TOL: float = 0.10           # error on that spare, either way (print + model)
    WING_W: float = 2.0         # stop wings beside the nub: across y
    WING_L: float = 4.0         # along x
    WING_CLR: float = 0.5       # wing to the U-slot
    RING_EXTRA: float = 0.10    # ring pads land this much (at the nub) after the wings: a backup
    PAD_W: float = 0.3          # ring pads stay this far inside the case back face, each side
    SKIRT_GAP: float = 0.05     # rim skirt clears the case back by this more than the pads
    # twist-lock: teeth outside the case wall turn LOCK under flat ledges; a latch key stops the turn back
    T_T: float = 1.6            # tooth, radial
    T_W: float = 6.0            # tooth (and latch key), along the rim
    T_CLR: float = 0.3          # tooth to the case wall, radial
    HOOK: float = 0.45          # tooth hook under the ledge
    GROOVE: float = 0.58        # ledge groove into the case wall (0.6 would land on the back chamfer's edge and pinch)
    HOOK_H: float = 1.0
    HOOK_PLAY: float = 0.10     # hook below the ledge at rest (axial)
    LOCK_PAST: float = 5.0      # locked tooth ends this far past its entry channel (the latch sits in between)
    CHANNELS: tuple = (10.0, 150.0, 215.0, 290.0)   # entry channels, deg from +x seen from the back; the last takes the latch key
    PRY_DEG: float = 345.0      # pry notch: middle of the one rim arc the lock grooves leave free (U's 120 is on the flat's corner)
    LATCH_W: float = 12.0       # latch: a radial tongue in the disc over the last channel, root inboard
    LATCH_L: float = 10.0
    LATCH_T: float = 1.0
    KEY_E: float = 0.8          # latch key down into its channel
    T_CHILD: float = 1.0        # N.m: the most we assume a child twists the rim with (a firm bottle-cap twist)
    # loads and limits
    F_SW: float = 2.0           # switch force (a guess)
    F_SW_MAX: float = 8.0       # most the switch (and the glass on its lip) may take on the stop, nominal
    F_SW_WORST: float = 16.0    # worst case (a hard mash with every tolerance stacked): a known weakness, see the README
    TAB_WORST: float = 0.017    # tab strain, worst case (agreed for this tab: PLA's 1% is the nominal limit)
    F_PRESS: float = 30.0       # a hard press
    F_EASY: float = 10.0        # what a child presses without trying
    F_PULL: float = 50.0        # least pull-off: ~5x a fingernail pull on a flush seam
    F_PUSH_MAX: float = 40.0    # most it may take to fit the kid button
    NU: float = 0.35
    FINGER_PAD_R: float = 5.0   # a fingertip's contact patch radius


@dataclass(frozen=True)
class Stack:
    """z levels behind the badge. The battery is the only thing that moves them."""
    z_plate: float              # button plate back face
    z_back: float               # case back face: where the kid button sits
    battery: tuple | None

    @staticmethod
    def of(c: Case, geo, battery):
        return Stack(geo["Z_CASE"], geo["Z_CASE"] + (battery[0] + 2*c.BAY_CLR if battery else 0.0), battery)


# ---- helpers ----------------------------------------------------------------
def rounded(cs, z0, z1, r0=0.0, r1=0.0, steps=6):
    """Prism of a CONVEX outline with its z0 / z1 edges rounded by r0 / r1 (hull of layers)."""
    layers = [prism(cs, z0 + r0, z1 - r1)]
    for r, z, sgn in ((r0, z0, +1), (r1, z1, -1)):
        for i in range(steps + 1) if r else ():
            ph_ = math.pi/2 * i/steps
            inset, dz = r*(1 - math.sin(ph_)), r*(1 - math.cos(ph_))
            zz = z + sgn*dz
            layers.append(prism(cs.offset(-inset, m3.JoinType.Miter, 4.0) if inset > 1e-4 else cs, min(zz, zz + sgn*0.01), max(zz, zz + sgn*0.01)))
    return m3.Manifold.batch_hull(layers)


def sector(r0, r1, a0, a1):
    R = 60.0
    wedge = m3.CrossSection([[(0, 0)] + [(R*math.cos(a), R*math.sin(a)) for a in np.linspace(a0, a1, 8)]])
    h = lambda r: circle(r).rotate(180/SEG)      # half a segment off the case's own circles, or vertices pinch
    return (h(r1) - h(r0)) ^ wedge


def tilted(m, y_h, z0, slope, extra=0.0):
    """Keep the part of m on or above the plane z = z0 + extra + slope*(y_h - y)."""
    n = np.array([0.0, slope, 1.0]); L = np.linalg.norm(n)
    return m.trim_by_plane(list(n/L), (z0 + extra + slope*y_h)/L)


# ---- geometry ---------------------------------------------------------------
def tab_width(p, d):
    """Tab width at distance d from the post (array or scalar)."""
    w0, w1 = 2*p.TAB_R, p.TAB_W
    return np.clip(w0 + (w1 - w0)*(np.asarray(d) - p.TAB_NECK)/(p.TAB_TAPER - p.TAB_NECK), w0, w1)


def tab_xy(p, px, py):
    """The flexure, symmetric about the post's y, narrow at the post, root at px + TAB_L."""
    d = np.linspace(0, p.TAB_L, 49)
    hw = tab_width(p, d)/2
    pts = [(px + di, py - h) for di, h in zip(d, hw)] + [(px + di, py + h) for di, h in zip(d[::-1], hw[::-1])]
    return m3.CrossSection([pts]) + circle(p.TAB_R).translate([px, py])


def button_plate(b, c, p, clr):
    """The USB-only plate (build_pocketwatch_usb) with this pendant's tab cut into it: a U-slot round the tab,
    the tab thinned to TAB_T from the badge side, the post moved onto it."""
    feats, _, plate, geo = U.build(b, c, clr)
    FLOOR = geo["FLOOR"]
    px, py = geo["sw"][c.BUTTON], b.sw_y
    tab = tab_xy(p, px, py)
    slot = (tab.offset(U.TAB_GAP, Round) - tab) ^ rect(-60, px + p.TAB_L, -60, 60)    # open at the root end
    skirt_in = geo["R_BORE"] - c.FIT_CLR - c.SKIRT_WALL
    plate -= geo["post_cyl"]
    plate -= prism(slot, FLOOR - 1, geo["Z_CASE"] + 1)
    plate -= prism(tab, FLOOR - 1, FLOOR + geo['Z_CASE'] - FLOOR - p.TAB_T)
    plate -= prism(tab.offset(U.TAB_GAP + 0.05, Round) ^ circle(skirt_in - 0.15), -1, FLOOR + 0.01)   # header guides off the tab
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_cyl = m3.Manifold.cylinder(geo['Z_CASE'] - p.TAB_T + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([px, py, tip_z])
    plate += post_cyl - union(f.keepout(c.FLOAT) for f in feats if not f.name.startswith(c.BUTTON))
    # every part stops at one flat: a plug pushes the floating board down RAD_CLR before it seats
    y_flat = b.tip_y - c.RAD_CLR - p.PORT_OUT
    plate = plate.trim_by_plane([0, -1, 0], -y_flat)
    geo.update(tab=tab, slot=slot, post_cyl=post_cyl, R_DISC=geo["R_REAR"] - clr, y_flat=y_flat)
    return feats, None, plate, geo


def case_body(b: Badge, c: Case, p: Pendant, feats, geo, z_back):
    """The pendant case without the twist-lock: the USB-only circle and crown boss cut off at the flat, bore,
    counterbore, snap groove, keepouts and the pry notch. Adds R_OUT, boss, groove_r_p and pry to geo."""
    bore_xy = feats[0].grown()
    R_BORE, R_REAR, FLOOR = geo["R_BORE"], geo["R_REAR"], geo["FLOOR"]
    R_OUT = R_REAR + c.CASE_WALL                                     # the USB-only outline: the circle ...
    boss = (bore_xy.offset(c.CASE_WALL, Round) ^ rect(-40, 40, 10, 40)).hull()   # ... and its crown boss beside the tab
    below = rect(-60, 60, -60, geo["y_flat"])                        # clipped before chamfering, so the flat is chamfered too

    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2   # as build_pocketwatch_usb
    _, groove_p, _, groove_r_p = snap(c, R_BORE, zb_p)
    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    case = chamfered([circle(R_OUT) ^ below, boss ^ below], -c.LIP_T, z_back, c.CHAMFER, U.BACK_CHAMFER)
    case -= prism(bore_xy, 0.0, z_back + 1)
    case -= prism(circle(R_REAR), FLOOR, z_back + 1)
    case -= window.rotate([0, 0, 90/SEG]).translate([0, 0, -c.LIP_T - 0.01])   # quarter segment off the bore's vertices, or one pinches
    case -= groove_p
    case -= union(keep.values())
    pry = U.pry_cut(R_BORE, R_OUT, FLOOR, z_back, p.PRY_DEG)
    case -= pry
    geo.update(R_OUT=R_OUT, boss=boss, groove_r_p=groove_r_p, pry=pry)
    return case


def build(b: Badge, c: Case, p: Pendant, battery=None, disc_clr=U.PLATE_DISC_CLR):
    feats, _, plate, geo = button_plate(b, c, p, disc_clr)
    st = Stack.of(c, geo, battery)
    case = case_body(b, c, p, feats, geo, st.z_back)
    bore_xy = feats[0].grown()
    R_REAR, FLOOR, R_OUT, boss = geo["R_REAR"], geo["FLOOR"], geo["R_OUT"], geo["boss"]
    below = rect(-60, 60, -60, geo["y_flat"])
    batt = None
    if battery:
        T, Wb, Lb = battery
        batt = prism(rect(-Wb/2, Wb/2, -Lb/2, Lb/2), st.z_plate + c.BAY_CLR, st.z_plate + c.BAY_CLR + T)
        case -= prism(rect(-Wb/2 - c.BAY_CLR, Wb/2 + c.BAY_CLR, -Lb/2 - c.BAY_CLR, Lb/2 + c.BAY_CLR), st.z_plate, st.z_back + 1)

    # ---- kid button
    px, py = geo["sw"][c.BUTTON], b.sw_y
    x_n = px + p.TAB_L - p.NUB_A
    kz0, kz1 = st.z_back + p.K_GAP, st.z_back + p.K_GAP + p.K_T
    pocket = circle(R_REAR) + bore_xy                                # what the back plate covers
    case_top = circle(R_OUT - U.BACK_CHAMFER) - pocket.offset(0.5, m3.JoinType.Miter, 4.0)   # case back face, off the plate
    pad_xy = case_top.offset(-p.PAD_W, Round)
    y_h = pad_xy.bounds()[3]                                         # fulcrum: the pads' top edge, gap 0
    model = tab_model(p, c, b)
    H = model["ya_click"] + p.SPARE                                  # nub tip below the wing tips: tab push at the stop
    d_stop = p.NUB_G + H                                             # nub travel when the wings land
    slope = (d_stop + p.RING_EXTRA) / (y_h - py)                     # ring pads: rotation when they land, rad
    R_K = R_OUT + p.T_CLR + p.T_T                                    # the teeth hang outside the case wall
    k_out = (circle(R_K) + boss.offset(-p.K_CLR, m3.JoinType.Miter, 4.0)).hull() ^ below
    # one solid for the disc and its rim (separate pieces would share the outline's faces and pinch):
    # the rim follows the ring pads' tilt down to the case, the middle is recessed K_GAP over the plate
    kid = rounded(k_out, st.z_back - 2, kz1, 0.0, p.K_FACE_R)
    kid = tilted(kid, y_h, st.z_back, slope, p.SKIRT_GAP).trim_by_plane([0, 0, 1], st.z_back + p.SKIRT_GAP)
    kid -= prism(pocket.offset(0.1, m3.JoinType.Miter, 4.0), st.z_back - 3, kz0)
    pads = tilted(prism(pad_xy, st.z_back - 2, kz0 + 0.01), y_h, st.z_back, slope)
    nub = m3.Manifold.cylinder(kz0 + 0.01 - (st.z_plate + p.NUB_G), p.NUB_D/2, p.NUB_D/2, 64).translate([x_n, py, st.z_plate + p.NUB_G])
    wy = float(tab_width(p, x_n - px))/2 + U.TAB_GAP + p.WING_CLR    # beside the tab and its U-slot
    wing_xy = rect(x_n - p.WING_L/2, x_n + p.WING_L/2, py - wy - p.WING_W, py - wy) + \
              rect(x_n - p.WING_L/2, x_n + p.WING_L/2, py + wy, py + wy + p.WING_W)
    th_w = d_stop/(y_h - py)                                         # rotation when the wings land
    wings = tilted(prism(wing_xy, st.z_plate - 2, kz0 + 0.01), y_h, st.z_plate, th_w)
    # twist-lock: teeth hook flat ledges in grooves round the case wall; a latch key in the last channel stops the turn back
    lock_cut, teeth, tl = twist_lock(p, st, R_OUT, FLOOR, kz0, slope*(y_h + R_OUT))
    case -= lock_cut
    cL = math.radians(p.CHANNELS[-1])
    latch_l = rect(R_K - p.LATCH_L, R_K + 1, -p.LATCH_W/2, p.LATCH_W/2)
    latch = latch_l.rotate(math.degrees(cL))
    slot = ((latch_l.offset(0.8, Round) - latch_l) ^ rect(R_K - p.LATCH_L, 60, -60, 60)).rotate(math.degrees(cL))
    kid -= prism(slot, st.z_back - 3, kz1 + 1)
    thin = rect(R_K - p.LATCH_L + 0.2, R_K + 1, -p.LATCH_W/2, p.LATCH_W/2).rotate(math.degrees(cL))   # 0.2 off the slot's end, or edges coincide
    latch_pad = tilted(prism(pad_xy ^ latch.offset(-0.2, Round), st.z_back - 2, kz1 - p.LATCH_T + 0.01), y_h, st.z_back, slope)
    key = prism(sector(R_OUT - p.HOOK, tl["r_fi"] + p.T_T, cL - tl["a_t"], cL + tl["a_t"]), st.z_back - p.KEY_E, kz1 - p.LATCH_T + 0.01)
    kid = kid + (pads - prism(latch.offset(0.9, Round), -50, 50)) + latch_pad + nub + wings + teeth + key

    geo.update(R_K=R_K, lock_cut=lock_cut, pad_xy=pad_xy, y_h=y_h,
               slope=slope, d_stop=d_stop, H=H, th_w=th_w, x_n=x_n, py=py, px=px, kz0=kz0, kz1=kz1, nub=nub,
               wings=wings, pads=pads, teeth=teeth, key=key, latch=latch, tl=tl, model=model, k_out=k_out, batt=batt)
    return feats, case, plate, kid, geo, st


def twist_lock(p, st, R_OUT, FLOOR, kz0, drop):
    """Bayonet. For each channel angle: an entry channel down the outside of the case wall and a groove arc running
    on past it, closed at the far end. The kid button's tooth drops down the channel and turns LOCK into the groove,
    its hook under the groove's flat ledge. Returns the case cuts, the teeth and their numbers."""
    a_t = p.T_W/2/R_OUT                                   # tooth half-angle at the wall
    a_c = (p.T_W/2 + 0.25)/R_OUT                          # channel half-angle
    turn = (p.T_W + p.LOCK_PAST)/R_OUT
    z_c = FLOOR - 0.35                                    # ledge below FLOOR: behind it is the bore, not the thinner counterbore wall
    z_hk = z_c - p.HOOK_PLAY                              # hook top at rest
    z_tb = z_hk - p.HOOK_H                                # tooth bottom
    z_lo = z_tb - drop - 0.3                              # groove floor: room for the teeth to ride down when the button rocks
    r_fi, r_g = R_OUT + p.T_CLR, R_OUT - p.GROOVE
    ring = lambda r0, r1, a0, a1, z0, z1: prism(sector(r0, r1, a0, a1), z0, z1)
    cuts, teeth = [], []
    ins = 0.15/R_OUT
    for cd in p.CHANNELS:
        ca = math.radians(cd)
        cuts.append(ring(r_g + 0.02, R_OUT + 1, ca - a_c, ca + a_c, z_c - 0.3, st.z_back + 1))   # 0.02 off the groove's wall
        cuts.append(ring(r_g, R_OUT + 1, ca - a_c - 0.05/R_OUT, ca + turn + a_t + 0.2/R_OUT, z_lo, z_c))   # not flush with the channel's sides
        ta = ca + turn
        teeth.append(ring(r_fi, r_fi + p.T_T, ta - a_t, ta + a_t, z_tb, kz0 + 0.01)
                     + ring(R_OUT - p.HOOK, r_fi + 0.1, ta - a_t + ins, ta + a_t - ins, z_tb + 0.05, z_hk))
    return union(cuts), union(teeth), dict(turn=turn, a_t=a_t, a_c=a_c, z_c=z_c, z_tb=z_tb, z_lo=z_lo, r_fi=r_fi)


def tab_model(p, c, b, E=MAT.E):
    """The plate's tab as an Euler beam of varying width: root fixed, nub load P at NUB_A from the root,
    switch at the post. Before the click the switch is a 2 N force; once it bottoms it is a rigid prop."""
    L, a, t = p.TAB_L, p.NUB_A, p.TAB_T
    xs = np.linspace(0, L, 1201)                                    # from the root
    w = tab_width(p, L - xs)
    EI = E*w*t**3/12
    flex = lambda xi, xj: np.trapezoid(np.clip(xi - xs, 0, None)*np.clip(xj - xs, 0, None)/EI, xs)
    cLP, cLL, caP = flex(L, a), flex(L, L), flex(a, a)
    caL = cLP
    P_click = (c.STROKE + cLL*p.F_SW)/cLP
    ya_click = caP*P_click - caL*p.F_SW
    k_od = 1/(caP - caL*caL/cLL)                       # nub stiffness once the switch has bottomed
    share = cLP/cLL                                    # extra switch force per extra nub force
    def at(over):                                      # nub pushed `over` past the click
        dP = k_od*max(over, 0.0)
        P, R = P_click + dP, p.F_SW + share*dP
        M = P*np.clip(a - xs, 0, None) - R*(L - xs)
        return dict(P=P, R=R, eps=float(np.max(np.abs(6*M/(E*w*t*t)))))
    return dict(P_click=P_click, ya_click=ya_click, k_od=k_od, share=share, at=at)


def tab_cases(p, c, b, geo, F):
    """The tab on the wing stop at E low / nominal / high. The stop height H is fixed by the design at nominal E;
    what the tab is pushed past the click shifts with E, the print (TOL) and the plate sagging under F."""
    H = geo["H"]
    ap, bp = (geo["R_BORE"] + geo["R_REAR"])/2, math.hypot(geo["x_n"], geo["py"])
    out = {}
    for tag, E in (("lo", MAT.E_lo), ("nom", MAT.E), ("hi", MAT.E_hi)):
        m = tab_model(p, c, b, E)
        Dp = E*c.PLATE_T**3/(12*(1 - p.NU**2))
        sag = (3 + p.NU)/(1 + p.NU)*F*(ap*ap - bp*bp)**2/(16*math.pi*Dp*ap*ap)   # Roark, off-centre load on the plate
        early = H - p.TOL - m["ya_click"]                      # least push past the click: wings land early
        worst = H + p.TOL - m["ya_click"] + sag                # most: wings land late, a hard press sags the plate
        out[tag] = dict(m=m, sag=sag, early=early, worst=worst, nom=m["at"](H - m["ya_click"]), hi=m["at"](worst))
    return out


def rock(m, geo, st, th):
    """Kid button rocked th radians about the fulcrum line (y = y_h on the case back); + presses."""
    return m.translate([0, -geo["y_h"], -st.z_back]).rotate([math.degrees(th), 0, 0]).translate([0, geo["y_h"], st.z_back])


# ---- checks ----------------------------------------------------------------
def run_pendant_checks(b, c, p, feats, case, plate, kid, geo, st):
    W = c.MIN_WALL
    print("\n8. Case: the USB-only outline, snap ledge wall, port sticking out")
    walls = {"case wall behind the lock grooves (vs the plate groove)": geo["R_OUT"] - p.GROOVE - geo["groove_r_p"],
             "case wall behind the entry channels (vs the counterbore)": geo["R_OUT"] - p.GROOVE - geo["R_REAR"],
             "kid button disc": p.K_T}
    for nm, t in walls.items():
        check(t >= W - 1e-6, f"{nm} >= {W}", f"{t:.2f}")
    d_n = geo["y_h"] - geo["py"]
    th_w = geo["th_w"]
    mouth = b.tip_y - c.RAD_CLR                                      # receptacle mouth with the board pushed fully down
    overmold = prism(rect(-15, 15, mouth, mouth + 25), -10, 30)
    print(f"      receptacle sticks out >= PORT_OUT {p.PORT_OUT} past every part with the board pushed down; any overmold seats")
    for nm, m in (("case", case), ("back plate", plate), ("kid button", kid),
                  ("kid button pressed to the stop", rock(kid, geo, st, th_w)),
                  ("kid button rocked to the ring", rock(kid, geo, st, geo["slope"]))):
        v, g = (overmold ^ m).volume(), overmold.min_gap(m, 5)
        check(v < 1e-3 and g >= p.PORT_OUT - 0.01, f"overmold on the pushed-down port clears the {nm}", f"gap {g:.2f}")

    print("\n9. Kid button at rest")
    for nm, m in (("case", case), ("back plate", plate)):
        v = (kid ^ m).volume()
        check(v < 1e-3, f"kid button does not overlap the {nm}", f"{v:.4f} mm^3")
    g_f = kid.min_gap(case, 1.0)
    check(g_f < 0.02, "fulcrum pads sit on the case back (gap 0)", f"{g_f:.3f} at y {geo['y_h']:.1f}")
    g_n = geo["nub"].min_gap(plate, 2.0)
    check(abs(g_n - p.NUB_G) < 0.02, "nub tip sits NUB_G off the tab", f"{g_n:.2f}")
    g_d = (kid - geo["nub"] - geo["wings"]).min_gap(plate, 3.0)
    check(g_d > 0.2, "the rest of the kid button clears the back plate", f"{g_d:.2f}")
    g_w = geo["wings"].min_gap(plate, 3.0)
    check(g_w > p.NUB_G, "wings sit NUB_G + H (less the tilt) off the plate", f"{g_w:.2f}")
    for nm, dz, want in (("lifts HOOK_PLAY freely", p.HOOK_PLAY - 0.03, False), ("pulled HOOK_PLAY + 0.1 catches", p.HOOK_PLAY + 0.1, True)):
        v = (kid.translate([0, 0, dz]) ^ case).volume()
        check((v > 0.5) == want, f"kid button {nm} (hooks under the ledge)", f"{v:.2f} mm^3")
    print(f"      {len(p.CHANNELS)} lock teeth; fulcrum line y {geo['y_h']:.2f}; nub at ({geo['x_n']:.1f}, {geo['py']:.1f}), "
          f"{d_n:.1f} below the fulcrum")

    print("\n10. Pressed: rock to the click, then the wings land beside the tab (the stop)")
    m = tab_model(p, c, b)
    th_c, th_s = (p.NUB_G + m["ya_click"])/d_n, geo["slope"]
    low = geo["pads"] ^ prism(rect(-60, 60, -60, geo["y_h"] - 15), -50, 50)     # ring pads well below the fulcrum
    tab_s = plate ^ prism(geo["tab"], -5, st.z_plate + 5)
    rest_plate = plate - tab_s
    wings = geo["wings"]
    rigid = kid
    k_c, k_w = rock(rigid, geo, st, th_c), rock(rigid, geo, st, th_w)
    g1, g2 = rock(wings, geo, st, th_c).min_gap(plate, 2.0), rock(low, geo, st, th_c).min_gap(case, 2.0)
    check(g1 > 0.05 and g2 > 0.05, "at the click neither the wings nor the ring pads have landed", f"wings {g1:.2f}, ring {g2:.2f} to go")
    w_s = rock(wings, geo, st, th_w)
    v, g = (w_s ^ plate).volume(), w_s.min_gap(plate, 1.0)
    check(v < 2e-2 and g < 0.02, "at the stop both wings sit on the back plate, off the tab", f"overlap {v:.4f} mm^3")
    nub_s = rock(geo["nub"], geo, st, th_w)
    probe = geo["nub"] ^ m3.Manifold.cylinder(60, 0.05, 0.05, 8).translate([geo["x_n"], geo["py"], -10])
    d = bbox(probe)[0, 2] - bbox(rock(probe, geo, st, th_w))[0, 2]
    check(abs(d - geo["d_stop"]) < 0.03, "nub travel at the stop = NUB_G + click + SPARE", f"{d:.2f}")
    v = (nub_s ^ tab_s).volume()
    check(v > 1e-3, f"at the stop the nub has pushed the tab H = {geo['H']:.2f}", f"{v:.3f} mm^3")
    for dy in (-0.7, 0.0, 0.7):
        v = (nub_s.translate([0, dy, 0]) ^ rest_plate).volume()
        check(v < 1e-4, f"nub {dy:+.1f} off in y lands on the tab only (not the plate round it)", f"{v:.4f} mm^3")
    g = rock(kid - geo["nub"] - wings, geo, st, th_w).min_gap(plate, 3.0)
    check(g > 0.15, "at the stop the disc still clears the back plate", f"{g:.2f}")
    g = rock(low, geo, st, th_w).min_gap(case, 2.0)
    check((k_w ^ case).volume() < 2e-2 and g > 0.05, "at the stop the ring pads are still clear (a backup stop)", f"{g:.2f} at 6 o'clock")
    drop = th_s*(geo["y_h"] + geo["R_OUT"])
    check(drop + 0.1 <= p.K_GAP, "ring pads stand proud of the disc all round (the disc is never the stop)", f"drop {drop:.2f} at 6 o'clock, gap {p.K_GAP}")
    k_s = rock(rigid, geo, st, th_s)
    v, g = (k_s ^ case).volume(), k_s.min_gap(case, 1.0)
    check(v < 2e-2 and g < 0.02, "rocked RING_EXTRA further the ring pads sit on the case", f"overlap {v:.4f} mm^3")
    g = min(rock(kid, geo, st, th_s).min_gap(f.solid(), 3.0) for f in feats)
    check(g > 0.5, "even then nothing on the kid button reaches the badge", f"{g:.2f}")
    swing = th_s*(st.z_back - geo["tl"]["z_tb"])           # rocking about the case back swings the tooth tips sideways
    check(swing < p.GROOVE - p.HOOK, "rocked to the ring, the tooth hooks swing less than their groove clearance",
          f"{swing:.2f} vs {p.GROOVE - p.HOOK:.2f}")

    print(f"\n11. Forces and strains: {MAT.NAME}, E {MAT.E:g} +-{100*MAT.E_TOL:g}%, flexing parts <= {100*MAT.FLEX_MAX:g}%")
    cs = tab_cases(p, c, b, geo, p.F_PRESS)
    early = min(v["early"] for v in cs.values())
    check(early >= 0.02, f"clicks at any E even if the wings land {p.TOL} early", f"{early:.2f} tab push to spare")
    R_hi = max(v["hi"]["R"] for v in cs.values())
    eps_hi = max(v["hi"]["eps"] for v in cs.values())
    nom = cs["nom"]["nom"]
    check(nom["R"] <= p.F_SW_MAX, f"switch force on the stop <= {p.F_SW_MAX:g} N, nominal", f"{nom['R']:.1f} N")
    check(R_hi <= p.F_SW_WORST, f"switch force <= {p.F_SW_WORST:g} N, worst ({p.TOL} late, any E, {p.F_PRESS:g} N mash): KNOWN WEAKNESS",
          f"{R_hi:.1f} N")
    check(nom["eps"] <= MAT.FLEX_MAX, f"tab strain on the stop <= {100*MAT.FLEX_MAX:g}%, nominal", f"{100*nom['eps']:.2f}%")
    check(eps_hi <= p.TAB_WORST, f"tab strain on the stop <= {100*p.TAB_WORST:g}%, worst (agreed)", f"{100*eps_hi:.2f}%")
    a = (geo["R_REAR"] + geo["R_OUT"] - U.BACK_CHAMFER)/2
    s_c = 3*p.F_PRESS/(2*math.pi*p.K_T**2)*((1 + p.NU)*math.log(a/p.FINGER_PAD_R) + 1)
    check(s_c/MAT.E_lo <= MAT.FLEX_MAX, f"disc strain, {p.F_PRESS:g} N on the centre", f"{100*s_c/MAT.E_lo:.2f}% ({s_c:.1f} MPa)")
    cc = geo["R_K"] - (geo["R_OUT"] - U.BACK_CHAMFER - p.PAD_W)
    s_e = 6*p.F_PRESS*cc/((2*cc + 2*p.FINGER_PAD_R)*p.K_T**2)
    check(s_e/MAT.E_lo <= MAT.FLEX_MAX, f"disc strain, {p.F_PRESS:g} N on the rim past the pads ({cc:.1f} overhang)", f"{100*s_e/MAT.E_lo:.2f}%")
    f_req = lambda y: m["P_click"]*d_n/(geo["y_h"] - y)
    y_easy = geo["y_h"] - m["P_click"]*d_n/p.F_EASY
    check(f_req(0.0) <= p.F_EASY, f"press force to click at the centre <= {p.F_EASY:g} N", f"{f_req(0):.1f} N")
    print(f"      to click: nub {m['P_click']:.1f} N; press {f_req(-geo['R_OUT']):.1f} N at 6 o'clock, {f_req(0):.1f} N at the centre, "
          f"<= {p.F_EASY:g} N anywhere below y {y_easy:+.1f}")

    print(f"\n12. Twist-lock: {len(p.CHANNELS)} teeth, {math.degrees(geo['tl']['turn']):.1f} deg turn, latch key at {p.CHANNELS[-1]:g} deg")
    tl, key, R = geo["tl"], geo["key"], geo["R_OUT"]
    spin = lambda m, a: m.rotate([0, 0, math.degrees(a)])
    free = kid - key                                        # the latch lifts the key while the button turns
    worst = max((spin(free, -tl["turn"]*k) ^ case).volume() for k in (0.25, 0.5, 0.75, 1.0))
    check(worst < 2e-2, "turning from locked to open, nothing but the key touches the case", f"{worst:.4f} mm^3")
    worst = max((spin(free, -tl["turn"]).translate([0, 0, dz]) ^ case).volume() for dz in (0.5, 1.5, 3.0, 5.0))
    check(worst < 1e-3, "turned open, the teeth lift straight out of their channels", f"{worst:.4f} mm^3")
    back, over = (0.25 + 0.3)/R, (0.2 + 0.3)/R
    v = (spin(key, -back) ^ case).volume()
    check(v > 1e-2, "locked: turning back 0.3 past the backlash, the key hits its channel wall", f"{v:.3f} mm^3")
    v = (spin(geo["teeth"], over) ^ case).volume()
    check(v > 1e-2, "locked: turning on, the teeth hit the closed ends of their grooves", f"{v:.3f} mm^3")
    e = (tl["r_fi"] + p.T_T/2) - (R - p.HOOK/2)            # hook load to tooth centre, radial
    per = MAT.INTERLAYER/(1/(p.T_W*p.T_T) + 6*e/(p.T_W*p.T_T**2))   # teeth print upright: pull is across the layers
    pull = len(p.CHANNELS)*per
    check(pull >= p.F_PULL, f"pull-off >= {p.F_PULL:g} N before any tooth reaches {MAT.INTERLAYER:g} MPa across the layers",
          f"{pull:.0f} N ({per:.0f} N a tooth)")
    F_tw = p.T_CHILD*1000/(R + p.T_T/2)
    h = (geo["kz1"] - p.LATCH_T) - (st.z_back - p.KEY_E/2)  # key root to the middle of its bite
    t_r = tl["r_fi"] + p.T_T - (R - p.HOOK)
    s_key = 6*F_tw*h/(t_r*p.T_W**2)
    check(s_key <= MAT.INTERLAYER, f"a {p.T_CHILD:g} N.m rim twist: key bending across the layers <= {MAT.INTERLAYER:g} MPa", f"{s_key:.1f} MPa")
    s_lat = 6*F_tw*p.LATCH_L/(p.LATCH_T*p.LATCH_W**2)
    check(s_lat <= MAT.STRENGTH, f"a {p.T_CHILD:g} N.m rim twist: latch bending in its plane <= {MAT.STRENGTH:g} MPa", f"{s_lat:.1f} MPa")
    lift = p.KEY_E + 0.1
    eps_l = 1.5*p.LATCH_T*lift/p.LATCH_L**2
    check(eps_l <= MAT.ONCE_MAX, f"latch lifted {lift:.1f} to release (adult, coin): strain <= {100*MAT.ONCE_MAX:g}%", f"{100*eps_l:.2f}%")
    f_fit = MAT.E_hi*p.LATCH_W*p.LATCH_T**3/(4*p.LATCH_L**3)*p.KEY_E
    check(f_fit <= p.F_PUSH_MAX, f"fitting it: the key rides the rim, latch force <= {p.F_PUSH_MAX:g} N", f"{f_fit:.1f} N")
    gap = (geo["kz1"] - p.LATCH_T) - st.z_back
    check(gap >= 1.9, "coin gap under the latch beside the key (a coin is ~1.7 thick)", f"{gap:.2f}")
    f_hook = p.F_PRESS*(geo["y_flat"] - geo["y_h"])/(geo["y_h"] + geo["R_OUT"])
    check(f_hook < pull/3, f"{p.F_PRESS:g} N on the top edge (above the fulcrum) loads the teeth far below pull-off", f"{f_hook:.1f} N")
    return dict(cs=cs, pull=pull, f_fit=f_fit, eps_l=eps_l, s_key=s_key, s_lat=s_lat, s_c=s_c, s_e=s_e)


def run_tab_checks(b, c, p, feats, plate, geo):
    print("\n7. BOOT tab: push the plastic behind the post, the glass is never touched")
    check((geo["slot"] - circle(geo["R_DISC"] - c.MIN_WALL)).area() < 1e-6, f"U-slot stays {c.MIN_WALL} inside the plate edge", "")
    moved = (plate ^ prism(geo["tab"], -2, geo["Z_CASE"] + 2)).translate([0, 0, -c.STROKE])
    for f in feats:
        v = (moved ^ f.solid()).volume()
        if f.name == f"{c.BUTTON} actuator":
            check(v > 1e-3, f"tab pushed {c.STROKE:.2f}: post reaches the {c.BUTTON} actuator", f"{v:.3f} mm^3")
        else:
            g = moved.min_gap(f.solid(), 3.0)
            check(v < 1e-3 and g > 0.05, f"tab pushed {c.STROKE:.2f}: {f.name} still clear", f"gap {g:.2f}")
    print(f"      tab {p.TAB_L:g} long, {2*p.TAB_R:g} wide at the post widening to {p.TAB_W:g}, {p.TAB_T:g} thick")


def run_pry_checks(n, c, p, case, plates, geo, lock_cut=None):
    """plates: name -> (plate, its disc radius). A blade slides in radially along the notch floor."""
    R_BORE, FLOOR, R_OUT = geo["R_BORE"], geo["FLOOR"], geo["R_OUT"]
    half = math.degrees(math.atan2(U.PRY_W/2, R_OUT))
    print(f"\n{n}. Pry notch at {p.PRY_DEG:g} deg (+-{half:.1f} at the rim), {U.PRY_W:g} wide, {U.PRY_DEPTH:g} under the plate's front face")
    if lock_cut is not None:
        g = geo["pry"].min_gap(lock_cut, 5.0)
        check(g >= c.MIN_WALL, f"notch keeps >= {c.MIN_WALL} of case to every lock cut", f"{g:.2f}")
    BLADE_T, BLADE_W = 0.5, 3.0                                    # a small flat screwdriver
    r_tip = R_BORE + 0.35
    blade = prism(rect(r_tip, R_OUT + 3, -BLADE_W/2, BLADE_W/2).rotate(p.PRY_DEG), FLOOR - 0.1 - BLADE_T, FLOOR - 0.1)
    for nm, (pl, r_disc) in plates.items():
        v = (blade ^ case).volume() + (blade ^ pl).volume()
        check(v < 1e-3, f"a {BLADE_T} blade slides in under the {nm}'s edge, touching nothing", f"{r_disc - r_tip:.2f} under it")
        v = (blade.translate([0, 0, 0.2]) ^ pl).volume()
        check(v > 1e-3, f"lifted 0.2 it bears on the {nm}", f"{v:.3f} mm^3")


def run_battery_checks(c, feats, case, plate, kid, geo, st):
    print(f"\n14. Battery {st.battery}: pocket between the back plate and the kid button")
    bt = geo["batt"]
    for nm, m in (("case", case), ("back plate", plate), ("kid button", kid), ("kid button pressed", rock(kid, geo, st, geo["slope"]))):
        v = (bt ^ m).volume()
        check(v < 1e-3, f"battery clear of the {nm}", f"{v:.3f} mm^3")


def renders(b, c, p, feats, case, plate, kid, geo, st):
    D = lambda m: m.rotate([90, 0, 0]).refine_to_length(1.0)        # badge +y up, glass toward the viewer at azim 90
    shell, back_c, kid_c, dark, white, green, violet, red = ((0.30, 0.62, 0.78), (0.20, 0.45, 0.62), (0.98, 0.72, 0.20),
        (0.10, 0.10, 0.11), (0.95, 0.95, 0.90), (0.25, 0.70, 0.35), (0.62, 0.30, 0.80), (0.85, 0.25, 0.20))
    fs = {f.name: f.solid() for f in feats if not f.name.startswith("plug")}
    colour = lambda n: dark if n == "disc + tab" else green if n.startswith(c.BUTTON) else white
    post = plate ^ geo["post_cyl"]
    plate_np = plate - geo["post_cyl"]
    plug = prism(rect(-6.0, 6.0, b.tip_y, b.tip_y + 22), b.port_z - 4, b.port_z + 4)
    asm = [(case, shell), (plate_np, back_c), (post, violet), (kid, kid_c), (fs["disc + tab"], dark), (plug, (0.35, 0.35, 0.38))]
    render([(D(m), col) for m, col in asm], OUT + "hero-front.png", elev=18, azim=62,
           title=f"Pendant, Ø{2*geo['R_OUT']:.1f} x {bbox(case)[1, 2] - bbox(case)[0, 2]:.1f} (+{p.K_GAP + p.K_T:.1f} kid button), plug at 12 o'clock")
    render([(D(m), col) for m, col in asm], OUT + "hero-back.png", elev=18, azim=-118,
           title="From the back: the kid button (orange); the U-cut near 5 o'clock is the latch (coin under its tip)")
    top = [(case, shell), (plate_np, back_c), (post, violet), (kid, kid_c)] + \
          [(s, (0.72, 0.74, 0.78) if n == "USB-C receptacle" else colour(n)) for n, s in fs.items()]
    crop = prism(rect(-14, 14, geo["y_flat"] - 6, 40), -10, 30)      # the top only, or the protrusion is too small to read
    render([(D(m ^ crop), col) for m, col in top], OUT + "port-top.png", elev=25, azim=50,
           title=f"12 o'clock: USB-C stands {b.tip_y - geo['y_flat']:.2f} past the flat, "
                 f"{p.PORT_OUT} with the board pushed down: any overmold seats")
    open_ = kid.rotate([0, 0, -math.degrees(geo["tl"]["turn"])]).translate([0, 0, 5])
    render([(D(case), shell), (D(open_), kid_c)], OUT + "twist-lock.png", elev=-8, azim=-150,
           title=f"Twist-lock, opened: teeth over their entry channels; drop in, turn {math.degrees(geo['tl']['turn']):.0f} deg to lock")
    E = 24.0
    ex = [(case, shell), (plate_np.translate([0, 0, 2*E]), back_c), (post.translate([0, 0, 2*E]), violet),
          (kid.translate([0, 0, 3.2*E]), kid_c)] + [(s.translate([0, 0, E]), colour(n)) for n, s in fs.items()]
    render([(D(m), col) for m, col in ex], OUT + "exploded.png", elev=14, azim=-32,
           title="Exploded from the back: case, badge, back plate (long BOOT tab), kid button")
    render([(D(kid - geo["nub"] - geo["wings"]), kid_c), (D(geo["nub"]), green), (D(geo["wings"]), red)],
           OUT + "kid-underside.png", elev=28, azim=70,
           title="Kid button underside: nub (green) and stop wings (red) over the tab, ring pads, 4 lock teeth + the latch key")
    render([(D(plate_np), back_c), (D(post), violet)], OUT + "plate-back.png", elev=-30, azim=-90,
           title=f"Back plate from the back: the {p.TAB_L:g} mm BOOT tab inside its U-slot")

    # section through the tab, nub and post (plane y = BOOT y), looking along +y: x right, back (z) up
    y0 = geo["py"]
    box = m3.Manifold.cube([24, 40, 13]).translate([-14, y0, 3.5])
    tab_s = plate ^ prism(geo["tab"], -5, st.z_plate + 5)
    root = geo["px"] + p.TAB_L
    phi = -math.degrees(c.STROKE/p.TAB_L)                          # post end toward the badge
    act = next(f for f in feats if f.name == f"{c.BUTTON} actuator").solid()
    def section(pressed, path, title):
        tab_m = tab_s.translate([-root, 0, -st.z_plate]).rotate([0, phi, 0]).translate([root, 0, st.z_plate]) if pressed else tab_s
        r = (lambda m: rock(m, geo, st, geo["th_w"])) if pressed else (lambda m: m)
        a = act.trim_by_plane([0, 0, -1], -(b.pcb_back_z + b.sw_cap_h - c.SW_TRAVEL)) if pressed else act
        parts = [(case, shell), (plate - tab_s, back_c), (tab_m, violet), (r(kid - geo["nub"] - geo["wings"]), kid_c),
                 (r(geo["nub"]), green), (r(geo["wings"]), red), (a, green)] + \
                [(s, colour(n)) for n, s in fs.items() if not n.endswith("actuator")]
        cut = []
        for m, col in parts:
            m = (m.trim_by_plane([0, 1, 0], y0) ^ box).refine_to_length(0.6)
            if not m.is_empty(): cut.append((m, col))
        render(cut, path, elev=0, azim=-90, title=title, figsize=(10, 10), zoom=1.15)
    section(False, OUT + "section-boot-rest.png",
            f"Section through BOOT (y {y0:+.1f}), at rest: nub (green) {p.NUB_G} over the tab, wings (red) {geo['H'] + p.NUB_G:.2f} over the plate")
    section(True, OUT + "section-boot-pressed.png",
            f"Pressed to the stop: wings on the plate, nub {geo['H']:.2f} into the tab, post on BOOT (tab drawn rigid)")

    # print layout: each part as exported, side by side on the bed
    lay = [(case.translate([0, 0, c.LIP_T]), shell, -55),
           (plate.rotate([0, 180, 0]).translate([0, 0, st.z_plate]), back_c, 0),
           (kid.rotate([0, 180, 0]).translate([0, 0, geo["kz1"]]), kid_c, 55)]
    render([(m.translate([dx, 0, 0]).refine_to_length(1.5), col) for m, col, dx in lay], OUT + "print-layout.png",
           elev=32, azim=-70, title="Print as exported, no supports: case bezel down, back plate and kid button face down",
           figsize=(12, 9), zoom=1.9)


# ---- main ------------------------------------------------------------------
def main():
    b, c, p = Badge(), Case(), Pendant()
    battery = None
    if "--battery" in sys.argv:
        battery = tuple(float(v) for v in sys.argv[sys.argv.index("--battery") + 1].split(","))
    feats, case, plate, kid, geo, st = build(b, c, p, battery)
    asm = bbox(case + plate + kid)
    mass = {k: m.volume()*MAT.RHO for k, m in (("case", case), ("back plate", plate), ("kid button", kid))}
    print(f"Pendant Ø{2*geo['R_OUT']:.2f}; case {bbox(case)[1, 2] - bbox(case)[0, 2]:.2f} thick, {asm[1, 2] - asm[0, 2]:.2f} with the kid button; "
          f"flat at y {geo['y_flat']:.2f}, USB-C sticks out {b.tip_y - geo['y_flat']:.2f} ({p.PORT_OUT} pushed down); " + ", ".join(f"{k} {g:.1f} g" for k, g in mass.items()) + " (solid)")
    U.run_checks(b, c, feats, case, plate, geo)
    run_tab_checks(b, c, p, feats, plate, geo)
    run_pendant_checks(b, c, p, feats, case, plate, kid, geo, st)
    _, _, plate_r, geo_r = button_plate(b, c, p, U.PLATE_DISC_CLR_ROOMY)
    run_pry_checks(13, c, p, case, {"back plate": (plate, geo["R_DISC"]), "roomy back plate": (plate_r, geo_r["R_DISC"])},
                   geo, geo["lock_cut"])
    if battery:
        run_battery_checks(c, feats, case, plate, kid, geo, st)
    else:
        print()
        export(case, STL + "Pendant - case.stl", lambda m: m.translate([0, 0, c.LIP_T]))
        flip = lambda z: (lambda m: m.rotate([0, 180, 0]).translate([0, 0, z]))
        export(plate, STL + "Pendant - back plate (button).stl", flip(st.z_plate))
        export(plate_r, STL + "Pendant - back plate (button, roomy).stl", flip(st.z_plate))
        export(kid, STL + "Pendant - kid button.stl", flip(geo["kz1"]))
        if "--no-render" not in sys.argv:
            renders(b, c, p, feats, case, plate, kid, geo, st)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
