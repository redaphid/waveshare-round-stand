#!/usr/bin/env python3
"""
Pocketwatch, USB-powered variant: no battery, so no chamber and no lid. Two parts.

  case   bezel lip, badge bore, a counterbore for the plate, and the USB-C tab pocket
         left open to the back at 12 o'clock for the plug. Ø43.6 x 12.5.
  plate  the back: snaps into the bore, grips the headers in x only, and its
         post clicks BOOT when the screen is pressed. Flush with the case back.

Everything that is not the battery comes from build_pocketwatch.py (Badge, Case,
features, snap), so a change to the badge or the fit applies to both variants.
Because the case is only 12.5 deep the recess roof of the battery case would sit
behind the back face, so the recess is simply open to the back: no bridge at all.

Run with ~/.venvs/cad/bin/python from the repo root.
"""
import sys, math
sys.path.insert(0, "pocketwatch")
import numpy as np, manifold3d as m3
from build_pocketwatch import (Badge, Case, Round, SEG, features, snap, circle, rect, prism, union, chamfered,
                               bbox, check, FAILS, export, render)

OUT = "pocketwatch/renders/usb-"
BACK_CHAMFER = 0.6        # smaller than the front: the back rim is only CASE_WALL thick


def build(b: Badge, c: Case):
    feats, sw = features(b, c)
    R_BORE = b.r + c.RAD_CLR
    R_REAR = R_BORE + 1.2                         # counterbore the plate sits in: a 1.2 step in front of it
    R_OUT = R_REAR + c.CASE_WALL
    FLOOR = b.hdr_top_z + c.FLOAT                 # the step = plate's front face
    Z_CASE = FLOOR + c.PLATE_T                    # plate back face = case back face
    bore_xy = feats[0].grown()

    keep = {f.name: f.keepout(c.FLOAT) for f in feats}
    all_keep = union(keep.values())

    skirt_xy = bore_xy.offset(-c.FIT_CLR, Round)
    zb_p = FLOOR - c.SNAP_LIP - c.SNAP_CLR - (2*(c.FIT_CLR + c.SNAP_INT) + c.BEAD_FLAT)/2
    bead_p, groove_p, bh_p, groove_r_p = snap(c, R_BORE, zb_p)
    bead_p -= prism(skirt_xy.offset(-0.2, Round), zb_p - bh_p, zb_p + bh_p)
    skirt_front = zb_p - bh_p/2 - 0.4

    window = m3.Manifold.cylinder(c.LIP_T + 0.02, b.r - c.LIP_OVERLAP + c.LIP_BEVEL, b.r - c.LIP_OVERLAP, SEG)
    case = chamfered([circle(R_OUT)], -c.LIP_T, Z_CASE, c.CHAMFER, BACK_CHAMFER)
    case -= prism(bore_xy, 0.0, FLOOR + 1)
    case -= prism(circle(R_REAR), FLOOR, Z_CASE + 1)
    case -= window.translate([0, 0, -c.LIP_T - 0.01])
    case -= groove_p
    case -= all_keep
    # The tab pocket is wider than the plug, so cutting it through the back face leaves no roof over
    # the USB-C end: the notch is open to the back and nothing bridges.
    case -= prism(bore_xy, FLOOR, Z_CASE + 1)

    hdrs = [f for f in feats if f.name.startswith("header")]
    guides = union(prism(h.outline.offset(c.HDR_CLR + c.GUIDE_WALL, m3.JoinType.Miter), 0.0, FLOOR + 0.01) for h in hdrs)
    guides = guides ^ prism(skirt_xy.offset(-0.3, Round), 0.0, FLOOR + 0.01)
    plate = prism(circle(R_REAR - c.FIT_CLR), FLOOR, Z_CASE)
    plate += prism(skirt_xy - skirt_xy.offset(-c.SKIRT_WALL, Round), skirt_front, FLOOR + 0.01) + bead_p
    plate += guides
    plate -= all_keep
    # the tab pocket reaches past the plate's round edge: a skirt wall there would hang in the air
    plate ^= prism(circle(R_REAR - c.FIT_CLR), -10, Z_CASE + 1)
    tip_z = b.pcb_back_z + b.sw_cap_h + c.REST_CLR
    post_cyl = m3.Manifold.cylinder(FLOOR + 0.01 - tip_z, c.POST_D/2, c.POST_D/2, 64).translate([sw[c.BUTTON], b.sw_y, tip_z])
    plate += post_cyl - union(k for n, k in keep.items() if not n.startswith(c.BUTTON))

    geo = dict(R_BORE=R_BORE, R_REAR=R_REAR, R_OUT=R_OUT, FLOOR=FLOOR, Z_CASE=Z_CASE, bh_p=bh_p,
               groove_r_p=groove_r_p, hdrs=hdrs, sw=sw, post_cyl=post_cyl)
    return feats, case, plate, geo


def run_checks(b, c, feats, case, plate, geo):
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
    probe = m3.Manifold.cylinder(c.LIP_T + 2, (b.active_d + 1)/2, (b.active_d + 1)/2, SEG).translate([0, 0, -c.LIP_T - 1])
    win_d = 2*(b.r - c.LIP_OVERLAP)
    check((probe ^ case).volume() < 1e-4, f"window clears active display {b.active_d:.2f} + 1",
          f"window {win_d:.2f}, margin {win_d - b.active_d - 1:.2f}")
    ring = prism(circle(b.r - 0.05) - circle(b.r - c.LIP_OVERLAP + 0.05), -0.05, 0.0)
    check((ring ^ case).volume() > 0.5, "lip overlaps the glass edge (retains it)", f"{c.LIP_OVERLAP:.2f} per side")

    print("\n5. Parts, snap, walls, USB-C notch")
    v = (case ^ plate).volume()
    check(v < 1e-3, "case and plate do not overlap", f"{v:.4f} mm^3")
    s = (case ^ plate.translate([0, 0, geo["bh_p"]])).volume()
    check(s > 1.0, "plate pulled back one bead height interferes (it snaps)", f"{s:.1f} mm^3")
    walls = {"case wall behind the plate groove": geo["R_OUT"] - geo["groove_r_p"], "bezel lip": c.LIP_T,
             "case wall at the back rim": geo["R_OUT"] - geo["R_REAR"] - BACK_CHAMFER,
             "step under the plate": geo["R_REAR"] - geo["R_BORE"], "plate": c.PLATE_T,
             "guide walls": c.GUIDE_WALL, "skirt": c.SKIRT_WALL}
    for nm, t in walls.items():
        check(t >= c.MIN_WALL - 1e-9, f"{nm} >= {c.MIN_WALL}", f"{t:.2f}")
    reach = geo["R_OUT"] - b.tip_y
    check(reach < 10.0, "plug overmold reaches the port through the notch", f"notch {reach:.1f} deep")
    back = bbox(case)[1, 2]
    check(abs(back - bbox(plate)[1, 2]) < 1e-3, "plate is flush with the case back", f"z {back:.2f}")


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
             title="From the back: plate removed, USB-C notch open at 12 o'clock")


def main():
    b, c = Badge(), Case()
    feats, case, plate, geo = build(b, c)
    asm = bbox(case + plate)
    size = asm[1] - asm[0]
    print(f"Case Ø{2*geo['R_OUT']:.2f} x {size[2]:.2f} thick; bore Ø{2*geo['R_BORE']:.2f}; counterbore Ø{2*geo['R_REAR']:.2f}")
    run_checks(b, c, feats, case, plate, geo)
    print()
    export(case, "stl/pocketwatch/Pocketwatch USB-only - case.stl", lambda m: m.translate([0, 0, c.LIP_T]))
    export(plate, "stl/pocketwatch/Pocketwatch USB-only - plate.stl",
           lambda m: m.rotate([0, 180, 0]).translate([0, 0, geo["Z_CASE"]]))
    if "--no-render" not in sys.argv:
        renders(b, c, feats, case, plate, geo)
    if FAILS:
        sys.exit("FAILED: " + "; ".join(FAILS))
    print("all checks passed")


if __name__ == "__main__":
    main()
