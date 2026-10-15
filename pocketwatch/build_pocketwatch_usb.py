#!/usr/bin/env python3
"""
Pocketwatch, USB-powered variant: no battery, so no chamber and no lid. Two parts.

  case   bezel lip, badge bore, a counterbore for the plate that follows the USB-C tab, and
         a slot the size of the plug's metal shell through the wall at 12 o'clock. Ø43.6 x 12.5, with a crown boss at 12 o'clock.
  plate  the back: snaps into the bore, grips the headers in x only, and its
         post clicks BOOT when the screen is pressed. Flush with the case back.

Everything that is not the battery comes from build_pocketwatch.py (Badge, Case,
features, snap), so a change to the badge or the fit applies to both variants.
The case wall wraps the tab in a boss, so the slot is a plain 9.6 x 4.3 hole with a
flat roof, the same as the battery case.

Run with ~/.venvs/cad/bin/python from the repo root.
"""
import sys, math
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)

OUT = "pocketwatch/renders/usb-"
SHELL_LEN, MIN_PLUG_ENGAGE = 6.65, 3.5    # USB-C plug metal shell length; least engagement trusted
BOOT_HOLE_D, PIN_D = 3.4, 2.0   # access hole through the plate over BOOT; the stylus or plunger that goes in it
PLATE_DISC_CLR = 0.18        # plate disc inside the counterbore, per side: the size that printed and fit
PLATE_DISC_CLR_ROOMY = 0.65  # for a print that runs oversize: 0.47 per side smaller, ~1 mm in diameter
TAB_R, TAB_GAP, TAB_L, TAB_T = 2.2, 0.65, 12.0, 1.2   # BOOT button flexure: tab half-width, slot, length to the root, thickness
PETG_E = 1500.0           # MPa, along the layers
PRY_DEG, PRY_W, PRY_DEPTH = 120.0, 5.0, 1.0   # pry notch at 10 o'clock (seen from the front): the plate printed too tight to get off
BACK_CHAMFER = 0.6       # smaller than the front: the back rim is only CASE_WALL thick


def build(b: Badge, c: Case, disc_clr=PLATE_DISC_CLR, button=False):
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    STEP = 1.2                                    # the plate sits in a counterbore this much wider than the bore
    R_REAR = R_BORE + STEP
    R_OUT = R_REAR + c.CASE_WALL
    FLOOR = b.hdr_top_z + c.FLOAT                 # the step = plate's front face
    Z_CASE = FLOOR + c.PLATE_T                    # plate back face = case back face
    bore_xy = feats[0].grown()
    pocket = circle(R_REAR) + bore_xy                             # counterbore: stepped round, straight over the tab
    # the case wall follows the tab too: a crown boss at 12 o'clock, so the plug slot goes through a wall
    boss = (bore_xy.offset(c.CASE_WALL, Round) ^ rect(-40, 40, 10, 40)).hull()

    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())

    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4

    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    case = chamfered([circle(R_OUT), boss], -c.LIP_T, Z_CASE, c.CHAMFER, BACK_CHAMFER)
    case -= prism(bore_xy, 0.0, Z_CASE + 1)             # the tab pocket runs straight through to the back
    case -= prism(circle(R_REAR), FLOOR, Z_CASE + 1)
    case -= window.translate([0, 0, -c.LIP_T - 0.01])
    case -= groove_p
    case -= pry_cut(R_BORE, R_OUT, FLOOR, Z_CASE, PRY_DEG)
    case -= all_keep
    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, m3.JoinType.Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    px, py = sw[c.BUTTON], b.sw_y
    if button:
        # a flexure: the BOOT post rides on a thin tab, cut free by a U-slot. Pushing the plate behind the post clicks BOOT.
        tab = rect(px, px + TAB_L, py - TAB_R, py + TAB_R) + circle(TAB_R).translate([px, py])
        zone = tab.offset(TAB_GAP, Round)
        slot = (zone - tab) ^ rect(-60, px + TAB_L, -60, 60)             # open at the root end
        guides = guides - prism(tab.offset(TAB_GAP + 0.05, Round), -1, FLOOR + 1)                    # the header guides stay off the tab
    disc = prism(pocket.offset(-disc_clr, Round), FLOOR, Z_CASE)   # also keeps the disc off the skirt face
    if button:
        disc -= prism(slot, FLOOR - 1, Z_CASE + 1)                        # the U-slot, clear through
        disc -= prism(tab, FLOOR - 1, FLOOR + TAB_T)                       # thin the tab from the front: the bed side stays flat
    plate = disc
    ring = prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01)
    if button:
        ring -= prism(slot, FLOOR, FLOOR + 1)                             # no 0.01 fin of skirt hanging over the slot
    plate += ring + bead_p
    plate += guides
    plate -= all_keep
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_top = FLOOR + (TAB_T if button else 0.0) + 0.01
    post_cyl = m3.Manifold.cylinder(post_top - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([px, py, tip_z])
    plate += post_cyl - union(k for n, k in keep.items() if not n.startswith(c.BUTTON))

    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_OUT, FLOOR=FLOOR, Z_CASE=Z_CASE, bh_p=bh_p,
               groove_r_p=groove_r_p, hdrs=hdrs, sw=sw, post_cyl=post_cyl, R_DISC=R_REAR - disc_clr)
    if button:
        geo.update(tab=tab, slot=slot)
    return feats, case, plate, geo


def pry_cut(R_BORE, R_OUT, FLOOR, z_back, deg):
    """Pry notch: a slot through the back rim at deg, cut PRY_DEPTH under the plate's edge, so a screwdriver or
    coin can lever a tight plate out without loosening the snap."""
    return prism(rect(R_BORE + 0.3, R_OUT + 1.0, -PRY_W/2, PRY_W/2).rotate(deg), FLOOR - PRY_DEPTH, z_back + 1)


def run_checks(b, c, feats, case, plate, geo, win_margin=0.5):
    static = {"case": case, "plate": plate}
    target = f"{c.BUTTON} actuator"

    print("\n1. At rest: no badge feature overlaps the case or plate (min gap, mm)")
    for f in feats:
        s = f.solid()
        vol = sum((s ^ m).volume() for m in static.values())
        gaps = {k: s.min_gap(m, 3.0) for k, m in static.items()}
        k = min(gaps, key=gaps.get)
        check(vol < 1e-3, f"{f.name:26s} overlap {vol:.4f} mm^3", f"gap {gaps[k]:.2f} to {k}")

    print("\n2a. Axial room before each feature touches anything: the switch must be first")
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
    r_p = b.active_d/2 + win_margin
    probe = m3.Manifold.cylinder(c.LIP_T + 2, r_p, r_p, SEG).translate([0, 0, -c.LIP_T - 1])
    gap = prism(circle(b.active_d/2), -c.LIP_T - 1, 0.0).min_gap(case, 3.0)
    check((probe ^ case).volume() < 1e-4, f"window clears active display {b.active_d:.2f} + {2*win_margin:g}",
          f"clear by {gap:.2f} a side at the closest")
    ring = prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0)
    check((ring ^ case).volume() > 0.5, "lip overlaps the glass edge (retains it)", f"{c.LIP_OVERLAP:.2f} per side")

    print("\n5. Parts, snap, walls, USB-C notch")
    v = (case ^ plate).volume()
    check(v < 1e-3, "case and plate do not overlap", f"{v:.4f} mm^3")
    s = (case ^ plate.translate([0, 0, geo["bh_p"]])).volume()
    check(s > 1.0, "plate pulled back one bead height interferes (it snaps)", f"{s:.1f} mm^3")
    walls = {"case wall behind the plate groove": geo["R_OUT"] - geo["groove_r_p"], "bezel lip": c.LIP_T,
             "case wall at the back rim": c.CASE_WALL - BACK_CHAMFER,
             "step under the plate": geo["R_REAR"] - geo["R_BORE"], "plate": c.PLATE_T,
             "guide walls": c.GUIDE_WALL, "skirt": c.SKIRT_WALL}
    for nm, t in walls.items():
        check(t >= c.MIN_WALL - 1e-9, f"{nm} >= {c.MIN_WALL}", f"{t:.2f}")
    wall = bbox(case)[1, 1] - b.tip_y
    engaged = SHELL_LEN - max(wall, 0)
    check(engaged >= MIN_PLUG_ENGAGE, f"plug shell engages the port >= {MIN_PLUG_ENGAGE} (a guess)",
          f"all {SHELL_LEN}, port sticks out {-wall:.1f}" if wall < 0 else f"{engaged:.1f} of {SHELL_LEN}, {wall:.1f} of case in front of the port")
    back = bbox(case)[1, 2]
    check(abs(back - bbox(plate)[1, 2]) < 1e-3, "plate is flush with the case back", f"z {back:.2f}")


def run_button_checks(b, c, feats, case, plate, geo):
    print("\n7. BOOT button flexure: push the plastic behind the post, the glass is never touched")
    tab, slot = geo["tab"], geo["slot"]
    check((slot - circle(geo["R_DISC"] - c.MIN_WALL)).area() < 1e-6, f"slot stays {c.MIN_WALL} inside the plate edge", "")
    travel = c.REST_CLR + c.SW_TRAVEL
    moved = (plate ^ prism(tab, -2, geo["Z_CASE"] + 2)).translate([0, 0, -travel])
    for f in feats:
        v = (moved ^ f.solid()).volume()
        if f.name == f"{c.BUTTON} actuator":
            check(v > 1e-3, f"tab pushed {travel:.2f}: post reaches the {c.BUTTON} actuator", f"{v:.3f} mm^3")
        else:
            gap = moved.min_gap(f.solid(), 3.0)
            check(v < 1e-3 and gap > 0.05, f"tab pushed {travel:.2f}: {f.name} still clear", f"gap {gap:.2f}")
    t, w = TAB_T, 2*TAB_R
    eps = 3*t*travel/(2*TAB_L**2)
    k = 3*PETG_E*(w*t**3/12)/TAB_L**3
    check(eps <= 0.02, "tab strain <= 2% at full push", f"{eps*100:.2f}% over {TAB_L:g} mm")
    check(t >= c.MIN_WALL, f"tab thickness >= {c.MIN_WALL}", f"{t:g}")
    print(f"      push at the post: {k*travel:.2f} N to flex the tab {travel:.2f} + the switch's own ~2 N (tab {w:g} wide, k {k:.2f} N/mm)")


def boot_hole_plate(b, c, plate, geo):
    """The same plate with the post replaced by a hole straight onto the BOOT actuator, so the
    button is pressed from behind and the glass is never touched."""
    x, y = geo["sw"][c.BUTTON], b.sw_y
    hole = m3.Manifold.cylinder(geo["Z_CASE"] + 1 - (b.pcb_back_z + 1.0), BOOT_HOLE_D/2, BOOT_HOLE_D/2, 64) \
        .translate([x, y, b.pcb_back_z + 1.0])
    return (plate - geo["post_cyl"]) - hole, x, y


def run_hole_checks(b, c, feats, case, plate_h, x, y, geo):
    print("\n6. BOOT access hole: a pin goes in from behind, presses the actuator, touches nothing else")
    top = b.pcb_back_z + b.sw_cap_h                       # actuator top at rest
    pin = lambda dz: m3.Manifold.cylinder(geo["Z_CASE"] + 8 - (top - dz), PIN_D/2, PIN_D/2, 48).translate([x, y, top - dz])
    for dz, label in ((0.0, "at rest"), (c.SW_TRAVEL, f"pressed {c.SW_TRAVEL:.2f}")):
        hit = sum((pin(dz) ^ m).volume() for m in (case, plate_h))
        check(hit < 1e-3, f"{PIN_D:g} mm pin {label} clears the case and plate", f"{hit:.4f} mm^3")
    act = next(f for f in feats if f.name == f"{c.BUTTON} actuator")
    v = (pin(c.SW_TRAVEL) ^ act.solid()).volume()
    check(v > 1e-3, f"pin pressed {c.SW_TRAVEL:.2f} reaches the actuator", f"{v:.3f} mm^3")
    depth = geo["Z_CASE"] - top
    check(depth > 0, "hole depth from the back face to the actuator", f"{depth:.1f} mm")


def renders(b, c, feats, case, plate, geo):
    D = lambda m: m.rotate([90, 0, 0]).refine_to_length(1.0)
    brass, back_c, dark, white, green, violet = ((0.82, 0.66, 0.32), (0.66, 0.50, 0.24), (0.10, 0.10, 0.11),
                                                 (0.95, 0.95, 0.90), (0.25, 0.70, 0.35), (0.62, 0.30, 0.80))
    post = plate ^ geo["post_cyl"]
    plate_np = plate - geo["post_cyl"]
    fs = {f.name: f.solid() for f in feats if not f.name.startswith("plug")}
    colour = lambda n: dark if n == "disc + tab" else green if n.startswith(c.BUTTON) else white
    E = 16.0
    ex = [(case, brass), (plate.translate([0, 0, 2*E]), back_c)] + [(s.translate([0, 0, E]), colour(n)) for n, s in fs.items()]
    render([(D(m), col) for m, col in ex], OUT + "exploded.png", elev=16, azim=-58,
             title="USB-powered pocketwatch, exploded from the back: case, badge, plate")
    x = geo["sw"][c.BUTTON]
    parts = [(case, brass), (plate_np, back_c), (post, violet)] + [(s, colour(n)) for n, s in fs.items()]
    cut = []
    for m, col in parts:
        m = m.trim_by_plane([1, 0, 0], x).refine_to_length(1.0)
        if not m.is_empty(): cut.append((D(m), col))
    render(cut, OUT + "section-post.png", elev=0, azim=180,
             title=f"USB-powered, section through the {c.BUTTON} post (x={x:+.1f}), at rest")
    render([(D(case), brass), (D(fs["disc + tab"]), dark)], OUT + "back.png", elev=-25, azim=-70,
             title="From the back: plate removed, crown boss and USB-C slot at 12 o'clock")


def main():
    b, c = Badge(), Case()
    feats, case, plate, geo = build(b, c)
    asm = bbox(case + plate)
    size = asm[1] - asm[0]
    print(f"Case Ø{2*geo['R_OUT']:.2f} x {size[2]:.2f} thick; bore Ø{2*geo['R_BORE']:.2f}; counterbore Ø{2*geo['R_REAR']:.2f}")
    run_checks(b, c, feats, case, plate, geo)
    print()
    export(case, "stl/pocketwatch/Pocketwatch USB-only - case.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    flip = lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]])
    export(plate, "stl/pocketwatch/Pocketwatch USB-only - plate.stl", flip)
    plate_h, x, y = boot_hole_plate(b, c, plate, geo)
    run_hole_checks(b, c, feats, case, plate_h, x, y, geo)
    export(plate_h, "stl/pocketwatch/Pocketwatch USB-only - plate (BOOT hole).stl", flip)
    _, _, plate_r, geo_r = build(b, c, PLATE_DISC_CLR_ROOMY)
    plate_rh, _, _ = boot_hole_plate(b, c, plate_r, geo_r)
    export(plate_r, "stl/pocketwatch/Pocketwatch USB-only - plate (roomy).stl", flip)
    export(plate_rh, "stl/pocketwatch/Pocketwatch USB-only - plate (BOOT hole, roomy).stl", flip)
    for clr, tag in ((PLATE_DISC_CLR, "button"), (PLATE_DISC_CLR_ROOMY, "button, roomy")):
        _, _, plate_b, geo_b = build(b, c, clr, button=True)
        if clr == PLATE_DISC_CLR:
            run_checks(b, c, feats, case, plate_b, geo_b)
            run_button_checks(b, c, feats, case, plate_b, geo_b)
        export(plate_b, f"stl/pocketwatch/Pocketwatch USB-only - plate ({tag}).stl", flip)
        if clr == PLATE_DISC_CLR:
            plate_btn, geo_btn = plate_b, geo_b
    if "--no-render" not in sys.argv:
        renders(b, c, feats, case, plate, geo)
        D = lambda m: m.rotate([90, 0, 0]).refine_to_length(1.0)
        render([(D(plate_btn - geo_btn["post_cyl"]), (0.66, 0.50, 0.24)), (D(plate_btn ^ geo_btn["post_cyl"]), (0.62, 0.30, 0.80))],
               OUT + "plate-button.png", elev=-28, azim=62, title="Button plate from the badge side: U-slot, thin tab, post (violet)")
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
