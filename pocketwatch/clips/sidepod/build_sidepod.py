#!/usr/bin/env python3
"""
Sidepod: the USB-only pocketwatch in a hooded single-gauge pod, on a pillar that
clamps to the RIGHT edge of a monitor. 90s aftermarket A-pillar pod: matte, faceted,
one 45-degree cone bezel, a brow that leans forward, louvres in the clamp.

Parts
  BODY   pillar + clamp + hooded pod + the case, one piece, printed STANDING UP the
         way it hangs. Everything stands on the bed (pod neck, pillar, lip, rear
         clamp), every load runs along the layers, and every downward face is
         <= 45 degrees: the case bore gets a teardrop roof (8 mm flat), the window
         bevel is 45 degrees and IS the hood cone.
  PLATE  the USB-only plate with the BOOT hole, outline teardropped to fill the bore
         roof. Snaps in flush with the pod back.
  KNOB   an M4 x 45 hex bolt pressed into it. The bolt runs through an M4 nut in the
         rear arm and pushes the PAD onto the back of the monitor: 8-32 mm, no tools.
  RING   optional glue-in trim ring for the cone bezel (print it silver).

Frames
  world  you sit at -Y. Screen front = plane y=0, monitor side face = plane x=0, the
         monitor is x<=0, 0<=y<=E. Z up. Print frame = world.
  badge  (b-) origin = glass-face centre, +y toward the USB-C tab, +z backward.
         Crown DOWN: b+y -> world -Z, b+z -> (sin CANT, cos CANT, 0).

Run with ~/.venvs/cad/bin/python from the repo root. --no-render for a fast run.
"""
import sys, math
from dataclasses import replace
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3, trimesh
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)

STL = "stl/pocketwatch/clips/sidepod/Sidepod - "
PNG = "pocketwatch/clips/sidepod/renders/"
Miter = m3.JoinType.Miter

# ---- pod, badge frame ----------------------------------------------------------------
CANT = 20.0            # pod turned toward you about vertical
Y_GLASS = -6.0         # glass centre in front of the screen plane
X_C = 36.0             # pod centre, out from the monitor's side face
HOOD_D0 = 5.5          # hood depth in front of the lip at centre height
HOOD_G_LO, HOOD_G_HI = 0.12, 0.25   # rim lean below / above centre: extra hood depth per mm (7 / 14 deg)
POD_W, POD_TOP = 26.5, 33.5     # octagon half-width, brow top above centre
CH_TOP, POD_V1 = 11.0, -7.5     # top chamfer; where the 45-degree chin starts
BACK_CH = 1.0
COLLAR_HW, COLLAR_LEN = 11.0, 12.0   # neck around the plug; the plug's top 12 mm hide in it
TD_FLAT = 4.0          # teardrop roof flat half-width -> an 8 mm bridge
PLUG_W, PLUG_T, PLUG_L, PLUG_CLR = 12.0, 8.0, 22.0, 0.5   # straight USB-C overmold
SHELL_LEN, MIN_PLUG_ENGAGE = 6.65, 3.5
BOOT_HOLE_D, PIN_D = 3.4, 2.0
RING_FRONT, RING_RI, RING_GAP = -3.4, 16.955, 0.10

# ---- pillar + clamp, world --------------------------------------------------------
SX, JT, YP = 12.0, 4.0, 7.0     # pillar x 0..SX, y -JT..YP; its inner face bears on the monitor side
H, LEAN, SX_TOP = 140.0, 14.0, 8.0   # pillar height; above the clamp it leans back LEAN and narrows to SX_TOP
LIP = 6.0              # front jaw onto the bezel
CL_TOP = 62.0          # lip, deep spine and rear arm stand on the bed up to here
SP0, SP1 = 1.0, 9.0    # deep spine x (inner face 1 mm off the monitor side: the pad passes it)
E_MIN, E_MAX = 8.0, 32.0
Z_S = CL_TOP/2         # bolt axis = centre of the lip band
SCREW_X = -LIP/2       # bolt on the lip's centre line: no clamp couple
PAD_D, PAD_T, SOCK_D, SOCK_DEPTH = 7.0, 5.0, 4.0, 3.5
ARM_T, ARM_X = 10.0, -11.0
Y_A0 = E_MAX + PAD_T + 1.0
Y_A1 = Y_A0 + ARM_T
BOLT_L, BOLT_D, BOLT_HOLE = 45.0, 4.0, 4.5
NUT_AF, NUT_H, NUT_CLR = 7.0, 3.2, 0.3
NUT_AC = NUT_AF*2/math.sqrt(3)
HEAD_AF, HEAD_H = 7.0, 2.8
KNOB_D, KNOB_WALL, KNOB_T = 24.0, 5.0, 8.5
CABLE_SLOT, HOOK_X, HOOK_DX, HOOK_Z = 4.6, 13.5, 4.0, 13.0  # J-hook in the foot of the pillar, beside the jaws
HOOK_Y0, HOOK_Y1, HOOK_XO = 0.0, 20.0, 17.0
LOUVRES = (12.5, 22.5, 32.5)    # speed holes in the deep spine (y centres)

# ---- statics -----------------------------------------------------------------------
RHO = 1.27e-3          # PETG g/mm^3, as if solid (more mass = more demand)
BADGE_G, BOLT_G, NUT_G, PLUG_G = 20.0, 4.6, 1.1, 5.0
MU = 0.30              # PETG on matte monitor plastic, low end
N_CLAMP = 20.0         # finger-light knob: 0.05 N.m on M4 is ~60 N; credit a third
PULL = 1.0             # cable pull, each of the 6 directions
SF_MIN, SF_MIN_PLUG = 3.0, 1.25   # hook routing is the design case; a yank at the plug must still hold
F_HARD = 100.0         # hard hand-tight, for strength
SIG_ALLOW = 12.0       # MPa: PETG ~50 yield / 4 for creep and layers


# ---- helpers ------------------------------------------------------------------------
def ccw(pts):
    pts = [tuple(map(float, p)) for p in pts]
    a = sum(x0*y1 - x1*y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return pts if a > 0 else pts[::-1]


def poly(pts): return m3.CrossSection([ccw(pts)])


def box(x0, x1, y0, y1, z0, z1): return m3.Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0, y0, z0])


def roof(R):
    """45-degree roof over a circle of radius R, toward b-y (world up), flat at an 8 mm bridge.
    Starts a hair inside the circle so it never shares vertices with the bore polygon."""
    a = (R - 0.05)/math.sqrt(2); h = R*math.sqrt(2) - TD_FLAT
    return poly([(-a, -a), (0, 0), (a, -a), (TD_FLAT, -h), (-TD_FLAT, -h)])


def ext(cs, axis, a0, a1):
    """Extrude a 2D section along a world axis: 'x' takes cs as (y, z), 'y' takes cs as (x, z)."""
    e = m3.Manifold.extrude(cs, a1 - a0)
    if axis == "x": return e.transform([[0, 0, 1, a0], [1, 0, 0, 0], [0, 1, 0, 0]])
    if axis == "y": return e.transform([[1, 0, 0, 0], [0, 0, 1, a0], [0, 1, 0, 0]])
    raise ValueError(axis)


C_, S_ = math.cos(math.radians(CANT)), math.sin(math.radians(CANT))


def b2w(zc): return np.array([[C_, 0, S_, X_C], [-S_, 0, C_, Y_GLASS], [0, -1, 0, zc]])


def inv(M):
    R, t = M[:, :3], M[:, 3]
    return np.hstack([R.T, (-R.T @ t)[:, None]])


def apply(M, p): return M[:, :3] @ np.asarray(p, float) + M[:, 3]


def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))


# ---- build --------------------------------------------------------------------------
def build(b: Badge, c: Case):
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    R_REAR = R_BORE + 1.2
    FLOOR = b.hdr_top_z + c.FLOAT
    Z_CASE = FLOOR + c.PLATE_T
    BOSS_TIP = b.tip_y + c.RAD_CLR + c.CASE_WALL          # the printed USB-only case's crown wall, kept exactly
    COLLAR_BOT = BOSS_TIP + COLLAR_LEN
    r_win = b.r - c.LIP_OVERLAP
    bore_xy = feats[0].grown()
    bore_td = bore_xy + roof(R_BORE)
    pocket_td = circle(R_REAR) + bore_xy + roof(R_REAR)
    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())
    body_keep = union(k for n, k in keep.items() if n != "disc + tab")   # inside the teardropped bore; a 2nd copy of its circle pinches
    rim = lambda by: -c.LIP_T - HOOD_D0 + (HOOD_G_LO if by > 0 else HOOD_G_HI)*by   # hood rim b-z at height by (up = -by)

    # outer shell: octagon in (u, v) = (b-x, -b-y), prism along b-z, back edge chamfered
    W, T, V1 = POD_W, POD_TOP, POD_V1
    vb = V1 - (W - COLLAR_HW)
    octo = [(-W + CH_TOP, T), (W - CH_TOP, T), (W, T - CH_TOP), (W, V1), (COLLAR_HW, vb), (-COLLAR_HW, vb),
            (-W, V1), (-W, T - CH_TOP)]
    pod = chamfered([poly([(u, -v) for u, v in octo])], rim(-T) - 1.0, Z_CASE, 0.0, BACK_CH)
    z_cf = rim(-vb) - 1.0                                  # the brow cut trims the neck's front (no shared edge)
    neck_cs = poly([(-COLLAR_HW, z_cf), (COLLAR_HW, z_cf), (COLLAR_HW, Z_CASE - 0.8), (COLLAR_HW - 0.8, Z_CASE),
                    (-COLLAR_HW + 0.8, Z_CASE), (-COLLAR_HW, Z_CASE - 0.8)])
    pod += m3.Manifold.extrude(neck_cs, COLLAR_BOT - 10.0).transform([[1, 0, 0, 0], [0, 0, 1, 10.0], [0, 1, 0, 0]])
    hs = lambda g: m3.Manifold.cube([400, 400, 200]).translate([-200, -200, -200]) \
        .rotate([math.degrees(math.atan(g)), 0, 0]).translate([0, 0, -c.LIP_T - HOOD_D0])
    half = hs(HOOD_G_LO) ^ hs(HOOD_G_HI)                   # everything in front of the two-plane rim: a peaked brow
    pod -= half

    DM = 40.0
    cone = m3.Manifold.cylinder(DM + 0.01, r_win + DM, r_win, SEG).translate([0, 0, -DM])   # window bevel = hood
    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4
    chan = box(-PLUG_W/2 - PLUG_CLR, PLUG_W/2 + PLUG_CLR, BOSS_TIP, COLLAR_BOT + 1,
               b.port_z - PLUG_T/2 - PLUG_CLR, b.port_z + PLUG_T/2 + PLUG_CLR)
    pry = box(R_REAR - 0.5, R_REAR + 1.6, -2.5, 2.5, Z_CASE - 1.5, Z_CASE + 1)   # fingernail notch, outboard
    cav = union([prism(bore_td, 0.0, Z_CASE + 1), prism(pocket_td, FLOOR, Z_CASE + 1), cone, groove_p, body_keep, chan, pry])
    pod -= cav

    # plate: USB-only plate, teardropped outline, BOOT hole, no post
    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    plate = prism(pocket_td.offset(-c.FIT_CLR - 0.03, Round), FLOOR, Z_CASE)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead_p
    plate += guides
    plate -= all_keep
    plate -= m3.Manifold.cylinder(Z_CASE + 1 - (b.pcb_back_z + 1.0), BOOT_HOLE_D/2, BOOT_HOLE_D/2, 64) \
        .translate([sw[c.BUTTON], b.sw_y, b.pcb_back_z + 1.0])

    # trim ring: rests on the cone RING_GAP off it, stops short of the glass
    k = RING_GAP*math.sqrt(2)
    ro = r_win - k - RING_FRONT - 0.8
    ring = m3.Manifold.revolve(poly([(RING_RI, RING_FRONT), (ro, RING_FRONT), (ro, RING_FRONT + 0.8),
                                     (RING_RI, r_win - k - RING_RI)]), SEG)

    zc = COLLAR_BOT                                        # neck bottom on the bed
    M = b2w(zc)
    pod_w = pod.transform(M)

    # ---- world: pillar (tapers above the clamp, swept top)
    sec = lambda w, d: poly([(0, -JT), (w - 3.0, -JT), (w, -JT + 3.0), (w, d - 1.5), (w - 1.5, d), (0, d)])
    pil = prism(sec(SX, YP), 0.0, CL_TOP) + m3.Manifold.batch_hull([prism(sec(SX, YP), CL_TOP - 0.01, CL_TOP),
                                                                    prism(sec(SX_TOP, YP), H - 0.01, H).translate([0, LEAN, 0])])
    pil -= m3.Manifold.cube([60, 60, 60]).translate([-30, -30, 0]).rotate([45, 0, 0]).translate([0, -JT + LEAN, H - 14.0])
    # web: wedge between the pillar's outer face and the pod's monitor-side face, trimmed by the rim plane
    side = [apply(M, (-W + 2.0, 0.0, bz))[:2] for bz in (z_cf, Z_CASE - 2.0)]   # inside the pod: no shared corner
    web_cs = poly([(SX - 2.0, -JT + 3.0), (SX - 2.0, YP)] + [tuple(p) for p in side[::-1]]).hull()
    web = prism(web_cs, 0.0, zc + T - CH_TOP - 2.0)
    web -= (half + cav).transform(M)
    # front lip, deep spine with louvres, rear arm: all stand on the bed
    lip = ext(poly([(-LIP, 0), (0.5, 0), (0.5, CL_TOP), (-LIP + 2.0, CL_TOP), (-LIP, CL_TOP - 2.0)]), "y", -JT, 0.0)
    lip -= prism(poly([(-LIP - 1, -JT - 1), (-LIP + 1.5, -JT - 1), (-LIP - 1, -JT + 1.5)]), -1, CL_TOP + 1)   # front edge chamfer
    spine = ext(poly([(YP - 1.0, 0), (Y_A1, 0), (Y_A1, CL_TOP - 3.0), (Y_A1 - 3.0, CL_TOP), (YP - 1.0, CL_TOP)]), "x", SP0, SP1)
    for yl in LOUVRES:                                     # pointed ends: 45-degree roofs
        spine -= ext(poly([(yl - 3.0, 23.0), (yl, 20.0), (yl + 3.0, 23.0), (yl + 3.0, 52.0), (yl, 55.0), (yl - 3.0, 52.0)]),
                     "x", SP0 - 1, SP1 + 1)
    arm = ext(poly([(ARM_X, 0), (SP1, 0), (SP1, CL_TOP - 3.0), (SP1 - 3.0, CL_TOP), (ARM_X + 3.0, CL_TOP),
                    (ARM_X, CL_TOP - 3.0)]), "y", Y_A0, Y_A1)
    y_nut = (Y_A0 + Y_A1)/2
    nut_slot = box(ARM_X - 1, SCREW_X + (NUT_AF + NUT_CLR)/2, y_nut - (NUT_H + NUT_CLR)/2, y_nut + (NUT_H + NUT_CLR)/2,
                   Z_S - NUT_AC/2 - 0.15, Z_S + NUT_AC/2 + 0.15)            # nut slides in from the inboard side
    bolt_hole = m3.Manifold.cylinder(Y_A1 - Y_A0 + 2, BOLT_HOLE/2, BOLT_HOLE/2, 48).rotate([-90, 0, 0]) \
        .translate([SCREW_X, Y_A0 - 1, Z_S])
    r2, w2, hx, hz, dx = math.sqrt(2), CABLE_SLOT/2, HOOK_X, HOOK_Z, HOOK_DX
    # J-hook in (x, z), through the arm along y: up the entry, over a 45-degree roof, down a 45-degree leg into a V
    entry = poly([(hx - w2, -1), (hx + w2, -1), (hx + w2, hz), (hx - w2, hz)])
    leg = poly([(hx - w2/r2, hz + w2/r2), (hx + w2/r2, hz - w2/r2), (hx - dx + w2/r2, hz - dx - w2/r2),
                (hx - dx - w2/r2, hz - dx + w2/r2)])
    cap = poly([(hx - w2/r2, hz + w2/r2), (hx - 0.207*w2, hz + 1.207*w2), (hx + w2, hz), (hx, hz)])
    hook = entry + leg + cap
    v_seat = np.array([hx - dx + w2/r2, (HOOK_Y0 + HOOK_Y1)/2, hz - dx - w2/r2 + 2.0*r2])   # Ø4 cable centre in the V
    hook_blk = ext(poly([(SP1 - 0.5, 0), (HOOK_XO, 0), (HOOK_XO, hz + 2.0), (HOOK_XO - 3.0, hz + 5.0), (SP1 - 0.5, hz + 5.0)]),
                   "y", HOOK_Y0, HOOK_Y1)
    hook_cut = ext(hook, "y", HOOK_Y0 - 1, HOOK_Y1 + 1)
    body = union([pod_w, pil, web, lip, spine, arm, hook_blk]) - nut_slot - bolt_hole - hook_cut

    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, FLOOR=FLOOR, Z_CASE=Z_CASE, BOSS_TIP=BOSS_TIP, COLLAR_BOT=COLLAR_BOT,
               bh_p=bh_p, hdrs=hdrs, sw=sw, M=M, zc=zc, r_win=r_win, pocket_td=pocket_td, cone=cone, half=half,
               y_nut=y_nut, pod_w=pod_w, hook_pt=v_seat)
    return feats, body, plate, ring, geo


# ---- clamp hardware at edge thickness E (world) -----------------------------------------
def hexa(af, h): return m3.Manifold.cylinder(h, af/math.sqrt(3), af/math.sqrt(3), 6)


def ycyl(h, r, seg=48): return m3.Manifold.cylinder(h, r, r, seg).rotate([-90, 0, 0])   # axis +y from y=0


def hardware(E):
    pad = (ycyl(PAD_T, PAD_D/2, 64) - ycyl(SOCK_DEPTH + 1, SOCK_D/2).translate([0, PAD_T - SOCK_DEPTH, 0])) \
        .translate([SCREW_X, E, Z_S])
    tip = E + PAD_T - SOCK_DEPTH
    head_y = tip + BOLT_L
    bolt = ycyl(BOLT_L, BOLT_D/2, 32).translate([SCREW_X, tip, Z_S]) + \
        hexa(HEAD_AF, HEAD_H).rotate([-90, 0, 0]).translate([SCREW_X, head_y, Z_S])
    nut = (hexa(NUT_AF, NUT_H).rotate([0, 0, 30]).rotate([-90, 0, 0]) - ycyl(NUT_H + 1, BOLT_D/2, 32).translate([0, -0.5, 0])) \
        .translate([SCREW_X, (Y_A0 + Y_A1)/2 - NUT_H/2, Z_S])
    knob = knob_solid().rotate([-90, 0, 0]).translate([SCREW_X, head_y - KNOB_WALL, Z_S])
    return dict(pad=pad, bolt=bolt, nut=nut, knob=knob, tip=tip, head_y=head_y)


def knob_solid():
    """Front face at z=0 (prints face down), M4 clearance through the front wall, hex pocket for the head."""
    k = m3.Manifold.cylinder(KNOB_T, KNOB_D/2, KNOB_D/2, 96)
    k -= union(m3.Manifold.cylinder(KNOB_T + 2, 1.6, 1.6, 24).translate([KNOB_D/2*math.cos(a), KNOB_D/2*math.sin(a), -1])
               for a in np.linspace(0, 2*math.pi, 12, endpoint=False))
    k -= m3.Manifold.cylinder(KNOB_T + 2, 2.2, 2.2, 32).translate([0, 0, -1])
    hr = (HEAD_AF + 0.15)/math.sqrt(3)
    return k - m3.Manifold.cylinder(KNOB_T, hr, hr, 6).translate([0, 0, KNOB_WALL])


def pad_print():
    return m3.Manifold.cylinder(PAD_T, PAD_D/2, PAD_D/2, 64) - \
        m3.Manifold.cylinder(SOCK_DEPTH + 1, SOCK_D/2, SOCK_D/2, 48).translate([0, 0, PAD_T - SOCK_DEPTH])


def monitor(E): return box(-140, 0, 0, E, -60, 200)


# ---- checks --------------------------------------------------------------------------
def run_checks(b, c, feats, body, plate, ring, geo):
    body_b = body.transform(inv(geo["M"]))
    static = {"body": body_b, "plate": plate}

    print("\n1. Badge at rest: no feature overlaps the body or plate (min gap, mm)")
    for f in feats:
        s = f.solid()
        vol = sum((s ^ m).volume() for m in static.values())
        gaps = {k: s.min_gap(m, 3.0) for k, m in static.items()}
        k = min(gaps, key=gaps.get)
        check(vol < 1e-3, f"{f.name:26s} overlap {vol:.4f} mm^3", f"gap {gaps[k]:.2f} to {k}")

    print(f"\n2. Header guides grip each header in x (>= {c.MIN_ENGAGE} deep)")
    i, o = c.HDR_CLR, c.HDR_CLR + c.GUIDE_WALL
    for h in geo["hdrs"]:
        x0, y0, x1, y1 = h.outline.bounds()
        for wn, w in {"-x wall": rect(x0 - o, x0 - i, y0, y1), "+x wall": rect(x1 + i, x1 + o, y0, y1)}.items():
            g = plate ^ prism(w, -5, geo["FLOOR"])
            eng = b.hdr_top_z - bbox(g)[0, 2] if not g.is_empty() else 0.0
            span = bbox(g)[1, 1] - bbox(g)[0, 1] if not g.is_empty() else 0.0
            check(eng >= c.MIN_ENGAGE and span >= 5.0, f"{h.name} {wn}", f"engages {eng:.2f} deep over {span:.1f} of y")

    print("\n3. Bezel: lip retains the glass, the display is clear, nothing presses the glass")
    probe = m3.Manifold.cylinder(30, (b.active_d + 1)/2, (b.active_d + 1)/2, SEG).translate([0, 0, -29.9])
    check((probe ^ body_b).volume() < 1e-4, f"window + hood clear the active display {b.active_d:.2f} + 1, 30 mm out",
          f"window {2*geo['r_win']:.2f}")
    lipring = prism(circle(b.r - 0.05) - circle(geo["r_win"] + 0.05), -0.05, 0.0)
    check((lipring ^ body_b).volume() > 0.5, "lip overlaps the glass edge (retains it)", f"{c.LIP_OVERLAP:.2f} per side")
    glass = feats[0].solid()
    g = ring.min_gap(glass, 2.0)
    check((ring ^ glass).volume() < 1e-6 and g >= 0.2, "trim ring never touches the glass", f"gap {g:.2f}")
    v, g = (ring ^ body_b).volume(), ring.min_gap(body_b, 1.0)
    check(v < 1e-3 and g <= RING_GAP + 0.02, "trim ring sits on the cone, no overlap", f"{v:.4f} mm^3, gap {g:.2f}")

    print("\n4. Plate snap, walls, crown wall")
    v = (body_b ^ plate).volume()
    check(v < 1e-3, "body and plate do not overlap", f"{v:.4f} mm^3")
    s = (body_b ^ plate.translate([0, 0, geo["bh_p"]])).volume()
    check(s > 1.0, "plate pulled back one bead height interferes (it snaps)", f"{s:.1f} mm^3")
    check(abs(bbox(plate)[1, 2] - geo["Z_CASE"]) < 1e-3, "plate is flush with the pod back", f"b-z {geo['Z_CASE']:.2f}")
    rw, t = geo["r_win"], c.MIN_WALL*math.sqrt(2)          # cone grown 1.2 along its normal
    grown = (m3.Manifold.cylinder(30, rw + 30 + t, rw + t, SEG).translate([0, 0, -30]) - geo["half"]) \
        ^ box(-40, 40, -40, 40, -40, -c.LIP_T)
    thin = (grown - geo["cone"] - body_b).volume()
    check(thin < 0.5, f"hood wall >= {c.MIN_WALL} all round the cone", f"{thin:.2f} mm^3 short")
    wall = geo["BOSS_TIP"] - b.tip_y
    check(abs(wall - 2.95) < 0.1, "crown wall in front of the port = the printed USB-only case's", f"{wall:.2f} mm")
    check(SHELL_LEN - wall >= MIN_PLUG_ENGAGE, f"plug shell engages the port >= {MIN_PLUG_ENGAGE}",
          f"{SHELL_LEN - wall:.2f} of {SHELL_LEN}")
    pry = box(geo["R_REAR"] - 0.4, geo["R_REAR"] + 1.5, -2.4, 2.4, geo["Z_CASE"] - 1.4, geo["Z_CASE"])
    check((pry ^ body_b).volume() < 1e-3, "pry notch beside the plate edge is open", "1.5 deep, outboard side")

    print("\n5. Paths: plug and cable, badge and plate in from the back, BOOT from the back")
    bt = geo["BOSS_TIP"]
    plug = box(-PLUG_W/2, PLUG_W/2, bt, bt + PLUG_L, b.port_z - PLUG_T/2, b.port_z + PLUG_T/2)
    shell = box(-4.2, 4.2, b.tip_y - (SHELL_LEN - (bt - b.tip_y)), bt, b.port_z - 1.3, b.port_z + 1.3)
    cable = ycyl(60, 2.2, 24).rotate([0, 0, 0]).translate([0, bt + PLUG_L, b.port_z])
    both = body_b + plate
    for nm, s in (("plug overmold 12 x 8 x 22, pushed home", plug), ("plug metal shell", shell),
                  ("cable, 60 mm straight down", cable)):
        v = (s ^ both).volume()
        check(v < 1e-3, f"{nm} clear", f"{v:.4f} mm^3, gap {s.min_gap(both, 3.0):.2f}")
    corridor = prism(geo["pocket_td"], geo["Z_CASE"] + 0.01, geo["Z_CASE"] + 50)
    v = (corridor ^ body_b).volume()
    check(v < 1e-3, "badge and plate go in straight from the back (50 mm corridor)", f"{v:.4f} mm^3")
    x, y = geo["sw"][c.BUTTON], b.sw_y
    top = b.pcb_back_z + b.sw_cap_h
    pin = lambda dz: m3.Manifold.cylinder(geo["Z_CASE"] + 60 - (top - dz), PIN_D/2, PIN_D/2, 48).translate([x, y, top - dz])
    for dz, label in ((0.0, "at rest"), (c.SW_TRAVEL, f"pressed {c.SW_TRAVEL:.2f}")):
        hit = sum((pin(dz) ^ m).volume() for m in (body_b, plate))
        check(hit < 1e-3, f"{PIN_D:g} mm stylus {label}, 60 mm long, clears everything", f"{hit:.4f} mm^3")
    act = next(f for f in feats if f.name == f"{c.BUTTON} actuator")
    v = (pin(c.SW_TRAVEL) ^ act.solid()).volume()
    check(v > 1e-3, f"stylus pressed {c.SW_TRAVEL:.2f} reaches the actuator", f"{v:.3f} mm^3")
    print(f"       BOOT hole: {geo['Z_CASE'] - top:.1f} mm from the plate back to the actuator")


def clamp_checks(body, geo):
    print(f"\n6. Clamp: grip range {E_MIN:g}-{E_MAX:g} mm; nothing touches the screen")
    for E in (E_MIN, 20.0, E_MAX):
        hw, mon = hardware(E), monitor(E)
        v = (body ^ mon).volume()
        check(v < 1e-3, f"E={E:4.1f}: body clear of the monitor", f"{v:.4f} mm^3")
        for nm in ("pad", "bolt", "nut", "knob"):
            v = (hw[nm] ^ body).volume() + ((hw[nm] ^ mon).volume() if nm != "pad" else 0.0)
            check(v < 1e-3, f"E={E:4.1f}: {nm} clear of the body{'' if nm == 'pad' else ' and monitor'}", f"{v:.4f} mm^3")
        gap = hw["pad"].min_gap(mon, 1.0)
        check(gap < 0.01 and (hw["pad"] ^ mon).volume() < 1e-3, f"E={E:4.1f}: pad lands on the monitor back", f"gap {gap:.3f}")
        eng = min(hw["head_y"], Y_A1) - max(hw["tip"], Y_A0)
        check(eng >= NUT_H + 2, f"E={E:4.1f}: bolt runs through nut and arm", f"{eng:.1f} mm of the arm threaded")
        kf = hw["head_y"] - KNOB_WALL - Y_A1
        check(kf >= 0.5, f"E={E:4.1f}: knob clear of the arm", f"{kf:.1f} mm")
    lf = body ^ box(-LIP - 1, 0, -0.01, 0.01, 0, H + 1)
    check(bbox(lf)[0, 0] >= -LIP - 1e-6, f"only the {LIP:g} mm lip touches the front face", f"x >= {bbox(lf)[0, 0]:.2f}")
    check((body ^ box(-200, -LIP - 0.01, -2.0, 0.0, -100, 300)).is_empty(),
          f"nothing within 2 mm of the screen beyond the {LIP:g} mm lip", "clear")
    check(bbox(geo["pod_w"])[0, 0] > 0, "pod entirely outboard of the monitor's side face", f"min x {bbox(geo['pod_w'])[0, 0]:.1f}")
    side = body ^ box(-0.01, 0.01, 0.0, min(YP, E_MIN), -1, CL_TOP)
    check(not side.is_empty() and bbox(side)[0, 2] < 0.5 and bbox(side)[1, 2] > CL_TOP - 0.5,
          f"pillar's inner face bears on the monitor side, z 0..{CL_TOP:g}, any edge", f"z {bbox(side)[0, 2]:.0f}..{bbox(side)[1, 2]:.0f}")
    hp = geo["hook_pt"]
    cab = lambda dz: m3.Manifold.cylinder(HOOK_Y1 - HOOK_Y0 + 15, 2.0, 2.0, 24).rotate([-90, 0, 0]).translate([hp[0], HOOK_Y0, hp[2] + dz])
    v0, v1 = (cab(0.05) ^ body).volume(), (cab(-0.5) ^ body).volume()
    check(v0 < 1e-3 and v1 > 1e-3, "Ø4 cable seats in the J-hook's V (a pull down seats it)", f"clear {v0:.4f}, 0.5 lower hits {v1:.1f} mm^3")


def grip_n_required(W, com, pulls, E):
    """Least clamp force that holds weight + each pull. Lip (y=0) and pad (y=E) carry friction <= MU*N;
    the lip's pressure spread carries moments up to its kern limit (N*h/6); the pillar's inner face
    pushes back at z=0 or z=CL_TOP (roll). Anything left over becomes a friction couple across E."""
    O = np.array([SCREW_X, E/2, Z_S])                      # midway between the lip and pad contacts
    zj = Z_S
    worst = 0.0
    for pt, d in pulls:
        F = np.array([0.0, 0.0, -W]) + PULL*np.asarray(d, float)
        r_w, r_p = np.asarray(com) - O, np.asarray(pt) - O
        Mo = np.cross(r_w, [0, 0, -W]) + np.cross(r_p, PULL*np.asarray(d, float))
        # roll (about y): side face R_b at z=0, R_t at z=CL_TOP (the leaning top may miss a thin monitor), both >= 0
        best = None
        for Rb in np.linspace(0, 30, 3001):
            Rt = (-Mo[1] + zj*Rb)/(CL_TOP - zj)
            if Rt < -1e-9: continue
            fx = -F[0] - Rb - Rt
            if best is None or abs(fx) < abs(best): best = fx
        fx = best

        def ok(N0):
            NL, NP = N0 + F[1]/2, N0 - F[1]/2
            if NL <= 0 or NP <= 0: return False
            ex_p = max(0.0, abs(Mo[0]) - NL*CL_TOP/6)   # pitch beyond the lip's kern -> z friction couple
            ex_y = max(0.0, abs(Mo[2]) - NL*LIP/6)      # yaw beyond the lip's kern -> x friction couple
            # (the pad sits on a bolt tip: it carries no moment)
            fz, gz, gx = abs(F[2])/2, ex_p/E, ex_y/E
            return math.hypot(abs(fx)/2 + gx, fz + gz) <= MU*min(NL, NP)
        lo, hi = 0.0, 500.0
        for _ in range(60):
            mid = (lo + hi)/2
            lo, hi = (mid, hi) if not ok(mid) else (lo, mid)
        worst = max(worst, hi)
    return worst


def statics(body, plate, geo):
    print(f"\n7. Statics: weight and 1 N cable pull vs grip (mu {MU}, clamp {N_CLAMP:g} N assumed)")
    M = geo["M"]; hw = hardware(20.0)
    items = [("body", body.volume()*RHO, to_tm(body).center_mass), ("plate", plate.volume()*RHO, apply(M, bbox(plate).mean(0))),
             ("badge", BADGE_G, apply(M, (0, 0, 3.0))), ("plug", PLUG_G, apply(M, (0, geo["BOSS_TIP"] + PLUG_L/2, 5.0))),
             ("bolt", BOLT_G, bbox(hw["bolt"]).mean(0)), ("nut", NUT_G, bbox(hw["nut"]).mean(0)),
             ("knob", hw["knob"].volume()*RHO, bbox(hw["knob"]).mean(0)), ("pad", hw["pad"].volume()*RHO, bbox(hw["pad"]).mean(0))]
    m_tot = sum(m for _, m, _ in items)
    com = sum(m*np.asarray(p) for _, m, p in items)/m_tot
    W = m_tot*9.81e-3
    print(f"       mass {m_tot:.0f} g if solid (body {items[0][1]:.0f} g), COM ({com[0]:.1f}, {com[1]:.1f}, {com[2]:.1f}), "
          f"{W:.2f} N, {com[0] - SCREW_X:.0f} mm out from the jaws")
    dirs = [(0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
    plug_end = apply(M, (0, geo["BOSS_TIP"] + PLUG_L, 5.0))
    for label, pt, need in (("cable in the J-hook", geo["hook_pt"], SF_MIN),
                            ("cable yanked at the plug, hook unused", plug_end, SF_MIN_PLUG)):
        n, E, d = max((grip_n_required(W, com, [(pt, d)], E), E, d) for E in (E_MIN, 20.0, E_MAX) for d in dirs)
        check(N_CLAMP/n >= need, f"grip SF >= {need:g}: {label}",
              f"SF {N_CLAMP/n:.1f} (worst: pull {d}, {E:g} mm edge, needs {n:.1f} N)")
    n0 = max(grip_n_required(W, com, [(com, (0, 0, 0))], E) for E in (E_MIN, E_MAX))
    print(f"       weight alone needs {n0:.1f} N of clamp: SF {N_CLAMP/n0:.0f}")
    lip_s = F_HARD*(LIP/2)/(CL_TOP*JT**2/6)
    arm_s = F_HARD*(SP0 - SCREW_X)/(CL_TOP*ARM_T**2/6)
    sp_h = CL_TOP - (55.0 - 20.0)                           # deep spine height left beside a louvre
    sp_s = F_HARD*((SP0 + SP1)/2 - SCREW_X)/(sp_h*(SP1 - SP0)**2/6) + F_HARD/(sp_h*(SP1 - SP0))
    for nm, sg in (("front lip root", lip_s), ("rear arm root", arm_s), ("deep spine through a louvre", sp_s)):
        check(sg < SIG_ALLOW, f"{nm} at {F_HARD:g} N clamp (bends along the layers)", f"{sg:.1f} MPa < {SIG_ALLOW:g}")
    check(10 <= CANT <= 25, "pod turned toward you 10-25 degrees", f"{CANT:g}")
    return com


# ---- renders ---------------------------------------------------------------------------
# "matte black" is drawn charcoal so the facets read; the plate a shade lighter
BODY_C, PLATE_C, DARK, STEEL, GLASS, WHITE, ORANGE, SILVER, MON, SCR, CAB, KNOB_C = ((0.30, 0.30, 0.33),
    (0.44, 0.44, 0.47), (0.07, 0.07, 0.08), (0.66, 0.68, 0.72), (0.03, 0.05, 0.10), (0.92, 0.92, 0.88),
    (1.0, 0.42, 0.08), (0.84, 0.84, 0.87), (0.13, 0.13, 0.15), (0.16, 0.24, 0.40), (0.85, 0.85, 0.85), (0.20, 0.20, 0.22))


def gauge_face(b):
    """Render-only: a boost gauge on the display, upright (b-y up, b+x right from the front)."""
    rf = b.active_d/2
    face = [(prism(circle(rf), -0.12, -0.02), GLASS)]
    for i in range(11):
        w, L = (0.9, 3.4) if i % 2 == 0 else (0.5, 2.0)
        face.append((m3.Manifold.cube([w, L, 0.1]).translate([-w/2, -(rf - 0.9), -0.24]).rotate([0, 0, -135 + 27*i]),
                     ORANGE if i >= 9 else WHITE))
    needle = poly([(-0.9, 3.0), (0.9, 3.0), (0.2, -(rf - 3.2)), (-0.2, -(rf - 3.2))])
    face += [(prism(needle, -0.36, -0.26).rotate([0, 0, -135 + 270*0.72]), ORANGE), (prism(circle(2.4), -0.5, -0.3), DARK)]
    return face


def cable_path(geo, b):
    """Render-only cable: down from the plug, under the pod to the foot of the pillar, up into the J-hook,
    back along the clamp's outer face and down behind the monitor. A Catmull-Rom curve through these points."""
    M = geo["M"]; hp = geo["hook_pt"]
    p0 = apply(M, (0, geo["BOSS_TIP"] + PLUG_L, b.port_z))
    hx, hz = hp[0], hp[2]
    ctrl = [p0 + (0, 0, 6), p0, p0 + (0, 0, -9), p0 + (-9, 4, -17), (HOOK_X + 2, 3, -10), (HOOK_X, 3.5, 2),
            (HOOK_X - 0.6, 4.5, HOOK_Z - 0.5), (hx, 7.5, hz), (hx, 14, hz), (hx, 24, hz), (hx + 0.5, 40, hz + 1),
            (hx, 54, hz - 3), (hx - 4, 60, -18), (hx - 6, 62, -45), (hx - 6, 62, -60)]
    ctrl = [np.asarray(q, float) for q in ctrl]
    pts = []
    for q0, q1, q2, q3 in zip(ctrl, ctrl[1:], ctrl[2:], ctrl[3:]):
        for t in np.linspace(0, 1, 6, endpoint=False):
            pts.append(0.5*((2*q1) + (-q0 + q2)*t + (2*q0 - 5*q1 + 4*q2 - q3)*t**2 + (-q0 + 3*q1 - 3*q2 + q3)*t**3))
    pts.append(ctrl[-2])
    sph = [m3.Manifold.sphere(2.0, 12).translate(list(map(float, p))) for p in pts]
    return union([m3.Manifold.batch_hull([a, c]) for a, c in zip(sph, sph[1:])])


def stylus(b, c, geo, L=28.0):
    top = b.pcb_back_z + b.sw_cap_h
    return m3.Manifold.cylinder(geo["Z_CASE"] + L - top, PIN_D/2, PIN_D/2, 24).translate([geo["sw"][c.BUTTON], b.sw_y, top])


def scene(b, c, feats, body, plate, ring, geo, E=20.0, mon=True, cable=True, hw_on=True, badge="face", pin=False,
          mon_box=(-60, -30, 120)):
    M = geo["M"]; Wd = lambda m: m.transform(M)
    bt = geo["BOSS_TIP"]
    parts = [(body, BODY_C), (Wd(plate), PLATE_C), (Wd(ring), SILVER)]
    if badge == "face":
        parts += [(Wd(feats[0].solid()), DARK)] + [(Wd(m), col) for m, col in gauge_face(b)]
    elif badge == "all":
        parts += [(Wd(f.solid()), DARK if f.name == "disc + tab" else (0.25, 0.70, 0.35) if f.name.startswith(c.BUTTON)
                   else WHITE) for f in feats if not f.name.startswith("plug")]
    if pin:
        parts.append((Wd(stylus(b, c, geo)), ORANGE))
    if cable:
        parts.append((Wd(box(-PLUG_W/2, PLUG_W/2, bt, bt + PLUG_L, b.port_z - PLUG_T/2, b.port_z + PLUG_T/2)), CAB))
        parts.append((cable_path(geo, b), CAB))
    if hw_on:
        hw = hardware(E)
        parts += [(hw["pad"], DARK), (hw["bolt"], STEEL), (hw["nut"], STEEL), (hw["knob"], KNOB_C)]
    if mon:
        x0, z0, z1 = mon_box
        parts.append((box(x0, 0, 0, E, z0, z1), MON))
        parts.append((box(x0, -LIP - 1.5, -0.4, 0.0, z0, z1), SCR))   # the screen, past a 7.5 mm bezel band
    return parts


def renders(b, c, feats, body, plate, ring, geo):
    R = lambda m: m.refine_to_length(1.5)
    def go(parts, path, **kw): render([(R(m), col) for m, col in parts if not m.is_empty()], PNG + path, **kw)
    M = geo["M"]; Wd = lambda m: m.transform(M)
    go(scene(b, c, feats, body, plate, ring, geo, mon_box=(-45, -20, 145)), "01-hero.png", elev=14, azim=-56, zoom=1.2,
       title=f"Sidepod on a 20 mm monitor edge: hooded pod, {CANT:g} deg toward you, cable to the hook and down the back")
    go(scene(b, c, feats, body, plate, ring, geo, mon_box=(-45, -10, 150)), "02-as-you-see-it.png", elev=4, azim=-110,
       zoom=1.1, title="From your chair, looking down the pod's axis")
    go(scene(b, c, feats, body, plate, ring, geo, pin=True, mon_box=(-30, -10, 150)), "03-back-boot.png", elev=12, azim=52,
       zoom=1.1, light=(0.55, 0.75, 0.45),
       title="From behind: plate flush in the pod back, Ø2 stylus (orange) in the BOOT hole, pry notch on the outboard edge")
    go(scene(b, c, feats, body, plate, ring, geo, E=32.0, mon_box=(-30, -10, 110)), "04-clamp-32mm.png", elev=26, azim=32,
       zoom=1.0, light=(0.6, 0.6, 0.55), title="Clamp on a 32 mm edge from behind: knob, M4 bolt, nut in its side slot, louvres, J-hook")

    # sections in the badge frame, drawn with world-up up and the glass to the left
    Mi = inv(M)
    D = np.array([[0, 0, 1, 0], [-1, 0, 0, 0], [0, -1, 0, 0]], float)       # (bx, by, bz) -> (bz, -bx, -by)
    bt = geo["BOSS_TIP"]
    plug_b = box(-PLUG_W/2, PLUG_W/2, bt, bt + PLUG_L, b.port_z - PLUG_T/2, b.port_z + PLUG_T/2)
    cab_b = ycyl(14, 2.0, 24).translate([0, bt + PLUG_L, b.port_z])
    sec = [(body.transform(Mi), BODY_C), (plate, PLATE_C), (ring, SILVER), (plug_b, CAB), (cab_b, CAB)] + \
          [(f.solid(), DARK if f.name == "disc + tab" else (0.25, 0.70, 0.35) if f.name.startswith(c.BUTTON) else WHITE)
           for f in feats if not f.name.startswith("plug")]
    for xc, nm, title, extra in (
            (0.0, "05-section-pod.png", "Section on the pod axis: 45-deg cone = window bevel, teardrop roof, plug home in the neck", []),
            (geo["sw"][c.BUTTON], "05b-section-boot.png", "Section through BOOT: Ø2 stylus (orange) through the plate onto the switch",
             [(stylus(b, c, geo, 20.0), ORANGE)])):
        crop = box(xc - 8.0, xc, -40, 60, -16, 13)                         # an 8 mm slab, b-x <= xc: the cut faces +b-x
        cut = [((m ^ crop).transform(D), col) for m, col in sec] + \
              [((m ^ box(xc - 8.0, xc + 2.0, -40, 60, -16, 40)).transform(D), col) for m, col in extra]
        go(cut, nm, elev=0, azim=-90, zoom=1.25, title=title)

    # clamp section at the bolt height, from above
    hw = hardware(20.0)
    parts = [(body, BODY_C), (hw["pad"], DARK), (hw["bolt"], STEEL), (hw["nut"], STEEL), (hw["knob"], KNOB_C),
             (box(-45, 0, 0, 20.0, -10, 80), MON), (box(-45, -LIP - 1.5, -0.4, 0.0, -10, 80), SCR),
             (Wd(plate), PLATE_C), (Wd(feats[0].solid()), DARK)]
    cut = [(m.trim_by_plane([0, 0, -1], -Z_S), col) for m, col in parts]
    go(cut, "06-section-clamp.png", elev=89, azim=-90, zoom=1.2,
       title=f"Section at the bolt (z {Z_S:g}), from above: lip on the bezel, pad on the back, pillar on the side face")

    # print layout: everything as exported, on a 256 bed
    bed = box(-128, 128, -128, 128, -1.0, 0.0)
    lay = [(bed, (0.80, 0.80, 0.78)), (body.translate([-bbox(body).mean(0)[0] - 40, -bbox(body).mean(0)[1], 0]), BODY_C),
           (plate.rotate([0, 180, 0]).translate([45, -25, geo["Z_CASE"]]), PLATE_C),
           (knob_solid().translate([45, 35, 0]), KNOB_C), (pad_print().translate([75, 35, 0]), DARK),
           (ring.translate([82, -25, -RING_FRONT]), SILVER)]
    go(lay, "07-print-layout.png", elev=32, azim=-62, zoom=1.0,
       title="Print layout, as exported: body upright (no supports), plate face-down, knob, pad, optional ring")

    # exploded: ring out the front, badge and plate out the back, plug from below, hardware lifted along its axis
    a = np.array([S_, C_, 0.0])
    up = np.array([0.0, 0.0, 70.0])
    ex = [(body, BODY_C), (Wd(ring).translate(list(-30*a)), SILVER)] + \
         [(Wd(f.solid()).translate(list(34*a)), DARK if f.name == "disc + tab" else WHITE) for f in feats
          if not f.name.startswith("plug")] + \
         [(Wd(plate).translate(list(66*a)), PLATE_C),
          (Wd(box(-PLUG_W/2, PLUG_W/2, geo["BOSS_TIP"], geo["BOSS_TIP"] + PLUG_L, b.port_z - PLUG_T/2,
                  b.port_z + PLUG_T/2)).translate([0, 0, -28]), CAB),
          (hw["pad"].translate(list(up + [0, -6, 0])), DARK), (hw["nut"].translate(list(up + [-16, 0, 0])), STEEL),
          (hw["bolt"].translate(list(up + [0, 18, 0])), STEEL), (hw["knob"].translate(list(up + [0, 30, 0])), KNOB_C)]
    go(ex, "08-exploded.png", elev=20, azim=-28, zoom=1.0,
       title="Exploded: ring in front; badge, plate in from the back; plug from below; pad, nut, M4 bolt, knob (lifted)")


def main():
    b = Badge()
    c = replace(Case(), LIP_BEVEL=Case().LIP_T)   # 45-degree window bevel: prints upright, flows into the hood
    feats, body, plate, ring, geo = build(b, c)
    bb = bbox(body)
    print(f"Body {bb[1][0]-bb[0][0]:.1f} x {bb[1][1]-bb[0][1]:.1f} x {bb[1][2]-bb[0][2]:.1f} mm (x y z); pod centre "
          f"({X_C:.0f}, {Y_GLASS:.0f}, {geo['zc']:.1f}); glass {-Y_GLASS:.0f} mm proud of the screen; cant {CANT:g}")
    run_checks(b, c, feats, body, plate, ring, geo)
    clamp_checks(body, geo)
    statics(body, plate, geo)
    print()
    export(body, STL + "pillar and pod.stl", lambda m: m.translate([0, 0, -bbox(m)[0, 2]]))
    export(plate, STL + "back plate (BOOT hole).stl", lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]]))
    export(knob_solid(), STL + "knob.stl", lambda m: m)
    export(pad_print(), STL + "pad.stl", lambda m: m)
    export(ring, STL + "trim ring (optional).stl", lambda m: m.translate([0, 0, -RING_FRONT]))
    if "--no-render" not in sys.argv:
        renders(b, c, feats, body, plate, ring, geo)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
