#!/usr/bin/env python3
"""
Measured schematics of the hood stand (row "hood" of the pocketwatch whiteboard), in the style of frames A-D:
flat sections and elevations cut from the solids build_hood.py checks, pastel fills, dimension lines.

  B  side section on the centre line (X = 0)
  C  front elevation (as you sit at it)
  D  section through BOOT (X = BOOT x): the stylus path through the back plate
  E  plan section through the base (Z = 4): coin wells, plug slot, cable tunnel, footprint

Writes draw-MCP ops (JSON) to the path given as the first argument; paste them with the `draw` tool.

  ~/.venvs/cad/bin/python pocketwatch/board/hood.py /tmp/ops-hood.json
"""
import sys, json, math, textwrap
sys.path.insert(0, "pocketwatch"); sys.path.insert(0, "pocketwatch/stands/hood"); sys.path.insert(0, "pocketwatch/board")
import numpy as np, manifold3d as m3
from schem import *
import build_hood as HD
from build_pocketwatch import Badge, Case, bbox, prism
from build_pocketwatch_usb import boot_hole_plate, PIN_D, BOOT_HOLE_D

D = "hood"
DESK = 730          # desk line, px below the frame top, in the elevations


def line(stem, pts, color="#495057", width=1, dashed=False):
    pts = np.asarray(pts, float)
    el = {"id": uid(stem), "type": "line", "x": round(float(pts[0, 0]), 1), "y": round(float(pts[0, 1]), 1),
          "width": round(float(np.ptp(pts[:, 0])), 1), "height": round(float(np.ptp(pts[:, 1])), 1),
          "points": [[round(float(x - pts[0, 0]), 1), round(float(y - pts[0, 1]), 1)] for x, y in pts],
          "strokeColor": color, "strokeWidth": width, "roughness": 0}
    if dashed: el["strokeStyle"] = "dashed"
    return el


def caption(fx, fy, fw, s):
    lines = textwrap.fill(s, 92).split("\n")
    return text(fx + 24, fy + 900 - 22 - 18*len(lines), "\n".join(lines), 14, f"ms-{D}-cap")


def model():
    b, c, h = Badge(), Case(), HD.BROW
    feats, body, plate, _, geo = HD.build(h, b, c)
    plate_h, bx, by = boot_hole_plate(b, c, plate, geo)
    Hc = geo["Hc"]
    W = HD.to_world(h, Hc)
    # the body is one print; colour the gauge cup (and its brow and band) as the case, the pillar and base as the stand
    cup_zone = W(prism(HD.oval(h.R_CO + h.BAND_R + 0.6, h.BROW), -150, geo["Z_CASE"] + 1))
    cup = body ^ cup_zone
    stand = body - cup_zone
    shell, plugb = HD.plug_solids(b, geo)
    cable = HD.tube(geo["path"], HD.CABLE_D/2, 24).trim_by_plane([0, -1, 0], -(bbox(body)[1, 1] + 15))   # cut 15 past the base
    feat_w = {f.name: W(f.solid()) for f in feats if not f.name.startswith("plug")}
    top = b.pcb_back_z + b.sw_cap_h
    stylus = W(m3.Manifold.cylinder(HD.STYLUS_L, PIN_D/2, PIN_D/2, 48).translate([bx, by, top]))
    return dict(b=b, c=c, h=h, body=body, cup=cup, stand=stand, plate=W(plate_h), plug=W(shell) + W(plugb), cable=cable,
                feat_w=feat_w, geo=geo, Hc=Hc, W=W, bx=bx, by=by, stylus=stylus, top=top)


def view_angles(M):
    """Same measurement as build_hood.run_checks part 3: how far off the axis the whole active area stays visible."""
    b, h = M["b"], M["h"]
    pod = HD.to_badge(h, M["Hc"])(M["body"])
    sl = pod.trim_by_plane([1, 0, 0], -0.5).trim_by_plane([-1, 0, 0], -0.5)
    v = np.asarray(sl.to_mesh().vert_properties)[:, :3]
    ra = b.active_d/2
    up = v[(v[:, 1] < -ra) & (v[:, 2] < -0.5)]
    dn = v[(v[:, 1] > ra) & (v[:, 2] < -0.5)]
    return (min(math.degrees(math.atan2(-p[1] - ra, -p[2])) for p in up),
            min(math.degrees(math.atan2(p[1] - ra, -p[2])) for p in dn))


def parts_section(M, x):
    out = [("base", M["stand"]), ("case", M["cup"]), ("plate", M["plate"]), ("plug", M["plug"]), ("plug", M["cable"])]
    out += [("badge", M["feat_w"]["disc + tab"])]
    out += [("header", m) for n, m in M["feat_w"].items() if n.startswith("header")]
    out += [("boot", m) for n, m in M["feat_w"].items() if n.startswith("BOOT")]
    return out


def side(M):
    h, b, c, geo, Hc = M["h"], M["b"], M["c"], M["geo"], M["Hc"]
    fid = f"ms-{D}-side"
    fx, fy, fw, fh = slot(D, "B")
    bb = bbox(M["body"])
    Y0, Z0 = fx + 330 - PX*float(bb[0, 1]), fy + DESK
    tb = lambda Y, Z: (Y0 + PX*Y, Z0 - PX*Z)
    o = frame(fid, fx, fy, fw, fh, "Hood · B · Side section on the centre line (X = 0), 6 px/mm, front to the left")
    for kind, m in parts_section(M, 0.0):
        o += draw_contours(section_yz(m, 0.0), kind, f"{fid}-{kind}", tb)
    o.append(line(f"{fid}-desk", [(fx + 30, Z0), (fx + fw - 30, Z0)], width=2))
    o.append(text(fx + fw - 90, Z0 + 4, "desk", 14, fid))

    H_top, yF, yB = float(bb[1, 2]), float(bb[0, 1]), float(bb[1, 1])
    xL = tb(yF, 0)[0]
    # heights on the left: overall, and the glass centre with an extension line from it
    gx, gz = tb(0, Hc)
    o += dim((xL - 250, Z0), (xL - 250, Z0 - PX*H_top), f"{H_top:.1f}\ntall", fid, (-62, -20))
    o.append(line(f"{fid}-ext", [(xL - 260, Z0 - PX*H_top), (tb(float(top_y(M)), H_top)[0], Z0 - PX*H_top)], "#adb5bd"))
    o += dim((xL - 170, Z0), (xL - 170, gz), f"{Hc:.1f}\nglass\ncentre", fid, (-60, -30))
    o.append(line(f"{fid}-ext", [(xL - 180, gz), (gx, gz)], "#adb5bd", dashed=True))
    # footprint depth under the desk line
    o += dim((xL, Z0 + 26), (tb(yB, 0)[0], Z0 + 26), f"footprint {yB - yF:.1f} deep (base {2*h.W_B:.0f} wide)", fid, (-120, 4))
    # base slab at the back
    o += dim((tb(yB, 0)[0] + 18, Z0), (tb(yB, 0)[0] + 18, Z0 - PX*h.T_B), f"base {h.T_B:g}", fid, (8, -26))
    # face axis, tilted back ALPHA
    ax = HD.wvec(h, [0, 0, -1])
    p_far = np.array([0, 0, Hc]) + 52*ax
    o.append(line(f"{fid}-axis", [(gx, gz), tb(p_far[1], p_far[2])], "#1971c2", dashed=True))
    ang_up, ang_dn = view_angles(M)
    o.append(text(tb(p_far[1], p_far[2])[0] - 10, tb(p_far[1], p_far[2])[1] - 66,
                  f"face axis: tilted back {h.ALPHA:g}°\nwhole screen seen from\n{ang_up:.1f}° above to {ang_dn:.1f}° below it", 14, fid))
    # hood depth in front of the glass, along the axis: brow tip and bottom lip
    nP, d0 = geo["nP"], geo["d0"]
    zfront = lambda y: (d0 - nP[1]*y)/nP[2]                       # front plane, badge frame
    Wp = lambda p: HD.wpt(h, Hc, p)
    y_top = -(h.R_CO + h.BROW) - 5
    yb_ = -(h.R_CO + h.BROW)
    p0, p1 = Wp([0, y_top, 0]), Wp([0, y_top, zfront(yb_)])
    o += dim(tb(p0[1], p0[2]), tb(p1[1], p1[2]), f"brow {-zfront(yb_):.1f} proud\nof the glass", fid, (0, -64))
    y_bot = h.R_F - 2.5
    p0, p1 = Wp([0, y_bot, 0]), Wp([0, y_bot, zfront(h.R_F)])
    o += dim(tb(p0[1], p0[2]), tb(p1[1], p1[2]), f"lip {-zfront(h.R_F):.1f}", fid, (-112, -8))
    # front plane: the print bed
    nPw = geo["nPw"]
    lean = math.degrees(math.atan2(-nPw[2], nPw[1]))
    o.append(text(xL - 160, tb(0, 17)[1],
                  f"front face = print bed,\nleans back {lean:.0f}°", 14, fid))
    # plug and cable
    o.append(text(tb(4, 0)[0], tb(0, 30)[1] - 8,
                  f"straight USB-C, {HD.PLUG_W:g}×{HD.PLUG_T:g}×{HD.PLUG_L:g}\novermold, in the open\nback of the pillar;\n"
                  f"cable bends R{HD.BEND_R:g} into the\ntunnel under the base", 14, fid))
    o.append(text(tb(25, 0)[0], tb(0, 84)[1],
                  f"badge in from the back,\nplate snaps flush\n(Z {geo['Z_CASE']:.2f} behind the glass)", 14, fid))
    o.append(caption(fx, fy, fw, "Blue = gauge cup with its brow, grey = pillar and oval base (one print, the front face on the bed). "
                     "Orange = back plate, green = badge, dark grey = plug and cable. Cut from build_hood.py's solids."))
    return o


def top_y(M):
    """Y of the highest point of the body (the brow tip): where the overall-height extension line ends."""
    v = np.asarray(M["body"].to_mesh().vert_properties)[:, :3]
    return v[np.argmax(v[:, 2]), 1]


def front(M):
    h, b, c, geo, Hc = M["h"], M["b"], M["c"], M["geo"], M["Hc"]
    fid = f"ms-{D}-front"
    fx, fy, fw, fh = slot(D, "C")
    X0, Zf = fx + 470, fy + DESK
    tb = lambda X, Z: (X0 + PX*X, Zf - PX*Z)
    o = frame(fid, fx, fy, fw, fh, "Hood · C · Front elevation (as you sit at it), 6 px/mm")
    o += draw_contours(project_xz(M["stand"]), "base", f"{fid}-base", tb)
    o += draw_contours(project_xz(M["cup"]), "case", f"{fid}-case", tb)
    # the badge, where nothing of the stand in front of it hides it
    ax = HD.wvec(h, [0, 0, -1])
    glass_c = np.array([0, 0, Hc])
    in_front = M["body"].trim_by_plane(list(ax), float(ax @ glass_c) + 0.3)
    disc = M["feat_w"]["disc + tab"]
    vis = disc.rotate([90, 0, 0]).project() - in_front.rotate([90, 0, 0]).project()
    o += draw_contours([[(p[0], -p[1]) for p in cc] for cc in vis.simplify(0.05).to_polygons()], "badge", f"{fid}-badge", tb)
    o.append(line(f"{fid}-desk", [(fx + 30, Zf), (fx + fw - 30, Zf)], width=2))
    ang_dn = view_angles(M)[1]
    bb = bbox(M["body"])
    cb = bbox(M["cup"])
    o += dim(tb(bb[0, 0], -4), tb(bb[1, 0], -4), f"base {bb[1, 0] - bb[0, 0]:.0f} wide", fid, (-50, 6))
    o += dim(tb(cb[0, 0], cb[1, 2] + 6), tb(cb[1, 0], cb[1, 2] + 6), f"cup {cb[1, 0] - cb[0, 0]:.1f} wide (with its band)", fid, (-110, -28))
    # pillar width just above the base
    zp = h.T_B + 6
    sl = np.asarray([p for cc in M["stand"].slice(zp).to_polygons() for p in cc])
    o += dim(tb(sl[:, 0].min(), zp), tb(sl[:, 0].max(), zp), f"pillar {np.ptp(sl[:, 0]):.0f}", fid, (-34, -26))
    xh = fx + fw - 70
    o += dim((xh, Zf), (xh, Zf - PX*bb[1, 2]), f"{bb[1, 2]:.1f}\ntall", fid, (8, -20))
    o.append(line(f"{fid}-ext", [(tb(0, 0)[0] + 20, Zf - PX*bb[1, 2]), (xh + 10, Zf - PX*bb[1, 2])], "#adb5bd"))
    o.append(text(tb(bb[1, 0] - 14, Hc)[0] + 80, tb(0, Hc)[1] - 70,
                  f"opening Ø{2*h.R_F:.1f}\nlip window Ø{2*(b.r - c.LIP_OVERLAP):.1f}\n(active Ø{b.active_d:.1f})\n"
                  f"brow {h.BROW:g} above\nthe round cup", 14, fid))
    o.append(text(fx + 24, fy + 24,
                  "Nothing to press on the front: BOOT is pressed from behind (D),\nthe plug goes in from underneath (E).", 14, fid))
    o.append(caption(fx, fy, fw, "Projection along Y, viewer level with the desk. Green = the badge where the stand doesn't hide it; "
                     + (f"from level the view is {h.ALPHA:g}° below the face axis, past the {ang_dn:.1f}° the bottom lip allows, so it hides a sliver of the screen's lower edge."
                      if h.ALPHA > ang_dn else f"from level ({h.ALPHA:g}° below the face axis) the whole screen shows.")))
    return o


def boot(M):
    h, b, c, geo, Hc = M["h"], M["b"], M["c"], M["geo"], M["Hc"]
    fid = f"ms-{D}-d"
    fx, fy, fw, fh = slot(D, "D")
    x = M["bx"]
    S, ZCUT = 10.0, 34.0                              # zoomed: the cup only, the pillar below Z = ZCUT left out
    ax = HD.wvec(h, [0, 0, 1])                         # out of the back of the badge
    act = HD.wpt(h, Hc, [x, M["by"], M["top"]])
    Y0, Z0 = fx + 470 - S*act[1], fy + 420 + S*act[2]
    tb = lambda Y, Z: (Y0 + S*Y, Z0 - S*Z)
    o = frame(fid, fx, fy, fw, fh, f"Hood · D · Section through BOOT (X = {x:.1f}), {S:g} px/mm: pressing it from behind")
    keep = m3.Manifold.cube([400, 400, 200]).translate([-200, -200, ZCUT])
    drawn = []
    for kind, m in parts_section(M, x) + [("rocker", M["stylus"])]:
        els = draw_contours(section_yz(m ^ keep, x), kind, f"{fid}-{kind}", tb)
        o += els
        if els and kind not in drawn: drawn.append(kind)
    yz = tb(-60, ZCUT)[1]
    o.append(line(f"{fid}-cut", [(fx + 30, yz), (fx + fw - 30, yz)], "#868e96", dashed=True))
    o.append(text(fx + 34, yz + 6, f"pillar and base below Z {ZCUT:g} not shown (see B)", 14, fid))
    tip = act + HD.STYLUS_L*ax
    st = tb(tip[1], tip[2])
    o.append(text(st[0] - 200, st[1] + 20, f"SIM tool / paperclip Ø{PIN_D:g},\n{HD.STYLUS_L:.0f} reach, straight in", 14, fid))
    hole_back = HD.wpt(h, Hc, [x, M["by"], geo["Z_CASE"]])
    up = np.array([0, -ax[2], ax[1]])                  # across the axis, toward the top of the cup
    pa, pb = act + 6*up, hole_back + 6*up
    o.append(dim(tb(pa[1], pa[2]), tb(pb[1], pb[2]), "", fid)[0])       # the arrow; its number is in the hole note
    hb = tb(hole_back[1], hole_back[2])
    o.append(text(hb[0] + 70, hb[1] - 110, f"Ø{BOOT_HOLE_D:g} hole in the back plate,\n"
                  f"{geo['Z_CASE'] - M['top']:.1f} from its back face to the switch", 15, fid))
    ha = tb(act[1], act[2])
    o.append(text(fx + 40, ha[1] - 20, f"red, under the stylus tip: BOOT,\npress {c.SW_TRAVEL:.2f}. The badge first\nfloats {c.FLOAT:.2f} forward onto the\nlip, then the switch clicks", 14, fid))
    names = {"case": "blue = cup", "plate": "orange = plate", "badge": "green = badge", "header": "cyan = header pins",
             "boot": "red = BOOT", "base": "grey = pillar", "plug": "dark grey = plug"}
    o.append(caption(fx, fy, fw, "Purple = the stylus, at rest on the actuator. It touches nothing else, at rest or pressed "
                     f"(build_hood.py check 5); nothing presses on the glass. Also cut here: {', '.join(names[k] for k in drawn if k in names)}."))
    return o


def plan(M):
    h, b, geo = M["h"], M["b"], M["geo"]
    fid = f"ms-{D}-e"
    fx, fy, fw, fh = slot(D, "E")
    zc = 4.0
    bb = bbox(M["body"])
    X0, Yc = fx + 470, fy + 420 + PX*float((bb[0, 1] + bb[1, 1])/2)
    tb = lambda X, Y: (X0 + PX*X, Yc - PX*Y)
    o = frame(fid, fx, fy, fw, fh, f"Hood · E · Plan section through the base (Z = {zc:g}), 6 px/mm, front at the bottom")
    cs = M["stand"].slice(zc).simplify(0.05).to_polygons()
    o += draw_contours(cs, "base", f"{fid}-base", tb)
    o += draw_contours(M["plug"].slice(zc).simplify(0.05).to_polygons(), "plug", f"{fid}-plug", tb)
    o += draw_contours(M["cable"].slice(zc).simplify(0.05).to_polygons(), "plug", f"{fid}-cable", tb)
    # the quarters in the wells
    wb = bbox(geo["wells"])
    xw = (wb[1, 0] - wb[0, 0])/2 - (HD.COIN_D/2 + 0.35)
    for sx in (-1, 1):
        coin = m3.CrossSection.circle(HD.COIN_D/2, 48).translate([sx*xw, geo["y_well"]])
        o += draw_contours(coin.to_polygons(), "rocker", f"{fid}-coin", tb)
    o += dim(tb(bb[0, 0], bb[0, 1] - 5), tb(bb[1, 0], bb[0, 1] - 5), f"{bb[1, 0] - bb[0, 0]:.0f} wide", fid, (-34, 6))
    o += dim(tb(bb[0, 0] - 17, bb[0, 1]), tb(bb[0, 0] - 17, bb[1, 1]), f"{bb[1, 1] - bb[0, 1]:.1f}\ndeep", fid, (-50, -20))
    o += dim(tb(-xw, geo["y_well"] + HD.COIN_D/2 + 4), tb(xw, geo["y_well"] + HD.COIN_D/2 + 4),
             f"wells {2*xw:.1f} apart", fid, (-268, -28))
    o.append(text(*tb(xw - 8, geo["y_well"] + 3), f"{h.COINS} quarters\nØ{HD.COIN_D:g}", 14, fid))
    o.append(text(*tb(-xw - 8, geo["y_well"] + 3), f"{h.COINS} quarters\nØ{HD.COIN_D:g}", 14, fid))
    # the slot the plug comes up through, and the tunnel the cable leaves by
    a0 = HD.wpt(h, M["Hc"], [0, geo["boss_tip"], b.port_z]); av = HD.wvec(h, [0, 1, 0])
    slot_c = a0 + (zc - a0[2])/av[2]*av                # where the plug's axis crosses the cut
    hw = HD.CABLE_D/2 + 0.4
    o.append(text(*[v + d for v, d in zip(tb(hw, bb[1, 1] + 12), (14, 0))], f"cable tunnel {2*hw:.1f} wide,\nout the back", 14, fid))
    xr = tb(bb[1, 0], 0)[0] + 24
    ys = tb(0, slot_c[1])[1]
    o.append(line(f"{fid}-lead", [(tb(HD.PLUG_W/2 + HD.PLUG_CLR, 0)[0] + 4, ys), (xr - 6, ys)], "#868e96"))
    o.append(text(xr, ys - 18,
                  f"plug slot {HD.PLUG_W + 2*HD.PLUG_CLR:g}×{HD.PLUG_T + 2*HD.PLUG_CLR:g}:\nthe plug goes in from\nunderneath, up its axis", 14, fid))
    o.append(caption(fx, fy, fw, f"Purple = {2*h.COINS} US quarters ({2*h.COINS*HD.COIN_G:.0f} g), loose in the wells; grey = base, "
                     f"dark grey = the cable, cut at Z {zc:g}. Wells {h.COINS*HD.COIN_T + 0.6:.2f} deep, base {h.T_B:g} thick."))
    return o


def main():
    out = sys.argv[1]
    M = model()
    for f in (side, front, boot, plan):
        ops.extend(f(M))
    json.dump([{"kind": "put", "drafts": ops}], open(out, "w"), separators=(",", ":"))
    print(f"{len(ops)} elements -> {out}")


if __name__ == "__main__":
    main()
