---
name: after-a-print
description: Handle the result of a real print of a waveshare-round-stand part — log it, read the photo, decide which single parameter to change, rebuild, ship. Use whenever Aaron reports or photographs a printed part.
---

# After a print

1. **Ask for / look at the photo** if there isn't one. A photo of the part in
   use told more in two seconds than any clearance table. Look for: does the
   board seat? where does the cable go? what's touching what it shouldn't?
2. **Log it first** in `docs/PRINT-LOG.md` (template at the top): part, file,
   presets, result in his words, photo reference. Before touching a number.
3. **Classify:**
   - *fit* (loose/tight): one number — `fit` in `build_stands.py`,
     `RING_PRESS` / `FIT` in `pod/build_pod.py`, `REST_CLR` for the post.
     Loose → −0.3; tight → +0.2. Say which and why.
   - *physically can't work* (like the straight plug): that is a **spec for the
     next part**, not a note. Design the variant that removes it; keep the
     old one.
   - *cosmetic*: ask if he cares before spending a build on it.
4. Change **one parameter**, `rebuild-and-ship`, and tell him which number
   moved and what he should see differently.
5. Presets, for the log: printer `Elegoo Centauri Carbon 2 0.6 nozzle`,
   process `0.30mm Standard @Elegoo CC2 0.6 nozzle - Copy`, filament
   `PRUSA Strontium` (PETG 260/85), textured plate — unless he says otherwise.
