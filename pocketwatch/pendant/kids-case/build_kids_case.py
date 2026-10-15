#!/usr/bin/env python3
"""
Kids case for the 1.28 badge: the pendant without the twist-lock, and a back plate whose BOOT button is one big
flap. Two printed parts.

  case        the pendant case (12 o'clock flat, USB-C sticking out, snap groove, pry notch) without the lock
              grooves.
  back plate  the pendant's plate with the U-slot tab replaced by a flap: a strip along BOOT's y, rooted at
              x = F_ROOT, cut free by two slits out through the plate's edge. A pole under it clicks BOOT;
              pressed on, a foot under its outer end lands on the case step: the stop.

Run from the repo root with ~/.venvs/cad/bin/python. --no-render for a fast check run.
"""
import sys, math, itertools
sys.path.insert(0, "pocketwatch")
sys.path.insert(0, "pocketwatch/pendant")
from dataclasses import dataclass
import numpy as np, manifold3d as m3
import build_pocketwatch_usb as U
from build_pocketwatch import Badge, Case, Round, circle, rect, prism, union, bbox, check, FAILS, export, render
from build_pendant import Pendant, MAT, case_body, run_pry_checks

OUT = "pocketwatch/pendant/kids-case/renders/"
STL = "stl/pocketwatch/pendant/kids-case/"


@dataclass(frozen=True)
class Flap:
    """The BOOT flap: a strip centred on BOOT's y, from its root line in -x out through the plate's edge."""
    F_W: float = 8.0            # across y
    F_ROOT: float = 8.0         # root line x
    F_T: float = 1.2            # thinned from the badge side (MIN_WALL); the back face stays flush
    FOOT_IN: float = 0.25       # foot's inner edge outside the bore: it lands on the step, never in the bore
    # the foot runs along the flap's edge arc from its corner by the pole out to here, not to the tip: a stop that
    # far out needs ~1.2 of travel, and 2.4 of plate less F_T leaves no room for a foot
    FOOT_X: float = -16.0
    # the step under the overhang past the foot is cut this much lower (one layer), so the far tip, which keeps on
    # dropping past the foot, never lands before it: a tip landing first loads the bottomed switch
    RELIEF: float = 0.3


def chord(f, py, r_edge, x):
    """Flap width across y at x: the strip, cut by the plate's edge circle."""
    h = np.sqrt(np.clip(r_edge**2 - np.asarray(x)**2, 0, None))
    return np.clip(np.minimum(py + f.F_W/2, h) - np.maximum(py - f.F_W/2, -h), 0, None)


def slit_sides(f, py):
    """Each slit edge's y and the side (+1: +y) its plate lies on: fixed, flap, flap, fixed."""
    y_lo, y_hi, gap = py - f.F_W/2, py + f.F_W/2, U.TAB_GAP
    return ((y_lo - gap, -1), (y_lo, +1), (y_hi, -1), (y_hi + gap, +1))


def wedge_x(r, y_e, sgn, W):
    """A slit edge at y_e running out through the plate's edge circle r (on the -x side) at an acute angle leaves
    the plate beside it, on side sgn, under W wide: cut it off square at the x returned. None if the angle is obtuse."""
    y_far = y_e + sgn*(W + 0.05)
    x_c, x_w = -math.sqrt(r*r - y_e*y_e), -math.sqrt(max(r*r - y_far*y_far, 0.0))
    return x_w if x_w > x_c else None


def tip_x(f, py, r_edge, W):
    """The flap's farthest point from its root: where its edge nearest y = 0 meets the plate's edge, or where the
    flap is cut square there if it is an acute wedge."""
    y0, y1 = py - f.F_W/2, py + f.F_W/2
    if y0 < 0 < y1:
        return -r_edge
    y_n, sgn = (y1, -1) if abs(y1) < abs(y0) else (y0, +1)
    x_w = wedge_x(r_edge, y_n, sgn, W)
    return -math.sqrt(r_edge**2 - y_n**2) if x_w is None else x_w


def flap_model(f, p, c, px, py, r_edge, E=MAT.E, drop=None):
    """The flap as an Euler beam from its root, as wide as its chord. Three supports below it: the switch under the
    pole (a), pushing back F_SW until it bottoms STROKE down; the foot (d, its point farthest from the root),
    landing g down; the far tip (d_tip) over the step, landing drop + RELIEF down. drop is the flap's underside
    above the surface the foot lands on: PLATE_T - F_T unless given."""
    drop = c.PLATE_T - f.F_T if drop is None else drop
    x_tip = tip_x(f, py, r_edge, c.MIN_WALL)
    a, d, d_tip = f.F_ROOT - px, f.F_ROOT - max(x_tip, f.FOOT_X), f.F_ROOT - x_tip
    s = np.linspace(0, d_tip, 2401)
    w = np.maximum(chord(f, py, r_edge, f.F_ROOT - s), 1e-3)
    EI = E*w*f.F_T**3/12
    flex = lambda i, j: np.trapezoid(np.clip(i - s, 0, None)*np.clip(j - s, 0, None)/EI, s)
    faa, fad, fdd = flex(a, a), flex(a, d), flex(d, d)
    P_click = (c.STROKE + faa*p.F_SW)/fad
    yd_click = fdd*P_click - fad*p.F_SW
    at = np.array([a, d, d_tip])
    C = np.array([[flex(i, j) for j in at] for i in at])
    pre = np.array([p.F_SW, 0.0, 0.0])
    contacts = sorted(itertools.product((False, True), repeat=3), key=sum)

    def press(F, b, g):
        """F at b from the root, foot g above the step: switch force R, foot S, tip T, peak strain, shape.
        A support that has come its gap down is a rigid prop and its force is free; one that has not pushes its preload."""
        gap = np.array([c.STROKE, g, drop + f.RELIEF])
        Fb = np.array([flex(i, b) for i in at])*F
        for on in map(np.array, contacts):
            Rs = pre.copy()
            if on.any():
                Rs[on] = np.linalg.solve(C[np.ix_(on, on)], Fb[on] - gap[on] - C[np.ix_(on, ~on)] @ pre[~on])
            y = Fb - C @ Rs
            if np.all(Rs[on] >= pre[on] - 1e-9) and np.all(y[~on] <= gap[~on] + 1e-9):
                break
        M = F*np.clip(b - s, 0, None) - sum(R*np.clip(x - s, 0, None) for R, x in zip(Rs, at))
        eps = float(np.max(np.abs(6*M/(E*w*f.F_T**2))))
        cum = lambda v: np.concatenate([[0.0], np.cumsum((v[1:] + v[:-1])/2*np.diff(s))])
        slope = cum(M/EI)
        return dict(R=float(Rs[0]), S=float(Rs[1]), T=float(Rs[2]), eps=eps, ya=float(y[0]), yd=float(y[1]), y_tip=float(y[2]),
                    s=s, slope=slope, defl=cum(slope))

    return dict(a=a, d=d, d_tip=d_tip, faa=faa, fad=fad, fdd=fdd, P_click=P_click, yd_click=yd_click, press=press)


def flap_cases(f, p, c, px, py, r_edge, drop=None):
    """g_stop, fixed at nominal E: the foot's travel at the click plus SPARE of pole push, scaled out to the foot.
    Then the outer end pressed onto the stop at E low / nominal / high, with the foot printed TOL early or late. A
    hard press at the foot goes into the stop, so the switch force is whatever it was when the foot landed."""
    nom = flap_model(f, p, c, px, py, r_edge, drop=drop)
    g_stop = nom["yd_click"] + p.SPARE*nom["d"]/nom["a"]
    out = {}
    for tag, E in (("lo", MAT.E_lo), ("nom", MAT.E), ("hi", MAT.E_hi)):
        m = flap_model(f, p, c, px, py, r_edge, E, drop)
        land = {k: m["press"](p.F_PRESS, m["d"], g_stop + dg) for k, dg in (("early", -p.TOL), ("nom", 0.0), ("late", p.TOL))}
        out[tag] = dict(m=m, land=land, early=g_stop - p.TOL - m["yd_click"])
    return g_stop, out


# ---- geometry ---------------------------------------------------------------
def flap_plate(b, c, p, f, clr):
    """The pendant's back plate (U.build: snap skirt and bead, header guides, keyed by the tab pocket) with the
    U-slot tab replaced by the flap. Skirt, bead and guides come off the flap and stay on the fixed plate.
    g_stop comes from the nominal plate's model whatever clr is, so the roomy plate's foot is the same height."""
    feats, _, plate, geo = U.build(b, c, clr)
    FLOOR, Z_CASE, R_BORE = geo["FLOOR"], geo["Z_CASE"], geo["R_BORE"]
    px, py = geo["sw"][c.BUTTON], b.sw_y
    g_stop, cs = flap_cases(f, p, c, px, py, geo["R_REAR"] - U.PLATE_DISC_CLR)
    disc = (circle(geo["R_REAR"]) + feats[0].grown()).offset(-clr, Round)      # as U.build's plate disc
    y_lo, y_hi, gap = py - f.F_W/2, py + f.F_W/2, U.TAB_GAP
    slit = lambda y0: rect(-60, f.F_ROOT, y0, y0 + gap) + m3.CrossSection.circle(gap/2, 24).translate([f.F_ROOT, y0 + gap/2])
    slits = slit(y_lo - gap) + slit(y_hi)
    # the flap's side of the slits' centre lines: thinning and selecting with it shares no face with the fixed plate
    sel = rect(-60, f.F_ROOT, y_lo - gap/2, y_hi + gap/2)
    W, r_disc = c.MIN_WALL, geo["R_REAR"] - clr
    wedges = [rect(-60, x_w, *sorted((y_e, y_e + sgn*(W + 0.35)))) for y_e, sgn in slit_sides(f, py)
              if (x_w := wedge_x(r_disc, y_e, sgn, W)) is not None]
    holes = slits
    for w_ in wedges:
        holes += w_
    flap = (disc ^ sel) - holes
    plate -= geo["post_cyl"]
    plate -= prism(holes, -1, Z_CASE + 1)
    z_under = Z_CASE - f.F_T
    plate -= prism(sel + rect(f.F_ROOT - 1, f.F_ROOT + gap/2, y_lo - gap/2, y_hi + gap/2), -1, z_under)   # to the slits' round ends
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    pole_cyl = m3.Manifold.cylinder(z_under + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([px, py, tip_z])
    pole = pole_cyl - union(k.keepout(c.FLOAT) for k in feats if not k.name.startswith(c.BUTTON))
    foot_xy = (flap.offset(-0.05, Round) ^ rect(f.FOOT_X, 60, -60, 60)) - circle(R_BORE + f.FOOT_IN)   # off the flap's sides: no shared faces
    foot = prism(foot_xy, FLOOR + g_stop, z_under + 0.01)
    plate += pole + foot
    y_flat = b.tip_y - c.RAD_CLR - p.PORT_OUT                       # every part stops at the pendant's flat
    plate = plate.trim_by_plane([0, -1, 0], -y_flat)
    geo.update(py=py, sel=sel, pole=pole, foot=foot, z_under=z_under, z_ax=Z_CASE - f.F_T/2, y_flat=y_flat, R_DISC=geo["R_REAR"] - clr,
               g_stop=g_stop, cs=cs)
    return feats, plate, geo


def build(b, c, p, f, clr=U.PLATE_DISC_CLR):
    feats, plate, geo = flap_plate(b, c, p, f, clr)
    case = case_body(b, c, p, feats, geo, geo["Z_CASE"])
    relief = (circle(geo["R_REAR"] - 0.1) ^ geo["sel"]) ^ rect(-60, f.FOOT_X - 0.3, -60, 60)   # 0.1 off the counterbore wall: no shared face
    case -= prism(relief, geo["FLOOR"] - f.RELIEF, geo["FLOOR"] + 0.01)
    return feats, case, plate, geo


def bend(geo, f, m, st):
    """m on the flap deflected as the model's state st: each x drops by the beam's deflection there and its
    section turns with the slope about the neutral axis. A rigid turn would push the pole past the bottomed switch."""
    s, defl, slope, z_ax = st["s"], st["defl"], st["slope"], geo["z_ax"]
    def move(v):
        d = np.clip(f.F_ROOT - v[:, 0], 0, None)
        out = np.array(v, float)
        out[:, 0] -= (v[:, 2] - z_ax)*np.interp(d, s, slope)
        out[:, 2] -= np.interp(d, s, defl)
        return out
    return m.refine_to_length(0.5).warp_batch(move)


def states(geo, p):
    """Nominal E, pressed at the foot: the click; landed on the stop; landed with the foot printed TOL late.
    Once both supports are fixed in height the shape no longer depends on E."""
    m, g = geo["cs"]["nom"]["m"], geo["g_stop"]
    return dict(click=m["press"](m["P_click"], m["d"], g), stop=m["press"](p.F_PRESS, m["d"], g),
                late=m["press"](p.F_PRESS, m["d"], g + p.TOL))


# ---- checks ----------------------------------------------------------------
def run_kids_checks(b, c, p, f, feats, case, plate, geo):
    FLOOR, Z_CASE = geo["FLOOR"], geo["Z_CASE"]
    W = c.MIN_WALL
    flap_s = plate ^ prism(geo["sel"] ^ rect(-60, f.F_ROOT - 0.3, -60, 60), -5, Z_CASE + 5)   # pole and foot included
    fixed = plate - prism(geo["sel"], -5, Z_CASE + 5)
    act = next(k for k in feats if k.name == f"{c.BUTTON} actuator").solid()
    others = [k for k in feats if k.name != f"{c.BUTTON} actuator"]
    g_stop, cs = geo["g_stop"], geo["cs"]
    m = cs["nom"]["m"]
    st = states(geo, p)
    flap_t = bend(geo, f, flap_s, st["stop"])

    print("\n6. Case: the pendant outline without the twist-lock, port sticking out")
    mouth = b.tip_y - c.RAD_CLR                                      # receptacle mouth with the board pushed fully down
    overmold = prism(rect(-15, 15, mouth, mouth + 25), -10, 30)
    for nm, s in (("case", case), ("back plate", plate), ("flap pressed to the stop", flap_t)):
        v, g = (overmold ^ s).volume(), overmold.min_gap(s, 5)
        check(v < 1e-3 and g >= p.PORT_OUT - 0.01, f"overmold on the pushed-down port clears the {nm}", f"gap {g:.2f}")

    print(f"\n7. Flap: {f.F_W:g} wide from x {f.F_ROOT:+g} out through the plate's edge, {f.F_T:g} thick, slits {U.TAB_GAP}")
    check(f.F_T >= W - 1e-9, f"flap >= {W} thick", f"{f.F_T:g}")
    thinnest = thinnest_beside_slits(plate.slice(Z_CASE - 0.15), f, geo["py"], W, -21.0)
    check(thinnest >= W - 0.02, f"plate beside each slit >= {W} wide wherever it continues", f"{thinnest:.2f}")
    h1 = next(h for h in geo["hdrs"] if h.name.startswith("header H1"))
    x0, y0, x1, y1 = h1.outline.bounds()
    i, o = c.HDR_CLR, c.HDR_CLR + c.GUIDE_WALL
    for wn, w in {"-x wall": rect(x0 - o, x0 - i, y0, y1), "+x wall": rect(x1 + i, x1 + o, y0, y1)}.items():
        g = fixed ^ prism(w, -5, FLOOR)
        span = bbox(g)[1, 1] - bbox(g)[0, 1] if not g.is_empty() else 0.0
        check(span >= 5.0, f"H1 {wn} on the fixed plate (pole and flap left out) grips >= 5 of y", f"{span:.1f}")
    foot_h = geo["z_under"] - FLOOR - g_stop
    check(foot_h >= 0.3 - 1e-6, "foot at least a layer (0.3) tall", f"{foot_h:.2f}")

    print(f"\n8. Pressed at the foot, the flap bent as the model has it (pole down {c.STROKE:.2f}, foot down {g_stop:.2f})")
    g = bend(geo, f, flap_s - geo["pole"], st["click"]).min_gap(case, 2.0)
    check(g > 0.05, "at the click neither the foot nor the far tip has landed", f"{g:.2f} to go")
    foot_s = bend(geo, f, geo["foot"], st["stop"])
    v, g = (foot_s ^ case).volume(), foot_s.min_gap(case, 1.0)
    check(v < 2e-2 and g < 0.02, "at the stop the foot sits on the case step", f"gap {g:.3f}, overlap {v:.4f} mm^3")
    v = (bend(geo, f, geo["pole"], st["stop"]) ^ act).volume()
    check(v > 1e-3, f"at the stop the pole has reached the {c.BUTTON} actuator", f"{v:.3f} mm^3")
    tip = flap_s ^ prism(rect(-60, f.FOOT_X - 0.05, -60, 60), -5, Z_CASE + 5)   # the overhang past the foot, off its face
    for tag, nm in (("stop", ""), ("late", f", foot {p.TOL} late")):
        body = bend(geo, f, flap_s - geo["foot"] - tip, st[tag])
        g = body.min_gap(case, 2.0)
        check((body ^ case).volume() < 1e-3 and g > 0.05, f"nothing but the foot and the far tip reaches the case{nm}", f"gap {g:.2f}")
        tb = bend(geo, f, tip, st[tag])
        v, g = (tb ^ case).volume(), tb.min_gap(case, 1.0)
        check(v < 2e-2, f"the far tip rests on the step at most (a second stop){nm}",
              f"gap {g:.2f}, overlap {v:.4f} mm^3, tip takes {st[tag]['T']:.1f} N")
    for k in others:
        g = flap_t.min_gap(k.solid(), 3.0)
        check((flap_t ^ k.solid()).volume() < 1e-3 and g > 0.05, f"at the stop the flap clears {k.name}", f"gap {g:.2f}")
    g = flap_t.min_gap(fixed, 2.0)
    check((flap_t ^ fixed).volume() < 1e-3 and g > 0.05, "at the stop the flap clears the fixed plate", f"gap {g:.2f}")

    print(f"\n9. Forces and strains: {MAT.NAME}, E {MAT.E:g} +-{100*MAT.E_TOL:g}%, flexing parts <= {100*MAT.FLEX_MAX:g}%")
    x_safe = f.F_ROOT - force_checks(f, p, c, cs, g_stop)
    g_sl = c.PLATE_T - 0.3*round((c.PLATE_T - g_stop)/0.3)
    R_sl = max(v["m"]["press"](p.F_PRESS, m["d"], g_sl)["R"] for v in cs.values())
    print(f"      as sliced at 0.3 layers the foot's underside lands {g_sl:.2f} above FLOOR; switch force on the stop then <= {R_sl:.1f} N")
    return dict(x_safe=x_safe)


def thinnest_beside_slits(face, f, py, W, x_from):
    """Narrowest strip of part beside each slit edge, probed across it every 0.1 from x_from to the root wherever the
    part starts at the edge. face: the part's section, in the flap's frame (root at +x)."""
    thinnest = W + 0.3
    for y_e, sgn in slit_sides(f, py):
        for x in np.arange(x_from, f.F_ROOT - 0.3, 0.1):
            if (face ^ rect(x - 0.01, x + 0.01, *sorted((y_e + sgn*0.01, y_e + sgn*0.06)))).area() > 1e-4:
                thinnest = min(thinnest, (face ^ rect(x - 0.01, x + 0.01, *sorted((y_e, y_e + sgn*(W + 0.3))))).area()/0.02)
    return thinnest


def force_checks(f, p, c, cs, g_stop, where=None):
    """The model's limit checks and KNOWN WEAKNESS lines. where(s) names the point s from the root.
    Returns the distance from the root past which a hard press keeps the switch under F_SW_MAX."""
    where = where or (lambda s: f"x {f.F_ROOT - s:+.1f}")
    m = cs["nom"]["m"]
    a, d, d_tip = m["a"], m["d"], m["d_tip"]
    print(f"      beam from the root: pole at {a:.1f}, stop at {d:.1f}, tip at {d_tip:.1f}; "
          f"g_stop {g_stop:.2f} = foot travel at the click {m['yd_click']:.2f} + SPARE {p.SPARE} x {d/a:.2f}")
    early = min(v["early"] for v in cs.values())
    check(early >= 0.02, f"clicks at any E even if the foot lands {p.TOL} early", f"{early:.3f} foot travel to spare")
    nom = cs["nom"]["land"]["nom"]
    R_w = max(v["land"]["late"]["R"] for v in cs.values())
    eps_w = max(v["land"]["late"]["eps"] for v in cs.values())
    check(nom["R"] <= p.F_SW_MAX, f"switch force on the stop <= {p.F_SW_MAX:g} N, nominal", f"{nom['R']:.1f} N")
    check(R_w <= p.F_SW_WORST, f"switch force on the stop <= {p.F_SW_WORST:g} N, worst ({p.TOL} late, any E)", f"{R_w:.1f} N")
    check(nom["eps"] <= MAT.FLEX_MAX, f"flap strain on the stop <= {100*MAT.FLEX_MAX:g}%, nominal", f"{100*nom['eps']:.2f}%")
    check(eps_w <= p.TAB_WORST, f"flap strain on the stop <= {100*p.TAB_WORST:g}%, worst", f"{100*eps_w:.2f}%")
    check(m["P_click"] <= p.F_EASY, f"press force to click, at the foot <= {p.F_EASY:g} N", f"{m['P_click']:.2f} N")
    lo = cs["lo"]["m"]
    for nm, bb in (("on the pole", a), ("mid-flap", d_tip/2)):
        R_n, R_lo = m["press"](p.F_PRESS, bb, g_stop)["R"], lo["press"](p.F_PRESS, bb, g_stop)["R"]
        print(f"  [KNOWN WEAKNESS] {p.F_PRESS:g} N {nm} ({where(bb)}): no stop, switch takes {R_n:.1f} N ({R_lo:.1f} at low E)")
    bs = np.linspace(0, d_tip, 241)
    worst_R = [max(v["m"]["press"](p.F_PRESS, bb, g_stop + p.TOL)["R"] for v in cs.values()) for bb in bs]
    ok = [bb for bb, R in zip(bs, worst_R) if R > p.F_SW_MAX]
    s_safe = max(ok) if ok else 0.0
    print(f"      a {p.F_PRESS:g} N press keeps {c.BUTTON} <= {p.F_SW_MAX:g} N (any E, foot late) only outboard of {where(s_safe)}")
    for F in (p.F_EASY, p.F_PRESS):
        e = max(v["m"]["press"](F, d_tip, g_stop + dg)["eps"] for v in cs.values() for dg in (-p.TOL, p.TOL))
        print(f"      {F:g} N on the very tip, past the foot: flap strain {100*e:.2f}% (worst E and foot)")
    return s_safe


# ---- renders ---------------------------------------------------------------
def renders(b, c, p, f, feats, case, plate, geo):
    D = lambda m: m.rotate([90, 0, 0]).refine_to_length(1.0)        # badge +y up, glass toward the viewer at azim 90
    shell, back_c, dark, white, green, violet, red = ((0.30, 0.62, 0.78), (0.20, 0.45, 0.62), (0.10, 0.10, 0.11),
        (0.95, 0.95, 0.90), (0.25, 0.70, 0.35), (0.62, 0.30, 0.80), (0.85, 0.25, 0.20))
    Z_CASE = geo["Z_CASE"]
    fs = {k.name: k.solid() for k in feats if not k.name.startswith("plug")}
    colour = lambda n: dark if n == "disc + tab" else green if n.startswith(c.BUTTON) else white
    flap_s = plate ^ prism(geo["sel"] ^ rect(-60, f.F_ROOT - 0.3, -60, 60), -5, Z_CASE + 5)
    fixed = plate - prism(geo["sel"], -5, Z_CASE + 5)
    flap_np = flap_s - geo["pole"] - geo["foot"]
    pole, foot = plate ^ geo["pole"], plate ^ geo["foot"]
    render([(D(case), shell), (D(fixed), back_c), (D(flap_np), violet)], OUT + "back.png", elev=20, azim=-90,
           title=f"From the back: the BOOT flap (violet), {f.F_W:g} wide, root at x {f.F_ROOT:+g}; press its left end")
    render([(D(fixed), back_c), (D(flap_np), violet), (D(pole), green), (D(foot), red)], OUT + "flap-underside.png",
           elev=30, azim=60, light=(0.35, 0.8, 0.45), title="Back plate from the badge side: pole (green) over BOOT, foot (red) under the flap's outer end")

    st = states(geo, p)["stop"]
    rin, red_ = geo["R_BORE"] + f.FOOT_IN, geo["R_DISC"]
    y0 = -(math.sqrt(rin**2 - f.FOOT_X**2) + math.sqrt(red_**2 - f.FOOT_X**2))/2   # through the foot's far edge and the pole
    box = m3.Manifold.cube([34, 8, 9.5]).translate([-23, y0, 3.5])         # shallow in y: render() scales to the largest extent
    detail = m3.Manifold.cube([12, 8, 8]).translate([-20, y0, 4.5])     # the foot, step, pole and switch only
    def section(pressed, path, title, box=box):
        sw = (lambda m: bend(geo, f, m, st)) if pressed else (lambda m: m)
        act = fs[f"{c.BUTTON} actuator"]
        a = act.trim_by_plane([0, 0, -1], -(b.pcb_back_z + b.sw_cap_h - c.SW_TRAVEL)) if pressed else act
        parts = [(case, shell), (fixed, back_c), (sw(flap_np), violet), (sw(pole), green), (sw(foot), red), (a, green)] + \
                [(s, colour(n)) for n, s in fs.items() if not n.endswith("actuator")]
        cut = []
        for m, col in parts:
            m = (m.trim_by_plane([0, 1, 0], y0) ^ box).refine_to_length(0.6)
            if not m.is_empty(): cut.append((m, col))
        render(cut, path, elev=0, azim=-90, title=title, figsize=(12, 7), zoom=1.6)
    rest_t = f"at rest: pole {c.REST_CLR} over BOOT, foot (red) {geo['g_stop']:.2f} over the step"
    press_t = f"pressed at the foot to the stop, flap bent as modelled: foot on the step, pole {c.STROKE:.2f} down on BOOT"
    section(False, OUT + "section-rest.png", f"Section at y {y0:+.1f}, through the pole and the foot, {rest_t}")
    section(True, OUT + "section-pressed.png", f"Section at y {y0:+.1f}, {press_t}")
    section(False, OUT + "section-detail-rest.png", f"Detail, {rest_t}", detail)
    section(True, OUT + "section-detail-pressed.png", f"Detail, {press_t}", detail)

    lay = [(case.translate([0, 0, c.LIP_T]), shell, -26), (plate.rotate([0, 180, 0]).translate([0, 0, Z_CASE]), back_c, 26)]
    render([(m.translate([dx, 0, 0]).refine_to_length(1.5), col) for m, col, dx in lay], OUT + "print-layout.png",
           elev=32, azim=-70, title="Print as exported, no supports: case bezel down, back plate back face down",
           figsize=(12, 9), zoom=1.6)
    E = 24.0
    ex = [(case, shell), (fixed.translate([0, 0, 2*E]), back_c), (flap_np.translate([0, 0, 2*E]), violet),
          (pole.translate([0, 0, 2*E]), green), (foot.translate([0, 0, 2*E]), red)] + \
         [(s.translate([0, 0, E]), colour(n)) for n, s in fs.items()]
    render([(D(m), col) for m, col in ex], OUT + "exploded.png", elev=14, azim=-32,
           title="Exploded from the back: case, badge, back plate with the BOOT flap")


# ---- main ------------------------------------------------------------------
def main():
    b, c, p, f = Badge(), Case(), Pendant(), Flap()
    feats, case, plate, geo = build(b, c, p, f)
    m = geo["cs"]["nom"]["m"]
    mass = {k: s.volume()*MAT.RHO for k, s in (("case", case), ("back plate", plate))}
    print(f"Kids case Ø{2*geo['R_OUT']:.2f} x {bbox(case)[1, 2] - bbox(case)[0, 2]:.2f}; flap {f.F_W:g} wide from x {f.F_ROOT:+g}, "
          f"{f.F_T:g} thick; foot {geo['g_stop']:.2f} over the step; click {m['P_click']:.1f} N at the foot; "
          + ", ".join(f"{k} {g:.1f} g" for k, g in mass.items()) + " (solid)")
    U.run_checks(b, c, feats, case, plate, geo)
    run_kids_checks(b, c, p, f, feats, case, plate, geo)
    _, plate_r, geo_r = flap_plate(b, c, p, f, U.PLATE_DISC_CLR_ROOMY)
    run_pry_checks(10, c, p, case, {"back plate": (plate, geo["R_DISC"]), "roomy back plate": (plate_r, geo_r["R_DISC"])}, geo)
    print()
    export(case, STL + "Kids case - case.stl", lambda m_: m_.translate([0, 0, c.LIP_T]))
    flip = lambda m_: m_.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]])
    export(plate, STL + "Kids case - back plate (flap).stl", flip)
    export(plate_r, STL + "Kids case - back plate (flap, roomy).stl", flip)
    if "--no-render" not in sys.argv:
        renders(b, c, p, f, feats, case, plate, geo)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
