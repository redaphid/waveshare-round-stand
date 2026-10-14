#!/usr/bin/env python3
"""
Measured schematics of the TE family (stand 01 and clip 02) for the pocketwatch whiteboard, row "te":
  B  stand side section on the centre line (X = 0), parts beyond the cut dashed
  C  stand front elevation
  D  clip plan section through the jaw tongue (Z = ZC), on an 8 mm and a 32 mm bezel
  E  clip front elevation on the monitor edge
Every outline is a slice or projection of the solids pocketwatch/styles/te/build_te.py builds and checks; every
number is read from that model or its constants.

  ~/.venvs/cad/bin/python pocketwatch/board/te.py /tmp/ops-te.json
"""
import sys, json, math
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pod"); sys.path.insert(0, "pocketwatch/styles/te")
sys.path.insert(0, "pocketwatch/board")
import numpy as np, manifold3d as m3
from schem import *
import schem
import build_te as T
from build_pocketwatch import Badge, Case, prism, circle, union

schem.STYLE["monitor"] = ("#868e96", "#ffffff")
D = "te"


def project_yz(m):
    """Side silhouette in world (Y, Z)."""
    cs = m.rotate([0, 90, 0]).project()
    return [[(p[1], p[0]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def section_xy(m, z):
    """Slice on the plane Z = z: contours in world (X, Y)."""
    return [[(p[0], p[1]) for p in c] for c in m.slice(z).simplify(0.05).to_polygons()]


def dashed(els):
    for e in els: e["strokeStyle"] = "dashed"
    return els


def hidden(els):
    """Hidden outline: dashed, no fill."""
    for e in dashed(els): e["backgroundColor"] = "transparent"
    return els


def line(stem, p0, p1, color="#495057", w=2, style=None):
    e = {"id": uid(stem), "type": "line", "x": round(p0[0], 1), "y": round(p0[1], 1), "width": round(p1[0] - p0[0], 1),
         "height": round(p1[1] - p0[1], 1), "points": [[0, 0], [round(p1[0] - p0[0], 1), round(p1[1] - p0[1], 1)]],
         "strokeColor": color, "strokeWidth": w, "roughness": 0}
    if style: e["strokeStyle"] = style
    return e


def bb(m): return np.array(m.bounding_box()).reshape(2, 3)


def stand_stability(F, sbody, cover, plate, cap, ring, feet_w):
    """build_te.main()'s tip-angle check, reused: (bare, worst with a 1 N pull along the desk)."""
    parts = [(F.world(m), 0, 0) for m in (sbody, cover, plate, cap, ring)] + [(f, 0, 0) for f in feet_w] + \
            [(None, T.BADGE_G, F.pt([0, 0, 2.5]))]
    mass, cg = T.mass_props(parts)
    pts = [(x + (T.FEET_D/2 - T.PRESS)*math.cos(a), y + (T.FEET_D/2 - T.PRESS)*math.sin(a))
           for x, y in T.STAND_FEET for a in np.linspace(0, 2*math.pi, 12, endpoint=False)]
    hull = T.convex_hull(pts)
    exit_y = bb(F.world(sbody) ^ T.box(-200, 200, -200, 200, -1, T.FEET_PROUD + 0.5))[1, 1]
    P = np.array([0.0, exit_y, T.CABLE_D/2])
    free, _ = T.tip_angle(cg, mass, hull, P, (0, 1, 0), 0.0)
    pull = min(T.tip_angle(cg, mass, hull, P, (math.cos(a), math.sin(a), 0.0), T.CABLE_PULL)[0]
               for a in np.radians(np.arange(0, 360, 15)))
    return mass, free, pull


def clip_grip(cbody, cover, plate):
    """build_te.main()'s grip check: clamp at half and full gap, and the safety factors."""
    Fc, _, _, _ = T.finger_force(T.GAP)
    Fh, _, _, _ = T.finger_force(T.GAP/2)
    cw = T.clip_world(cbody)
    cmass, ccg = T.mass_props([(cw, 0, 0), (T.clip_world(cover), 0, 0), (T.clip_world(plate), 0, 0),
                               (T.slider_at(20.0), 0, 0), (T.knob_at(20.0), 0, 0), (None, T.BADGE_G, [T.OX, 0, 0])])
    Wc = cmass/1000*9.81
    load = Wc + T.CABLE_PULL
    Ne = (Wc*ccg[0] + T.CABLE_PULL*T.OX)/((T.ZT + T.ZC)/2 - bb(cw)[0, 2])
    need = math.hypot(load, Ne)
    return Fh, Fc, 2*T.MU*Fh/need, 2*T.MU*Fc/need, cmass


def main():
    out = sys.argv[1]
    b, c = Badge(), Case()
    feats, case_cuts, plate, geo = T.head_core(b, c)
    head_cuts, cover, cover_fixed, tongue, cap, ring = T.head_parts(b, c, geo)
    cuts = case_cuts + head_cuts
    F, sbody, foot_part, feet_w = T.build_stand(b, c, geo, cuts)
    cbody = T.build_clip(b, c, geo, cuts)
    shell, pbody = T.plug_solids(b, geo)
    pts, s1 = T.cable_path_stand(b, F, geo)
    fsol = {f.name: f.solid() for f in feats if not f.name.startswith("plug")}
    bx, by, Zb, stop = geo["bx"], geo["by"], geo["Z_BACK"], geo["stop"]
    click = T.G + c.SW_TRAVEL
    win_r = b.r - c.LIP_OVERLAP + c.LIP_BEVEL
    window = prism(circle(win_r), -c.LIP_T - 0.05, -c.LIP_T)
    mass, tip_free, tip_pull = stand_stability(F, sbody, cover, plate, cap, ring, feet_w)
    Fh, Fc, sf_h, sf_f, cmass = clip_grip(cbody, cover, plate)

    # ================= B: stand side section, X = 0 =================
    fid = "ms-te-side"
    fx, fy, fw, fh = slot(D, "B")
    Y0, Z0 = fx + 250, fy + 720
    tb = lambda Y, Z: (Y0 + PX*Y, Z0 - PX*Z)
    W = F.world
    sw = W(sbody)
    swb = bb(sw)
    whole = sw + W(cover) + W(cap) + union(feet_w)
    H_all = float(bb(whole)[1, 2])
    D_all = float(bb(whole)[1, 1] - bb(whole)[0, 1])
    cable_w = T.tube(pts, T.CABLE_D) ^ T.box(-50, 50, -50, (fx + fw - 30 - Y0)/PX, -50, 200)
    beyond = lambda m: m ^ T.box(-200, -0.01, -200, 300, -200, 300)          # the half the viewer looks at
    ops_f = frame(fid, fx, fy, fw, fh, "Stand 01 · Side section on the centre line (X = 0), 6 px/mm, front to the left")
    ops_f += dashed(draw_contours(project_yz(beyond(union(feet_w))), "base", fid + "-feet", tb))
    behind = dashed(draw_contours(project_yz(beyond(sw)), "case", fid + "-case-b", tb))
    for e in behind:
        if e["backgroundColor"] != "#ffffff": e["backgroundColor"] = "#e7f5ff"     # paler: not cut
    ops_f += behind
    ops_f += draw_contours(section_yz(sw, 0.0), "case", fid + "-case", tb)
    for kind, m in (("header", fsol["header H1 (any y)"]), ("badge", fsol["JST"]), ("boot", fsol["BOOT housing"] + fsol["BOOT actuator"]),
                    ("rocker", cap)):
        ops_f += dashed(draw_contours(project_yz(beyond(W(m))), kind, fid + "-" + kind + "-b", tb))
    for kind, m in (("plate", W(plate)), ("plate", W(cover)), ("rocker", W(ring)), ("badge", W(fsol["disc + tab"])),
                    ("badge", W(fsol["USB-C receptacle"])), ("plug", W(shell)), ("plug", W(pbody)), ("plug", cable_w)):
        ops_f += draw_contours(section_yz(m, 0.0), kind, fid + "-" + kind, tb)
    ops_f.append(line(fid + "-desk", (fx + 30, Z0), (fx + fw - 30, Z0)))
    # heights, left
    ops_f += dim((fx + 70, Z0), (fx + 70, Z0 - PX*H_all), f"{H_all:.1f}\nhigh", fid, (8, -20))
    gc = F.pt([0, 0, 0])
    gx, gz = tb(gc[1], gc[2])
    ops_f += dim((fx + 205, Z0), (fx + 205, gz), f"glass\ncentre\n{gc[2]:.1f}", fid, (-62, -10))
    ops_f.append(line(fid + "-gc", (fx + 200, gz), (gx, gz), "#adb5bd", 1, "dashed"))
    # tilt: the face plane and a vertical through its bottom edge
    fb, ft = F.pt([0, T.Y_BOT, -c.LIP_T]), F.pt([0, T.Y_TOP, -c.LIP_T])
    ops_f.append(line(fid + "-vert", tb(fb[1], fb[2]), tb(fb[1], ft[2] + 6), "#adb5bd", 1, "dashed"))
    ops_f.append(text(*tb(fb[1] + 1, ft[2] + 12), f"face leans {T.TILT:g}° back", 15, fid))
    # depth and feet, below the desk
    ops_f += dim(tb(swb[0, 1], -3.5), tb(swb[1, 1], -3.5), f"{D_all:.1f} deep", fid, (-30, 4))
    fy0, fy1 = T.STAND_FEET[0][1], T.STAND_FEET[2][1]
    ops_f.append(text(*tb(swb[1, 1] + 4, 17), f"orange feet Ø{T.FEET_D:g}, {T.FEET_PROUD:g} proud,\n"
                      f"{fy1 - fy0:g} apart front to back", 14, fid))
    # head internals
    cp = F.pt([bx, by, Zb + stop + T.CAP_T])
    cx_, cz_ = tb(cp[1], cp[2])
    ops_f.append(text(cx_ + 22, cz_ - 30, f"BOOT cap (beyond, X {bx:+.1f}):\nclick at {click:.2f}, rim stops at {stop:.2f}\n"
                      f"on a {T.TONGUE_W:g} x {T.TONGUE_T:g} x {T.TONGUE_L:g} flexure tongue", 14, fid))
    wall = geo["boss_tip"] - b.tip_y
    pe = F.pt([0, geo["boss_tip"] + T.PLUG_L, b.port_z])
    ex_, ez_ = tb(pe[1], pe[2])
    ops_f.append(text(*tb(swb[1, 1] + 3, 36), f"plug {T.PLUG_W:g} x {T.PLUG_T:g} x {T.PLUG_L:g} hangs in the bay,\n"
                      f"shell {T.SHELL_L - wall:.1f} of {T.SHELL_L:g} into the port\n(port wall {wall:.2f});"
                      f" cable bends R {T.BEND_R:g} out the back", 14, fid))
    ops_f.append(text(fx + 560, fy + 40, f"tips at {tip_free:.1f}° bare,\n{tip_pull:.1f}° with a {T.CABLE_PULL:g} N cable pull\n"
                      f"(~{mass:.0f} g incl. badge, {T.FILL:.0%} infill)", 15, fid))
    ops_f.append(text(fx + 30, fy + 815, "Blue = body (slab, case and foot block, one print), orange = back plate + screwed cover, purple = BOOT cap\n"
                      "and trim ring, green = badge, cyan = headers, red = BOOT switch, grey = feet, dark grey = plug + cable.\n"
                      "Dashed = beyond the cut. Cut from build_te.py's solids; crown down, so the plug hangs below the display.", 14, fid))
    ops.extend(ops_f)

    # ================= C: stand front elevation =================
    fid = "ms-te-front"
    fx, fy, fw, fh = slot(D, "C")
    X0, Zf = fx + 430, fy + 720
    tb = lambda X, Z: (X0 + PX*X, Zf - PX*Z)
    ops_f = frame(fid, fx, fy, fw, fh, "Stand 01 · Front elevation (as you sit at it), 6 px/mm")
    ops_f += draw_contours(project_xz(union(feet_w)), "base", fid + "-feet", tb)
    ops_f += draw_contours(project_xz(sw), "case", fid + "-case", tb)
    ops_f += draw_contours(project_xz(W(ring)), "rocker", fid + "-ring", tb)
    ops_f += draw_contours(project_xz(W(window)), "badge", fid + "-glass", tb)
    ops_f += hidden(draw_contours(project_xz(W(cap)), "rocker", fid + "-cap", tb))
    ops_f.append(line(fid + "-desk", (fx + 30, Zf), (fx + fw - 30, Zf)))
    ops_f += dim(tb(-T.HW, -4.5), tb(T.HW, -4.5), f"{2*T.HW:g} wide (footprint {2*T.HW:g} x {D_all:.1f})", fid, (-120, 4))
    fx0, fx1 = T.STAND_FEET[0][0], T.STAND_FEET[1][0]
    ops_f += dim(tb(fx0, -11), tb(fx1, -11), f"feet {fx1 - fx0:g} apart", fid, (-50, 4))
    ops_f += dim((X0 + PX*T.HW + 20, Zf), (X0 + PX*T.HW + 20, Zf - PX*H_all), f"{H_all:.1f}", fid, (8, 0))
    cz = gc[2]
    ops_f += dim(tb(-T.RING_OUT, cz), tb(T.RING_OUT, cz), f"ring Ø{2*T.RING_OUT:g}\n(inside Ø{2*T.RING_IN:.1f})", fid, (-40, 4))
    ops_f += dim((X0 - PX*T.HW - 50, Zf), (X0 - PX*T.HW - 50, Zf - PX*cz), f"glass\ncentre\n{cz:.1f}", fid, (-64, -10))
    gp = F.pt([T.M, 9*T.M, -c.LIP_T])
    ops_f.append(text(*tb(T.HW + 5, gp[2] + 4), f"dot grille 3 x {len(geo['grille'])//3},\nØ{T.GRILLE_D:g} on a {T.M:g} mm grid:\nthe plug shows\nthrough it", 14, fid))
    cpf = F.pt([bx, by, Zb])
    ops_f.append(text(*tb(-T.HW - 2, H_all + 9), f"BOOT cap Ø{T.CAP_D:g}, on the back\n(dashed: hidden), press toward you", 14, fid))
    ops_f.append(text(fx + 30, fy + 815, f"Blue = body, purple = orange trim ring (4 pegs), green = the window onto the display\n"
                      f"(Ø{2*win_r:.1f} at the face). Seen on a {T.TILT:g}° lean, so heights are foreshortened by cos {T.TILT:g}°.", 14, fid))
    ops.extend(ops_f)

    # ================= D: clip plan section through the jaw tongue =================
    fid = "ms-te-d"
    fx, fy, fw, fh = slot(D, "D")
    X0 = fx + 260
    cw = T.clip_world(cbody)
    z_cut = (T.ZT - T.SCREW_L + T.ZC + T.CH_H/2 - T.CLR)/2       # mid-way down the screw's bite in the tongue
    ops_f = frame(fid, fx, fy, fw, fh, f"Clip 02 · Section from above through the jaw and lock screw (Z = {z_cut:.1f}), 6 px/mm")
    for k, (e, yb0) in enumerate(((T.EDGE_MIN, fy + 330), (T.EDGE_MAX, fy + 700))):
        tb = lambda X, Y: (X0 + PX*X, yb0 - PX*Y)
        st = f"{fid}-{k}"
        ops_f += draw_contours([[(-26, 0), (0, 0), (0, e), (-26, e)]], "monitor", st + "-mon", tb)
        for kind, m in (("case", cw), ("plate", T.clip_world(plate)), ("plate", T.clip_world(cover)),
                        ("badge", T.clip_world(fsol["disc + tab"])), ("rocker", T.slider_at(e)), ("plug", T.screw_at(e))):
            ops_f += draw_contours(section_xy(m, z_cut), kind, st + "-" + kind, tb)
        ops_f.append(text(*tb(-25, e - 0.8), f"{e:g} mm bezel", 15, st))
        ops_f += dim(tb(-30, 0), tb(-30, e), f"{e:g}", st, (-28, -8))
        ops_f += dim(tb(-T.LIP, -6), tb(0, -6), f"lip {T.LIP:g}", st, (-24, 4))
        ops_f.append(text(*tb(-T.REACH - 14, e + 14), f"rear jaw\n+ finger,\n{T.GAP:.1f} gap", 14, st))
        ops_f.append(text(*tb(T.SPINE_W + 1.5, e + T.SCREW_DY + 1.5), "M3 lock\nscrew", 14, st))
    tb = lambda X, Y: (X0 + PX*X, fy + 700 - PX*Y)
    ops_f.append(text(*tb(-26, -10), "front: you sit here", 14, fid))
    ops_f.append(text(fx + 720, fy + 380, f"clamps edges\n{T.EDGE_MIN:g} to {T.EDGE_MAX:g} mm\n\n"
                      f"finger {T.FINGER_T:g} thick,\n{T.GAP:.1f} gap: clamp\n{Fh:.1f} N half shut,\n{Fc:.1f} N shut\n\n"
                      f"grip safety\nfactor {sf_h:.1f} to {sf_f:.1f}\n(mu {T.MU:g}, {cmass:.0f} g\n+ {T.CABLE_PULL:g} N cable)", 15, fid))
    ops_f.append(text(fx + 30, fy + 815, "Blue = body (face, lip, spine, case: one print), purple = sliding rear jaw with its flex finger, orange = back\n"
                      "plate + cover, dark grey = M3 screw (cut above the badge). Push the jaw until the gap is half shut, then turn the knob.", 14, fid))
    ops.extend(ops_f)

    # ================= E: clip front elevation =================
    fid = "ms-te-e"
    fx, fy, fw, fh = slot(D, "E")
    X0, Zf = fx + 290, fy + 300
    tb = lambda X, Z: (X0 + PX*X, Zf - PX*Z)
    cwb = bb(cw)
    kn = T.knob_at(20.0)
    ops_f = frame(fid, fx, fy, fw, fh, "Clip 02 · Front elevation on the monitor's right edge, 6 px/mm")
    ops_f += draw_contours([[(-40, cwb[0, 2] - 12), (0, cwb[0, 2] - 12), (0, T.ZT + 12), (-40, T.ZT + 12)]], "monitor", fid + "-mon", tb)
    ops_f += draw_contours(project_xz(cw), "case", fid + "-case", tb)
    ops_f += draw_contours(project_xz(kn), "rocker", fid + "-knob", tb)
    ops_f += draw_contours(project_xz(T.clip_world(ring)), "rocker", fid + "-ring", tb)
    ops_f += draw_contours(project_xz(T.clip_world(window)), "badge", fid + "-glass", tb)
    ops_f += hidden(draw_contours(project_xz(T.clip_world(cap)), "rocker", fid + "-cap", tb))
    ops_f.append(text(*tb(-38, T.ZT + 10), "monitor,\nright edge", 15, fid))
    ops_f += dim(tb(cwb[0, 0], cwb[0, 2] - 5), tb(cwb[1, 0], cwb[0, 2] - 5), f"{cwb[1, 0] - cwb[0, 0]:g} wide", fid, (-30, 4))
    ops_f += dim(tb(cwb[1, 0] + 6, cwb[0, 2]), tb(cwb[1, 0] + 6, T.ZT), f"{T.ZT - cwb[0, 2]:g} high\n(+{T.KNOB_H:g} knob)", fid, (8, -16))
    ops_f += dim(tb(T.SCREW_X - T.KNOB_D/2, T.ZT + T.KNOB_H + 4), tb(T.SCREW_X + T.KNOB_D/2, T.ZT + T.KNOB_H + 4),
                 f"knob Ø{T.KNOB_D:g}", fid, (-30, -24))
    ops_f += dim(tb(-T.LIP, cwb[0, 2] + 8), tb(0, cwb[0, 2] + 8), f"lip {T.LIP:g}\non the bezel", fid, (-100, -8))
    ops_f += dim(tb(0, 0), tb(T.OX, 0), f"{T.OX:g} to centre", fid, (-120, 6))
    ops_f += dim(tb(T.OX - T.RING_OUT - 4, 0), tb(T.OX - T.RING_OUT - 4, T.ZT), f"{T.ZT:g}\nto top", fid, (-52, -16))
    ops_f.append(text(*tb(T.OX + T.HW + 8, -24), f"dot grille:\nthe plug\nhangs behind", 14, fid))
    ops_f.append(text(*tb(T.SCREW_X + T.KNOB_D/2 + 4, T.ZT + 7), f"BOOT cap Ø{T.CAP_D:g} on the back (dashed)", 14, fid))
    ops_f.append(text(fx + 30, fy + 815, f"Blue = body, purple = orange knob and trim ring, green = display window. The face sits\n"
                      f"{T.LIP_T:g} proud of the screen; only the {T.LIP:g} mm lip is in front of the monitor, the screen is untouched.\n"
                      f"Right edge only (the spine is not mirrored for a left one).", 14, fid))
    ops.extend(ops_f)

    els = [compact(e) for e in ops]
    json.dump([{"kind": "put", "drafts": els}], open(out, "w"), separators=(",", ":"))
    for f in ("side", "front", "d", "e"):               # one put per frame keeps each paste small
        part = [e for e in els if e["id"].startswith(f"ms-te-{f}-") or e["id"] == f"ms-te-{f}"]
        json.dump([{"kind": "put", "drafts": part}], open(out.replace(".json", f"-{f}.json"), "w"), separators=(",", ":"))
    print(f"{len(ops)} elements -> {out}")
    print(f"stand H {H_all:.2f} D {D_all:.2f} glass {gc[2]:.2f} tip {tip_free:.1f}/{tip_pull:.1f} mass {mass:.0f}; "
          f"clip {cwb[1,0]-cwb[0,0]:.1f} x {T.ZT-cwb[0,2]:.1f}, clamp {Fh:.1f}/{Fc:.1f} SF {sf_h:.1f}/{sf_f:.1f} mass {cmass:.0f}")


def compact(e):
    """Whole pixels (1/6 mm) are plenty on the board."""
    e = dict(e)
    for k in ("x", "y", "width", "height"):
        if k in e: e[k] = round(e[k])
    if "points" in e:
        q = []
        for a, b in e["points"]:
            p = [round(a), round(b)]
            if not q or p != q[-1]: q.append(p)
        if e.get("polygon") and q[-1] != q[0]: q.append(q[0])
        e["points"] = q
    return e


if __name__ == "__main__":
    main()
