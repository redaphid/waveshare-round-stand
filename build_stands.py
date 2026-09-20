#!/usr/bin/env python3
"""
Desk stands for three Waveshare round display boards.

A tapered wedge with one groove angled back from vertical; the board drops in
rim-first. A cable notch is cut clean through the middle of the ridge, front to
back, so a USB-C lead can run through the stand instead of over it. The two
shoulders either side of the notch keep hold of the board.

Prints flat on the base -- no supports, no overhangs.

Dimensions come from Waveshare's own outline drawings (see reference/), not
from guesswork; neither product page states them in text.

Mesh construction
-----------------
The solid is three slabs stacked along X:

    [0, x1)   profile A -- full wedge with the groove
    [x1, x2)  profile B -- just the base slab below the notch floor
    [x2, W]   profile A

A and B share their lower boundary exactly, so the exposed face at each
internal boundary is precisely C = A \\ B, a single simple polygon (the notch
floor sits below the groove floor, so the groove does not split it in two).
That keeps the result watertight without needing a general polygon boolean.
"""
import math, struct

# ------------------------------------------------------------------ profiles
def build_profiles(p):
    """Return (A, B, C, axis, perp, groove_floor_centre)."""
    a = math.radians(p["lean"])
    axis = (math.sin(a), math.cos(a))     # up-and-back, along the board
    perp = (math.cos(a), -math.sin(a))    # across the groove
    half = p["gap"] / 2.0
    H, D, f = p["base_h"], p["base_d"], p["notch_floor"]

    wall_off = axis[0] * (half * math.tan(a)) + perp[0] * half
    top_back  = (p["slot_y"] + wall_off, H)
    top_front = (p["slot_y"] - wall_off, H)
    bc = (p["slot_y"] - axis[0]*p["depth"], H - axis[1]*p["depth"])
    bottom_back  = (bc[0] + perp[0]*half, bc[1] + perp[1]*half)
    bottom_front = (bc[0] - perp[0]*half, bc[1] - perp[1]*half)
    ridge_back  = (top_back[0]  + p["ridge_half"], H)
    ridge_front = (top_front[0] - p["ridge_half"], H)

    # Optional: stop the groove's REAR wall short of the ridge. The 1.28 needs
    # this -- its BOOT/RESET switches stand ~1.7 mm off the back of the PCB only
    # 2.7 mm in from the rim, so with a full-height rear wall the switch housing
    # is below the lip and simply cannot enter a 5.4 mm groove: the badge is
    # propped proud and shoved forward (print 09-20). Lowering the rear wall
    # also drops the pivot, which is what gives a press any travel at the switch.
    rl = p.get("rear_lip")
    if rl is None:
        upper = [(D, p["back_h"]), ridge_back, top_back, bottom_back,
                 bottom_front, top_front, ridge_front, (0.0, p["front_h"])]
    else:
        lip_back = (bottom_back[0] + axis[0]*rl, bottom_back[1] + axis[1]*rl)
        upper = [(D, p["back_h"]), lip_back, bottom_back,
                 bottom_front, top_front, ridge_front, (0.0, p["front_h"])]

    A = [(0.0, 0.0), (D, 0.0), (D, f)] + upper + [(0.0, f)]
    B = [(0.0, 0.0), (D, 0.0), (D, f), (0.0, f)]
    C = [(0.0, f), (D, f)] + upper
    return A, B, C, axis, perp, bc

# ------------------------------------------------- polygon -> watertight mesh
def area2(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        s += x1*y2 - x2*y1
    return s

def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

def in_tri(p, a, b, c):
    d1, d2, d3 = cross(a,b,p), cross(b,c,p), cross(c,a,p)
    return not ((d1<0 or d2<0 or d3<0) and (d1>0 or d2>0 or d3>0))

def triangulate(poly):
    assert area2(poly) > 0, "profile must wind counter-clockwise"
    idx = list(range(len(poly))); tris = []; guard = 0
    while len(idx) > 2 and guard < 20000:
        guard += 1; made = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k-1], idx[k], idx[(k+1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if cross(a, b, c) <= 1e-12:
                continue
            if any(in_tri(poly[j], a, b, c) for j in idx if j not in (i0,i1,i2)):
                continue
            tris.append((a, b, c)); idx.pop(k); made = True; break
        if not made:
            raise RuntimeError("ear clipping stalled")
    return tris

def cap(poly, x, flip):
    """Planar face at plane X = x. CCW in (y,z) faces +X; flip for -X."""
    out = []
    for a, b, c in triangulate(poly):
        t = ((x,)+a, (x,)+b, (x,)+c)
        out.append(t[::-1] if flip else t)
    return out

def walls(poly, x0, x1):
    """Side walls of `poly` swept from X=x0 to X=x1."""
    out = []; n = len(poly)
    for i in range(n):
        v0, v1 = poly[i], poly[(i+1) % n]
        A_, B_ = (x0,)+v0, (x0,)+v1
        C_, D_ = (x1,)+v1, (x1,)+v0
        out += [(A_, B_, C_), (A_, C_, D_)]
    return out

def build_mesh(A, B, C, width, notch_w):
    x1 = (width - notch_w) / 2.0
    x2 = (width + notch_w) / 2.0
    f  = []
    f += cap(A, 0.0,   flip=True)     # -X end
    f += cap(A, width, flip=False)    # +X end
    f += walls(A, 0.0, x1)            # left shoulder
    f += walls(B, x1,  x2)            # notch floor slab
    f += walls(A, x2,  width)         # right shoulder
    f += cap(C, x1, flip=False)       # notch wall, facing +X into the gap
    f += cap(C, x2, flip=True)        # notch wall, facing -X
    return f

def write_stl(facets, path):
    def nrm(t):
        (ax,ay,az),(bx,by,bz),(cx,cy,cz) = t
        ux,uy,uz = bx-ax, by-ay, bz-az
        vx,vy,vz = cx-ax, cy-ay, cz-az
        nx,ny,nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
        L = math.sqrt(nx*nx+ny*ny+nz*nz) or 1.0
        return nx/L, ny/L, nz/L
    with open(path, "wb") as fh:
        fh.write(b"\0"*80); fh.write(struct.pack("<I", len(facets)))
        for t in facets:
            fh.write(struct.pack("<3f", *nrm(t)))
            for v in t: fh.write(struct.pack("<3f", *v))
            fh.write(struct.pack("<H", 0))

# ------------------------------------------------------------------- boards
PETG = 1.27  # g/cm^3

BOARDS = {
    "1.28": dict(
        group = "stand",
        label   = "ESP32-S3-LCD-1.28 (SKU 26541)",
        board_d = 36.5, thick = 4.7, screen_d = 32.4,   # PCB + display module at the rim (gauge, 09-18)
        gap = 5.4, lean = 20, depth = 5.0,             # gauge slot 5.0 + 0.4: the leaned walls stair-step ~0.1 each into the slot (print 09-20)
        rear_lip = 3.0,                                # rear wall stops here: clears the BOOT/RESET housings (photo, 09-20)
        base_d = 27.0, base_h = 12.0, front_h = 3.0, back_h = 4.0,
        ridge_half = 2.0, width = 30.0, slot_y = 12.0,  # 26 -> 30: the switches are at |x| 11.45, the post needs shoulder
        notch_w = 13.0, notch_floor = 2.0,
        stl = "stl/small/Stand.stl",
    ),
    # The 1.46 ships in two cover-glass options and they are NOT the same part.
    # With glass: a round Ø44.77 glass disc overhangs the PCB, 12.30 stack.
    # Without:    a 39.36 x 41.53 panel on a Ø42.58 PCB -- the PCB rim is then
    #             the widest thing -- 10.65 stack.
    "1.46-glass": dict(
        group = "stand",
        label   = "ESP32-S3-Touch-LCD-1.46, with cover glass",
        board_d = 44.77, thick = 12.30, screen_d = 36.96,
        gap = 12.30+0.8, lean = 20, depth = 8.0,
        base_d = 36.0, base_h = 16.0, front_h = 4.0, back_h = 5.0,
        ridge_half = 2.5, width = 30.0, slot_y = 16.0,
        notch_w = 14.0, notch_floor = 2.0,
        stl = "stl/large/Stand - cover glass.stl",
    ),
    "1.46-bare": dict(
        group = "stand",
        label   = "ESP32-S3-Touch-LCD-1.46, no cover glass",
        board_d = 42.58, thick = 10.65, screen_d = 36.96,
        gap = 10.65+0.8, lean = 20, depth = 8.0,
        base_d = 35.0, base_h = 16.0, front_h = 4.0, back_h = 5.0,
        ridge_half = 2.5, width = 29.0, slot_y = 15.5,
        notch_w = 14.0, notch_floor = 2.0,
        stl = "stl/large/Stand - no cover glass.stl",
    ),
    # DOCKS. A straight USB-C plug in the 1.46's bottom port points radially
    # down. The low stands leave ~5 mm under the rim; a plug body is ~20-25 mm.
    # These lift the board so the plug hangs straight down through the notch
    # and the cable turns out the back at desk level.
    "1.46-glass-dock": dict(
        group = "dock",
        label   = "ESP32-S3-Touch-LCD-1.46, with cover glass -- DOCK",
        board_d = 44.77, thick = 12.30, screen_d = 36.96,
        gap = 12.30+0.8, lean = 20, depth = 8.0,
        base_d = 38.0, base_h = 38.0, front_h = 5.0, back_h = 6.0,
        ridge_half = 2.5, width = 30.0, slot_y = 19.0,
        notch_w = 16.0, notch_floor = 2.0, plug_len = 24.0,
        stl = "stl/large/Dock for straight cable - cover glass.stl",
    ),
    "1.46-bare-dock": dict(
        group = "dock",
        label   = "ESP32-S3-Touch-LCD-1.46, no cover glass -- DOCK",
        board_d = 42.58, thick = 10.65, screen_d = 36.96,
        gap = 10.65+0.8, lean = 20, depth = 8.0,
        base_d = 37.0, base_h = 38.0, front_h = 5.0, back_h = 6.0,
        ridge_half = 2.5, width = 29.0, slot_y = 18.5,
        notch_w = 16.0, notch_floor = 2.0, plug_len = 24.0,
        stl = "stl/large/Dock for straight cable - no cover glass.stl",
    ),
}

if __name__ == "__main__":
    for key, p in BOARDS.items():
        A, B, C, axis, perp, bc = build_profiles(p)
        facets = build_mesh(A, B, C, p["width"], p["notch_w"])
        write_stl(facets, p["stl"])

        top = (bc[0] + axis[0]*p["board_d"], bc[1] + axis[1]*p["board_d"])
        ctr = (bc[0] + axis[0]*p["board_d"]/2, bc[1] + axis[1]*p["board_d"]/2)
        solid = abs(area2(A))/2.0 * p["width"]
        cut   = abs(area2(C))/2.0 * p["notch_w"]
        vol   = (solid - cut) / 1000.0
        shoulder = (p["width"] - p["notch_w"]) / 2.0
        # how far the disc sinks, unsupported across the notch
        R = p["board_d"]/2.0
        sag = R - math.sqrt(max(R*R - (p["notch_w"]/2.0)**2, 0.0))

        print(f"\n=== {p['label']} -> {p['stl']} ===")
        print(f"  groove        {p['gap']:.2f} wide x {p['depth']:.1f} deep "
              f"(board {p['thick']} + {p['gap']-p['thick']:.1f} fit)")
        print(f"  cable notch   {p['notch_w']:.0f} wide, floor at z={p['notch_floor']:.1f}, "
              f"{p['base_h']-p['notch_floor']:.1f} tall, open front-to-back")
        print(f"  shoulders     {shoulder:.1f} mm each side")
        full_wall = p["depth"] + (p["gap"]/2.0)*math.tan(math.radians(p["lean"]))
        if p.get("rear_lip") is not None:
            print(f"  rear wall     stops {p['rear_lip']:.1f} mm up the board "
                  f"(full wall would be {full_wall:.2f}) -- switch clearance")
        clear = bc[1] - sag - p["notch_floor"]
        print(f"  disc sag      {sag:.2f} mm over the notch "
              f"(engagement {p['depth']+sag:.1f} mm)")
        print(f"  cable clear   {clear:.2f} mm between the board rim and the notch floor")
        if p.get("plug_len"):
            print(f"  straight plug {p['plug_len']:.0f} mm body -> "
                  f"{clear - p['plug_len']:.1f} mm spare for the cable to turn")
            run = (bc[1] - sag - p["notch_floor"]) / axis[1]      # along the plug axis
            tip_y = bc[0] - axis[0] * run
            print(f"  plug tip lands y={tip_y:.1f} of base 0..{p['base_d']:.0f} "
                  f"-> {tip_y:.0f} mm to the front edge, {p['base_d']-tip_y:.0f} mm to the back")
        print(f"  footprint     {p['width']:.0f} x {p['base_d']:.0f}, ridge {p['base_h']:.0f} tall")
        print(f"  screen top    {top[1]:.1f} mm above the desk")
        print(f"  material      {vol:.2f} cm^3  ~= {vol*PETG:.1f} g PETG")
        print(f"  facets        {len(facets)}")

        assert 0 < top[0] < p["base_d"], f"{key}: board overhangs the base"
        assert p["base_d"]*0.25 < ctr[0] < p["base_d"]*0.75, f"{key}: CoM off-centre"
        assert bc[1] > p["notch_floor"] + 0.5, \
            f"{key}: notch floor {p['notch_floor']} not clear of groove floor {bc[1]:.2f}"
        assert p["notch_floor"] < min(p["front_h"], p["back_h"]), \
            f"{key}: notch floor above the front/back lip -- profile C would not be simple"
        assert shoulder >= 4.0, f"{key}: shoulders only {shoulder:.1f} mm"
        if p.get("plug_len"):
            assert clear >= p["plug_len"] + 2.0, \
                f"{key}: {clear:.1f} mm under the rim will not take a {p['plug_len']} mm plug"
        assert clear >= 3.5, \
            f"{key}: only {clear:.2f} mm under the rim -- a cable will not pass"
        assert p["width"] < p["board_d"], f"{key}: stand wider than the board"
        if p.get("rear_lip") is not None:
            rl = p["rear_lip"]
            assert 0 < rl < full_wall, f"{key}: rear_lip {rl} not inside the groove (wall is {full_wall:.2f})"
            lip_z = bc[1] + perp[1]*(p["gap"]/2.0) + axis[1]*rl
            assert lip_z > p["back_h"] + 0.5, \
                f"{key}: rear lip z={lip_z:.2f} not above the back face {p['back_h']} -- ramp would invert"
            assert lip_z > p["notch_floor"] + 0.5, f"{key}: rear lip below the notch floor"
        print("  checks        OK")
