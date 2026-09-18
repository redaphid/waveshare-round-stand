#!/usr/bin/env python3
"""
ElegooSlicer's CLI does not resolve a preset's `inherits` chain when the
preset is handed to it as a standalone file -- so settings defined only on
the parent (layer_gcode, use_relative_e_distances, ...) silently vanish and
slicing dies on a validation error. This walks each chain and emits a
fully flattened preset instead.
"""
import json, os, sys, glob

RES  = "/mnt/d/tools/ElegooSlicer/resources/profiles"
USER = "/mnt/c/Users/hypnodroid/AppData/Roaming/ElegooSlicer/user/default"
OUT  = "/mnt/d/tmp/waveshare-stand/presets"

# index every system preset by its `name`
# Scope the index to the Elegoo vendor. Names like "fdm_machine_common" are
# reused by many vendors, so a global index silently resolves a parent to the
# wrong printer's preset.
index = {}
for path in glob.glob(os.path.join(RES, "Elegoo", "**", "*.json"), recursive=True):
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    n = d.get("name")
    if isinstance(n, str) and ("inherits" in d or "type" in d or "from" in d):
        index.setdefault(n, (path, d))
print(f"indexed {len(index)} system presets")

CHAIN = []

def resolve(d, typ, seen=None):
    seen = seen or set()
    parent_name = d.get("inherits")
    if not parent_name:
        base = {}
    else:
        if parent_name in seen:
            raise RuntimeError(f"inherits cycle at {parent_name}")
        seen.add(parent_name)
        hit = index.get(parent_name)
        if hit is None:
            raise RuntimeError(f"cannot resolve parent preset {parent_name!r} "
                               f"within the Elegoo vendor profiles")
        CHAIN.append(parent_name)
        base = resolve(hit[1], typ, seen)
    merged = dict(base)
    for k, v in d.items():
        if k in ("inherits", "from"):
            continue
        merged[k] = v
    return merged

def build(src, typ, dst, chain_note):
    global CHAIN
    CHAIN = []
    d = json.load(open(src, encoding="utf-8"))
    flat = resolve(d, typ)
    flat["type"] = typ
    flat.pop("inherits", None)
    flat["from"] = "User"   # CLI rejects a preset with no `from`
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, dst)
    json.dump(flat, open(p, "w", encoding="utf-8"), indent=2)
    print(f"\n{dst}  ({chain_note})")
    print(f"  name   : {flat.get('name')}")
    print(f"  keys   : {len(flat)}  (was {len(d)})")
    print(f"  chain  : {' <- '.join(CHAIN) if CHAIN else '(none)'}")
    return flat

m = build(f"{RES}/Elegoo/machine/ECC2/Elegoo Centauri Carbon 2 0.6 nozzle.json",
          "machine", "machine.json", "system")
print(f"  nozzle : {m.get('nozzle_diameter')}")
print(f"  rel E  : {m.get('use_relative_e_distances')}")
lg = m.get("layer_gcode", "")
print(f"  layer_gcode has G92 E0: {'G92 E0' in str(lg)}")
print(f"  bed    : {m.get('printable_area', [])[:2]} ... ")

p = build(f"{USER}/process/0.30mm Standard @Elegoo CC2 0.6 nozzle - Copy.json",
          "process", "process.json", "your user copy")
print(f"  layer  : {p.get('layer_height')}  first: {p.get('initial_layer_print_height')}")
print(f"  walls  : {p.get('wall_loops')}  infill: {p.get('sparse_infill_density')}")

f = build(f"{USER}/filament/PRUSA Strontium.json",
          "filament", "filament.json", "your user copy")
print(f"  type   : {f.get('filament_type')}  nozzle T: {f.get('nozzle_temperature')}")
print(f"  bed T  : {f.get('hot_plate_temp')}")
