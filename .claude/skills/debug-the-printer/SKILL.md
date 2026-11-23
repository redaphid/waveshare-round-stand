---
name: debug-the-printer
description: Help the owner work through the problems with his own 3D printer, using docs/PRINTER-TROUBLE.md as the record - read what is known, pick the next test, have him run it, log what happened. Use when the owner mentions his printer failing, jamming, under-extruding, not detecting filament, or asks for help debugging it; also when a contributor offers to help with it.
---

# Debug the owner's printer

The contributor knows printers better than the owner. This skill makes that
help land: one test at a time, every result written down, nothing guessed
from memory.

1. **Read `docs/PRINTER-TROUBLE.md` in full.** It holds the printer, the
   symptoms, what has been tried and the result of each try. Do not suggest
   a test it already records, unless you say why a repeat is worth it.
2. **State one hypothesis** in a sentence, and the one observation that
   would confirm or kill it (a photo of the nozzle, a cold pull, a test
   print, a reading from the printer's screen or log).
3. **Ask the owner for exactly that,** with the steps to take it. One
   message, one test. He may be on his phone.
4. **"The job ran" is not "a part came out".** A finished status, a
   progress bar at 100 % or a printer that says it detected filament proves
   nothing about plastic on the bed. Ask for a photo of the bed.
5. **Log every result** in `docs/PRINTER-TROUBLE.md` before you interpret
   it: date, the test, what happened in his words, the photo. Then your
   reading of it, labelled as inference.
6. When a fix works, add a short **Resolved** entry (what it was, what fixed
   it), keep the history, and print the bore fit gauge as the first proof
   that parts come out right.

Owner-only: if this session is the owner's own and has his printer's tools,
`CLAUDE.md` (section *Owner's workflow*) says how to reach the printer. A
contributor's session never needs that; it works from his reports.
