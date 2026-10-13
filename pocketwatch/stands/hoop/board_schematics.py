#!/usr/bin/env python3
"""
Measured schematics of the front-BOOT hoop stand for the pocketwatch whiteboard, in the style of frames A-D:
flat sections and elevations cut from the real CAD, pastel fills, dimension lines with numbers.

Writes draw-MCP ops (JSON) to the path given as the first argument; paste them into the `draw` tool.
Every outline is a slice or projection of the same solids build_hoop_frontboot.py checks, so the numbers on
the board are the numbers in the model.

  ~/.venvs/cad/bin/python pocketwatch/stands/hoop/board_schematics.py /tmp/ops.json
"""
import sys, json, math
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pocketwatch/stands/hoop")
import numpy as np, manifold3d as m3
sys.path.insert(0, "pocketwatch/board")
from schem import *
import schem
import build_hoop_frontboot as FB
from build_hoop_frontboot import Rocker, hoop_setup, rocker_geometry, springs, stroke, base_cuts, rocker_solid
import build_hoop as H

def main():
    out = sys.argv[1]
    r = Rocker()
    s, b, c, F, feats, case, plate_b, geo_b, base, geo, keyinfo, info, screw, extra = hoop_setup()
    g0 = rocker_geometry(r, b, c, F, geo, 0.0)
    k = springs(r, g0, s)
    d_stop = stroke(r, g0, k, r.G + r.G_TOL)[45, 0] + r.STOP_SPARE
    g = rocker_geometry(r, b, c, F, geo, d_stop)
    base_fb, _, _ = base_cuts(r, g, base, d_stop/g["a"], r.TONGUE_L + r.FIT + 0.15)
    rock = rocker_solid(r, g)
    rows = stroke(r, g, k, r.G)
    body, shell, boot_, cable, cable_exit = H.cable_and_plug(s, b, F, geo, keyinfo)
    W = lambda m: F.W(m)
    case_w, plate_w = W(case), W(plate_b)
    feat_w = {f.name: W(f.solid()) for f in feats if not f.name.startswith("plug")}
    parts = [("base", base_fb), ("case", case_w), ("plate", plate_w), ("rocker", rock), ("plug", body)]
    badge = [("badge", feat_w["disc + tab"])] + [("header", m) for n, m in feat_w.items() if n.startswith("header")] + \
            [("boot", m) for n, m in feat_w.items() if n.startswith("BOOT")]
    allm = base_fb + case_w + rock
    bb = np.array(allm.bounding_box()).reshape(2, 3)
    H_top = float(np.array((case_w + body).bounding_box()).reshape(2, 3)[1, 2])
    glass_c = F.pt([0, 0, 0])

    # ---- frame S: centre-line side section (X = 0), and frame R: the rocker plane (X = nub middle) ----
    xr = r.X0 + r.NUB_W/2
    for fid, fx, xcut, title in (("ms-side", slot("hoop", "B")[0], 0.0, "S · Side section on the centre line (X = 0), 6 px/mm, front to the left"),
                                 ("ms-rock", slot("hoop", "D")[0], xr, f"R · Section through the front-BOOT key and rocker (X = {xr:.1f}), 6 px/mm")):
        fy, fw, fh = slot("hoop", "B")[1], 940, 900
        Y0, Z0 = fx + 470 - PX*float((bb[0, 1] + bb[1, 1])/2), fy + 760
        tb = lambda Y, Z: (Y0 + PX*Y, Z0 - PX*Z)
        ops_f = frame(fid, fx, fy, fw, fh, title)
        for kind, m in parts + badge:
            if kind == "rocker" and xcut == 0.0: continue
            ops_f += draw_contours(section_yz(m, xcut), kind, fid + "-" + kind, tb)
        ops_f.append({"id": uid(fid + "-desk"), "type": "line", "x": fx + 30, "y": Z0, "width": fw - 60, "height": 0,
                      "points": [[0, 0], [fw - 60, 0]], "strokeColor": "#495057", "strokeWidth": 2, "roughness": 0})
        if xcut == 0.0:
            yL = Y0 + PX*float(bb[0, 1]) - 50
            ops_f += dim((yL, Z0), (yL, Z0 - PX*H_top), f"{H_top:.0f} to the plug top", fid, (-150, 0))
            ops_f += dim((yL + 30, Z0), (yL + 30, Z0 - PX*s.BASE_T), f"{s.BASE_T:g}", fid, (6, -8))
            yb = Y0 + PX*(geo["Yb"] + s.TIER_R) + 30
            ops_f += dim((yb, Z0), (yb, Z0 - PX*s.TIER_T), f"tier {s.TIER_T:g}\n(mortise {s.MORT_D:g} deep)", fid, (8, -16))
            gx, gz = tb(glass_c[1], glass_c[2])
            ops_f += dim((gx - 120, Z0), (gx - 120, gz), f"glass centre {glass_c[2]:.0f}", fid, (-130, 0))
            ops_f.append(text(gx + 40, gz - 200, f"face leans {s.TILT:g}° back\ncrown (USB-C) up; cable loops\nover and back to the keyhole", 15, fid))
            ops_f.append(text(fx + 30, fy + 790, "Blue = hoop + case (one print), orange = button plate, green = badge, cyan = headers,\n"
                              "red = BOOT switch, grey = base, dark grey = plug. Cut from build_hoop_frontboot.py's solids.", 14, fid))
        else:
            P, K, D, Nc = g["P"], g["K"], g["D"], g["Nc"]
            px_, pz_ = tb(*P)
            ops_f.append({"id": uid(fid + "-pivot"), "type": "ellipse", "x": px_ - 7, "y": pz_ - 7, "width": 14, "height": 14,
                          "strokeColor": "#9c36b5", "backgroundColor": "#9c36b5", "fillStyle": "solid"})
            ops_f.append(text(px_ + 12, pz_ + 4, "flexure pivot\n(1.4 x 6 blade)", 14, fid))
            kx, kz = tb(*K)
            ops_f += dim((kx, kz - 40), (kx, kz - 40 + PX*d_stop), f"key: click {rows_click(rows):.1f} mm,\nstop {d_stop:.1f} mm", fid, (-170, -10))
            ops_f += dim(tb(K[0], P[1] - 4), tb(P[0], P[1] - 4), f"key arm {g['a']:.0f}", fid, (-30, 6))
            nx, nz = tb(*Nc)
            ops_f += dim((px_ + 40, pz_), (px_ + 40, pz_ - PX*g["h"]), f"nub arm {g['h']:.0f}", fid, (8, 0))
            ops_f.append(text(nx + 30, nz - 60, f"nub {r.G:g} off the flush tab\n(pushes it {STROKE_TXT}: post clicks BOOT)", 14, fid))
            ops_f.append(text(fx + 30, fy + 790, f"Purple = rocker (one print). Press the key straight down: it pivots on the blade, the nub\n"
                              f"pushes the plate's tab {STROKE_TXT}, the post (on the tab) clicks BOOT. Stop {d_stop:.1f} mm. Glass untouched.", 14, fid))
        ops.extend(ops_f)

    # ---- frame V: front elevation (viewer at -Y) ----
    fx, fy, fw, fh = slot("hoop", "C")
    X0, Zf = fx + 450, fy + 760
    tb = lambda X, Z: (X0 + PX*X, Zf - PX*Z)
    ops_f = frame("ms-front", fx, fy, fw, fh, "V · Front elevation (as you sit at it), 6 px/mm")
    for kind, m in (("base", base_fb), ("case", case_w), ("rocker", rock), ("plug", body)):
        ops_f += draw_contours(project_xz(m), kind, "ms-front-" + kind, tb)
    ops_f.append({"id": uid("ms-front-desk"), "type": "line", "x": fx + 30, "y": Zf, "width": fw - 60, "height": 0,
                  "points": [[0, 0], [fw - 60, 0]], "strokeColor": "#495057", "strokeWidth": 2, "roughness": 0})
    ops_f += dim(tb(-s.BASE_R, -4), tb(s.BASE_R, -4), f"Ø{2*s.BASE_R:.0f} base", "ms-front", (-30, 6))
    R_HI, R_HO, _ = H.ring_radii(s, geo)
    cz = glass_c[2]
    ops_f += dim(tb(-R_HO, cz + R_HO*0.94 + 6), tb(R_HO, cz + R_HO*0.94 + 6), f"ring Ø{2*R_HO:.1f} (inside Ø{2*R_HI:.1f})", "ms-front", (-60, -26))
    ops_f += dim(tb(-geo['R_OUT'], cz), tb(geo['R_OUT'], cz), f"case Ø{2*geo['R_OUT']:.1f}", "ms-front", (-30, 4))
    kx = r.X0 + r.PAD_W/2
    ops_f.append(text(*tb(kx + 8, 22), "ivory key: press down", 14, "ms-front"))
    ops.extend(ops_f)
    json.dump([{"kind": "put", "drafts": ops}], open(out, "w"), separators=(",", ":"))
    print(f"{len(ops)} elements -> {out}")


STROKE_TXT = f"{FB.STROKE:.2f} mm"


def rows_click(rows):
    """Key travel at the click: row 45 of build_hoop_frontboot.stroke() is where the switch bottoms."""
    return float(rows[45, 0])


if __name__ == "__main__":
    from build_pocketwatch import Case
    main()
