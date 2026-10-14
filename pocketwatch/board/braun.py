#!/usr/bin/env python3
"""
Measured schematics of the Braun family (stand + clip) for the pocketwatch whiteboard, row "braun".
Flat sections and elevations cut from build_braun.py's own solids, in the frame-A colour key, with
dimension lines whose numbers come from the model or the design's constants.

  B  stand: side section on the face centre line (X = glass centre), plug + cable dashed behind the cut
  C  stand: front elevation (face slice 0.6 behind the face: grille, ring, window, glass)
  D  clip:  clamp section from above through the screw (Z = CZ), monitor edge at 20 mm, 8-32 range
  E  clip:  front elevation beside the monitor

  ~/.venvs/cad/bin/python pocketwatch/board/braun.py /tmp/ops-braun.json
"""
import sys, io, json, math, contextlib
from dataclasses import replace
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pocketwatch/styles/braun"); sys.path.insert(0, "pocketwatch/board")
import numpy as np, manifold3d as m3
from schem import *
import build_braun as B
from build_pocketwatch import Badge, Case, bbox

D = "braun"
P = f"ms-{D}"
GHOST = "#495057"


def cs_contours(cs, swap):
    """CrossSection polygons mapped to world 2D by `swap` (a function of the section's (u, v))."""
    return [[swap(*p) for p in c] for c in cs.simplify(0.05).to_polygons()]


def section_xz(m, y):
    """Slice on the plane Y = y: contours in world (X, Z)."""
    return cs_contours(m.rotate([90, 0, 0]).slice(y), lambda u, v: (u, -v))


def section_xy(m, z):
    return cs_contours(m.slice(z), lambda u, v: (u, v))


def project_yz(m):
    return cs_contours(m.rotate([0, 90, 0]).project(), lambda u, v: (v, u))


def ghost(contours, stem, to_board, color=GHOST):
    """Dashed, unfilled outline: something behind the cut or out of sight."""
    out = []
    for c in contours:
        if len(c) < 3 or abs(signed_area(c)) < 0.05: continue
        e = poly_el([to_board(*p) for p in c], "plug", stem)
        e.update(backgroundColor="transparent", strokeColor=color, strokeStyle="dashed")
        out.append(e)
    return out


def hline(x0, y0, w, stem, color="#495057", width=2, dashed=False):
    e = {"id": uid(stem), "type": "line", "x": round(x0, 1), "y": round(y0, 1), "width": round(w, 1), "height": 0,
         "points": [[0, 0], [round(w, 1), 0]], "strokeColor": color, "strokeWidth": width, "roughness": 0}
    if dashed: e["strokeStyle"] = "dashed"
    return e


def seg(p0, p1, stem, color="#495057", dashed=True):
    (x0, y0), (x1, y1) = p0, p1
    e = {"id": uid(stem), "type": "line", "x": round(x0, 1), "y": round(y0, 1), "width": round(abs(x1 - x0), 1),
         "height": round(abs(y1 - y0), 1), "points": [[0, 0], [round(x1 - x0, 1), round(y1 - y0, 1)]],
         "strokeColor": color, "strokeWidth": 1, "roughness": 0}
    if dashed: e["strokeStyle"] = "dashed"
    return e


def slab(x0, y0, x1, y1, stem):
    """The monitor: a plain grey outline, unfilled, so draw order never matters (the board lifts rectangles
    above lines); whatever it hides is left out or drawn dashed instead."""
    e = poly_el([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "base", stem)
    e.update(backgroundColor="transparent", strokeWidth=2)
    return e


def dot(x, y, stem, color="#9c36b5", r=6):
    return {"id": uid(stem), "type": "ellipse", "x": round(x - r, 1), "y": round(y - r, 1), "width": 2*r, "height": 2*r,
            "strokeColor": color, "backgroundColor": color, "fillStyle": "solid", "roughness": 0}


def as_ellipse(e):
    """A small round polygon (a grille hole) as an ellipse element: same look, a tenth of the ops."""
    if e["type"] != "line" or not e.get("polygon") or len(e["points"]) < 12: return e
    if max(e["width"], e["height"]) > 3*PX or abs(e["width"] - e["height"]) > 0.6: return e
    keep = {k: e[k] for k in ("id", "x", "y", "width", "height", "strokeColor", "backgroundColor", "fillStyle", "strokeWidth", "roughness")}
    return {**keep, "type": "ellipse"}


def quiet(f, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        return f(*a)


def main():
    out = sys.argv[1]
    b = Badge()
    c = replace(Case(), LIP_T=B.LIP_T, LIP_BEVEL=B.LIP_BEVEL)
    ring = B.orange_ring()
    model = {v: B.build(b, c, v) for v in ("stand", "clip")}

    def world_parts(v):
        feats, body, plate, geo = model[v]
        W = lambda m: B.to_world(m, v)
        fw = {f.name: W(f.solid()) for f in feats}
        badge = [("badge", fw["disc + tab"])] + [("header", m) for n, m in fw.items() if n.startswith("header")] + \
                [("boot", m) for n, m in fw.items() if n.startswith(c.BUTTON)]
        shell, mould, cable, _ = B.plug_and_cable(geo, v)
        return dict(body=W(body), plate=W(plate), ring=W(ring.translate([0, 0, geo["front"]])), badge=badge,
                    plug=W(shell + mould), cable=W(cable), disc=fw["disc + tab"], geo=geo)

    win_face = b.r - c.LIP_OVERLAP + c.LIP_BEVEL           # window radius at the face
    win_glass = b.r - c.LIP_OVERLAP                        # at the glass
    ring_d = 2*(B.RING_R0 + B.RING_W)
    stylus_top = b.pcb_back_z + b.sw_cap_h                 # badge z of the BOOT actuator top

    # =============================== B: stand side section =========================================
    S = world_parts("stand")
    geo = S["geo"]
    gc = B.pt_world((0, 0, 0), "stand")                    # glass centre (18, 2.4, 27)
    xcut = float(gc[0])
    bb = bbox(S["body"])
    H, DEP, LEN = bb[1, 2] - bb[0, 2], bb[1, 1] - bb[0, 1], bb[1, 0] - bb[0, 0]
    fx, fy, fw_, fh = slot(D, "B")
    Y0, Z0 = fx + 250, fy + 600
    tb = lambda Y, Z: (Y0 + PX*Y, Z0 - PX*Z)
    o = frame(f"{P}-side", fx, fy, fw_, fh, f"B · Braun STAND: side section on the face centre (X = {xcut:g}), 6 px/mm")
    o.append(hline(fx + 30, Z0, fw_ - 60, f"{P}-side-desk"))
    for kind, m in (("case", S["body"]), ("plate", S["plate"]), ("rocker", S["ring"])) + tuple(S["badge"]):
        o += draw_contours(section_yz(m, xcut), kind, f"{P}-side-{kind}", tb)
    o += ghost(project_yz(S["plug"] + S["cable"]), f"{P}-side-plugghost", tb)
    # numbers
    o += dim((Y0 - 130, Z0), (Y0 - 130, Z0 - PX*H), f"{H:.0f}", f"{P}-side", (-34, -8))
    o += dim((Y0 - 30, Z0), (Y0 - 30, Z0 - PX*gc[2]), f"glass\ncentre {gc[2]:.0f}", f"{P}-side", (-88, -20))
    o += dim(tb(0, -3.5), tb(DEP, -3.5), f"depth {DEP:.0f}", f"{P}-side", (-40, 4))
    lx, lz = tb(0, gc[2] + b.r + 4)
    o += dim((lx, lz - 40), (lx + PX*B.LIP_T, lz - 40), "", f"{P}-side")
    o.append(text(lx - 150, lz - 74, f"lip {B.LIP_T:g} in front of the glass\n(Ø{2*win_glass:.1f} window, bevel to Ø{2*win_face:.1f})", 14, f"{P}-side"))
    yw0, yw1 = gc[1] + geo["Z_CASE"], gc[1] + geo["back"]
    o += dim(tb(yw0, 6.0), tb(yw1, 6.0), f"well {yw1 - yw0:.1f} deep", f"{P}-side", (-40, -24))
    # BOOT stylus, off this cut
    bw = B.pt_world((geo["sw"][c.BUTTON], b.sw_y, stylus_top), "stand")
    sx0, sz = tb(bw[1], bw[2]); sx1, _ = tb(bb[1, 1] + 8, bw[2])
    o.append(seg((sx0, sz), (sx1, sz), f"{P}-side-stylus", "#e03131"))
    o.append(text(sx1 + 8, sz - 18, f"BOOT: Ø{B.PIN_D:g} stylus, {geo['back'] - stylus_top:.1f} from the\n"
                                    f"back face (at X = {bw[0]:.1f}, off this cut)", 14, f"{P}-side"))
    # stability: centre of mass and tip angle, recomputed with the build's own functions
    mass, com = quiet(B.stand_checks, b, c, model["stand"][1], model["stand"][2], ring, geo)
    exit_pt = B.pt_world((B.FACE/2 - B.CABLE_D/2, geo["plug_end"] + B.BEND_R, geo["back"]), "stand")
    poly = np.array(S["body"].slice(0.15).hull().to_polygons()[0])
    th0 = B.tip_angle(poly, com, mass*9.81e-3, exit_pt, np.zeros(3))[0]
    cx, cz = tb(com[1], com[2])
    o.append(dot(cx, cz, f"{P}-side-com"))
    o.append(text(cx + 10, cz - 4, f"CoM ({mass:.0f} g)", 14, f"{P}-side"))
    ex, ez = tb(bb[1, 1] + 14, exit_pt[2])
    o.append(text(ex, ez - 66, f"cord out the back,\n{exit_pt[2]:.1f} above the desk", 14, f"{P}-side"))
    o.append(text(Y0 + PX*DEP + 20, Z0 - PX*H, f"face vertical (0° tilt)\ntips at {th0:.1f}° (weight only)", 15, f"{P}-side"))
    o.append(text(fx + 30, fy + 790,
                  f"Blue = body (case fused into the block, one print), purple = orange ring, orange = back plate,\n"
                  f"green = badge, cyan = headers. Dashed = USB-C plug + cord behind the cut. Footprint {LEN:.0f} x {DEP:.0f},\n"
                  f"{B.INFILL_STAND*100:.0f} % infill. Cut from build_braun.py's solids.", 14, f"{P}-side"))
    ops.extend(o)

    # =============================== C: stand front elevation ======================================
    fx, fy, fw_, fh = slot(D, "C")
    X0, Zf = fx + 450, fy + 560
    tb = lambda X, Z: (X0 + PX*X, Zf - PX*Z)
    o = frame(f"{P}-front", fx, fy, fw_, fh, "C · Braun STAND: front elevation (as you sit at it), 6 px/mm")
    o.append(hline(fx + 30, Zf, fw_ - 60, f"{P}-front-desk"))
    yf = 0.6                                                  # 0.6 behind the face: grille, ring groove, window
    o += draw_contours(section_xz(S["body"], yf), "case", f"{P}-front-case", tb)
    o += draw_contours(section_xz(S["ring"], yf), "rocker", f"{P}-front-ring", tb)
    glass = S["disc"].rotate([90, 0, 0]).project() ^ m3.CrossSection.circle(win_glass, 96).translate([gc[0], -gc[2]])
    o += draw_contours(cs_contours(glass, lambda u, v: (u, -v)), "badge", f"{P}-front-glass", tb)
    o += dim(tb(bb[0, 0], -4), tb(bb[1, 0], -4), f"{LEN:.0f}", f"{P}-front", (-10, 4))
    o += dim(tb(bb[1, 0] + 4, 0), tb(bb[1, 0] + 4, H), f"{H:.0f}", f"{P}-front", (8, -8))
    o += dim(tb(gc[0] - ring_d/2, gc[2]), tb(gc[0] + ring_d/2, gc[2]), f"ring Ø{ring_d:.1f}", f"{P}-front", (-40, -26))
    o += dim(tb(gc[0] - win_face, gc[2] - 8), tb(gc[0] + win_face, gc[2] - 8), f"window Ø{2*win_face:.1f}", f"{P}-front", (-50, 4))
    o += dim(tb(gc[0], H + 3), tb(bb[1, 0], H + 3), f"{bb[1, 0] - gc[0]:.0f}", f"{P}-front", (-10, -24))
    o += dim(tb(bb[0, 0], H + 3), tb(gc[0], H + 3), f"grille field {B.GRILLE_L:g} + face {B.FACE:g}", f"{P}-front", (-140, -24))
    bwx, bwz = tb(bw[0], bw[2])
    o.append({"id": uid(f"{P}-front-boot"), "type": "ellipse", "x": bwx - 12, "y": bwz - 12, "width": 24, "height": 24,
              "strokeColor": "#e03131", "backgroundColor": "transparent", "strokeStyle": "dashed", "strokeWidth": 2, "roughness": 0})
    o.append(text(fx + 30, fy + 630,
                  f"Grille: 9 x 15 blind holes Ø{B.HOLE_D:g}, pitch {B.PITCH:g}, {B.HOLE_DEPTH:g} deep (decorative).\n"
                  f"Nothing to touch on the face. BOOT (dashed red) is pressed from the BACK with a Ø{B.PIN_D:g} stylus.\n"
                  f"Crown (USB-C) points left: rotate the display 90° in firmware. Glass centre {gc[2]:.0f} up.", 14, f"{P}-front"))
    o.append(text(fx + 30, fy + 790,
                  f"Blue = body, cut {yf:g} behind the face so the grille holes, ring groove and window show;\n"
                  f"purple = the orange ring, green = glass seen through the window.", 14, f"{P}-front"))
    ops.extend(o)

    # =============================== D: clip clamp section from above ===============================
    C = world_parts("clip")
    geo = C["geo"]
    t = 20.0
    cs = B.clamp_set(t)
    cl = B.clamp()
    fx, fy, fw_, fh = slot(D, "D")
    X0, Yb = fx + 320, fy + 680
    tb = lambda X, Y: (X0 + PX*X, Yb - PX*Y)
    zc = B.CZ
    o = frame(f"{P}-d", fx, fy, fw_, fh, f"D · Braun CLIP: clamp section from above through the screw (Z = {zc:g}), 6 px/mm")
    mx0 = -40.0
    o.append(slab(*tb(mx0, t), *tb(0, 0), f"{P}-d-monitor"))
    o.append(text(*tb(mx0 + 2, t - 1), f"monitor\nedge {t:g}\n(shown)", 14, f"{P}-d"))
    for kind, m in (("case", C["body"]), ("plug", C["plug"]), ("base", cl),
                    ("rocker", cs["pad"]), ("rocker", cs["nut"]), ("rocker", cs["screw"]), ("rocker", cs["knob"])):
        o += draw_contours(section_xy(m, zc), kind, f"{P}-d-{kind}", tb)
    for tt in (B.EDGE_MIN, B.EDGE_MAX):          # monitor back and knob at the two ends of the range
        s2 = B.clamp_set(tt)
        o.append(seg(tb(mx0, tt), tb(0, tt), f"{P}-d-range", "#868e96"))
        o += ghost(section_xy(s2["knob"], zc), f"{P}-d-knobghost", tb, "#9c36b5")
        o.append(text(*tb(mx0 - 4, tt + 1.2), f"{tt:g}", 14, f"{P}-d"))
    o += dim(tb(mx0 + 30, 0), tb(mx0 + 30, B.EDGE_MAX), "", f"{P}-d")
    o.append(text(*tb(mx0 - 8, B.EDGE_MAX + 7), f"clamps {B.EDGE_MIN:g}-{B.EDGE_MAX:g}\n(dashed: back face, knob)", 14, f"{P}-d"))
    o += dim(tb(-B.LIP_REACH, -B.JAW_T - 3), tb(0, -B.JAW_T - 3), f"lip {B.LIP_REACH:g}", f"{P}-d", (-40, 4))
    o += dim(tb(0, -B.JAW_T - 3), tb(B.CLIP_T[0] - B.FACE/2, -B.JAW_T - 3), f"{B.CLIP_T[0] - B.FACE/2:g}", f"{P}-d", (-4, 4))
    bbc = bbox(C["body"])
    o += dim(tb(bbc[1, 0] + 4, bbc[0, 1]), tb(bbc[1, 0] + 4, bbc[1, 1]), f"body {bbc[1, 1] - bbc[0, 1]:.0f}", f"{P}-d", (8, -8))
    sx, sy = tb(B.SCREW_X, cs["head"])
    o.append(text(sx + 50, sy - 6, f"knob Ø{B.KNOB_D:g} on an M4 x {B.M4_LEN:g} bolt head", 14, f"{P}-d"))
    nx, ny = tb(B.SCREW_X, B.NUT_Y0)
    o.append(text(nx + 50, ny - 6, f"M4 nut in the rear jaw ({B.JAW_Y1 - B.JAW_Y0:g} thick)", 14, f"{P}-d"))
    px_, py_ = tb(B.SCREW_X, t + B.PAD_T)
    o.append(text(px_ + 50, py_ - 4, f"pad Ø{B.PAD_D:g} threads onto the bolt tip", 14, f"{P}-d"))
    dx, dy = tb(B.TAIL_XC, B.BAR_Y1 + 6)
    o.append(text(dx + 8, dy - 30, f"dovetail ({B.TAIL_ROOT:g} root, {B.TAIL_CLR:g} clear):\nclamp slides up into the body", 14, f"{P}-d"))
    tx, ty = tb(B.CLIP_T[0], -B.LIP_T + B.CLIP_T[1])
    o.append(text(tx + 40, ty + 12, "plug in the trough (dark grey)", 14, f"{P}-d"))
    mass_c, com_c, _ = quiet(B.clip_checks, C["body"], C["ring"], C["plate"], geo, b)
    F = B.KNOB_TORQUE/(B.SCREW_K*4.0)
    sf = 2*B.MU*F/(mass_c*9.81e-3 + 1.0)
    o.append(text(fx + 30, fy + 790,
                  f"Grey = clamp (printed flat), purple = pad, bolt, nut, knob; blue = clip body, dark grey = plug.\n"
                  f"Finger-tight knob ({B.KNOB_TORQUE:g} N mm) = {F:.0f} N clamp; grip SF {sf:.0f} on {mass_c:.0f} g + 1 N pull "
                  f"(mu {B.MU:g}).\nScreen-side reach: only the {B.LIP_REACH:g} lip. Monitor drawn at X < 0, cut at X = {mx0:g}.", 14, f"{P}-d"))
    ops.extend(o)

    # =============================== E: clip front elevation =======================================
    fx, fy, fw_, fh = slot(D, "E")
    X0, Zf = fx + 330, fy + 228
    tb = lambda X, Z: (X0 + PX*X, Zf - PX*Z)
    gcc = B.pt_world((0, 0, 0), "clip")
    o = frame(f"{P}-e", fx, fy, fw_, fh, "E · Braun CLIP: front elevation beside the monitor, 6 px/mm")
    zlo, zhi = -82.0, bbc[1, 2] + 6                         # cord cut off at Z = -80
    o += draw_contours(project_xz(C["cable"] ^ B.box(-50, 80, -50, 100, zlo + 2, 50)), "plug", f"{P}-e-cable", tb)
    o += draw_contours(project_xz(cl ^ B.box(0, 50, -10, 60, -100, 50)), "base", f"{P}-e-clamp", tb)  # beside it
    o.append(slab(*tb(-40, zhi), *tb(0, zlo), f"{P}-e-monitor"))
    o += ghost(project_xz(cs["knob"]), f"{P}-e-knobghost", tb, "#9c36b5")
    o.append(text(*tb(-38, zhi - 3), "monitor\n(right edge\nat X = 0)", 14, f"{P}-e"))
    front_cl = cl ^ B.box(-50, 50, -10, 0.01, -100, 50)                     # lip + spine face, in front of it
    o += draw_contours(project_xz(front_cl), "base", f"{P}-e-lip", tb)
    yf = bbc[0, 1] + 0.6
    o += draw_contours(section_xz(C["body"], yf), "case", f"{P}-e-case", tb)
    o += draw_contours(section_xz(C["ring"], yf), "rocker", f"{P}-e-ring", tb)
    glass = C["disc"].rotate([90, 0, 0]).project() ^ m3.CrossSection.circle(win_glass, 96).translate([gcc[0], -gcc[2]])
    o += draw_contours(cs_contours(glass, lambda u, v: (u, -v)), "badge", f"{P}-e-glass", tb)
    bwc = B.pt_world((geo["sw"][c.BUTTON], b.sw_y, stylus_top), "clip")
    bx, bz = tb(bwc[0], bwc[2])
    o.append({"id": uid(f"{P}-e-boot"), "type": "ellipse", "x": bx - 12, "y": bz - 12, "width": 24, "height": 24,
              "strokeColor": "#e03131", "backgroundColor": "transparent", "strokeStyle": "dashed", "strokeWidth": 2, "roughness": 0})
    o += dim(tb(bbc[0, 0], bbc[1, 2] + 4), tb(bbc[1, 0], bbc[1, 2] + 4), f"{bbc[1, 0] - bbc[0, 0]:.0f}", f"{P}-e", (-10, -24))
    o += dim(tb(bbc[1, 0] + 4, bbc[0, 2]), tb(bbc[1, 0] + 4, bbc[1, 2]), f"{bbc[1, 2] - bbc[0, 2]:.0f}", f"{P}-e", (8, -8))
    o += dim(tb(bbc[1, 0] + 16, gcc[2]), tb(bbc[1, 0] + 16, bbc[1, 2]), f"glass centre\n{bbc[1, 2] - gcc[2]:.0f} below the top", f"{P}-e", (8, -20))
    o += dim(tb(gcc[0] - ring_d/2, gcc[2]), tb(gcc[0] + ring_d/2, gcc[2]), f"ring Ø{ring_d:.1f}", f"{P}-e", (-40, -26))
    o += dim(tb(0, B.CZ0 - 3), tb(bbc[0, 0], B.CZ0 - 3), f"{bbc[0, 0]:g}", f"{P}-e", (-4, 4))
    xk = B.SCREW_X - B.KNOB_D/2 - 4                                      # left of the knob's outline
    o += dim(tb(xk, B.CZ0), tb(xk, B.CZ1), f"clamp\n{B.CZ1 - B.CZ0:g}", f"{P}-e", (-60, -20))
    o.append(text(*tb(bbc[1, 0] + 6, bbc[0, 2] + 4), f"cord hangs down\nthe back", 14, f"{P}-e"))
    o.append(text(fx + 30, fy + 790,
                  f"Crown (USB-C) down: rotate the display 180°. Grey = clamp: only the {B.LIP_REACH:g} lip sits on the bezel.\n"
                  f"Touch: the knob (dashed purple, behind the monitor); BOOT (dashed red) from the back, Ø{B.PIN_D:g} stylus,\n"
                  f"{geo['back'] - stylus_top:.1f} deep. Body cut {yf - bbc[0, 1]:g} behind the face; dark grey = cord.", 14, f"{P}-e"))
    ops.extend(o)

    json.dump([{"kind": "put", "drafts": [as_ellipse(e) for e in ops if e.get("text", "x") != ""]}], open(out, "w"), separators=(",", ":"))
    print(f"{len(ops)} elements -> {out}")
    print(f"stand {LEN:.0f} x {DEP:.0f} x {H:.0f}, glass centre {gc[2]:.1f}, tip {th0:.1f}, mass {mass:.0f}; "
          f"clip body {bbc[1] - bbc[0]}, F {F:.0f} N, SF {sf:.1f}")


if __name__ == "__main__":
    main()
