import struct, collections, math
import sys
PATH = sys.argv[1]
d = open(PATH,"rb").read()
n = struct.unpack("<I", d[80:84])[0]
tris=[]; off=84
for _ in range(n):
    nx,ny,nz = struct.unpack("<3f", d[off:off+12]); off+=12
    vs=[struct.unpack("<3f", d[off+12*i:off+12*i+12]) for i in range(3)]; off+=36
    off+=2
    tris.append((vs,(nx,ny,nz)))
print(f"--- {PATH} ---")
print("facets:", len(tris))

q=lambda v: tuple(round(c,5) for c in v)
edges=collections.Counter()
for vs,_ in tris:
    for i in range(3):
        a,b=q(vs[i]),q(vs[(i+1)%3])
        edges[(a,b)]+=1
bad=[e for e,c in edges.items() if c!=1]
open_e=[e for e in edges if (e[1],e[0]) not in edges]
print("directed edges used more than once:", len(bad))
print("unpaired (boundary) edges:", len(open_e))

# signed volume via divergence theorem -> also confirms outward normals
V=0.0
for vs,_ in tris:
    (ax,ay,az),(bx,by,bz),(cx,cy,cz)=vs
    V += (ax*(by*cz-bz*cy) - ay*(bx*cz-bz*cx) + az*(bx*cy-by*cx))/6.0
print(f"signed volume: {V/1000.0:.3f} cm^3  (positive => normals point outward)")

# degenerate / zero-area facets
zero=0
for vs,_ in tris:
    (ax,ay,az),(bx,by,bz),(cx,cy,cz)=vs
    ux,uy,uz=bx-ax,by-ay,bz-az; vx,vy,vz=cx-ax,cy-ay,cz-az
    cr=(uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx)
    if math.sqrt(sum(c*c for c in cr))/2.0 < 1e-9: zero+=1
print("zero-area facets:", zero)

xs=[v[0] for vs,_ in tris for v in vs]; ys=[v[1] for vs,_ in tris for v in vs]; zs=[v[2] for vs,_ in tris for v in vs]
print(f"bbox  X {min(xs):.2f}..{max(xs):.2f}   Y {min(ys):.2f}..{max(ys):.2f}   Z {min(zs):.2f}..{max(zs):.2f}")
ok = not bad and not open_e and V>0 and zero==0
print("WATERTIGHT + CORRECTLY ORIENTED" if ok else "*** MESH PROBLEM ***")
sys.exit(0 if ok else 1)
