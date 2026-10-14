#!/usr/bin/env python3
"""
Hoop stand, telegraph key: the badge leans further back (40 deg from vertical, or 50; the hoop leans 20) and
BOOT is a telegraph key on the base. Press the brass knob at the front: the lever turns on a pin between two
posts, its short rear arm tips up into the back plate's flush BOOT tab, and the switch clicks.

  lever  NEW. One print, on its side: a profile in world (Y, Z), extruded along X from X0 (the bed face),
         beside the neck under BOOT's side of the case. Knob arm 2x the nub arm. Parts of it:
           hub     on a pin between two posts; the rear arm rises from it to the nub, 2 mm behind the plate
           front   a tapered blade out to the knob pad: it is the overtravel spring. Once the switch has
                   bottomed, more press only bends the blade; the anvil under the pad then stops the lever,
                   so a hard press goes into the base, never the switch or the glass
           hairpin a spring under the hub, its foot on the base just forward of the pin: it holds the knob up
           heel    behind the pin, it rests on the back stop: that sets the nub's gap at rest
  knob   NEW. A brass mushroom, printed upright, snapped onto a split peg on the pad.
  pin    NEW. Ø3.5, printed lying on its flat. Head outside; a split, barbed end snaps past the inner post.
  base   NEW. Ø76 like today, under the centre of mass; a low plinth round the mortise; the two posts, the
         anvil and the back stop; the cable keyhole at the back.
  hoop + case   build_hoop.py's, regenerated at the new lean (the tenon and barbs follow the angle).
  back plate    the existing button plate, unchanged.

Material PLA: E 2500 MPa, <= 1.0% strain for anything that flexes on every press, <= 1.5% for snap-once,
10 MPa across the layers. World frame as build_hoop.py: z up, viewer at -Y, BOOT at world X = +11.1.
Run from the repo root: ~/.venvs/cad/bin/python pocketwatch/stands/hoop/build_hoop_telegraph.py [--no-render]
"""
import sys, math, os, tempfile
from dataclasses import dataclass, replace
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pocketwatch/stands/hoop")
import numpy as np, manifold3d as m3
from build_pocketwatch import Badge, Case, Round, circle, rect, prism, union, chamfered, bbox, check, FAILS, export, render
import build_pocketwatch_usb as U
import build_hoop as H
import build_hoop_frontboot as FB

STL = H.STL + "Hoop stand telegraph - "
OUT = H.OUT + "telegraph-"
REST, STROKE = Case().REST_CLR, Case().STROKE
E, RHO, MPA, MPA_Z = 2500.0, 1.24e-3, 45.0, 10.0      # PLA: modulus, g/mm^3, strength along / across the layers
FLEX, SNAP = 0.010, 0.015                              # strain limits: flexes every press / snaps once
xprism, poly, band, yzrect, rot3 = FB.xprism, FB.poly, FB.band, FB.yzrect, FB.rot3


@dataclass(frozen=True)
class Key:
    TILT: float = 40.0        # face leans back this far from vertical (the hoop: 20)
    TIER_T: float = 10.0      # plinth top; the mortise is MORT_D deep, 1.5 of floor under it
    MORT_D: float = 8.5       # >= (TANG_L + 0.5) cos(TILT): the snap slots must end inside the mortise
    PLINTH_WALL: float = 1.3
    PLINTH_CH: float = 0.5
    BASE_R: float = 38.0      # today's Ø76
    BASE_T: float = 5.0
    # lever
    X0: float = 10.3          # bed face (the side toward the neck); the lever runs X0..X0+W
    W: float = 9.0
    NUB_W: float = 2.3        # nub X0..X0+NUB_W: on the tab, whose round end is at X 13.3
    G: float = 0.5            # nub tip to the flush tab at rest
    G_TOL: float = 0.3
    R_NUB: float = 2.2
    NUB_P: float = 2.0        # nub stands this proud of the rear arm
    W_R: float = 4.5          # rear arm, in-plane: stiff
    BETA: float = 15.0        # rear arm this much steeper than the plate: the pin sits behind the plate's plane,
                              # clear of the case rim. The nub then pushes 15 deg off square; it slides on the tab
                              # only until the switch bottoms (0.1 mm)
    RATIO: float = 2.0        # knob travel / nub travel
    R_HUB: float = 3.0
    PIN_D: float = 3.0
    PIN_FLAT: float = 0.25    # the pin prints on a flat this deep
    PIN_CLR: float = 0.15     # per side, in the lever's bore
    HOLE_CLR: float = 0.10    # per side, in the posts
    POST_T: float = 3.0
    POST_HY: float = 3.3      # post half-depth (Y); round top of this radius round the pin
    CLR_X: float = 0.4        # lever to each post
    PIN_HEAD_R: float = 2.8
    PIN_HEAD_T: float = 1.2
    PIN_SLOT: float = 0.9
    PIN_SLOT_L: float = 8.0
    PIN_BARB: float = 0.35
    T0: float = 2.0           # front blade depth at the hub, tapering (constant strain) to T_TIP = 0.6 T0 at the pad;
                              # build() sets T0 for the stiffness the gap tolerance needs
    T_TIP: float = 1.2
    F_N_DESIGN: float = 7.6   # what the blade is sized for at the smallest gap (the limit is F_N_MAX)
    T_PAD: float = 2.6        # the pad under the knob, on the anvil at the stop
    PAD_HL: float = 3.6
    ARM_CLR: float = 0.6      # blade under the hoop at rest
    FIL: float = 0.5
    HEEL_L: float = 7.5
    HEEL_T: float = 2.5
    # hairpin return spring
    HP_W: float = 6.0
    T_HP: float = 1.6
    HP_GAP: float = 1.0
    HP_L: float = 10.0
    HP_DW: float = 2.0
    X_T: float = 2.0          # foot this far forward of the pin: the spring's lever arm
    HP_PRE: float = 0.5       # preload at rest
    FOOT_R: float = 1.0
    FOOT_H: float = 0.8
    HP_ARM_CLR: float = 1.6   # upper leg under the blade: 0.4 + the blade's sag + the leg's own lift
    PHI_EST: float = 0.20     # rad, at least the swing to the stop: sets how far the lower leg climbs to the bend
    # knob
    PEG_W: float = 7.0        # split peg X0..X0+PEG_W; the knob is centred on it, clear of the neck's root
    PEG_T: float = 1.3
    PEG_SLOT: float = 1.2
    PEG_BARB: float = 0.4
    PEG_ENG: float = 8.2      # socket depth: the knob sits on the peg tops
    SOCK_CLR: float = 0.15
    KNOB_RB: float = 5.6
    KNOB_RS: float = 5.8      # foot ring
    KNOB_H: float = 9.0
    R_ANV: float = 3.0
    FINGER_R: float = 8.0
    FINGER_CLR: float = 0.8
    SPARE: float = 0.4        # knob travel left after the click at the largest gap
    # loads
    F_SW: float = 2.0         # tact switch actuation force (a guess)
    F_N_MAX: float = 8.0      # most the nub may push on the tab (switch and glass) at the stop
    PRESS: float = 30.0       # a hard press on the knob
    PRESS_STAB: float = 6.0
    MU: float = 0.3
    CLR: float = 0.4


CANDIDATES = (Key(), Key(TILT=50.0, TIER_T=9.5, MORT_D=8.0))
tag = lambda k: f"{k.TILT:.0f} deg"


# ---- the hoop at a new lean ------------------------------------------------------
def hoop_at(k):
    s = replace(H.Stand(), TILT=k.TILT, TIER_T=k.TIER_T, MORT_D=k.MORT_D, BASE_R=k.BASE_R, BASE_T=k.BASE_T, PETG_E=E)
    b, c = Badge(), Case()
    _, _, _, geo = H.build(b, c)
    _, R_HO, _ = H.ring_radii(s, geo)
    Z0 = -c.LIP_T
    F = H.Frame(s.TILT, s.TIER_T + s.NECK_H + math.cos(math.radians(s.TILT))*R_HO + math.sin(math.radians(s.TILT))*(Z0 + s.HD))
    zm = Z0 + s.HD/2
    geo["y_t"] = (s.TIER_T - F.H0 + F.S*zm)/F.C
    geo["Yb"] = 0.0
    extra, _, info, screw, ki = H.stand_solids(s, c, geo, F, "hoop")
    feats, case, _, geo2 = H.build(b, c, extra)
    geo.update(geo2)
    return s, b, c, F, feats, case, geo, ki, info, screw, extra


def plinth_outline(k, s, ki):
    mort = ki["mort"] ^ m3.Manifold.cube([300, 300, s.TIER_T]).translate([-150, -150, 0])
    return mort.project().offset(k.PLINTH_WALL + k.PLINTH_CH, Round).simplify(0.01)


# ---- the lever -------------------------------------------------------------------
def thick_path(pts, w):
    out = circle(w/2).translate(list(pts[0]))
    for p, q in zip(pts[:-1], pts[1:]):
        out = out + band(p, q, w) + circle(w/2).translate(list(q))
    return out


def lever_geometry(k, s, b, c, F, geo, hoopW, plinth_cs, z_kb, d_stop=None):
    S, C = F.S, F.C
    n, u = np.array([-C, S]), np.array([S, C])               # into the plate; up the plate
    D = F.pt([geo["sw"][c.BUTTON], b.sw_y, geo["Z_CASE"]])[1:]   # tab back face over the post
    Tip = D - n*k.G
    Nc = Tip - n*k.R_NUB
    al = math.atan2(u[1], u[0]) + math.radians(k.BETA)
    e = np.array([math.cos(al), math.sin(al)])               # pin -> nub tip
    cb = math.cos(math.radians(k.BETA))
    Xk = k.X0 + k.PEG_W/2
    # the knob: a Ø16 fingertip comes straight down onto it in front of the hoop
    front = lambda r, z: bbox(hoopW ^ m3.Manifold.cube([2*r, 300, 200]).translate([Xk - r, -150, z]))[0, 1] - r
    K_Y = min(front(k.FINGER_R, z_kb + k.KNOB_H + 0.5) - k.FINGER_CLR, front(k.KNOB_RS + k.CLR, z_kb) - 0.3)
    for _ in range(4):        # steepen the rear arm if the hub would reach the case rim
        h = (Tip[0] - K_Y)/(e[0] + k.RATIO*cb)                # so the knob arm is RATIO x the nub arm
        beta = max(k.BETA, math.degrees(math.asin(min(1.0, (k.R_HUB + k.CLR + 0.2)/h))))
        al = math.atan2(u[1], u[0]) + math.radians(beta)
        e, cb = np.array([math.cos(al), math.sin(al)]), math.cos(math.radians(beta))
    P = Tip - h*e
    a = P[0] - K_Y
    # the blade: as high as the hoop allows, never above the hub
    box = m3.Manifold.cube([k.W + 1.0, P[0] - k.R_HUB - (K_Y - 12), 200]).translate([k.X0 - 0.5, K_Y - 12, s.TIER_T + 0.5])
    z_low = bbox(hoopW ^ box)[0, 2]
    Z_AT = min(z_low - k.ARM_CLR, P[1] + k.R_HUB - 0.5)
    zc = Z_AT - k.T0/2
    Y_root = P[0] - math.sqrt(max(k.R_HUB**2 - (zc - P[1])**2, 0.0)) - k.FIL
    Yp = K_Y + k.PAD_HL
    t = lambda y: np.maximum(k.T_TIP, k.T0*np.sqrt(np.clip((y - K_Y)/(Y_root - K_Y), 0, 1)))
    ys = np.linspace(Yp - 0.3, Y_root, 40)
    blade = poly([(P[0], Z_AT), (Yp - 0.3, Z_AT)] + [(y, Z_AT - float(t(y))) for y in ys] + [(P[0], Z_AT - k.T0)])
    pad = yzrect(K_Y - k.PAD_HL, K_Y + k.PAD_HL, Z_AT - k.T_PAD, Z_AT).offset(-0.6, Round).offset(0.6, Round)
    A = Nc + n*(k.R_NUB - k.NUB_P - k.W_R/2)                  # a point on the rear arm's centre line
    dr = (A - P)/np.linalg.norm(A - P)
    A_end = A + dr*(k.R_NUB + 0.5)
    rear = band(P, A_end, k.W_R) + circle(k.W_R/2).translate(list(A_end))
    heel = yzrect(P[0], P[0] + k.HEEL_L, P[1] - k.R_HUB, P[1] - k.R_HUB + k.HEEL_T).offset(-0.8, Round).offset(0.8, Round)
    hub = circle(k.R_HUB).translate(list(P))
    body = (hub + rear + heel + blade + pad).offset(k.FIL, Round).offset(-k.FIL, Round).simplify(0.005)
    nub = circle(k.R_NUB).translate(list(Nc)) + band(Nc, A, 2*k.R_NUB)
    # hairpin: a drop just in front of the hub, the upper leg forward, a U, the lower leg back to a foot
    Y_hr = Y_root - 1.0 - k.HP_DW/2
    Y_b = Y_hr - k.HP_L
    Y_ft = P[0] - k.X_T
    rise = k.PHI_EST*(P[0] - Y_b) + 0.6                       # the bend sinks about this far at the stop
    l1 = Z_AT - float(t(Y_b)) - k.HP_ARM_CLR - k.T_HP/2
    l2b = l1 - k.T_HP - k.HP_GAP
    floor = min(k.BASE_T, l2b - k.T_HP/2 - rise)              # below BASE_T: a pocket in the base
    l2f = floor - k.HP_PRE + k.FOOT_H + k.T_HP/2
    rb = (l1 - l2b)/2
    arc = [(Y_b - rb*math.sin(th), (l1 + l2b)/2 + rb*math.cos(th)) for th in np.linspace(0, math.pi, 9)]
    path = [(Y_hr, l1)] + arc + [(Y_ft, l2f)]
    hp = thick_path(path, k.T_HP) + band((Y_hr, Z_AT - k.T0/2), (Y_hr, l1), k.HP_DW) + \
        circle(k.FOOT_R).translate([Y_ft, floor - k.HP_PRE + k.FOOT_R])
    # the knob's peg; LIFT keeps the knob's skirt 0.4 over the plinth at the stop where they overlap in plan
    lift = 0.3
    if d_stop is not None and (circle(k.KNOB_RS).translate([Xk, K_Y]) ^ plinth_cs).area() > 0:
        lift = max(lift, s.TIER_T + 0.5 + d_stop*(a + k.KNOB_RS)/a - Z_AT)     # its front edge drops the most
    peg_top = Z_AT + lift + k.PEG_ENG
    zbf = peg_top - 2.2                                       # barb back face
    o = k.PEG_SLOT/2 + k.PEG_T
    peg = yzrect(K_Y - o, K_Y - k.PEG_SLOT/2, Z_AT - 0.3, peg_top) + yzrect(K_Y + k.PEG_SLOT/2, K_Y + o, Z_AT - 0.3, peg_top)
    for sg in (-1, 1):
        peg = peg + poly([(K_Y + sg*o, zbf), (K_Y + sg*(o + k.PEG_BARB), zbf), (K_Y + sg*(o + k.PEG_BARB), zbf + 0.4),
                          (K_Y + sg*o, peg_top - 0.3)])
    return dict(n=n, u=u, D=D, Tip=Tip, Nc=Nc, e=e, cb=cb, beta=beta, P=P, h=h, a=a, K_Y=K_Y, Xk=Xk, Z_AT=Z_AT, Y_root=Y_root, Yp=Yp,
                t=t, A=A, body=body, nub=nub, hp=hp, path=path, Y_hr=Y_hr, Y_b=Y_b, Y_ft=Y_ft, floor=floor, l1=l1, l2b=l2b,
                rise=rise, peg=peg, lift=lift, peg_top=peg_top, zbf=zbf, Z_kb=Z_AT + lift, pad_bot=Z_AT - k.T_PAD,
                heel_bot=P[1] - k.R_HUB, z_low=z_low)


def lever_solid(k, g, hairpin=True):
    m = xprism(g["body"], k.X0, k.X0 + k.W) + xprism(g["nub"], k.X0, k.X0 + k.NUB_W) + xprism(g["peg"], k.X0, k.X0 + k.PEG_W)
    if hairpin:
        m += xprism(g["hp"], k.X0, k.X0 + k.HP_W)
    return m - xprism(circle(k.PIN_D/2 + k.PIN_CLR).translate(list(g["P"])), k.X0 - 1, k.X0 + k.W + 1)


def knob_solid(k, g):
    H_, RB, RS = k.KNOB_H, k.KNOB_RB, k.KNOB_RS
    prof = [(0, 0), (RS - 0.4, 0), (RS, 0.4), (RS, 1.3), (RB, 2.1), (RB, H_ - 3.0)]
    prof += [(RB*math.cos(th), H_ - 3.0 + 3.0*math.sin(th)) for th in np.linspace(0, math.pi/2, 10)[1:]]
    knob = m3.Manifold.revolve(m3.CrossSection([prof]), 96)
    o = k.PEG_SLOT/2 + k.PEG_T + k.SOCK_CLR
    xw = k.PEG_W/2 + k.SOCK_CLR
    sock = m3.Manifold.cube([2*xw, 2*o, k.PEG_ENG + 1]).translate([-xw, -o, -1])
    ow = o + k.PEG_BARB
    z_ledge = k.PEG_ENG - 2.2 - 0.15                          # the barbs' back faces catch under this ledge
    sock += m3.Manifold.cube([2*xw, 2*ow, k.PEG_ENG - z_ledge]).translate([-xw, -ow, z_ledge])
    return (knob - sock).translate([g["Xk"], g["K_Y"], g["Z_kb"]])


def pin_solid(k, P):
    R = k.PIN_D/2
    xa = k.X0 - k.CLR_X - k.POST_T - 0.1                      # barbs' back faces, just past the inner post
    xb = k.X0 + k.W + k.CLR_X + k.POST_T + 0.1                # head, just past the outer post
    above = rect(-200, 200, P[1] - R + k.PIN_FLAT, 200)
    tip = xa - 1.8
    pin = xprism(circle(R).translate(list(P)) ^ above, tip, xb) + \
        xprism(circle(k.PIN_HEAD_R).translate(list(P)) ^ above, xb, xb + k.PIN_HEAD_T)
    for sg in (-1, 1):
        q = [(tip, P[0] + sg*(R - 0.3)), (xa - 0.4, P[0] + sg*(R + k.PIN_BARB)), (xa, P[0] + sg*(R + k.PIN_BARB)),
             (xa, P[0] + sg*(R - 0.3))]
        pin += prism(poly(q), P[1] - 0.9, P[1] + 0.9)
    pin -= xprism(yzrect(P[0] - k.PIN_SLOT/2, P[0] + k.PIN_SLOT/2, P[1] - 5, P[1] + 5), tip - 1, tip + k.PIN_SLOT_L)
    return pin, xa, xb, tip


# ---- the base --------------------------------------------------------------------
def post_holes(k, P):
    r = k.PIN_D/2 + k.HOLE_CLR
    q = 0.7071*r
    roof = poly([(P[0] - q, P[1]), (P[0] - q, P[1] + q), (P[0] - 0.45, P[1] + 1.4142*r - 0.45),
                 (P[0] + 0.45, P[1] + 1.4142*r - 0.45), (P[0] + q, P[1] + q), (P[0] + q, P[1])])
    return circle(r).translate(list(P)) + roof          # teardrop with a 0.9 flat top: prints without support


def post_xs(k):
    return ((k.X0 - k.CLR_X - k.POST_T, k.X0 - k.CLR_X), (k.X0 + k.W + k.CLR_X, k.X0 + k.W + k.CLR_X + k.POST_T))


def make_base(k, s, c, F, geo, g, ki, plinth_cs, BASE_Y, d_stop):
    P = g["P"]
    base = chamfered([circle(k.BASE_R).translate([0, BASE_Y])], 0, k.BASE_T, 0.6, 1.5)
    base += H.slab(plinth_cs, k.BASE_T - 2.0, s.TIER_T, k.PLINTH_CH)
    post = yzrect(P[0] - k.POST_HY, P[0] + k.POST_HY, k.BASE_T - 0.5, P[1]) + circle(k.POST_HY).translate(list(P))
    n, D = g["n"], g["D"]
    far = D - n*(k.CLR + 0.4) + np.array([n[1], -n[0]])*60, D - n*(k.CLR + 0.4) - np.array([n[1], -n[0]])*60
    post = (post ^ poly([far[0], far[1], far[1] - n*80, far[0] - n*80])).simplify(0.05)   # no slivers where it cuts the round
    posts = union(xprism(post, x0, x1) for x0, x1 in post_xs(k))
    phi = d_stop/g["a"]
    y0 = P[0] + (g["K_Y"] - P[0] + (g["pad_bot"] - P[1])*math.sin(phi))/math.cos(phi)
    anvil_top = P[1] + (y0 - P[0])*math.sin(phi) + (g["pad_bot"] - P[1])*math.cos(phi)   # pad underside over the crest
    rr = k.R_ANV/2
    anvil = xprism(yzrect(g["K_Y"] - rr, g["K_Y"] + rr, k.BASE_T - 0.5, anvil_top - rr) + circle(rr).translate([g["K_Y"], anvil_top - rr]),
                   g["Xk"] - k.PEG_W/2, g["Xk"] + k.PEG_W/2)
    bs = xprism(yzrect(P[0] + k.HEEL_L - 3.2, P[0] + k.HEEL_L - 0.6, k.BASE_T - 0.5, g["heel_bot"]), k.X0 + 0.5, k.X0 + k.W - 0.5)
    base += posts + anvil + bs
    base -= ki["mort"]
    # build_hoop.py runs the mortise straight up 4 mm past the tier top (enough at 20 deg); at a steeper lean the
    # tier top meets the back of the neck further up, so carry the straight sides on
    Z0 = -c.LIP_T
    w = s.FIT - 0.03                                          # just inside the mortise: no coincident faces
    mouth = prism(rect(-s.NECK_BOT/2 - w, s.NECK_BOT/2 + w, geo["y_t"], geo["y_t"] + 12), Z0 - w, Z0 + s.HD + w)
    base -= F.W(mouth).trim_by_plane([0, 0, 1], s.TIER_T - 3.0)
    zk = k.BASE_T - 0.4 - H.Stand().KEY_D/2
    yk0 = BASE_Y + k.BASE_R - 18.0
    st = H.Stand()
    key = H.orient_keyhole(H.disc(st.KEY_D/2, 0, zk, 48) + rect(-st.KEY_MOUTH/2, st.KEY_MOUTH/2, zk, s.TIER_T + 1), yk0, BASE_Y + k.BASE_R + 5)
    key += H.orient_keyhole(H.disc(st.KEY_D/2, 0, zk, 48) + rect(-st.KEY_D/2, st.KEY_D/2, zk, s.TIER_T + 1), yk0 - 2.0, yk0 + st.KEY_ENTRY)
    base -= key
    holes = xprism(post_holes(k, P), k.X0 - k.CLR_X - k.POST_T - 1, k.X0 + k.W + k.CLR_X + k.POST_T + 1)
    base -= holes
    pocket = None
    if g["floor"] < k.BASE_T - 0.01:
        pocket = xprism(yzrect(g["Y_b"] - 2.5, g["Y_ft"] + 1.6, g["floor"], k.BASE_T + 1), k.X0 - k.CLR, k.X0 + k.HP_W + k.CLR)
        base -= pocket
    return base, dict(zk=zk, yk0=yk0, key=key, mort=ki["mort"], anvil=anvil, bs=bs, posts=posts, anvil_top=anvil_top, pocket=pocket)


# ---- springs and the press --------------------------------------------------------
def springs(k, g):
    ys = np.linspace(g["Yp"], g["Y_root"], 400)
    dy = ys[1] - ys[0]
    x = ys - g["K_Y"]
    I = k.W*g["t"](ys)**3/12
    c_f = float(np.sum(x*x/(E*I))*dy)                          # knob deflection per N on the knob
    eps_f = lambda Fk: float(np.max(Fk*x*(g["t"](ys)/2)/(E*I)))
    def sag(Fk, y_at):                                         # blade deflection at y_at (root at Y_root)
        m = ys >= y_at
        return float(np.sum(Fk*x[m]*(ys[m] - y_at)/(E*I[m]))*dy)
    Lr = float(np.linalg.norm(g["A"] - g["P"])) - k.R_HUB
    c_r = Lr**3/(3*E*k.W*k.W_R**3/12)
    k_tab = 3*E*(2*U.TAB_R*U.TAB_T**3/12)/U.TAB_L**3
    c_hoop = 0.038/3.0*2000.0/E                                 # build_hoop.py: 38 um at 3 N with E 2000
    # hairpin: integrate M = F x along its centre line, x = horizontal distance from the foot
    EI1, EId = E*k.HP_W*k.T_HP**3/12, E*k.HP_W*k.HP_DW**3/12
    segs = [((g["Y_hr"], g["Z_AT"] - k.T0/2), g["path"][0], EId)] + [(p, q, EI1) for p, q in zip(g["path"][:-1], g["path"][1:])]
    c_hp = xmax = lift_b = 0.0
    for i, (p, q, EI) in enumerate(segs):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        for tt in (np.arange(40) + 0.5)/40:
            y = p[0] + (q[0] - p[0])*tt
            xx = abs(y - g["Y_ft"])
            c_hp += xx*xx*L/40/EI
            xmax = max(xmax, xx)
            if i <= 1:                                         # drop and upper leg: they carry the bend
                lift_b += xx*(y - g["Y_b"])*L/40/EI
    return dict(c_f=c_f, eps_f=eps_f, sag=sag, Lr=Lr, c_r=c_r, k_tab=k_tab, c_hoop=c_hoop, k_hp=1/c_hp, hp_xmax=xmax,
                EI1=EI1, lift_b=lift_b, F_b=k_tab*STROKE + k.F_SW)


CLICK = 11 + 45            # row index of the click in press()


def press(k, g, sp, G):
    """Rows: knob drop, knob force, nub force, lever turn (rad), hairpin force, tab travel."""
    hcb, a = g["h"]*g["cb"], g["a"]
    def row(phi, Fn, x):
        Fr = sp["k_hp"]*(k.HP_PRE + k.X_T*phi)
        Fk = (hcb*Fn + k.X_T*Fr)/a
        return (a*phi + sp["c_f"]*Fk, Fk, Fn, phi, Fr, x)
    rows = [row(p, 0.0, 0.0) for p in np.linspace(0, G/hcb, 12)]
    adv = lambda x, Fn: (G + x + Fn*(sp["c_r"] + sp["c_hoop"]))/hcb
    for x in np.linspace(0, STROKE, 46)[1:]:
        Fn = sp["k_tab"]*x + (k.F_SW if x >= REST - 1e-9 else 0.0)
        rows.append(row(adv(x, Fn), Fn, x))
    for extra in np.linspace(0, 16, 161)[1:]:
        Fn = sp["F_b"] + extra
        rows.append(row(adv(STROKE, Fn), Fn, STROKE))
    return np.array(rows)


# ---- build one candidate --------------------------------------------------------
def build(k, plate_b, geo_b, verbose):
    s, b, c, F, feats, case, geo, ki, info, screw, extra = hoop_at(k)
    hoopW, plateW = F.W(case), F.W(plate_b)
    pl = plinth_outline(k, s, ki)
    z_kb, d_stop = s.TIER_T + s.NECK_H, None
    for _ in range(5):     # the knob's height sets where it clears the hoop, which sets the lever, which sets the knob
        g = lever_geometry(k, s, b, c, F, geo, hoopW, pl, z_kb, d_stop)
        # blade stiffness: the gap tolerance (x RATIO at the knob) plus SPARE must fit between the click force and
        # F_N_DESIGN on the nub. The profile scales, so compliance goes as 1/T0^3
        sp = springs(k, g)
        Rt = k.RATIO
        C_need = (2*Rt*k.G_TOL + k.SPARE)/(k.F_N_DESIGN - sp["F_b"])
        cf_need = Rt*(C_need - Rt*(sp["c_r"] + sp["c_hoop"]))
        T0 = k.T0*(sp["c_f"]/cf_need)**(1/3)
        k = replace(k, T0=round(T0, 3), T_TIP=round(max(1.0, 0.6*T0), 3))
        g = lever_geometry(k, s, b, c, F, geo, hoopW, pl, z_kb, d_stop)
        d_stop = press(k, g, springs(k, g), k.G + k.G_TOL)[CLICK, 0] + k.SPARE
        z_kb = g["Z_kb"]
    g = lever_geometry(k, s, b, c, F, geo, hoopW, pl, z_kb, d_stop)
    sp = springs(k, g)
    lever, lever_rigid = lever_solid(k, g), lever_solid(k, g, hairpin=False)
    knob = knob_solid(k, g)
    pin, xa, xb, tip = pin_solid(k, g["P"])
    body, shell, boot, _, _ = H.cable_and_plug(s, b, F, dict(geo, Yb=0.0), dict(zk=2.5, yk0=0.0))
    # base centre: the plug inside the footprint if it can be, else the stand alone
    vs = lambda m: np.asarray(m.to_mesh().vert_properties)[:, :2]
    rig_v = np.vstack([vs(hoopW), vs(lever), vs(knob), vs(pin), vs(prism(pl, 0, 1))])
    plug_v = vs(body)
    def best(V):
        ys = np.arange(-30, 20, 0.1)
        r = [np.max(np.hypot(V[:, 0], V[:, 1] - y)) for y in ys]
        return ys[int(np.argmin(r))], min(r)
    BASE_Y, r_all = best(np.vstack([rig_v, plug_v]))
    if r_all > k.BASE_R - 0.3:
        BASE_Y, _ = best(rig_v)
    base, bi = make_base(k, s, c, F, geo, g, ki, pl, BASE_Y, d_stop)
    body, shell, boot, cable, cable_exit = H.cable_and_plug(s, b, F, dict(geo, Yb=BASE_Y), bi)
    R = dict(k=k, s=s, b=b, c=c, F=F, feats=feats, case=case, geo=geo, ki=ki, info=info, screw=screw, extra=extra,
             hoopW=hoopW, plateW=plateW, pl=pl, g=g, sp=sp, d_stop=d_stop, lever=lever, lever_rigid=lever_rigid, knob=knob,
             pin=pin, pin_x=(xa, xb, tip), base=base, bi=bi, BASE_Y=BASE_Y, plug=(body, shell, boot), cable=cable,
             cable_exit=cable_exit, plate_b=plate_b, geo_b=geo_b)
    print(f"\n==================== {tag(k)}: glass centre {F.H0:.1f} above the desk; pin at Y {g['P'][0]:+.1f} Z {g['P'][1]:.1f}; "
          f"nub arm {g['h']:.1f}, knob arm {g['a']:.1f}; base centre Y {BASE_Y:+.1f}")
    joint_checks(R)
    path_checks(R)
    lever_checks(R)
    force_checks(R)
    assembly_checks(R)
    size_checks(R)
    stability(R)
    return R


# ---- checks ---------------------------------------------------------------------
def joint_checks(R):
    k, s, c, F, ki, screw, geo = R["k"], R["s"], R["c"], R["F"], R["ki"], R["screw"], R["geo"]
    base, hw = R["base"], R["hoopW"]
    print(f"\n12. Joint ({tag(k)}): the hoop's tenon in a plinth {k.TIER_T:g} tall, mortise {k.MORT_D:g} deep")
    check((hw ^ base).volume() < 1e-2, "hoop and base do not overlap", f"{(hw ^ base).volume():.4f} mm^3")
    seat = (hw.translate([0, 0, -0.05]) ^ base).volume()
    check(seat > 1.0, "tenon bottoms on the mortise floor (sets the height)", f"{seat:.1f} mm^3 at 0.05 down")
    stuck = max((F.W(ki["tenon_nb"].translate([0, t, 0])) ^ base).volume() for t in np.arange(0.25, k.MORT_D/F.C + 1.0, 0.25))
    check(stuck < 1e-3, "tenon (barbs flexed in) slides straight in and out along the neck", f"{stuck:.4f} mm^3 in the way")
    side = (hw.translate([s.FIT + 0.05, 0, 0]) ^ base).volume()
    check(side > 1.0, f"tenon located sideways within {s.FIT + 0.05:.2f} (mortise FIT {s.FIT:g})", f"{side:.1f} mm^3")
    h_def = s.BARB_H - s.FIT
    L_eff = s.TANG_L - s.BARB_Y
    eps = 3*s.TANG_T*h_def/(2*L_eff**2)
    check(eps <= SNAP, f"snap arm strain <= {SNAP*100:g}% while the barbs pass (PLA, snaps once)", f"{eps*100:.2f}%")
    kk = 3*E*(s.HD*s.TANG_T**3/12)/L_eff**3
    ramp, back = math.atan(s.BARB_H/(s.BARB_RAMP - 0.2)), math.atan(s.BARB_BACK/s.BARB_H)
    f_in, f_out = 2*kk*h_def*math.tan(ramp), 2*kk*h_def/math.tan(back)
    check(f_in <= 30.0 and f_out >= s.PUSH_N, "snap in <= 30 N, out >= a 20 N plug pull (PLA)", f"in {f_in:.1f} N, out {f_out:.0f} N")
    gap = -H.ring_radii(s, geo)[0] - (screw["y_bot"] + s.TANG_L)
    check(gap >= c.MIN_WALL, f"slots stop short of the gap inside the ring by >= {c.MIN_WALL}", f"{gap:.2f}")
    above = k.MORT_D/F.C - s.TANG_L
    check(above >= 0.5, "slots end inside the mortise, never open above the plinth", f"{above:.1f} mm to spare")
    inner = R["pl"].offset(-k.PLINTH_CH, Round)
    worst = 99.0
    for z in (s.TIER_T - k.MORT_D + 0.3, s.TIER_T - 0.6):
        hole = ki["mort"].slice(z)
        for wl in np.arange(0.2, 6.0, 0.05):
            if (hole - inner.offset(-wl, Round)).area() > 1e-3:
                worst = min(worst, wl - 0.05); break
    check(worst >= c.MIN_WALL, f"plinth wall round the mortise >= {c.MIN_WALL} (inside its chamfer)", f"{worst:.2f}")
    hp_ = (R['hoopW'] ^ m3.Manifold.cube([300, 300, 300]).translate([-150, -150, s.TIER_T + 0.2])) + F.W(ki["tenon_nb"]) + R['plateW']
    worst = max((hp_.translate(list(t*F.vec([0, 1, 0]))) ^ base).volume() for t in np.arange(0.5, 40.0, 0.5))
    check(worst < 1e-3, "whole hoop (plate on) slides up its neck clear of the base and posts: 40 mm", f"{worst:.4f} mm^3")
    check(s.TIER_T - k.MORT_D >= c.MIN_WALL, f"floor under the mortise >= {c.MIN_WALL}", f"{s.TIER_T - k.MORT_D:.1f}")


def path_checks(R):
    k, s, b, c, F, geo, feats = R["k"], R["s"], R["b"], R["c"], R["F"], R["geo"], R["feats"]
    case, base, cable = R["case"], R["base"], R["cable"]
    print(f"\n13. Stand paths ({tag(k)})")
    tipb = 23.95
    plug_b = prism(rect(-s.PLUG_W/2, s.PLUG_W/2, tipb, tipb + s.PLUG_L), b.port_z - s.PLUG_T/2, b.port_z + s.PLUG_T/2)
    v = (F.W(plug_b) ^ (F.W(case) + base + R["lever"])).volume()
    check(v < 1e-3, "plug body 12 x 8 x 22 clear of the hoop, base and lever", f"{v:.4f} mm^3")
    fing = prism(rect(-s.PLUG_W/2 - s.FINGER, s.PLUG_W/2 + s.FINGER, tipb + 4, tipb + s.PLUG_L), b.port_z - s.PLUG_T/2 - 2, b.port_z + s.PLUG_T/2 + 2)
    check((fing ^ case).volume() < 1e-3, "finger room 5 mm each side of the plug body", "")
    v = (cable ^ (F.W(case) + base + R["lever"] + R["knob"])).volume()
    check(v < 0.5, "cable loop clear of the hoop, base and key (sits in the keyhole)", f"{v:.3f} mm^3")
    disc_tab = next(f for f in feats if f.name == "disc + tab")
    stand = case - prism(circle(geo["R_OUT"]) + geo["boss"], -5, 40)
    path = prism(disc_tab.outline, 0, geo["Z_CASE"] + 30)
    v = (path ^ stand).volume()
    check(v < 1e-3, "badge goes in from the back past the hoop (hoop off the base)", f"{v:.4f} mm^3")
    v = (prism(circle(b.r), -30, 0) ^ stand).volume()
    check(v < 1e-3, "nothing of the stand in front of the glass", f"{v:.4f} mm^3")
    stand_only = R["extra"] - prism(circle(geo["R_OUT"] + 0.5) + geo["boss"].offset(0.5, Round), -c.LIP_T - 1, 40)
    stand_only -= prism(rect(-60, 60, -200, -H.ring_radii(s, geo)[1] - 1), -c.LIP_T - 1, 40)
    stand_only -= union(prism(p.offset(0.6, Round), -c.LIP_T - 1, 40) for p in R["info"]["pivots"])
    Z0 = -c.LIP_T
    areas = [stand_only.slice(z).area() for z in np.linspace(Z0 + s.EDGE + 0.05, Z0 + s.HD - s.EDGE - 0.05, 7)]
    check(max(areas) - min(areas) < 0.01*max(areas), "hoop is a straight extrusion in print: layers run along every member", "")


def lever_checks(R):
    k, s, b, c, F, g = R["k"], R["s"], R["b"], R["c"], R["F"], R["g"]
    P = g["P"]
    hoopW, plateW, base, bi = R["hoopW"], R["plateW"], R["base"], R["bi"]
    lev, rig, knob, pin = R["lever"], R["lever_rigid"], R["knob"], R["pin"]
    nub3 = xprism(g["nub"], k.X0, k.X0 + k.NUB_W)
    print(f"\n14. Key at rest ({tag(k)}): pin {k.PIN_D:g}, nub arm {g['h']:.1f}, knob arm {g['a']:.1f} "
          f"(ratio {g['a']/(g['h']*g['cb']):.2f}), rear arm {g['beta']:.0f} deg steeper than the plate; blade {k.T0:.2f} to {k.T_TIP:.2f}")
    foot = xprism(circle(k.FOOT_R + 0.3).translate([g["Y_ft"], g["floor"] - k.HP_PRE + k.FOOT_R]), k.X0 - 1, k.X0 + k.W + 1)
    for nm, m in (("hoop + case", hoopW), ("back plate", plateW), ("base", base), ("pin", pin)):
        v = ((lev - foot) ^ m).volume() + (knob ^ m).volume()
        check(v < 1e-3, f"lever and knob do not overlap the {nm}", f"{v:.4f} mm^3")
    v = (foot ^ lev ^ base).volume()
    check(v > 0.05, f"hairpin foot pressed {k.HP_PRE:g} into the base at rest: its preload", f"{v:.2f} mm^3")
    v = (pin ^ (base - bi["posts"])).volume() + (pin ^ hoopW).volume()
    check(v < 1e-3, "pin touches nothing but its post holes", f"{v:.4f} mm^3")
    gp = rig.min_gap(plateW, 5.0)
    check(abs(gp - k.G) < 0.03 and gp - k.G_TOL >= 0.15, "nub tip G behind the flush tab; even at G - tol the hoop slides past",
          f"gap {gp:.2f} (min {gp - k.G_TOL:.2f})")
    g_case = (rig - nub3).min_gap(hoopW + plateW, 6.0)
    check(g_case >= k.CLR, f"rest of the lever >= {k.CLR} off the case and hoop", f"{g_case:.2f}")
    g_kh = knob.min_gap(hoopW, 10.0)
    check(g_kh >= k.CLR, f"knob >= {k.CLR} off the hoop", f"{g_kh:.2f}")
    others = base - bi["bs"] - bi["anvil"]
    gb = min((m.min_gap(o, 5.0), f"{mn} to {on}") for mn, m in (("lever", rig), ("knob", knob))
             for on, o in (("posts", bi["posts"]), ("plinth, plate", others - bi["posts"])))
    check(gb[0] >= k.CLR - 0.01, f"lever and knob >= {k.CLR} off the base, posts and plinth at rest", f"{gb[0]:.2f} ({gb[1]})")
    heel = xprism(yzrect(P[0], P[0] + k.HEEL_L, P[1] - k.R_HUB - 0.01, P[1] - k.R_HUB + 0.5), k.X0, k.X0 + k.W)
    v = (heel.translate([0, 0, -0.05]) ^ bi["bs"]).volume()
    check(v > 0.01 and (rig ^ bi["bs"]).volume() < 1e-3, "heel rests on the back stop (sets G at rest)", f"{v:.3f} mm^3 at 0.05 down")
    disc_tab = next(f for f in R["feats"] if f.name == "disc + tab")
    glassW = F.W(disc_tab.solid())
    v = (rig ^ F.W(prism(circle(b.r + 2.0), -40, 0))).volume() + (rig ^ glassW).volume()
    check(v < 1e-4, "nothing of the key in front of, or on, the glass", f"{rig.min_gap(glassW, 30):.1f} mm from the badge")
    # the hairpin, deformed: its bend sinks with the lever and lifts with its own bending; the blade sags onto it
    sp = R["sp"]
    gap_l2 = g["l2b"] - k.T_HP/2 - k.BASE_T if g["floor"] >= k.BASE_T - 1e-6 else g["l2b"] - k.T_HP/2 - g["floor"]
    R["hp_gaps"] = gap_l2
    print(f"      hairpin: legs {k.T_HP:g} x {k.HP_W:g}, upper {k.HP_L:g} long; foot {k.X_T:g} forward of the pin; "
          f"{'pocket floor ' + format(g['floor'], '.1f') if g['floor'] < k.BASE_T - 1e-6 else 'on the plate top'}")


def force_checks(R):
    k, g, sp, d_stop, F = R["k"], R["g"], R["sp"], R["d_stop"], R["F"]
    print(f"\n15. The press ({tag(k)}): blade {k.T0:g} tapering to {k.T_TIP:g}, {sp['c_f']:.2f} mm/N at the knob; "
          f"tab {sp['k_tab']:.2f} N/mm; switch {k.F_SW:g} N")
    res = {}
    for nm, G in (("G-tol", k.G - k.G_TOL), ("G", k.G), ("G+tol", k.G + k.G_TOL)):
        rows = press(k, g, sp, G)
        click = rows[CLICK]
        touch = rows[11]
        stop = FB.at_drop(rows, d_stop)
        res[nm] = (rows, touch, click, stop)
        print(f"      {nm:5s} {G:.2f}: touch at {touch[0]:.2f} mm, click at {click[0]:.2f} mm with {click[1]:.2f} N on the knob; "
              f"stop at {d_stop:.2f}: knob {stop[1]:.2f} N, nub {stop[2]:.2f} N")
    R["res"] = res
    ck = res["G"][2]
    check(2.4 <= ck[0] <= 3.3, "knob travel to the click 2.4-3.3 mm (nominal gap; aim 2.5-3)", f"{ck[0]:.2f} mm, {ck[1]:.2f} N")
    hi = res["G+tol"][2]
    check(hi[0] <= d_stop - k.SPARE + 1e-6, f"clicks before the stop even at the largest gap", f"{d_stop - hi[0]:.2f} mm of knob to spare")
    st = res["G-tol"][3]
    sw = st[2] - sp["k_tab"]*STROKE
    check(st[2] <= k.F_N_MAX, f"push on the tab at the stop, smallest gap <= {k.F_N_MAX:g} N (switch and glass)",
          f"{st[2]:.2f} N: switch {sw:.2f} N + tab spring {sp['k_tab']*STROKE:.2f}")
    R["worst"] = st
    # every strain, at the worst stop (smallest gap). Past the stop a press goes straight into the anvil.
    print(f"      a {k.PRESS:g} N press: the pad is on the anvil, so the lever carries no more than at the stop")
    Fk, Fn, Fr = st[1], st[2], st[4]
    e_f = sp["eps_f"](Fk)
    check(e_f <= FLEX, f"blade strain <= {FLEX*100:g}% (flexes every press)", f"{e_f*100:.2f}% at {Fk:.2f} N, deflecting {Fk*sp['c_f']:.2f} mm")
    e_r = 6*Fn*sp["Lr"]/(E*k.W*k.W_R**2)
    check(e_r <= FLEX, f"rear arm strain <= {FLEX*100:g}%", f"{e_r*100:.2f}%")
    e_h = Fr*sp["hp_xmax"]*(k.T_HP/2)/sp["EI1"]
    check(e_h <= FLEX, f"hairpin strain <= {FLEX*100:g}%", f"{e_h*100:.2f}% at {Fr:.2f} N")
    e_t = 3*U.TAB_T*STROKE/(2*U.TAB_L**2)
    check(e_t <= FLEX, f"plate tab strain <= {FLEX*100:g}% (stops when the switch bottoms)", f"{e_t*100:.2f}%")
    Lp = k.PIN_SLOT_L - 1.4
    e_p = 3*((k.PIN_D - k.PIN_SLOT)/2)*(k.PIN_D/2 + k.PIN_BARB - k.PIN_D/2 - k.HOLE_CLR)/(2*Lp**2)
    check(e_p <= SNAP, f"pin's snap prongs <= {SNAP*100:g}% passing the post", f"{e_p*100:.2f}%")
    Lq = k.PEG_ENG + g["lift"] - 1.9
    e_q = 3*k.PEG_T*(k.PEG_BARB - k.SOCK_CLR)/(2*Lq**2)
    check(e_q <= SNAP, f"knob peg prongs <= {SNAP*100:g}% snapping on", f"{e_q*100:.2f}%")
    # pin and posts carry the lever's reaction at the stop
    n = g["n"]
    Rv = -(np.array([0.0, -Fk]) + (-Fn)*n + np.array([0.0, Fr]))          # pin on the lever
    span = k.W + 2*k.CLR_X + k.POST_T
    M = np.linalg.norm(Rv)*(span/4 - k.W/8)
    sig = M/(math.pi*k.PIN_D**3/32)
    check(MPA/sig >= 2.0, "pin in bending (printed lying down: along its layers) SF >= 2", f"{np.linalg.norm(Rv):.1f} N, {sig:.1f} MPa")
    sig_p = abs(Rv[0])/2*(g["P"][1] - k.BASE_T)/(k.POST_T*(2*k.POST_HY)**2/6)
    check(MPA_Z/sig_p >= 2.0, "each post bending across its layers SF >= 2 (10 MPa)", f"{sig_p:.2f} MPa")
    sig_k = k.PRESS/(2*k.PEG_T*k.PEG_W)
    sig_a = k.PRESS/(math.pi*k.R_ANV**2)
    check(max(sig_k, sig_a) < MPA_Z, f"{k.PRESS:g} N on the knob: peg tops and anvil in compression", f"peg {sig_k:.1f} MPa, anvil {sig_a:.1f} MPa")
    # the hairpin: preload holds the knob up; leg clearances when deformed at the stop
    lev_g = H.to_tm(R["lever"]).center_mass
    m_l = (R["lever"].volume() + R["knob"].volume())*RHO
    M_g = m_l*H.G*(g["P"][0] - lev_g[1])
    M_0 = sp["k_hp"]*k.HP_PRE*k.X_T
    check(M_0 >= 3*max(M_g, 0.0), "hairpin holds the knob up: rest moment >= 3x the key's weight", f"{M_0:.2f} vs {M_g:.2f} N.mm")
    phi_s = d_stop/g["a"]
    sink = phi_s*(g["P"][0] - g["Y_b"]) - Fr*sp["lift_b"]
    gl2 = R["hp_gaps"] - max(sink, 0.0)
    check(gl2 >= k.CLR, "hairpin's bend stays off the base at the stop", f"{gl2:.2f} (sinks {sink:.2f})")
    zab = g["Z_AT"] - float(g["t"](g["Y_b"]))
    gl1 = zab - (g["l1"] + k.T_HP/2) - sp["sag"](Fk, g["Y_b"]) - Fr*sp["lift_b"]
    check(gl1 >= k.CLR, "blade's sag stays off the hairpin's upper leg", f"{gl1:.2f}")
    R["phi_s"] = phi_s


def first_contact(moving, target, lo, hi):
    return FB.first_contact(moving, target, lo, hi)


def assembly_checks(R):
    k, s, F, g, d_stop = R["k"], R["s"], R["F"], R["g"], R["d_stop"]
    P = g["P"]
    hoopW, plateW, base, bi = R["hoopW"], R["plateW"], R["base"], R["bi"]
    rig, knob, pin, lev = R["lever_rigid"], R["knob"], R["pin"], R["lever"]
    geo_b = R["geo_b"]
    tab_reg = prism(geo_b["tab"].offset(0.02, Round), -2, geo_b["Z_CASE"] + 2)
    tab = R["plate_b"] ^ tab_reg
    tabW_moved = F.W(tab.translate([0, 0, -STROKE]))
    plate_rest = F.W(R["plate_b"] - tab_reg)
    nub3 = xprism(g["nub"], k.X0, k.X0 + k.NUB_W)
    swing = lambda phi: rot3(rig + knob, P, phi)
    phi_s = R["phi_s"]
    phi_t = first_contact(swing, plateW, 0.0, phi_s)
    phi_c = first_contact(swing, tabW_moved, 0.0, phi_s)
    pad3 = xprism(yzrect(g["K_Y"] - k.PAD_HL, g["K_Y"] + k.PAD_HL, g["pad_bot"], g["Z_AT"]), k.X0, k.X0 + k.W)
    phi_a = first_contact(lambda p: rot3(pad3, P, p), bi["anvil"], 0.0, phi_s + 0.1)
    print(f"\n16. The swing ({tag(k)}): first touch {math.degrees(phi_t):.2f} deg, click {math.degrees(phi_c):.2f} deg (rigid), "
          f"pad on the anvil {math.degrees(phi_a):.2f} deg")
    check(abs(phi_a - phi_s) < 0.01, "the pad lands on the anvil at the stop the model asks for", f"{math.degrees(phi_a - phi_s):+.2f} deg")
    # past the click the tab holds the nub and the blade bends: the rear of the lever turns only as far as the
    # model says (phi_m), while the blade, pad and knob turn at most rigidly to the anvil (phi_s)
    fbox = m3.Manifold.cube([200, 200, 200]).translate([-100, P[0] - k.R_HUB - 0.5 - 200, -100])
    front, rear = (rig ^ fbox) + knob, rig - fbox
    phi_m = max(R["res"][nm][3][3] for nm in R["res"])
    others = base - bi["anvil"] - bi["bs"]
    named = (("posts", bi["posts"]), ("plinth, plate", others - bi["posts"]))
    worst_b, worst_h = (9.0, ""), (9.0, "")
    for f in np.linspace(0.05, 1.0, 6):
        pf, pr = f*(phi_s - 0.004), f*phi_m
        mf, mr = rot3(front, P, pf) - rot3(pad3, P, pf), rot3(rear, P, pr)
        for nm, m in (("blade/knob", mf), ("hub/rear arm", mr)):
            for on, o in named:
                gg = m.min_gap(o, 3.0)
                if gg < worst_b[0]: worst_b = (gg, f"{nm} to {on}")
            gg = (m - rot3(nub3, P, pr)).min_gap(hoopW + plateW, 4.0)
            if gg < worst_h[0]: worst_h = (gg, nm)
        gg = rot3(pad3, P, pf).min_gap(others, 3.0)
        if gg < worst_b[0]: worst_b = (gg, "pad to base")
    check(worst_b[0] >= k.CLR - 0.02, f"swing to the stop: lever and knob >= {k.CLR} off the base, posts, plinth",
          f"min {worst_b[0]:.2f} ({worst_b[1]})")
    check(worst_h[0] >= k.CLR - 0.02, f"swing to the stop: the lever (bar the nub) >= {k.CLR} off the hoop", f"min {worst_h[0]:.2f} ({worst_h[1]})")
    mv_c = swing(phi_c)
    check((mv_c ^ plate_rest).volume() < 1e-4, "at the click the nub touches the tab only", "")
    worst = 0.0
    for dx, du in ((-0.7, 0), (0.7, 0), (0, -0.7), (0, 0.7)):
        worst = max(worst, (mv_c.translate([dx, du*g["u"][0], du*g["u"][1]]) ^ plate_rest).volume())
    check(worst < 1e-4, "nub 0.7 off in X or up/down the plate still pushes the tab only", f"{worst:.4f} mm^3")
    R["phi_c"] = phi_c
    print(f"\n17. Assembly and retention ({tag(k)})")
    xa, xb, tip = R["pin_x"]
    inner_face = k.X0 - k.CLR_X - k.POST_T
    check(xa < inner_face and xb > k.X0 + k.W + k.CLR_X + k.POST_T, "pin: head outside the outer post, barbs snapped past the inner one",
          f"{k.PIN_BARB:g} barbs, {inner_face - xa:.1f} end play")
    shank = pin - xprism(rect(-200, 200, -200, 200), tip - 1, xa + 0.01)
    worst = max((shank.translate([t, 0, 0]) ^ (base + hoopW)).volume() for t in np.arange(0.5, 30.0, 0.5))
    check(worst < 1e-3, "pin goes in from outside, along X, past the hoop: 30 mm of path", f"{worst:.4f} mm^3")
    up = F.vec([0, 1, 0])
    hoop = hoopW + plateW
    worst = max((hoop.translate(list(t*up)) ^ (lev + knob + pin)).volume() for t in np.arange(0.0, 30.0, 0.5))
    check(worst < 1e-3, "hoop (plate on) slides up its neck past the nub and knob: 30 mm", f"{worst:.4f} mm^3")
    worst = max((knob.translate([0, 0, t]) ^ (base + hoopW)).volume() for t in np.arange(0.5, 25.0, 0.5))
    check(worst < 1e-3, "knob snaps straight down onto its peg, 25 mm of path", f"{worst:.4f} mm^3")
    nofoot = lev - xprism(rect(-200, 200, -200, g["floor"] + 1.2), k.X0 - 1, k.X0 + k.W + 1)
    worst = max((nofoot.translate([0, 0, t]) ^ base).volume() for t in np.arange(0.0, 25.0, 0.5))
    check(worst < 1e-3, "lever drops in between the posts from above", f"{worst:.4f} mm^3")
    wk = bi["key"].min_gap(bi["posts"] + bi["anvil"], 30.0)
    check(wk >= 1.2, "cable keyhole well clear of the key's posts and anvil", f"{wk:.1f} mm")


def plan_r(m, BASE_Y):
    v = np.asarray(m.to_mesh().vert_properties)[:, :2]
    return float(np.max(np.hypot(v[:, 0], v[:, 1] - BASE_Y)))


def size_checks(R):
    k, BASE_Y = R["k"], R["BASE_Y"]
    body = R["plug"][0]
    stand = R["hoopW"] + R["lever"] + R["knob"] + R["pin"] + R["base"]
    r_st = plan_r(R["hoopW"] + R["lever"] + R["knob"] + R["pin"], BASE_Y)
    r_pl = plan_r(body, BASE_Y)
    top = bbox(stand + body)[1, 2]
    R["sizes"] = dict(r_st=r_st, r_pl=r_pl, top=top, glass=R["F"].H0)
    print(f"\n18. Size ({tag(k)})")
    check(r_st <= k.BASE_R + 1e-6, f"hoop, key and base all inside the Ø{2*k.BASE_R:g} footprint", f"{r_st:.1f} of {k.BASE_R:g} from the centre")
    print(f"      plug: reaches {r_pl:.1f} from the base centre ({'inside' if r_pl <= k.BASE_R else 'over the edge by ' + format(r_pl - k.BASE_R, '.0f') + ' mm'})")
    check(top <= 89.0, "height <= 89 mm (today's, to the plug top)", f"{top:.1f} mm")


def stability(R):
    k, s, b, F, BASE_Y = R["k"], R["s"], R["b"], R["F"], R["BASE_Y"]
    print(f"\n19. Stability ({tag(k)}): PLA, base 100% infill, 1 N cable pull, a press on the knob")
    parts = {"hoop + case": R["hoopW"], "plate": R["plateW"], "base": R["base"], "lever": R["lever"], "knob": R["knob"], "pin": R["pin"]}
    masses = []
    for nm, m in parts.items():
        masses.append((m.volume()*RHO, H.to_tm(m).center_mass))
    masses.append((s.BADGE_G, F.pt([0, 0, 2.5])))
    masses.append((s.PLUG_G, F.pt([0, 23.95 + s.PLUG_L/2, b.port_z])))
    print("      " + ", ".join(f"{nm} {g_:.1f} g" for nm, (g_, _) in zip(parts, masses)))
    cxy, cr = np.array([0, BASE_Y]), k.BASE_R - 0.6
    worst, com, Wt = H.tip_angles(s, F, masses, cxy, cr, R["cable_exit"], 90.0)
    check(worst[0] >= s.MIN_TIP, f"tip angle >= {s.MIN_TIP:g} with the 1 N cable pull", f"worst {worst[0]:.1f} deg toward {worst[1]:.0f} deg")
    K3 = np.array([R["g"]["Xk"], R["g"]["K_Y"], R["g"]["Z_kb"] + k.KNOB_H])
    s0 = replace(s, PULL_N=0.0)
    w0 = H.tip_angles(s0, F, masses + [(k.PRESS_STAB/H.G, K3)], cxy, cr, K3, 90.0)[0]
    inside = math.hypot(K3[0] - cxy[0], K3[1] - cxy[1])
    check(inside < cr and w0[0] >= s.MIN_TIP, f"{k.PRESS_STAB:g} N straight down on the knob can't tip it",
          f"knob {cr - inside:.0f} mm inside the rim; tip angle {w0[0]:.0f} deg")
    a_max = 0.0
    for a in np.arange(0, 60, 0.25):
        A = math.radians(a)
        if k.PRESS_STAB*math.sin(A) > k.MU*(Wt + k.PRESS_STAB*math.cos(A)): break
        a_max = a
    A = math.radians(a_max)
    s2 = replace(s, PULL_N=k.PRESS_STAB*math.sin(A))
    w2 = min(H.tip_angles(s2, F, masses + [(k.PRESS_STAB*math.cos(A)/H.G, K3)], cxy, cr, K3, d)[0][0] for d in (0, 90, 180, 270))
    check(a_max >= 15.0 and w2 >= 5.0, f"{k.PRESS_STAB:g} N may lean {a_max:.0f} deg before the {Wt/H.G:.0f} g stand slides (mu {k.MU:g}); "
          "leaning that far it can't tip it", f"{w2:.0f} deg more tilt to tip")
    R["tip"] = worst[0]
    R["mass"] = Wt/H.G


# ---- exports and renders ----------------------------------------------------------
def exports(R, first):
    k, c, g = R["k"], R["c"], R["g"]
    print()
    export(R["case"], STL + f"hoop and case ({tag(k)}).stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(R["base"], STL + f"base ({tag(k)}).stl", lambda m: m)
    export(R["lever"], STL + f"lever ({tag(k)}).stl", lambda m: m.transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -k.X0]], float)))
    if first:
        export(R["knob"], STL + "knob.stl", lambda m: m.translate([0, 0, -g["Z_kb"]]))
        export(R["pin"], STL + "pin.stl", lambda m: m.translate([0, 0, -(g["P"][1] - k.PIN_D/2 + k.PIN_FLAT)]))


COL = dict(brass=(0.84, 0.67, 0.33), lever=(0.90, 0.72, 0.30), plate=(0.66, 0.50, 0.24), dark=(0.07, 0.07, 0.09),
           white=(0.95, 0.95, 0.90), red=(0.88, 0.22, 0.18), steel=(0.75, 0.77, 0.80), walnut=(0.36, 0.22, 0.13),
           black=(0.15, 0.15, 0.16), cream=(0.96, 0.92, 0.80), green=(0.25, 0.70, 0.35), violet=(0.62, 0.30, 0.80))


def scene(R, phi=0.0, gear=True, face=True):
    rf = lambda m, L=1.0: m.refine_to_length(L)
    F, g, k = R["F"], R["g"], R["k"]
    P = g["P"]
    out = [(rf(R["hoopW"]), COL["brass"]), (rf(R["plateW"]), COL["plate"]), (rf(R["base"], 1.6), COL["walnut"]),
           (rf(rot3(R["lever"], P, phi), 0.8), COL["lever"]), (rf(rot3(R["knob"], P, phi), 0.8), COL["lever"]),
           (rf(R["pin"], 0.6), COL["steel"])]
    if face:
        disc_tab = next(f for f in R["feats"] if f.name == "disc + tab").solid()
        ticks, hands, sec_, hub = H.dial(R["b"])
        out += [(rf(F.W(disc_tab)), COL["dark"]), (rf(F.W(ticks), 0.6), COL["cream"]), (rf(F.W(hands), 0.6), COL["cream"]),
                (rf(F.W(sec_), 0.6), COL["red"]), (rf(F.W(hub), 0.6), COL["brass"])]
    if gear:
        body, shell, boot = R["plug"]
        out += [(rf(body), COL["black"]), (rf(shell, 0.6), COL["steel"]), (rf(boot), COL["black"]), (rf(R["cable"], 1.5), COL["black"])]
    return out


def grid(paths, out, title, ncol):
    import matplotlib.pyplot as plt, matplotlib.image as mpimg
    nrow = (len(paths) + ncol - 1)//ncol
    fig, axs = plt.subplots(nrow, ncol, figsize=(5.6*ncol, 5.4*nrow), dpi=110)
    for ax, pth in zip(np.ravel(axs), paths):
        ax.imshow(mpimg.imread(pth)[50:-30, 30:-30]); ax.set_axis_off()
    fig.suptitle(title, fontsize=11)
    fig.subplots_adjust(0, 0, 1, 0.94, 0.0, 0.02); fig.savefig(out, facecolor="white"); plt.close(fig)
    print("wrote", out)


def renders(Rs):
    tmp = tempfile.mkdtemp()
    R = Rs[0]
    k, g, F, c = R["k"], R["g"], R["F"], R["c"]
    P = g["P"]
    rf = lambda m, L=1.0: m.refine_to_length(L)
    sz = R["sizes"]
    render(scene(R), OUT + "01-hero.png", elev=16, azim=-50, zoom=1.2,
           title=f"Telegraph-key hoop, face {k.TILT:.0f} deg back: press the brass knob, the lever tips up into BOOT")
    render(scene(R, face=False), OUT + "02-back.png", elev=20, azim=40, zoom=1.2, light=(0.45, 0.75, 0.5),
           title="From behind and below the case: pin on two posts, rear arm up to the plate's BOOT tab")
    # sections through the nub, at rest and at the click
    xs = k.X0 + k.NUB_W/2
    geo_b, feats = R["geo_b"], R["feats"]
    tab_reg = prism(geo_b["tab"].offset(0.02, Round), -2, geo_b["Z_CASE"] + 2)
    post = R["plate_b"] ^ geo_b["post_cyl"]
    plate_np = R["plate_b"] - geo_b["post_cyl"]
    fs = [(f.solid(), COL["dark"] if f.name == "disc + tab" else COL["green"] if f.name.startswith(c.BUTTON) else COL["white"])
          for f in feats if not f.name.startswith("plug")]
    Tip = g["Tip"]
    box = m3.Manifold.cube([40, 16, 16]).translate([-20, Tip[0] - 8, Tip[1] - 8])
    res = R["res"]
    for nm, phi, push in (("rest", 0.0, 0.0), ("pressed", R["phi_c"], STROKE)):
        moved = lambda m: F.W(m - tab_reg) + F.W((m ^ tab_reg).translate([0, 0, -push]))
        parts = [(R["hoopW"], COL["brass"]), (moved(plate_np), COL["plate"]), (moved(post), COL["violet"]), (R["base"], COL["walnut"]),
                 (rot3(R["lever"], P, phi), COL["lever"]), (rot3(R["knob"], P, phi), COL["lever"]), (R["pin"], COL["steel"])] + \
                [(F.W(m), col) for m, col in fs]
        cut, det = [], []
        for m, col in parts:
            m = m.trim_by_plane([1, 0, 0], xs)
            if m.is_empty(): continue
            cut.append((rf(m, 1.2), col))
            d = m ^ box
            if not d.is_empty(): det.append((rf(d, 0.4), col))
        render(cut, os.path.join(tmp, "full.png"), elev=0, azim=180, zoom=1.2)
        render(det, os.path.join(tmp, "det.png"), elev=0, azim=180, zoom=1.0)
        if nm == "rest":
            ttl = (f"Section on the nub (X {xs:.1f}), at rest: nub {k.G:g} off the tab, heel on the back stop, "
                   f"pad {R['d_stop']:.1f} over the anvil")
        else:
            ttl = (f"Pressed to the click: the tab is in {STROKE:.2f} and the post (violet) is on BOOT. Knob travel "
                   f"{res['G'][2][0]:.1f} mm; the stop is at {R['d_stop']:.1f}")
        FB.side_by_side([os.path.join(tmp, "full.png"), os.path.join(tmp, "det.png")], OUT + f"section-{nm}.png", ttl)
    # angle comparison: hero and side view of each candidate
    paths = []
    for Ri in Rs:
        for view, (el, az) in (("hero", (16, -50)), ("side", (2, 0))):
            pth = os.path.join(tmp, f"cmp-{Ri['k'].TILT:.0f}-{view}.png")
            si = Ri["sizes"]
            render(scene(Ri), pth, elev=el, azim=az, zoom=1.15,
                   title=f"{tag(Ri['k'])}: glass centre {si['glass']:.0f} mm up, {si['top']:.0f} tall, tip {Ri['tip']:.0f} deg"
                   + ("" if si["r_pl"] <= Ri["k"].BASE_R else f", plug {si['r_pl'] - Ri['k'].BASE_R:.0f} mm over the base"))
            paths.append(pth)
    grid(paths, OUT + "angles.png", "Choose the lean: " + " vs ".join(tag(Ri["k"]) for Ri in Rs) +
         " from vertical (the hoop stand: 20). Same key, same Ø76 base.", 2)
    # exploded
    up, back = F.vec([0, 1, 0]), F.vec([0, 0, 1])
    mv = lambda m, v: m.translate(list(v))
    disc_tab = next(f for f in feats if f.name == "disc + tab").solid()
    ex = [(rf(mv(R["hoopW"], 40*up)), COL["brass"]), (rf(mv(F.W(disc_tab), 40*up + 24*back)), COL["dark"]),
          (rf(mv(R["plateW"], 40*up + 40*back)), COL["plate"]), (rf(R["base"], 1.6), COL["walnut"]),
          (rf(R["lever"].translate([0, 0, 14]), 0.8), COL["lever"]), (rf(R["knob"].translate([0, 0, 30]), 0.8), COL["lever"]),
          (rf(R["pin"].translate([22, 0, 14]), 0.6), COL["steel"])]
    render(ex, OUT + "exploded.png", elev=16, azim=-40, zoom=1.0,
           title="Assembly: lever between the posts, pin in from outside, knob on; then badge, plate, hoop down its neck")
    # print layout
    lay_h = R["case"].translate([0, 0, c.LIP_T])
    pl = R["plate_b"].rotate([0, 180, 0]).translate([0, 0, geo_b["Z_CASE"]])
    lv = R["lever"].transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -k.X0]], float))
    lb = bbox(lv)
    kn = R["knob"].translate([0, 0, -g["Z_kb"]])
    pn = R["pin"].translate([0, 0, -(P[1] - k.PIN_D/2 + k.PIN_FLAT)])
    lay = [(rf(lay_h), COL["brass"]), (rf(pl.translate([64, 4, 0])), COL["plate"]),
           (rf(R["base"].translate([0, -R["BASE_Y"] - 92, 0]), 1.6), COL["walnut"]),
           (rf(lv.translate([52 - lb[0, 0], -64 - lb[0, 1], 0]), 0.8), COL["lever"]),
           (rf(kn.translate([60 - g["Xk"], -30 - g["K_Y"], 0]), 0.8), COL["lever"]),
           (rf(pn.translate([50, -40 - P[0], 0]), 0.6), COL["steel"])]
    render(lay, OUT + "print-layout.png", elev=38, azim=-70, zoom=1.1,
           title="Print: hoop + case bezel down, base flat (100% infill), lever on its side, knob upright, pin on its flat. No supports.")


def main():
    b, c = Badge(), Case()
    _, _, plate_b, geo_b = U.build(b, c, U.PLATE_DISC_CLR, button=True)
    Rs = []
    for i, k in enumerate(CANDIDATES):
        if i == 0:
            s, b, c, F, feats, case, geo, *_ = hoop_at(k)
            print("--- the hoop's case with the button plate (checks from build_pocketwatch_usb.py) ---")
            H.run_case_checks(b, c, feats, case, plate_b, geo_b)
            U.run_button_checks(b, c, feats, case, plate_b, geo_b)
        Rs.append(build(k, plate_b, geo_b, i == 0))
    for i, R in enumerate(Rs):
        exports(R, i == 0)
    print("\nSummary")
    for R in Rs:
        k, sz, res = R["k"], R["sizes"], R["res"]
        print(f"  {tag(k)}: {sz['top']:.0f} tall, footprint {2*sz['r_st']:.0f} (plug reaches {sz['r_pl']:.0f} from centre), "
              f"glass centre {sz['glass']:.0f} up, tip {R['tip']:.1f} deg, {R['mass']:.0f} g; click at {res['G'][2][0]:.2f} mm "
              f"(G {res['G-tol'][2][0]:.2f}..{res['G+tol'][2][0]:.2f}), stop {R['d_stop']:.2f}; worst nub {R['worst'][2]:.2f} N")
    if "--no-render" not in sys.argv:
        renders(Rs)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
