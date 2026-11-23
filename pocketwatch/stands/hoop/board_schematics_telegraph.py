#!/usr/bin/env python3
"""
Measured schematics of the hoop telegraph key for the pocketwatch-schematics board: sections and elevations
cut from the solids build_hoop_telegraph.build() makes and checks, pastel fills from board/schem.py,
dimension lines with numbers. Nothing is drawn by hand: every outline is a slice or projection, every number
is read off the built model, and the script refuses to write ops if any of the model's checks fail.

Writes, into the directory given as the first argument:
  frames.json      the four frames (id, box, name): create them first
  <frame id>.json  {"protocol":"draw","ops":[...]} for that frame's edit link (deletes any id an earlier run
                   wrote that this run no longer draws, so a rerun converges)
  fits.json        the key's mating pairs and their clearances, with the constant that sets each

Run from the repo root:
  PYTHONDONTWRITEBYTECODE=1 ~/.venvs/cad/bin/python <this file> /tmp/telegraph-ops
"""
import sys, os, json, math, re, subprocess, contextlib
from dataclasses import dataclass, field
sys.path[:0] = ["pocketwatch", "pocketwatch/stands/hoop", "pocketwatch/board"]
import numpy as np, manifold3d as m3
import schem
from schem import section_yz, project_xz, draw_contours
import build_hoop_telegraph as TG
import build_hoop as H
import build_pocketwatch_usb as U
from build_pocketwatch import Badge, Case, prism, circle

SRC = "pocketwatch/stands/hoop/build_hoop_telegraph.py"
CANVAS = "#ebe4d6"                      # architect-parchment's canvas: holes are painted with it
INK, DIM, FAINT = "#1b2129", "#495057", "#adb5bd"
schem.STYLE.update(lever=("#9c36b5", "#eebefa"), knob=("#f08c00", "#ffec99"), pin=("#495057", "#ced4da"))
FRAMES = {  # id: (x, y, width, height, name); all inside the board's free box x 2100..6950, y 1400..3150
    "tg-overview": (2100, 1460, 1560, 1690, "Telegraph key · 40° vs 50°"),
    "tg-side": (3720, 1460, 1460, 1690, "Telegraph · side section"),
    "tg-front": (5240, 1460, 1710, 880, "Telegraph · front elevation"),
    "tg-lever": (5240, 2410, 1710, 740, "Lever · 2:1 on a pin"),
}


def project_yz(m):
    """Side elevation (viewer at +X): silhouette in world (Y, Z)."""
    cs = m.rotate([0, 90, 0]).project()
    return [[(p[1], p[0]) for p in c] for c in cs.simplify(0.05).to_polygons()]


@dataclass
class Sheet:
    """One frame: its box, its scale (px per mm) and the board point of the model's origin."""
    fid: str
    px: float
    ox: float = 0.0
    oy: float = 0.0
    els: list = field(default_factory=list)

    @property
    def box(self): return FRAMES[self.fid][:4]

    def tb(self, a, z): return (self.ox + self.px*a, self.oy - self.px*z)

    def polys(self, contours, kind, ghost=False):
        for e in draw_contours(contours, kind, f"{self.fid}-{kind}", lambda a, z: self.tb(a, z)):
            if e["backgroundColor"] == "#ffffff": e["backgroundColor"] = CANVAS
            if ghost:
                e.update(backgroundColor="transparent", strokeStyle="dashed", strokeColor=FAINT if kind != "badge" else "#2f9e44",
                         strokeWidth=1.5, opacity=80)
            self.els.append(e)

    def text(self, x, y, t, size=16, color=INK, anchor="w", stem="t", **kw):
        """A text whose anchor (w: left-middle, c: centre, e: right-middle, nw: top-left) sits at x, y."""
        lines = t.split("\n")
        w, h = 0.6*size*max(map(len, lines)), 1.25*size*len(lines)
        x0 = {"w": x, "nw": x, "c": x - w/2, "e": x - w}[anchor]
        y0 = y if anchor == "nw" else y - h/2
        e = {"id": schem.uid(f"{self.fid}-{stem}"), "type": "text", "x": round(x0, 1), "y": round(y0, 1), "text": t,
             "fontSize": size, "strokeColor": color, "_w": w, "_h": h}
        e.update(kw)
        self.els.append(e)
        return e

    def line(self, pts, color=FAINT, width=1, stem="ln", **kw):
        pts = np.asarray(pts, float)
        e = {"id": schem.uid(f"{self.fid}-{stem}"), "type": "line", "x": round(pts[0, 0], 1), "y": round(pts[0, 1], 1),
             "width": round(float(np.ptp(pts[:, 0])), 1), "height": round(float(np.ptp(pts[:, 1])), 1),
             "points": [[round(float(p[0] - pts[0, 0]), 1), round(float(p[1] - pts[0, 1]), 1)] for p in pts],
             "strokeColor": color, "strokeWidth": width, "roughness": 0, "roundness": None}
        e.update(kw)
        self.els.append(e)
        return e

    def arrow(self, p0, p1, color=DIM, width=1, both=True, stem="dim", **kw):
        (x0, y0), (x1, y1) = p0, p1
        e = {"id": schem.uid(f"{self.fid}-{stem}"), "type": "arrow", "x": round(x0, 1), "y": round(y0, 1),
             "width": round(x1 - x0, 1), "height": round(y1 - y0, 1), "points": [[0, 0], [round(x1 - x0, 1), round(y1 - y0, 1)]],
             "startArrowhead": "arrow" if both else None, "endArrowhead": "arrow", "strokeColor": color,
             "strokeWidth": width, "roughness": 0, "roundness": None}
        e.update(kw)
        self.els.append(e)

    def dim(self, p0, p1, label, off=(0, 0), size=18, anchor="c", color=DIM):
        self.arrow(p0, p1, color)
        if label: self.text((p0[0] + p1[0])/2 + off[0], (p0[1] + p1[1])/2 + off[1], label, size, color, anchor, "dimt")

    def radial(self, P, Q, label, off, size=18, anchor="w"):
        """A distance measured from a centre P out to Q, drawn along the part itself: one head, at Q."""
        p0, p1 = self.tb(*P), self.tb(*Q)
        self.arrow(p0, p1, INK, 1.5, both=False, stem="rad")
        self.text((p0[0] + p1[0])/2 + off[0], (p0[1] + p1[1])/2 + off[1], label, size, DIM, anchor, "dimt")

    def dot(self, x, y, r=5, color=INK):
        self.els.append({"id": schem.uid(f"{self.fid}-dot"), "type": "ellipse", "x": round(x - r, 1), "y": round(y - r, 1),
                         "width": 2*r, "height": 2*r, "strokeColor": color, "backgroundColor": color, "fillStyle": "solid"})

    def desk(self, z_board, pad=40):
        x, _, w, _ = self.box
        self.line([(x + pad, z_board), (x + w - pad, z_board)], DIM, 2, "desk")

    def provenance(self, sha):
        x, y, _, _ = self.box
        self.text(x + 32, y + 26, f"MEASURED · build_hoop_telegraph · {sha}", 12, "#6b6459", "nw", "prov")

    def checked(self):
        """Every element inside the frame (16 px margin), no two texts overlapping; strip the private sizes."""
        x, y, w, h = self.box
        boxes = []
        for e in self.els:
            ew, eh = e.pop("_w", None), e.pop("_h", None)
            if e["type"] == "text":
                bx = (e["x"], e["y"], e["x"] + ew, e["y"] + eh)
                for o in boxes:
                    assert bx[2] <= o[1][0] or o[1][2] <= bx[0] or bx[3] <= o[1][1] or o[1][3] <= bx[1], \
                        f"{self.fid}: text {e['text']!r} {[round(v) for v in bx]} overlaps {o[0]!r} {[round(v) for v in o[1]]}"
                boxes.append((e["text"], bx))
            elif e["type"] in ("line", "arrow"):
                pts = np.array(e["points"]) + [e["x"], e["y"]]
                bx = (*pts.min(0), *pts.max(0))
            else:
                bx = (e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"])
            assert x + 16 <= bx[0] and bx[2] <= x + w - 16 and y + 16 <= bx[1] and bx[3] <= y + h - 16, \
                f"{self.fid}: {e['id']} ({e.get('text', e['type'])}) leaves the frame: {[round(v) for v in bx]}"
        return self.els


def built():
    """Both candidates, built and checked by build_hoop_telegraph itself (its prints go to stderr)."""
    b, c = Badge(), Case()
    with contextlib.redirect_stdout(sys.stderr):
        _, _, plate_b, geo_b = U.build(b, c, U.PLATE_DISC_CLR, button=True)
        Rs = [TG.build(k, plate_b, geo_b, i == 0) for i, k in enumerate(TG.CANDIDATES)]
    if TG.FAILS:
        sys.exit("model checks failed, no ops written: " + "; ".join(TG.FAILS))
    return Rs


def parts(R):
    """(kind, world solid) in drawing order."""
    F = R["F"]
    feats = {f.name: F.W(f.solid()) for f in R["feats"] if not f.name.startswith("plug")}
    body, shell, _ = R["plug"]
    return ([("base", R["base"]), ("case", R["hoopW"]), ("plate", R["plateW"]), ("badge", feats["disc + tab"])] +
            [("header", m) for n, m in feats.items() if n.startswith("header")] +
            [("boot", m) for n, m in feats.items() if n.startswith("BOOT")] +
            [("lever", R["lever"]), ("knob", R["knob"]), ("pin", R["pin"]), ("plug", body), ("plug", shell)])


def fmt(v, nd=1): return f"{v:.{nd}f}".rstrip("0").rstrip(".") if nd else f"{v:.0f}"


# ---- frame: the hero, the assembly from the side at 40° with the 50° stand ghosted over it ----
def overview(R40, R50, sha):
    S = Sheet("tg-overview", 15.0)
    x, y, w, h = S.box
    allv = np.vstack([np.vstack(project_yz(m)) for R in (R40, R50) for _, m in parts(R) if _ != "base"] +
                     [np.vstack(project_yz(R40["base"]))])
    ymin, ymax = allv[:, 0].min(), allv[:, 0].max()
    S.ox, S.oy = x + 120 + (w - 360)/2 - S.px*(ymin + ymax)/2, y + h - 300
    for kind, m in parts(R40):
        S.polys(project_yz(m), kind)
    for kind, m in parts(R50):
        if kind in ("case", "plate", "badge", "plug"):
            S.polys(project_yz(m), kind, ghost=True)
    S.desk(S.oy)
    # heights to the plug top, each stand's own
    xr = S.ox + S.px*ymax + 70
    for i, (R, dash) in enumerate(((R40, False), (R50, True))):
        top = R["sizes"]["top"]
        xd = xr + 70*i
        S.line([(xd - 26, S.oy - S.px*top), (xd + 6, S.oy - S.px*top)], FAINT, 1, "ext")
        S.arrow((xd, S.oy), (xd, S.oy - S.px*top), DIM, 1.5, strokeStyle="dashed" if dash else "solid")
        S.text(xd + 14, S.oy - S.px*top/2 - 30*(1 - 2*i), f"{top:.0f}", 20, DIM, "w")
    # the press: a finger on the knob
    g = R40["g"]
    kx, kz = S.tb(g["K_Y"], g["Z_kb"] + R40["k"].KNOB_H)
    S.arrow((kx, kz - 150), (kx, kz - 22), INK, 3, both=False, stem="press")
    S.text(kx, kz - 176, "press", 20, INK, "c")
    # lean gauge, angles to scale: vertical, 40° (solid) and 50° (ghost), leaning back
    vx, vy, r = x + 260, y + 600, 230
    S.line([(vx, vy), (vx, vy - r - 30)], FAINT, 1.5, "gauge", strokeStyle="dotted")
    for t, col, dash, sz in ((R40["k"].TILT, "#2f9e44", "solid", 44), (R50["k"].TILT, "#868e96", "dashed", 30)):
        a = math.radians(t)
        S.line([(vx, vy), (vx + r*math.sin(a), vy - r*math.cos(a))], col, 4 if t == R40["k"].TILT else 2.5, "gauge", strokeStyle=dash)
        ra = 0.42*r if t == R40["k"].TILT else 0.62*r
        arc = [(vx + ra*math.sin(q), vy - ra*math.cos(q)) for q in np.linspace(0, a, 24)]
        S.line(arc, col, 1.5, "arc", strokeStyle=dash)
        first = t == R40["k"].TILT
        tx_, ty_ = vx + (r + 18)*math.sin(a), vy - (r + 18)*math.cos(a)
        S.text(tx_ - 12 if first else tx_ + 12, ty_, f"{t:.0f}°", sz, col, "e" if first else "w")
    S.dot(vx, vy, 5, INK)
    S.text(vx, vy + 28, "face lean", 16, DIM, "c")
    # key: one swatch per part
    kx0, ky0 = x + 40, y + h - 120
    names = (("case", "hoop + case"), ("plate", "plate"), ("badge", "badge"), ("base", "base"), ("lever", "lever"),
             ("knob", "knob"), ("pin", "pin"))
    for i, (kind, nm) in enumerate(names):
        cx = kx0 + i*212
        st, fi = schem.STYLE[kind]
        S.els.append({"id": schem.uid("tg-overview-key"), "type": "rectangle", "x": cx, "y": ky0, "width": 30, "height": 22,
                      "strokeColor": st, "backgroundColor": fi, "fillStyle": "solid", "strokeWidth": 1, "roughness": 0})
        S.text(cx + 40, ky0 + 11, nm, 16, INK, "w")
    S.line([(kx0, ky0 + 64), (kx0 + 44, ky0 + 64)], FAINT, 1.5, "key", strokeStyle="dashed")
    S.text(kx0 + 56, ky0 + 64, "50° ghost", 16, DIM, "w")
    S.text(kx0 + 300, ky0 + 64, f"{R40['sizes']['top']:.0f} / {R50['sizes']['top']:.0f} tall · Ø{2*R40['k'].BASE_R:.0f} base · "
           f"{S.px:g} px/mm", 16, DIM, "w")
    S.provenance(sha)
    return S


# ---- frame: section on the nub plane, the 2:1 arms, the press path drawn to scale ----
def side(R, sha):
    k, g, F = R["k"], R["g"], R["F"]
    xc = k.X0 + k.NUB_W/2
    S = Sheet("tg-side", 17.0)
    x, y, w, h = S.box
    secs = [(kind, section_yz(m, xc)) for kind, m in parts(R)]
    allv = np.vstack([np.vstack(c) for _, cs in secs for c in cs if len(c)])
    S.ox, S.oy = x + w/2 - S.px*(allv[:, 0].min() + allv[:, 0].max())/2, y + 80 + S.px*allv[:, 1].max()
    for kind, cs in secs:
        S.polys(cs, kind)
    pressed = TG.FB.rot3(R["lever_rigid"] + R["knob"], g["P"], R["phi_s"])
    S.polys(section_yz(pressed, xc), "lever", ghost=True)
    S.desk(S.oy)
    P, Tip, K_Y = g["P"], g["Tip"], g["K_Y"]
    px_, pz_ = S.tb(*P)
    S.dot(px_, pz_, 6)
    S.text(px_ - 36, pz_ - 44, "pin", 18, INK, "e")
    # the arms: the knob arm under the desk (drafting style, extension lines down), the nub arm beside the rear arm
    zk = -4.0
    a0, a1 = S.tb(K_Y, zk), S.tb(P[0], zk)
    S.line([S.tb(K_Y, g["Z_kb"] - 0.5), (a0[0], a0[1] + 12)], FAINT, 1, "ext")
    S.line([S.tb(P[0], P[1] - k.PIN_D/2), (a1[0], a1[1] + 12)], FAINT, 1, "ext")
    S.dim(a0, a1, f"knob arm {g['a']:.1f}", (0, 26))
    S.radial(P, Tip, f"nub arm {g['h']:.1f}", (125, 30))
    S.text(x + 250, y + 330, f"{g['a']/(g['h']*g['cb']):.0f} : 1", 64, "#9c36b5", "c")
    S.text(x + 250, y + 400, "knob : nub travel", 16, DIM, "c")
    # nub to the flush BOOT tab at rest
    tx, tz = S.tb(*Tip)
    S.arrow((tx + 150, tz - 110), (tx + 6, tz - 6), DIM, 1, both=False, stem="lead")
    S.text(tx + 158, tz - 124, f"gap {k.G:g}", 18, DIM, "w")
    S.text(x + w - 60, y + 200, f"face {k.TILT:.0f}° back", 20, DIM, "e")
    gx, gz = S.tb(g["K_Y"] - k.KNOB_RS - 1.5, g["Z_kb"] + k.KNOB_H/2)
    S.text(gx, gz, "pressed", 16, "#868e96", "e")
    # the press path, knob travel to scale: touch, click (with its tolerance band), the anvil stop
    res, d_stop = R["res"], R["d_stop"]
    sc, rx, ry = 250.0, x + 110, y + h - 250
    ruler = lambda d: rx + sc*d
    S.els.append({"id": schem.uid("tg-side-band"), "type": "rectangle", "x": round(ruler(res["G-tol"][2][0]), 1), "y": ry - 20,
                  "width": round(sc*(res["G+tol"][2][0] - res["G-tol"][2][0]), 1), "height": 40, "strokeColor": "transparent",
                  "backgroundColor": "#eebefa", "fillStyle": "solid", "opacity": 60})
    S.line([(ruler(0), ry), (ruler(d_stop), ry)], DIM, 3, "track")
    S.line([(ruler(0), ry), (ruler(res["G"][2][0]), ry)], "#9c36b5", 6, "travel")
    S.els.append({"id": schem.uid("tg-side-anvil"), "type": "rectangle", "x": round(ruler(d_stop), 1), "y": ry - 30, "width": 14,
                  "height": 60, "strokeColor": "#495057", "backgroundColor": "#ced4da", "fillStyle": "solid", "roughness": 0})
    for d, nm, up in ((0, "rest", True), (res["G"][1][0], "touch", False), (res["G"][2][0], "click", True), (d_stop, "stop", False)):
        S.line([(ruler(d), ry - 26), (ruler(d), ry + 26)], INK, 2, "tick")
        S.text(ruler(d), ry - 60 if up else ry + 60, f"{nm} {fmt(d, 1)}" if d else nm, 18, INK, "c")
    S.text(ruler(res["G"][2][0]), ry + 60, f"{res['G'][2][1]:.1f} N", 18, "#9c36b5", "c")
    S.text(rx, ry - 120, "knob travel, mm", 16, DIM, "w")
    S.text(rx, ry + 116, f"band: click across the gap tolerance, {res['G-tol'][2][0]:.1f}–{res['G+tol'][2][0]:.1f}", 14, "#6b6459", "w")
    S.text(x + w - 40, y + 26 + 7, f"cut at X {xc:.2f} · {S.px:g} px/mm", 12, "#6b6459", "e")
    S.provenance(sha)
    return S


# ---- frame: front elevation as you sit at it ----
def front(R, sha):
    k, g, F, geo = R["k"], R["g"], R["F"], R["geo"]
    S = Sheet("tg-front", 8.5)
    x, y, w, h = S.box
    S.ox, S.oy = x + w/2 - 120, y + h - 150
    for kind, m in parts(R):
        if kind in ("header", "boot"): continue
        S.polys(project_xz(m), kind)
    S.desk(S.oy)
    S.dim(S.tb(-k.BASE_R, -8.0), S.tb(k.BASE_R, -8.0), f"Ø{2*k.BASE_R:.0f} base", (0, 26))
    cz = F.pt([0, 0, 0])[2]
    R_OUT = geo["R_OUT"]
    xl = S.tb(-R_OUT - 9, 0)[0]
    S.line([S.tb(-R_OUT - 12, cz), S.tb(-R_OUT - 1, cz)], FAINT, 1, "ext")
    S.dim((xl, S.oy), (xl, S.tb(0, cz)[1]), f"glass\ncentre {cz:.0f}", (-70, 0))
    zl = -3.2
    S.dim(S.tb(k.X0, zl), S.tb(k.X0 + k.W, zl), "", (0, 0))
    S.text(S.tb(k.X0 + k.W, zl)[0] + 14, S.tb(0, zl)[1], f"lever {k.W:g}", 18, DIM, "w")
    for X in (k.X0, k.X0 + k.W):
        S.line([S.tb(X, g["pad_bot"] - 0.3), S.tb(X, zl - 1.2)], FAINT, 1, "ext")
    kx, kz = S.tb(g["Xk"] + k.KNOB_RB + 2, g["Z_kb"] + k.KNOB_H*0.6)
    S.arrow((kx + 130, kz - 40), (kx + 4, kz), DIM, 1, both=False, stem="lead")
    S.text(kx + 138, kz - 52, f"knob Ø{2*k.KNOB_RB:.1f}", 18, DIM, "w")
    xb_ = TG.post_xs(k)[1][1] + 1.4
    px_, pz_ = S.tb(xb_, g["P"][1])
    S.arrow((px_ + 130, pz_ + 50), (px_ + 4, pz_), DIM, 1, both=False, stem="lead")
    S.text(px_ + 138, pz_ + 62, f"pin Ø{k.PIN_D:g}", 18, DIM, "w")
    S.text(*S.tb(0, cz), "badge", 18, "#2f9e44", "c")
    top = R["sizes"]["top"]
    S.text(S.tb(0, top)[0] + 70, S.tb(0, top - 4)[1], "USB-C plug", 16, DIM, "w")
    S.text(x + w - 40, y + 26 + 7, f"viewer in front · {S.px:g} px/mm", 12, "#6b6459", "e")
    S.provenance(sha)
    return S


# ---- frame: the lever alone, its arms, bore and pin ----
def lever(R, sha):
    k, g = R["k"], R["g"]
    S = Sheet("tg-lever", 21.0)
    x, y, w, h = S.box
    cs = project_yz(R["lever"])
    v = np.vstack(cs)
    S.ox = x + 140 + (w - 560)/2 - S.px*(v[:, 0].min() + v[:, 0].max())/2
    S.oy = y + 110 + S.px*v[:, 1].max()
    S.polys(cs, "lever")
    P, Tip, K_Y = g["P"], g["Tip"], g["K_Y"]
    px_, pz_ = S.tb(*P)
    rp = S.px*k.PIN_D/2
    S.els.append({"id": schem.uid("tg-lever-pin"), "type": "ellipse", "x": round(px_ - rp, 1), "y": round(pz_ - rp, 1),
                  "width": round(2*rp, 1), "height": round(2*rp, 1), "strokeColor": "#495057", "backgroundColor": "#ced4da",
                  "fillStyle": "solid", "strokeWidth": 1, "roughness": 0})
    # arms
    zb = v[:, 1].min() - 2.4
    a0, a1 = S.tb(K_Y, zb), S.tb(P[0], zb)
    for X, Z in ((K_Y, g["pad_bot"]), (P[0], P[1] - k.PIN_D/2 - k.PIN_CLR)):
        S.line([S.tb(X, Z - 0.4), S.tb(X, zb - 0.8)], FAINT, 1, "ext")
    S.dim(a0, a1, f"knob arm {g['a']:.1f}", (0, 26), size=20)
    S.radial(P, Tip, f"nub arm {g['h']:.1f}", (-70, -20), size=20, anchor="e")
    S.text(x + w - 260, y + 250, f"{g['a']/(g['h']*g['cb']):.0f} : 1", 56, "#9c36b5", "c")
    S.text(x + w - 260, y + 310, "knob moves 2×\nwhat the nub does", 16, DIM, "c")
    # the bore and the pin in it
    S.arrow((px_ + 110, pz_ + 130), (px_ + 0.7*rp + 2, pz_ + 0.7*rp + 2), DIM, 1, both=False, stem="lead")
    S.text(px_ + 118, pz_ + 150, f"bore Ø{k.PIN_D + 2*k.PIN_CLR:.2f}\npin Ø{k.PIN_D:g}", 18, DIM, "w")
    # blade taper, nub, hairpin
    yb = K_Y + k.PAD_HL + 2.0
    bx, bz = S.tb(yb, g["Z_AT"])
    S.arrow((bx + 10, bz - 110), (bx + 10, bz - 4), DIM, 1, both=False, stem="lead")
    S.text(bx + 40, bz - 130, f"blade {k.T0:.2f} → {k.T_TIP:.2f}", 18, DIM, "c")
    tx, tz = S.tb(*Tip)
    S.text(tx - 24, tz - 30, "nub", 18, DIM, "e")
    (ya, za), (yf, zf) = g["path"][-2], g["path"][-1]
    hx, hz = S.tb((ya + yf)/2, (za + zf)/2)
    S.text(hx, hz + 52, "hairpin spring", 16, DIM, "c")
    S.text(x + w - 260, y + h - 130, f"{k.W:g} wide · prints on its side", 16, DIM, "c")
    S.text(x + w - 40, y + 26 + 7, f"seen from the side · {S.px:g} px/mm", 12, "#6b6459", "e")
    S.provenance(sha)
    return S


def const_line(path, name):
    for i, ln in enumerate(open(path), 1):
        if re.match(rf"\s*{name}\s*[:=]", ln):
            return f"{os.path.basename(path)}:{i}"
    raise KeyError(name)


def fits(R):
    k, s = R["k"], R["s"]
    hp = "pocketwatch/stands/hoop/build_hoop.py"
    o = k.PEG_SLOT/2 + k.PEG_T
    return [
        dict(pair="pin in the lever's bore", part=f"pin Ø{k.PIN_D:g}", hole=f"Ø{k.PIN_D + 2*k.PIN_CLR:.2f}",
             per_side=k.PIN_CLR, const="Key.PIN_CLR", where=const_line(SRC, "PIN_CLR")),
        dict(pair="pin in the post holes", part=f"pin Ø{k.PIN_D:g}", hole=f"Ø{k.PIN_D + 2*k.HOLE_CLR:.2f} teardrop",
             per_side=k.HOLE_CLR, const="Key.HOLE_CLR", where=const_line(SRC, "HOLE_CLR")),
        dict(pair="lever between the posts", part=f"lever {k.W:g} wide", hole=f"{k.W + 2*k.CLR_X:.1f} between posts",
             per_side=k.CLR_X, const="Key.CLR_X", where=const_line(SRC, "CLR_X")),
        dict(pair="knob socket on the split peg", part=f"peg {k.PEG_W:g} x {2*o:.1f}",
             hole=f"{k.PEG_W + 2*k.SOCK_CLR:.1f} x {2*o + 2*k.SOCK_CLR:.1f}", per_side=k.SOCK_CLR, const="Key.SOCK_CLR",
             where=const_line(SRC, "SOCK_CLR"), note=f"barbs {k.PEG_BARB:g} snap under a ledge"),
        dict(pair="pin barbs past the inner post", part=f"barbs {k.PIN_BARB:g} proud", hole="snap, 0.1 end play",
             per_side=None, const="Key.PIN_BARB", where=const_line(SRC, "PIN_BARB")),
        dict(pair="hoop tenon in the plinth mortise", part="tenon", hole=f"mortise +{2*s.FIT:.2f}", per_side=s.FIT,
             const="Stand.FIT", where=const_line(hp, "FIT")),
        dict(pair="back plate disc in the case counterbore", part="plate disc", hole="counterbore",
             per_side=U.PLATE_DISC_CLR, const="PLATE_DISC_CLR", where=const_line("pocketwatch/build_pocketwatch_usb.py", "PLATE_DISC_CLR")),
        dict(pair="nub to the flush BOOT tab at rest (a gap, not a fit)", part="nub", hole="tab", per_side=k.G,
             const="Key.G ± Key.G_TOL", where=const_line(SRC, "G"), note=f"± {k.G_TOL:g}; heel on the back stop sets it"),
    ]


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    sha = subprocess.run(["git", "log", "-1", "--format=%h", "--", SRC], capture_output=True, text=True, check=True).stdout.strip()
    R40, R50 = built()
    sheets = [overview(R40, R50, sha), side(R40, sha), front(R40, sha), lever(R40, sha)]
    json.dump([dict(id=f, x=v[0], y=v[1], width=v[2], height=v[3], name=v[4]) for f, v in FRAMES.items()],
              open(os.path.join(out, "frames.json"), "w"), indent=1)
    checked = [(S, S.checked()) for S in sheets]           # every sheet passes before any file is written
    for S, els in checked:
        pth = os.path.join(out, S.fid + ".json")
        old = set()
        if os.path.exists(pth):                           # what the last run drew, and any delete it still owed
            for op in json.load(open(pth))["ops"]:
                old |= {d["id"] for d in op["drafts"]} if op["kind"] == "put" else set(op["ids"])
        gone = sorted(old - {e["id"] for e in els})
        ops = ([{"kind": "delete", "ids": gone}] if gone else []) + [{"kind": "put", "drafts": els}]
        json.dump({"protocol": "draw", "ops": ops}, open(pth, "w"), separators=(",", ":"))
        print(f"{S.fid}: {len(els)} elements, {len(gone)} deleted -> {pth}")
    json.dump(fits(R40), open(os.path.join(out, "fits.json"), "w"), indent=1)
    print(f"fits -> {os.path.join(out, 'fits.json')}")


if __name__ == "__main__":
    main()
