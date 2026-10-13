"""
Shared drawing helpers for measured whiteboard schematics (frames in the style of A-D): slice and project
world-frame manifold3d solids, emit draw-MCP ops with pastel fills, holes painted white, dimension lines.

Board layout for the design gallery (one row per design, frames in a grid, no overlaps):
  row y0 = 40 + ROW[design]*1100; frames sit at y0 + 90, their titles at y0 + 56.
  slots (x, width): A 7200/740 (traced render), B 7980/940, C 8960/900, D 9900/940, E 10880/940, F 11860/940.
"""
import numpy as np

ROW = {"hoop": 0, "pedestal": 1, "hood": 2, "kickstand": 3, "scissor": 4, "sidepod": 5, "stalk": 6,
       "lowprofile": 7, "braun": 8, "te": 9}
SLOT = {"A": (7200, 740), "B": (7980, 940), "C": (8960, 900), "D": (9900, 940), "E": (10880, 940), "F": (11860, 940)}
FRAME_H = 900


def slot(design, letter):
    """(x, y, width, height) of a frame slot for a design's row."""
    x, w = SLOT[letter]
    return x, 40 + ROW[design]*1100 + 90, w, FRAME_H


PX = 6.0                      # px per mm in every frame
STYLE = {  # (stroke, fill): the frame A colour key
    "base": ("#868e96", "#e9ecef"), "case": ("#1971c2", "#a5d8ff"), "plate": ("#e8590c", "#ffd8a8"),
    "badge": ("#2f9e44", "#b2f2bb"), "header": ("#0c8599", "#99e9f2"), "rocker": ("#9c36b5", "#eebefa"),
    "boot": ("#e03131", "#ffc9c9"), "plug": ("#495057", "#ced4da"),
}
ops, ids = [], set()


def uid(stem):
    i = 0
    while f"{stem}-{i}" in ids: i += 1
    ids.add(f"{stem}-{i}"); return f"{stem}-{i}"


def poly_el(pts, kind, stem, hole=False):
    pts = np.asarray(pts, float)
    mn = pts.min(0)
    rel = [[round(float(x - mn[0]), 1), round(float(y - mn[1]), 1)] for x, y in pts] + [[round(float(pts[0, 0] - mn[0]), 1), round(float(pts[0, 1] - mn[1]), 1)]]
    st, fi = STYLE[kind]
    return {"id": uid(stem), "type": "line", "x": round(float(mn[0]), 1), "y": round(float(mn[1]), 1),
            "width": round(float(np.ptp(pts[:, 0])), 1), "height": round(float(np.ptp(pts[:, 1])), 1), "points": rel,
            "strokeColor": st, "backgroundColor": "#ffffff" if hole else fi, "fillStyle": "solid",
            "strokeWidth": 1, "roughness": 0, "roundness": None, "polygon": True}


def section_yz(m, x):
    """Slice a world solid on the plane X = x: contours in world (Y, Z)."""
    cs = m.rotate([0, 90, 0]).slice(-x)              # (x, y, z) -> (z, y, -x); slice at new z = -x
    return [[(p[1], p[0]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def project_xz(m):
    """Front elevation (viewer at -Y): silhouette in world (X, Z)."""
    cs = m.rotate([90, 0, 0]).project()             # (x, y, z) -> (x, -z, y); drop the new z
    return [[(p[0], -p[1]) for p in c] for c in cs.simplify(0.05).to_polygons()]


def signed_area(c):
    c = np.asarray(c); return 0.5*np.sum(c[:, 0]*np.roll(c[:, 1], -1) - np.roll(c[:, 0], -1)*c[:, 1])


def draw_contours(contours, kind, stem, to_board):
    """Fill outer contours, paint holes white. A contour is a hole when it sits inside an odd number of others
    (orientation is no help: the section swaps axes)."""
    from matplotlib.path import Path
    cs = [np.asarray(c) for c in contours if len(c) > 2 and abs(signed_area(c)) > 0.05]
    cs.sort(key=lambda c: -abs(signed_area(c)))
    paths = [Path(c) for c in cs]
    els = []
    for i, c in enumerate(cs):
        depth = sum(paths[j].contains_point(c[0]) for j in range(i))
        els.append(poly_el([to_board(*p) for p in c], kind, stem, hole=depth % 2 == 1))
    return els


def text(x, y, t, size=16, stem="t"):
    return {"id": uid(stem), "type": "text", "x": round(x, 1), "y": round(y, 1), "text": t, "fontSize": size}


def dim(p0, p1, label, stem, off=(0, 0), size=15):
    """A two-headed dimension line from p0 to p1 (board coords) with its label beside the middle."""
    (x0, y0), (x1, y1) = p0, p1
    a = {"id": uid(stem), "type": "arrow", "x": round(x0, 1), "y": round(y0, 1), "width": round(x1 - x0, 1),
         "height": round(y1 - y0, 1), "points": [[0, 0], [round(x1 - x0, 1), round(y1 - y0, 1)]],
         "startArrowhead": "arrow", "endArrowhead": "arrow", "strokeColor": "#495057", "strokeWidth": 1, "roughness": 0}
    return [a, text((x0 + x1)/2 + off[0], (y0 + y1)/2 + off[1], label, size, stem)]


def frame(fid, x, y, w, h, title):
    return [{"id": fid, "type": "frame", "x": x, "y": y, "width": w, "height": h}, text(x, y - 32, title, 20, fid + "-t")]


