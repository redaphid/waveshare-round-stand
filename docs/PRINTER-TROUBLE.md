# Printer trouble: Elegoo Centauri Carbon 2

**Summary.** Since June 2026 most prints on the owner's Centauri Carbon 2 (CC2) with the CANVAS multi-filament unit have failed. The first layer does not stick, curls onto the nozzle, or the job stops with a filament error at the toolhead (1243, 1252, 1265).
Nozzles, the plate, the slicer settings and the filament sensor have each been changed or ruled out, one at a time, and it still fails.
The leading suspects are friction or broken filament in the feed path between CANVAS and the extruder gears, and a dirty nozzle tip throwing off the nozzle-touch bed leveling. Neither is proven. The checks below can tell them apart.

This page is for anyone with more printing experience who wants to help debug it, with the owner. It lists what happened, what Elegoo says each error means, what has been tried, and what to check next.

The `debug-the-printer` skill walks a Claude session through these checks with the owner. His slicer presets and slicer notes are in [docs/ELEGOO.md](ELEGOO.md).

## How to read this page

Every fact carries a label and a source tag.

| Label | Meaning |
|---|---|
| **owner** | The owner's own words, quoted. |
| **telemetry** | Read from the printer over its LAN API, or from slicer files. |
| **inference** | An agent's interpretation. Treat it as a guess until a check confirms it. |

Source tags (`[S1]` and so on) are listed in [Sources](#sources). Dates are the owner's local date (UTC-7).

## The machine

| Item | Value | Source |
|---|---|---|
| Printer | Elegoo Centauri Carbon 2 Combo, with CANVAS (4 trays) | owner [S1] |
| Firmware | 02.01.01.13 (2026-11-19) | telemetry [S2] |
| Nozzle now | 0.6 mm hardened steel | owner: "0.6mm hardened" [S1] |
| Nozzle at first | brass, size not recorded | owner, 2026-09-02: "Looks brass to me" [S5] |
| Slicer | ElegooSlicer 1.5.3.5, stock CC2 machine profile, no custom printer preset | telemetry (slicer config) [S2] |
| Bed leveling | Probes by touching the nozzle tip to the plate. The start gcode sets 140 °C, runs `BED_MESH_CALIBRATE` and `G28`, and only then heats to print temperature. Whether the firmware's probe macro wipes the nozzle first is not known. | telemetry (start gcode, 2026-09-04) [S4], inference |
| Plate | Textured plate (the presets set `textured_plate_temp`) | telemetry [S2] |
| External spool path | None used. All filament goes through CANVAS. | owner, 2026-09-04: "I can't avoid using CANVAS." [S4] |

## Timeline

| Date | What happened | Label, source |
|---|---|---|
| 2026-06-20 | "Most of the time, the printing fails. The print head will get clogged, or the pla plastic will snap off in the print head, etc. This wasn't always a problem." Also: "the pla plastic can like warp on the bed. Bending or peeling up." "It's 70 degrees in here". The climate is dry, so damp filament is unlikely. | owner [S6] |
| 2026-06-20 | A separate diagnosis blamed first-layer adhesion. Fix list: wash the plate, recalibrate Z offset, add a brim. Marked done 2026-09-02. | task record [S7] |
| 2026-09-02 | A 20 mm part reported "finished" by the printer, but "looks like nothing printed at all." `filament_detected` read 0 for the whole job. | owner + telemetry [S8] |
| 2026-09-02 | Fibres found on the plate after repeated washing. They land in a new place each time, so they look like a calibration fault. | owner, as recorded by an agent [S4] |
| 2026-09-03 | Plates with several parts failed: the nozzle hit finished parts on travel moves. Printing one object at a time fixed it. Error **707** (toolhead cover detached) followed one failed print, after a blob formed on the head. | telemetry + inference [S4] |
| 2026-09-03 | Small PLA parts printed well from tray 1: 5 of 5 in black, 1 of 4 in red from another tray. | telemetry + owner [S4] |
| 2026-09-04 | Switched to Prusament PETG Ultraglow (glow PETG filled with strontium aluminate) on the 0.6 nozzle, 260 °C / 85 °C. First layers failed: "loose round strands that never bond, balling onto the nozzle." | telemetry + inference [S4] |
| 2026-09-04 | After a hot tip clean, a plate wash and a fresh auto-level, the skirt still failed from the first millimetre. During layer 1 the printer kept sending the head back to the wipe station and scraping off a blob. No error was raised. | telemetry [S4] |
| around 2026-10-02 | Error **1220** (abnormal filament in extruder). Two CANVAS tubes each held a snapped-off piece of filament near the 4-in-1 hub. Cleared by pushing the piece through the hot nozzle with the extrude button. | owner's notes [S9] |
| 2026-10-12 to 10-15 | Pocketwatch cases and plates printed in PLA and were test-fitted. | owner [S10] |
| 2026-10-14 to 10-15 | About 18 of 24 jobs finished on the 0.6 nozzle (PLA, then glow PETG). | telemetry (`print_history`) [S2] |
| 2026-10-15 to 10-31 | Long glow PETG prints at 260 °C / 85 °C. | telemetry [S2] |
| 2026-10-31 to 11-19 | **3 of 21 jobs finished.** Two were tiny glow-PLA test rectangles (11-17), one a 51-minute glow PETG part. Every Elegoo PLA job stopped, most 3 to 13 minutes in (heat, level, first layers). | telemetry [S2] |
| 2026-11-02 to 11-05 | Nozzle sizes changed: 0.2, a 0.4 attempt, back to 0.6. | telemetry [S2] |
| by 2026-11-19 | "I have gone through many, many nozzles. 4 nozzles, testing this. ... I cleaned the nozzle many times." "I have also washed the bed many times." | owner [S1] |
| by 2026-11-19 | Error **1265** seen. Followed Elegoo's 1265 guide, "replacing the filament sensor even". Did not inspect the CANVAS feeder motors "because all 4 of the filaments failed to load. I eventually managed to unclog the canvas 'head' ... which was clogged by something invisible, intermittently." | owner [S1] |
| by 2026-11-19 | "I have problems often where the print will peel off and just stick to the toolhead and I have to abort." | owner [S1] |
| 2026-11-19 | Slicer audit: stock settings, filament ramming off. `debug-back.3mf` matches a file that printed in October except that supports are on. | telemetry [S2] |
| 2026-11-19, run 1 | Conservative "SAFE" presets (below), tray 1 (light blue PLA). Fibres seen on the plate on camera; owner wiped it. During load, `filament_detected` went 1 to 0 to 1 and the job time grew without progress. Owner: "I'm hearing the printer make a repetitive noise". Stopped with **1243** before the first layer. | telemetry + owner [S1][S2] |
| 2026-11-19, run 2 | Tray 4 (purple PLA). Loaded and purged cleanly. The first layer printed but did not stick and left a loose strand. Owner: "it was printing. That's residue from a print". The printer went back to prep, reheated, then stopped with **1252**. | telemetry + owner [S1][S2] |
| 2026-11-22 | Printer did not answer on the LAN (MQTT port closed, other API timed out). Probably powered off. | telemetry [S3] |

**Tray numbers.** The touchscreen counts trays 1 to 4. The LAN API counts 0 to 3. Run 1 is tray 1 on screen (API tray 0). Run 2 is tray 4 on screen (API tray 3). [S2]

## What Elegoo says each error means

All pages checked 2026-11-22. They render with JavaScript, so open them in a browser.

| Code | Elegoo's message | Elegoo's listed causes | Elegoo's fix, in order |
|---|---|---|---|
| [1243](https://wiki.elegoo.com/en/centauri-carbon-2-combo/errorcode-1243) | Filament extrusion failed at the toolhead. Check if the toolhead is clogged. | Wrong hotend (CC1 and CC2 differ); filament ramming enabled in the slicer; tangled spool; extruder gears not meshing enough; hotend clog | Confirm the CC2 hotend. Turn ramming off. Untangle the spool. Gear test: drop the hotend (two 2.5 mm screws, cable stays connected), push filament into the top of the gearbox, set 170 °C in Control > Prepare and press ▽. **Do not load through the CANVAS menu** (it homes the axes with the hotend loose). If no filament comes out, turn the screw at the gearbox's top right counter-clockwise to tighten. If it feeds, clear the nozzle with the needle at 250 °C or replace the hotend kit (B0C241). |
| [1252](https://wiki.elegoo.com/en/centauri-carbon-2-combo/errorcode-1252) | Filament unload failed at the toolhead. The nozzle may be clogged or filament stuck inside the extruder. | Broken filament in the PTFE tube; detection board false trigger; unload took over 15 s and pulled back under 120 mm | Power off and unplug. Check PTFE tubes. Remove the 4-in-1 hub (2.0 and 2.5 mm keys for the cable and tank chain, then two 2.0 mm screws) and check it and the gearbox for broken filament. Push filament by hand and check that the toolhead icon turns green. If not, reinstall, then replace, the detection board. |
| [1265](https://wiki.elegoo.com/en/centauri-carbon-2-combo/errorcode-1265) | Filament detection failed at the toolhead. The filament may be jammed. | Jam in the CANVAS feed assembly; loose assembly with wiring catching the filament; damaged 8-pin wiring or motor; detection board fault | Try another CANVAS port. If another port works, inspect that feeder unit (slots aligned, motor wiring in its clips, reseat the connector). If every port fails, reinstall the detection board, **minding the spring behind it**. Still failing: replace the **board, spring and trigger piece** together. |
| [1220](https://wiki.elegoo.com/en/centauri-carbon-2-combo/errorcode-1220) | Abnormal filament detected in extruder. Please unload manually. | Residue or blockage in the toolhead or 4-in-1 hub; CANVAS feed fault; detection board or its cable | Load and check the toolhead icon turns green. Remove the hub and toolhead housing and look for residue. Check the detection board for dust or debris, and the spring plate behind it. |
| [707](https://wiki.elegoo.com/en/centauri-carbon-2-combo/errorcode-707) | Toolhead front cover detached. | Cover not seated; magnets weak or fallen out | Reseat the cover. Test its three magnets with a steel object. |

There is no 1245 page (404). The owner thinks he may have misremembered that code. [S1]

## What has been tried

| Tried | Result | Label, source |
|---|---|---|
| 4 different nozzles, cleaned many times | Still fails | owner [S1] |
| Plate washed many times with dish soap | Still fails | owner [S1] |
| Elegoo's 1265 guide, new filament detection board | Still fails. Whether the spring and trigger piece were also replaced is not recorded. | owner [S1], inference |
| CANVAS feed head unclogged | All 4 trays load again | owner [S1] |
| New PLA in every tray | Still fails | telemetry + owner's notes [S2] |
| Brim, one object at a time | Fixed the September multi-part collisions, not the first-layer failures | telemetry [S4] |
| Hot tip clean plus fresh auto-level (glow PETG) | Still failed on the skirt | telemetry [S4] |
| SAFE presets (below) | Both runs failed at the feed or the first layer, not mid-print | telemetry [S2] |

**SAFE presets (2026-11-19).** They change speed and flow only. They do not change Z offset, first-layer height or first-layer flow. [S2]

| Preset | Change from stock |
|---|---|
| Process `SAFE 0.30mm @CC2 0.6 HS` (inherits `0.30mm Standard @Elegoo CC2 0.6 nozzle`) | walls 60/80 mm/s, infill 100, travel 200 mm/s (stock 500), accel 4000 (stock 10000), avoid crossing walls on, first layer 20 mm/s, 5 mm outer brim |
| Filament `PLA SAFE 0.6 HS` (inherits `Elegoo PLA @ECC2`) | max flow 10 mm³/s (stock 21), 220 °C, 225 °C first layer, plate 60 °C, 65 °C first layer, z-hop 0.4 mm Normal Lift |

## Hypotheses, ranked

Confidence is an agent's judgment from the evidence above. None is proven.

### Hardware

| # | Hypothesis | For | Against | Confidence |
|---|---|---|---|---|
| H1 | **Friction or broken filament in the feed path between CANVAS and the gearbox.** Candidates: worn or kinked PTFE, a burr or misaligned joint at the 4-in-1 hub, the toolhead filament cutter, fragments left from earlier breaks. | Filament snapped "in the print head" in June [S6]. Two broken strands in CANVAS tubes around 10-02 [S9]. An "invisible, intermittent" CANVAS head clog [S1]. 1243, 1252, 1265 and 1220 all point at the hub, gearbox or detection board on Elegoo's pages. Sensor flicker during load on a new board [S2]. Prusa warns that Ultraglow wears PTFE tubes [S4]. Explains failures before and after the glow filament. | Run 2 loaded and purged cleanly, then failed on adhesion [S2]. The cutter is an inference: nothing yet points at it directly. | Medium |
| H2 | **Dirty nozzle tip during touch-probing makes the first layer too high.** Plastic on the tip touches the plate first, so the printer sets Z too high. Nothing sticks, the strand balls onto the nozzle, and that blob spoils the next probe. | The printer probes at 140 °C, before it heats to print temperature [S4]. The main symptom is "peel off and just stick to the toolhead" [S1]. Run 2's first layer was a loose, unbonded strand after a clean load [S2]. September's PETG failures looked the same [S4]. A worn nozzle wiper is a common complaint on this printer family (community, unverified) [S11]. | Nozzles were cleaned and replaced many times [S1]. But cleaning when cold, or ooze from the 140 °C heat-up, would still leave a film at probe time (inference). | Medium |
| H3 | **Extruder gears slipping or worn.** The gears bite weakly: enough filament to trip the sensor, not enough for a full first-layer line. | The PLA collapse came right after two weeks of glow PETG, which is abrasive [S2]. The gearbox meshing check in Elegoo's 1243 guide has not been done [S2]. Cheap to test. | Failures go back to June, before any glow filament [S6]. The drive gear is reported as hardened tool steel (from Elegoo's gear guide, as summarised in [S2]). Two glow-PLA tests finished on 11-17 [S2]. | Medium-low |
| H4 | **Detection board assembly.** The new board may be seated wrong, or the old spring and trigger piece reused. | Flicker 1 to 0 to 1 on a new board [S2]. Elegoo says to replace board, spring and trigger piece together [1265 page]. | Explains the error codes, not the poor first layers. | Low-medium, as a contributor |
| H5 | **Plate contamination.** Fibres or residue on the plate. | Fibres seen on camera on 11-19 [S2] and found in September [S4]. Weeks at 85 °C with PETG. | Washed many times [S1]. Intermittent at best. | Low |

### Slicer and presets

| # | Hypothesis | For | Against | Confidence |
|---|---|---|---|---|
| H6 | **Hardened steel nozzle runs PLA too cool for the stock flow.** Hardened steel conducts heat worse than brass, so the stock 21 mm³/s at 220 °C is optimistic (inference). This answers the owner's question "is it normal to have these problems with a hardened nozzle?" [S1] | Stock PLA flow is 21 mm³/s on this nozzle [S1]. | June failures were on the original brass nozzle [S5][S6]. The first layer runs at 20 mm/s, far below any flow limit. SAFE capped flow at 10 and still failed. | Low |
| H7 | **Wrong Z offset or first-layer settings.** | Never tuned by hand. Auto-leveling can reset a saved Z offset (community, CC1) [S11]. | Stock profile printed in October [S2]. | Low, but H2 acts through it |
| H8 | **Slicer settings broken by the owner.** | None. | Audit found stock settings. Ramming is off. Old cruft (a PETG slot, odd copied presets) is unrelated to the failing file. | Ruled out for `debug-back.3mf` [S2] |

**One fault or two?** The record fits two linked faults better than one (inference). H1 explains the error codes and the June snapping. H2 explains why the first layer will not stick even when filament loads cleanly. Under-extrusion from H1 or H3 also leaves thin, weak first-layer lines, so the checks below test feed first, then the first layer.

## Next checks, in order

Each step is cheap, and each one rules hypotheses in or out. Do them in this order.

| # | Check | How | Result that confirms or kills |
|---|---|---|---|
| 1 | **Look before touching** | Photograph the nozzle tip and the wiper at room temperature, and the plate after a failed first layer. | Film or blob on the tip, or a flattened or torn wiper: supports H2. Clean tip and good wiper: weakens H2. |
| 2 | **Hand-feel each lane** | Unload. Pull each PTFE tube at the CANVAS side and push filament by hand toward the toolhead. | One lane drags or stops: H1, in that lane. All lanes smooth: H1 is in the hub, gearbox or cutter, or not present. |
| 3 | **100 mm extrude test** | Heat to 220 °C. Mark the filament 120 mm above the toolhead. Extrude 100 mm from the screen. Watch the strand. | About 20 mm left, fat steady strand: feed is fine, so H1 and H3 are unlikely and H2 moves up. Over 25 mm left, clicking, or a thin or wavy strand: H1 or H3. |
| 4 | **Gearbox bench test** (Elegoo 1243) | Drop the hotend, feed at 170 °C with ▽, not the CANVAS menu. Tighten the top-right screw if nothing comes out. | Filament will not come out until tightened: H3 confirmed. |
| 5 | **Open the hub and toolhead** (Elegoo 1252 and 1220) | Remove the 4-in-1 hub and toolhead housing. Look for fragments, shavings, glow dust, a chipped or misaligned cutter, rounded gear teeth. Reseat the detection board and check the spring and trigger piece. | Fragments or burrs: H1. Rounded or dust-packed teeth: H3. Loose spring or old trigger piece: H4. |
| 6 | **Controlled first-layer test** | Heat the nozzle to printing temperature and wipe the tip hot with a brass brush. Clean the plate. Run auto-level. Then print one large single-layer square at stock PLA settings and watch it go down. | Round lines that lift or drag: too high, H2 or H7. Fix with Z offset, -0.05 mm at a time. Translucent or scraped lines: too low. Gappy, thin lines: under-extrusion, back to H1 or H3. Good square: run `debug-back.3mf` next. |
| 7 | **Swap trays** | Print the same file from two trays. | Fails on one tray only: that CANVAS lane or feeder (Elegoo 1265 step 2). Fails on all: shared toolhead path. |
| 8 | **Then the slicer** | Only if 1 to 7 pass, compare stock and SAFE presets on the same file. | Only SAFE prints: stock settings too aggressive for this nozzle (H6). |

The gear parts page says "Centauri Series" without naming the CC2, so confirm fit before ordering ([Dual Extruder Gears for Centauri Series](https://us.elegoo.com/products/dual-extruder-gears-for-centauri-carbon-series)). [S2]

## What the owner can hand over

| Item | Where |
|---|---|
| Preset names | `SAFE 0.30mm @CC2 0.6 HS`, `PLA SAFE 0.6 HS`, and the stock pair `0.30mm Standard @Elegoo CC2 0.6 nozzle` + `Elegoo PLA @ECC2`. The JSON files from ElegooSlicer's user preset folder (`user\default` under the slicer's app-data folder). |
| Test project | `debug-back.3mf` (one part, about 40 x 42 x 6 mm). The October file that printed: `pocketwatch-hoop-stand-works-no-support.3mf`. |
| Gcode of the failed run | `ECC2_0.6_debug-back_PLA SAFE 0.6 HS_0.3_11m38s.gcode`, still on the printer. |
| Photos | Nozzle tip and wiper (cold), the plate after a failed first layer, the strand that came off, gear teeth and hub interior if opened. |
| Video | The first 60 seconds of the first layer, filmed from the front at plate level. The chamber camera cannot see the plate centre. |
| Telemetry fields | `print_status`, `sub_status`, `filament_detected`, `exception_status`, current and total ticks, nozzle and bed temperatures, Z, active CANVAS tray. Capture them every 30 seconds through load, level and layer 1. |
| Error list | The printer's own error history screen, photographed. |

**Telemetry limit.** A finished job status only means the gcode ran. It does not prove plastic came out. The camera looks across the front lip of the plate, so the centre is out of frame. Only someone at the machine can see the first layer. [S8]

## Sources

| Tag | Source | Date |
|---|---|---|
| S1 | Owner's messages, owner's conversation index, session 98033 | 2026-11-19 local |
| S2 | Agent debug journal and print-history summary written during conversation 98033, from `print_history`, `get_status` and slicer files | 2026-11-19 |
| S3 | Live printer query (`get_status`) during this write-up: failed to connect | 2026-11-22 |
| S4 | Print log and handoff notes from another of the owner's projects, and session 42999 | 2026-09-02 to 09-04 |
| S5 | Owner's conversation index, session 39027 | 2026-09-02 |
| S6 | Owner's conversation index, session 221 | 2026-06-20 local |
| S7 | Task "Fix the printer before printing a batch" | created 2026-09-01, done 2026-09-02 |
| S8 | Agent note on job status versus real output | 2026-09-02 |
| S9 | Owner's reference note on the error 1220 broken strand | 2026-10-02 |
| S10 | This repo's `docs/PRINT-LOG.md` | 2026-10-12 to 10-15 |
| S11 | Web search summary, not read in full: [printer-hub, Centauri Carbon known issues](https://printer-hub.ru/en/posts/elegoo-centauri-carbon-known-issues) (CC1, third party); [Elegoo CC2 clogged nozzle](https://wiki.elegoo.com/centauri-carbon-2-combo/troubleshooting/clogged-nozzle) | 2026-11-22 |
| Elegoo | Error pages linked in the error table | checked 2026-11-22 |
