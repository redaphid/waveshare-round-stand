#!/usr/bin/env python3
"""
Measured schematics of the scissor stand for the pocketwatch whiteboard (row "scissor"): flat sections and
elevations cut from the solids build_scissor.py checks, pastel fills in the frame-A key, dimension lines.

  B  side section on the centre line, standing (viewer at -X, front to the left), far-side legs seen beyond
  C  front elevation, standing, as you sit at it
  D  folded: front and side elevations, legs hanging in the plane of the case

Writes draw-MCP ops (JSON) to the path given as the first argument; paste them into the `draw` tool.

  ~/.venvs/cad/bin/python pocketwatch/board/scissor.py /tmp/ops.json
"""
import sys, json, math, textwrap
sys.path[:0] = ["pocketwatch", "pod", "pocketwatch/stands/scissor", "pocketwatch/board"]
import numpy as np, manifold3d as m3
from schem import *
import schem
import build_scissor as S
from build_pocketwatch import Badge, Case, bbox

D = "scissor"


def project_yz(m):
    """Side elevation: silhouette in world (Y, Z), projected along X."""
    cs = m.rotate([0, 90, 0]).project()              # (x, y, z) -> (z, y, -x); keeps (z, y)
    return [[(p[1], p[0]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def project_xy(m):
    cs = m.project()
    return [[(p[0], p[1]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def rdp(pts, eps):
    """Douglas-Peucker on a closed polyline (first point repeated at the end)."""
    P = np.asarray(pts, float)
    def go(a, b):
        if b <= a + 1: return [a]
        d = P[b] - P[a]; L = np.hypot(*d) or 1.0
        dist = np.abs(d[0]*(P[a+1:b, 1] - P[a, 1]) - d[1]*(P[a+1:b, 0] - P[a, 0]))/L
        i = int(dist.argmax())
        return go(a, a + 1 + i) + go(a + 1 + i, b) if dist[i] > eps else [a]
    m = len(P)//2
    keep = go(0, m) + go(m, len(P) - 1) + [len(P) - 1]
    return [pts[i] for i in keep]


def caption(x, y, s, stem):
    return text(x, y, "\n".join(textwrap.wrap(s, 92)), 14, stem)


def hline(stem, x0, x1, y, dashed=False, w=2):
    e = {"id": uid(stem), "type": "line", "x": round(x0, 1), "y": round(y, 1), "width": round(x1 - x0, 1), "height": 0,
         "points": [[0, 0], [round(x1 - x0, 1), 0]], "strokeColor": "#495057", "strokeWidth": w, "roughness": 0}
    if dashed: e["strokeStyle"] = "dashed"
    return e


def seg(stem, p0, p1, color="#868e96"):
    (x0, y0), (x1, y1) = p0, p1
    return {"id": uid(stem), "type": "line", "x": round(x0, 1), "y": round(y0, 1), "width": round(x1 - x0, 1),
            "height": round(y1 - y0, 1), "points": [[0, 0], [round(x1 - x0, 1), round(y1 - y0, 1)]],
            "strokeColor": color, "strokeWidth": 1, "strokeStyle": "dashed", "roughness": 0}


def main():
    out = sys.argv[1]
    b, c = Badge(), Case()
    feats, case, plate, plate_h, front, rear, geo = S.assemble(b, c)
    H, af, br, Zp = geo["H"], geo["af"], geo["br"], geo["Zp"]
    plug, shell, _ = S.props(b, c, geo["boss_tip"])
    fr_d, re_d = S.deployed(geo, front, rear)
    sc = S.screws()
    Wd = lambda m: S.world(m, H)
    cable_w, _ = S.cable_world(b, geo["boss_tip"], H, back=-46.0)
    feat = {f.name: f.solid() for f in feats}
    window = m3.Manifold.cylinder(0.3, b.r - c.LIP_OVERLAP, b.r - c.LIP_OVERLAP, 128).translate([0, 0, -c.LIP_T - 0.3])

    # numbers, all from the model
    feet = []
    for m in (fr_d, re_d):
        v = np.asarray(Wd(m).to_mesh().vert_properties)[:, :3]
        feet.append(v[v[:, 2] < 0.02][:, :2])
    poly = S.hull2d(np.vstack(feet))
    fx_lo, fx_hi = poly[:, 0].min(), poly[:, 0].max()
    fy_lo, fy_hi = poly[:, 1].min(), poly[:, 1].max()
    stand_w = Wd(case + plate_h + fr_d + re_d + sc + plug)
    sb = bbox(stand_w)
    top = float(sb[1, 2])
    glass_c = S.wpt([0, 0, 0], H)
    piv = S.wpt([0, S.PIV_Y, S.PIV_Z], H)
    plug_end = S.wpt([0, geo["boss_tip"] + S.PLUG_LEN, b.port_z], H)
    zbar = bbox(Wd(re_d) ^ S.box(-8, 8, -200, 200, -10, 300))[0, 2]
    a_f, a_r = S.LEAN + af, br - S.LEAN                   # legs from vertical
    case_d = 2*geo["R_OUT"]

    # ---- B: side section on the centre line, legs beyond ----
    fx, fy, fw, fh = slot(D, "B")
    Yc = (sb[0, 1] + sb[1, 1])/2
    Y0, Z0 = fx + fw/2 + PX*Yc + 20, fy + 680
    tb = lambda Y, Z: (Y0 - PX*Y, Z0 - PX*Z)            # front (+Y) to the left
    fid = f"ms-{D}-side"
    o = frame(fid, fx, fy, fw, fh, "B · Side section on the centre line, standing, 6 px/mm")
    half = lambda m: Wd(m).trim_by_plane([1, 0, 0], 0.0)      # the far half (X > 0), seen beyond the cut
    for kind, m in (("base", half(re_d)), ("base", half(fr_d))):
        o += draw_contours(project_yz(m), kind, fid + "-leg", tb)
    o += draw_contours(project_yz(half(case) ^ S.box(S.X_LUG - 3, 40, -100, 100, -10, 200)), "case", fid + "-hood", tb)
    o += draw_contours(section_yz(cable_w, 0.0), "plug", fid + "-cable", tb)
    for kind, m in (("case", case), ("plate", plate_h), ("badge", feat["disc + tab"]),
                    ("header", feat["header H1 (any y)"]), ("header", feat["header H2 (any y)"]),
                    ("boot", feat["BOOT housing"]), ("plug", plug), ("plug", shell)):
        o += draw_contours(section_yz(Wd(m), 0.0), kind, fid + "-" + kind, tb)
    o += draw_contours(project_yz(half(sc)), "rocker", fid + "-screw", tb)
    o.append(hline(fid + "-desk", fx + 30, fx + fw - 30, Z0))
    # heights: a ladder of vertical dimensions on the front side, tallest outermost, each label above its top end
    px_, pz_ = tb(piv[1], piv[2])
    gx, gz = tb(glass_c[1], glass_c[2])
    ex, ez = tb(plug_end[1], plug_end[2])
    cv = np.asarray(Wd(case).to_mesh().vert_properties)[:, :3]
    tx_, tz_ = tb(*cv[cv[:, 2].argmax(), 1:3])
    for i, (z, name, to_x) in enumerate(((top, f"{top:.0f} overall", tx_), (glass_c[2], f"glass centre {glass_c[2]:.0f}", gx),
                                         (piv[2], f"M3 pivot {piv[2]:.1f}", px_), (plug_end[2], f"plug end {plug_end[2]:.0f}", ex))):
        x = fx + 60 + 52*i
        zt = Z0 - PX*z
        o += dim((x, Z0), (x, zt), name, fid)
        o[-1].update(x=x - 4, y=zt - 24)
        o.append(seg(fid + "-ext", (x, zt), (to_x, zt)))
    o.append(seg(fid + "-plumb", (px_, pz_), (px_, Z0)))
    o.append(text(fx + 262, Z0 - PX*31, f"front legs\n{a_f:.0f}° forward", 15, fid))
    o.append(text(px_ + 70, Z0 - PX*37, f"rear legs\n{a_r:.0f}° back", 15, fid))
    bar = bbox(Wd(re_d) ^ S.box(-8, 8, -200, 200, -10, 300))
    bx_, _ = tb((bar[0, 1] + bar[1, 1])/2, 0)
    o += dim((bx_, Z0), (bx_, Z0 - PX*zbar), "", fid)
    o[-1].update(x=bx_ + 22, y=Z0 - PX*zbar - 64, text=f"rear crossbar {zbar:.1f} up:\ncable runs under it", fontSize=14)
    o.append(text(gx + 50, tz_ - 44, f"face leans {S.LEAN:g}° back", 15, fid))
    # footprint under the desk line
    o += dim(tb(fy_hi, -5), tb(fy_lo, -5), f"footprint {fy_hi - fy_lo:.0f} deep (feet {fy_hi:+.0f} .. {fy_lo:+.0f})", fid, (-140, 6))
    o.append(caption(fx + 30, fy + 790,
                     f"Front to the left, seen from the stand's left. Blue = case (one print with the lugs and stop hoods), orange = back plate, green = badge, cyan = headers, red = BOOT, "
                     f"grey = the far-side legs seen beyond the cut, purple = M3 screw head, dark grey = plug and cable. "
                     f"Legs stop at {af:.1f}° and {br:.1f}° on the hood. Cut from build_scissor.py's solids.", fid))
    schem.ops.extend(o)

    # ---- C: front elevation, as you sit at it (viewer at +Y) ----
    fx, fy, fw, fh = slot(D, "C")
    X0, Zf = fx + fw/2, fy + 680
    tb = lambda X, Z: (X0 - PX*X, Zf - PX*Z)
    fid = f"ms-{D}-front"
    o = frame(fid, fx, fy, fw, fh, "C · Front elevation (as you sit at it), standing, 6 px/mm")
    proj = lambda m: [[(p[0], p[1]) for p in cc] for cc in project_xz(Wd(m))]
    for kind, m, st in (("plug", None, "cable"), ("base", re_d, "rear"), ("case", case, "case"), ("plug", plug, "plug"),
                        ("base", fr_d, "front"), ("badge", window, "glass"), ("rocker", sc, "screw")):
        cont = project_xz(cable_w) if m is None else proj(m)
        o += draw_contours(cont, kind, fid + "-" + st, tb)
    o.append(hline(fid + "-desk", fx + 30, fx + fw - 30, Zf))
    o += dim(tb(fx_hi, -5), tb(fx_lo, -5), f"footprint {fx_hi - fx_lo:.0f} wide", fid, (-70, 6))
    wx = float(sb[1, 0])
    ztop = top + 4
    o += dim(tb(wx, ztop + 8), tb(-wx, ztop + 8), f"{2*wx:.1f} over the screw heads", fid, (-100, -26))
    o += dim(tb(geo["R_OUT"], glass_c[2]), tb(-geo["R_OUT"], glass_c[2]), f"case Ø{case_d:.1f}", fid, (-PX*geo["R_OUT"] - 120, -10))
    o.append(text(*tb(10, glass_c[2] - 5), f"glass (Ø{2*(b.r - c.LIP_OVERLAP):.1f} window)", 14, fid))
    hx, hz = tb(-(S.X_OUT1 + S.HEAD_H), piv[2])
    o.append(text(hx + 14, hz - 70, "screw head: tighten\nuntil legs swing stiffly", 14, fid))
    o.append(caption(fx + 30, fy + 790,
                     f"Face tipped back {S.LEAN:g}°, so the glass reads as a {2*(b.r - c.LIP_OVERLAP):.0f} wide, "
                     f"{2*(b.r - c.LIP_OVERLAP)*math.cos(math.radians(S.LEAN)):.0f} tall ellipse. You touch the glass, the two "
                     f"screw heads and the legs. BOOT is at the back: a {S.PIN_D:g} mm pin through the plate.", fid))
    schem.ops.extend(o)

    # ---- D: folded (badge frame, hanging upright: board down = badge +y) ----
    fx, fy, fw, fh = slot(D, "D")
    fid = f"ms-{D}-d"
    o = frame(fid, fx, fy, fw, fh, "D · Folded for the pocket: front and side, 6 px/mm")
    cf = S.cable_folded(b, geo["boss_tip"]) ^ S.box(-10, 10, 0, geo["boss_tip"] + S.PLUG_LEN + 14, -10, 20)
    pk = bbox(case + front + rear + sc)
    Xa, Ya = fx + 60 + PX*(-pk[0, 0]), fy + 110 + PX*(-pk[0, 1])
    tf = lambda x, y: (Xa + PX*x, Ya + PX*y)               # viewer at the glass (-z)
    for kind, m, st in (("base", rear, "rear"), ("plug", cf, "cable"), ("plug", plug, "plug"), ("case", case, "case"),
                        ("base", front, "front"), ("badge", window, "glass"), ("rocker", sc, "screw")):
        o += draw_contours(project_xy(m), kind, fid + "-f" + st, tf)
    o += dim(tf(pk[0, 0], pk[0, 1] - 6), tf(pk[1, 0], pk[0, 1] - 6), f"{pk[1, 0] - pk[0, 0]:.0f} wide (screw heads)", fid, (-90, -26))
    o += dim(tf(pk[1, 0] + 6, pk[0, 1]), tf(pk[1, 0] + 6, pk[1, 1]), f"{pk[1, 1] - pk[0, 1]:.0f} tall", fid, (8, -10))
    # side: viewer at +x, glass to the left, back to the right
    zc = bbox(case)
    Xs = fx + 640 + PX*(-zc[0, 2])
    ts = lambda z, y: (Xs + PX*z, Ya + PX*y)
    for kind, m, st in (("case", case, "case"), ("plug", plug, "plug"), ("plug", cf, "cable"), ("base", front, "front"),
                        ("base", rear, "rear"), ("rocker", sc, "screw")):
        o += draw_contours(project_yz(m.trim_by_plane([1, 0, 0], 0.0)), kind, fid + "-s" + st,
                           lambda y, z: ts(z, y))
    th = zc[1, 2] - zc[0, 2]
    o += dim(ts(zc[0, 2], pk[0, 1] - 6), ts(zc[1, 2], pk[0, 1] - 6), f"{th:.2f}", fid, (-22, -26))
    o.append(text(*ts(zc[1, 2] + 4, pk[1, 1] - 40), "legs stay inside\nthe case thickness", 14, fid))
    o.append(text(*ts(zc[0, 2] - 9, (pk[0, 1] + pk[1, 1])/2 - 30), "glass", 14, fid))
    o.append(caption(fx + 30, fy + 790,
                     f"Folded, both legs hang straight down in the plane of the case: {pk[1, 0] - pk[0, 0]:.0f} x "
                     f"{pk[1, 1] - pk[0, 1]:.0f} x {th:.2f} mm. The plug and cable lie between the two crossbars, which "
                     f"guard them in a pocket. Folded legs can swing ~18° before the hood stops them (README).", fid))
    schem.ops.extend(o)

    for e in schem.ops:                                   # thin polygon points to ~half a pixel: smaller paste, same drawing
        if e.get("polygon"): e["points"] = rdp(e["points"], 0.5)
    json.dump([{"kind": "put", "drafts": schem.ops}], open(out, "w"), separators=(",", ":"), default=float)
    print(f"{len(schem.ops)} elements -> {out}")
    print(f"top {top:.1f}, glass {glass_c[2]:.1f}, pivot {piv[2]:.1f}, plug end {plug_end[2]:.1f}, bar {zbar:.1f}, "
          f"legs {a_f:.1f}/{a_r:.1f}, footprint {fx_hi - fx_lo:.1f} x {fy_hi - fy_lo:.1f}, folded {pk[1] - pk[0]}, th {th:.2f}")


if __name__ == "__main__":
    main()
