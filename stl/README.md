# Printable STLs

Three stands, one per board. Names carry the board's outside diameter so the
size is obvious without opening anything.

| file | for | board Ø | stand footprint | material |
|---|---|---|---|---|
| `esp32-s3-lcd-1.28_board-36.5mm_stand.stl` | ESP32-S3-LCD-1.28 (SKU 26541), non-touch | 36.5 mm | 26 × 27 mm, 12 mm tall | 4.6 g |
| `esp32-s3-touch-lcd-1.46-bare_board-42.58mm_stand.stl` | ESP32-S3-Touch-LCD-1.46, **no** cover glass | 42.58 mm | 29 × 35 mm, 16 mm tall | 8.2 g |
| `esp32-s3-touch-lcd-1.46-coverglass_board-44.77mm_stand.stl` | ESP32-S3-Touch-LCD-1.46, **with** cover glass | 44.77 mm | 30 × 36 mm, 16 mm tall | 8.9 g |

The two 1.46 files are **not** interchangeable — the boards are 12.30 mm and
10.65 mm thick respectively, so the grooves differ by 1.65 mm. If you're not
sure which you have, see the "telling them apart" note in [`../BOARDS.md`](../BOARDS.md).

Print flat on the base, no supports. Slicer settings and seating guidance are in
[`../PRINTING.md`](../PRINTING.md).

Regenerate these from source with `python3 ../build_stands.py` (run from the
repo root). Masses are PETG at 1.27 g/cm³.
