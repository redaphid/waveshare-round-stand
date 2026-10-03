#!/usr/bin/env python3
"""
Pocketwatch case for the 1.28 badge (ESP32-S3-LCD-1.28).

Two printed parts:
  CASE  bezel lip, bore, and the pendant at 12 o'clock that the right-angle
        USB-C plug pushes into. The plug is the crown; the cable is the chain.
  BACK  snaps into a groove in the case bore. Carries the header guides, the
        BOOT post and the battery bay.

The badge floats. At rest the glass sits on the lip. Pressing the screen slides
it back REST_CLR + SW_TRAVEL until the BOOT actuator bottoms on the post, and
that is the click. Everything else stays FLOAT clear, so the switch is the first
hard stop.

Every solid comes from two tables. `Badge` is what the board IS (measured).
`Case` is what we CHOOSE. Badge frame: origin = disc centre on the glass face,
+y toward the USB-C tab (12 o'clock), +x right as seen from the BACK, +z
backward from the glass into the case.

Both parts are "raw shape minus every badge feature's keep-out" (the feature
grown sideways by its fit and swept back by FLOAT), so moving a feature in
`Badge` moves every pocket, notch and clearance with it.

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
    port_w: float = 8.94             # USB-C receptacle shell (standard), opening +y
    port_h: float = 3.26
    port_len: float = 7.35
    active_d_drawing: float = 32.4   # active display on Waveshare's drawing (PCB 36.5)
    hdr_len: float = 13.25           # female 2x10 1.27 sockets, along y
    hdr_w: float = 3.0
    hdr_span: float = ph(26.0, "outside edge of H1 to outside edge of H2")                 # PLACEHOLDER
    tab_to_hdr: float = ph(15.8, "tab tip down to the near (top) end of the headers")      # PLACEHOLDER
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


@dataclass(frozen=True)
class Case:
    BUTTON: str = "BOOT"         # which switch the post presses; the other gets a pocket
    REST_CLR: float = 0.20       # post tip to actuator at rest
    SW_TRAVEL: float = 0.25      # typical tact switch
    FLOAT: float = 0.70          # every other stop behind the badge: stroke + 0.25 print slop.
                                 # Capped by the guides: switch-end wall engages hdr_top - (housing + FLOAT)
    RAD_CLR: float = 0.25        # bore around disc + tab, per side
    XY_CLR: float = 0.30         # case material beside switches, JST, port
    HDR_CLR: float = 0.15        # header guides, per side: snug in x and y, free in z
    PLUG_CLR: float = 0.30       # pendant window around the plug overmold
    LIP_T: float = 1.2           # bezel lip thickness
    LIP_OVERLAP: float = 1.0     # lip over the glass edge
    LIP_BEVEL: float = 0.6       # window opens toward the front by this much
    CASE_WALL: float = 1.8
    CHAMFER: float = 0.8         # outer front / back edges
    BOSS_WALL: float = 1.6       # pendant side walls around the tab slot
    BOSS_TOP: float = 2.0        # pendant wall the plug passes through; < the plug's straight length
    BOSS_R: float = 3.0          # pendant corner radius
    GUIDE_WALL: float = 1.2
    POST_D: float = 3.0          # forgives ~0.6 mm of switch-position error
    FIT_CLR: float = 0.15        # back's skirt in the bore, per side
    SKIRT_WALL: float = 1.2
    SNAP_INT: float = 0.30       # bead past the bore wall, radial: the snap interference
    SNAP_CLR: float = 0.15       # groove around the bead
    SNAP_LIP: float = 1.2        # case material behind the groove
    BEAD_FLAT: float = 0.3
    BACK_T: float = 1.2          # back wall behind the battery
    BAY_CLR: float = 0.3
    BATT_T: float = ph(4.0, "LiPo thickness (default 401730)")                    # PLACEHOLDER
    BATT_W: float = ph(17.0, "LiPo width")                                        # PLACEHOLDER
    BATT_L: float = ph(30.0, "LiPo length, along y")                              # PLACEHOLDER
    BATT_Y: float = 0.0
    LEAD_X: float = ph(-6.0, "where the LiPo lead leaves the battery's top end")   # PLACEHOLDER
    LEAD_W: float = 4.0
    LEAD_L: float = 1.2          # room past the battery end for the lead to turn forward
    PLUG_W: float = ph(12.0, "plug overmold width at the metal")                  # PLACEHOLDER
    PLUG_T: float = ph(6.5, "plug overmold thickness at the metal")               # PLACEHOLDER
    PLUG_L: float = ph(15.0, "plug overmold straight length before the bend")     # PLACEHOLDER
    PLUG_GAP: float = 0.0        # overmold face to tab tip when fully seated
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
    front: float = 0.0   # clearance in front of z0 (only the plug has free space there)

    def solid(self, dz=0.0):
        return prism(self.outline, self.z0 + dz, self.z1 + dz)

    def grown(self):
        # Miter: a Round offset of a polygonal circle adds micro-arcs whose vertices pinch on export
        return self.outline.offset(self.fit, m3.JoinType.Miter, 4.0)

    def keepout(self, rear):
        return prism(self.grown(), self.z0 - self.front, self.z1 + rear)


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
    hx0, hy1 = b.hdr_span/2 - b.hdr_w, b.tip_y - b.tab_to_hdr
    hdr = lambda sx: rect(*sorted((sx*hx0, sx*b.hdr_span/2)), hy1 - b.hdr_len, hy1)
    sw = {"BOOT": -b.sw_x, "RESET": +b.sw_x}     # seen from the back, BOOT is lower-LEFT
    out = [
        Feature("disc + tab", disc_and_tab(b), 0.0, pcb, c.RAD_CLR),
        Feature("USB-C receptacle", rect(-b.port_w/2, b.port_w/2, b.tip_y - b.port_len, b.tip_y),
                b.port_z - b.port_h/2, b.port_z + b.port_h/2, c.XY_CLR),
        Feature("header H1", hdr(-1), pcb, b.hdr_top_z, c.HDR_CLR),
        Feature("header H2", hdr(+1), pcb, b.hdr_top_z, c.HDR_CLR),
        Feature("JST", rect(b.jst_x - b.jst_w/2, b.jst_x + b.jst_w/2, b.jst_y - b.jst_d/2, b.jst_y + b.jst_d/2),
                pcb, b.jst_top_z, c.XY_CLR),
        Feature("plug overmold", rect(-c.PLUG_W/2, c.PLUG_W/2, b.tip_y + c.PLUG_GAP, b.tip_y + c.PLUG_GAP + c.PLUG_L),
                b.port_z - c.PLUG_T/2, b.port_z + c.PLUG_T/2, c.PLUG_CLR, front=c.PLUG_CLR),
    ]
    for name, x in sw.items():
        out.append(Feature(f"{name} housing", m3.CrossSection.square([b.sw_body]*2, True).translate([x, b.sw_y]),
                           pcb, pcb + b.sw_body_h, c.XY_CLR))
        out.append(Feature(f"{name} actuator", m3.CrossSection.circle(b.sw_cap_d/2, 48).translate([x, b.sw_y]),
                           pcb, pcb + b.sw_cap_h, c.XY_CLR))
    return out, sw


# ---- the case and the back -------------------------------------------------
def build(b: Badge, c: Case):
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    R_OUT = R_BORE + c.CASE_WALL
    FLOOR = b.hdr_top_z + c.FLOAT                 # guide floors = back's inner face = case rear face
    bore_xy = feats[0].grown()                    # the disc + tab keep-out, so bore and keep-out are one surface
    pend_hw = b.tab_w_root/2 + c.RAD_CLR + c.BOSS_WALL
    pend_top = b.tip_y + c.RAD_CLR + c.BOSS_TOP
    pendant = rect(-pend_hw, pend_hw, 10.0, pend_top).offset(-c.BOSS_R, Round).offset(c.BOSS_R, Round)
    outline = [circle(R_OUT), pendant]

    # snap: a 45-degree bead on the back's skirt, a matching groove in the case bore
    r_s = R_BORE - c.FIT_CLR
    p = c.FIT_CLR + c.SNAP_INT
    bh = 2*p + c.BEAD_FLAT
    zb = FLOOR - c.SNAP_LIP - c.SNAP_CLR - bh/2
    bead_prof = m3.CrossSection([[(r_s - 0.5, zb - bh/2), (r_s, zb - bh/2), (r_s + p, zb - bh/2 + p),
                                  (r_s + p, zb + bh/2 - p), (r_s, zb + bh/2), (r_s - 0.5, zb + bh/2)]])
    # half a segment out of phase with the bore polygon, or their vertices coincide and pinch
    revolve = lambda cs: m3.Manifold.revolve(cs, SEG).rotate([0, 0, 180/SEG])
    groove = revolve(bead_prof.offset(c.SNAP_CLR, m3.JoinType.Miter))
    plug_xy = bore_xy.offset(-c.FIT_CLR, Round)
    bead = revolve(bead_prof) - prism(plug_xy.offset(-0.2, Round), zb - bh, zb + bh)
    skirt_front = zb - bh/2 - 0.4

    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())

    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    case = chamfered(outline, -c.LIP_T, FLOOR, c.CHAMFER, 0.0)
    case -= prism(bore_xy, 0.0, FLOOR + 1)
    case -= window.translate([0, 0, -c.LIP_T - 0.01])
    case -= groove
    case -= all_keep

    bay_y0, bay_y1 = c.BATT_Y - c.BATT_L/2 - c.BAY_CLR, c.BATT_Y + c.BATT_L/2 + c.BAY_CLR
    bay_xy = rect(-c.BATT_W/2 - c.BAY_CLR, c.BATT_W/2 + c.BAY_CLR, bay_y0, bay_y1) + \
             rect(c.LEAD_X - c.LEAD_W/2, c.LEAD_X + c.LEAD_W/2, bay_y1 - 1, bay_y1 + c.LEAD_L)
    bay_back = FLOOR + c.BATT_T + c.BAY_CLR
    Z_BACK = bay_back + c.BACK_T

    hdrs = [f for f in feats if f.name.startswith("header")]
    # solid blocks; the header keep-outs carve the pockets, so pocket and clearance are one solid
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, m3.JoinType.Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    back = chamfered(outline, FLOOR, Z_BACK, 0.0, c.CHAMFER)
    back += prism(plug_xy - plug_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead
    back -= prism(bay_xy, skirt_front - 1, bay_back)  # the battery goes in from the front, past the skirt
    back += guides
    back -= all_keep
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_cyl = m3.Manifold.cylinder(FLOOR + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([sw[c.BUTTON], b.sw_y, tip_z])
    post = post_cyl - union(k for n, k in keep.items() if not n.startswith(c.BUTTON))
    back += post

    battery = prism(rect(-c.BATT_W/2, c.BATT_W/2, c.BATT_Y - c.BATT_L/2, c.BATT_Y + c.BATT_L/2),
                    bay_back - c.BATT_T, bay_back)
    geo = dict(R_BORE=R_BORE, R_OUT=R_OUT, FLOOR=FLOOR, Z_BACK=Z_BACK, bay_back=bay_back, zb=zb, bh=bh, p=p,
               bore_xy=bore_xy, outline_xy=circle(R_OUT) + pendant, bay_xy=bay_xy, hdrs=hdrs, sw=sw,
               skirt_front=skirt_front, tip_z=tip_z, post_cyl=post_cyl, pend_hw=pend_hw, groove_r=r_s + p + c.SNAP_CLR)
    return feats, case, back, battery, geo


# ---- checks ----------------------------------------------------------------
FAILS = []


def check(ok, label, margin):
    print(f"  [{'ok' if ok else 'FAIL'}] {label:60s} {margin}")
    if not ok: FAILS.append(label)


def run_checks(b, c, feats, case, back, battery, geo):
    static = {"case": case, "back": back, "battery": battery}
    target = f"{c.BUTTON} actuator"

    print(f"\n1. At rest: no badge feature overlaps the case, back or battery (min gap, mm)")
    for f in feats:
        s = f.solid()
        vol = sum((s ^ m).volume() for m in static.values())
        gaps = {k: s.min_gap(m, 3.0) for k, m in static.items()}
        k = min(gaps, key=gaps.get)
        note = "  (glass resting on the lip)" if f.name == "disc + tab" else \
               f"  (= REST_CLR {c.REST_CLR})" if f.name == target else ""
        check(vol < 1e-3, f"{f.name:18s} overlap {vol:.4f} mm^3", f"gap {gaps[k]:.2f} to {k}{note}")
    gap_b = battery.min_gap(union(f.solid() for f in feats), 5.0)
    check(gap_b >= c.STROKE, f"battery clear of the badge by >= stroke {c.STROKE:.2f}", f"gap {gap_b:.2f}")

    print(f"\n2a. Axial room from rest before each feature touches anything: the switch must be first")
    def overlaps(f, dz): return sum((f.solid(dz) ^ m).volume() for m in static.values()) > 1e-4
    room = {}
    for f in feats:
        lo, hi = 0.0, 2.0
        if not overlaps(f, hi): room[f.name] = math.inf; continue
        while hi - lo > 0.005:
            mid = (lo + hi)/2
            lo, hi = (mid, hi) if not overlaps(f, mid) else (lo, mid)
        room[f.name] = lo
    for n, r in room.items():
        if n == target:
            check(abs(r - c.REST_CLR) < 0.02, f"{n:18s} meets the post after REST_CLR", f"{r:.2f}")
        else:
            check(r > c.STROKE + 0.1, f"{n:18s} room > stroke {c.STROKE:.2f} + 0.1",
                  f"{r:.2f} (margin {r - c.STROKE:.2f} past full click)" if r < math.inf else "nothing behind it")

    print(f"\n2b. Pressed {c.STROKE:.2f} (REST_CLR + SW_TRAVEL): {target} on the post is the ONLY contact")
    for f in feats:
        s = f.solid(c.STROKE)
        vol = sum((s ^ m).volume() for m in static.values())
        if f.name == target:
            check(vol > 1e-3, f"{f.name:18s} pressed into the post {vol:.3f} mm^3",
                  f"= {c.SW_TRAVEL} travel x actuator area {math.pi*(b.sw_cap_d/2)**2*c.SW_TRAVEL:.3f}")
            continue
        gaps = {k: s.min_gap(m, 3.0) for k, m in static.items()}
        k = min(gaps, key=gaps.get)
        check(vol < 1e-3 and gaps[k] > 0.05, f"{f.name:18s} still clear", f"gap {gaps[k]:.2f} to {k}")

    print(f"\n3. Header guides engage the headers at rest (>= {c.MIN_ENGAGE}), deepest reach per wall")
    i, o = c.HDR_CLR, c.HDR_CLR + c.GUIDE_WALL
    for h in geo["hdrs"]:
        x0, y0, x1, y1 = h.outline.bounds()
        walls = {"-x wall": rect(x0 - o, x0 - i, y0 - i, y1 + i), "+x wall": rect(x1 + i, x1 + o, y0 - i, y1 + i),
                 "tab-end wall": rect(x0 - i, x1 + i, y1 + i, y1 + o), "switch-end wall": rect(x0 - i, x1 + i, y0 - o, y0 - i)}
        for wn, w in walls.items():
            g = back ^ prism(w, -5, geo["FLOOR"])
            eng = b.hdr_top_z - bbox(g)[0, 2] if not g.is_empty() else 0.0
            check(eng >= c.MIN_ENGAGE, f"{h.name} {wn}", f"engages {eng:.2f}")

    print("\n4. Bezel lip")
    probe = m3.Manifold.cylinder(c.LIP_T + 2, (b.active_d + 1)/2, (b.active_d + 1)/2, SEG).translate([0, 0, -c.LIP_T - 1])
    win_d = 2*(b.r - c.LIP_OVERLAP)
    check((probe ^ case).volume() < 1e-4, f"window clears active display {b.active_d:.2f} + 1",
          f"window {win_d:.2f}, margin {win_d - b.active_d - 1:.2f}")
    ring = prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0)
    check((ring ^ case).volume() > 0.5, "lip overlaps the glass edge (retains it)", f"{c.LIP_OVERLAP:.2f} per side")

    print("\n5. Snap, walls, meshes")
    check((case ^ back).volume() < 1e-3, "case and back do not overlap when assembled", f"{(case ^ back).volume():.4f} mm^3")
    snap = (case ^ back.translate([0, 0, geo["bh"]])).volume()
    check(snap > 1.0, "back pulled out one bead height interferes (it snaps)", f"{snap:.1f} mm^3 interference, SNAP_INT {c.SNAP_INT}")
    path = prism(rect(-c.BATT_W/2, c.BATT_W/2, c.BATT_Y - c.BATT_L/2, c.BATT_Y + c.BATT_L/2), geo["skirt_front"] - 3, geo["bay_back"])
    check((path ^ back).volume() < 1e-3, "battery drops into its bay past the guides and skirt",
          f"between guides {2*(b.hdr_span/2 - b.hdr_w - c.HDR_CLR - c.GUIDE_WALL):.2f} vs width {c.BATT_W}")
    outer = geo["outline_xy"]
    for nm, cav in (("bore + tab slot", geo["bore_xy"]), ("battery bay", geo["bay_xy"])):
        spill = (cav.offset(c.MIN_WALL, Round) - outer).area()
        check(spill < 1e-3, f"wall around {nm} >= {c.MIN_WALL}", f"spill {spill:.4f} mm^2")
    walls = {"case wall behind the snap groove": geo["R_OUT"] - geo["groove_r"],
             "pendant arms beside the plug window": geo["pend_hw"] - c.PLUG_W/2 - c.PLUG_CLR,
             "bezel lip": c.LIP_T, "back wall behind the battery": c.BACK_T,
             "guide walls": c.GUIDE_WALL, "skirt": c.SKIRT_WALL}
    for nm, t in walls.items():
        check(t >= c.MIN_WALL, f"{nm} >= {c.MIN_WALL}", f"{t:.2f}")
    check(c.BOSS_TOP + c.RAD_CLR < c.PLUG_L, "plug's straight overmold reaches the port through the pendant",
          f"wall {c.BOSS_TOP + c.RAD_CLR:.2f} < {c.PLUG_L}")


# ---- output ----------------------------------------------------------------
def export(m, path, print_xform):
    m = print_xform(m)
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    tm.export(path)
    check(tm.is_watertight and tm.volume > 0, f"{path} watertight", f"{m.volume()/1000:.2f} cm^3, {len(tm.faces)} tris")


def renders(b, c, feats, case, back, battery, geo):
    # badge +y -> up, badge +z (backward) -> away from a viewer at azim 90. Refined to short edges because
    # the painter's sort misorders the long sliver triangles of big flat faces.
    D = lambda m: m.rotate([90, 0, 0]).refine_to_length(1.0)
    brass, back_c, dark, blue, white, red, steel, green, violet = ((0.82, 0.66, 0.32), (0.66, 0.50, 0.24), (0.10, 0.10, 0.11),
        (0.15, 0.48, 0.90), (0.95, 0.95, 0.90), (0.90, 0.25, 0.20), (0.55, 0.62, 0.72), (0.25, 0.70, 0.35), (0.62, 0.30, 0.80))
    post = back ^ geo["post_cyl"]
    back_np = back - geo["post_cyl"]
    fs = {f.name: f.solid() for f in feats}
    colour = lambda n: red if n.startswith("plug") else dark if n == "disc + tab" else \
        green if n.startswith(c.BUTTON) else white
    out = "pocketwatch/renders/"

    E = 14.0
    ex = [(case, brass), (back.translate([0, 0, 3*E]), back_c), (battery.translate([0, 0, 2*E]), steel)]
    ex += [(s.translate([0, 0, E] if not n.startswith("plug") else [0, 12, E]), colour(n)) for n, s in fs.items()]
    render([(D(m), col) for m, col in ex], out + "exploded.png", elev=16, azim=-58,
           title="Pocketwatch, exploded from the back: case, badge (+ plug, red), battery, back")

    def section(dz, path, title, box=None):
        parts = [(case, brass), (back_np, back_c), (post, violet), (battery, steel)] + [(s.translate([0, 0, dz]), colour(n)) for n, s in fs.items()]
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
            f"{c.BUTTON} detail, at rest: switch (green) {c.REST_CLR} short of the post (violet); PCB black, glass left", box)
    section(c.STROKE, out + "section-post-detail-pressed.png",
            f"{c.BUTTON} detail, pressed {c.STROKE:.2f}: actuator on the post (click), glass {c.STROKE:.2f} off the lip", box)

    inside = [(back_np, back_c), (post, violet), (battery, steel)] + [(fs[n], colour(n)) for n in fs if n not in ("disc + tab", "USB-C receptacle", "plug overmold")]
    render([(D(m), col) for m, col in inside], out + "back-inside-with-parts.png", elev=28, azim=118,
           title="Back, inside face: headers (white) in their guides, battery bay, post under the switch (green)")
    render([(D(back), back_c), (D(battery), steel)], out + "back-inside.png", elev=30, azim=118,
           title="Back, inside face: header guides either side, battery between them, lead notch at its top end")
    render([(D(case), brass), (D(fs["disc + tab"]), dark),
            (D(prism(circle(b.active_d/2), -0.3, 0.0)), blue), (D(fs["plug overmold"]), red)],
           out + "front.png", elev=12, azim=70, title="Front: bezel lip over the glass edge, plug in the pendant as the crown")


def main():
    b, c = Badge(), Case()
    print("PLACEHOLDERS still in use (replace with measurements):")
    for t in (b, c):
        for f in fields(t):
            if "placeholder" in f.metadata:
                print(f"  {type(t).__name__}.{f.name:12s} = {getattr(t, f.name):7.2f}   <- {f.metadata['placeholder']}")

    feats, case, back, battery, geo = build(b, c)
    asm = bbox(case + back)
    size = asm[1] - asm[0]
    print(f"\nTip at y={b.tip_y:.3f}; active display Ø{b.active_d:.2f}; bore Ø{2*geo['R_BORE']:.2f}; "
          f"case Ø{2*geo['R_OUT']:.2f}, {size[1]:.1f} tall with the pendant, {size[2]:.2f} thick "
          f"(lip -{c.LIP_T} .. back {geo['Z_BACK']:.2f})")
    run_checks(b, c, feats, case, back, battery, geo)
    print()
    export(case, "stl/pocketwatch/Pocketwatch - case.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(back, "stl/pocketwatch/Pocketwatch - back.stl", lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["Z_BACK"]]))
    if "--no-render" not in sys.argv:
        renders(b, c, feats, case, back, battery, geo)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
