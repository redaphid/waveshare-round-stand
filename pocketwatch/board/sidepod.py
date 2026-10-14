#!/usr/bin/env python3
"""
Measured schematics of the sidepod monitor clip for the pocketwatch whiteboard (row "sidepod"), in the style of
frames A-D: flat sections and elevations cut from build_sidepod.py's own solids, pastel fills, dimension lines.

  B  section on the pod axis (the pod is turned 20 deg, so its true section is the vertical plane through its axis),
     and a second cut through BOOT, both in the badge frame drawn world-up
  C  front elevation (projection along world Y, as you sit at it), 5 px/mm so the 136 mm pillar fits
  D  clamp section on the bolt plane (world X = SCREW_X) on a 32 mm and an 8 mm monitor edge
  E  plan section at the bolt height (world Z = Z_S) on a 20 mm edge: cant, offsets, lip, pad, pillar

  ~/.venvs/cad/bin/python pocketwatch/board/sidepod.py /tmp/ops.json
"""
import sys, json, math
from dataclasses import replace
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pocketwatch/clips/sidepod"); sys.path.insert(0, "pocketwatch/board")
import numpy as np, manifold3d as m3
from schem import *
import build_sidepod as S
from build_pocketwatch import Badge, Case, bbox

D = "sidepod"


def rect(x, y, w, h, stem, stroke="#868e96", dashed=False):
    """A plain grey-outlined slab (the monitor). A closed polygon line, not a rectangle: the board stacks
    rectangles above lines, and the slab has to sit under the parts drawn after it."""
    return {"id": uid(stem), "type": "line", "x": round(x, 1), "y": round(y, 1), "width": round(w, 1),
            "height": round(h, 1), "points": [[0, 0], [round(w, 1), 0], [round(w, 1), round(h, 1)], [0, round(h, 1)], [0, 0]],
            "strokeColor": stroke, "backgroundColor": "transparent", "fillStyle": "solid", "polygon": True,
            "strokeWidth": 2, "roughness": 0, "roundness": None, "strokeStyle": "dashed" if dashed else "solid"}


def seg(p0, p1, stem, color="#868e96", dashed=True, w=1):
    (x0, y0), (x1, y1) = p0, p1
    return {"id": uid(stem), "type": "line", "x": round(x0, 1), "y": round(y0, 1), "width": round(x1 - x0, 1),
            "height": round(y1 - y0, 1), "points": [[0, 0], [round(x1 - x0, 1), round(y1 - y0, 1)]],
            "strokeColor": color, "strokeWidth": w, "roughness": 0, "strokeStyle": "dashed" if dashed else "solid"}


def hidden(els):
    """Hidden-line style: dashed outline, no fill."""
    for e in els:
        e["backgroundColor"] = "transparent"; e["strokeStyle"] = "dashed"
    return els


def cs_pts(cs, f):
    return [[f(*p) for p in c] for c in cs.simplify(0.05).to_polygons()]


def proj_y(m):
    """Silhouette along world Y as a CrossSection in (X, -Z) (schem.project_xz's frame, before the flip)."""
    return m.rotate([90, 0, 0]).project()


def main():
    out = sys.argv[1]
    b = Badge(); c = replace(Case(), LIP_BEVEL=Case().LIP_T)     # exactly as build_sidepod.main()
    feats, body, plate, ring, geo = S.build(b, c)
    M, Mi, zc = geo["M"], S.inv(geo["M"]), geo["zc"]
    to_b = lambda m: m.transform(Mi)
    case_w = body ^ geo["pod_w"]                                   # the pod housing (blue)
    base_w = body - geo["pod_w"]                                   # pillar, web, jaws, hook (grey)
    plate_w, ring_w = plate.transform(M), ring.transform(M)
    feat_b = {f.name: f.solid() for f in feats if not f.name.startswith("plug")}
    kind_of = lambda n: "boot" if n.startswith(c.BUTTON) else "header" if n.startswith("header") else "badge"
    bt = geo["BOSS_TIP"]
    plug_b = S.box(-S.PLUG_W/2, S.PLUG_W/2, bt, bt + S.PLUG_L, b.port_z - S.PLUG_T/2, b.port_z + S.PLUG_T/2)
    cable_b = S.ycyl(14, 2.0, 24).translate([0, bt + S.PLUG_L, b.port_z])
    bbw = bbox(body)
    H_all, X_all, Y_all = bbw[1, 2] - bbw[0, 2], bbw[1, 0] - bbw[0, 0], bbw[1, 1] - bbw[0, 1]
    pod_top = bbox(geo["pod_w"])[1, 2]

    # ================= B: pod-axis section + BOOT section (badge frame, drawn world-up) =================
    fx, fy, fw, fh = slot(D, "B")
    fid = f"ms-{D}-side"
    ops_f = frame(fid, fx, fy, fw, fh, "Side sections on the pod axis and through BOOT, 6 px/mm, front to the left")
    Z0 = fy + 500                                                  # world z = 0 (the clip's foot)
    parts_b = [("base", to_b(base_w)), ("case", to_b(case_w)), ("plate", plate), ("rocker", ring),
               ("plug", plug_b), ("plug", cable_b)] + [(kind_of(n), m) for n, m in feat_b.items()]
    rim = lambda by: -c.LIP_T - S.HOOD_D0 + (S.HOOD_G_LO if by > 0 else S.HOOD_G_HI)*by
    for xcut, Xc, sub in ((0.0, fx + 270, "on the pod axis (b-x 0)"),
                          (geo["sw"][c.BUTTON], fx + 680, f"through BOOT (b-x {geo['sw'][c.BUTTON]:g})")):
        tb = lambda by, bz, Xc=Xc: (Xc + PX*bz, Z0 - PX*(zc - by))
        ops_f.append(text(Xc - 120, fy + 24, sub, 16, fid))
        for kind, m in parts_b:
            ops_f += draw_contours(section_yz(m, xcut), kind, f"{fid}-{kind}", tb)
        ops_f.append(seg((Xc - 150, Z0), (Xc + 150, Z0), fid, "#495057", True, 1))
    ops_f.append(text(fx + 640, Z0 + 8, "z 0: foot of the clip (the print bed)", 14, fid))

    # left cut: the numbers that define the pod
    Xc = fx + 270
    tb = lambda by, bz: (Xc + PX*bz, Z0 - PX*(zc - by))
    gx, gz = tb(0, 0)
    ops_f += dim((gx - 150, Z0), (gx - 150, gz), f"glass centre\n{zc:.1f} above\nthe foot", fid, (-100, -20))
    ops_f += dim((gx + 120, Z0), (gx + 120, Z0 - PX*pod_top), f"pod {pod_top:.1f} tall", fid, (8, -60))
    brow, chin_by = -S.POD_TOP, -(S.POD_V1 - (S.POD_W - S.COLLAR_HW))
    yb = tb(brow, 0)[1] - 14
    ops_f += dim((tb(0, rim(brow))[0], yb), (gx, yb), f"hood at brow {-rim(brow):.1f}\n(rim {math.degrees(math.atan(S.HOOD_G_HI)):.0f}° lean)", fid, (-160, -26))
    yc = tb(chin_by, 0)[1] + 14
    ops_f += dim((tb(0, rim(chin_by))[0], yc), (gx, yc), f"chin {-rim(chin_by):.1f}\n(rim {math.degrees(math.atan(S.HOOD_G_LO)):.0f}°)", fid, (-110, -14))
    xs = tb(0, -S.Y_GLASS/S.C_)[0]                                 # screen plane y = 0 meets this cut here
    ops_f.append(seg((xs, Z0 - PX*(pod_top + 4)), (xs, Z0 + 60), fid, "#868e96", True, 2))
    ops_f.append(text(xs + 8, fy + 52, f"screen plane (y 0): glass {-S.Y_GLASS:g} in front, in world Y", 14, fid))
    ops_f += dim((gx - 40, tb(-geo["r_win"], 0)[1]), (gx - 40, tb(geo["r_win"], 0)[1]),
                 f"window\nØ{2*geo['r_win']:.1f}", fid, (-70, -20))
    pz0, pz1 = tb(bt, 0)[1], tb(bt + S.PLUG_L, 0)[1]
    ops_f += dim((gx + 75, pz0), (gx + 75, pz1), f"plug {S.PLUG_L:g},\ntop {S.COLLAR_LEN:g} in the neck", fid, (8, 40))
    # right cut: BOOT
    Xc2 = fx + 680
    tb2 = lambda by, bz: (Xc2 + PX*bz, Z0 - PX*(zc - by))
    top = b.pcb_back_z + b.sw_cap_h
    ax_, az_ = tb2(b.sw_y, top)
    ops_f.append(seg((ax_, az_), (tb2(b.sw_y, geo["Z_CASE"] + 18)[0], az_), fid, "#e03131", True, 2))
    ops_f += dim((ax_, az_ - 30), (tb2(b.sw_y, geo["Z_CASE"])[0], az_ - 30), f"{geo['Z_CASE'] - top:.1f} to BOOT", fid, (30, -12))
    ops_f.append(text(tb2(b.sw_y, geo["Z_CASE"] + 2)[0], az_ + 10, f"Ø{S.PIN_D:g} stylus through\nthe Ø{S.BOOT_HOLE_D:g} hole", 14, fid))
    ops_f.append(text(fx + 30, fy + 812,
                      f"Both cuts in the pod's own vertical plane (it turns {S.CANT:g}° toward you). Blue = pod housing, grey = pillar\n"
                      "+ jaws (same print), orange = back plate, purple = optional trim ring, green = badge, cyan = headers,\n"
                      "red = BOOT, dark grey = plug + cable. Crown (USB-C) down. Cut from build_sidepod.py's solids.", 14, fid))
    ops.extend(ops_f)

    # ================= C: front elevation (projection along world Y), 5 px/mm =================
    fx, fy, fw, fh = slot(D, "C")
    fid, P5 = f"ms-{D}-front", 5.0
    ops_f = frame(fid, fx, fy, fw, fh, "Front elevation (as you sit at it), 5 px/mm so the pillar fits")
    X0, Zf = fx + 380, fy + 720
    tb = lambda X, Z: (X0 + P5*X, Zf - P5*Z)
    flip = lambda x, nz: tb(x, -nz)
    mx0, mz0, mz1 = -40.0, -12.0, 140.0
    unflip = lambda x, nz: (x, -nz)
    ops_f.append(rect(*tb(mx0, mz1), -P5*mx0, P5*(mz1 - mz0), fid + "-slab"))
    ops_f.append(text(*tb(mx0 + 3, mz1 - 4), "monitor\n(right edge,\nseen from\nthe front)", 14, fid))
    # visible grey: everything outboard of the monitor (x > 0), plus what stands in front of its face (the lip);
    # the rear arm and spine behind the monitor (x < 0, y > 0) are out of sight
    behind = m3.CrossSection.square([200, 600]).translate([-200, -300])                      # x < 0 in proj_y's frame
    front = base_w ^ S.box(-50, 100, -50, 0.0, -1, 200)
    vis = (proj_y(base_w) - behind) + proj_y(front)
    ops_f += draw_contours(cs_pts(vis, unflip), "base", fid + "-base", tb)
    ops_f += draw_contours(cs_pts(proj_y(case_w), unflip), "case", fid + "-case", tb)
    hw20 = S.hardware(20.0)
    ops_f += hidden(draw_contours(cs_pts(proj_y(hw20["knob"]) - vis, unflip), "rocker", fid + "-knob", tb))   # clipped by the lip
    glass = proj_y(feat_b["disc + tab"].transform(M)) - proj_y(case_w)          # glass you see through the window
    ops_f += draw_contours(cs_pts(glass, lambda x, nz: (x, -nz)), "badge", fid + "-glass", tb)
    ops_f += draw_contours(cs_pts(proj_y(plug_b.transform(M)) - proj_y(case_w), unflip), "plug", fid + "-plug", tb)
    ops_f.append(seg(tb(-48, 0), tb(80, 0), fid, "#495057", True, 1))
    xr = bbw[1, 0]
    ops_f += dim(tb(mx0 - 6, 0), tb(mx0 - 6, H_all), f"{H_all:.1f}\noverall", fid, (-66, -20))
    ops_f += dim(tb(xr + 6, 0), tb(xr + 6, pod_top), f"pod top\n{pod_top:.1f}", fid, (8, -60))
    ops_f += dim(tb(bbw[0, 0], -12), tb(xr, -12), f"{X_all:.1f} wide, rear arm to pod", fid, (-190, -26))
    ops_f += dim(tb(-S.LIP, S.CL_TOP + 6), tb(0, S.CL_TOP + 6), f"lip {S.LIP:g}", fid, (-110, -12))
    ops_f += dim(tb(-34, 0), tb(-34, S.CL_TOP), f"jaws\n{S.CL_TOP:g} tall", fid, (6, -20))
    ops_f.append(text(*tb(-30, S.Z_S + 25), f"knob Ø{S.KNOB_D:g}\n(hidden, behind\nthe monitor)", 14, fid))
    ops_f.append(text(*tb(S.SX + 6, 112), f"fin {H_all - S.CL_TOP:.0f} above the jaws,\nleans {S.LEAN:g} back", 14, fid))
    ops_f.append(text(fx + 30, fy + 812,
                      f"Projection along Y. The pod turns {S.CANT:g}° toward you, so its window reads narrower than Ø{2*geo['r_win']:.1f}.\n"
                      "Blue = pod, grey = pillar + jaws, green = glass, dark grey = plug. Purple outline = knob, out of sight.", 14, fid))
    ops.extend(ops_f)

    # ================= D: clamp section on the bolt plane, 32 mm and 8 mm edges =================
    fx, fy, fw, fh = slot(D, "D")
    fid = f"ms-{D}-d"
    ops_f = frame(fid, fx, fy, fw, fh, f"Clamp section on the bolt plane (X = {S.SCREW_X:g}), {S.E_MAX:g} and {S.E_MIN:g} mm edges, 6 px/mm")
    for E, Zb in ((S.E_MAX, fy + 396), (S.E_MIN, fy + 796)):
        Y0 = fx + 140
        tb = lambda Y, Z, Y0=Y0, Zb=Zb: (Y0 + PX*Y, Zb - PX*Z)
        hw = S.hardware(E)
        ops_f.append(rect(*tb(0, S.CL_TOP), PX*E, PX*S.CL_TOP, f"{fid}-slab"))
        for kind, m in (("base", body), ("rocker", hw["pad"]), ("rocker", hw["knob"]), ("plug", hw["bolt"]), ("plug", hw["nut"])):
            ops_f += draw_contours(section_yz(m, S.SCREW_X), kind, f"{fid}-{kind}", tb)
        ops_f += dim(tb(0, 54), tb(E, 54), "", fid)[:1]
        ops_f.append(text(*tb(E + 2 if E < 20 else 2, 52), f"monitor edge {E:g}", 15, fid))
        kf = hw["head_y"] - S.KNOB_WALL - S.Y_A1
        ops_f.append(text(*tb(S.Y_A1 + kf + S.KNOB_T + 3, S.Z_S + 6), f"knob {kf:.1f} clear of the arm\n"
                          f"bolt in arm {min(hw['head_y'], S.Y_A1) - max(hw['tip'], S.Y_A0):.0f} mm", 14, fid))
        if E == S.E_MAX:
            ops_f += dim(tb(-S.JT - 3, 0), tb(-S.JT - 3, S.CL_TOP), f"{S.CL_TOP:g}", fid, (-34, -10))
            ops_f += dim(tb(-S.JT - 10, 0), tb(-S.JT - 10, S.Z_S), f"bolt\n{S.Z_S:g}", fid, (-50, -40))
            ops_f += dim(tb(0, 4), tb(S.Y_A0, 4), f"arm {S.Y_A0:g} behind the screen", fid, (-104, -24))
            ops_f += dim(tb(S.Y_A0, 16), tb(S.Y_A1, 16), f"arm {S.ARM_T:g}", fid, (36, -10))
    ops_f.append(text(fx + 30, fy + 812,
                      f"Grey = body ({S.JT:g} mm lip in front, rear arm behind), grey outline = monitor, purple = pad + knob (printed),\n"
                      f"dark grey = M4 x {S.BOLT_L:g} bolt + nut (steel). Range {S.E_MIN:g}-{S.E_MAX:g} mm, checked at {S.E_MIN:g}, 20, {S.E_MAX:g} in build_sidepod.py.", 14, fid))
    ops.extend(ops_f)

    # ================= E: plan section at the bolt height, 20 mm edge =================
    fx, fy, fw, fh = slot(D, "E")
    fid, E = f"ms-{D}-e", 20.0
    ops_f = frame(fid, fx, fy, fw, fh, f"Plan section at the bolt height (Z = {S.Z_S:g}) on a {E:g} mm edge, from above, 6 px/mm")
    X0, Yb = fx + 330, fy + 520
    tb = lambda X, Y: (X0 + PX*X, Yb - PX*Y)
    zs = S.Z_S
    sl = lambda m: [[(p[0], p[1]) for p in c_] for c_ in m.slice(zs).simplify(0.05).to_polygons()]
    hw = S.hardware(E)
    ops_f.append(rect(*tb(-48, E), 48*PX, E*PX, fid + "-slab"))
    ops_f.append(text(*tb(-30, E - 3), f"monitor, {E:g} edge", 14, fid))
    parts_e = [("base", base_w), ("case", case_w), ("plate", plate_w), ("rocker", ring_w),
               ("rocker", hw["pad"]), ("rocker", hw["knob"]), ("plug", hw["bolt"]), ("plug", hw["nut"])] + \
              [(kind_of(n), m.transform(M)) for n, m in feat_b.items()]
    for kind, m in parts_e:
        ops_f += draw_contours(sl(m), kind, f"{fid}-{kind}", tb)
    ops_f.append(seg(tb(-48, 0), tb(0, 0), fid, "#1971c2", False, 3))
    ops_f.append(text(*tb(-46, -9), "screen face (y 0)", 14, fid))
    gx, gy = tb(S.X_C, S.Y_GLASS)
    a = np.array([S.S_, S.C_])
    ops_f.append(seg(tb(*(np.array([S.X_C, S.Y_GLASS]) - 18*a)), tb(*(np.array([S.X_C, S.Y_GLASS]) + 36*a)), fid, "#1971c2", True, 1))
    ops_f.append(seg(tb(S.X_C, S.Y_GLASS - 20), tb(S.X_C, S.Y_GLASS + 36), fid, "#868e96", True, 1))
    ops_f.append(text(*tb(S.X_C + 13, S.Y_GLASS + 34), f"pod axis {S.CANT:g}° toward you", 14, fid))
    ops_f += dim(tb(0, -32), tb(S.X_C, -32), f"glass centre {S.X_C:g} out from the side face", fid, (-140, 4))
    ops_f += dim(tb(-24, 0), tb(-24, S.Y_GLASS), f"glass {-S.Y_GLASS:g} in front", fid, (6, 4))
    ops_f += dim(tb(-42, 0), tb(-42, E), f"E {E:g}", fid, (6, -8))
    ops_f += dim(tb(S.ARM_X, S.Y_A1 + 5), tb(0, S.Y_A1 + 5), f"arm {-S.ARM_X:g} over the back", fid, (-175, -10))
    ops_f += dim(tb(bbw[1, 0] + 6, bbw[0, 1]), tb(bbw[1, 0] + 6, bbw[1, 1]), f"body {Y_all:.1f} deep\n(all heights)", fid, (8, -20))
    ops_f.append(text(*tb(S.SX + 2, 23), "pillar bears on\nthe side face", 14, fid))
    ops_f.append(text(fx + 30, fy + 812,
                      f"Cut {zc - zs:.1f} below the glass centre: pod (blue), plate (orange), glass (green), grey pillar, spine with louvres\n"
                      f"and rear arm. Purple = pad + knob, dark grey = bolt + nut. Only the {S.LIP:g} mm lip touches the screen face.", 14, fid))
    ops.extend(ops_f)

    json.dump([{"kind": "put", "drafts": ops}], open(out, "w"), separators=(",", ":"))
    print(f"{len(ops)} elements -> {out}")
    print(f"body {X_all:.1f} x {Y_all:.1f} x {H_all:.1f}, glass centre z {zc:.1f}, pod top {pod_top:.1f}, "
          f"brow {-rim(-S.POD_TOP):.2f}, chin {-rim(-(S.POD_V1 - (S.POD_W - S.COLLAR_HW))):.2f}")


if __name__ == "__main__":
    main()
