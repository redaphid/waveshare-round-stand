# Hoop stand: the USB-only pocketwatch in a gimbal ring

**The case is fused into an open brass-look ring on two trunnions, on a two-tier round base, face 20° back. Crown up: the plug rises out of the crown and the cable loops back and down behind it, like a watch's bow and chain.** Ø76 footprint, 89 mm tall to the top of the plug. **No screw: two snap arms on the neck click into the base.** Rebuild: `~/.venvs/cad/bin/python pocketwatch/stands/hoop/build_hoop.py` from the repo root (82 checks; `--no-render` is faster).

**Why crown up:** the display reads the right way up with no firmware flip. The case sits low, with the glass centre 43 mm above the desk. Crown down would put 22 mm of straight plug plus its bend under the case, which makes the stand about 40 mm taller and top-heavy.

| print | file (`stl/pocketwatch/stands/hoop/`) | orientation | notes |
|---|---|---|---|
| **hoop + case** | `Hoop stand - hoop and case.stl` | bezel down, as exported | one piece; same case as the USB-only build |
| **base** | `Hoop stand - base.stl` | flat, as exported | **100% infill**: it's the ballast |
| **back plate** | `Hoop stand - back plate (button).stl` | flat back down | BOOT button: push the U-shaped tab on the back. `(BOOT hole)` is the stylus-hole alternative; `roomy` variants if a plate runs tight |

No supports on any part, and no hardware. The default mortise is 0.08 per side (0.12 printed loose). The base also comes as `base (looser, 0.12)` and `base (roomier, 0.18)` for a printer that runs tight.

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

## Front-BOOT: press a key on the base (2026-10-13; v2 after the first print)
**Press the ivory key at the front right of the base straight down. BOOT clicks after 2.1 mm of travel at about 3.1 N, and the key bottoms on the lower tier at 3.4 mm.**

**v2, after the first print** ("close to good"; the lever and the hoop flex more than the model says, so the click came too late): the key stop is 0.7 mm deeper (1.0 mm of key to spare after the click at the worst gap, was 0.25), and the nub is bigger, Ø4.4 and 2.0 proud (was Ø3.2, 1.4). Reprint the **base and the rocker** only. A one-piece rocker (`renders/frontboot-*.png`) pivots on a flexure in the tier. Its arm rises behind the case to a nub 0.5 mm off the button plate's flush flexure tab, and the nub pushes that tab, so nothing touches the glass. Rebuild: `~/.venvs/cad/bin/python pocketwatch/stands/hoop/build_hoop_frontboot.py` (103 checks).

| print (`stl/pocketwatch/stands/hoop/`) | notes |
|---|---|
| `Hoop stand - hoop and case.stl`, `Hoop stand - back plate (button).stl` | unchanged. **Must be the button plate**: the BOOT-hole plate won't work |
| `Hoop stand front-BOOT - base.stl` | replaces the base: adds the rocker slot and pocket. 100% infill |
| `Hoop stand front-BOOT - rocker.stl` | 2.3 g, on its side as exported, no supports. Every arm bends along its layers |

**Assembly:** (1) drop the rocker's foot into its pocket 2 mm forward of home, then slide it back so the heel hooks under the ledge. (2) Fit the badge and button plate into the hoop. (3) Push the hoop down its neck until it clicks. The plate slides past the nub at 0.5 mm (0.2 at worst). Once the hoop is in, the rocker can't come out forward or up. **To take the plate off, lift the hoop out first.** From behind, pushing the top of the rocker arm still clicks BOOT.

| number (all asserted) | value |
|---|---|
| lever | nub 27 mm from the pivot, key 28 mm. The pivot is straight below the nub tip, so the nub meets the tab square |
| gap G (nub to tab) 0.2 / 0.5 / 0.8 | touch at 0.2 / 0.55 / 0.9 mm; click at 1.8 / 2.1 / 2.4 mm with 3.0–3.2 N; at the 3.4 mm stop the key takes 7.4 / 6.6 / 5.9 N (model; the printed rocker is softer) |
| push on the switch (and glass on its lip) at the stop | at most 7.1 N, against 2.7 N needed. The arms bend, so overtravel can't crush anything |
| strain | blade 1.4 × 4 × 6 at a 30° tilt: 1.02%; upright arm 1.11%; key arm 1.23%; tab 0.56% |
| stability | tip angle 24.9° with a 1 N cable pull. 7.4 N straight down on the key can't tip it (39°). The press may lean 18° off vertical before the 83 g stand slides (μ 0.3), and leaning that far it still can't tip |
| clearances | 0.4 to the slot all the way to the stop; nub 0.7 off in any direction still hits only the tab; tier walls 1.4–1.8 |

**Honest weaknesses**
- **G is ±0.3**, mostly the tenon's play in the mortise (now 0.08) times a 2.5× lever to the tab. The stop leaves 1.0 mm of key spare at the largest gap, to soak up the flex the first print showed.
- The forces come from a linear beam-and-spring model, not FEA. The switch force (2 N) and the BOOT position (±1 mm) are still guesses.
- Pressing the outer edge of the pad to the stop twists the nub 0.93 mm sideways, against a 1.35 mm margin. A press leaning more than 18° slides the stand; a flat key invites a straight press, and rubber feet would fix it.
- Gravity, the heel hook and the plate retain the rocker, so shaken upside down it could work loose. The blade's fatigue life at 1% strain is untested. The slot leaves a small notch at the back of the tier.

## Telegraph key: the badge leans back 40°, BOOT is a brass key (2026-10-14)
**Press the brass knob at the front. The lever turns on a pin between two posts, and its short rear arm tips up into the button plate's flush BOOT tab. BOOT clicks after 3.2 mm of knob travel (2.6–3.8 across the gap tolerance) at about 1.75 N. At 4.2 mm the lever lands on an anvil, so a hard press goes into the base, never into the switch.** The face leans 40° back (the hoop stand leans 20°), so the badge looks up more. Rebuild: `~/.venvs/cad/bin/python pocketwatch/stands/hoop/build_hoop_telegraph.py` from the repo root (both angles, 196 checks, `--no-render` is faster). `build_hoop.py` is unchanged.

**Choose the lean** (`renders/telegraph-angles.png`):

| lean | glass centre | height | stand footprint | plug | tip angle, 1 N cable pull |
|---|---|---|---|---|---|
| **40° (default)** | 40 mm up | 75 mm | Ø70 | inside the Ø76 base | 24.0° |
| 50° | 37 mm up | 66 mm | Ø75 | 12 mm past the rim | 24.8° |

55° doesn't fit Ø76. At 55° the tilted hoop and neck alone run 75 mm front to back, before the mortise wall and the knob.

| print (`stl/pocketwatch/stands/hoop/`) | orientation | notes |
|---|---|---|
| `Hoop stand telegraph - hoop and case (40 deg).stl` | bezel down | the same hoop, with the tenon cut for the new lean |
| `Hoop stand telegraph - base (40 deg).stl` | flat | **100% infill**: it's the ballast. Has the posts, anvil, back stop and a low plinth round the mortise |
| `Hoop stand telegraph - lever (40 deg).stl` | on its side, as exported | 2.1 g. Every arm and the hairpin spring bend along the layers |
| `Hoop stand telegraph - knob.stl` | upright | snaps onto the lever's split peg |
| `Hoop stand telegraph - pin.stl` | on its flat | Ø3, with a head on one end and a split, barbed end on the other |
| `Hoop stand - back plate (button).stl` | unchanged | **must be the button plate** |

For 50°, use the `(50 deg)` hoop, base and lever. The knob and pin fit both.

**Assembly:**
1. Lower the lever between the posts. The hairpin's foot touches the base first.
2. Push the pin in from the outside (the right) until its split end clicks past the inner post.
3. Press the knob onto the peg until it clicks.
4. Fit the badge and plate into the hoop, then push the hoop down its neck until it clicks. The plate slides past the nub with 0.5 mm to spare (0.2 at worst). **To take the plate off, lift the hoop out first.**

| number (all asserted, 40°) | value |
|---|---|
| lever | nub arm 12.1, knob arm 23.1: **2:1**. The rear arm is 17° steeper than the plate so the pin clears the case rim. The nub then pushes 17° off square and slides 0.1 mm on the tab before the switch bottoms |
| gap G (nub to tab) 0.2 / 0.5 / 0.8 | click at 2.6 / 3.2 / 3.8 mm of knob travel. The anvil stops the knob at 4.2 |
| push on the tab at the stop | at most **7.6 N** at the smallest gap (switch 6.4 + tab spring 1.2), against a limit of 8 |
| why the blade bends | ±0.3 of gap is ±0.6 at the knob. Once the switch bottoms, the front blade (1.5 thick, tapering to 1.0) bends, up to 2.7 mm. It's sized so the worst case stays under 8 N. A 30 N press lands on the anvil |
| strain (PLA, 1% limit for every-press parts) | blade 0.93%, rear arm 0.1%, hairpin 0.3%, plate tab 0.56%. Snap-once parts (limit 1.5%): pin 0.90%, knob peg 0.98%, hoop arms 1.21% |
| pin and posts | 9.5 N on the pin, 7.5 MPa along its layers. The posts see 1.2 MPa across theirs (limit 10) |
| return | the hairpin holds the knob up with 2.1 N·mm, 15× the key's own weight. The heel on the back stop sets the gap |
| stability | tip angle 24.0° with 1 N on the cable. 6 N straight down on the knob can't tip it (26°). A press can lean 19° before the 76 g stand slides (μ 0.3), and leaning that far it still can't tip |
| clearances | 0.4 to the base, posts and hoop through the whole swing. The nub lands on the tab only, even 0.7 off in any direction |
| hoop joint | plinth 10 tall, mortise 8.5 deep, FIT 0.08. Snaps in at 3.6 N; pulling it out takes 54 N (PLA) |

**Honest weaknesses**
- **The blade flexes on purpose.** About 1 mm of the 3.2 mm to the click is the blade bending. A stiffer blade I tried first (0.2 mm/N) put 16 N on the switch at the smallest gap. If the printed blade is softer than the model, the click comes later: there's 0.4 mm of knob travel to spare at the largest gap. If a print doesn't click, lower the anvil (reprint the base) rather than stiffening the blade.
- At the nominal gap the click comes at 3.2 mm, a little over the 2.5–3 target.
- The forces come from linear beam models, not FEA. The switch force (2 N) and the BOOT position (±1 mm) are still guesses. G ±0.3 is assumed, with the pin's 0.15 clearance and the tenon's play counted inside it.
- There are four new prints (base, lever, knob, pin) against the rocker's two, and the pin and knob are small parts.
- At 50° the mortise roof is a 50° overhang. It passes the bridge check but prints as stair-steps. The plug also hangs 12 mm past the rim.
- The hairpin's foot slides about 1.5 mm on the base with every press.
