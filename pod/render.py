"""Headless renders of manifold3d solids via matplotlib (no GL needed).
All parts go into ONE depth-sorted collection so solids occlude each other."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def to_tris(man):
    m = man.to_mesh()
    v = np.asarray(m.vert_properties)[:, :3]; f = np.asarray(m.tri_verts)
    return v[f]

def render(parts, path, elev=18, azim=-55, title="", figsize=(9, 9), light=(-0.45, -0.75, 0.5), zoom=1.0):
    """parts: list of (manifold, rgb)."""
    fig = plt.figure(figsize=figsize, dpi=110); ax = fig.add_subplot(111, projection="3d")
    L = np.array(light, float); L /= np.linalg.norm(L)
    T_all, C_all = [], []
    for man, rgb in parts:
        T = to_tris(man)
        if len(T) == 0: continue
        n = np.cross(T[:, 1]-T[:, 0], T[:, 2]-T[:, 0]); n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
        shade = 0.30 + 0.70*np.clip(n @ L, 0, 1) + 0.12*np.clip(n[:, 2], 0, 1)     # key light + sky
        T_all.append(T); C_all.append(np.clip(np.array(rgb)[None, :]*shade[:, None], 0, 1))
    T = np.concatenate(T_all); C = np.concatenate(C_all)
    pc = Poly3DCollection(T, facecolors=C, edgecolors="none", zsort="average"); ax.add_collection3d(pc)
    V = T.reshape(-1, 3); c = (V.max(0)+V.min(0))/2; r = (V.max(0)-V.min(0)).max()/2*1.02/zoom
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    if title: fig.suptitle(title, fontsize=11, y=0.93)
    fig.subplots_adjust(0, 0, 1, 1); fig.savefig(path, facecolor="white"); plt.close(fig); print("wrote", path)
