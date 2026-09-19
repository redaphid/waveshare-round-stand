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

## 1.28 stand with a button post

| file | does |
|---|---|
| `esp32-s3-lcd-1.28_board-36.5mm_stand_BOOT-post.stl` | press the screen → clicks **BOOT** (GPIO0, the user button) |
| `esp32-s3-lcd-1.28_board-36.5mm_stand_RESET-post.stl` | press the screen → clicks **RESET** |

Same stand as the plain 1.28 one plus a Ø3.2 pad on a short column behind the
badge, placed exactly behind the switch. Seat the badge **USB-C chord at the
top**; the post is then behind the lower-right (BOOT) or lower-left (RESET)
of the badge as you look at it. See `PRINTING.md` for how it works.

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

## Fit gauge

| file | does |
|---|---|
| `fit-gauge_groove-3.0-to-6.5mm.stl` | eight slots, 3.0 → 6.5 mm in 0.5 steps. Slot N has N dots under it; slot 1 is at the chamfered end. Slide the badge rim in; the narrowest slot it drops into freely is the groove width to use. ~6 g, prints flat. |

## Pod cup test — print before the pod

| file | does |
|---|---|
| `cup-stand-1.28.stl` | one 1.28 pod cup on a desk base, leaning back 20°. ~16 g. Exported face-up — print as is, no supports, then stand it on its two feet. Badge goes in **USB-C tab down**, then press `trim-ring-1.28.stl` in. |

What to report: does the badge drop onto the ledge without force, does the tab
clear, does the ring press in and hold. Loose or tight: say which.
