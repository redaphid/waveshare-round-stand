# Board reference

Everything here was read off the outline drawings in `reference/`. Waveshare
states none of it in page text — the product pages say only "tiny size" and
point at an image.

## ESP32-S3-LCD-1.28 (SKU 26541)

Non-touch, GC9A01 driver. This is the board from Waveshare order
`260713-003325-E0` (12 Jul 2026, 10 pcs).

| feature | value |
|---|---|
| PCB outline | **round, R 18.25 → Ø 36.5 mm** |
| PCB thickness | 1.6 mm (standard 2-layer; not stated on the drawing) |
| flat chord | 18.37 mm wide, at the top |
| USB-C | 12.81 mm wide, sits on the chord, **inserts sideways/upward** |
| active display | **Ø 32.4 mm**, 240 × 240 |
| headers | H1 + H2, 1.27 mm pitch, 20 pins each, ~27.00 mm outer span |
| buttons | BOOT and RESET, lower left and lower right |
| battery | MX1.25 2-pin |

### Pin map

`H1` (left, pins 1–20) and `H2` (right, pins 1–20), viewed from the front:

| H1 odd | | | H1 even | | H2 odd | | | H2 even |
|---|---|---|---|---|---|---|---|---|
| GP36 | 1 | 2 | GP46 | | GP5 | 1 | 2 | GP13 |
| GP35 | 3 | 4 | GP45 | | GP4 | 3 | 4 | GP12 |
| GP34 | 5 | 6 | GP42 | | GP3 | 5 | 6 | GP11 |
| GP33 | 7 | 8 | GP41 | | GP2 | 7 | 8 | GP10 |
| GP21 | 9 | 10 | GP40 | | GP1 | 9 | 10 | GP9 |
| GP18 | 11 | 12 | GP39 | | GP0 | 11 | 12 | GP8 |
| GP17 | 13 | 14 | GP38 | | RUN | 13 | 14 | GP7 |
| GP16 | 15 | 16 | GP37 | | BOOT | 15 | 16 | GP6 |
| GP15 | 17 | 18 | VSYS | | ADC_AVDD | 17 | 18 | VSYS |
| GP14 | 19 | 20 | GND | | GND | 19 | 20 | GND |

Fixed-function pins:

| pin | signal | |
|---|---|---|
| GP1 | BAT_ADC | battery voltage, divided by 2 |
| GP6 / GP7 | IMU_SDA / IMU_SCL | I²C to the QMI8658C |
| GP8 | LCD_DC | command/data select |
| GP9 | LCD_CS | chip select |
| GP10 | LCD_CLK | SPI clock |
| GP11 | LCD_DIN | SPI MOSI |
| GP12 | LCD_RST | reset |
| GP40 | LCD_BL | backlight |
| GP47 / GP48 | IMU_INT1 / IMU_INT2 | IMU interrupts |

## How the two compare

Worth stating plainly, because "1.28 vs 1.46" sounds like a bigger jump than it
is. Those numbers are screen diagonals in inches; the boards around them are
much closer in size than the thickness difference suggests.

| | 1.28 | 1.46 | delta | ratio |
|---|---|---|---|---|
| active screen | 32.40 | 36.96 | +4.56 mm | 1.14× |
| PCB diameter | 36.50 | 42.58 | **+6.08 mm** | 1.17× |
| outermost (1.46 = cover glass) | 36.50 | 44.77 | +8.27 mm | 1.23× |
| thickness at the rim | 1.60 | 12.30 | +10.70 mm | **7.69×** |

The screen ratio 36.96 / 32.40 = 1.141 matches the name ratio 1.46 / 1.28 =
1.141 exactly, which is a useful cross-check that both drawings were read right.

So the 1.46 is a **17 % wider PCB** — noticeable, not dramatic. The real
difference is depth. And note the 1.28's 1.6 mm is the *bare PCB rim*, which is
all the groove ever grips; its assembled height with headers and USB-C is far
more than that. The 1.46's 12.30 mm, by contrast, is the whole stack, because
its glass and PCB are laminated into one puck.

## ESP32-S3-Touch-LCD-1.46

Capacitive touch, 412 × 412, ESP32-S3R8. Adds a QMI8658 IMU, PCF85063 RTC, TF
slot, speaker and microphone.

**It ships in two cover-glass options, and they are different parts.** Check
yours before printing a stand — the groove differs by 1.65 mm.

| | with cover glass | without cover glass |
|---|---|---|
| front element | round glass disc, **Ø 44.77** | rounded-rect panel, **39.36 × 41.53** |
| widest part | the glass, Ø 44.77 | **the PCB**, Ø 42.58 |
| total stack | **12.30 mm** | **10.65 mm** |
| secondary thickness dim | 11.00 | 9.33 |
| active display | Ø 36.96 | Ø 36.96 |
| PCB | Ø 42.58 / 41.33 | Ø 42.58 / 41.33 |
| stand to print | `...-coverglass.stl` | `...-bare.stl` |

**Telling them apart:** the cover-glass version has a glossy black disc that
overhangs the PCB all the way round and hides the panel edge. The bare version
shows the panel's flex tail at the bottom and the PCB rim sticks out past the
panel on the left and right.

Common to both:

| feature | value |
|---|---|
| mounting | 3 × **M2** holes |
| USB-C | bottom edge, **inserts downward** — see the orientation note in `PRINTING.md` |
| hole spacing | 23.54 mm between the two lower holes |
| other datums | 8.32, 10.41, 31.17, 32.70, 41.33, 42.58 |

### Pin map — single 20-pin header

| odd | | | even |
|---|---|---|---|
| GP13 | 1 | 2 | GP17 |
| GP12 | 3 | 4 | GP16 |
| RXD | 5 | 6 | GP14 |
| TXD | 7 | 8 | GP3 |
| GND | 9 | 10 | GP1 |
| 3V3 | 11 | 12 | GP0 |
| SDA | 13 | 14 | DP |
| SCL | 15 | 16 | DN |
| GND | 17 | 18 | GND |
| BAT | 19 | 20 | 5V |

`DP`/`DN` are the USB data pair; `SDA`/`SCL` are the external I²C.
