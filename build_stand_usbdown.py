#!/usr/bin/env python3
"""1.28 dock, badge seated USB-C DOWN, for a right-angle cable.

The badge is the same one, turned over. That moves three things at once, and
all three are checked here as solids rather than as arithmetic:

  * the USB-C tab (which sticks 2.85 mm past the disc) and the plug on it now
    hang into the cable notch -- so the notch has to pass an 18.37 mm tab, not
    a cable;
  * BOOT/RESET go to the TOP, out of the groove entirely (they were the thing
    that broke the 20 deg stand);
  * the headers and the battery JST come DOWN toward the groove, which is what
    `rear_lip` is keeping clear of.

Leaning it 30 deg rather than 20 points the port down-and-forward, so the plug
tucks into the notch instead of demanding headroom under the rim.

Run with ~/.venvs/cad/bin/python.
"""
import sys, math, importlib.util, numpy as np, manifold3d as m3
sys.path.insert(0, "pod"); from render import render
spec = importlib.util.spec_from_file_location("bs", "build_stands.py")
bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)

p = bs.BOARDS["1.28-usbdown"]
A, B, C, axis, perp, bc = bs.build_profiles(p)
W, R, T = p["width"], p["board_d"]/2, p["thick"]
x1, x2 = (W - p["notch_w"])/2, (W + p["notch_w"])/2
LEAN = p["lean"]

stand = m3.Manifold.extrude(m3.CrossSection([[list(v) for v in A]]), W).rotate([90, 0, 90])
stand -= m3.Manifold.cube([p["notch_w"], p["base_d"] + 2, p["base_h"]]).translate([x1, -1, p["notch_floor"]])

sag = R - math.sqrt(R*R - (p["notch_w"]/2)**2)
ctr = np.array([bc[0], bc[1]]) + np.array(axis)*(R - sag)      # disc centre in (y,z)
ax_, pp_ = np.array(axis), np.array(perp)


def board_pt(bx, by, d):
    """bx across the badge, by up the badge from its centre, d behind the PCB mid-plane."""
    yz = ctr + ax_*by + pp_*d
    return [W/2 + bx, yz[0], yz[1]]


def blk(w, thk, by0, by1, d0, bx=0.0):
    """A box in badge coordinates: w wide, thk deep, spanning by0..by1 up the badge,
    its near face d0 behind the PCB mid-plane."""
    h = by1 - by0
    b = m3.Manifold.cube([w, thk, h]).translate([-w/2, 0, 0]).rotate([-LEAN, 0, 0])
    return b.translate(board_pt(bx, by0, d0))


def disc(r, thk, d0):
    c = m3.Manifold.cylinder(thk, r, circular_segments=160).rotate([-(90 + LEAN), 0, 0])
    return c.translate(board_pt(0, 0, d0))


# A disc must lie IN the badge's plane: its axis is `perp` (through the thickness),
# not `axis` (up the badge). Check the rotation rather than trusting the sign.
_probe = m3.Manifold.cylinder(10.0, 0.5, circular_segments=8).rotate([-(90 + LEAN), 0, 0])
_c = np.asarray(_probe.to_mesh().vert_properties)[:, :3].mean(0) / 5.0
assert np.allclose(_c[1:], pp_, atol=0.02), f"disc() axis is {_c[1:]}, wanted perp {pp_}"


# ---- the badge as it sits, turned over ------------------------------------
badge = disc(R, T, -T/2)
face  = disc(p["screen_d"]/2, 0.4, -T/2 - 0.4)
tab   = blk(p["tab_w"], 1.6, -(R - 1.0), -p["tab_r"], -0.8)
plug  = blk(14.0, 9.0, -p["tab_r"] - p["plug_len"], -p["tab_r"], -4.5)
# back-mounted parts, measured off the 09-20 photo then flipped (by -> -by)
hdrL  = blk(6.2, 8.5, -11.4, 12.7, T/2, bx=-13.5)
hdrR  = blk(6.2, 8.5, -11.4, 12.7, T/2, bx=+13.5)
jst   = blk(8.4, 5.0, -12.1, -5.5, T/2, bx=+7.9)
sw1   = blk(3.5, 2.0, 10.5 - 1.75, 10.5 + 1.75, T/2, bx=-11.45)
sw2   = blk(3.5, 2.0, 10.5 - 1.75, 10.5 + 1.75, T/2, bx=+11.45)

parts = [("badge", badge), ("USB-C tab", tab), ("right-angle plug", plug),
         ("header H1", hdrL), ("header H2", hdrR), ("battery JST", jst),
         ("BOOT", sw1), ("RESET", sw2)]
print(f"{p['label']}\n  lean {LEAN}deg, notch {p['notch_w']:.0f}, rear wall stops {p['rear_lip']} mm up\n")
bad = []
for nm, s in parts:
    v = (s ^ stand).volume()
    print(f"  {nm:18s} overlap with the stand: {v:8.2f} mm^3")
    if v > 0.5:
        bad.append(nm)
assert not bad, f"these hit the stand: {', '.join(bad)}"

low = min(board_pt(0, -p["tab_r"] - p["plug_len"], d)[2] for d in (-4.5, 4.5))
print(f"\n  plug bottom {low:.1f} mm above the desk; notch floor at {p['notch_floor']}")
assert low > p["notch_floor"] + 1.0, "plug fouls the notch floor"

# build_stands.py owns the STL (the proven watertight path); this script only
# re-derives the same solid to check it against the real badge, and renders it.
print(f"  {p['stl']}: {stand.volume()/1000:.2f} cm^3 -- written by build_stands.py")

grey, dark, blue, red, tan, white = ((0.62, 0.64, 0.68), (0.07, 0.07, 0.08), (0.15, 0.48, 0.90),
                                     (0.90, 0.25, 0.20), (0.85, 0.72, 0.45), (0.95, 0.95, 0.9))
render([(stand, grey), (badge, dark), (face, blue), (tab, tan), (plug, red)],
       "renders/stand-1.28-usbdown-side.png", elev=6, azim=-88,
       title=f"1.28 USB-C DOWN dock — from the side: tab (tan) and right-angle plug (red) hang in the notch")
render([(stand, grey), (badge, dark), (tab, tan), (plug, red), (hdrL, white), (hdrR, white), (jst, white)],
       "renders/stand-1.28-usbdown-back.png", elev=18, azim=125,
       title="1.28 USB-C DOWN dock — from behind: headers and battery JST (white) clear the lowered rear wall")
