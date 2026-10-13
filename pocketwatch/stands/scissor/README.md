# Scissor stand (USB-only pocketwatch)

**The case grows two lugs at about 4:30 and 7:30. On each lug, two flat blades share one M3 screw and open like scissors: the front legs swing 16° forward and the rear legs swing 56° back, each until it hits a stop in a hood over the screw. Standing, the face tips back 20°. Folded, both legs hang flat in the plane of the case, no thicker than the case, with the plug and cable between their crossbars.**

**Why not the sketch's X across the back:** I changed it on purpose. Two feet in a line give no footing front to back, so a third leg was needed anyway. The plug also hangs *in front of* that X, so a downward cable pull tipped it forward. Here the X is seen from the side, the feet still spread sideways, and the front crossbar sits in front of the plug.

| print | file (`stl/pocketwatch/stands/scissor/`) | orientation | supports |
|---|---|---|---|
| **case** | `Scissor stand - case.stl` | bezel down, as exported | none |
| **back plate** | `Scissor stand - back plate (BOOT hole).stl` | flat back down | none |
| **front legs** | `Scissor stand - front legs.stl` | flat face down, arms stand on edge | none |
| **rear legs** | `Scissor stand - rear legs.stl` | flat face down, arms stand on edge | none |

**Hardware:** 2× M3×12 socket or button head screws. They cut their own thread in the lug's Ø2.6 hole.

**Assembly:** 1) Fit the badge and snap in the plate, the same as the USB-only case. 2) Spring the front U open about 5 mm and slip its arms over the hoods onto the lug faces. 3) Put the rear U outside it the same way. 4) Drive one screw per side until the legs swing stiffly. 5) Plug in a straight USB-C cable and lay it back under the rear crossbar.

| number | value |
|---|---|
| standing | glass centre 55 up, plug end 10 up, footprint 54 wide × 71 deep, 46 g with the badge |
| tip angle (weight only) | 30° sideways, 37° back, 41° forward (asserted ≥ 20°) |
| 1 N cable pull | no tip straight down, along the plug, or down-back. A flat tug slides it at 0.22 N; tipping needs 1.15 N or more |
| folded | 60 × 90 × 12.45 (case thickness), screw heads included |
| clearances | 0.4 at every sliding face. Plug, cable, screen and the Ø2 BOOT pin path are all asserted clear |
| assembly flex | 1.0 % strain (front), 0.8 % (rear), asserted < 2 % |

Every one of these is checked in `build_scissor.py` (100 checks): `~/.venvs/cad/bin/python pocketwatch/stands/scissor/build_scissor.py [--no-render]` from the repo root.

**Weaknesses (honest):**
- **Not pocket-sized.** Folded it is 60 × 90 mm, against a bare case of 44 × 44, because the legs have to be longer than the 22 mm plug.
- **Light.** 46 g on a 71 mm footprint. Pressing BOOT or a firm tap on the glass tips it, so hold the case rim when you press BOOT.
- **Cable is not anchored.** A tug drags the stand rather than tipping it. Nothing clamps the cable.
- **Untested guesses.** The thread-forming M3 in PETG and the friction that holds the folded legs have not been tried. Folded legs can swing 18° before the hood stops them.
- **Look.** It reads as a gauge on a folding easel, not as an A-pillar pod. The lug hoods and screw heads stand 8 mm out from the case on each side.

**Scores (1–5):** aesthetics **3**, printability **4**, robustness **3**.

Renders: `renders/hero.png`, `front.png`, `side-section.png`, `back.png` (BOOT pin), `hinge-front-stop.png`, `hinge-rear-stop.png`, `folded.png`, `print-layout.png`.
