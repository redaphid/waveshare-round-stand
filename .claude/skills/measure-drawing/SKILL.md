---
name: measure-drawing
description: Measure an undimensioned feature (switch, connector, hole) off a vendor's board drawing by fitting a known dimension and locating the feature by colour, producing a verifiable overlay. Use when a board drawing shows a feature but gives no number for it.
---

# Measure a feature off a drawing

Worked for the 1.28's BOOT/RESET switches (±0.5 mm). System `python3` has
numpy, scipy, PIL, matplotlib.

1. **Calibrate.** Threshold the PCB colour (blue: `b>90 & b>r+40 & b>g+15`),
   take the centroid as the disc centre and the 99.5th-percentile radius as
   the disc edge. Divide by the known radius (e.g. 18.25) → px/mm. Print it.
2. **Find the feature.** Threshold for its colour (white caps: all channels
   > 195), restrict to a radius band and a half of the disc where it must be,
   `scipy.ndimage.label`, keep blobs by area and by size in mm. **Print every
   candidate** with its mm position, size, radius and angle from bottom — pick
   by eye from that list, don't trust a size filter alone (it picked one blob
   for both switches the first time).
3. **Convert.** Back-view drawing → front-view coordinates negate x. State
   which view every number is in.
4. **Save an overlay** under `reference/`: the drawing, the fit circle, a 2 mm
   grid, circles on the detected features with their mm labels. View it. This
   is what lets the number be trusted later.
5. Feed the numbers into the model with a **tolerance** the geometry forgives
   (a Ø3.2 pad for a ±1 mm switch position) and record the source in the
   script's docstring.

Template: the measurement block in the 2026-09-18 conversation is reproduced
in spirit by `build_stand_button.py`'s docstring; the overlay is
`reference/esp32-s3-lcd-1.28-switch-positions.png`.
