# Printable STLs

Five files. Names carry the board's outside diameter so the size is obvious
without opening anything, and `DOCK` marks the tall variants.

**Stand or dock?** If you'll run a straight USB-C cable into the 1.46's bottom
port, you need a `DOCK` — the low stands only leave ~5 mm under the rim and a
plug body is ~24 mm. Right-angle lead, battery, or port turned sideways: the low
stand is fine and half the material.

## Low stands

| file | for | board Ø | stand footprint | material |
|---|---|---|---|---|
| `esp32-s3-lcd-1.28_board-36.5mm_stand.stl` | ESP32-S3-LCD-1.28 (SKU 26541), non-touch | 36.5 mm | 26 × 27 mm, 12 mm tall | 4.6 g |
| `esp32-s3-touch-lcd-1.46-bare_board-42.58mm_stand.stl` | ESP32-S3-Touch-LCD-1.46, **no** cover glass | 42.58 mm | 29 × 35 mm, 16 mm tall | 8.2 g |
| `esp32-s3-touch-lcd-1.46-coverglass_board-44.77mm_stand.stl` | ESP32-S3-Touch-LCD-1.46, **with** cover glass | 44.77 mm | 30 × 36 mm, 16 mm tall | 8.9 g |

## Docks (straight plug in the bottom port)

| file | for | board Ø | footprint | material |
|---|---|---|---|---|
| `esp32-s3-touch-lcd-1.46-bare_board-42.58mm_DOCK-straight-plug.stl` | ESP32-S3-Touch-LCD-1.46, **no** cover glass | 42.58 mm | 29 × 37 mm, 38 mm tall | 17.9 g |
| `esp32-s3-touch-lcd-1.46-coverglass_board-44.77mm_DOCK-straight-plug.stl` | ESP32-S3-Touch-LCD-1.46, **with** cover glass | 44.77 mm | 30 × 38 mm, 38 mm tall | 19.8 g |

27 mm clear under the rim — a 24 mm plug body plus room for the cable to turn.
The plug tip lands ~6 mm in from the front; the notch is open both ends, so the
cable exits front or back as you prefer. No dock for the 1.28: its port is on the top chord and
never points at the desk.

The two 1.46 sizes are **not** interchangeable — the boards are 12.30 mm and
10.65 mm thick respectively, so the grooves differ by 1.65 mm. If you're not
sure which you have, see the "telling them apart" note in [`../BOARDS.md`](../BOARDS.md).

Print flat on the base, no supports. Slicer settings and seating guidance are in
[`../PRINTING.md`](../PRINTING.md).

Regenerate these from source with `python3 ../build_stands.py` (run from the
repo root). Masses are PETG at 1.27 g/cm³.
