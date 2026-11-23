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
Printed with the screw joint: the case wobbled in the mortise at 0.25 mm per side. The snap version replaces the screw: two 1.5 mm arms on the tenon, a 0.45 mm barb each, 8.3 mm of flex length (1.1% strain, push-in about 2 N before friction, pull-out about 29 N, above a 20 N plug pull). The mortise is 0.12 per side. The screw version's script and notes are in `archive/hoop-screw-v1/`; its STLs were deleted and are last in commit `1580ce5`. Not printed yet.

## Front-BOOT (replaced)
A rocker key on the base, replaced by the telegraph key below. Its STLs, renders and notes were deleted on 2026-11-22 and are last in commit `1580ce5`. `build_hoop_frontboot.py` stays only as the library the telegraph and the board schematics import; it still runs its checks.

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
