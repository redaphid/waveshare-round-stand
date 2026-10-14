#!/usr/bin/env python3
"""
Measured schematics of the pedestal (desk pebble, puck shape) for the pocketwatch whiteboard's design gallery,
row "pedestal": flat sections and an elevation cut from the same solids build_pedestal.py checks.

  ~/.venvs/cad/bin/python pocketwatch/board/pedestal.py /tmp/ops.json

Frames (slots from schem.slot):
  B  ms-pedestal-side   side section on the centre line (X = 0): body, fused case, plate, badge, plug, cable
  C  ms-pedestal-front  front elevation as you sit at it
  D  ms-pedestal-d      section through the BOOT axis: the stylus path through the plate's hole
"""
import sys, json, math, io, contextlib
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pocketwatch/stands/pedestal"); sys.path.insert(0, "pocketwatch/board")
import numpy as np, manifold3d as m3
from schem import *
import build_pedestal as P
import build_pocketwatch_usb as usb
from build_pocketwatch import Badge, Case

D = "pedestal"


def hline(stem, x0, y0, x1, y1, color="#495057", width=1, dashed=False):
    e = {"id": uid(stem), "type": "line", "x": round(x0, 1), "y": round(y0, 1), "width": round(x1 - x0, 1),
         "height": round(y1 - y0, 1), "points": [[0, 0], [round(x1 - x0, 1), round(y1 - y0, 1)]],
         "strokeColor": color, "strokeWidth": width, "roughness": 0}
    if dashed: e["strokeStyle"] = "dashed"
    return e


def dot(stem, x, y, r=6, color="#1e1e1e"):
    return {"id": uid(stem), "type": "ellipse", "x": round(x - r, 1), "y": round(y - r, 1), "width": 2*r, "height": 2*r,
            "strokeColor": color, "backgroundColor": color, "fillStyle": "solid", "roughness": 0}


def cs_to_xz(cs):
    return [[(p[0], -p[1]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def proj(m):
    """Front projection as a CrossSection (in project_xz's rotated coords), for booleans before drawing."""
    return m.rotate([90, 0, 0]).project()


def setup():
    b, c = Badge(), Case()
    feats, case, plate, plate_h, sw, geo = P.case_parts(b, c)
    geo["case"] = case
    H = P.height(b, geo)
    F = P.Frame(H)
    body, gs = P.build_body(P.FINAL, b, c, geo, F)
    with contextlib.redirect_stdout(io.StringIO()):
        st = P.stability(P.FINAL, b, geo, body, F)
    return b, c, feats, plate_h, sw, geo, H, F, body, gs, st


def main():
    out = sys.argv[1]
    b, c, feats, plate_h, sw, geo, H, F, body, gs, st = setup()
    W = F.w
    body_case, body_rest = W(body ^ geo["env"]), W(body - geo["env"])      # the proven case, fused in: blue
    body_w = W(body)
    plate_w = W(plate_h)
    shell, omold = P.plug_solids(b, c, geo)
    pts, (cy, ch) = P.cable_path(F, b, geo, run=45.0)
    cable = P.tube(pts, P.CABLE_D/2, 16)
    plug = [W(shell), W(omold), cable]
    fw_ = {f.name: W(f.solid()) for f in feats if not f.name.startswith("plug")}
    badge = [("badge", m) for n, m in fw_.items() if not n.startswith(("header", "BOOT"))] + \
            [("header", m) for n, m in fw_.items() if n.startswith("header")] + \
            [("boot", m) for n, m in fw_.items() if n.startswith("BOOT")]
    parts = [("base", body_rest), ("case", body_case), ("plate", plate_w)] + [("plug", m) for m in plug] + badge

    bb = np.array(body_w.bounding_box()).reshape(2, 3)
    H_top, W_body = float(bb[1, 2]), float(bb[1, 0] - bb[0, 0])
    foot = body_w.slice(0.05).hull().bounds()                # (xmin, ymin, xmax, ymax) of the footprint
    glass = F.pw([0, 0, 0])
    y_lo, y_hi = float(bb[0, 1]), float(pts[-1][1])
    bx, by = sw
    cap = b.pcb_back_z + b.sw_cap_h                            # BOOT cap top, badge z
    z_back = geo["Z_CASE"]                                     # the plate's back face, flush with the case back
    depth = z_back - cap
    up = np.array([0, P.S, P.C])                               # up the face, world
    back = np.array([0, P.C, -P.S])                            # badge +z (out of the back), world

    # ---- B and D: sections in world Y-Z -----------------------------------------------------------------
    for letter, fid, xcut, title in (
            ("B", f"ms-{D}-side", 0.0, "S · Side section on the centre line (X = 0), 6 px/mm, front to the left"),
            ("D", f"ms-{D}-d", float(bx), f"K · Section through the BOOT axis (X = {bx:.1f}), 6 px/mm")):
        fx, fy, fw, fh = slot(D, letter)
        Y0, Z0 = fx + fw/2 - PX*(y_lo + y_hi)/2 + 30, fy + 680
        tb = lambda Y, Z: (Y0 + PX*Y, Z0 - PX*Z)
        ops_f = frame(fid, fx, fy, fw, fh, title)
        for kind, m in parts:
            ops_f += draw_contours(section_yz(m, xcut), kind, f"{fid}-{kind}", tb)
        ops_f.append(hline(fid + "-desk", fx + 30, Z0, fx + fw - 30, Z0, width=2))
        ops_f.append(text(fx + fw - 70, Z0 - 24, "desk", 14, fid))
        xl = Y0 + PX*y_lo                                      # body front at the desk, board x
        gx, gz = tb(glass[1], glass[2])
        if letter == "B":
            # heights, left of the body
            ops_f += dim((xl - 210, Z0), (xl - 210, Z0 - PX*H_top), f"{H_top:.0f}\ntall", fid, (-50, -16))
            ops_f.append(hline(fid + "-ext", xl - 220, Z0 - PX*H_top, Y0 + PX*float(bb[0, 1] + 24), Z0 - PX*H_top, "#adb5bd", dashed=True))
            ops_f += dim((xl - 140, Z0), (xl - 140, gz), f"glass\ncentre\n{glass[2]:.1f}", fid, (-62, -24))
            ops_f.append(hline(fid + "-ext", xl - 150, gz, gx, gz, "#adb5bd", dashed=True))
            # the face plane and its lean
            pf = F.pw([0, 0, gs["z_f"]])
            a0, a1 = pf - up*26, pf + up*33
            ops_f.append(hline(fid + "-face", *tb(a0[1], a0[2]), *tb(a1[1], a1[2]), "#1971c2", dashed=True))
            vx, vz = tb(a0[1], a0[2])
            ops_f.append(hline(fid + "-vert", vx, vz, vx, vz - PX*40*P.C, "#adb5bd", dashed=True))
            ops_f.append(text(vx - 225, gz - 84,
                              f"face leans {P.THETA:g}° back;\nglass {-gs['z_f']:.1f} behind the face\nin a 45° trim cone\n+ Ø{2*P.R_CUP:g} cup", 14, fid))
            # footprint and cable exit, under the desk line
            ops_f += dim(tb(foot[1], -5), tb(foot[3], -5), f"footprint {foot[3] - foot[1]:.0f} deep", fid, (-70, 4))
            ops_f += dim(tb(0, -12), tb(float(bb[1, 1]), -12), f"cable leaves {bb[1, 1]:.0f} behind the dial centre", fid, (70, -9))
            ops_f.append(hline(fid + "-ext", gx, gz, gx, Z0 + PX*14, "#adb5bd", dashed=True))
            # centre of mass, with a leader from the left
            cgx, cgz = tb(st["cg"][1], st["cg"][2])
            ops_f.append(dot(fid + "-cg", cgx, cgz, 6))
            tx = xl - 125
            ops_f.append(text(tx, cgz + 30, f"CG with badge\n+ plug (Y {st['cg'][1]:+.1f},\nZ {st['cg'][2]:.0f})", 14, fid))
            ops_f.append(hline(fid + "-lead", tx + 70, cgz + 28, cgx - 6, cgz + 2, "#868e96"))
            pe = pts[0]
            px_, pz_ = tb(pe[1], pe[2])
            ops_f.append(text(px_ + 70, pz_ - 70, f"straight plug ≤ {P.PLUG_L:g} long\n(the crown, pointing down)", 14, fid))
            ops_f.append(text(Y0 + PX*(cy + 12), Z0 - PX*18, f"Ø{P.CABLE_D:g} cable, one R{P.R_BEND:g} bend,\n"
                              f"then flat on the desk", 14, fid))
            nz = F.pw([0, -(geo["R_REAR"] + 0.6), geo["Z_CASE"]])
            nx_, nz_ = tb(nz[1], nz[2])
            ops_f.append(text(nx_ + 60, nz_ - 40, "pry notch at the\ntop of the plate rim", 14, fid))
            ops_f.append(hline(fid + "-lead", nx_ + 58, nz_ - 22, nx_ + 4, nz_ - 2, "#868e96"))
            ops_f.append(text(fx + 30, fy + 800,
                              f"Grey = body, blue = the proven USB-only case fused in (one print, front face down), orange = back plate,\n"
                              f"green = badge, dark grey = plug + cable. Tips at {st['tip0']:.1f}° unloaded, {st['tip']:.1f}° with a 1 N sideways\n"
                              f"cable pull ({st['mass']:.0f} g body at 20% infill). Cut from build_pedestal.py's solids.", 14, fid))
        else:
            # the stylus: Ø PIN_D from the pressed cap out along the badge axis, then a grip
            pin = m3.Manifold.cylinder(24, usb.PIN_D/2, usb.PIN_D/2, 24).translate([bx, by, cap - c.SW_TRAVEL])
            grip = m3.Manifold.cylinder(34, 3.5, 3.5, 32).translate([bx, by, cap + 24])
            for m in (pin, grip):
                ops_f += draw_contours(section_yz(W(m), xcut), "rocker", f"{fid}-stylus", tb)
            p0, p1 = F.pw([bx, by, z_back]), F.pw([bx, by, cap])
            q0, q1 = p0 + up*4.5, p1 + up*4.5
            ops_f += dim(tb(q0[1], q0[2]), tb(q1[1], q1[2]), "", fid)[:1]
            for p, q in ((p0, q0), (p1, q1)):
                ops_f.append(hline(fid + "-ext", *tb(p[1], p[2]), *tb(q[1], q[2]), "#adb5bd", dashed=True))
            mx, mz = tb(*((q0 + q1)/2)[1:])
            ops_f.append(text(mx + 70, mz - 90, f"{depth:.1f} deep: plate back\nface to the BOOT cap", 15, fid))
            ops_f.append(hline(fid + "-lead", mx + 68, mz - 66, mx + 2, mz - 4, "#868e96"))
            sx, sz = tb(*(p0 + back*30)[1:])
            ops_f.append(text(sx + 40, sz + 70, f"Ø{usb.PIN_D:g} stylus / SIM tool\nthrough the plate's hole", 14, fid))
            bt = F.pw([bx, by, cap])
            btx, btz = tb(bt[1], bt[2])
            ops_f.append(text(btx - 240, btz - 80, "BOOT (red), upper right\nseen from behind", 14, fid))
            ops_f.append(hline(fid + "-lead", btx - 80, btz - 56, btx - 4, btz - 2, "#868e96"))
            ops_f.append(text(fx + 30, fy + 800,
                              f"Purple = stylus (not printed), pressed {c.SW_TRAVEL:g} mm. It reaches BOOT square on, past the body and plate;\n"
                              f"a Ø12 grip clears from 12 mm behind the plate. BOOT position is a ±1 mm guess; the plate hole forgives it.", 14, fid))
        ops.extend(ops_f)

    # ---- C: front elevation (viewer at -Y) --------------------------------------------------------------
    fid = f"ms-{D}-front"
    fx, fy, fw, fh = slot(D, "C")
    X0, Zf = fx + fw/2, fy + 680
    tb = lambda X, Z: (X0 + PX*X, Zf - PX*Z)
    ops_f = frame(fid, fx, fy, fw, fh, "V · Front elevation (as you sit at it), 6 px/mm")
    pb = proj(body_w)
    seen = proj(W(feats[0].solid())) - pb                      # the badge where the body does not hide it
    ops_f += draw_contours(cs_to_xz(pb), "base", fid + "-base", tb)
    # the face's edges, true to the leaned plane: cup chamfer edge and cup bore (the trim cone runs in from there)
    for r_ in (P.R_CUP + P.CUP_CH, P.R_CUP):
        ring = [F.pw([r_*math.cos(t), r_*math.sin(t), gs["z_f"]]) for t in np.linspace(0, 2*math.pi, 97)[:-1]]
        ops_f.append(poly_el([tb(q[0], q[2]) for q in ring], "base", fid + "-cup"))
    ops_f += draw_contours(cs_to_xz(seen), "badge", fid + "-badge", tb)
    ops_f.append(hline(fid + "-desk", fx + 30, Zf, fx + fw - 30, Zf, width=2))
    # crown flutes along the stem's face
    p = P.SHAPES[P.FINAL]
    y0, y1 = gs["R_ARCH"] + P.FRONT_CH, p["Y_PLINTH"] - 1.0
    for i in range(P.FLUTES):
        xi = P.FLUTE_P*(i - (P.FLUTES - 1)/2)
        a, e = F.pw([xi, y0, gs["z_f"]]), F.pw([xi, y1, gs["z_f"]])
        ops_f.append(hline(fid + "-flute", *tb(a[0], a[2]), *tb(e[0], e[2]), "#495057"))
    gz = glass[2]
    ops_f += dim(tb(bb[0, 0], -5), tb(bb[1, 0], -5), f"{W_body:.0f} wide (plinth)", fid, (-60, 6))
    ops_f += dim(tb(-gs["R_ARCH"], H_top + 6), tb(gs["R_ARCH"], H_top + 6), f"puck Ø{2*gs['R_ARCH']:g}", fid, (-40, -26))
    zc = gz + (P.R_CUP + P.CUP_CH)*P.C + 1.2
    ops_f += dim(tb(-P.R_CUP, zc), tb(P.R_CUP, zc), f"cup Ø{2*P.R_CUP:g}", fid, (+150, -10))
    ops_f += dim(tb(-b.active_d/2, gz - 6), tb(b.active_d/2, gz - 6), f"display Ø{b.active_d:.1f}", fid, (-46, 4))
    xr = float(bb[1, 0]) + 10
    ops_f += dim(tb(xr, 0), tb(xr, H_top), f"{H_top:.0f}", fid, (8, -8))
    xg = float(bb[0, 0]) - 10
    ops_f += dim(tb(xg, 0), tb(xg, gz), f"{gz:.1f} to\nthe dial\ncentre", fid, (-80, -26))
    ops_f.append(hline(fid + "-ext", *tb(xg - 2, gz), *tb(-b.active_d/2, gz), "#adb5bd", dashed=True))
    sw0, sw1 = F.pw([0, y0, gs["z_f"]]), F.pw([0, y1, gs["z_f"]])
    ops_f.append(text(*tb(p["W_STEM"]/2 + 3, (sw0[2] + sw1[2])/2 + 3),
                      f"crown stem {p['W_STEM']:g} wide,\n{P.FLUTES} V-flutes, {P.FLUTE_P:g} pitch", 14, fid))
    ops_f.append(text(fx + 30, fy + 800,
                      f"Silhouette of the body (grey) with the badge (green) where it shows through the window. Nothing to press\n"
                      f"on the front: BOOT is from behind (frame K). Widths are true; heights of the leaned face read {P.C:.2f}x.", 14, fid))
    ops.extend(ops_f)

    json.dump([{"kind": "put", "drafts": ops}], open(out, "w"), separators=(",", ":"))
    print(f"{len(ops)} elements -> {out}")


if __name__ == "__main__":
    main()
