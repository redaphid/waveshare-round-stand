#!/usr/bin/env python3
"""
1.28 desk stand with a button post.

Same stand as "stl/small/Stand.stl", plus a short post
behind the badge, placed exactly behind the BOOT (or RESET) tactile switch.
Press the display and the badge rocks back in its groove onto the post: the
switch is the softest thing in the load path, so it is what gives -- click.

Because the badge leans on the groove's rear lip just *below* the post, a
push at the top of the display is levered ~12x onto the switch. A light tap
does it; the badge's own weight (~30 gf on the post) does not.

Seat the badge with its USB-C chord at the TOP. BOOT is then at the lower
right as you look at it; RESET at the lower left.

Switch positions come from reference/esp32-s3-lcd-1.28-switch-positions.png
(measured off Waveshare's outline drawing).

Run with ~/.venvs/cad/bin/python.   Args: [BOOT|RESET]
"""
import sys, math, importlib.util, numpy as np, manifold3d as m3, trimesh
sys.path.insert(0, "pod"); from render import render
spec = importlib.util.spec_from_file_location("bs", "build_stands.py")
bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)

BUTTON = (sys.argv[1] if len(sys.argv) > 1 else "BOOT").upper()
# front-view mm from disc centre, +x = your right, +y = up   (back-view x negated)
SWITCH = {"BOOT": (+8.95, -8.28), "RESET": (-9.67, -8.31)}[BUTTON]
CAP_H     = 2.0    # PCB surface to top of the switch actuator
REST_CLR  = 0.20   # post tip stands off the cap at rest
POST_R    = 1.6    # Ø3.2 pad -- forgiving of ±1 mm in the measurement
POST_LEN  = 14.0   # reaches back into the ridge/ramp

p = bs.BOARDS["1.28"]
A, B, C, axis, perp, bc = bs.build_profiles(p)
W, R, T = p["width"], p["board_d"]/2, p["thick"]
x1, x2 = (W - p["notch_w"])/2, (W + p["notch_w"])/2

# ---- the stand, rebuilt in manifold from the very same profile ------------
prof = m3.CrossSection([[list(v) for v in A]])
stand = m3.Manifold.extrude(prof, W).rotate([90, 0, 90])          # (y,z) profile swept along X
stand -= m3.Manifold.cube([p["notch_w"], p["base_d"] + 2, p["base_h"]]).translate([x1, -1, p["notch_floor"]])

# ---- where the badge sits ------------------------------------------------
sag = R - math.sqrt(R*R - (p["notch_w"]/2)**2)                    # rim rests on the shoulders
ctr = np.array([bc[0], bc[1]]) + np.array(axis)*(R - sag)          # disc centre in (y,z)
ax_, pp_ = np.array(axis), np.array(perp)
def board_pt(bx, by, depth):                                       # depth: + = behind the PCB mid-plane
    yz = ctr + ax_*by + pp_*depth
    return np.array([W/2 + bx, yz[0], yz[1]])

# The badge is loose in the groove by (gap - T) and rocks in it. Place the pad from the groove's
# FRONT wall: with the badge pushed upright against that wall the cap clears the pad by REST_CLR,
# so the post can never hold the switch down, whatever the real rim thickness turns out to be.
G = p["gap"]
tip_depth = -G/2 + T + CAP_H + REST_CLR                           # behind the groove centre-plane
tip  = board_pt(*SWITCH, tip_depth)
base = tip + np.array([0, pp_[0], pp_[1]]) * POST_LEN
def along_perp(make, half_len):
    """make(): a manifold built along +Z from z=0. Return it rotated so +Z lies along perp,
    checked numerically rather than by trusting a sign convention."""
    for rx in (90 + p["lean"], -(90 + p["lean"]), 90 - p["lean"], -(90 - p["lean"])):
        cand = make().rotate([rx, 0, 0])
        c = np.asarray(cand.to_mesh().vert_properties)[:, :3].mean(0) / half_len
        if np.allclose(c[1:], pp_, atol=0.03): return cand
    raise SystemExit("could not orient along perp")

# The pad faces the switch (its end face parallel to the PCB). The board's normal is only 20°
# below horizontal, so a post along it would leave the stand out the back without touching
# it -- hence a vertical column from inside the shoulder up to the pad.
PAD_L = 3.5
pad = along_perp(lambda: m3.Manifold.cylinder(PAD_L, POST_R, circular_segments=48), PAD_L/2).translate(tip.tolist())
pad_mid = tip + np.array([0, pp_[0], pp_[1]]) * (PAD_L/2)
col_top = pad_mid[2]
column = m3.Manifold.cylinder(col_top - 1.0, POST_R + 0.4, circular_segments=48).translate([pad_mid[0], pad_mid[1], 1.0])
post = pad + column

exposed_pad = (pad - stand).volume() / (math.pi*POST_R**2)
col_free    = (column - stand).volume() / (math.pi*(POST_R+0.4)**2)
buried      = (col_top - 1.0) - col_free
assert buried > 3.0, f"column only {buried:.1f} mm inside the stand"
out = stand + post

# ---- report ----------------------------------------------------------------
print(f"{BUTTON} switch at front-view ({SWITCH[0]:+.2f}, {SWITCH[1]:+.2f}) mm  ->  stand x={tip[0]:.2f} (shoulder {x2:.1f}..{W:.0f})"
      if SWITCH[0] > 0 else
      f"{BUTTON} switch at front-view ({SWITCH[0]:+.2f}, {SWITCH[1]:+.2f}) mm  ->  stand x={tip[0]:.2f} (shoulder 0..{x1:.1f})")
print(f"post tip   y={tip[1]:.2f} z={tip[2]:.2f}   Ø{2*POST_R:.1f} pad; column Ø{2*(POST_R+0.4):.1f} stands {col_free:.1f} mm out of the shoulder, {buried:.1f} mm rooted")
lip_h = p["base_h"]                                                 # groove opening (rear lip) height
btn_up = (tip[2] - bc[1]) / axis[1]                                # along the board, from the groove floor
print(f"switch sits {btn_up:.1f} mm up the badge; rear lip at {p['depth']:.0f} mm  ->  lever to the top ≈ "
      f"{(2*R - btn_up)/(btn_up - p['depth']):.0f}x")
# Can a press actually click it? Fully rocked back the badge lies on the rear lip with its bottom
# front edge on the front wall; the cap must be able to travel well past the pad before that.
SW_TRAVEL = 0.25                                                    # typical tact switch
u_lip = p["depth"] + G/2*math.tan(math.radians(p["lean"]))         # rear lip, up the board from the groove floor
u_sw  = (R - sag) + SWITCH[1]                                       # switch, up the board from the groove floor
cap_max = G/2 + (u_sw - u_lip)*(G - T)/u_lip + CAP_H
press = cap_max - tip_depth
print(f"press travel {press:.2f} mm available at the switch (needs {SW_TRAVEL}); badge loose by {G-T:.1f} in the groove")
assert u_sw > u_lip, "switch is below the rear lip -- pressing the screen would lift it off the post"
assert press >= 2*SW_TRAVEL, f"badge bottoms out in the groove after {press:.2f} mm -- the switch would not click"
assert x1 - POST_R > tip[0] or tip[0] > x2 + POST_R, "post would land in the cable notch"

name = f"stl/small/Stand - {BUTTON} button.stl"
m = out.to_mesh(); tm = trimesh.Trimesh(vertices=np.asarray(m.vert_properties)[:, :3], faces=np.asarray(m.tri_verts))
tm.export(name); print(f"{name}: {out.volume()/1000:.2f} cm^3, watertight {tm.is_watertight}, {len(tm.faces)} tris")

# ---- render: badge in place, post visible behind it -----------------------
badge = along_perp(lambda: m3.Manifold.cylinder(T, R, circular_segments=128), T/2).translate(board_pt(0, 0, -T/2).tolist())
face  = along_perp(lambda: m3.Manifold.cylinder(0.4, p["screen_d"]/2, circular_segments=128), 0.2).translate(board_pt(0, 0, -T/2 - 0.4).tolist())
sw    = along_perp(lambda: m3.Manifold.cylinder(CAP_H, 1.75, circular_segments=32), CAP_H/2).translate(board_pt(*SWITCH, T/2).tolist())
grey, dark, red, blue = (0.62, 0.64, 0.68), (0.07, 0.07, 0.08), (0.90, 0.25, 0.20), (0.15, 0.48, 0.90)
render([(stand, grey), (post, red), (badge, dark), (face, blue), (sw, (0.95, 0.95, 0.9))],
       f"renders/stand-1.28-{BUTTON}-post-back.png", elev=22, azim=140,
       title=f"1.28 stand, {BUTTON} post (red) — from behind: post lands on the switch (white), press travel {press:.1f} mm")
render([(stand, grey), (post, red), (badge, dark), (face, blue)],
       f"renders/stand-1.28-{BUTTON}-post-front.png", elev=12, azim=-62,
       title=f"1.28 stand, {BUTTON} post — from the front, badge seated USB-C up; press the screen to click {BUTTON}")
