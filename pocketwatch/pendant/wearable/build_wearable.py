#!/usr/bin/env python3
"""
Wearable pendants for the 1.28 badge: thin bezel, a bail at 12 o'clock for a cord, and a small cell. Two variants, each
three printed parts (case, plate, lid), all PLA, no supports.

  150  EEMB LP401730, 150 mAh, from EEMB's drawing: 4.3 x 17.5 x 32.0 (H x W x L), Molex 51021-0200 plug (MX1.25).
       Built on the battery pendant (pocketwatch/pendant/battery/): BOOT is the flap lever in the lid, a pole beside
       the cell. The short cell sits inside the badge's own circle, so the case is barely bigger than the badge.
  500  503035, 500 mAh (KBT / CaoDuRen listings with the 1.25 plug). Sized from the cell code with EEMB's margins:
       5.3 x 30.5 x 37.0. Measure one. A 30 mm wide cell covers BOOT at any turn, so no lever can reach past it:
       built on the v2 pocketwatch instead, where pressing the screen clicks BOOT on the plate's post.

Both get, over their base design:
  bezel   lip LIP_T thinner (0.9, three 0.3 layers), LIP_OVERLAP 0.7 (a wider window), a wider outer chamfer.
  bail    two ears either side of the plug at 12 o'clock and one cord hole through both along x. The cord crosses
          over the port behind the plug, so a charging cable still plugs in with the cord on. 45 deg ramps under the
          ears and a teardrop hole: prints bezel down, no supports.

Every check of the base design runs on these numbers; the few that encode the base's own cell are waived below with
the reason, and replaced where the idea still needs checking. Run from the repo root with ~/.venvs/cad/bin/python.
--no-render for a fast check run, --only 150 or --only 500 for one variant.
"""
import sys, math
sys.path[:0] = ["pocketwatch", "pocketwatch/pendant", "pocketwatch/pendant/kids-case", "pocketwatch/pendant/battery"]
from dataclasses import dataclass, replace
import numpy as np, manifold3d as m3
import build_pocketwatch as V2
import build_pocketwatch_usb as U
import build_battery_pendant as BP
from build_pocketwatch import Badge, Case, rect, prism, bbox, check, FAILS, export
from build_pendant import Pendant, MAT

ROOT_OUT = "pocketwatch/pendant/wearable/renders/"
ROOT_STL = "stl/pocketwatch/pendant/wearable/"
OUT = ROOT_OUT


@dataclass(frozen=True)
class Cell:
    """The cell's envelope (not its nominal code): T thick, W across, L along the USB axis, protection board included."""
    NAME: str
    T: float
    W: float
    L: float


EEMB_401730 = Cell("EEMB LP401730 150 mAh", 4.3, 17.5, 32.0)       # EEMB's drawing
CELL_503035 = Cell("503035 500 mAh (assumed envelope)", 5.3, 30.5, 37.0)   # code + EEMB's margins: +0.3, +0.5, +2.0


@dataclass(frozen=True)
class Slim:
    """What makes it thinner than the battery pendant."""
    LIP_T: float = 0.9          # bezel lip, front to back: three 0.3 layers (battery pendant: 1.2)
    LIP_OVERLAP: float = 0.7    # lip over the glass edge (v2: 1.0): a wider window, a narrower ring
    CHAMFER: float = 1.2        # outer front and back edges (v2: 0.8): reads as a thinner ring
    FRONT_WALL: float = 1.8     # the front face stops this far outside the bore, then the case widens at 45 deg to its
                                # full size: a cell bigger than the badge no longer shows as a wide flat ring


@dataclass(frozen=True)
class Bail:
    """Two ears either side of the plug notch at 12 o'clock, one cord hole through both along x. The cord crosses over
    the port behind the notch's roof, so a charging cable's overmold still seats on the port with the cord on."""
    HOLE: float = 2.6           # cord hole: a 2 mm cord with room to thread it
    WALL: float = 1.6           # plastic round the hole
    EAR_W: float = 3.6          # each ear, along x
    EAR_GAP: float = 0.5        # ear to the plug notch's side, along x
    BACK_IN: float = 0.6        # the ears stop this far in front of the case's back face (the back chamfer)
    CORD: float = 2.0           # the cord the hole is sized for
    CORD_CLR: float = 0.3       # cord over the case's 12 o'clock rim, between the ears


def case_table(cell: Cell, s: Slim):
    """LID_T 1.6 (v2: 2.0): the flap is thinned to 1.2 from the cell side either way. The plate stays 2.4: it carries
    the cell lead's channel, and the 150's hood over the plug needs the depth."""
    return replace(Case(), BATT_T=cell.T, BATT_W=cell.W, BATT_L=cell.L, LIP_T=s.LIP_T, LIP_OVERLAP=s.LIP_OVERLAP,
                   CHAMFER=s.CHAMFER, LID_T=1.6)


def battery_table(cell: Cell):
    """The battery pendant's flap and ribs, scaled to the short cell: the key rib starts the same 5.3 short of the
    cell's corner, and a narrower flap keeps the switch force on the stop under the limit on the shorter lever."""
    return replace(BP.Battery(), KEY_X=cell.L/2 - 5.3, F_W=5.5)


def teardrop(r, seg=48):
    """A circle with a 45 deg peak on top (+z): its roof prints without a bridge."""
    pts = [(r*math.cos(a), r*math.sin(a)) for a in np.linspace(math.radians(135), math.radians(405), seg)]
    return m3.CrossSection([pts + [(0.0, r*math.sqrt(2))]])


def yz_solid(cs, x0, x1):
    """Extrude an outline drawn in (y, z) along x from x0 to x1."""
    return m3.Manifold.extrude(cs, x1 - x0).transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], float))


def bail(c: Case, bl: Bail, D):
    """The two ears and the hole through them. Each ear is a block in (y, z) from inside the wall up past the rim, its
    underside a 45 deg ramp down to the wall, so it prints bezel down with no supports. Returns the ears (not yet cut
    to the case's inside), the hole, and the hole's centre and ears' extent."""
    R, z_top = D["R_OUT"], D["Z_CASE"] - bl.BACK_IN
    r = bl.HOLE/2
    y_h = R + bl.CORD/2 + bl.CORD_CLR + (r - bl.CORD/2)     # the cord's underside CORD_CLR over the rim at x = 0
    z_h = z_top - bl.WALL - r*math.sqrt(2)                   # teardrop peak WALL under the ears' back face
    y_out = y_h + r + bl.WALL
    x0 = D["hw"] + bl.EAR_GAP
    x1 = x0 + bl.EAR_W
    y_in = math.sqrt(R**2 - x1**2) - c.CASE_WALL             # inside the wall at the ear's outer x
    z_lo = z_h - r - bl.WALL
    z_root = z_lo - (y_out - y_in)
    prof = m3.CrossSection([[(y_in, z_root), (y_out, z_lo), (y_out, z_top), (y_in, z_top)]])
    ears = yz_solid(prof, x0, x1) + yz_solid(prof, -x1, -x0)
    hole = yz_solid(teardrop(r).translate([y_h, z_h]), -x1 - 1, x1 + 1)
    return ears, hole, dict(y_h=y_h, z_h=z_h, y_out=y_out, z_root=z_root, x0=x0, x1=x1)


def add_bail(c, bl, D, case):
    ears, hole, at = bail(c, bl, D)
    # the ears reach into the wall only (out past the lid's groove), never the chamber, bore, groove or notch
    hollow = m3.CrossSection.circle(D["geo"]["groove_r_l"] + 0.1, V2.SEG) + D["feats"][0].grown().offset(0.3, m3.JoinType.Miter, 4.0)
    solid = ears - prism(hollow, -c.LIP_T - 1, D["Z_CASE"] + 1) - D["notch"] - V2.union(k.keepout(c.FLOAT) for k in D["feats"])
    D.update(bail=solid, bail_hole=hole, bail_at=at)
    return (case + solid) - hole


def front_taper(c, s, D, case):
    """Keep only what is inside a 45 deg cone from FRONT_WALL outside the bore (and the USB tab's pocket) at the front
    face. Grows outward toward the back, so it prints bezel down with no supports."""
    out = D["feats"][0].grown().hull().offset(s.FRONT_WALL, m3.JoinType.Round)
    z0 = -c.LIP_T
    keep = m3.Manifold.batch_hull([prism(out, z0 - 0.01, z0), prism(out.offset(80, m3.JoinType.Round), z0 + 80, z0 + 80.01)])
    D["front_r"] = s.FRONT_WALL + D["geo"]["R_BORE"]
    return case ^ keep


def build_150(b, c, p, bt, bl, s):
    D = BP.design(b, c, p, bt)
    case = front_taper(c, s, D, add_bail(c, bl, D, BP.build_case(b, c, p, bt, D)))
    plate = BP.build_plate(b, c, D, c.FIT_CLR)
    lid, L = BP.build_lid(b, c, D, c.FIT_CLR)
    D.update(**L)
    return D, case, plate, lid


def build_500(b, c, p, bt, bl, s):
    """v2 as it is: the plug's shell slot through the wall at 12 o'clock, the overmold seated on the case's outside."""
    feats, case, plate, lid, cell, geo = V2.build(b, c)
    D = dict(feats=feats, geo=geo, cell=cell, R_OUT=geo["R_OUT"], R_REAR=geo["R_REAR"], Z_CASE=geo["Z_CASE"],
             FLOOR=geo["FLOOR"], lid_z0=geo["lid_z0"], y_flat=geo["R_OUT"], hw=bt.OM_W/2 + p.PORT_OUT, notch=m3.Manifold())
    return D, front_taper(c, s, D, add_bail(c, bl, D, case)), plate, lid


def bail_checks(b, c, p, bt, bl, D, case):
    A = D["bail_at"]
    r = bl.HOLE/2
    print(f"\n13. The bail: two ears at 12 o'clock, x {A['x0']:.1f} to {A['x1']:.1f} each side, one Ø{bl.HOLE:g} cord hole along x")
    om = prism(rect(-bt.OM_W/2, bt.OM_W/2, D["y_flat"], D["R_OUT"] + 30), b.port_z - bt.OM_T/2, b.port_z + bt.OM_T/2)
    g = om.min_gap(D["bail"], 5.0)
    check(g >= p.PORT_OUT, f"a {bt.OM_W:g} x {bt.OM_T:g} overmold on the pushed-down port clears the ears", f"gap {g:.2f}")
    cord = yz_solid(m3.CrossSection.circle(bl.CORD/2, 32).translate([A["y_h"], A["z_h"]]), -A["x1"] - 3, A["x1"] + 3)
    g = cord.min_gap(case, 3.0)
    check((cord ^ case).volume() < 1e-3 and g >= bl.CORD_CLR - 0.01, f"a {bl.CORD:g} mm cord runs straight through both ears and over the rim",
          f"gap {g:.2f}")
    g = cord.min_gap(om, 5.0)
    check(g >= p.PORT_OUT, "with the cord on, the overmold still seats (the cord passes behind it)", f"gap {g:.2f}")
    check(len(case.decompose()) == 1, "the ears are one piece with the case", f"{len(case.decompose())} body")
    for nm, t in (("plastic outside the hole", bl.WALL), ("plastic under the hole", bl.WALL)):
        check(t >= c.MIN_WALL, f"{nm} >= {c.MIN_WALL}", f"{t:.2f}")
    # hung from the cord, the pendant pulls each ear's outer ligament along y: in the layers' plane as printed
    F = 20.0
    stress = F/(2*bl.EAR_W*bl.WALL)
    check(stress <= MAT.STRENGTH/4, f"a {F:g} N tug: ligaments in the layers' plane under a quarter of {MAT.STRENGTH:g} MPa",
          f"{stress:.2f} MPa")


def seat_check(c, D, case, plate):
    """The battery pendant's seat probe stands 0.5 in from both edges of a seat its big cell made wide. Here the bore
    sets the chamber and the seat is STEP wide, so probe 0.2 in."""
    from build_pocketwatch import circle
    step = circle(D["R_REAR"] - 0.2) - D["geo"]["bore_xy"].offset(0.5, m3.JoinType.Miter, 4.0)   # past the snap bead
    z_pf = bbox(plate ^ prism(step, -5, 50))[0, 2]
    check(abs(z_pf - D["FLOOR"]) < 1e-3 and (plate.translate([0, 0, -0.05]) ^ case).volume() > 1e-2,
          f"plate sits flush on the {c.STEP:g} wide seat", f"front face z {z_pf:.2f}")


def slit_check(c, D, lid):
    """The kids-case probe samples every 0.1 from the lid's edge; one sample lands on the flap tip's square cut and
    reads half a strip. Probe on two grids shifted off that line."""
    import build_kids_case as K
    face = D["F"].l(lid.slice(D["z_back"] - 0.15))
    t = min(K.thinnest_beside_slits(face, D["f"], D["yc"], c.MIN_WALL, -D["r_lid"] + off) for off in (0.03, 0.05))
    check(t >= c.MIN_WALL - 0.02, f"lid and flap beside each slit >= {c.MIN_WALL} wide (shifted grids)", f"{t:.2f}")


def com_hang(D, case, plate, lid):
    """The hung pendant's centre of mass sits under the cord: how far the face tips down from vertical."""
    mass, mom = 0.0, np.zeros(3)
    for m, rho in ((case, MAT.RHO), (plate, MAT.RHO), (lid, MAT.RHO), (D["cell"], 2.3e-3)):   # LiPo ~2.3 g/cm^3
        mesh = m.to_mesh()
        v = np.asarray(mesh.vert_properties)[:, :3]
        t = v[np.asarray(mesh.tri_verts)]
        vol6 = np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2]))
        mass += rho*vol6.sum()/6
        mom += rho*(vol6[:, None]*t.sum(1)/4).sum(0)/6
    com = mom/mass
    A = D["bail_at"]
    return mass, com, math.degrees(math.atan2(A["z_h"] - com[2], A["y_h"] - com[1]))


def wearable_renders(b, c, bl, D, case, plate, lid, tag):
    from build_pocketwatch import render
    Dv = lambda m: m.rotate([90, 0, 0]).refine_to_length(1.0)
    shell, back_c, lid_c, dark, cord_c, steel = ((0.25, 0.47, 0.62), (0.62, 0.52, 0.30), (0.74, 0.58, 0.28),
                                                (0.08, 0.08, 0.09), (0.85, 0.20, 0.20), (0.55, 0.62, 0.72))
    A = D["bail_at"]
    cord = yz_solid(m3.CrossSection.circle(bl.CORD/2, 24).translate([A["y_h"], A["z_h"]]), -A["x1"] - 8, A["x1"] + 8)
    disc = D["feats"][0].solid()
    parts = [(case, shell), (plate, back_c), (lid, lid_c), (disc, dark), (cord, cord_c)]
    render([(Dv(m), col) for m, col in parts], OUT + "front.png", elev=8, azim=90, zoom=1.2,
           title=f"{tag} front: Ø{2*D['R_OUT']:.1f}, flat ring {min(D['R_OUT'], D['front_r']) - (b.r - c.LIP_OVERLAP):.1f} round the screen, cord (red) through the ears")
    render([(Dv(m), col) for m, col in parts], OUT + "three-quarter.png", elev=22, azim=40, zoom=1.2,
           title=f"{tag}: the ears stand behind the plug notch, so a cable still plugs in with the cord on")
    side = [(m.trim_by_plane([1, 0, 0], 0.0), col) for m, col in parts[:3] + [(D["cell"], steel), (disc, dark)]] + [(cord, cord_c)]
    asm = bbox(case + plate + lid)
    render([(Dv(m), col) for m, col in side if not m.is_empty()], OUT + "side-section.png", elev=0, azim=180, zoom=1.2,
           title=f"{tag}: section on the centre line, glass to the left: {asm[1, 2] - asm[0, 2]:.1f} thick, cell {c.BATT_T:g}")
    E = 14.0
    ex = [(case, shell), (disc.translate([0, 0, E]), dark), (plate.translate([0, 0, 2*E]), back_c),
          (D["cell"].translate([0, 0, 3*E]), steel), (lid.translate([0, 0, 4*E]), lid_c)]
    render([(Dv(m), col) for m, col in ex], OUT + "exploded.png", elev=16, azim=-58, figsize=(9, 11),
           title=f"{tag}, exploded from the back: case, badge, plate, cell, lid")


# Base-design checks that encode the base's own cell, not the idea. Each is replaced by what holds here.
WAIVE_150 = {
    "chamber = the cell's half-diagonal": "the short cell is inside the badge's own circle, so the bore sets the chamber",
    "the cell runs into a rib": "the 32 mm cell turns BAY_CLR / 16 = 1.07 deg before a rib stops it (the 42.65 cell: 0.8)",
    "the lid runs into the key rib": "the key rib is shorter with the cell; the lid still only fits one way (notch)",
    "plate sits flush on the step": "its probe needs a seat over 1.0 wide; seat_check probes this one",
    "bezel lip >= 1.2": "the thin bezel: three 0.3 layers. It only holds the glass in; BOOT is the flap's, not a press on the screen",
    "lid beside each slit": "a sample on the flap tip's square cut reads half a strip; slit_check probes off that line",
    "the lead stays clear of the lid": "a 4.3 cell leaves the 1.0 thick lead 2.4 under the lid, not 3; still nothing pinches it",
}
WAIVE_500 = {
    "bezel lip >= 1.2": "the thin bezel: three 0.3 layers. A press on the screen slides the badge back onto the post, "
                        "away from the lip, so the lip only holds the glass in",
}


def waive(table, label):
    print(f"\nWaived ({label}):")
    for key, why in table.items():
        hit = [f for f in FAILS if key in f]
        for f in hit:
            FAILS.remove(f)
        print(f"  [{'waived' if hit else 'passes'}] {key}: {why}")


def summary(tag, cell, b, c, D, case, plate, lid, extra):
    asm = bbox(case + plate + lid)
    mass, com, tilt = com_hang(D, case, plate, lid)
    A = D["bail_at"]
    print(f"\n==== Wearable {tag}, {cell.NAME}: Ø{2*D['R_OUT']:.2f} x {asm[1, 2] - asm[0, 2]:.2f} thick; ears {A['y_out'] - D['R_OUT']:.1f} "
          f"past the rim at 12; flat ring round the screen {min(D['R_OUT'], D['front_r']) - (b.r - c.LIP_OVERLAP):.2f} wide (case edge {D['R_OUT'] - (b.r - c.LIP_OVERLAP):.2f}), lip {c.LIP_T:g} thick; "
          f"{extra}~{mass:.1f} g with the cell; hung, the face tips {tilt:.0f} deg down")


def variant_150(b, p, bl, s, render_on):
    global OUT
    tag, cell = "150 mAh", EEMB_401730
    c, bt = case_table(cell, s), battery_table(cell)
    OUT, stl = ROOT_OUT + "150mAh/", ROOT_STL + "150mAh/"
    D, case, plate, lid = build_150(b, c, p, bt, bl, s)
    plate_r = BP.build_plate(b, c, D, U.PLATE_DISC_CLR_ROOMY)
    lid_r, _ = BP.build_lid(b, c, D, BP.LID_CLR_ROOMY)
    m = D["cs"]["nom"]["m"]
    summary(tag, cell, b, c, D, case, plate, lid, f"BOOT: the lid's flap, {m['P_click']:.2f} N at its outer end; cell turned {D['tilt']:.2f} deg; ")
    V2.run_checks(b, c, D["feats"], case, plate, lid, D["cell"], D["geo"], recess=False)
    BP.run_battery_checks(b, c, p, bt, D, case, plate, lid, lid_r, plate_r)
    bail_checks(b, c, p, bt, bl, D, case)
    seat_check(c, D, case, plate)
    slit_check(c, D, lid)
    waive(WAIVE_150, "the battery pendant's numbers, not this one's")
    print()
    flip = lambda z: (lambda m_: m_.rotate([0, 180, 0]).translate([0, 0, z]))
    nm = f"{stl}Wearable {tag} - "
    export(case, nm + "case.stl", lambda m_: m_.translate([0, 0, c.LIP_T]))
    export(plate, nm + "plate.stl", flip(D["FLOOR"] + c.PLATE_T))
    export(plate_r, nm + "plate (roomy).stl", flip(D["FLOOR"] + c.PLATE_T))
    export(lid, nm + "lid (flap).stl", flip(D["z_back"]))
    export(lid_r, nm + "lid (flap, roomy).stl", flip(D["z_back"]))
    if render_on:
        BP.OUT = OUT
        BP.renders(b, c, p, bt, D, case, plate, lid)
        wearable_renders(b, c, bl, D, case, plate, lid, tag)


def variant_500(b, p, bl, s, render_on):
    global OUT
    tag, cell = "500 mAh", CELL_503035
    c, bt = case_table(cell, s), BP.Battery()
    OUT, stl = ROOT_OUT + "500mAh/", ROOT_STL + "500mAh/"
    D, case, plate, lid = build_500(b, c, p, bt, bl, s)
    summary(tag, cell, b, c, D, case, plate, lid, "BOOT: press the screen; ")
    V2.run_checks(b, c, D["feats"], case, plate, lid, D["cell"], D["geo"])
    bail_checks(b, c, p, bt, bl, D, case)
    waive(WAIVE_500, "v2's numbers, not this one's")
    print()
    nm = f"{stl}Wearable {tag} - "
    export(case, nm + "case.stl", lambda m_: m_.translate([0, 0, c.LIP_T]))
    export(plate, nm + "plate.stl", lambda m_: m_.rotate([0, 180, 0]).translate([0, 0, D["FLOOR"] + c.PLATE_T]))
    export(lid, nm + "lid.stl", lambda m_: m_.translate([0, 0, -D["lid_z0"]]))
    if render_on:
        wearable_renders(b, c, bl, D, case, plate, lid, tag)


def main():
    import os
    b, p, bl, s = Badge(), Pendant(), Bail(), Slim()
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    render_on = "--no-render" not in sys.argv
    for tag, fn in (("150", variant_150), ("500", variant_500)):
        if only in (None, tag):
            os.makedirs(f"{ROOT_OUT}{tag}mAh", exist_ok=True)
            os.makedirs(f"{ROOT_STL}{tag}mAh", exist_ok=True)
            fn(b, p, bl, s, render_on)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
