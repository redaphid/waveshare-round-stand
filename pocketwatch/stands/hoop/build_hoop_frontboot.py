#!/usr/bin/env python3
"""
Hoop stand, front-BOOT: press a key on the front of the base and BOOT clicks. Nobody reaches behind,
nothing touches the glass.

  rocker   NEW. One flat print (an L-shaped bell crank lying in the world Y-Z plane, at X 10..14, under
           BOOT's side of the watch). A key pad at the front of the base; a key arm running back through a
           slot in the upper tier; a 1.4 mm flexure blade as the pivot, tilted 30 deg so it lines up with the
           load it carries; a foot that hooks into a pocket in the tier; and an upright arm that rises behind
           the case to a nub sitting 0.5 mm off the button plate's flush BOOT tab. The pivot is straight below the
           nub tip along the plate, so the nub moves square onto the tab. Press the key down: the arm swings forward, the nub pushes the plate's
           flexure tab, the post on the tab clicks BOOT. The key bottoms on the lower tier: a hard stop.
  base     the hoop base, plus the rocker's slot and pocket. Mortise, keyhole, ballast unchanged.
  hoop + case, back plate (button)   unchanged: the files build_hoop.py already exports.

Every load the key puts on the rocker pushes it down and back, into its pocket: nothing pulls. Before the
nub reaches the plate, the flexure's own moment tips the foot nose-down; a tongue under a ledge at the
foot's back holds its heel. The hoop (once clicked in) traps the rocker: lifting it walks the nub into
the plate. Assembly: rocker first, then the hoop slides down past the nub, parallel to the plate.

World frame as build_hoop.py: z up, viewer at -Y, BOOT at world X = +11.1 (the viewer's right).
Run from the repo root: ~/.venvs/cad/bin/python pocketwatch/stands/hoop/build_hoop_frontboot.py [--no-render]
"""
import sys, math
from dataclasses import dataclass
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pocketwatch/stands/hoop")
import numpy as np, manifold3d as m3
from build_pocketwatch import Badge, Case, Round, circle, rect, prism, union, bbox, check, FAILS, export, render
import build_pocketwatch_usb as U
import build_hoop as H

STL = H.STL + "Hoop stand front-BOOT - "
OUT = H.OUT + "frontboot-"
Miter = m3.JoinType.Miter
REST, STROKE = Case().REST_CLR, Case().STROKE
REST_CLR_TXT = f"{Case().REST_CLR:.2f}"      # post 0.20 off the switch, + 0.25 of switch travel


@dataclass(frozen=True)
class Rocker:
    X0: float = 10.0          # bed face of the rocker print (world X); the body runs X0..X0+T
    T: float = 4.0            # body thickness = print height
    NUB_W: float = 2.6        # nub runs X0..X0+NUB_W: inside the tab (round end at X 13.3, slot to 13.95)
    PAD_W: float = 10.0       # key pad runs X0..X0+PAD_W: a fingertip wide
    G: float = 0.5            # nub tip to the flush tab (= plate back face) at rest; G - G_TOL still clears the plate
    G_TOL: float = 0.3        # what G can really be: mortise 0.12 + pocket 0.12 + print slop
    R_NUB: float = 2.2        # 1.6 printed too small
    NUB_P: float = 2.0        # nub stands this proud of the arm's front face (1.4 printed too small)
    W_UP: float = 4.0         # upright arm, in-plane width: also the overtravel spring
    BLADE_T: float = 1.4      # flexure pivot: thickness (in-plane, along the layers)
    BLADE_L: float = 6.0
    BLADE_TILT: float = 30.0  # top leans forward: the blade lines up with the push it carries, so it barely bends
    FIL: float = 0.5          # fillet on every inside corner of the outline
    ZFL: float = 1.5          # pocket floor (base material under it: 1.5)
    FOOT_H: float = 3.5
    FOOT_FWD: float = 9.5     # foot runs from the pivot this far forward ...
    FOOT_BACK: float = 1.5    # ... and this far back
    TONGUE_L: float = 2.0     # heel hook under the ledge
    TONGUE_H: float = 1.5
    KEY_H: float = 4.0        # key arm depth: also the overtravel spring
    PAD_Y0: float = -35.0     # key pad, world Y (front .. back)
    PAD_Y1: float = -24.5
    PAD_TOP: float = 16.0
    DISH: float = 0.8         # finger dish in the pad top
    STOP_SPARE: float = 1.0   # pad travel left after the click at the worst (largest) G: 0.25 printed short, the
                              # lever and hoop flex more than the springs below say
    CLR: float = 0.4          # every moving face to the base / hoop
    FIT: float = 0.12         # foot in its pocket, per side
    # loads and material
    F_SW: float = 2.0         # tact switch actuation force
    E: float = 1500.0         # PETG along the layers, MPa
    STRENGTH: float = 45.0
    MU: float = 0.3           # PETG on a desk
    F_NUB_MAX: float = 8.0    # most the nub may push on the switch (and the glass on its lip) at the stop
    F_KEY_MIN: float = 2.0
    F_KEY_MAX: float = 8.0    # the model's stop force; the printed rocker is softer, so the real figure is lower


def xprism(cs, x0, x1):
    """A section drawn in world (Y, Z), extruded along world X from x0 to x1."""
    return m3.Manifold.extrude(cs, x1 - x0).transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], float))


def poly(pts):
    q = m3.CrossSection([[tuple(p) for p in pts]])
    return q if q.area() > 0 else m3.CrossSection([[tuple(p) for p in pts[::-1]]])


def band(p0, p1, w):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = (p1 - p0)/np.linalg.norm(p1 - p0)
    nrm = np.array([-d[1], d[0]])*w/2
    return poly([p0 - nrm, p1 - nrm, p1 + nrm, p0 + nrm])


def yzrect(y0, y1, z0, z1):
    return rect(min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))


def rot2(cs, P, phi):
    """Rotate a (Y, Z) section by phi (rad, CCW = key down) about P."""
    return cs.translate([-P[0], -P[1]]).rotate(math.degrees(phi)).translate([P[0], P[1]])


def rot3(m, P, phi):
    return m.translate([0, -P[0], -P[1]]).rotate([math.degrees(phi), 0, 0]).translate([0, P[0], P[1]])


def open_up(cs, top=40.0, step=0.5):
    """The region swept by a section moved straight up to z = top: a slot open at the top."""
    out = cs
    z0 = cs.bounds()[1]
    for k in range(1, int((top - z0)/step) + 1):
        out = out + cs.translate([0, k*step])
    return out


# ---- the stand as build_hoop.py makes it -------------------------------------
def hoop_setup():
    s, b, c = H.Stand(), Badge(), Case()
    feats, _, _, geo = H.build(b, c)
    R_HI, R_HO, Rc = H.ring_radii(s, geo)
    S, C = math.sin(math.radians(s.TILT)), math.cos(math.radians(s.TILT))
    Z0 = -c.LIP_T
    F = H.Frame(s.TILT, s.TIER_T + s.NECK_H + C*R_HO + S*(Z0 + s.HD))
    zm = Z0 + s.HD/2
    geo["y_t"] = (s.TIER_T - F.H0 + F.S*zm)/F.C
    geo["Yb"] = F.pt([0, geo["y_t"], zm])[1] + s.BASE_SHIFT
    extra, base, info, screw, keyinfo = H.stand_solids(s, c, geo, F, "hoop")
    feats, case, plate, geo2 = H.build(b, c, extra)
    geo.update(geo2)
    _, _, plate_b, geo_b = U.build(b, c, U.PLATE_DISC_CLR, button=True)
    return s, b, c, F, feats, case, plate_b, geo_b, base, geo, keyinfo, info, screw, extra


# ---- the rocker --------------------------------------------------------------
def rocker_geometry(r: Rocker, b, c, F, geo, d_stop):
    S, C = F.S, F.C
    n = np.array([-C, S])            # badge -z in world (Y, Z): the way the nub pushes
    u = np.array([S, C])             # badge +y: up the plate
    px = geo["sw"][c.BUTTON]
    D = F.pt([px, b.sw_y, geo["Z_CASE"]])[1:]                 # tab back face (flush with the plate), over the post
    Nc = D - n*(r.G + r.R_NUB)                                 # nub centre
    Ac = Nc + n*(r.R_NUB - r.NUB_P - r.W_UP/2)                 # a point on the upright arm's centre line
    Tip = Nc + n*r.R_NUB
    ab = np.array([-math.sin(math.radians(r.BLADE_TILT)), math.cos(math.radians(r.BLADE_TILT))])   # blade, root -> top
    Zp = r.ZFL + r.FOOT_H + ab[1]*r.BLADE_L/2                  # pivot: the blade's middle ...
    P = Tip + u*(Zp - Tip[1])/C                                # ... straight below the nub tip along the plate, so the
    arm_y = lambda z: Ac[0] + (z - Ac[1])*S/C                  # tip moves square onto the tab and never slides on it
    Yp = P[0]
    zb0, zb1 = Zp - ab[1]*r.BLADE_L/2, Zp + ab[1]*r.BLADE_L/2
    root, B = P - ab*r.BLADE_L/2, P + ab*r.BLADE_L/2
    Yr = root[0]
    foot = yzrect(Yr - r.FOOT_FWD, Yr + r.FOOT_BACK, r.ZFL, r.ZFL + r.FOOT_H)
    tongue = yzrect(Yr + r.FOOT_BACK - 0.5, Yr + r.FOOT_BACK + r.TONGUE_L, r.ZFL, r.ZFL + r.TONGUE_H)
    blade = band(root - ab*0.5, B + ab*0.5, r.BLADE_T)
    corner = yzrect(B[0] - 3.0, arm_y(zb1) + r.W_UP/2/C, zb1, zb1 + r.KEY_H)
    top = Nc + u*(r.R_NUB + 1.5)
    upright = band(np.array([arm_y(zb1 + 1.0), zb1 + 1.0]), Ac + (top - Nc), r.W_UP)
    karm = yzrect(r.PAD_Y1 - 4.0, B[0], zb1, zb1 + r.KEY_H)
    body = foot + tongue + blade + corner + upright + karm
    body = body.offset(r.FIL, Round).offset(-r.FIL, Round).simplify(0.005)
    nub = circle(r.R_NUB).translate(list(Nc)) + band(Nc, Ac, 2*r.R_NUB)
    pad_bot = H.Stand().BASE_T + d_stop
    pad = yzrect(r.PAD_Y0, r.PAD_Y1, pad_bot, r.PAD_TOP).offset(-1.5, Round).offset(1.5, Round)
    dish_r = 40.0
    pad -= circle(dish_r).translate([(r.PAD_Y0 + r.PAD_Y1)/2, r.PAD_TOP + dish_r - r.DISH])
    pad += yzrect(r.PAD_Y1 - 4.0, r.PAD_Y1 + 0.5, zb1, zb1 + r.KEY_H)          # key arm into the pad, full width
    moving = body - yzrect(-200, 200, -10, zb0 + 0.2)                           # the part that swings
    foot_act = body ^ yzrect(-200, 200, -10, r.ZFL + r.FOOT_H)                  # the foot as filleted
    heel = foot_act ^ yzrect(Yr + r.FOOT_BACK, 200, -10, 50)                    # the tongue and its fillet
    K = np.array([(r.PAD_Y0 + r.PAD_Y1)/2, r.PAD_TOP - r.DISH])               # where the finger presses
    sol = dict(ab=ab, root=root, body=body, nub=nub, pad=pad, foot=foot_act, heel=heel, moving=moving, P=P, B=B, K=K, Nc=Nc,
               D=D, n=n, u=u, Yp=Yp, zb0=zb0, zb1=zb1, pad_bot=pad_bot, h=float((Nc - P) @ u), a=float(P[0] - K[0]))
    return sol


def rocker_solid(r: Rocker, g, phi=0.0):
    m = xprism(g["body"], r.X0, r.X0 + r.T) + xprism(g["nub"], r.X0, r.X0 + r.NUB_W) + \
        xprism(g["pad"], r.X0, r.X0 + r.PAD_W)
    return rot3(m, g["P"], phi) if phi else m


# ---- the force model: rocker + blade + arms + tab + switch, all linear springs ---
def springs(r: Rocker, g, s):
    L = r.BLADE_L - r.FIL                              # straight length between the fillets
    EI_b = r.E*r.T*r.BLADE_T**3/12
    h_arm = float((g["Nc"] - g["B"]) @ g["u"])
    k_arm = 3*r.E*(r.T*r.W_UP**3/12)/h_arm**3
    a_key = float(g["B"][0] - g["K"][0])
    k_key = 3*r.E*(r.T*r.KEY_H**3/12)/a_key**3
    k_tab = 3*U.PETG_E*(2*U.TAB_R*U.TAB_T**3/12)/U.TAB_L**3
    c_hoop = 0.038/s.BOOT_N                            # build_hoop.py: 3 N on BOOT from behind moves the hoop 38 um
    return dict(L=L, EI_b=EI_b, k_arm=k_arm, k_key=k_key, k_tab=k_tab, c_hoop=c_hoop, h_arm=h_arm, a_key=a_key)


def respond(r, g, k, F_k, F_n):
    """Nub advance along n and pad drop, for key force F_k and nub force F_n (both >= 0)."""
    B, K, N, n = g["B"], g["K"], g["Nc"] + g["n"]*r.R_NUB, g["n"]
    rN = N - B
    Fn_vec = -F_n*n                                    # the plate pushes back on the nub; its moment about B is r x F
    Mt = F_k*(B[0] - K[0]) + (rN[0]*Fn_vec[1] - rN[1]*Fn_vec[0])
    L, EI, ab = k["L"], k["EI_b"], g["ab"]
    tb = np.array([-ab[1], ab[0]])                     # across the blade, CCW of its axis
    Ft = (np.array([0.0, -F_k]) + Fn_vec) @ tb         # the load across the blade at its top
    th = Mt*L/EI + Ft*L**2/(2*EI)
    dv = tb*(Ft*L**3/(3*EI) + Mt*L**2/(2*EI))
    disp = lambda p: dv + th*np.array([-(p - B)[1], (p - B)[0]])
    adv = disp(N) @ n - F_n/k["k_arm"] - F_n*k["c_hoop"]
    drop = -disp(K)[1] + F_k/k["k_key"]
    return adv, drop, th


def solve_fk(r, g, k, F_n, adv_target):
    """Key force that advances the nub to adv_target while it pushes with F_n (linear in F_k)."""
    a0, _, _ = respond(r, g, k, 0.0, F_n)
    a1, _, _ = respond(r, g, k, 1.0, F_n)
    return (adv_target - a0)/(a1 - a0)


def stroke(r, g, k, G):
    """The press, from first touch to the switch bottoming, then on into overtravel. Rows: pad drop, key
    force, nub force, tab travel, blade rotation."""
    rows = []
    for x in np.linspace(0, STROKE, 46):
        F_n = k["k_tab"]*x + (r.F_SW if x >= REST else 0.0)
        fk = solve_fk(r, g, k, F_n, G + x)
        adv, drop, th = respond(r, g, k, fk, F_n)
        rows.append((drop, fk, F_n, x, th))
    F0 = rows[-1][2]
    for extra in np.linspace(0, 12, 121)[1:]:
        F_n = F0 + extra
        fk = solve_fk(r, g, k, F_n, G + STROKE)
        adv, drop, th = respond(r, g, k, fk, F_n)
        rows.append((drop, fk, F_n, STROKE, th))
    return np.array(rows)


def at_drop(rows, d):
    i = int(np.searchsorted(rows[:, 0], d))
    i = min(max(i, 1), len(rows) - 1)
    t = (d - rows[i - 1, 0])/(rows[i, 0] - rows[i - 1, 0])
    return rows[i - 1] + t*(rows[i] - rows[i - 1])


# ---- the base: a slot for the swinging arm, a pocket and ledge for the foot ---
def base_cuts(r: Rocker, g, base, phi_stop, slide):
    sweep = g["moving"].translate([-slide, 0])
    for phi in np.linspace(-0.02, phi_stop + 0.02, 15):
        sweep = sweep + rot2(g["moving"], g["P"], phi)
    slot = open_up(sweep.offset(r.CLR, Round))
    foot = g["foot"]
    pocket = open_up((foot - g["heel"]).offset(r.FIT, Miter) + foot.translate([-slide, 0]).offset(r.FIT, Miter)) \
        + foot.offset(r.FIT, Miter)                    # the heel's own place is NOT opened upward: that is the ledge
    pocket3 = xprism(pocket, r.X0 - r.FIT, r.X0 + r.T + r.FIT)
    cut = xprism(slot, r.X0 - r.CLR, r.X0 + r.T + r.CLR) + pocket3
    return base - cut, cut, pocket3


# ---- checks -------------------------------------------------------------------
def first_contact(moving, target, lo, hi):
    """Smallest phi in [lo, hi] at which moving(phi) meets target."""
    for _ in range(22):
        mid = (lo + hi)/2
        lo, hi = (mid, hi) if (moving(mid) ^ target).volume() < 1e-5 else (lo, mid)
    return lo


def run_frontboot_checks(r, s, b, c, F, feats, case, plate_b, geo_b, base_fb, cut, keyinfo, g, k, d_stop, slide, cable):
    P = g["P"]
    hoopW, plateW = F.W(case), F.W(plate_b)
    rock = rocker_solid(r, g)
    foot3 = xprism(g["foot"], r.X0, r.X0 + r.T)
    pad3 = xprism(g["pad"], r.X0, r.X0 + r.PAD_W)
    above_blade = m3.Manifold.cube([200, 200, 200]).translate([-100, -100, g["zb1"]])
    swing = lambda phi: rot3(rocker_solid(r, g) ^ above_blade, P, phi)    # everything above the blade
    tab_reg = prism(geo_b["tab"].offset(0.02, Round), -2, geo_b["Z_CASE"] + 2)
    tab = plate_b ^ tab_reg
    tabW_moved = F.W(tab.translate([0, 0, -STROKE]))
    plate_rest = F.W(plate_b - tab_reg)
    disc_tab = next(f for f in feats if f.name == "disc + tab")
    glassW = F.W(disc_tab.solid())
    in_front = F.W(prism(circle(b.r + 2.0), -40, 0))

    print(f"\n12. Rocker at rest (pivot at world Y {P[0]:+.1f}, Z {P[1]:.1f}; nub arm {g['h']:.1f}, key arm {g['a']:.1f})")
    for nm, m in (("hoop + case", hoopW), ("back plate", plateW), ("base", base_fb)):
        v = (rock ^ m).volume()
        check(v < 1e-3, f"rocker does not overlap the {nm}", f"{v:.4f} mm^3")
    gp = rock.min_gap(plateW, 5.0)
    check(abs(gp - r.G) < 0.02 and gp - r.G_TOL >= 0.15, "nub tip G behind the flush tab; even at G - tol the hoop slides past it",
          f"gap {gp:.2f} (min {gp - r.G_TOL:.2f})")
    gc = (rock - xprism(g["nub"], r.X0, r.X0 + r.NUB_W)).min_gap(hoopW + plateW, 5.0)
    check(gc >= r.NUB_P, f"upright arm >= NUB_P {r.NUB_P} behind the case back", f"{gc:.2f}")
    above = rock ^ m3.Manifold.cube([200, 200, 200]).translate([-100, -100, g["zb1"]])
    gb = above.min_gap(base_fb, 5.0)
    check(gb >= r.CLR - 0.01, f"everything above the blade >= {r.CLR} from the base", f"{gb:.2f}")
    lo, hi = 0.0, 8.0
    for _ in range(24):
        mid = (lo + hi)/2
        lo, hi = (mid, hi) if (pad3.translate([0, 0, -mid]) ^ base_fb).volume() < 1e-5 else (lo, mid)
    check(abs(lo - d_stop) < 0.05, "key pad hangs d_stop over the lower tier (its stop)", f"{lo:.2f} (d_stop {d_stop:.2f})")
    gf = foot3.min_gap(base_fb, 3.0)
    check(gf <= r.FIT + 0.02, f"foot sits in its pocket at FIT {r.FIT}", f"{gf:.2f}")
    v = (rock ^ in_front).volume() + (rock ^ glassW).volume()
    check(v < 1e-4, "nothing of the rocker in front of, or on, the glass", f"{v:.4f} mm^3; {rock.min_gap(glassW, 30):.1f} mm from the badge")

    phi_s = d_stop/g["a"]                                         # pad on its stop, rocker rigid
    phi_c = first_contact(swing, tabW_moved, 0.0, phi_s)          # rigid nub on the tab pushed a full stroke
    phi_t = first_contact(swing, plateW, 0.0, phi_s)              # rigid nub first touches the plate
    print(f"\n13. The swing: first touch at {math.degrees(phi_t):.2f} deg, click at {math.degrees(phi_c):.2f} deg (rigid), "
          f"stop at {math.degrees(phi_s):.2f} deg")
    # past the click the bottomed tab holds the nub and the arms bend, so the top of the arm goes no further
    # than its click pose while everything low on the rocker can at most turn rigidly to the stop
    ZS = 22.0
    hi_box = m3.Manifold.cube([200, 200, 200]).translate([-100, -100, ZS])
    worst, worst_h = 9.0, 9.0
    for phi in np.linspace(0, phi_s, 7):
        mv = swing(phi)
        low = mv ^ rot3(m3.Manifold.cube([200, 200, ZS + 100]).translate([-100, -100, -100]), P, phi)
        worst = min(worst, (low - rot3(pad3, P, phi)).min_gap(base_fb, 3.0))
        worst_h = min(worst_h, low.min_gap(hoopW, 5.0))
    check(worst >= r.CLR - 0.05, f"swing to the stop: rocker >= {r.CLR} from the base slot all the way", f"min {worst:.2f}")
    check(worst_h >= r.CLR, f"swing to the stop: the rocker below Z {ZS:g} stays clear of the hoop", f"min {worst_h:.2f}")
    mv_c = swing(phi_c)
    v = (mv_c ^ plate_rest).volume()
    gq = (mv_c - rot3(xprism(g["nub"], r.X0, r.X0 + r.NUB_W), P, phi_c)).min_gap(plateW, 5)
    check(v < 1e-4, "at the click the nub touches the tab only (not the plate round it)", f"{v:.4f} mm^3")
    check(gq >= r.CLR - 0.05, "at the click the arm itself is still clear of the plate", f"{gq:.2f}")
    # the nub must find the tab even if the rocker or hoop sit off: shift it every way at the click
    worst = 0.0
    for dx, du in ((-0.7, 0), (0.7, 0), (0, -0.7), (0, 0.7)):
        sh = mv_c.translate([dx, du*g["u"][0], du*g["u"][1]])
        worst = max(worst, (sh ^ plate_rest).volume())
    check(worst < 1e-4, "nub 0.7 off in X or up/down the plate still pushes the tab only", f"{worst:.4f} mm^3")
    # a press on the outer half of the pad twists the rocker: blade torsion + bending about its stiff axis.
    # The most the rocker can carry is what bottoms the key at the smallest gap; past that the pad rests on the tier
    F_tw = at_drop(stroke(r, g, k, r.G - r.G_TOL), d_stop)[1]
    Gs = r.E/2.6
    w_, t_ = r.T, r.BLADE_T
    J = w_*t_**3*(1/3 - 0.21*(t_/w_)*(1 - t_**4/(12*w_**4)))
    I_s = t_*w_**3/12
    off = (r.X0 + r.PAD_W/2) - (r.X0 + r.T/2)
    Tq = F_tw*off
    ab = g["ab"]; tb = np.array([-ab[1], ab[0]])
    om = (Tq*ab[0]/(Gs*J/k["L"]))*ab + (Tq*tb[0]/(r.E*I_s/k["L"]))*tb
    rr = g["Nc"] + g["n"]*r.R_NUB - g["P"]
    dx = abs(om[0]*rr[1] - om[1]*rr[0])
    check(dx < 1.0, f"{F_tw:.1f} N (to the stop) on the pad's outer edge twists the nub sideways < 1.0 (nub-to-disc margin 1.35)",
          f"{dx:.2f} mm (pad centre {off:g} off the blade)")
    mv_s = swing(phi_s)
    lo, hi = 0.0, 3.0
    for _ in range(22):
        mid = (lo + hi)/2
        back = mv_s.translate([0, -g["n"][0]*mid, -g["n"][1]*mid])
        lo, hi = (lo, mid) if (back ^ tabW_moved).volume() < 1e-5 else (mid, hi)
    print(f"      a rigid rocker at the stop would put the nub {hi:.2f} into the bottomed tab: the arms and blade bend that much")
    v = (mv_s ^ in_front).volume() + (mv_s ^ glassW).volume() + (mv_c ^ glassW).volume()
    check(v < 1e-4, "at the stop nothing reaches the glass", f"{v:.4f} mm^3")

    print("\n14. The press, as springs (blade, both arms, tab, switch, hoop); G is the nub-to-tab gap")
    res = {}
    for tag, G in (("G-tol", r.G - r.G_TOL), ("G", r.G), ("G+tol", r.G + r.G_TOL)):
        rows = stroke(r, g, k, G)
        touch, click = rows[0], rows[45]
        stop = at_drop(rows, d_stop)
        res[tag] = (rows, touch, click, stop)
        print(f"      {tag:5s} {G:.2f}: touch at {touch[0]:.2f} mm of key travel, click at {click[0]:.2f} mm with "
              f"{click[1]:.2f} N on the key, stop at {d_stop:.2f} mm: key {stop[1]:.2f} N, nub {stop[2]:.2f} N")
    click_hi = res["G+tol"][2]
    check(click_hi[0] <= d_stop - 0.2, "clicks before the stop even at the largest gap", f"{d_stop - click_hi[0]:.2f} mm of key to spare")
    fk = res["G"][2][1]
    check(r.F_KEY_MIN <= fk <= r.F_KEY_MAX, f"key force at the click {r.F_KEY_MIN:g}-{r.F_KEY_MAX:g} N", f"{fk:.2f} N")
    st = res["G-tol"][3]
    check(st[1] <= r.F_KEY_MAX, f"key force at the stop <= {r.F_KEY_MAX:g} N (smallest gap)", f"{st[1]:.2f} N")
    check(st[2] <= r.F_NUB_MAX, f"push on the switch, and the glass on its lip, at the stop <= {r.F_NUB_MAX:g} N",
          f"{st[2]:.2f} N (switch alone {r.F_SW:g} N + tab {k['k_tab']*STROKE:.2f} N)")
    # strains, worst case = smallest gap at the stop
    F_k, F_n = st[1], st[2]
    Fn_vec = -F_n*g["n"]
    rN = g["Nc"] + g["n"]*r.R_NUB - g["B"]
    Mt = F_k*(g["B"][0] - g["K"][0]) + (rN[0]*Fn_vec[1] - rN[1]*Fn_vec[0])
    tb = np.array([-g["ab"][1], g["ab"][0]])
    Ft = (np.array([0.0, -F_k]) + Fn_vec) @ tb
    M_root = max(abs(Mt), abs(Mt + Ft*k["L"]))
    eps_b = M_root*(r.BLADE_T/2)/k["EI_b"]
    print(f"      blade at the stop: {Mt:+.1f} N.mm at its top, {Ft:+.1f} N across it ({r.BLADE_TILT:g} deg tilt), {M_root:.1f} N.mm worst")
    check(eps_b <= 0.02, "flexure blade strain at the stop <= 2%", f"{eps_b*100:.2f}% ({r.BLADE_T:g} x {r.T:g}, {k['L']:.1f} long)")
    I_up = r.T*r.W_UP**3/12
    eps_u = F_n*k["h_arm"]*(r.W_UP/2)/I_up/r.E
    check(eps_u <= 0.02, "upright arm strain at the stop <= 2%", f"{eps_u*100:.2f}%, {eps_u*r.E:.1f} MPa (SF {r.STRENGTH/(eps_u*r.E):.1f})")
    I_k = r.T*r.KEY_H**3/12
    eps_k = F_k*k["a_key"]*(r.KEY_H/2)/I_k/r.E
    check(eps_k <= 0.02, "key arm strain at the stop <= 2%", f"{eps_k*100:.2f}%")
    eps_t = 3*U.TAB_T*STROKE/(2*U.TAB_L**2)
    check(eps_t <= 0.02, "plate tab strain (it stops when the switch bottoms) <= 2%", f"{eps_t*100:.2f}%")
    m_r = rock.volume()*H.PETG
    com = H.to_tm(rock).center_mass
    M_g = m_r*H.G*(g["B"][0] - com[1])                           # CCW (key down) when the mass is forward of the blade
    th_g = M_g*k["L"]/k["EI_b"]
    sag = th_g*float((g["Nc"] - g["B"]) @ g["u"])
    check(abs(sag) < 0.1*r.G, "the rocker's own weight barely moves the nub at rest", f"{sag*1000:+.0f} um ({m_r:.1f} g)")
    # before the nub touches, the blade's moment tips the foot nose-down; the tongue holds the heel
    M_pre = res["G"][1][1]*(g["B"][0] - g["K"][0])
    heel = M_pre/(r.FOOT_FWD + r.FOOT_BACK)
    print(f"      just before the touch the key needs {res['G'][1][1]:.2f} N; the heel hook holds {heel:.2f} N down")
    check(st[1] + F_n*F.S > 0 and F_n*F.C > 0, "during the click every load pushes the foot down and back into its pocket",
          f"down {st[1] + F_n*F.S:.1f} N, back {F_n*F.C:.1f} N")
    return res, phi_c, phi_s, m_r, com


def run_assembly_checks(r, s, F, geo, case, plate_b, base_fb, cut, pocket3, keyinfo, g, slide, cable, plug):
    print("\n15. Assembly and the stand's own paths")
    rock = rocker_solid(r, g)
    worst = 0.0
    for dz in np.arange(25.0, -0.01, -0.5):                 # dropped in, slid forward ...
        worst = max(worst, (rock.translate([0, -slide, dz]) ^ base_fb).volume())
    for dy in np.arange(slide, -0.01, -0.25):               # ... then back, heel under the ledge
        worst = max(worst, (rock.translate([0, -dy, 0]) ^ base_fb).volume())
    check(worst < 1e-3, f"rocker drops in {slide:.2f} forward of home, then slides back under the ledge", f"{worst:.4f} mm^3 in the way")
    up = F.vec([0, 1, 0])
    hoop = F.W(case) + F.W(plate_b)
    worst = max((hoop.translate(list(t*up)) ^ rock).volume() for t in np.arange(0.0, 30.0, 0.5))
    check(worst < 1e-3, "hoop (plate on) slides down its neck past the nub: 30 mm of path", f"{worst:.4f} mm^3")
    fwd = r.G/F.C
    check(r.TONGUE_L > fwd + 0.3, "hoop in: the rocker can't slide forward off its heel hook (the nub meets the plate first)",
          f"{fwd:.2f} of {r.TONGUE_L:g} mm")
    v = (cut ^ keyinfo["mort"]).volume()
    wall = cut.min_gap(keyinfo["mort"], 5.0)
    check(v < 1e-4 and wall >= 1.2, "tier wall between the rocker slot and the mortise >= 1.2", f"{wall:.2f}")
    wk = cut.min_gap(keyinfo["key"], 30.0)
    check(wk >= 1.2, "cable keyhole untouched", f"{wk:.1f} mm away")
    body, shell, boot = plug
    v = sum((m ^ (rock + base_fb)).volume() for m in (body, shell, boot))
    check(v < 1e-3, "plug clear of the rocker and base", f"{v:.4f} mm^3")
    gcab = cable.min_gap(rock, 20.0)
    check((cable ^ rock).volume() < 1e-3 and gcab > 1.0, "cable loop clear of the rocker", f"{gcab:.1f} mm")
    # tier wall behind the pocket, measured in the slices above the lower tier
    tier = circle(s.TIER_R - 1.2).translate([0, geo["Yb"]])
    wmin = 99.0
    for z in (6.0, 9.0, 12.0):
        hole = pocket3.slice(z)
        for wl in np.arange(0.1, 6.0, 0.1):
            if (hole - tier.offset(-wl, Round)).area() > 1e-3:
                wmin = min(wmin, wl - 0.1); break
    check(wmin >= 1.2, "tier wall round the foot's pocket >= 1.2 (inside the top chamfer)", f"{wmin:.1f}")
    # the pad and a fingertip on it
    pad3 = xprism(g["pad"], r.X0, r.X0 + r.PAD_W)
    pb = bbox(pad3)
    finger = m3.Manifold.cylinder(30, 8.0, 8.0, 48).translate([(pb[0, 0] + pb[1, 0])/2, (pb[0, 1] + pb[1, 1])/2, r.PAD_TOP + 0.5])
    v = (finger ^ (F.W(case) + base_fb)).volume()
    gfin = finger.min_gap(F.W(case), 40.0)
    check(v < 1e-3, "a Ø16 fingertip comes straight down onto the key", f"{gfin:.1f} mm from the hoop")


def stability(r, s, b, F, case, plate_b, base_fb, geo, rock, m_r, cable_exit, F_press, K3):
    print("\n16. Stability: with the rocker, the 1 N cable pull, and the key press")
    parts = {"hoop + case": F.W(case), "plate": F.W(plate_b), "base (100% infill)": base_fb, "rocker": rock}
    masses = []
    for nm, m in parts.items():
        g_ = m.volume()*H.PETG
        masses.append((g_, H.to_tm(m).center_mass))
        print(f"      {nm:22s} {g_:5.1f} g")
    masses.append((s.BADGE_G, F.pt([0, 0, 2.5])))
    masses.append((s.PLUG_G, F.pt([0, 23.95 + s.PLUG_L/2, b.port_z])))
    cxy, cr = np.array([0, geo["Yb"]]), s.BASE_R - 0.6
    worst, com, Wt = H.tip_angles(s, F, masses, cxy, cr, cable_exit, 90.0)
    check(worst[0] >= s.MIN_TIP, f"tip angle >= {s.MIN_TIP:g} with the 1 N cable pull", f"worst {worst[0]:.1f} deg toward {worst[1]:.0f} deg")
    # a straight-down press: an extra weight at the key
    pm = masses + [(F_press/H.G, K3)]
    s0 = H.Stand(**{**s.__dict__, "PULL_N": 0.0})
    w0 = H.tip_angles(s0, F, pm, cxy, cr, K3, 90.0)[0]
    inside = math.hypot(K3[0] - cxy[0], K3[1] - cxy[1])
    check(inside < cr and w0[0] >= s.MIN_TIP, f"press {F_press:.1f} N straight down on the key: inside the footprint, can't tip",
          f"key {cr - inside:.0f} mm inside the rim; tip angle {w0[0]:.0f} deg")
    # slanted: the horizontal part must not slide it (friction MU) nor tip it
    W = Wt
    a_max = 0.0
    for a in np.arange(0, 60, 0.25):
        A = math.radians(a)
        if F_press*math.sin(A) > r.MU*(W + F_press*math.cos(A)): break
        a_max = a
    A = math.radians(a_max)
    pm2 = masses + [(F_press*math.cos(A)/H.G, K3)]
    s2 = H.Stand(**{**s.__dict__, "PULL_N": F_press*math.sin(A)})
    w2 = min(H.tip_angles(s2, F, pm2, cxy, cr, K3, d)[0][0] for d in (0, 90, 180, 270))
    check(a_max >= 15.0, f"press may lean {a_max:.0f} deg off vertical before the base slides (mu {r.MU:g}, {W/H.G:.0f} g)",
          f"a finger on a flat key presses within that")
    check(w2 >= s.MIN_TIP, f"leaning {a_max:.0f} deg, the press still can't tip it", f"tip angle {w2:.0f} deg")
    return masses


def main():
    r = Rocker()
    s, b, c, F, feats, case, plate_b, geo_b, base, geo, keyinfo, info, screw, extra = hoop_setup()
    g0 = rocker_geometry(r, b, c, F, geo, 0.0)
    k = springs(r, g0, s)
    d_stop = stroke(r, g0, k, r.G + r.G_TOL)[45, 0] + r.STOP_SPARE      # click at the worst gap, then a little more
    g = rocker_geometry(r, b, c, F, geo, d_stop)
    slide = r.TONGUE_L + r.FIT + 0.15
    base_fb, cut, pocket3 = base_cuts(r, g, base, d_stop/g["a"], slide)
    body, shell, boot, cable, cable_exit = H.cable_and_plug(s, b, F, geo, keyinfo)
    print(f"Front-BOOT rocker: pivot world Y {g['P'][0]:+.2f} Z {g['P'][1]:.2f}; nub arm {g['h']:.1f}, key arm {g['a']:.1f}; "
          f"key stop {d_stop:.2f} mm below rest")
    print("\n--- the hoop's case with the button plate (checks from build_pocketwatch_usb.py) ---")
    H.run_case_checks(b, c, feats, case, plate_b, geo_b)
    U.run_button_checks(b, c, feats, case, plate_b, geo_b)
    res, phi_c, phi_s, m_r, com = run_frontboot_checks(r, s, b, c, F, feats, case, plate_b, geo_b, base_fb, cut, keyinfo,
                                                       g, k, d_stop, slide, cable)
    run_assembly_checks(r, s, F, geo, case, plate_b, base_fb, cut, pocket3, keyinfo, g, slide, cable, (body, shell, boot))
    rock = rocker_solid(r, g)
    K3 = np.array([r.X0 + r.PAD_W/2, g["K"][0], g["K"][1]])
    stability(r, s, b, F, case, plate_b, base_fb, geo, rock, m_r, cable_exit, max(res["G-tol"][3][1], 6.0), K3)

    print()
    export(base_fb, STL + "base.stl", lambda m: m)
    export(rock, STL + "rocker.stl",
           lambda m: m.transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -r.X0]], float)))
    if "--no-render" not in sys.argv:
        renders(r, s, b, c, F, feats, case, plate_b, geo_b, base_fb, g, phi_c, phi_s, (body, shell, boot), cable,
                res["G"][2][0])
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


def side_by_side(paths, out, title):
    import matplotlib.pyplot as plt, matplotlib.image as mpimg
    fig, axs = plt.subplots(1, len(paths), figsize=(9*len(paths)*0.62, 6.2), dpi=110)
    for ax, pth in zip(axs, paths):
        ax.imshow(mpimg.imread(pth)[60:-40, 40:-40]); ax.set_axis_off()
    fig.suptitle(title, fontsize=11)
    fig.subplots_adjust(0, 0, 1, 0.93, 0.0); fig.savefig(out, facecolor="white"); plt.close(fig)
    print("wrote", out)


def renders(r, s, b, c, F, feats, case, plate_b, geo_b, base_fb, g, phi_c, phi_s, plug, cable, click_mm):
    import os, tempfile
    tmp = tempfile.mkdtemp()
    rf = lambda m, L=1.0: m.refine_to_length(L)
    brass, plate_c, dark, white, red, steel, walnut, black, cream, ivory, green, violet = (
        (0.84, 0.67, 0.33), (0.66, 0.50, 0.24), (0.07, 0.07, 0.09), (0.95, 0.95, 0.90), (0.88, 0.22, 0.18),
        (0.75, 0.77, 0.80), (0.36, 0.22, 0.13), (0.15, 0.15, 0.16), (0.96, 0.92, 0.80), (0.94, 0.90, 0.80),
        (0.25, 0.70, 0.35), (0.62, 0.30, 0.80))
    rock = rocker_solid(r, g)
    disc_tab = next(f for f in feats if f.name == "disc + tab").solid()
    ticks, hands, sec_, hub = H.dial(b)
    body, shell, boot = plug
    face = [(rf(F.W(disc_tab)), dark), (rf(F.W(ticks), 0.6), cream), (rf(F.W(hands), 0.6), cream),
            (rf(F.W(sec_), 0.6), red), (rf(F.W(hub), 0.6), brass)]
    gear = [(rf(body), black), (rf(shell, 0.6), steel), (rf(boot), black), (rf(cable, 1.5), black)]
    stand = [(rf(F.W(case)), brass), (rf(F.W(plate_b)), plate_c), (rf(base_fb, 1.6), walnut), (rf(rock, 0.8), ivory)]
    render(stand + face + gear, OUT + "01-hero.png", elev=16, azim=-50, zoom=1.2,
           title="Front-BOOT hoop: press the ivory key on the base, BOOT clicks. Nothing touches the glass.")
    render(stand + gear, OUT + "02-back.png", elev=22, azim=55, zoom=1.2, light=(0.45, 0.75, 0.5),
           title="From behind: the rocker's arm rises to a nub just off the plate's flush BOOT tab")

    # sections on the nub's middle plane, at rest and at the click (rigid pose: nub on the tab pushed a full stroke)
    xs = r.X0 + r.NUB_W/2
    tab_reg = prism(geo_b["tab"].offset(0.02, Round), -2, geo_b["Z_CASE"] + 2)
    post = plate_b ^ geo_b["post_cyl"]
    plate_np = plate_b - geo_b["post_cyl"]
    fs = [(f.solid(), dark if f.name == "disc + tab" else green if f.name.startswith(c.BUTTON) else white)
          for f in feats if not f.name.startswith("plug")]
    D = g["D"]
    box = m3.Manifold.cube([30, 16, 16]).translate([0, D[0] - 8, D[1] - 8])
    for tag, phi, push in (("rest", 0.0, 0.0), ("pressed", phi_c, STROKE)):
        moved = lambda m: F.W(m - tab_reg) + F.W((m ^ tab_reg).translate([0, 0, -push]))
        parts = [(F.W(case), brass), (moved(plate_np), plate_c), (moved(post), violet), (base_fb, walnut),
                 (rot3(rock, g["P"], phi), ivory)] + [(F.W(m), col) for m, col in fs]
        cut, det = [], []
        for m, col in parts:
            m = m.trim_by_plane([1, 0, 0], xs)
            if m.is_empty(): continue
            cut.append((rf(m, 1.2), col))
            d = m ^ box
            if not d.is_empty(): det.append((rf(d, 0.4), col))
        render(cut, os.path.join(tmp, "full.png"), elev=0, azim=180, zoom=1.15)
        render(det, os.path.join(tmp, "det.png"), elev=0, azim=180, zoom=1.0)
        if tag == "rest":
            ttl = (f"Section on the nub (X {xs:.1f}), at rest: nub {r.G:g} off the tab, post {REST_CLR_TXT} off BOOT (green), "
                   f"key {g['pad_bot'] - H.Stand().BASE_T:.1f} above its stop")
        else:
            ttl = (f"Pressed (true scale): the nub has pushed the tab {STROKE:.2f}, the post (violet) is on BOOT. "
                   f"Key travel {click_mm:.1f} mm to the click, stop at {g['pad_bot'] - H.Stand().BASE_T:.1f}")
        side_by_side([os.path.join(tmp, "full.png"), os.path.join(tmp, "det.png")], OUT + f"section-{tag}.png", ttl)

    up, back = F.vec([0, 1, 0]), F.vec([0, 0, 1])
    mv = lambda m, v: m.translate(list(v))
    hoop_up = 40*up
    ex = [(rf(mv(F.W(case), hoop_up)), brass), (rf(mv(F.W(disc_tab), hoop_up + 24*back)), dark),
          (rf(mv(F.W(plate_b), hoop_up + 42*back)), plate_c), (rf(base_fb, 1.6), walnut),
          (rf(rock.translate([0, -r.TONGUE_L - 0.3, 16]), 0.8), ivory)]
    render(ex, OUT + "exploded.png", elev=14, azim=-35, zoom=1.0,
           title="Assembly: rocker into the base (drop, slide back) -> badge and plate into the hoop -> hoop down its neck")

    lay_h = case.translate([0, 0, c.LIP_T])
    pl = plate_b.rotate([0, 180, 0]).translate([0, 0, geo_b["Z_CASE"]])
    rk = rock.transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -r.X0]], float))
    rb = bbox(rk)
    lay = [(rf(lay_h), brass), (rf(pl.translate([62, 4, 0])), plate_c),
           (rf(base_fb.translate([0, -96, 0]), 1.6), walnut),
           (rf(rk.translate([58 - rb[0, 0], -70 - rb[0, 1], 0]), 0.8), ivory)]
    render(lay, OUT + "print-layout.png", elev=38, azim=-70, zoom=1.1,
           title="Print: hoop + case bezel down, plate flat, new base flat (100% infill), rocker on its side. No supports.")


if __name__ == "__main__":
    main()
