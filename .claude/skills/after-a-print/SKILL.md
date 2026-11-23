---
name: after-a-print
description: Handle the result of a real print of a waveshare-round-stand part - get the photo, log it in docs/PRINT-LOG.md, classify the problem, decide the single parameter to change, rebuild and hand off. Use whenever the owner or a contributor reports, describes or photographs a printed part.
---

# After a print

1. **Get a photo** if there is none. A photo of the part in use tells more
   in two seconds than any clearance table: does the badge seat? Where does
   the cable go? What touches what it should not?
2. **Log it first** in `docs/PRINT-LOG.md` (template at its top, newest
   first): part, file, printer and nozzle, material, result **in the
   printer's own words**, photo. Before touching a number. The heading's
   date is what `log =` in `stl/catalog.toml` points at.
3. **Classify:**
   - **fit** (tight, loose, will not snap): one constant. The `tune-fit`
     skill maps the symptom to it.
   - **physically cannot work** (a plug that cannot reach its port): that is
     a spec for the next design, not a note. Design the variant that removes
     it.
   - **cosmetic:** ask whether it matters before spending a build on it.
4. **Update the catalog status** of the printed part in `stl/catalog.toml`
   (`proven`, `printed`, `needs-work`, `failed`) with `log` set to the entry's
   date, then `tools/py build_catalog.py`.
5. Change **one** parameter (`change-a-model` steps 2 to 5), and say which
   number moved and what the next print should show differently.
6. If the board shows this part, record the result there (`update-the-board`,
   board skill `log-a-print`).

The owner's presets for his own prints are in `docs/ELEGOO.md`. A
contributor logs his own printer and settings.
