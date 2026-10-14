#!/usr/bin/env python3
"""
Measured schematics of the kickstand pocketwatch for the design-gallery row on the pocketwatch whiteboard.
Every outline is a slice or projection of the solids build_kickstand.py checks, posed by its own stance()
(leg at the stop it measures), so the numbers on the board are the numbers in the model.

  B  side section on the centre line, standing (leg open)
  C  front elevation, as you sit at it
  D  folded puck: section through BOOT, and the back elevation (where the stylus goes)
  E  plan of the footprint: heel, foot, centre of mass, tip angles

  ~/.venvs/cad/bin/python pocketwatch/board/kickstand.py /tmp/ops-kickstand.json
"""
import sys, json, math
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pocketwatch/stands/kickstand"); sys.path.insert(0, "pocketwatch/board")
import numpy as np, manifold3d as m3
from schem import *
import build_kickstand as K
from build_pocketwatch import Badge, Case, bbox, prism, circle, SEG

D_ = "kickstand"
P = f"ms-{D_}-"


def project_yz(m):
    """Side elevation: silhouette in world (Y, Z), seen along X."""
    cs = m.rotate([0, 90, 0]).project()
    return [[(p[1], p[0]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def project_xy(m):
    """Plan: silhouette in world (X, Y), seen from above."""
    return [[(p[0], p[1]) for p in c] for c in m.project().simplify(0.05).to_polygons()]


def line(stem, pts, stroke="#495057", width=1, style=None):
    pts = np.asarray(pts, float); mn = pts.min(0)
    e = {"id": uid(stem), "type": "line", "x": round(float(mn[0]), 1), "y": round(float(mn[1]), 1),
         "width": round(float(np.ptp(pts[:, 0])), 1), "height": round(float(np.ptp(pts[:, 1])), 1),
         "points": [[round(float(x - mn[0]), 1), round(float(y - mn[1]), 1)] for x, y in pts],
         "strokeColor": stroke, "strokeWidth": width, "roughness": 0}
    if style: e["strokeStyle"] = style
    return e


def dot(stem, x, y, col, r=6):
    return {"id": uid(stem), "type": "ellipse", "x": round(x - r, 1), "y": round(y - r, 1), "width": 2*r, "height": 2*r,
            "strokeColor": col, "backgroundColor": col, "fillStyle": "solid", "roughness": 0}


def ghost(els, stroke=None, fill="#ffffff"):
    """Restyle polygons as a dashed outline: what lies beyond the cut."""
    for e in els:
        e["strokeStyle"] = "dashed"; e["backgroundColor"] = fill
        if stroke: e["strokeColor"] = stroke
    return els


def desk(stem, fx, fw, z):
    return {"id": uid(stem), "type": "line", "x": fx + 30, "y": z, "width": fw - 60, "height": 0,
            "points": [[0, 0], [fw - 60, 0]], "strokeColor": "#495057", "strokeWidth": 2, "roughness": 0}


def main():
    out = sys.argv[1]
    b, c, k = Badge(), Case(), K.Kick()
    feats, case, plate, leg, bump, pin, geo = K.build(b, c, k)
    po = K.phi_open(k)                                     # the designed stop (the build's check finds it within 1 deg)
    st = K.stance(b, c, k, feats, case, plate, leg, pin, geo, po)
    W, beta, lean = st["W"], st["beta"], st["lean"]
    legp = K.open_leg(leg + bump, po, k)
    shell, body, cable, notch, back = K.plug_and_cable(b, c, k, case, geo, po, st)
    poly = K.support(st, k)
    com = st["com"]
    wt = sum(st["mass"].values())*9.81e-3
    fw_ = {f.name: f.solid() for f in feats if not f.name.startswith("plug")}
    badge = [("badge", fw_["disc + tab"]), ("badge", fw_["USB-C receptacle"])] + \
            [("header", m) for n, m in fw_.items() if n.startswith("header")] + \
            [("boot", m) for n, m in fw_.items() if n.startswith("BOOT")]
    to_w = lambda p: K._rot_pt(np.asarray(p, float), beta) - [0, 0, st["z0"]]
    glass_c = to_w([0, 0, 0])
    hinge_w = to_w([0, k.Y_H, k.Z_H])
    notch_w = to_w(notch)
    bbw = lambda ms: np.array(bbox(union_all([W(m) for m in ms])))
    case_bb, plug_bb, cable_bb = bbw([case]), bbw([body]), bbw([cable])
    hw_bb = bbw([case, legp, body])                       # the hardware, without the cable's run over the desk
    Y_CLIP = -60.0                                         # the cable's run along the desk is drawn cut off here
    cable_w = W(cable) ^ m3.Manifold.cube([200, 200, 200]).translate([-100, Y_CLIP, -50])

    # ---- B: side section on the centre line, standing ----
    fx, fy, fw, fh = slot(D_, "B")
    Y0, Z0 = fx + 230 + PX*float(case_bb[1, 1]), fy + 620
    tb = lambda Y, Z: (Y0 - PX*Y, Z0 - PX*Z)             # front (+Y in the stand's world) to the left
    fid = P + "side"
    o = frame(fid, fx, fy, fw, fh, f"B · Side section on the centre line (X = 0), standing, 6 px/mm, front to the left")
    o += ghost(draw_contours(project_yz(W(legp)), "rocker", fid + "-legbeyond", tb), fill="#f8f0fc")
    for kind, m in [("case", W(case)), ("plate", W(plate)), ("rocker", W(legp)), ("rocker", W(pin)), ("plug", W(shell)),
                    ("plug", W(body)), ("plug", cable_w)] + [(kd, W(m)) for kd, m in badge]:
        o += draw_contours(section_yz(m, 0.0), kind, fid + "-" + kind, tb)
    o.append(desk(fid + "-desk", fx, fw, Z0))
    # contact points and footprint depth
    y_heel, y_foot = float(poly[:, 1].max()), float(poly[:, 1].min())
    o += dim(tb(y_heel, -11), tb(y_foot, -11), f"footprint {y_heel - y_foot:.1f} deep (heel to foot)", fid, (-110, 8))
    for y_ in (y_heel, y_foot):
        o.append(line(fid + "-ext", [tb(y_, -1), tb(y_, -13)], "#868e96", 1))
    o.append(text(*np.add(tb(y_heel, 0), (-80, 10)), "heel flat", 14, fid))
    o.append(text(*np.add(tb(y_foot, 0), (8, 10)), "leg foot", 14, fid))
    # overall depth of the hardware (case, leg, plug), above everything
    zt = float(cable_bb[1, 2]) + 8
    o += dim(tb(hw_bb[1, 1], zt), tb(hw_bb[0, 1], zt), f"{hw_bb[1, 1] - hw_bb[0, 1]:.1f} case front to plug back", fid, (-110, -28))
    # heights, on the right, past the cut-off cable
    for i, (h, lbl) in enumerate(((float(case_bb[1, 2]), "case"), (float(plug_bb[1, 2]), "plug"),
                                  (float(cable_bb[1, 2]), "loop"))):
        x = fx + 810 + 46*i
        o += dim((x, Z0), (x, Z0 - PX*h), "", fid)[:1]
        o.append(text(x - 16, Z0 - PX*h - 42, f"{h:.1f}\n{lbl}", 14, fid))
    # glass centre and lean, on the left
    gx, gz = tb(glass_c[1], glass_c[2])
    xl = fx + 60
    o += dim((xl, Z0), (xl, gz), f"glass\ncentre\n{glass_c[2]:.1f}", fid, (8, -24))
    o.append(line(fid + "-gc", [(xl, gz), (gx, gz)], "#868e96", 1, "dashed"))
    face = np.array([math.cos(math.radians(beta)), math.sin(math.radians(beta))])   # case +y (crown) in world (Y, Z)
    a, e = (glass_c[1] - 26*face[0], glass_c[2] - 26*face[1]), (glass_c[1] + 30*face[0], glass_c[2] + 30*face[1])
    o.append(line(fid + "-face", [tb(*a), tb(*e)], "#1971c2", 1, "dashed"))
    o.append(line(fid + "-vert", [tb(glass_c[1], glass_c[2] - 26), tb(glass_c[1], glass_c[2] + 30)], "#868e96", 1, "dashed"))
    o.append(text(gx - 200, gz - 200, f"glass face leans\n{lean:.1f}° back\nfrom vertical", 15, fid))
    # hinge and notch, labelled in the clear space behind the stand
    hx, hz = tb(hinge_w[1], hinge_w[2])
    o.append(dot(fid + "-hinge", hx, hz, "#9c36b5", 5))
    lx, ly = fx + 650, Z0 - 260
    o.append(line(fid + "-hl", [(hx + 5, hz + 3), (lx - 6, ly + 10)], "#9c36b5", 1))
    o.append(text(lx, ly, f"hinge pin Ø{k.PIN_D:g}:\nleg stops {po:.1f}°\nopen; clicks shut\nand open", 14, fid))
    nx, nz = tb(notch_w[1], notch_w[2])
    lx, ly = fx + 650, Z0 - 130
    o.append(line(fid + "-nl", [(nx + 4, nz - 4), (lx - 6, ly + 10)], "#495057", 1))
    o.append(text(lx, ly, f"cable Ø{k.CABLE_D:g} held\nin the foot\nnotch, {notch_w[2]:.1f} up", 14, fid))
    o.append(text(fx + 30, fy + 800, "Blue = case, orange = BOOT-hole plate, purple = leg + pin (dashed: the leg beyond the\n"
                  "cut, which runs through its cable notch), green = badge, dark grey = plug + cable (its run\n"
                  "along the desk drawn cut short). Cut from build_kickstand.py's solids at its own stance.", 14, fid))
    ops.extend(o)

    # ---- C: front elevation ----
    fx, fy, fw, fh = slot(D_, "C")
    X0, Zf = fx + 450, fy + 650
    tf = lambda X, Z: (X0 - PX*X, Zf - PX*Z)              # seen from the front, +X is on your left
    fid = P + "front"
    o = frame(fid, fx, fy, fw, fh, "C · Front elevation (as you sit at it), 6 px/mm")
    glass = fw_["disc + tab"] ^ m3.Manifold.cylinder(40, b.r - c.LIP_OVERLAP, b.r - c.LIP_OVERLAP, SEG).translate([0, 0, -20])
    for kind, m in (("plug", cable), ("plug", body), ("rocker", legp), ("case", case), ("badge", glass)):
        o += draw_contours(project_xz(W(m)), kind, fid + "-" + kind, tf)
    o.append(desk(fid + "-desk", fx, fw, Zf))
    R = geo["R_OUT"]
    o += dim(tf(R, glass_c[2]), tf(-R, glass_c[2]), f"case Ø{2*R:.1f}", fid, (-40, 6))
    front = poly[poly[:, 1] > poly[:, 1].mean()]; rear = poly[poly[:, 1] < poly[:, 1].mean()]
    hf, hr = np.ptp(front[:, 0]), np.ptp(rear[:, 0])
    o += dim(tf(front[:, 0].max(), -5), tf(front[:, 0].min(), -5), f"heel flat {hf:.1f} (front)", fid, (-70, 8))
    o += dim(tf(rear[:, 0].max(), -11), tf(rear[:, 0].min(), -11), f"leg foot {hr:.1f} (behind)", fid, (-70, 8))
    o += dim(tf(plug_bb[1, 0], plug_bb[1, 2] + 3), tf(plug_bb[0, 0], plug_bb[1, 2] + 3), f"plug {k.PLUG_W:g} wide", fid, (60, -30))
    xh = X0 - PX*R - 70
    o += dim((xh, Zf), (xh, Zf - PX*float(cable_bb[1, 2])), f"{cable_bb[1, 2]:.1f} overall\n(cable loop)", fid, (-110, -20))
    o += dim((xh - 50, Zf), (xh - 50, Zf - PX*glass_c[2]), f"glass\ncentre\n{glass_c[2]:.1f}", fid, (-56, -24))
    o.append(text(X0 + PX*R + 20, Zf - PX*(float(plug_bb[1, 2]) - 6), "plug stands up out of the\ncrown like a watch bow;\n"
                  "the cable loops back\nover the top", 14, fid))
    o.append(text(X0 + PX*R + 20, Zf - PX*glass_c[2] + 20, f"window Ø{2*(b.r - c.LIP_OVERLAP):.1f}\n(glass Ø{2*b.r:.1f})", 14, fid))
    o.append(text(fx + 30, fy + 790, "Nothing to press from the front: BOOT is reached from behind with a stylus (D). The leg\n"
                  f"hides behind the case. Crown at 12, so the badge needs no firmware rotation.", 14, fid))
    ops.extend(o)

    # ---- D: folded puck. Section through BOOT (case frame) and the back elevation ----
    fx, fy, fw, fh = slot(D_, "D")
    fid = P + "d"
    fa = fid + "-a"                                        # stem for D's labels and dimensions
    xs, ys = geo["boot"]
    o = frame(fid, fx, fy, fw, fh, f"D · Folded: section through BOOT (X = {xs:g}) and the back, 6 px/mm")
    cbb = np.array(bbox(case))
    Ys, Zs = fy + 250 + PX*float(cbb[1, 1]), fx + 150
    td = lambda Y, Z: (Zs + PX*Z, Ys - PX*Y)              # crown up, glass left, back right
    for kind, m in [("case", case), ("plate", plate), ("rocker", leg + bump), ("rocker", pin)] + badge:
        o += draw_contours(section_yz(m, xs), kind, fid + "-" + kind, td)
    top = b.pcb_back_z + b.sw_cap_h
    sx0, sy0 = td(ys, geo["Z_BACK"] + 14); sx1, _ = td(ys, top)
    o.append({**dim((sx0, sy0), (sx1, sy0), "", fa)[0], "startArrowhead": None, "strokeColor": "#e03131", "strokeWidth": 2})
    o.append(text(sx0 + 8, sy0 - 26, f"Ø{k.STYLUS_D:g} stylus,\n{geo['Z_BACK'] - top:.1f} deep to BOOT", 14, fa))
    zf, zb = -c.LIP_T, geo["Z_BACK"]
    yb = float(cbb[0, 1]) - 4
    o += dim(td(yb, zf), td(yb, zb), f"{zb - zf:.2f} thick", fa, (-40, 6))
    lgx, lgy = td(2.0, geo["Z_PL"] + k.G + k.LEG_T/2)
    o.append(line(fid + "-ll", [(lgx, lgy), (lgx + 50, lgy - 20)], "#9c36b5", 1))
    o.append(text(lgx + 54, lgy - 44, f"leg {k.LEG_T:g} thick,\n{k.G:g} off the plate,\nflush with the back", 14, fa))
    hx, hy = td(k.Y_H, k.Z_H)
    o.append(text(hx + 70, hy - 50, f"hinge axis {k.Y_H:g} up,\n{k.Z_H:g} behind the glass", 14, fa))
    o.append(line(fid + "-hl", [(hx, hy), (hx + 66, hy - 36)], "#9c36b5", 1))
    # back elevation, folded: seen from behind (+x to the right)
    Xb, Yb = fx + 640, Ys
    tk = lambda X, Y: (Xb + PX*X, Yb - PX*Y)
    for kind, m in (("case", case), ("plate", plate), ("rocker", leg + bump), ("rocker", pin)):
        o += draw_contours(project_xy(m), kind, fid + "-back-" + kind, tk)
    o += draw_contours(project_xy(fw_["BOOT actuator"]), "boot", fid + "-back-boot", tk)
    bx, by = tk(xs, ys)
    o.append(line(fid + "-bl", [(bx - 8, by + 8), (bx - 60, by + 90)], "#e03131", 1))
    o.append(text(bx - 150, by + 92, f"BOOT: Ø{k.BOOT_HOLE_D:g} hole\nthrough leg + plate", 14, fa))
    o += dim(tk(-k.NOTCH_W/2, -R - 3), tk(k.NOTCH_W/2, -R - 3), f"cable notch {k.NOTCH_W:g}", fa, (-50, 8))
    o += dim(tk(-geo["xo"], k.Y_H + 9), tk(geo["xo"], k.Y_H + 9), f"pin {2*geo['xo']:.1f} long", fa, (-40, -26))
    o.append(text(Xb - 70, Yb - PX*float(cbb[1, 1]) - 90, "from behind, folded", 15, fa))
    xl = Xb + PX*R + 30
    o += dim((xl, Ys - PX*float(cbb[1, 1])), (xl, Ys - PX*float(cbb[0, 1])),
             f"{cbb[1, 1] - cbb[0, 1]:.1f} tall\nwith the\ncrown", fa, (8, -26))
    o.append(text(fx + 30, fy + 790, f"Folded it is a Ø{2*R:.1f} × {zb - zf:.2f} puck: the leg lies flush in a well over the plate. Its\n"
                  f"BOOT hole lines up with the plate's, so the stylus goes straight in, folded or open\n"
                  f"(open: {geo['Z_PL'] - top:.1f} deep). Purple = leg, pin; red = BOOT switch.", 14, fa))
    ops.extend(o)

    # ---- E: plan of the footprint, tip angles ----
    fx, fy, fw, fh = slot(D_, "E")
    fid = P + "e"
    o = frame(fid, fx, fy, fw, fh, "E · Plan from above: footprint, centre of mass, tip angles, 6 px/mm")
    Xp, Yp = fx + 430, fy + 110 - PX*float(cable_bb[0, 1])
    tp = lambda X, Y: (Xp - PX*X, Yp + PX*Y)             # front (+Y) at the bottom, your right on the right
    for kind, m in (("plug", cable), ("rocker", legp), ("case", case), ("plug", body)):
        o += draw_contours(project_xy(W(m)), kind, fid + "-" + kind, tp)
    sp = [tp(*p) for p in poly] + [tp(*poly[0])]
    o.append(line(fid + "-sup", sp, "#e03131", 2, "dashed"))
    cx, cy = tp(com[0], com[1])
    o.append(dot(fid + "-com", cx, cy, "#e03131", 6))
    o.append(line(fid + "-cl", [(cx, cy), (Xp + PX*R + 50, cy + 70)], "#e03131", 1))
    o.append(text(Xp + PX*R + 54, cy + 60, f"centre of mass\n{com[2]:.1f} up, {wt/9.81e-3:.0f} g", 14, fid))
    names = lambda m: "sideways" if abs(m[0]) > 4 else "forward" if m[1] > com[1] else "backward"
    tips = K.tip_angle(poly, com, wt)
    for mid, ang in tips:
        mx, my = tp(*mid)
        nm = names(mid)
        ax_ = Xp + (PX*R + 50)*(1 if mx > cx else -1)
        lx = {"forward": (mx - 50, tp(0, case_bb[1, 1])[1] + 40), "backward": (Xp + PX*R + 50, my - 18),
              "sideways": (ax_ if mx > cx else ax_ - 110, my - 18)}[nm]
        o.append(line(fid + "-tl", [(mx, my), (lx[0] + (0 if lx[0] > mx else 100), lx[1] + 18)], "#868e96", 1))
        o.append(text(lx[0], lx[1], f"tips {nm}\nat {ang:.1f}°", 14, fid))
    worst = min(min(K.tip_angle(poly, com, wt, F, notch_w), key=lambda t: t[1])[1]
                for F in (k.CABLE_N*back, np.array([0, 0, -k.CABLE_N])))
    o.append(text(fx + 30, fy + 30, "front (you) at the bottom", 15, fid))
    # forward margin by lean: the build's own table (it stands on the heel's back edge)
    cc = K._centroid_all(st)
    heel_back = np.array([0.0, -R, geo["Z_BACK"] - k.BACK_CHAMFER])
    row = []
    for ln in (15, 20, 25, 30, 35, round(lean, 1)):
        p, q = K._rot_pt(cc, 90 + ln), K._rot_pt(heel_back, 90 + ln)
        row.append(f"{ln:g}°→{math.degrees(math.atan2(q[1] - p[1], p[2] - q[2])):.0f}°")
    o.append(text(fx + 30, fy + 780, f"Red dashes = where it touches the desk (heel flat + leg foot). With 1 N on the cable (back\n"
                  f"along the desk or straight down) every edge still holds to {worst:.1f}°. Why {lean:.0f}° of lean: it is\n"
                  f"front-heavy, so less lean falls on its face. Forward margin by lean (build's own table):\n"
                  f"{', '.join(row)}.", 14, fid))
    ops.extend(o)

    for e in ops:                                          # whole pixels are plenty, and keep the paste small
        for f in ("x", "y", "width", "height"):
            if f in e: e[f] = round(float(e[f]))
        if "points" in e: e["points"] = [[round(float(u)), round(float(v))] for u, v in e["points"]]
    json.dump([{"kind": "put", "drafts": ops}], open(out, "w"), separators=(",", ":"), ensure_ascii=False)
    print(f"{len(ops)} elements -> {out}")


def union_all(ms):
    out = ms[0]
    for m in ms[1:]: out = out + m
    return out


if __name__ == "__main__":
    main()
