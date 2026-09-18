#!/usr/bin/env python3
"""
Desk stand for Waveshare ESP32-S3-LCD-1.28 (SKU 26541).

Board facts, read off the official outline drawing
(waveshare.com/w/upload/e/ed/Esp32-s3-lcd-1.28-003.jpg):
  - round PCB, R = 18.25 mm  ->  D = 36.5 mm
  - flat chord at top, 18.37 mm wide, carrying the USB-C (12.81 mm wide)
  - 1.27 mm pitch headers H1/H2, ~27 mm outer span, mid-board
  - active display  D = 32.4 mm

Design: an angled slot ("plate stand") extruded as a single prism.
The disc drops into the groove edge-first and leans back; no supports,
no overhangs, no moving parts, ~5 g of filament.
Emits binary STL.
"""
import math, struct

# ---- parameters (mm) -------------------------------------------------
BOARD_D     = 36.5   # PCB outside diameter
PCB_T       = 1.6    # bare PCB thickness at the rim
FIT         = 0.8    # total slop added to the groove width
LEAN        = 20.0   # degrees the screen leans back from vertical
SLOT_DEPTH  = 5.0    # how far the rim sits into the groove
BASE_D      = 27.0   # base depth, front-to-back (Y)
BASE_H      = 10.0   # ridge height at the groove (Z)
FRONT_H     = 3.0    # height of the front lip
BACK_H      = 4.0    # height of the back lip
RIDGE_HALF  = 2.0    # flat top either side of the groove
WIDTH       = 24.0   # base width (X); disc overhangs slightly -> looks light
SLOT_Y      = 12.0   # groove centreline where it meets the top face

SLOT_GAP = PCB_T + FIT

# ---- 2D side profile in (y, z) ---------------------------------------
a = math.radians(LEAN)
axis = (math.sin(a), math.cos(a))      # up-and-back, along the board
perp = (math.cos(a), -math.sin(a))     # across the groove
half = SLOT_GAP / 2.0

# where each groove wall crosses the top face z = BASE_H
dy = half / math.cos(a) + 0.0
shift = half * math.tan(a) * math.sin(a) + half * math.cos(a)
t = half * math.sin(a) / math.cos(a)
wall_off = axis[0] * t + perp[0] * half   # horizontal offset at z = BASE_H

top_back  = (SLOT_Y + wall_off, BASE_H)
top_front = (SLOT_Y - wall_off, BASE_H)

bc = (SLOT_Y - axis[0] * SLOT_DEPTH, BASE_H - axis[1] * SLOT_DEPTH)  # groove floor centre
bottom_back  = (bc[0] + perp[0] * half, bc[1] + perp[1] * half)
bottom_front = (bc[0] - perp[0] * half, bc[1] - perp[1] * half)

# tapered wedge: low front lip -> ridge carrying the groove -> low back lip
ridge_back  = (top_back[0]  + RIDGE_HALF, BASE_H)
ridge_front = (top_front[0] - RIDGE_HALF, BASE_H)
profile = [
    (0.0, 0.0), (BASE_D, 0.0), (BASE_D, BACK_H), ridge_back,
    top_back, bottom_back, bottom_front, top_front,
    ridge_front, (0.0, FRONT_H),
]

# ---- ear-clipping triangulation --------------------------------------
def area2(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return s

def cross(o, a_, b_):
    return (a_[0]-o[0])*(b_[1]-o[1]) - (a_[1]-o[1])*(b_[0]-o[0])

def inside(p, a_, b_, c_):
    d1 = cross(a_, b_, p); d2 = cross(b_, c_, p); d3 = cross(c_, a_, p)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)

def triangulate(poly):
    assert area2(poly) > 0, "profile must be CCW"
    idx = list(range(len(poly)))
    tris = []
    guard = 0
    while len(idx) > 2 and guard < 10000:
        guard += 1
        made = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k-1], idx[k], idx[(k+1) % len(idx)]
            a_, b_, c_ = poly[i0], poly[i1], poly[i2]
            if cross(a_, b_, c_) <= 1e-12:      # reflex or degenerate
                continue
            if any(inside(poly[j], a_, b_, c_)
                   for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            made = True
            break
        if not made:
            raise RuntimeError("ear clipping stalled")
    return tris

tris2d = triangulate(profile)

# ---- build the prism -------------------------------------------------
W = WIDTH
facets = []
def add(p, q, r):
    facets.append((p, q, r))

# cap at x = W  (CCW in yz  ->  +X normal)
for i0, i1, i2 in tris2d:
    add((W,) + profile[i0], (W,) + profile[i1], (W,) + profile[i2])
# cap at x = 0  (reversed  ->  -X normal)
for i0, i1, i2 in tris2d:
    add((0.0,) + profile[i2], (0.0,) + profile[i1], (0.0,) + profile[i0])
# side walls
n = len(profile)
for i in range(n):
    v0 = profile[i]; v1 = profile[(i + 1) % n]
    A = (0.0,) + v0; B = (0.0,) + v1
    C = (W,) + v1;   D = (W,) + v0
    add(A, B, C); add(A, C, D)

def normal(t3):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t3
    ux, uy, uz = bx-ax, by-ay, bz-az
    vx, vy, vz = cx-ax, cy-ay, cz-az
    nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
    L = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
    return nx/L, ny/L, nz/L

with open("esp32-s3-lcd-128-stand.stl", "wb") as f:
    f.write(b"\0" * 80)
    f.write(struct.pack("<I", len(facets)))
    for t3 in facets:
        f.write(struct.pack("<3f", *normal(t3)))
        for v in t3:
            f.write(struct.pack("<3f", *v))
        f.write(struct.pack("<H", 0))

# ---- report ----------------------------------------------------------
vol = abs(area2(profile)) / 2.0 * W / 1000.0          # cm^3
bottom = bc
centre = (bottom[0] + axis[0]*(BOARD_D/2), bottom[1] + axis[1]*(BOARD_D/2))
top    = (bottom[0] + axis[0]*BOARD_D,     bottom[1] + axis[1]*BOARD_D)
print(f"groove gap        {SLOT_GAP:.2f} mm  (PCB {PCB_T} + {FIT} fit)")
print(f"groove opening    y {top_front[0]:.2f} .. {top_back[0]:.2f}")
print(f"groove floor      y {bottom_front[0]:.2f} .. {bottom_back[0]:.2f}  z {bc[1]:.2f}")
print(f"disc centre       y {centre[0]:.2f}  z {centre[1]:.2f}")
print(f"disc top edge     y {top[0]:.2f}  z {top[1]:.2f}   (base spans y 0..{BASE_D})")
print(f"screen height     {top[1]:.1f} mm above the desk")
print(f"facets            {len(facets)}")
print(f"solid volume      {vol:.2f} cm^3  (~{vol*1.24:.1f} g PLA)")
assert 0 < top[0] < BASE_D, "board overhangs the base - deepen BASE_D"
assert centre[0] < BASE_D and centre[0] > 0, "unstable"
print("OK: board footprint stays inside the base")
