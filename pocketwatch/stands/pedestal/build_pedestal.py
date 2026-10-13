#!/usr/bin/env python3
"""
Desk pebble: the USB-only pocketwatch case fused into one solid pedestal.

One printed body plus the existing BOOT-hole back plate. The face leans back THETA degrees.
The crown (USB-C) points down into the body; the plug lies in a trough open to the back, and
the cable bends once and leaves under the rear of the foot, lying on the desk.

Print orientation is the whole trick: the body prints FRONT FACE DOWN. The fused case is then
on the bed exactly as the printed-and-proven USB-only case was (bezel down), so none of its
features change print direction. Everything else is either a vertical wall in that
orientation or faces upward, so nothing needs supports. It also means nothing may stand
in front of the face plane, so there is no projecting visor. The face sits in a
cup with a 45-degree trim cone around the glass instead.

Two shape languages share every functional cut (case, trough, cable, access):
  puck    the watch as a round puck on its crown stem, on a low plinth square to the face  (FINAL)
  wedge   a pod cylinder on a flared base with a 42-degree buttress behind (mantel clock)  (alternate)

Frames: badge frame = print frame (origin glass centre, +y toward the tab = DOWN the face,
+z backward = UP off the bed when printing). World: X right as you face it, Y away from
you, Z up, desk at Z = 0. Run from the repo root with ~/.venvs/cad/bin/python.
"""
import sys, math
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3, trimesh
import build_pocketwatch_usb as usb
from build_pocketwatch import (Badge, Case, Round, SEG, circle, rect, prism, union, chamfered, bbox, check,
                               FAILS, export, render)

STL = "stl/pocketwatch/stands/pedestal/"
PNG = "pocketwatch/stands/pedestal/renders/"

# ---- choices --------------------------------------------------------------------
THETA = 20.0              # face leans back from vertical
PLUG_L, PLUG_W, PLUG_T = 22.0, 12.0, 8.0   # straight USB-C overmold outside the case (brief)
PLUG_CLR = 0.5            # trough around the overmold, per side
CABLE_D, R_BEND = 4.5, 9.0   # cable, and the one bend it makes (centreline), ~2x its diameter
CABLE_SLOT = 6.0          # groove under the foot
R_CUP, CUP_D, CUP_CH = 21.5, 1.5, 0.8   # cup in front of the glass: 45-degree trim cone, then a short bore
RING = 5.0                # body wall around the cup at the face
FRONT_CH, BACK_CH = 1.8, 2.0
ACCESS = 3.0              # clear radius past the case all round, behind it: plate, thumb, stylus
NOTCH_W = 6.0             # pry notch at the top of the plate rim
FLUTES, FLUTE_P, FLUTE_W = 5, 3.6, 2.0   # crown knurl: V-flutes along the stem's face, 45-degree walls (3 layers deep)
SHAPES = {   # pod: around the case, slab-deep only; base: runs back into a foot; back: how the foot ends
    "wedge": dict(back="slope", RIDGE_H=27.0, BETA=42.0, W_T=40.0, Y_T=-4.0, W_B=76.0, R_POD=27.5),
    "puck":  dict(back="square", W_STEM=24.0, W_STEM_B=30.0, Y_PLINTH=48.0, W_PL_T=70.0, W_PL_B=80.0),
}
FINAL = "puck"

# stability model (assumptions, printed with the result)
RHO, INFILL, T_SHELL = 1.27, 0.20, 1.8     # PETG g/cm^3; 20% infill; 3 perimeters of 0.6
BADGE_G, PLUG_G, PULL_N, MIN_TIP = 20.0, 8.0, 1.0, 20.0

S, C = math.sin(math.radians(THETA)), math.cos(math.radians(THETA))
R_BW = np.array([[1, 0, 0], [0, -S, C], [0, -C, -S]])     # world = R_BW @ badge + (0,0,H)


class Frame:
    """Badge (print) frame <-> world frame."""
    def __init__(self, H): self.H = H
    def w(self, m): return m.rotate([-(90 + THETA), 0, 0]).translate([0, 0, self.H])
    def b(self, m): return m.translate([0, 0, -self.H]).rotate([90 + THETA, 0, 0])
    def pw(self, p): return R_BW @ np.asarray(p, float) + [0, 0, self.H]
    def pb(self, p): return R_BW.T @ (np.asarray(p, float) - [0, 0, self.H])
    def keep(self, m, n_w, p_w):
        """Keep the world half-space n_w . (p - p_w) >= 0 of a badge-frame solid."""
        n = R_BW.T @ np.asarray(n_w, float); n /= np.linalg.norm(n)
        return m.trim_by_plane(list(n), float(n @ self.pb(p_w)))


def trap(w0, y0, w1, y1):
    return m3.CrossSection([[(-w0/2, y0), (w0/2, y0), (w1/2, y1), (-w1/2, y1)]])


def rounded(cs, r):
    return cs.offset(-r, Round).offset(r, Round)


def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


# ---- the case, as proven, and what we do to it --------------------------------
def case_parts(b, c):
    feats, case, plate, geo = usb.build(b, c)
    plate_h, bx, by = usb.boot_hole_plate(b, c, plate, geo)
    bore_xy = feats[0].grown()
    boss = (bore_xy.offset(c.CASE_WALL, Round) ^ rect(-40, 40, 10, 40)).hull()
    env = chamfered([circle(geo["R_OUT"]), boss], -c.LIP_T, geo["Z_CASE"], c.CHAMFER, usb.BACK_CHAMFER)
    y_boss = bbox(case)[1, 1]
    # 1. the plug slot opened to the back, so the badge goes in with the cable already plugged
    #    (the boss wall in front of the port is untouched: same 3.0 mm, same engagement)
    slot = next(f for f in feats if f.name.startswith("plug")).keepout(c.FLOAT)
    sbb = slot.bounding_box()
    sx0, sx1, sz0 = sbb[0], sbb[3], sbb[2]
    slot_open = box(sx0, sx1, b.tip_y - 0.5, y_boss + 1, sz0, geo["Z_CASE"] + 1)
    # 2. a pry notch at the top of the plate rim, through the step, so a blade gets under the plate
    pry = prism(rect(-NOTCH_W/2, NOTCH_W/2, -(geo["R_REAR"] + 1.2), -geo["R_BORE"]),
                geo["FLOOR"] - 0.6, geo["Z_CASE"] + 1)
    geo.update(env=env, y_boss=y_boss, bore_xy=bore_xy, boss=boss, slot_open=slot_open, pry=pry,
               slot_x=(sx0, sx1), slot_z0=sz0)
    return feats, case, plate, plate_h, (bx, by), geo


def plug_solids(b, c, geo, dz=0.0):
    """The plug seated: overmold from the boss face, metal shell into the port."""
    yb = geo["y_boss"]
    shell = box(-4.2, 4.2, yb - usb.SHELL_LEN, yb + 0.01, b.port_z - 1.3, b.port_z + 1.3)
    body = m3.Manifold.batch_hull([box(-PLUG_W/2 + 1, PLUG_W/2 - 1, yb, yb + 0.01, b.port_z - PLUG_T/2 + 1, b.port_z + PLUG_T/2 - 1),
                                   box(-PLUG_W/2, PLUG_W/2, yb + 1.5, yb + PLUG_L - 4, b.port_z - PLUG_T/2, b.port_z + PLUG_T/2),
                                   box(-3.5, 3.5, yb + PLUG_L - 0.01, yb + PLUG_L, b.port_z - 3.0, b.port_z + 3.0)])
    return shell.translate([0, 0, dz]), body.translate([0, 0, dz])


def height(b, geo):
    """Face-centre height so the cable, after one R_BEND bend, lies on the desk."""
    y_pe = geo["y_boss"] + PLUG_L
    return C*y_pe + S*b.port_z + R_BEND*(1 + S) + CABLE_D/2


def cable_path(F, b, geo, run=70.0, n=24):
    """World points of the cable centreline: plug end, one bend, then flat along the desk."""
    p0 = F.pw([0, geo["y_boss"] + PLUG_L, b.port_z])
    cy, ch = p0[1] + R_BEND*C, p0[2] - R_BEND*S          # centre of the bend (Y, Z)
    pts = [(0, cy + R_BEND*math.cos(a), ch + R_BEND*math.sin(a))
           for a in np.radians(np.linspace(180 - THETA, 270, n))]
    pts.append((0, cy + run, ch - R_BEND))
    return np.array(pts), (cy, ch)


def tube(points, r, seg=20):
    s = [m3.Manifold.sphere(r, seg).translate(list(p)) for p in points]
    return union(m3.Manifold.batch_hull([s[i], s[i + 1]]) for i in range(len(s) - 1))


# ---- the body ---------------------------------------------------------------------
def build_body(shape, b, c, geo, F):
    p = SHAPES[shape]
    Z_CASE = geo["Z_CASE"]
    # the trim cone starts 0.05 INSIDE the window's front edge: coincident vertex rings there would be
    # welded by the STL writer into a non-manifold seam, and a cone wider than the window leaves a
    # hairline ceiling. Inside, the 0.05 ring faces up (toward the glass): it prints.
    r_w0 = (b.r - c.LIP_OVERLAP + c.LIP_BEVEL) - 0.05
    z_c = -c.LIP_T - (R_CUP - r_w0)
    z_f = z_c - CUP_D
    R_ARCH = R_CUP + RING
    y_desk_f = (F.H - S*z_f)/C                          # where the desk meets the front plane
    Z_FAR = 140.0

    yb = y_desk_f + 6
    if shape == "wedge":
        pod = [circle(p["R_POD"])]
        base = [rounded(trap(p["W_T"], p["Y_T"], p["W_B"], yb), 3.0)]
    else:
        y_pl = p["Y_PLINTH"]
        pod = [circle(R_ARCH), trap(p["W_STEM"], 0, p["W_STEM_B"], y_pl + 2)]
        base = [rounded(trap(p["W_PL_T"], y_pl, p["W_PL_B"], yb), 4.0)]
    # each piece gets its front chamfer exactly once (two chamfers from near-equal outlines leave
    # slivers that the STL writer welds into a non-manifold seam)
    slab = chamfered(pod, z_f, Z_CASE, FRONT_CH, BACK_CH)
    long_ = chamfered(base, z_f, Z_FAR, FRONT_CH, 0)
    in_slab = F.keep(box(-200, 200, -200, 200, z_f - 5, Z_CASE), [0, 0, 1], [0, 0, -50])
    if p["back"] == "slope":
        # the foot's top: a plane from a ridge on the slab's back plane, down at BETA to the desk
        h_r, bt = p["RIDGE_H"], math.radians(p["BETA"])
        pr = F.pw([0, (F.H - h_r - S*Z_CASE)/C, Z_CASE])
        below = F.keep(box(-200, 200, -200, 400, -200, 400), [0, -math.sin(bt), -math.cos(bt)], pr)
        foot = long_ ^ (in_slab + below)
        y_end = pr[1] + h_r/math.tan(bt)
    else:
        # the foot's top is the base outline's own top edge, square to the face: it falls back at THETA
        y_pl = min(o.bounds()[1] for o in base)
        foot = long_
        y_end = F.pw([0, y_pl, (F.H - C*y_pl)/S])[1]
    foot = F.keep(foot, [0, -1, 0], [0, y_end - 4.0, 0])
    solid = slab + foot
    geo_s = dict(y_rear=y_end - 4.0)
    if shape == "puck":       # crown knurl down the stem, between the puck and the plinth
        y0, y1 = R_ARCH + FRONT_CH, p["Y_PLINTH"] - 1.0
        v = m3.CrossSection([[(-FLUTE_W/2, 0), (FLUTE_W/2, 0), (0, FLUTE_W/2)]])      # (x, z): 45-degree V
        fl = m3.Manifold.extrude(v, y1 - y0).rotate([-90, 0, 0]).mirror([0, 0, 1])    # along +y, apex up (+z)
        flutes = union(fl.translate([FLUTE_P*(i - (FLUTES - 1)/2), y0, z_f - 0.01]) for i in range(FLUTES))
        geo_s["flutes"] = flutes

    solid = solid + geo["env"]
    # cuts ------------------------------------------------------------------------
    case_void = geo["env"] - geo["case"]
    # The recess is ONE revolved profile: voids that only touch across a plane (cone on cup, cone on
    # window) leave a double-sided zero-thickness sheet even inside a union. The 45-degree cone runs
    # 0.3 on past the lip plane into the window: it narrows faster than the window, so it stays inside it.
    prof = m3.CrossSection([[(0, z_f - 1), (R_CUP + CUP_CH + 1, z_f - 1), (R_CUP, z_f + CUP_CH), (R_CUP, z_c),
                             (r_w0 - 0.3, -c.LIP_T + 0.3), (0, -c.LIP_T + 0.3)]])
    recess = m3.Manifold.revolve(prof, SEG).rotate([0, 0, 180/SEG])
    pocket = geo["bore_xy"] + circle(geo["R_REAR"])
    recess += prism(pocket.offset(-0.05, Round), Z_CASE - 0.3, Z_CASE + 1.0)      # counterbore | access overlap
    y_boss = geo["y_boss"]
    trough = box(-PLUG_W/2 - PLUG_CLR, PLUG_W/2 + PLUG_CLR, y_boss, y_boss + PLUG_L + 0.7,
                 b.port_z - PLUG_T/2 - PLUG_CLR, Z_FAR + 10)
    pts, (cy, ch) = cable_path(F, b, geo)
    p0 = pts[0]
    cslot = F.b(box(-CABLE_SLOT/2, CABLE_SLOT/2, cy - R_BEND - CABLE_D/2 - 0.75, 400, -10, p0[2] + CABLE_D/2 + 0.75))
    # starts 0.05 behind the back plane: sharing that plane with the slab's back face leaves a seam
    access = prism(circle(geo["R_OUT"] + ACCESS) + geo["boss"].offset(ACCESS, Round), Z_CASE + 0.05, Z_CASE + 160)
    removed_by_access = (solid ^ access).volume()
    # one union of every void, then one subtraction: voids that touch merge instead of leaving a sheet
    cuts = [case_void, geo["slot_open"], geo["pry"], recess, trough, cslot, access] + \
           ([geo_s["flutes"]] if "flutes" in geo_s else [])
    body = solid - union(cuts)
    body = F.keep(body, [0, 0, 1], [0, 0, 0])
    geo_s.update(z_f=z_f, z_c=z_c, r_w0=r_w0, R_ARCH=R_ARCH, access=access, trough=trough, cslot=cslot,
                 removed_by_access=removed_by_access, recess=recess, solid=solid)
    return body, geo_s


# ---- checks ---------------------------------------------------------------------
def tip_angles(F, body_w, loads, pull_pt, pulls):
    """Smallest tilt about any footprint edge before the load tips the body, per pull."""
    foot = body_w.slice(0.05).hull()
    poly = np.array(foot.to_polygons()[0])
    area2 = np.sum(poly[:, 0]*np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1)*poly[:, 1])
    if area2 < 0: poly = poly[::-1]                                                  # CCW
    worst = (90.0, None)
    for f_dir in pulls:
        for i in range(len(poly)):
            e0, e1 = poly[i], poly[(i + 1) % len(poly)]
            u = (e1 - e0)/np.linalg.norm(e1 - e0)
            nin = np.array([-u[1], u[0]])                    # inward, for a CCW polygon
            def net(a):
                t = 0.0
                for (pt, fv) in loads + [(pull_pt, f_dir)]:
                    d, h = (pt[:2] - e0) @ nin, pt[2]
                    d2, h2 = d*math.cos(a) - h*math.sin(a), d*math.sin(a) + h*math.cos(a)
                    t += d2*fv[2] - h2*(fv[:2] @ nin)
                return t
            a_star = 90.0
            for a in np.radians(np.arange(0, 90.1, 0.25)):
                if net(a) >= 0: a_star = math.degrees(a); break
            if a_star < worst[0]: worst = (a_star, (f_dir, e0, e1))
    return worst, poly


def run_pedestal_checks(shape, b, c, feats, case, plate, plate_h, sw, geo, gs, body, F):
    Z_CASE = geo["Z_CASE"]
    env = geo["env"]
    print(f"\n== {shape}: fused body ==")
    print("\n7. The case inside the body is the printed USB-only case, plus two deliberate cuts")
    local = body ^ env
    expect = case - geo["slot_open"] - geo["pry"]
    diff = (local - expect).volume() + (expect - local).volume()
    check(diff < 0.5, "case region == proven case - slot opening - pry notch (to 5 um)", f"{diff:.3f} mm^3 differ")
    check((env - gs["solid"]).volume() < 1e-3, "case envelope fully embedded in the body", "")
    wall = geo["y_boss"] - b.tip_y
    check(abs(wall - 2.95) < 0.1, "wall in front of the port unchanged (never thickened)", f"{wall:.2f} mm")
    groove_top = geo["FLOOR"] - c.SNAP_LIP
    check(geo["FLOOR"] - 0.6 - groove_top >= 0.5, "pry notch stops above the snap groove",
          f"{geo['FLOOR'] - 0.6 - groove_top:.2f} mm of lip left over the groove at the notch")

    print("\n8. Badge, plug and plate go in from behind with the case fused in place")
    badge_sweep = union(prism(f.outline, f.z0, f.z1 + 120) for f in feats if not f.name.startswith("plug"))
    v = (badge_sweep ^ body).volume()
    check(v < 1e-3, "badge (every feature) slides in along its axis from 120 mm back", f"{v:.4f} mm^3")
    shell, omold = plug_solids(b, c, geo)
    for nm, s in (("plug shell", shell), ("plug overmold", omold)):
        sw_ = union([s, s.translate([0, 0, 120])]).hull()
        v = (sw_ ^ body).volume()
        check(v < 1e-3, f"{nm} rides in with the badge (cable plugged first)", f"{v:.4f} mm^3")
    v = (omold ^ body).volume() + (shell ^ body).volume()
    check(v < 1e-3, "plug seated: overmold on the boss face, clear of the trough", f"{v:.4f} mm^3")
    eng = usb.SHELL_LEN - (geo["y_boss"] - b.tip_y)
    check(eng >= usb.MIN_PLUG_ENGAGE, "plug shell engages the port", f"{eng:.2f} of {usb.SHELL_LEN}")
    tail = omold ^ box(-50, 50, geo["y_boss"] + 1.0, 500, -50, 50)     # all but the face that seats on the boss
    gap = min(tail.min_gap(body, 3.0), 3.0)
    check(gap >= 0.3, "overmold clear of the trough walls and floor (bears only on the boss face)", f"gap {gap:.2f}")
    t0 = c.SNAP_LIP + c.SNAP_CLR + geo["bh_p"] + 0.05       # bead fully out of the bore
    worst = (0.0, None)
    for t in np.concatenate([np.arange(t0, 10, 0.25), np.arange(10, 120, 2.0)]):
        v = (plate_h.translate([0, 0, t]) ^ body).volume()
        if v > worst[0]: worst = (v, t)
    check(worst[0] < 1e-3, f"plate clear of the body from {t0:.2f} to 120 mm back (closer, the proven bead snaps)",
          f"{worst[0]:.4f} mm^3" + (f" at {worst[1]:.2f}" if worst[1] else ""))
    thumb = m3.Manifold.cylinder(60, 10, 10, 64).translate([0, 0, Z_CASE])
    v = (thumb ^ body).volume()
    check(v < 1e-3, "a Ø20 thumb reaches the plate centre square on", f"{v:.4f} mm^3")
    bx, by = sw
    top = b.pcb_back_z + b.sw_cap_h
    pin = m3.Manifold.cylinder(120, usb.PIN_D/2, usb.PIN_D/2, 48).translate([bx, by, top - c.SW_TRAVEL])
    hand = m3.Manifold.cylinder(80, 6, 6, 48).translate([bx, by, Z_CASE + 12])
    v = (pin ^ body).volume() + (pin ^ plate_h).volume()
    check(v < 1e-3, f"Ø{usb.PIN_D:g} stylus to BOOT along its axis clears body and plate", f"{v:.4f} mm^3")
    v = (hand ^ body).volume()
    check(v < 1e-3, "Ø12 grip on that stylus clear from 12 mm behind the plate", f"{v:.4f} mm^3")
    act = next(f for f in feats if f.name == f"{c.BUTTON} actuator")
    check((pin ^ act.solid()).volume() > 1e-3, "stylus pressed reaches the BOOT actuator", "")
    blade = box(-1.5, 1.5, -(geo["R_REAR"] + 1.1), -(geo["R_REAR"] + 0.5), geo["FLOOR"] - 0.55, Z_CASE + 30)
    v = (blade ^ body).volume() + (blade ^ plate_h).volume()
    under = geo["R_REAR"] - c.FIT_CLR - 0.03 - geo["R_BORE"]
    check(v < 1e-3, "a 0.6 blade drops into the pry notch, below the plate's front face, beside its rim",
          f"plate rim overhangs the notch by {under:.2f}")
    v = (gs["solid"] ^ gs["access"]).volume()
    check(v < 1.0, "nothing of the body sits in the access zone behind the case (no hidden scoop)", f"{v:.2f} mm^3")

    print("\n9. Plug and cable path")
    pts, _ = cable_path(F, b, geo)
    cab = F.b(tube(pts, CABLE_D/2 + 0.3))
    v = (cab ^ body).volume()
    check(v < 1e-3, f"Ø{CABLE_D} cable (+0.3) bends R{R_BEND:g} and runs out the back, clear", f"{v:.4f} mm^3")
    lo = min(p[2] for p in pts)
    check(abs(lo - CABLE_D/2) < 0.05, "cable lies on the desk after the bend", f"centre {lo:.2f} above the desk")
    print(f"  cable leaves the body at Y {F.w(body).bounding_box()[4]:+.1f} (gauge centre at Y 0), flat on the desk")
    for f in feats:
        if f.name.startswith("plug"): continue        # the slot keepout, not a part; the real plug is checked above
        v = (f.solid() ^ body).volume()
        if v > 1e-3: check(False, f"{f.name} clear of the body", f"{v:.4f}")
    check(True, "every badge feature clear of the body at rest", "")

    print("\n10. The face: nothing in front of the glass, nothing in the line of sight")
    r_act = b.active_d/2
    eye = None
    for el, az, nm in ((35, 0, "seated eye, 35 deg down"), (THETA, 0, "square on"), (THETA + 30, 0, "30 deg above"),
                       (THETA - 30, 0, "30 deg below"), (THETA, 30, "30 deg left"), (THETA, -30, "30 deg right")):
        v_w = np.array([math.sin(math.radians(az))*math.cos(math.radians(el)), -math.cos(math.radians(az))*math.cos(math.radians(el)),
                        math.sin(math.radians(el))])
        v_b = R_BW.T @ v_w
        disc = m3.Manifold.cylinder(0.01, r_act, r_act, 96).translate([0, 0, -0.02])
        ray = m3.Manifold.batch_hull([disc, disc.translate(list(v_b*200))])
        v = (ray ^ body).volume()
        check(v < 1e-3, f"active display fully visible: {nm}", f"{v:.4f} mm^3")
    front = bbox(body)[0, 2]
    check(abs(front - gs["z_f"]) < 1e-3, "front plane is the body's lowest print face (bed)", f"glass {-front:.2f} behind it")

    me = body.to_mesh()
    cen = np.asarray(me.vert_properties)[:, :3][np.asarray(me.tri_verts)].mean(1)
    rr = np.hypot(cen[:, 0], cen[:, 1])
    probes = {"window, glass to the face": (rr < 16.5) & (cen[:, 2] > gs["z_f"] - 1) & (cen[:, 2] < 0.0),
              "behind the glass to the back": (rr < geo["R_BORE"] - 0.1) & (cen[:, 2] > 0.0) & (cen[:, 2] < Z_CASE + 5),
              "plug slot through the boss": (np.abs(cen[:, 0]) < 4.0) & (cen[:, 1] > b.tip_y + 0.2) & (cen[:, 1] < geo["y_boss"] + 5)
                                            & (cen[:, 2] > b.port_z - 1.0) & (cen[:, 2] < Z_CASE + 5)}
    for nm, sel in probes.items():
        check(sel.sum() == 0, f"no surface (zero-thickness skin) in the {nm}", f"{sel.sum()} triangles")
    tri = np.round(np.asarray(me.vert_properties)[:, :3][np.asarray(me.tri_verts)], 4)
    keys = [tuple(sorted(map(tuple, t))) for t in tri]
    dup = len(keys) - len(set(keys))
    check(dup == 0, "no coincident triangle pairs anywhere (a sheet or fin a volume test cannot see)", f"{dup} pairs")

    print("\n11. Print, walls")
    # strict: export()'s test lets a 5 mm cantilever pass as half a bridge; this one does not
    pm = body.translate([0, 0, -gs["z_f"]]).to_mesh()
    V = np.asarray(pm.vert_properties)[:, :3]; T = V[np.asarray(pm.tri_verts)]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(n, axis=1)/2
    nz = n[:, 2]/(2*a + 1e-12)
    down = (nz < -math.cos(math.radians(45)) - 1e-3) & (T[:, :, 2].max(1) > 0.01)
    check(a[down].sum() < 0.5, "no downward face steeper than 45 deg above the bed (strict, per triangle)",
          f"{a[down].sum():.2f} mm^2" + (f" at print z {T[down][:, :, 2].mean():.1f}" if down.any() else ""))
    wf = (b.port_z - PLUG_T/2 - PLUG_CLR) - gs["z_f"]
    check(wf >= 3*c.MIN_WALL, "trough front wall", f"{wf:.2f}")
    check(RING - CUP_CH >= c.MIN_WALL, "ring around the cup at the face", f"{RING - CUP_CH:.2f}")
    bw = bbox(body)
    size = bw[1] - bw[0]
    check(max(size) < 250, "fits the 256 bed in print orientation", f"{size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f}")
    return size


def stability(shape, b, geo, body, F):
    print("\n12. Stability: tip angle with the badge, plug and a 1 N pull on the cable")
    bw = F.w(body)
    mesh = bw.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    V, A = tm.volume/1000, tm.area/100
    g = 9.81e-3
    def mass_at(infill): return RHO*(infill*V + (1 - infill)*min(V, A*T_SHELL/10))
    def loads_at(m): return [(np.array(tm.center_mass), np.array([0, 0, -m*g])),
                             (F.pw([0, 0, 2.3]), np.array([0, 0, -BADGE_G*g])),
                             (F.pw([0, geo["y_boss"] + PLUG_L/2, b.port_z]), np.array([0, 0, -PLUG_G*g]))]
    mass = mass_at(INFILL)
    loads = loads_at(mass)
    pts, _ = cable_path(F, b, geo)
    y_exit = bw.bounding_box()[4]
    pull_pt = np.array([0, y_exit, CABLE_D/2])
    pulls = []
    for az in range(-90, 91, 15):
        a = math.radians(az)
        pulls.append(PULL_N*np.array([math.sin(a), math.cos(a), 0.0]))
    (tip, info), poly = tip_angles(F, bw, loads, pull_pt, pulls)
    (tip0, _), _ = tip_angles(F, bw, loads, pull_pt, [np.zeros(3)])
    print(f"  body {V:.1f} cm^3 solid; printed at {INFILL:.0%} infill + {T_SHELL} shell ~ {mass:.0f} g; "
          f"+ badge {BADGE_G:.0f} g + plug {PLUG_G:.0f} g")
    cg = (loads[0][0]*mass + loads[1][0]*BADGE_G + loads[2][0]*PLUG_G)/(mass + BADGE_G + PLUG_G)
    print(f"  centre of mass Y {cg[1]:+.1f}  Z {cg[2]:.1f} mm; footprint {np.ptp(poly[:, 0]):.0f} x {np.ptp(poly[:, 1]):.0f} mm "
          f"(Y {poly[:, 1].min():+.0f} .. {poly[:, 1].max():+.0f})")
    check(tip0 >= MIN_TIP, f"tip angle, no pull, every direction >= {MIN_TIP:.0f}", f"{tip0:.1f} deg")
    check(tip >= MIN_TIP, f"tip angle with {PULL_N:g} N along the desk, any direction behind", f"{tip:.1f} deg")
    f_dir, e0, e1 = info
    az = math.degrees(math.atan2(f_dir[0], f_dir[1]))
    print(f"  worst: pull {az:+.0f} deg from straight back, tipping over the edge ({e0[0]:+.0f},{e0[1]:+.0f})-({e1[0]:+.0f},{e1[1]:+.0f})")
    (t15, _), _ = tip_angles(F, bw, loads_at(mass_at(0.15)), pull_pt, pulls)
    print(f"  at 15% infill ({mass_at(0.15):.0f} g) the same worst case is {t15:.1f} deg")
    # how far up a 1 N pull can be lifted before the rear comes off the desk
    lift = 0
    for el in range(0, 91, 1):
        a = math.radians(el)
        (t, _), _ = tip_angles(F, bw, loads, pull_pt, [PULL_N*np.array([0, math.cos(a), math.sin(a)])])
        if t <= 0.0: break
        lift = el
    print(f"  a {PULL_N:g} N pull straight back can be raised {lift} deg off the desk before the foot lifts")
    return dict(mass=mass, tip=tip, tip0=tip0, lift=lift, cg=cg, poly=poly)


# ---- renders --------------------------------------------------------------------
BODY_C, PLATE_C = (0.58, 0.60, 0.64), (0.47, 0.49, 0.53)
DARK, SCREEN, TICK, NEEDLE = (0.07, 0.07, 0.08), (0.05, 0.12, 0.30), (0.93, 0.93, 0.90), (0.98, 0.45, 0.12)
STEEL, CABLE, DESK, VIOLET = (0.72, 0.74, 0.77), (0.10, 0.10, 0.11), (0.88, 0.86, 0.82), (0.62, 0.30, 0.80)


def gauge_face(b):
    """A dial so the render reads as a gauge (badge frame). The painter's sort needs real depth
    between layers, so ticks and needle stand 0.5 and 0.9 in front of the screen."""
    r = b.active_d/2
    parts = [(m3.Manifold.cylinder(0.4, r, r, 96).translate([0, 0, -0.4]), SCREEN)]
    ticks = []
    for i in range(11):
        a = -135 + 27*i                          # badge -y is world up: the sweep goes over the top
        t = box(-0.45, 0.45, -r + 0.9, -r + (4.0 if i % 5 == 0 else 2.4), -0.9, -0.5).rotate([0, 0, a])
        ticks.append(t)
    arc = [box(-0.6, 0.6, -r + 0.9, -r + 1.6, -0.9, -0.5).rotate([0, 0, a]) for a in np.arange(76, 136, 2.5)]
    parts += [(union(ticks), TICK), (union(arc), NEEDLE)]
    needle = m3.Manifold.batch_hull([box(-1.0, 1.0, -1.0, 1.0, -1.3, -0.9), box(-0.3, 0.3, -r + 3.2, -r + 3.8, -1.3, -0.9)])
    parts.append((needle.rotate([0, 0, -38]), NEEDLE))
    parts.append((m3.Manifold.cylinder(0.4, 1.6, 1.6, 32).translate([0, 0, -1.6]), DARK))
    return parts


def badge_solid(b, feats):
    fs = [f.solid() for f in feats if not f.name.startswith("plug")]
    return union(fs) - m3.Manifold.cylinder(1.0, b.active_d/2 + 0.01, b.active_d/2 + 0.01, 96).translate([0, 0, -0.6])


def scene(shape, b, c, feats, plate_h, geo, body, F, plate_dz=0.0, badge_dz=0.0, desk=True, filled=False):
    badge = badge_solid(b, feats)
    if filled:      # front views only: the bore behind the glass, filled, hides nothing that shows
        body = body + prism(geo["bore_xy"] + circle(geo["R_REAR"]), 0.6, geo["Z_CASE"])
    shell, omold = plug_solids(b, c, geo, badge_dz)
    pts, _ = cable_path(F, b, geo, run=95)
    if badge_dz:
        pts = pts + (R_BW @ np.array([0, 0, badge_dz]))
    parts = [(F.w(body), BODY_C), (F.w(plate_h.translate([0, 0, plate_dz])), PLATE_C),
             (F.w(badge.translate([0, 0, badge_dz])), DARK), (F.w(shell), STEEL), (F.w(omold), CABLE),
             (tube(pts, CABLE_D/2, 16), CABLE)]
    parts += [(F.w(m.translate([0, 0, badge_dz])), col) for m, col in gauge_face(b)]
    if desk:
        bw = F.w(body).bounding_box()
        parts.append((box(bw[0] - 8, bw[3] + 8, bw[1] - 8, bw[4] + 30, -1.5, 0.0), DESK))
    return parts


def R(parts, path, **kw):
    render([(m.refine_to_length(1.4), col) for m, col in parts], path, **kw)


def renders(shape, b, c, feats, plate_h, sw, geo, gs, body, F, st, final):
    tag = "" if final else f"alt-{shape}-"
    front = scene(shape, b, c, feats, plate_h, geo, body, F, filled=True)     # views that never see the back
    back = scene(shape, b, c, feats, plate_h, geo, body, F)
    R(front, PNG + f"{tag}01-hero.png", elev=16, azim=-58, zoom=1.35,
      title=f"Desk pebble ({shape}): one printed body, face {THETA:.0f}° back, cable out under the plinth")
    R(front, PNG + f"{tag}02-front-as-seen.png", elev=35, azim=-90, zoom=1.4,
      title="From your chair, 35° down: trim cone and cup around the dial" +
            (", knurled crown stem" if shape == "puck" else ""))
    if not final:
        return
    R(back, PNG + "03-back-three-quarter.png", elev=26, azim=132, zoom=1.35,
      title="Behind: plate flush in the back, plug lying in its trough, cable along the desk")
    cut = []
    for m, col in back:
        m2 = m.trim_by_plane([-1, 0, 0], 0.0)
        if not m2.is_empty(): cut.append((m2, col))
    R(cut, PNG + "04-section.png", elev=0, azim=0, zoom=1.3,
      title=f"Centreline section: case fused in, plug in the trough, one R{R_BEND:g} bend, cable on the desk")
    bx, by = sw
    top = b.pcb_back_z + b.sw_cap_h
    stylus = m3.Manifold.cylinder(24, 1.0, 1.0, 24).translate([bx, by, top]) + \
        m3.Manifold.cylinder(34, 3.5, 3.5, 32).translate([bx, by, top + 24])
    R(back[:-1] + [(F.w(stylus), VIOLET)], PNG + "05-back-boot.png", elev=-4, azim=112, zoom=1.5,
      title="BOOT from behind: Ø2 stylus (violet) through the plate's hole; pry notch at the top of the plate rim")
    ex = scene(shape, b, c, feats, plate_h, geo, body, F, plate_dz=80.0, badge_dz=40.0, desk=False)
    R(ex, PNG + "06-exploded.png", elev=20, azim=128, zoom=1.15,
      title="Assembly: cable into the badge first, drop both in from behind, snap the plate")
    pb = body.translate([0, 0, -gs["z_f"]])
    pl = plate_h.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]])
    bb = bbox(pb)
    pl = pl.translate([bb[1, 0] + 28, (bb[0, 1] + bb[1, 1])/2 - 20, 0])
    bed = box(bb[0, 0] - 8, bb[1, 0] + 56, bb[0, 1] - 8, bb[1, 1] + 8, -1.0, 0.0)
    R([(pb, BODY_C), (pl, PLATE_C), (bed, (0.22, 0.22, 0.24))], PNG + "07-print-layout.png", elev=34, azim=-62, zoom=1.25,
      title="Print layout: body FRONT FACE DOWN (the case prints bezel-down, as proven), plate flat. No supports.")
    crop = box(-34, 34, -34, 34, -20, 20)
    filled = body + prism(geo["bore_xy"] + circle(geo["R_REAR"]), 0.6, geo["Z_CASE"])
    det = [(F.w(filled ^ crop), BODY_C), (F.w(badge_solid(b, feats)), DARK)] + [(F.w(m), col) for m, col in gauge_face(b)]
    R(det, PNG + "08-trim-cone-detail.png", elev=24, azim=-68, zoom=1.15,
      title="The bezel: 45° trim cone from the window out to a short cup bore, chamfered at the face")


def main():
    b, c = Badge(), Case()
    feats, case, plate, plate_h, sw, geo = case_parts(b, c)
    geo["case"] = case
    H = height(b, geo)
    F = Frame(H)
    print(f"Face centre {H:.1f} mm above the desk, leaning back {THETA:.0f} deg. "
          f"BOOT from the back at badge ({sw[0]:+.1f}, {sw[1]:+.1f}).")
    print("\n== The case region, run through the USB-only build's own checks (post plate) ==")
    shapes = [FINAL] + [s for s in SHAPES if s != FINAL]
    results = {}
    for shape in shapes:
        body, gs = build_body(shape, b, c, geo, F)
        if shape == FINAL:
            local = body ^ geo["env"]
            usb.run_checks(b, c, feats, local, plate, geo)
            usb.run_hole_checks(b, c, feats, local, plate_h, sw[0], sw[1], geo)
        size = run_pedestal_checks(shape, b, c, feats, case, plate, plate_h, sw, geo, gs, body, F)
        st = stability(shape, b, geo, body, F)
        bw = F.w(body).bounding_box()
        print(f"\n  {shape}: {bw[3] - bw[0]:.0f} wide x {bw[4] - bw[1]:.0f} deep x {bw[5]:.0f} tall; "
              f"face centre at {H:.1f}; print height {size[2]:.0f}")
        print()
        name = "Pedestal - body" if shape == FINAL else f"Pedestal (alternate, {shape}) - body"
        export(body, STL + f"{name}.stl", lambda m: m.translate([0, 0, -gs["z_f"]]))
        results[shape] = (body, gs, st)
    export(plate_h, STL + "Pedestal - back plate (BOOT hole).stl",
           lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]]))
    if "--no-render" not in sys.argv:
        for shape in shapes:
            body, gs, st = results[shape]
            renders(shape, b, c, feats, plate_h, sw, geo, gs, body, F, st, shape == FINAL)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
