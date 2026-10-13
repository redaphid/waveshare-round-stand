# Hoop stand: the USB-only pocketwatch in a gimbal ring

**The case is fused into an open brass-look ring on two trunnions, on a two-tier round base, face 20° back. Crown up: the plug rises out of the crown and the cable loops back and down behind it, like a watch's bow and chain.** Ø76 footprint, 89 mm tall to the top of the plug. **No screw: two snap arms on the neck click into the base.** Rebuild: `~/.venvs/cad/bin/python pocketwatch/stands/hoop/build_hoop.py` from the repo root (82 checks; `--no-render` is faster).

**Why crown up:** the display reads the right way up with no firmware flip. The case sits low, with the glass centre 43 mm above the desk. Crown down would put 22 mm of straight plug plus its bend under the case, which makes the stand about 40 mm taller and top-heavy.

| print | file (`stl/pocketwatch/stands/hoop/`) | orientation | notes |
|---|---|---|---|
| **hoop + case** | `Hoop stand - hoop and case.stl` | bezel down, as exported | one piece; same case as the USB-only build |
| **base** | `Hoop stand - base.stl` | flat, as exported | **100% infill**: it's the ballast |
| **back plate** | `Hoop stand - back plate (button).stl` | flat back down | BOOT button: push the U-shaped tab on the back. `(BOOT hole)` is the stylus-hole alternative; `roomy` variants if a plate runs tight |

No supports on any part, and no hardware. The base also comes as `base (roomier, 0.18)` for a printer that runs tight (the default mortise is 0.12 per side).

## Assembly
1. Put the **badge** in the case from the back, screen first, with the tab in the crown slot. **Snap the plate** in flush.
2. **Push the neck straight down** into the slot in the base, which leans back 20°. The two arms on the tenon flex in, ride over the barbs' ramps and **click** into their notches. A firm push (a few N) does it. To remove, pull the hoop straight up with about 30 N.
3. **Plug the cable** into the crown. Loop it back and press it into the **keyhole groove** at the back of the base. The groove grips 3.5–4.5 mm cable at desk height.
4. **BOOT:** press the U-shaped tab on the back of the plate with a fingertip: the little tab flexes and its post clicks BOOT. (With the `BOOT hole` plate instead, push a Ø2 pin or a SIM tool straight into the hole.) There are 40 mm of clear path behind it, 11 mm to the side of the cable.

## The numbers (all asserted by the script)
| what | value |
|---|---|
| ring | Ø49.6–58.6, section 4.5 in-plane × 7 deep, open 80° over the crown |
| 20 N plug push (worst case of the USB-C spec) | 11.5 MPa, **SF 3.9**, worst-case beam estimate |
| neck under a 1 N cable pull plus a 3 N BOOT press | SF 17. A BOOT press moves the hoop 38 µm |
| layer lines | the stand is a straight extrusion in print, so every member bends along its layers |
| mass | 78 g in all: base 34 g, hoop and case 13 g, plate 5 g, badge 20 g, plug 6 g |
| tip angle with 1 N pulling the cable sideways at the keyhole | **24.2°** (needs ≥ 20). Without the pull it is 48.9° |
| plug body 12 × 8 × 22, plus 5 mm of finger room each side | clear. The nearest finial is 9.7 mm away |
| badge in, plate out, stylus to BOOT, tenon slide-in | each path checked clear |
## Weaknesses (honest)
- **The base has to weigh at least 20 g.** Below 58% of solid, the tip angle drops under 20°. Print it at 100% infill.
- **Unplugging takes a hand on the hoop.** USB-C pull-out force is 8–20 N, and the whole stand weighs 0.77 N.
- **A straight plug stands 22 mm proud** and dominates the top. A right-angle plug pointing backward would be neater, but I haven't checked it against the finials.
- The strength figures are cantilever estimates, not FEA. The BOOT position is still the ±1 mm guess from the case.
- The 20° mortise prints as stair-steps. I picked 0.25 mm of clearance per side for that, and it isn't tested yet.

**Alternate silhouette:** a crescent cantilever arm (`renders/06-alternate-crescent.png`). It's prettier from one side, but one arm carries all the load (SF 2.2 against 3.9), and a BOOT press twists a single arm (I didn't compute how much). Not built.
**Scores:** aesthetics **4**/5 · printability **4**/5 · robustness **4**/5

## Print result (2026-10-13), then the snap
Printed with the screw joint: the case wobbled in the mortise at 0.25 mm per side. The snap version replaces the screw: two 1.5 mm arms on the tenon, a 0.45 mm barb each, 8.3 mm of flex length (1.1% strain, push-in about 2 N before friction, pull-out about 29 N, above a 20 N plug pull). The mortise is 0.12 per side. The screw version is in `archive/hoop-screw-v1/`. Not printed yet.

## Front-BOOT: press a key on the base (2026-10-13, not printed)
**Press the ivory key at the front right of the base straight down. BOOT clicks after 2.1 mm of travel at about 3.1 N, and the key bottoms on the lower tier at 2.7 mm.** A one-piece rocker (`renders/frontboot-*.png`) pivots on a flexure in the tier. Its arm rises behind the case to a nub 0.5 mm off the button plate's flush flexure tab, and the nub pushes that tab, so nothing touches the glass. Rebuild: `~/.venvs/cad/bin/python pocketwatch/stands/hoop/build_hoop_frontboot.py` (103 checks).

| print (`stl/pocketwatch/stands/hoop/`) | notes |
|---|---|
| `Hoop stand - hoop and case.stl`, `Hoop stand - back plate (button).stl` | unchanged. **Must be the button plate**: the BOOT-hole plate won't work |
| `Hoop stand front-BOOT - base.stl` | replaces the base: adds the rocker slot and pocket. 100% infill |
| `Hoop stand front-BOOT - rocker.stl` | 2.3 g, on its side as exported, no supports. Every arm bends along its layers |

**Assembly:** (1) drop the rocker's foot into its pocket 2 mm forward of home, then slide it back so the heel hooks under the ledge. (2) Fit the badge and button plate into the hoop. (3) Push the hoop down its neck until it clicks. The plate slides past the nub at 0.5 mm (0.2 at worst). Once the hoop is in, the rocker can't come out forward or up. **To take the plate off, lift the hoop out first.** From behind, pushing the top of the rocker arm still clicks BOOT.

| number (all asserted) | value |
|---|---|
| lever | nub 27 mm from the pivot, key 28 mm. The pivot is straight below the nub tip, so the nub meets the tab square |
| gap G (nub to tab) 0.2 / 0.5 / 0.8 | touch at 0.2 / 0.55 / 0.9 mm; click at 1.8 / 2.1 / 2.4 mm with 3.0–3.2 N; at the 2.7 mm stop the key takes 5.4 / 4.7 / 3.9 N |
| push on the switch (and glass on its lip) at the stop | at most 5.1 N, against 2.7 N needed. The arms bend, so overtravel can't crush anything |
| strain | blade 1.4 × 4 × 6 at a 30° tilt: 0.82%; upright arm 0.80%; key arm 0.90%; tab 0.56% |
| stability | tip angle 24.9° with a 1 N cable pull. 6 N straight down on the key can't tip it (40°). The press may lean 19° off vertical before the 83 g stand slides (μ 0.3), and leaning that far it still can't tip |
| clearances | 0.4 to the slot all the way to the stop; nub 0.7 off in any direction still hits only the tab; tier walls 1.4–1.8 |

**Honest weaknesses**
- **G is ±0.3**, mostly the tenon's 0.12 play in the mortise times a 2.5× lever to the tab. The stop leaves only 0.25 mm of key spare at the largest gap.
- The forces come from a linear beam-and-spring model, not FEA. The switch force (2 N) and the BOOT position (±1 mm) are still guesses.
- Pressing the outer edge of the pad twists the nub 0.75 mm sideways, against a 1.35 mm margin. A press leaning more than 19° slides the stand; a flat key invites a straight press, and rubber feet would fix it.
- Gravity, the heel hook and the plate retain the rocker, so shaken upside down it could work loose. The blade's fatigue life at 1% strain is untested. The slot leaves a small notch at the back of the tier.
