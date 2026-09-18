import math, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse
import importlib.util, sys

spec = importlib.util.spec_from_file_location("bs", "build_stands.py")
bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)

n = len(bs.BOARDS)
fig, axes = plt.subplots(2, n, figsize=(5.4*n, 11), dpi=125)

for col, (key, p) in enumerate(bs.BOARDS.items()):
    A, B, C, axis, perp, bc = bs.build_profiles(p)

    # ---------------- row 0: side section -------------------------------
    ax = axes[0][col]
    ax.add_patch(Polygon(A, closed=True, fc="#5b8dd9", ec="#1f3b6e", lw=1.5, zorder=2))
    # the notch, seen through the shoulder
    ax.add_patch(Polygon(C, closed=True, fc="#ffffff", ec="#1f3b6e",
                         lw=0.9, ls=(0,(4,2)), alpha=.95, zorder=3))
    ax.add_patch(Polygon(B, closed=True, fc="#9fc0ea", ec="#1f3b6e", lw=0.9, zorder=3))

    ht = p["thick"]/2
    corners = []
    for e in (0.0, p["board_d"]):
        for s in (-1, 1):
            corners.append((bc[0]+axis[0]*e + perp[0]*ht*s,
                            bc[1]+axis[1]*e + perp[1]*ht*s))
    board = [corners[0], corners[1], corners[3], corners[2]]
    ax.add_patch(Polygon(board, closed=True, fc="none", ec="#111", lw=1.8, zorder=5))

    s0 = (p["board_d"]-p["screen_d"])/2
    d0 = (bc[0]+axis[0]*s0, bc[1]+axis[1]*s0)
    d1 = (d0[0]+axis[0]*p["screen_d"], d0[1]+axis[1]*p["screen_d"])
    off = (perp[0]*(ht+0.7), perp[1]*(ht+0.7))
    ax.plot([d0[0]-off[0], d1[0]-off[0]], [d0[1]-off[1], d1[1]-off[1]],
            color="#e04a2f", lw=4, solid_capstyle="butt", zorder=6,
            label=f"screen Ø{p['screen_d']}")
    ax.plot([0, p["base_d"]], [0, 0], color="#888", lw=1, ls="--", zorder=1)
    ax.annotate("cable notch\n(through)", xy=((A[0][0]+p['base_d'])/2, p["notch_floor"]+1.6),
                xytext=(p["base_d"]*0.52, p["base_h"]+6), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set_title(f"{p['label']}\nØ{p['board_d']} × {p['thick']} mm", fontsize=9.5)
    ax.set_xlabel("depth Y (mm)"); ax.set_ylabel("height Z (mm)")
    ax.set_xlim(-12, 56); ax.set_ylim(-4, 60); ax.set_aspect("equal")
    ax.grid(alpha=.25); ax.legend(loc="upper left", fontsize=8, frameon=False)

    # ---------------- row 1: front elevation ----------------------------
    ax = axes[1][col]
    W, H, f = p["width"], p["base_h"], p["notch_floor"]
    x1, x2 = (W-p["notch_w"])/2, (W+p["notch_w"])/2
    sil = [(0,0),(W,0),(W,H),(x2,H),(x2,f),(x1,f),(x1,H),(0,H)]
    # A disc leaning back by `lean` projects onto the front elevation as an
    # ellipse: full width, but foreshortened vertically by cos(lean).
    R  = p["board_d"]/2
    k  = math.cos(math.radians(p["lean"]))
    cx = W/2
    sag = R - math.sqrt(max(R*R - (p["notch_w"]/2.0)**2, 0.0))
    z_bottom = bc[1] - sag                      # rim rests on the shoulders
    cy = z_bottom + R*k
    ax.add_patch(Ellipse((cx, cy), 2*R, 2*R*k, fc="none", ec="#111", lw=1.6, zorder=4))
    ax.add_patch(Ellipse((cx, cy), p["screen_d"], p["screen_d"]*k,
                         fc="#2a2a2a", ec="#e04a2f", lw=1.4, alpha=.85, zorder=3))
    ax.add_patch(Polygon(sil, closed=True, fc="#5b8dd9", ec="#1f3b6e", lw=1.5, zorder=5))
    ax.plot([-6, W+6], [0,0], color="#888", lw=1, ls="--", zorder=1)
    ax.annotate(f"notch {p['notch_w']:.0f} wide",
                xy=(cx, f+0.8), xytext=(cx+R*0.62, -3.2),
                fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.8), zorder=7)
    ax.annotate(f"shoulder\n{(W-p['notch_w'])/2:.1f}", xy=(x1/2, H*0.55),
                fontsize=7.5, ha="center", color="#0d2547", zorder=7)
    ax.set_title("front elevation — board shown behind", fontsize=9)
    ax.set_xlabel("width X (mm)"); ax.set_ylabel("height Z (mm)")
    ax.set_xlim(-10, W+10); ax.set_ylim(-5, cy+R*k+6); ax.set_aspect("equal")
    ax.grid(alpha=.25)

fig.suptitle("Waveshare round-board desk stands — side sections (top) and front elevations (bottom)",
             fontsize=12)
fig.tight_layout()
fig.savefig("preview-all.png")
print("wrote preview-all.png")
