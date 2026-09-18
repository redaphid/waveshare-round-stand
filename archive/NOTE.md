Superseded files, kept rather than deleted.

- `esp32-s3-touch-lcd-146-stand.stl` — the first 1.46 stand, before it was clear
  the board ships in two cover-glass options. Byte-identical to what is now
  `stl/esp32-s3-touch-lcd-1.46-coverglass_board-44.77mm_stand.stl`,
  before the cable notch was added. Renamed away because an
  unqualified "146-stand" is easy to print by mistake.
- `gen_stand.py` — 1.28-only generator, superseded by `build_stands.py`, which
  reproduces its output exactly.
- `preview-side.png` — 1.28-only preview, superseded by `preview-all.png`.
