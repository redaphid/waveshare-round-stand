#!/usr/bin/env python3
"""
Measured schematics of the stalk gauge (52 mm cup on a side-bezel clip) for the pocketwatch whiteboard, row 6:
  B  side section through the cup centre (X = cup centre), clip, knobs and monitor seen beyond it
  C  front elevation, as you sit at it
  D  section through the pivot (Y = joint axis), seen from the front: teeth, bolt, nut trap
  E  clamp sections at the thumbscrew height, seen from above, on an 8 mm and a 32 mm edge

Every outline is a slice or projection of the solids build_stalk.py checks, and every number comes from its
constants or the solids' bounds. Cut faces are pastel; parts seen beyond the cut are white with a coloured edge.

  ~/.venvs/cad/bin/python pocketwatch/board/stalk.py /tmp/ops.json
"""
import sys, json, math
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pod"); sys.path.insert(0, "pocketwatch/clips/stalk")
sys.path.insert(0, "pocketwatch/board")
import numpy as np, manifold3d as m3
from schem import *
import build_stalk as S
from build_pocketwatch import Badge, Case, bbox, SEG
from build_pocketwatch_usb import boot_hole_plate

D = "stalk"
T_SIDE = 20.0                       # monitor edge drawn in B, C, D (the README's hero edge)
CABLE = 6.0                         # cable stub drawn below the plug


def project_yz(m):
    """Side silhouette (viewer at +X, front to the left): world (Y, Z)."""
    cs = m.rotate([0, 90, 0]).project()
    return [[(p[1], p[0]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def section_xz(m, y):
    """Slice on the plane Y = y: contours in world (X, Z)."""
    cs = m.rotate([90, 0, 0]).slice(y)
    return [[(p[0], -p[1]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def section_xy(m, z):
    return [[(p[0], p[1]) for p in c] for c in m.slice(z).simplify(0.05).to_polygons()]


def beyond(contours, kind, stem, tb):
    """Seen beyond the cut: white fill, role-coloured edge (outer contours only: it is a silhouette)."""
    els = draw_contours(contours, kind, stem, tb)
    for e in els: e["backgroundColor"] = "#ffffff"
    return els


def slab(stem, x0, y0, x1, y1, label=None, lx=0, ly=0, size=14):
    """The monitor: a plain grey-outlined slab (board coords)."""
    e = poly_el([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "base", stem)
    e.update(backgroundColor="#f8f9fa", strokeWidth=2)
    out = [e]
    if label: out.append(text(lx, ly, label, size, stem))
    return out


def hline(stem, x0, x1, y, dashed=True, color="#495057"):
    return {"id": uid(stem), "type": "line", "x": round(x0, 1), "y": round(y, 1), "width": round(x1 - x0, 1), "height": 0,
            "points": [[0, 0], [round(x1 - x0, 1), 0]], "strokeColor": color, "strokeWidth": 1, "roughness": 0,
            "strokeStyle": "dashed" if dashed else "solid"}


def vline(stem, x, y0, y1, dashed=True, color="#495057"):
    return {"id": uid(stem), "type": "line", "x": round(x, 1), "y": round(y0, 1), "width": 0, "height": round(y1 - y0, 1),
            "points": [[0, 0], [0, round(y1 - y0, 1)]], "strokeColor": color, "strokeWidth": 1, "roughness": 0,
            "strokeStyle": "dashed" if dashed else "solid"}


def bb(m):
    return np.array(m.bounding_box()).reshape(2, 3)


def main():
    out = sys.argv[1]
    b, c = Badge(), Case()
    feats, cup, plate, geo = S.build_cup(b, c)
    plate_h, _, _ = boot_hole_plate(b, c, plate, geo)
    ring, clip = S.trim_ring(), S.build_clip()
    body, cable, shell = S.plug_and_cable(b, geo, CABLE)
    P = lambda m: S.place(m, 0)
    kind_of = lambda n: ("badge" if n in ("disc + tab", "JST", "USB-C receptacle") else "header" if n.startswith("header")
                         else "boot" if n.startswith(("BOOT", "RESET")) else "plug")
    badge_w = [(kind_of(f.name), P(f.solid())) for f in feats if not f.name.startswith("plug")]   # the plug is drawn whole below
    gauge = [("case", P(cup)), ("plate", P(plate_h)), ("rocker", P(ring)), ("plug", P(body + shell)), ("plug", P(cable))] + badge_w
    cx, gy, gz = S.X_A + S.L_EAR, S.Y_A - S.Z_AX, S.H + S.EAR_Y      # glass centre, world
    hw, tip, head = S.clip_hardware(T_SIDE)
    b_ring, b_cup = bb(P(ring)), bb(P(cup))
    y_face, y_back, z_top, z_bot = b_ring[0, 1] + S.VIS, b_cup[1, 1], b_ring[1, 2], b_cup[0, 2]

    # ================= B: side section on the cup centre ==================================================
    fx, fy, fw, fh = slot(D, "B")
    Y0, Z0 = fx + 380, fy + 560
    tb = lambda Y, Z: (Y0 + PX*Y, Z0 - PX*Z)
    o = frame(f"ms-{D}-side", fx, fy, fw, fh, f"B · Side section on the cup centre (X = {cx:g}), 6 px/mm, front to the left")
    st = f"ms-{D}-side"
    mon_top, mon_bot = z_top + 1, -26
    o += slab(st + "-mon", *tb(0, mon_top), *tb(T_SIDE, mon_bot), "monitor\n(beyond)", *tb(-21, -12), 13)
    for k, m in (("rocker", hw["pad"]), ("plug", hw["thumbscrew"]), ("rocker", hw["clamp knob"]), ("base", clip),
                 ("plug", hw["joint bolt"]), ("rocker", hw["joint knob"])):
        o += beyond(project_yz(m), k, st + "-by", tb)
    half = m3.Manifold.cube([200, 300, 300]).translate([cx - 200, -150, -150])
    o += beyond(project_yz(union_(m for _, m in gauge) ^ half), "case", st + "-byc", tb)
    for k, m in gauge:
        o += draw_contours(section_yz(m, cx), k, f"{st}-{k}", tb)
    o.append(hline(st + "-foot", fx + 20, fx + fw - 20, Z0))
    o.append(text(fx + fw - 175, Z0 + 4, "clip foot, Z = 0", 13, st))
    o.append(vline(st + "-scr", Y0, fy + 40, Z0 + PX*14))
    o.append(text(Y0 + 6, fy + 44, "screen plane, Y = 0", 13, st))
    xL = Y0 + PX*(b_ring[0, 1]) - 130
    o += dim((xL, Z0), (xL, Z0 - PX*z_top), f"{z_top:.0f}\nfoot to\nvisor top", st, (-80, -30), 14)
    gx, gzb = tb(gy, gz)
    o += dim((xL + 25, Z0), (xL + 25, gzb), f"glass\ncentre\n{gz:g}", st, (6, 30), 14)
    o += dim(tb(y_face, z_top + 3), tb(0, z_top + 3), f"ring face {-y_face:g} in front of the screen", st, (30, -24), 14)
    o += dim(tb(b_ring[0, 1], z_top + 9), tb(y_face, z_top + 9), f"visor {S.VIS:g}", st, (-100, -10), 14)
    o += dim(tb(y_face, z_bot - 4), tb(y_back, z_bot - 4), f"cup {y_back - y_face:.0f} deep", st, (-150, -8), 14)
    yc = y_back + 9
    o += dim(tb(yc, z_bot), tb(yc, z_bot + 2*S.R_C), f"cup Ø{2*S.R_C:g}", st, (8, -8), 14)
    cb = bb(clip)
    o += dim(tb(cb[0, 1], -19), tb(cb[1, 1], -19), f"clip {cb[1, 1] - cb[0, 1]:.0f} deep (lip to rear leg)", st, (-5, 8), 14)
    o += dim(tb(bb(hw["clamp knob"])[1, 1] + 4, 0), tb(bb(hw["clamp knob"])[1, 1] + 4, S.H), f"pillar\ntop {S.H:g}\n(hidden\nby the cup)", st, (8, -40), 14)
    o += dim(tb(0, -10), tb(T_SIDE, -10), f"grip {T_SIDE:g} (takes {S.EDGE_MIN:g}-{S.EDGE_MAX:g})", st, (72, -9), 14)
    o.append(text(*tb(gy + 10.5, 8), "plug + cable\nstraight down", 13, st))
    o.append(text(fx + 20, fy + 790,
                  "Pastel = cut on the cup centre; white = seen beyond (clip, knobs, pad, thumbscrew). Blue = cup, orange =\n"
                  f"back plate (BOOT hole is {abs(geo['sw'][c.BUTTON]):.0f} mm off this plane), purple = trim ring + visor, knobs, pad; green = badge, cyan =\n"
                  "headers, dark grey = plug + steel, grey = clip. Glass centre sits behind the screen plane, beside the monitor.", 14, st))
    ops.extend(o)

    # ================= C: front elevation ==================================================================
    fx, fy, fw, fh = slot(D, "C")
    X0, Zf = fx + 250, fy + 560
    tf = lambda X, Z: (X0 + PX*X, Zf - PX*Z)
    st = f"ms-{D}-front"
    o = frame(st, fx, fy, fw, fh, "C · Front elevation (as you sit at it), 6 px/mm")
    y_back_of = lambda m: m ^ m3.Manifold.cube([300, 300, 300]).translate([-150, 0, -150])
    y_front_of = lambda m: m - m3.Manifold.cube([300, 300, 300]).translate([-150, 0, -150])
    for k, m in (("rocker", hw["clamp knob"]), ("plug", hw["thumbscrew"]), ("rocker", hw["pad"]), ("base", y_back_of(clip))):
        o += draw_contours(project_xz(m), k, st + "-" + k, tf)
    o += slab(st + "-mon", fx + 20, tf(0, 80)[1], *tf(0, -16), "monitor", fx + 30, tf(0, 76)[1], 14)
    o.append(vline(st + "-glass", tf(-S.LIP, 0)[0], tf(0, 80)[1], tf(0, -16)[1], True, "#1971c2"))
    o.append(text(fx + 30, tf(0, 62)[1], "screen\nglass", 13, st))
    o += draw_contours(project_xz(y_front_of(clip)), "base", st + "-base", tf)
    for k, m in (("plug", P(cable)), ("plug", P(body)), ("plate", P(plate_h)), ("case", P(cup)),
                 ("plug", hw["joint bolt"]), ("rocker", hw["joint knob"]), ("rocker", P(ring))):
        o += draw_contours(project_xz(m), k, st + "-" + k, tf)
    r_hole = S.R_C - S.CUP_WALL - S.SPIG - S.SPIG_FIT*math.sqrt(2) - S.SPIG_W*math.sqrt(2) - 0.05
    tube = lambda r: P(m3.Manifold.cylinder(80, r, r, SEG).translate([0, 0, -40]))
    o += draw_contours(project_xz(P(cup) ^ tube(r_hole)), "case", st + "-case", tf)
    r_win = b.r - c.LIP_OVERLAP
    o += draw_contours(project_xz(P([f for f in feats if f.name == "disc + tab"][0].solid()) ^ tube(r_win - 0.02)), "badge", st + "-badge", tf)
    R_R = S.R_C + S.RING_OVER
    o += dim(tf(cx - R_R, gz - R_R - 5), tf(cx + R_R, gz - R_R - 5), f"ring Ø{2*R_R:g}\n(cup Ø{2*S.R_C:g} behind)", st, (44, 4), 14)
    o += dim(tf(cx - r_win, gz), tf(cx + r_win, gz), f"window Ø{2*r_win:.1f}", st, (-55, 4), 14)
    o += dim(tf(-S.LIP, -10), tf(cx + R_R, -10), f"{cx + R_R + S.LIP:.1f} overall, lip edge to ring ({cx + R_R:.1f} past the monitor side)", st, (-200, 4), 14)
    o += dim(tf(-S.LIP, 3), tf(0, 3), f"lip {S.LIP:g}", st, (-90, -10), 14)
    o += dim(tf(S.X_A, gz + R_R + 4), tf(cx, gz + R_R + 4), f"axis to centre {S.L_EAR:g}", st, (-80, -26), 14)
    kz = bb(hw["joint knob"])[1, 2]
    o += dim(tf(S.X_A - S.R_KNOB, kz + 12), tf(S.X_A + S.R_KNOB, kz + 12), f"knob Ø{2*S.R_KNOB:g}", st, (-40, -24), 14)
    xr = cx + R_R + 6
    o += dim((tf(xr, 0)[0], Zf), tf(xr, gz), f"glass\ncentre\n{gz:g}", st, (8, -20), 14)
    o.append(hline(st + "-foot", fx + 20, fx + fw - 20, Zf))
    o.append(text(*tf(cx + R_R + 2, gz + R_R + 2), "knob over the pivot:\nloosen, turn the\ncup, tighten", 13, st))
    o.append(text(fx + 20, fy + 790,
                  f"Clip on the monitor's right side edge (mirror it for the left). The {S.LIP:g} mm lip is the only thing in front of\n"
                  f"the screen. Visor at 12 o'clock, plug and cable drop straight down. Aim 0 shown; the cup turns about the\n"
                  f"pillar from {min(S.AIMS):+d}° to {max(S.AIMS):+d}° toward you in {360/S.TEETH:g}° clicks.", 14, st))
    ops.extend(o)

    # ================= D: section through the pivot (Y = Y_A) ===========================================
    fx, fy, fw, fh = slot(D, "D")
    X0, Zd = fx + 200, fy + 560
    td = lambda X, Z: (X0 + PX*X, Zd - PX*Z)
    st = f"ms-{D}-d"
    o = frame(st, fx, fy, fw, fh, f"D · Section through the pivot axis (Y = {S.Y_A:.1f}), from the front, 6 px/mm")
    o += slab(st + "-mon", fx + 20, td(0, 80)[1], *td(0, -16), f"monitor\n(cut)", fx + 30, td(0, 76)[1], 14)
    for k, m in [("base", clip), ("plug", hw["joint nut"]), ("plug", hw["joint bolt"]), ("rocker", hw["joint knob"])] + \
                [g for g in gauge if g[0] != "rocker"]:
        o += draw_contours(section_xz(m, S.Y_A), k, f"{st}-{k}", td)
    o.append(hline(st + "-foot", fx + 20, fx + fw - 20, Zd))
    o.append(vline(st + "-ax", td(S.X_A, 0)[0], td(0, 64)[1], Zd + 20, True, "#9c36b5"))
    o.append(text(td(S.X_A, 0)[0] - 30, td(0, 68)[1], "yaw axis", 13, st))
    o += dim((td(-12, 0)[0], Zd), td(-12, S.H), f"pillar\ntop {S.H:g}", st, (-64, 40), 14)
    o += dim(td(0, -6), td(S.X_A, -6), f"{S.X_A:g}", st, (-6, 4), 14)
    o += dim(td(S.X_A, gz + S.R_C + 4), td(cx, gz + S.R_C + 4), f"axis {S.L_EAR:g} to the cup centre", st, (-60, -24), 14)
    o += dim(td(S.X_A + S.R_D + 3, S.H), td(S.X_A + S.R_D + 3, S.H + S.EAR_T), f"ear {S.EAR_T:g}", st, (6, -10), 13)
    o += dim(td(S.X_A - S.R_D - 3, S.H), td(S.X_A - S.R_D - 3, S.H - S.NUT_Z), f"nut\n{S.NUT_Z:g}\ndown", st, (-40, -24), 13)
    o += dim(td(cx + S.R_C + 5, 0), td(cx + S.R_C + 5, gz), f"glass\ncentre\n{gz:g}", st, (8, -20), 14)
    tooth_h = (S.R_D - 0.6 - 0.8 - 0.3) * S.TOOTH_A
    o.append(text(*td(S.X_A + 14, -6), f"Teeth: {S.TEETH} × {360/S.TEETH:g}°, {tooth_h:.1f} tall, 45° flanks, on the pillar top and\n"
                  f"under the ear. M4×{S.JOINT_BOLT:g} bolt from the knob into a nut trapped {S.NUT_Z:g} down.", 13, st))
    o.append(text(fx + 20, fy + 790,
                  f"Grey = clip (pillar is the stalk), blue = cup and its ear, purple = knob, dark grey = bolt, nut and plug.\n"
                  f"The ear's teeth sit on the pillar's; the bolt only keeps them meshed. Gravity acts across this vertical\n"
                  f"axis, so on a level monitor the cup's weight puts no torque on it. Aim {min(S.AIMS):+d}° to {max(S.AIMS):+d}°.", 14, st))
    ops.extend(o)

    # ================= E: clamp sections at the thumbscrew height, 8 and 32 mm ==========================
    fx, fy, fw, fh = slot(D, "E")
    st = f"ms-{D}-e"
    o = frame(st, fx, fy, fw, fh, f"E · Clamp from above, cut at the thumbscrew (Z = {S.Z_S:g}), 6 px/mm")
    for i, T in enumerate((S.EDGE_MIN, S.EDGE_MAX)):
        hwT, tipT, headT = S.clip_hardware(T)
        X0, Yb = fx + 220 + i*450, fy + 640
        te = lambda X, Y: (X0 + PX*X, Yb - PX*Y)
        o.append(text(X0 - 120, fy + 24, f"{T:g} mm edge", 18, st))
        o += slab(f"{st}-mon", X0 - PX*24, te(0, T)[1], *te(0, 0), "monitor", X0 - PX*23, te(0, T/2)[1] - 8, 13)
        o.append(hline(st + "-glass", X0 - PX*24, te(-S.LIP, 0)[0], Yb + 2, False, "#1971c2"))
        for k, m in (("base", clip), ("plug", hwT["clamp nut"]), ("plug", hwT["thumbscrew"]), ("rocker", hwT["pad"]),
                     ("rocker", hwT["clamp knob"])):
            o += draw_contours(section_xy(m, S.Z_S), k, f"{st}-{k}", te)
        o += dim(te(S.X_A + S.R_D + 4, 0), te(S.X_A + S.R_D + 4, T), f"edge\n{T:g}", st, (14, -18), 14)
        gap = S.Y_RL0 - T - S.PAD_T
        o += dim(te(S.X_S - S.PAD_R - 3, T + S.PAD_T), te(S.X_S - S.PAD_R - 3, S.Y_RL0), f"pad\ngap\n{gap:g}", st, (-44, -26), 13)
        o += dim(te(S.X_S + 5, S.Y_RL1 + 1), te(S.X_S + 5, headT), f"head\n{headT - S.Y_RL1:.1f}\nout", st, (6, -26), 13) if headT - S.Y_RL1 > 3 else []
        o.append(text(*te(S.X_S - 9.5, (T + S.PAD_T + S.Y_RL0)/2 if headT - S.Y_RL1 < 10 else S.Y_RL1 + 8), f"M4×{S.CLAMP_SCREW:g}", 13, st))
        o += dim(te(-S.LIP, -S.JAW_T - 3), te(0, -S.JAW_T - 3), f"lip {S.LIP:g}", st, (-64, -8), 13)
    X0 = fx + 220
    o.append(text(fx + 20, fy + 790,
                  f"You are at the bottom. Lip on the bezel front, spine on the monitor's side, rear leg {S.REAR_IN:g} mm behind it.\n"
                  f"The M4×{S.CLAMP_SCREW:g} thumbscrew (knob) pushes the purple pad onto the monitor back. Grip {S.EDGE_MIN:g}-{S.EDGE_MAX:g} mm;\n"
                  f"the pillar (right) carries the cup. Blue line = screen glass, which starts {S.LIP:g} mm in from the edge.", 14, st))
    ops.extend(o)

    for e in ops:
        if e.get("polygon") and len(e["points"]) > 8: e["points"] = thin(e["points"], 0.3)
    json.dump([{"kind": "put", "drafts": ops}], open(out, "w"), separators=(",", ":"), ensure_ascii=False)
    print(f"{len(ops)} elements -> {out}")


def thin(pts, tol):
    """Douglas-Peucker on a closed board-px polyline (keeps the closing point): smaller ops, same picture."""
    P = np.asarray(pts, float)
    def dp(i, j):
        a, b = P[i], P[j]; d = b - a; n = math.hypot(*d)
        seg = P[i + 1:j]
        if len(seg) == 0: return [i]
        dist = np.abs(d[0]*(seg[:, 1] - a[1]) - d[1]*(seg[:, 0] - a[0]))/n if n > 1e-9 else np.hypot(*(seg - a).T)
        k = int(np.argmax(dist))
        return dp(i, i + 1 + k) + dp(i + 1 + k, j) if dist[k] > tol else [i]
    m = len(P)//2
    keep = dp(0, m) + dp(m, len(P) - 1) + [len(P) - 1]
    return [pts[i] for i in keep]


def union_(ms):
    ms = list(ms)
    return m3.Manifold.batch_boolean(ms, m3.OpType.Add) if len(ms) > 1 else ms[0]


if __name__ == "__main__":
    main()
