---
name: start-here
description: First session on a fresh clone of waveshare-round-stand. Sets up the Python toolchain, builds and checks every model, shows the featured pocketwatch case and telegraph key, offers to connect the draw board, then asks what the person wants to print. Use when someone has just cloned the repo, says "get me started", "what is this", "set this up", or asks what to print first.
---

# Start here

Goal: within a few minutes the person has a working build, knows the two
featured models, and has told you what he wants to print. He knows 3D
printing better than the owner; explain this repo, not printing.

1. **Read `AGENTS.md`** in full. It holds the answers this skill points at.
2. **Set up.** From the repo root:
   ```
   ./setup.sh
   ./build_all.sh --no-render
   ```
   `setup.sh` needs Python 3.11+; if it says none was found, give him the
   one-line install for his OS from AGENTS.md *Setup* and stop there.
   `build_all.sh` must end with `== OK.` and `0 broken`. If a check fails on
   a fresh clone, that is a repo bug: report the `[FAIL]` line, do not patch
   around it.
3. **Check the catalog is in step:** `./tools/py build_catalog.py --check`.
4. **Show the two featured models,** pocketwatch case first:
   - open `pocketwatch/renders/front.png` and
     `pocketwatch/renders/usb-exploded.png`;
   - then `pocketwatch/stands/hoop/renders/telegraph-01-hero.png` and
     `telegraph-section-pressed.png`.
   Look at each image before describing it. Say each one's status from
   `stl/catalog.toml` (plate proven; case needs-work with the fix unprinted;
   telegraph printed on the owner's word, details unrecorded).
5. **Offer the draw board** (one sentence): a zoomable, public, read-only
   schematic. If he wants it, give him the `claude mcp add` line from
   AGENTS.md *The draw board*.
6. **Ask what he wants to do,** as one question with three options:
   - print the pocketwatch case (start with the bore fit gauge: the
     `calibrate-my-printer` skill, then `print-a-part`);
   - change a model (the `change-a-model` skill);
   - settle the open dimensions with the owner (`settle-dimensions`).

Do not dump the unknowns table or the repo map on him. Offer them if he asks.
