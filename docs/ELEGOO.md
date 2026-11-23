# The owner's Elegoo

**Owner-only notes.** Nothing in this repo needs an Elegoo; contributors can
skip this page. It holds everything specific to the owner's printer and
slicer, so no other doc has to.

## The printer

| item | value |
|---|---|
| printer | Elegoo Centauri Carbon 2 Combo, with the CANVAS 4-tray unit |
| nozzle | 0.6 mm hardened steel (brass at first) |
| plate | textured |
| material | **PLA** for the pocketwatch family since 2026-10-14; the September wedge stands were PETG |
| state | most prints have failed since June 2026: [docs/PRINTER-TROUBLE.md](PRINTER-TROUBLE.md) |

An agent on the owner's machine reaches the printer through his MCP tools
(`centauri__get_status`, `centauri__print_history`, `centauri__upload_file`,
`centauri__start_print`). Only sliced `.gcode` prints. A connection error
that says the MQTT port is closed and the other API did not answer means
the printer is **off**, not misconfigured. Ask before assuming anything else.

## Slicer and presets

**ElegooSlicer 1.5.3.5** (a fork of OrcaSlicer 2.4.2), in the GUI on Windows.
User presets live under `%APPDATA%\ElegooSlicer\user\default\` in
`machine`, `process` and `filament` folders.

| use | printer | process | filament |
|---|---|---|---|
| **pocketwatch family, PLA** (the stock pair; inferred from the 2026-11-19 slicer audit) | `Elegoo Centauri Carbon 2 0.6 nozzle` | `0.30mm Standard @Elegoo CC2 0.6 nozzle` | `Elegoo PLA @ECC2` |
| conservative test (2026-11-19) | same | `SAFE 0.30mm @CC2 0.6 HS` | `PLA SAFE 0.6 HS` |
| September wedge stands, PETG (stale) | same | `0.30mm Standard @Elegoo CC2 0.6 nozzle - Copy` | `PRUSA Strontium` |

`PRUSA Strontium` inherits `Elegoo PETG PRO @ECC2`: **PETG, 260 °C nozzle,
85 °C bed**, despite the name. What the SAFE presets change, and why:
[PRINTER-TROUBLE.md](PRINTER-TROUBLE.md#what-has-been-tried).

Print every part as exported, flat, with no supports. The default 2 walls
and 15% infill are enough, except the hoop and telegraph bases: **100%
infill**, they are the ballast.

## `tools/elegoo/`: headless slicing, unfinished

Driving `elegoo-slicer.exe` headless from WSL was tried and dropped; the
owner slices in the GUI. Two obstacles were solved and live in
`tools/elegoo/flatten_presets.py`:

1. User preset JSONs have no `type` field, so the CLI says *"unknown config
   type"*. Adding `"type": "process"` (and so on) fixes it. Keep
   `"from": "User"`: without it the CLI says *"from unsupported"*.
2. The CLI does not resolve a preset's `inherits` chain when handed a
   standalone file. Parent-only settings (`layer_gcode`,
   `use_relative_e_distances`) vanish and validation fails (*"Relative
   extruder addressing requires ... G92 E0"*). `flatten_presets.py` walks
   and merges the chain. **Scope it to the Elegoo vendor folder**: names like
   `fdm_machine_common` exist in every vendor, and a global index resolves
   them to another printer.

Not solved: with fully flattened presets the CLI exits **239 with no output,
even at `--debug 5`**. The exe also swallows stdout, so redirect it to a
file. If it matters again, try `--datadir` pointing at the app-data folder
with presets referenced by name, or slice a `.3mf` project exported from the
GUI (it carries `Metadata/project_settings.config`).

From WSL, Windows executables run but want Windows paths (`D:\...`) as
arguments, and `/mnt/c` and `/mnt/d` are slow for recursive globs.
