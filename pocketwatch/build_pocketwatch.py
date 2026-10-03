#!/usr/bin/env python3
"""
Pocketwatch case for the 1.28 badge (ESP32-S3-LCD-1.28).

Three printed parts:
  CASE   bezel lip, the badge bore, a step, and a wider battery chamber behind
         it. At 12 o'clock a recess lets any straight USB-C cable seat fully in
         the port: the plug is the crown, the cable is the chain.
  PLATE  drops in from the back onto the step and snaps into a groove in the
         badge bore. Carries the header guides and the BOOT post.
  LID    snaps into the back of the battery chamber and holds the LiPo
         against the plate.

The badge floats. At rest the glass sits on the lip. Pressing the screen slides
it back REST_CLR + SW_TRAVEL until the BOOT actuator bottoms on the post, and
that is the click. Everything else stays FLOAT clear, so the switch is the first
hard stop. The header guides fit snugly in x and are open-ended in y. y and
rotation come from the round board in the bore and the tab in its slot.

Every solid comes from two tables. `Badge` is what the board IS (measured).
`Case` is what we CHOOSE. Badge frame: origin = disc centre on the glass face,
+y toward the USB-C tab (12 o'clock), +x right as seen from the BACK, +z
backward from the glass into the case.

Run with ~/.venvs/cad/bin/python from the repo root.
"""
import sys, math
from dataclasses import dataclass, field, fields
import numpy as np, manifold3d as m3, trimesh
sys.path.insert(0, "pod"); from render import render

Round = m3.JoinType.Round
SEG = 180


def ph(value, replaced_by):
    """A PLACEHOLDER: a guess standing in for a measurement. Listed at the top of every run."""
    return field(default=value, metadata={"placeholder": replaced_by})


@dataclass(frozen=True)
class Badge:
    disc_d: float = 35.31            # envelope across, treated as a circle
    tip_to_far_edge: float = 38.64   # USB-C tab tip to the far edge of the disc
    tab_w_root: float = 16.25
    tab_w_tip: float = 15.38
    tab_corner_r: float = 1.0        # assumed
    pcb_back_z: float = 4.53         # owner also wrote "~5"; 4.53 is the caliper number
    hdr_top_z: float = 8.15
    jst_top_z: float = 7.64
    port_z: float = 5.0              # USB-C port centre, behind the glass face
    port_w: float = 8.94             # USB-C receptacle shell (standard), flush with the tab tip
    port_h: float = 3.26
    port_len: float = 7.35
    active_d_drawing: float = 32.4   # active display on Waveshare's drawing (PCB 36.5)
    hdr_len: float = 13.25           # female 2x10 1.27 sockets, along y
    hdr_w: float = 3.0
    hdr_span: float = 30.0           # outside edge of H1 to outside edge of H2
    sw_x: float = ph(11.1, "switch actuator |x| from centre (BOOT at -x, from the back)")  # PLACEHOLDER
    sw_y: float = ph(-10.2, "switch actuator y from centre")                               # PLACEHOLDER
    sw_body: float = ph(3.5, "switch housing, square")                                     # PLACEHOLDER
    sw_body_h: float = ph(1.4, "switch housing height off the PCB back")                   # PLACEHOLDER
    sw_cap_d: float = ph(1.8, "switch actuator diameter")                                  # PLACEHOLDER
    sw_cap_h: float = ph(2.0, "actuator top behind the PCB back")                          # PLACEHOLDER
    jst_x: float = ph(-7.6, "JST centre x, from the back")                                 # PLACEHOLDER
    jst_y: float = ph(8.5, "JST centre y")                                                 # PLACEHOLDER
    jst_w: float = ph(8.4, "JST footprint along x")                                        # PLACEHOLDER
    jst_d: float = ph(4.0, "JST footprint along y")                                        # PLACEHOLDER

    @property
    def r(self): return self.disc_d / 2

    @property
    def tip_y(self): return self.tip_to_far_edge - self.r

    @property
    def active_d(self): return self.active_d_drawing * self.disc_d / 36.5

    @property
    def hdr_y_half(self):
        """Headers' y position is unmeasured. Anywhere a header fits on the board is allowed:
        at its outer face the disc spans +-this, so the header sweeps y in [-this, +this]."""
        return math.sqrt(self.r**2 - (self.hdr_span/2)**2)


@dataclass(frozen=True)
class Case:
    BUTTON: str = "BOOT"         # which switch the post presses; the other gets a pocket
    REST_CLR: float = 0.20       # post tip to actuator at rest
    SW_TRAVEL: float = 0.25      # typical tact switch
    FLOAT: float = 0.70          # every other stop behind the badge: stroke + 0.25 print slop
    RAD_CLR: float = 0.25        # bore around disc + tab, per side
    XY_CLR: float = 0.30         # material beside switches, JST, port
    HDR_CLR: float = 0.15        # header guides, per side in x: snug sideways, free in z
    LIP_T: float = 1.2           # bezel lip thickness
    LIP_OVERLAP: float = 1.0     # lip over the glass edge
    LIP_BEVEL: float = 0.6       # window opens toward the front by this much
    CASE_WALL: float = 1.8
    CHAMFER: float = 0.8         # outer front / back edges
    RECESS_W: float = 14.0       # room for any straight USB-C overmold at 12 o'clock
    RECESS_T: float = 9.0
    GUIDE_WALL: float = 1.2
    POST_D: float = 3.0          # forgives ~0.6 mm of switch-position error
    FIT_CLR: float = 0.15        # plate skirt in the bore, lid in the chamber, per side
    SKIRT_WALL: float = 1.2
    SNAP_INT: float = 0.30       # bead past the bore wall, radial: the snap interference
    SNAP_CLR: float = 0.15       # groove around the bead
    SNAP_LIP: float = 1.2        # case material behind each groove
    BEAD_FLAT: float = 0.3
    PLATE_T: float = 2.4        # plate between the badge and the battery; carries the lead channel
    LEAD_CH_W: float = 3.0       # channel in the plate's back face: battery end -> lead hole
    LEAD_CH_D: float = 1.2
    LID_T: float = 2.0
    BAY_CLR: float = 0.3
    BATT_T: float = 7.4          # Makerfocus 1000 mAh, measured
    BATT_W: float = 22.28
    BATT_L: float = 42.65        # along y
    LEAD_HOLE: float = 6.0       # square hole in the plate over the JST for the battery lead
    MIN_WALL: float = 1.2
    MIN_ENGAGE: float = 1.5

    @property
    def STROKE(self): return self.REST_CLR + self.SW_TRAVEL


@dataclass(frozen=True)
class Feature:
    """One part of the badge (or the plug riding in its port): an xy outline over a z range."""
    name: str
    outline: m3.CrossSection
    z0: float
    z1: float
    fit: float           # sideways clearance any printed material keeps

    def solid(self, dz=0.0):
        return prism(self.outline, self.z0 + dz, self.z1 + dz)

    def grown(self):
        # Miter: a Round offset of a polygonal circle adds micro-arcs whose vertices pinch on export
        return self.outline.offset(self.fit, m3.JoinType.Miter, 4.0)

    def keepout(self, rear):
        return prism(self.grown(), self.z0, self.z1 + rear)


# ---- 2D/3D helpers ---------------------------------------------------------
def rect(x0, x1, y0, y1):
    return m3.CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])


def circle(r):
    return m3.CrossSection.circle(r, SEG)


def prism(cs, z0, z1):
    return m3.Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def union(ms):
    return m3.Manifold.batch_boolean(list(ms), m3.OpType.Add)


def chamfered(pieces, z0, z1, c0=0.0, c1=0.0):
    """Prism over the union of convex `pieces`, chamfered c0 at z0 and c1 at z1 (hull per piece)."""
    out = []
    for p in pieces:
        layers = [prism(p, z0 + c0, z1 - c1)]
        if c0: layers.append(prism(p.offset(-c0, Round), z0, z0 + 0.01))
        if c1: layers.append(prism(p.offset(-c1, Round), z1 - 0.01, z1))
        out.append(m3.Manifold.batch_hull(layers))
    return union(out)


def bbox(m):
    return np.array(m.bounding_box()).reshape(2, 3)


# half a segment out of phase with the bore polygons, or their vertices coincide and pinch
revolve = lambda cs: m3.Manifold.revolve(cs, SEG).rotate([0, 0, 180/SEG])


def snap(c: Case, r_bore, zb):
    """A 45-degree bead of radius r_bore - FIT_CLR at height zb, and the groove for it in the bore."""
    r_s = r_bore - c.FIT_CLR
    p = c.FIT_CLR + c.SNAP_INT
    bh = 2*p + c.BEAD_FLAT
    prof = m3.CrossSection([[(r_s - 0.5, zb - bh/2), (r_s, zb - bh/2), (r_s + p, zb - bh/2 + p),
                             (r_s + p, zb + bh/2 - p), (r_s, zb + bh/2), (r_s - 0.5, zb + bh/2)]])
    groove = revolve(prof.offset(c.SNAP_CLR, m3.JoinType.Miter))
    return revolve(prof), groove, bh, r_s + p + c.SNAP_CLR


# ---- the badge, as a table of features --------------------------------------
def disc_and_tab(b: Badge):
    y0, y1 = 12.0, b.tip_y                       # trapezoid starts inside the disc
    slope = (b.tab_w_root - b.tab_w_tip) / 2 / (b.tip_y - math.sqrt(b.r**2 - (b.tab_w_root/2)**2))
    w0 = b.tab_w_tip/2 + slope*(y1 - y0)
    tab = m3.CrossSection([[(-w0, y0), (w0, y0), (b.tab_w_tip/2, y1), (-b.tab_w_tip/2, y1)]])
    tab = tab.offset(-b.tab_corner_r, Round).offset(b.tab_corner_r, Round)
    return circle(b.r) + tab


def features(b: Badge, c: Case):
    pcb = b.pcb_back_z
    hx0, hh = b.hdr_span/2 - b.hdr_w, b.hdr_y_half
    hdr = lambda sx: rect(*sorted((sx*hx0, sx*b.hdr_span/2)), -hh, hh)   # every y a header can sit at
    sw = {"BOOT": -b.sw_x, "RESET": +b.sw_x}     # seen from the back, BOOT is lower-LEFT
    out = [
        Feature("disc + tab", disc_and_tab(b), 0.0, pcb, c.RAD_CLR),
        Feature("USB-C receptacle", rect(-b.port_w/2, b.port_w/2, b.tip_y - b.port_len, b.tip_y),
                b.port_z - b.port_h/2, b.port_z + b.port_h/2, c.XY_CLR),
        Feature("header H1 (any y)", hdr(-1), pcb, b.hdr_top_z, c.HDR_CLR),
        Feature("header H2 (any y)", hdr(+1), pcb, b.hdr_top_z, c.HDR_CLR),
        Feature("JST", rect(b.jst_x - b.jst_w/2, b.jst_x + b.jst_w/2, b.jst_y - b.jst_d/2, b.jst_y + b.jst_d/2),
                pcb, b.jst_top_z, c.XY_CLR),
        Feature("plug (any straight cable)", rect(-c.RECESS_W/2, c.RECESS_W/2, b.tip_y, b.tip_y + 40),
                b.port_z - c.RECESS_T/2, b.port_z + c.RECESS_T/2, c.XY_CLR),
    ]
    for name, x in sw.items():
        out.append(Feature(f"{name} housing", m3.CrossSection.square([b.sw_body]*2, True).translate([x, b.sw_y]),
                           pcb, pcb + b.sw_body_h, c.XY_CLR))
        out.append(Feature(f"{name} actuator", m3.CrossSection.circle(b.sw_cap_d/2, 48).translate([x, b.sw_y]),
                           pcb, pcb + b.sw_cap_h, c.XY_CLR))
    return out, sw


# ---- the case, plate and lid ------------------------------------------------
def build(b: Badge, c: Case):
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    R_BATT = 0.5*math.hypot(c.BATT_W, c.BATT_L) + c.BAY_CLR
    R_REAR = max(R_BATT, R_BORE + 1.0)            # battery chamber; always a step for the plate to sit on
    R_OUT = R_REAR + c.CASE_WALL
    FLOOR = b.hdr_top_z + c.FLOAT                 # the step = plate's front face
    batt_z0 = FLOOR + c.PLATE_T + c.BAY_CLR
    lid_z0 = batt_z0 + c.BATT_T + c.BAY_CLR
    bead_l, groove_l, bh_l, groove_r_l = snap(c, R_REAR, lid_z0 + c.LID_T/2)
    Z_CASE = lid_z0 + c.LID_T/2 + bh_l/2 + c.SNAP_CLR + c.SNAP_LIP   # case material behind the lid's groove
    bore_xy = feats[0].grown()
    outline = [circle(R_OUT)]

    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())

    # plate snap: bead on the skirt, groove in the badge bore SNAP_LIP in front of the step
    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4

    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    case = chamfered(outline, -c.LIP_T, Z_CASE, c.CHAMFER, c.CHAMFER)
    case -= prism(bore_xy, 0.0, FLOOR + 1)
    case -= prism(circle(R_REAR), FLOOR, Z_CASE + 1)
    case -= window.translate([0, 0, -c.LIP_T - 0.01])
    case -= groove_p + groove_l
    case -= all_keep
    # The recess ceiling is the chamber wall spanning 14 mm: a flat roof prints as a floating
    # bridge. A 45-degree pointed arch above it is self-supporting in the bezel-down print.
    w = c.RECESS_W/2 + c.XY_CLR
    z_top = b.port_z + c.RECESS_T/2 + c.FLOAT
    y0, L = b.tip_y - c.XY_CLR, R_OUT + 2 - (b.tip_y - c.XY_CLR)
    arch = m3.Manifold.extrude(m3.CrossSection([[(-w, z_top - 0.01), (w, z_top - 0.01), (0, z_top + w)]]), L)
    arch = arch.rotate([90, 0, 0]).translate([0, y0 + L, 0])
    ab = bbox(arch)
    assert abs(ab[0, 1] - y0) < 1e-3 and abs(ab[1, 2] - (z_top + w)) < 1e-3, f"arch misplaced: {ab}"
    case -= arch

    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, m3.JoinType.Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)   # overlap the skirt, never share its face
    plate = prism(circle(R_REAR - c.FIT_CLR), FLOOR, FLOOR + c.PLATE_T)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead_p
    plate += guides
    plate -= all_keep
    lead = m3.CrossSection.square([c.LEAD_HOLE]*2, True).translate([b.jst_x, b.jst_y])
    plate -= prism(lead, FLOOR - 1, FLOOR + c.PLATE_T + 1)
    # the battery covers the hole, so its lead runs past the battery end in a channel to reach it
    ch = rect(b.jst_x - c.LEAD_CH_W/2, b.jst_x + c.LEAD_CH_W/2, b.jst_y, R_REAR + 1)
    plate -= prism(ch, FLOOR + c.PLATE_T - c.LEAD_CH_D, FLOOR + c.PLATE_T + 1)
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_cyl = m3.Manifold.cylinder(FLOOR + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([sw[c.BUTTON], b.sw_y, tip_z])
    post = post_cyl - union(k for n, k in keep.items() if not n.startswith(c.BUTTON))
    plate += post

    lid = prism(circle(R_REAR - c.FIT_CLR), lid_z0, lid_z0 + c.LID_T) + bead_l
    battery = prism(rect(-c.BATT_W/2, c.BATT_W/2, -c.BATT_L/2, c.BATT_L/2), batt_z0, batt_z0 + c.BATT_T)
    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_OUT, FLOOR=FLOOR, Z_CASE=Z_CASE, lid_z0=lid_z0,
               bh_p=bh_p, bh_l=bh_l, groove_r_p=groove_r_p, groove_r_l=groove_r_l, bore_xy=bore_xy,
               outline_xy=circle(R_OUT), hdrs=hdrs, sw=sw, tip_z=tip_z, post_cyl=post_cyl)
    return feats, case, plate, lid, battery, geo


# ---- checks ----------------------------------------------------------------
FAILS = []


def check(ok, label, margin):
    print(f"  [{'ok' if ok else 'FAIL'}] {label:62s} {margin}")
    if not ok: FAILS.append(label)


def run_checks(b, c, feats, case, plate, lid, battery, geo):
    static = {"case": case, "plate": plate, "lid": lid, "battery": battery}
    target = f"{c.BUTTON} actuator"

    print(f"\n1. At rest: no badge feature overlaps the case, plate, lid or battery (min gap, mm)")
    for f in feats:
        s = f.solid()
        vol = sum((s ^ m).volume() for m in static.values())
        gaps = {k: s.min_gap(m, 3.0) for k, m in static.items()}
        k = min(gaps, key=gaps.get)
        check(vol < 1e-3, f"{f.name:26s} overlap {vol:.4f} mm^3", f"gap {gaps[k]:.2f} to {k}")
    gap_b = battery.min_gap(union(f.solid() for f in feats), 5.0)
    check(gap_b >= c.STROKE, f"battery clear of the badge by >= stroke {c.STROKE:.2f}", f"gap {gap_b:.2f}")

    print(f"\n2a. Axial room from rest before each feature touches anything: the switch must be first")
    def overlaps(f, dz): return sum((f.solid(dz) ^ m).volume() for m in static.values()) > 1e-4
    for f in feats:
        lo, hi = 0.0, 2.0
        if not overlaps(f, hi):
            r = math.inf
        else:
            while hi - lo > 0.005:
                mid = (lo + hi)/2
                lo, hi = (mid, hi) if not overlaps(f, mid) else (lo, mid)
            r = lo
        if f.name == target:
            check(abs(r - c.REST_CLR) < 0.02, f"{f.name:26s} meets the post after REST_CLR", f"{r:.2f}")
        else:
            check(r > c.STROKE + 0.1, f"{f.name:26s} room > stroke {c.STROKE:.2f} + 0.1",
                  f"{r:.2f} (margin {r - c.STROKE:.2f} past full click)" if r < math.inf else "nothing behind it")

    print(f"\n2b. Pressed {c.STROKE:.2f}: {target} on the post is the ONLY contact")
    for f in feats:
        s = f.solid(c.STROKE)
        vol = sum((s ^ m).volume() for m in static.values())
        if f.name == target:
            check(vol > 1e-3, f"{f.name:26s} pressed into the post {vol:.3f} mm^3",
                  f"= {c.SW_TRAVEL} travel x actuator area {math.pi*(b.sw_cap_d/2)**2*c.SW_TRAVEL:.3f}")
            continue
        gaps = {k: s.min_gap(m, 3.0) for k, m in static.items()}
        k = min(gaps, key=gaps.get)
        check(vol < 1e-3 and gaps[k] > 0.05, f"{f.name:26s} still clear", f"gap {gaps[k]:.2f} to {k}")

    print(f"\n3. Header guides grip each header in x at rest (>= {c.MIN_ENGAGE} deep)")
    i, o = c.HDR_CLR, c.HDR_CLR + c.GUIDE_WALL
    for h in geo["hdrs"]:
        x0, y0, x1, y1 = h.outline.bounds()
        for wn, w in {"-x wall": rect(x0 - o, x0 - i, y0, y1), "+x wall": rect(x1 + i, x1 + o, y0, y1)}.items():
            g = plate ^ prism(w, -5, geo["FLOOR"])
            eng = b.hdr_top_z - bbox(g)[0, 2] if not g.is_empty() else 0.0
            span = bbox(g)[1, 1] - bbox(g)[0, 1] if not g.is_empty() else 0.0
            check(eng >= c.MIN_ENGAGE and span >= 5.0, f"{h.name} {wn}", f"engages {eng:.2f} deep over {span:.1f} of y")

    print("\n4. Bezel lip")
    probe = m3.Manifold.cylinder(c.LIP_T + 2, (b.active_d + 1)/2, (b.active_d + 1)/2, SEG).translate([0, 0, -c.LIP_T - 1])
    win_d = 2*(b.r - c.LIP_OVERLAP)
    check((probe ^ case).volume() < 1e-4, f"window clears active display {b.active_d:.2f} + 1",
          f"window {win_d:.2f}, margin {win_d - b.active_d - 1:.2f}")
    ring = prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0)
    check((ring ^ case).volume() > 0.5, "lip overlaps the glass edge (retains it)", f"{c.LIP_OVERLAP:.2f} per side")

    print("\n5. Parts, snaps, walls")
    parts = {"case": case, "plate": plate, "lid": lid, "battery": battery}
    names = list(parts)
    for i1 in range(len(names)):
        for i2 in range(i1 + 1, len(names)):
            v = (parts[names[i1]] ^ parts[names[i2]]).volume()
            check(v < 1e-3, f"{names[i1]} and {names[i2]} do not overlap", f"{v:.4f} mm^3")
    for nm, part, bh in (("plate", plate, geo["bh_p"]), ("lid", lid, geo["bh_l"])):
        s = (case ^ part.translate([0, 0, bh])).volume()
        check(s > 1.0, f"{nm} pulled back one bead height interferes (it snaps)", f"{s:.1f} mm^3")
    walls = {"case wall behind the plate groove": geo["R_OUT"] - geo["groove_r_p"],
             "case wall behind the lid groove": geo["R_OUT"] - geo["groove_r_l"],
             "bezel lip": c.LIP_T, "plate under the lead channel": c.PLATE_T - c.LEAD_CH_D, "lid": c.LID_T,
             "guide walls": c.GUIDE_WALL, "skirt": c.SKIRT_WALL}
    for nm, t in walls.items():
        check(t >= c.MIN_WALL, f"{nm} >= {c.MIN_WALL}", f"{t:.2f}")
    recess_floor = geo["R_OUT"] - b.tip_y
    check(recess_floor < 10.0, "plug overmold reaches the port through the recess", f"recess {recess_floor:.1f} deep")


# ---- output ----------------------------------------------------------------
def export(m, path, print_xform):
    m = print_xform(m)
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    tm.export(path)
    check(tm.is_watertight and tm.volume > 0, f"{path} watertight", f"{m.volume()/1000:.2f} cm^3, {len(tm.faces)} tris")
    # In print orientation, every point of a layer that isn't over the layer below (45 degrees
    # allowed) must be within 2 mm of a supported point: a bridge spanning at most 4 mm.
    L, prev, worst = 0.3, None, (0.0, None)
    for z in np.arange(m.bounding_box()[2] + L/2, m.bounding_box()[5], L):
        cs = m.slice(z)
        if prev is not None:
            below = prev.offset(L, Round)
            far = (cs - below) - (cs ^ below).offset(2.0, Round)
            if far.area() > worst[0]: worst = (far.area(), z)
        prev = cs
    check(worst[0] < 0.1, f"{path} prints without supports",
          "every overhang bridges <= 4 mm" if worst[0] < 0.1 else f"{worst[0]:.1f} mm^2 floating at z {worst[1]:.2f}")


def renders(b, c, feats, case, plate, lid, battery, geo):
    # badge +y -> up, badge +z (backward) -> away from a viewer at azim 90. Refined to short edges because
    # the painter's sort misorders the long sliver triangles of big flat faces.
    D = lambda m: m.rotate([90, 0, 0]).refine_to_length(1.0)
    brass, back_c, lid_c, dark, white, red, steel, green, violet = ((0.82, 0.66, 0.32), (0.66, 0.50, 0.24),
        (0.74, 0.58, 0.28), (0.10, 0.10, 0.11), (0.95, 0.95, 0.90), (0.90, 0.25, 0.20), (0.55, 0.62, 0.72),
        (0.25, 0.70, 0.35), (0.62, 0.30, 0.80))
    post = plate ^ geo["post_cyl"]
    plate_np = plate - geo["post_cyl"]
    fs = {f.name: f.solid() for f in feats if not f.name.startswith("plug")}
    colour = lambda n: dark if n == "disc + tab" else green if n.startswith(c.BUTTON) else white
    out = "pocketwatch/renders/"

    E = 16.0
    ex = [(case, brass), (plate.translate([0, 0, 2*E]), back_c), (battery.translate([0, 0, 3*E]), steel),
          (lid.translate([0, 0, 4*E]), lid_c)]
    ex += [(s.translate([0, 0, E]), colour(n)) for n, s in fs.items()]
    render([(D(m), col) for m, col in ex], out + "exploded.png", elev=16, azim=-58,
           title="Pocketwatch, exploded from the back: case, badge, plate, battery, lid")

    def section(dz, path, title, box=None):
        parts = [(case, brass), (plate_np, back_c), (post, violet), (battery, steel), (lid, lid_c)] + \
                [(s.translate([0, 0, dz]), colour(n)) for n, s in fs.items()]
        x = geo["sw"][c.BUTTON]
        cut = []
        for m, col in parts:
            m = m.trim_by_plane([1, 0, 0], x).refine_to_length(1.0)
            if box is not None: m = m ^ box
            if not m.is_empty(): cut.append((D(m), col))
        render(cut, path, elev=0, azim=180, title=title)

    x = geo["sw"][c.BUTTON]
    section(0.0, out + "section-post.png",
            f"Section through the {c.BUTTON} post (x={x:+.1f}), at rest: glass on the lip, post {c.REST_CLR} off the switch")
    box = m3.Manifold.cube([3, 9, 9]).translate([x, b.sw_y - 4.5, 2.0])
    section(0.0, out + "section-post-detail-rest.png",
            f"{c.BUTTON} detail, at rest: switch (green) {c.REST_CLR} short of the post (violet)", box)
    section(c.STROKE, out + "section-post-detail-pressed.png",
            f"{c.BUTTON} detail, pressed {c.STROKE:.2f}: actuator on the post (click)", box)
    render([(D(plate_np), back_c), (D(post), violet)] + [(D(fs[n]), colour(n)) for n in fs if n.startswith(("header", "BOOT", "RESET", "JST"))],
           out + "plate-front.png", elev=-28, azim=62, title="Plate from the badge side: header guides, BOOT post, lead hole")
    render([(D(case), brass), (D(fs["disc + tab"]), dark)], out + "front.png", elev=12, azim=70,
           title="Front: bezel lip over the glass edge, USB-C recess at 12 o'clock")


def main():
    b, c = Badge(), Case()
    print("PLACEHOLDERS still in use (replace with measurements):")
    for t in (b, c):
        for f in fields(t):
            if "placeholder" in f.metadata:
                print(f"  {type(t).__name__}.{f.name:12s} = {getattr(t, f.name):7.2f}   <- {f.metadata['placeholder']}")

    feats, case, plate, lid, battery, geo = build(b, c)
    asm = bbox(case + plate + lid)
    size = asm[1] - asm[0]
    print(f"\nTip at y={b.tip_y:.3f}; headers may sit anywhere in y +-{b.hdr_y_half:.2f}; bore Ø{2*geo['R_BORE']:.2f}; "
          f"battery chamber Ø{2*geo['R_REAR']:.2f}; case Ø{2*geo['R_OUT']:.2f} x {size[2]:.2f} thick")
    run_checks(b, c, feats, case, plate, lid, battery, geo)
    print()
    export(case, "stl/pocketwatch/Pocketwatch - case.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(plate, "stl/pocketwatch/Pocketwatch - plate.stl",
           lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["FLOOR"] + c.PLATE_T]))
    export(lid, "stl/pocketwatch/Pocketwatch - lid.stl", lambda m: m.translate([0, 0, -geo["lid_z0"]]))
    if "--no-render" not in sys.argv:
        renders(b, c, feats, case, plate, lid, battery, geo)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
