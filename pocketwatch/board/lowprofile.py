#!/usr/bin/env python3
"""
Measured schematics of the lowprofile corner clip for the pocketwatch whiteboard (row "lowprofile"), in the style of
frames A-D: flat sections and elevations cut from the real CAD, pastel fills, dimension lines with numbers.

Every outline is a slice or projection of the solids build_lowprofile.py checks (use frame: origin at the monitor's
top-right corner, +x outboard, +y into the monitor, +z up), and every number is read from the model or its Mount.

  ~/.venvs/cad/bin/python pocketwatch/board/lowprofile.py /tmp/ops.json
"""
import sys, json, math
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pocketwatch/clips/lowprofile"); sys.path.insert(0, "pocketwatch/board")
import numpy as np
from schem import *
import build_lowprofile as L
from build_pocketwatch import Badge, Case, bbox
from build_pocketwatch_usb import boot_hole_plate, BOOT_HOLE_D, PIN_D

D = "lowprofile"
T_SHOW = 12.0                 # the hero render's monitor edge (S clip)
Z_CROP = -85.0                # the cable is cut off below this
CAP = "Blue = housing + case (one print), orange = back plate, green = badge, cyan = headers, red = BOOT,\n" \
      "grey = clip, purple = its flexure leaf + nub (moves), dark grey = plug. Monitor: grey outline."


def section_xz(m, y):
    """Slice a world solid on the plane Y = y: contours in world (X, Z)."""
    cs = m.rotate([90, 0, 0]).slice(y)              # (x, y, z) -> (x, -z, y); slice at new z = y
    return [[(p[0], -p[1]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def section_xy(m, z):
    return [[(p[0], p[1]) for p in c] for c in m.slice(z).simplify(0.05).to_polygons()]


def project_yz(m):
    """Side elevation: silhouette in world (Y, Z)."""
    cs = m.rotate([0, 90, 0]).project()             # (x, y, z) -> (z, y, -x); drop the new z
    return [[(p[1], p[0]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def outline(pts, stem, stroke="#495057", width=2, dashed=False):
    """A plain outlined slab (the monitor) or a dashed ghost: no fill."""
    e = poly_el(pts, "base", stem)
    e.update(strokeColor=stroke, backgroundColor="transparent", strokeWidth=width)
    if dashed: e["strokeStyle"] = "dashed"
    return e


def ghost(contours, stem, to_board, stroke):
    return [outline([to_board(*p) for p in c], stem, stroke, 1, True) for c in contours if len(c) > 2 and abs(signed_area(c)) > 0.05]


def setup():
    b, c, m = Badge(), Case(), L.Mount()
    feats, case, plate, geo = L.build_housing(b, c, m)
    plate_h, bx, by = boot_hole_plate(b, c, plate, geo)
    F = geo["F"]
    H, P = F.use(case), F.use(plate_h)
    fw = {f.name: F.use(f.solid()) for f in feats if not f.name.startswith("plug")}
    badge = [("badge", fw["disc + tab"])] + [("header", s) for n, s in fw.items() if n.startswith("header")] + \
            [("boot", s) for n, s in fw.items() if n.startswith(c.BUTTON)]
    shell, pbody, cable = L.plug_and_cable(b, geo)
    keep = L.box(-400, 400, -400, 400, Z_CROP, 400)
    plug = (shell + pbody + cable) ^ keep
    boot_back = F.pt([bx, by, geo["Z_CASE"]])
    return b, c, m, geo, F, H, P, badge, plug, boot_back


def clip_on(m, geo, size, T):
    lf = L.Leaf(m, *L.SIZES[size])
    d = L.solve_deflection(m, lf, T)
    parts, _ = L.build_clip(m, size, d, geo)
    return parts, lf, d


def main():
    out = sys.argv[1]
    b, c, m, geo, F, H, P, badge, plug, boot_back = setup()
    R_OUT, gc = geo["R_OUT"], F.t
    hb = bbox(H)
    sl = H ^ L.box(0, 0.05, -50, 50, -100, 0)                 # the spine's bearing patch on the side face
    sb = bbox(sl)
    parts, lf, d12 = clip_on(m, geo, "S", T_SHOW)
    clip_fixed, clip_flex = parts["all"] - parts["flex"], parts["flex"]
    cb = bbox(parts["all"])
    mon = L.monitor(T_SHOW) ^ L.box(-84, 0, -400, 400, Z_CROP, 0)

    # ---- B: side section through the gauge centre (X = gauge centre), monitor and clip behind the cut ----
    fx, fy, fw_, fh = slot(D, "B")
    xs = float(gc[0])
    Y0, Z0 = fx + 520 - PX*6.0, fy + 190
    tb = lambda Y, Z: (Y0 + PX*Y, Z0 - PX*Z)
    S = f"ms-{D}-side"
    o = frame(S, fx, fy, fw_, fh, f"Lowprofile · side section through the gauge centre (X = {xs:.1f}), 6 px/mm")
    o.append(outline([tb(0, Z_CROP), tb(T_SHOW, Z_CROP), tb(T_SHOW, 0), tb(0, 0)], S + "-mon"))
    o += draw_contours(project_yz(clip_flex), "rocker", S + "-leaf", tb)
    o += draw_contours(project_yz(clip_fixed), "base", S + "-clip", tb)
    for kind, s in [("case", H), ("plate", P)] + badge + [("plug", plug)]:
        o += draw_contours(section_yz(s, xs), kind, f"{S}-{kind}", tb)
    cut = np.concatenate([np.asarray(q) for q in section_yz(H, xs) + section_yz(P, xs)])
    ymin, ymax = float(cut[:, 0].min()), float(cut[:, 0].max())
    top, bot = float(hb[1, 2]), float(hb[0, 2])
    yl = ymin - 6
    o += dim(tb(yl, 0), tb(yl, top), f"{top:.1f} above the\nmonitor top", S, (-118, -22))
    o += dim(tb(yl, 0), tb(yl, gc[2]), f"glass centre\n{-gc[2]:.1f} below\nthe top", S, (-104, -24))
    o += dim(tb(yl - 32, top), tb(yl - 32, bot), f"pod {top - bot:.1f}\ntall", S, (-80, 0))
    o += dim(tb(ymin, top + 4), tb(0, top + 4), f"{-ymin:.1f} in front of the screen", S, (-200, -24))
    o += dim(tb(0, top + 4), tb(T_SHOW, top + 4), f"edge {T_SHOW:g} (S clip: 8-16)", S, (-20, -24))
    o += dim(tb(ymin, top + 13), tb(ymax, top + 13), f"pod {ymax - ymin:.1f} deep at this cut", S, (-90, -24))
    yr = float(cb[1, 1]) + 4
    o += dim(tb(yr, 0), tb(yr, m.DECK_T), f"deck {m.DECK_T:g}", S, (10, -14))
    o += dim(tb(yr, 0), tb(yr, -m.REACH), f"leaf + nub reach\n{m.REACH:g} down the back", S, (10, -10))
    o.append(text(*tb(T_SHOW + 3, -40), f"monitor, {T_SHOW:g} mm edge\n(beside the cut, X < 0)", 15, S))
    o.append(text(*tb(T_SHOW + 3, -24), f"glass upright; turned {-m.PHI:g}°\ntoward you in plan (D)", 14, S))
    o.append(text(*tb(T_SHOW + 3, -70), "plug + cable\nstraight down", 14, S))
    o.append(text(fx + 30, fy + 800, CAP + f"\nCut at X = {xs:.1f}, the gauge centre; the {-m.PHI:g}° cant stretches depths here by "
                  f"{100*(1/math.cos(math.radians(m.PHI)) - 1):.1f} %.", 14, S))
    ops.extend(o)

    # ---- C: front elevation (viewer at -Y): what is hidden behind the monitor is dashed ----
    fx, fy, fw_, fh = slot(D, "C")
    X0, Z0 = fx + 25 + 82*PX, fy + 190
    tb = lambda X, Z: (X0 + PX*X, Z0 - PX*Z)
    S = f"ms-{D}-front"
    o = frame(S, fx, fy, fw_, fh, "Lowprofile · front elevation (as you sit at it), 6 px/mm")
    o.append(outline([tb(-82, Z_CROP), tb(0, Z_CROP), tb(0, 0), tb(-82, 0)], S + "-mon"))
    sc = [tb(-82, -m.BEZEL_MIN), tb(-m.BEZEL_MIN, -m.BEZEL_MIN), tb(-m.BEZEL_MIN, Z_CROP)]
    o.append({"id": uid(S + "-scr"), "type": "line", "x": sc[0][0], "y": sc[0][1], "width": sc[1][0] - sc[0][0],
              "height": sc[2][1] - sc[0][1], "points": [[0, 0], [sc[1][0] - sc[0][0], 0], [sc[2][0] - sc[0][0], sc[2][1] - sc[0][1]]],
              "strokeColor": "#868e96", "strokeWidth": 1, "strokeStyle": "dashed", "roughness": 0, "roundness": None})
    seen = L.box(-400, 400, -400, 400, -m.LIP_REACH, 400)      # below the lip, the clip is behind the monitor
    o += ghost(project_xz(clip_flex - seen), S + "-hid", tb, "#9c36b5")
    o += draw_contours(project_xz(clip_flex ^ seen), "rocker", S + "-leaf", tb)
    o += draw_contours(project_xz(clip_fixed ^ seen), "base", S + "-clip", tb)
    o += draw_contours(project_xz(plug), "plug", S + "-plug", tb)
    o += draw_contours(project_xz(H), "case", S + "-case", tb)
    o += draw_contours(project_xz(badge[0][1]), "badge", S + "-badge", tb)
    x0h, x1h = float(hb[0, 0]), float(hb[1, 0])
    o += dim(tb(-m.B, top + 3), tb(0, top + 3), f"shoe {m.B:g}", S, (-30, -24))
    o += dim(tb(x0h, top + 9), tb(x1h, top + 9), f"pod {x1h - x0h:.1f} wide", S, (-50, -24))
    o += dim(tb(cb[0, 0], top + 15), tb(cb[1, 0], top + 15), f"clip {cb[1, 0] - cb[0, 0]:.1f} along the top", S, (-110, -24))
    xd = x1h + 2
    o += dim(tb(xd, gc[2] - R_OUT), tb(xd, gc[2] + R_OUT), f"case\nØ{2*R_OUT:.1f}", S, (6, -20))
    o += dim(tb(0, gc[2]), tb(gc[0], gc[2]), f"centre {gc[0]:.1f} out", S, (25, -24))
    o += dim(tb(-4, 0), tb(-4, sb[0, 2]), f"spine bears on the\nside face, {-sb[0, 2]:.0f} down", S, (-150, -18))
    o += dim(tb(0, -m.LIP_REACH - 1), tb(m.SPINE_GAP, -m.LIP_REACH - 1), "", S)[:1]
    o.append(text(*tb(0.5, -m.LIP_REACH - 2), f"gap {m.SPINE_GAP:g}", 13, S))
    o.append(text(*tb(-80, -16), f"screen: ≥ {m.BEZEL_MIN:g} below the edge;\nthe lip reaches {m.LIP_REACH:g}, nothing below.\n"
                  f"Dashed purple: leaf + nub\nbehind the monitor", 14, S))
    o.append(text(*tb(-81, top + 3), "horn: pull back\nto open", 14, S))
    bx, bz = tb(boot_back[0], boot_back[2])
    r = PX*BOOT_HOLE_D/2
    o.append({"id": uid(S + "-boot"), "type": "ellipse", "x": round(bx - r, 1), "y": round(bz - r, 1), "width": round(2*r, 1),
              "height": round(2*r, 1), "strokeColor": "#e03131", "backgroundColor": "#ffc9c9", "fillStyle": "solid",
              "strokeStyle": "dashed", "strokeWidth": 2, "roughness": 0})
    lx, ly = tb(-62, -36)
    o.append(text(lx, ly, f"BOOT hole Ø{BOOT_HOLE_D:g} in the back plate\n(red dashed, hidden): reach behind,\n{PIN_D:g} mm pin straight in", 14, S))
    ax0, ay0 = lx + 270, ly + 20
    o.append({"id": uid(S + "-bootl"), "type": "arrow", "x": round(ax0, 1), "y": round(ay0, 1), "width": round(bx - r - ax0, 1),
              "height": round(bz - ay0, 1), "points": [[0, 0], [round(bx - r - ax0, 1), round(bz - ay0, 1)]],
              "startArrowhead": None, "endArrowhead": "arrow", "strokeColor": "#e03131", "strokeWidth": 1, "roughness": 0})
    o.append(text(*tb(-80, -62), f"monitor top-right corner\n(S clip on {T_SHOW:g} mm)", 15, S))
    o.append(text(fx + 30, fy + 800, CAP + "\nLeft corner: mirror housing + clip in the slicer (the bore is symmetric, checked).", 14, S))
    ops.extend(o)

    # ---- D: the clamp in plan, a slice at Z = -LIP_REACH/2 through lip, leaf and nub: 8 mm (S) and 32 mm (L) ----
    fx, fy, fw_, fh = slot(D, "D")
    zc_ = -m.LIP_REACH/2
    X0 = fx + 25 + 82*PX
    o = frame(f"ms-{D}-d", fx, fy, fw_, fh, f"Lowprofile · clamp in plan, slice at Z = {zc_:g} (you below), 6 px/mm")
    for size, T, Yb in (("S", L.SIZES["S"][0], fy + 230), ("L", L.SIZES["L"][1], fy + 640)):
        tb = lambda X, Y, Yb=Yb: (X0 + PX*X, Yb - PX*Y)
        pr, lf_, d = clip_on(m, geo, size, T)
        p0 = L.build_clip(m, size, 0.0, geo)[0]          # as printed
        st = f"ms-{D}-d{size}"
        o.append(outline([tb(-82, 0), tb(0, 0), tb(0, T), tb(-82, T)], st + "-mon"))
        o += ghost(section_xy(p0["flex"], zc_), st + "-rest", tb, "#9c36b5")
        o += draw_contours(section_xy(pr["all"] - pr["flex"], zc_), "base", st + "-clip", tb)
        o += draw_contours(section_xy(pr["flex"], zc_), "rocker", st + "-leaf", tb)
        for kind, s in [("case", H), ("plate", P)] + badge:
            o += draw_contours(section_xy(s, zc_), kind, st + "-" + kind, tb)
        xn = lf_.Pt[0] + m.NUB_W + 3
        o += dim(tb(xn, 0), tb(xn, T), f"{T:g}", st, (8, -10))
        N, eps = lf_.k()*d*math.cos(lf_.alpha), lf_.strain(d)
        lo, hi = L.SIZES[size]
        o.append(text(*tb(-80, -m.LIP_W - 1.5), f"{size} clip ({lo:.0f}-{hi:.0f} mm) on a {T:.0f} mm edge:\n"
                                                   f"tip moves {d:.1f}, clamp {N:.1f} N, strain {100*eps:.2f} %", 15, st))
        o.append(text(*tb(-40, T/2 + 1.5), f"monitor {T:.0f}", 15, st))
        back = lf_.y_root + m.LEAF_T + 3.0
        if size == "S": o.append(text(*tb(-50, back + 6), f"leaf {m.LEAF_T:g} x {m.DECK_T + m.REACH:.0f} tall, {m.LEAF_L:g} long, "
                                          f"{math.degrees(lf_.alpha):.1f}° to the edge, k {lf_.k():.2f} N/mm", 14, st))
    o.append(text(*tb(gc[0] - 20, -16), f"spine bears on the side face\n(y {sb[0, 1]:.1f}..{sb[1, 1]:.1f});"
                                         f" face turned {-m.PHI:g}° to you", 14, f"ms-{D}-d"))
    o.append(text(fx + 30, fy + 800, "Purple = flexure leaf, nub and 45° horn (the moving part); dashed = as printed. Grey = deck, front\n"
                  f"lip (on the bezel), root. One clip per 8 mm band: S 8-16, M 16-24, L 24-32. Strain under {100*m.STRAIN_MAX:g} %\n"
                  "(PETG yields ~4 %). Housing cut at the same height (blue).", 14, f"ms-{D}-d"))
    ops.extend(o)

    # ---- E: front section at Y = 3 (inside the thinnest edge): dovetail, deck, spine on the side face ----
    fx, fy, fw_, fh = slot(D, "E")
    ye = 3.0
    X0, Z0 = fx + 25 + 82*PX, fy + 190
    tb = lambda X, Z: (X0 + PX*X, Z0 - PX*Z)
    S = f"ms-{D}-e"
    o = frame(S, fx, fy, fw_, fh, f"Lowprofile · front section at Y = {ye:g} (dovetail, spine), 6 px/mm")
    o.append(outline([tb(-82, -45), tb(0, -45), tb(0, 0), tb(-82, 0)], S + "-mon"))
    o += draw_contours(section_xz(clip_fixed, ye), "base", S + "-clip", tb)
    for kind, s in [("case", H), ("plate", P)] + badge:
        o += draw_contours(section_xz(s, ye), kind, f"{S}-{kind}", tb)
    xd = geo["x_dt"]
    n0, n1 = xd - m.DT_N/2, xd + m.DT_N/2
    o += dim(tb(n0, top + 3), tb(n1, top + 3), f"dovetail neck {m.DT_N:g}, {m.DT_D:g} deep,\n45° flanks, {m.DT_FIT:g} fit a side", S, (-120, -46))
    xr = -m.B - 3
    o += dim(tb(xr, 0), tb(xr, m.DECK_T), f"deck {m.DECK_T:g}", S, (-72, -9))
    o += dim(tb(xr, m.DECK_T), tb(xr, m.DECK_T + m.BROW_T), f"shoe {m.BROW_T:g}", S, (-72, -12))
    o += dim(tb(-3, 0), tb(-3, sb[0, 2]), f"spine bears on the\nside face, top to {-sb[0, 2]:.0f} down", S, (-205, -18))
    o.append(text(*tb(-80, -30), f"monitor (any edge {L.SIZES['S'][0]:.0f}-{L.SIZES['L'][1]:.0f})", 15, S))
    o.append(text(fx + 30, fy + 800, "The pod slides on from the front: the ridge under the shoe runs in the deck's groove to a stop\n"
                  f"{L.RIDGE_BACK:g} mm short of the back. Lift, sideways or back: blocked. Weight sits on the deck; the spine takes\n"
                  "the side force, so the clamp only stops it walking.", 14, S))
    ops.extend(o)

    json.dump([{"kind": "put", "drafts": ops}], open(out, "w"), separators=(",", ":"))
    print(f"{len(ops)} elements -> {out}")
    print(f"gauge centre {gc.round(1)}, housing bbox {hb.round(1).tolist()}, bearing {sb.round(1).tolist()}, S@12 tip {d12:.2f}")


if __name__ == "__main__":
    main()
