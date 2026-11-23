@AGENTS.md

## Owner's workflow

**Skip this section if you are not Aaron.** It is how the owner works on his
own machines. A contributor commits as himself, opens a PR, and never touches
the paths below.

- **Commit identity:** commit as `Aaron Herres <iam@hypnodroid.com>`
  (`git -c user.name=... -c user.email=... commit`), end the message with the
  `Co-Authored-By` line the session specifies, and push after every verified
  step. The `rebuild-and-ship` skill has the full sequence.
- **Python:** his CAD venv is `~/.venvs/cad`; `tools/py` falls back to it when
  the repo has no `.venv`.
- **Checkout:** WSL distro `survivor`, `~/Projects/waveshare-round-stand`.
  When git misbehaves on Windows, do the git work inside WSL.
- **Windows slicing mirror:** `D:\Projects\waveshare-round-stand`
  (`/mnt/d/Projects/waveshare-round-stand`). Copy the tree there after a
  merge; he slices from it. **`stand.3mf` and every untracked `.3mf` there
  are his**: never overwrite or move them. List what is there that the repo
  does not have before any bulk copy.
- **Printer:** Elegoo Centauri Carbon 2, 0.6 nozzle, on his LAN,
  reachable through the `soul` MCP `centauri__*` tools. It is
  often off. Its problems: `docs/PRINTER-TROUBLE.md`.
- **Material:** he prints the pocketwatch family in **PLA** (since
  2026-10-14). Older notes naming the PETG preset `PRUSA Strontium` are stale.
- **Slicer:** ElegooSlicer in the GUI on Windows. Presets, the headless CLI
  post-mortem and `tools/elegoo/flatten_presets.py`: `docs/ELEGOO.md`.
- **His notes:** his general working rules live in his vault
  (`kb/procedures/working-with-aaron-read-first.md`).
