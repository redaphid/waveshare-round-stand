# Design decisions

Chronological. Each entry: what was decided, what it replaced, why. When a
decision gets reversed, add a new entry — don't edit the old one.

## Stands

**Slot-wedge, not a cradle or tripod** (09-17). A straight groove holding a round
board contacts it on two lines and cannot rock; prints flat with no supports;
no snap features to fatigue; the round board rotates freely to put connectors
where you want. Replaced the "tripod" idea from the first brief.

**Prism construction** (09-17). One 2D side profile extruded across → trivially
watertight, every dimension is a number in a table. Pure standard library.
Limitation: nothing that varies along the extrusion. Worked around once (the
notch, as three slabs sharing a lower boundary); anything more → manifold3d.

**Groove grips the bare PCB rim** (09-17). The 1.28's 1.6 mm figure is the rim,
not the assembled board. Components are inboard; only the rim enters the groove.

**Two 1.46 variants, not one** (09-17). Waveshare sells the 1.46 with or without
cover glass: Ø44.77/12.30 vs Ø42.58/10.65. Grooves differ by 1.65 mm. Built both
rather than ask which he had; documented how to tell by eye. (He has cover glass
— confirmed from a photo 09-17.)

**Cable notch through the ridge** (09-17). Aaron asked for "notches to run USB-C
cables through". Centre slab is just the base floor; the two shoulders hold the
board. Also shed ~⅓ of the material. Then re-tuned so a cable actually fits under
the rim (4.1–5.4 mm) — the first cut left 2.4 mm.

**Front-elevation preview draws an ellipse** (09-17). A leaning disc projects
foreshortened; the first render drew a circle dipping below the desk. Preview
bugs are documentation bugs.

**Docks** (09-18). He printed the low stand, plugged in his straight cable,
photographed the board lying across it. A straight plug needs ~24 mm below the
rim; there were 5. Lifting the board is the only fix: ridge 16 → 38, notch
widened to 16, groove moved back 3 mm so the plug tip lands inside the base.
Low stands kept for battery / right-angle / side-port use.

**Header pins constrain seating** (09-18). Photo showed a 2×10 header fitted,
pins out the back. On the low stand the 20–50° band either side of bottom is a
hard clash; the dock's steep rear ramp clears everything. Natural orientation
(USB-C down) is safe on both.

## Button post

**Pad on a column, not a post along the board's normal** (09-18). At 20° lean the
normal is 20° below horizontal; a post along it exits the stand out the back
without touching it. Assert on buried length caught it.

**BOOT by default** (09-18). GPIO0 is what firmware reads as a user button;
RESET reboots. RESET twin generated anyway.

**Mechanics** (09-18). Badge leans on the groove's rear lip (5 mm up); switch is
7.7 mm up; a push at the top of the screen is levered ~11× onto the switch. Its
own weight → ~30 gf on the pad, under the ~160 gf a tactile switch needs.

**Switch positions measured from the drawing** (09-18). Disc fitted to R 18.25,
caps found by colour: BOOT back (−9.0, −8.3), RESET (+9.7, −8.3). Overlay saved
so the fit can be checked by eye. Ø3.2 pad forgives ±1 mm.

**1.28 groove 2.4 → 2.7** (09-18). First button-post print: the badge's groove
was slightly too small. Fit 0.8 → 1.1; shared with the plain 1.28 stand.

**…which was the wrong fix** (09-18). His photo shows the 1.28 in a case — the
rim is several mm thick, not 1.6. Fit gauge printed to measure it; the groove
gets the gauge's number, not another guess.

**1.28 groove 5.0, thick 4.7** (09-18). Gauge photo: no case — the display
module itself reaches the rim. Drops into the 5.0 slot. `thick` 4.7 moves the
button post back to meet the switch. Pod 1.28 cups: `seat_t` 1.6 → 4.7, so the
pocket is 7.7 deep (seat + ring) and the trim ring lands on the display module,
not 3 mm proud of it.

## Pod

**Cups on a spine, not a box with holes** (09-18, v2). v1 was a rectangular block
with cylinders subtracted. Zero pillar-pod character. Real pods: the cylinders
are the form, the body joins them.

**Spine on the monitor side, cups cantilevered outboard** (v2). The rail on the
spine's monitor-facing side mates the clip's outer face, so the pod faces you.
Wiring channel down the *back* of the spine. (v1 had the rail on the back and
the channel on the side — the pod would have faced away from the user.)

**Trim rings** (v3). Nothing in v2 stopped a gauge falling forward. Press-fit
ring in front of each gauge, flush with the cup face; also hides the PCB edge.
Standard gauge-pod construction.

**1.46 shoulder grips the glass** (v3). Its brass standoffs would foul a normal
shoulder. The glass overhangs the PCB by 1.1 mm; the shoulder grips that and a
snug Ø42.58+0.5 bore passes the whole stack. The 1.28's bore is Ø33 — past its
buttons, inside the PCB rim.

**Two clips, full-height rail** (v3). A 45 mm clip on a 209 mm cantilever would
rock. Two clips anywhere on the rail; pod slides to height.

**Adjustable clip, 8–32 mm** (v1→). Fixed front jaw with 6 mm bezel lip, sliding
rear jaw on a tongue, M3 lock through a slot in the *top* (the outer face is
taken by the dovetail socket). Spine 20 mm so tongue channel and socket root
have 4 mm between them (was 2 at 18).

**gap12 default** (09-18). Right-angle cables bought. 181 mm vs 209. Drop slot
widened 11 → 16 for the head; a pass-through from each drop slot into the wiring
channel so the lead tucks in whichever way the plug exits. gap26 kept.

**No fillets** (standing). manifold3d has no fillet op. Prints fine; looks
crisper than a moulded pod. Revisit only if he asks.

## Not done / rejected

- **Headless slicing.** ElegooSlicer CLI: `type`/`from` fields and `inherits`
  resolution solved (`flatten_presets.py`), then exit 239 with no diagnostic.
  Dropped on Aaron's say-so; he slices in the GUI.
- **M2 screw retention for the 1.46** in the pod. Would be more robust than the
  ring; needs the three hole coordinates, which the drawing gives only
  partially (23.54 lower spacing). Trim rings chosen instead.
- **Mirroring the pillar's curve.** Explicitly ruled out: "adapted to a modern
  monitor, we don't have to mirror the angle of the pillar".
