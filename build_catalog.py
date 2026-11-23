"""Check stl/catalog.toml against the STLs on disk and docs/PRINT-LOG.md, then write stl/README.md from it.

    python3 build_catalog.py           check, then write stl/README.md
    python3 build_catalog.py --check   check, and fail if stl/README.md is not what the catalog generates

Exits non-zero, listing every problem, if an STL has no catalog row, a row names a missing file, or a
status lacks its print-log entry. Standard library only (Python 3.11+).
"""
import hashlib, os, re, sys, tomllib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STL = ROOT / "stl"
CATALOG = STL / "catalog.toml"
README = STL / "README.md"
LOG = ROOT / "docs" / "PRINT-LOG.md"

STATUS = {   # order = README order; text is the legend
    "proven":     "printed and logged as fitting or working",
    "printed":    "printed; the owner says it works, but no fit details are logged",
    "needs-work": "printed, changes requested; the row says whether this file already has them",
    "failed":     "printed and did not work",
    "unprinted":  "never printed: a design that has passed only its script's checks",
}
PRINTED = {"proven", "printed", "needs-work", "failed"}
BOARDS = {"1.28", "1.46 cover glass", "1.46 bare", "any"}
FAMILY_KEYS = {"id", "name", "dir", "about", "board", "material", "script", "edit", "readme", "renders",
               "featured", "also", "parts"}
PART_KEYS = {"file", "what", "status", "log", "fixed", "print", "note", "sets", "board", "script", "edit",
             "material", "render"}


def load():
    with open(CATALOG, "rb") as f:
        return tomllib.load(f)["family"]


def boards(v):
    return [v] if isinstance(v, str) else list(v)


def problems(families):
    bad = []
    log_dates = set(re.findall(r"^## (\d{4}-\d{2}-\d{2})", LOG.read_text(), re.M))
    rows = {}
    ids = Counter(f["id"] for f in families)
    bad += [f"family id {i!r} used {n} times" for i, n in ids.items() if n > 1]
    for fam in families:
        fid = fam["id"]
        bad += [f"{fid}: unknown family key {k!r}" for k in fam.keys() - FAMILY_KEYS]
        bad += [f"{fid}: missing {k!r}" for k in ("name", "dir", "about", "board", "material", "renders")
                if k not in fam]
        for path in [fam.get("readme"), fam.get("script"), *fam.get("renders", [])]:
            if path and not (ROOT / path).exists():
                bad.append(f"{fid}: {path} does not exist")
        for part in fam["parts"]:
            name = part.get("file", "?")
            where = f"{fid}: {name}"
            bad += [f"{where}: unknown key {k!r}" for k in part.keys() - PART_KEYS]
            if name in rows:
                bad.append(f"{where}: listed twice")
            rows[name] = (fam, part)
            if not (STL / name).is_file():
                bad.append(f"{where}: no such file in stl/")
            if fid == "fit-gauges" and not {"render", "sets"} <= part.keys():
                bad.append(f"{where}: a fit gauge needs `render` and `sets`")
            if part.get("render") and not (ROOT / part["render"]).exists():
                bad.append(f"{where}: render {part['render']} does not exist")
            if not name.startswith(fam["dir"] + "/"):
                bad.append(f"{where}: not in the family folder {fam['dir']}/")
            st = part.get("status")
            if st not in STATUS:
                bad.append(f"{where}: status {st!r} is not one of {', '.join(STATUS)}")
            if st in PRINTED and part.get("log") not in log_dates:
                bad.append(f"{where}: status {st} needs `log`, the date of a docs/PRINT-LOG.md entry "
                           f"(got {part.get('log')!r})")
            if st == "unprinted" and "log" in part:
                bad.append(f"{where}: unprinted, yet cites a log entry")
            if (st == "needs-work") != ("fixed" in part):
                bad.append(f"{where}: `fixed` is required for needs-work and only for it")
            for b in boards(part.get("board", fam["board"])):
                if b not in BOARDS:
                    bad.append(f"{where}: board {b!r} is not one of {sorted(BOARDS)}")
            script, edit = part.get("script", fam.get("script")), part.get("edit", fam.get("edit"))
            if not script or not edit:
                bad.append(f"{where}: needs `script` and `edit`, on the row or its family")
            elif not (ROOT / script).exists():
                bad.append(f"{where}: script {script} does not exist")
    for fam in families:
        for name in fam.get("also", []):
            if name not in rows:
                bad.append(f"{fam['id']}: `also` names {name}, which has no row")
    on_disk = {p.relative_to(STL).as_posix() for p in STL.rglob("*") if p.suffix.lower() == ".stl"}
    bad += [f"stl/{n}: on disk but has no catalog row" for n in sorted(on_disk - rows.keys())]
    by_hash = defaultdict(list)
    for name in sorted(rows.keys() & on_disk):
        by_hash[hashlib.sha256((STL / name).read_bytes()).hexdigest()].append(name)
    same = {n: [m for m in g if m != n] for g in by_hash.values() if len(g) > 1 for n in g}
    for g in by_hash.values():
        statuses = {rows[n][1]["status"] for n in g}
        if len(statuses) > 1:
            bad.append(f"byte-identical files disagree on status ({', '.join(sorted(statuses))}): {'; '.join(g)}")
    return bad, same


def target(path):
    """A link target relative to stl/README.md, in <...> so spaces and parentheses in file names work."""
    return "<" + os.path.relpath(ROOT / path, STL).replace(os.sep, "/") + ">"


def link(path, text=None):
    return f"[{text or Path(path).name}]({target(path)})"


def image(fam, path):
    return f"![{fam['name']}]({target(path)})"


def stl_link(name):
    return link(f"stl/{name}", Path(name).stem)


def evidence(part):
    """The print-log citation and, for needs-work, whether this file already has the requested change."""
    bits = []
    if "log" in part:
        bits.append(f"*Log {part['log']}:* {part['note']}" if part.get("note") else f"*Log {part['log']}.*")
    elif part.get("note"):
        bits.append(part["note"])
    if part["status"] == "needs-work":
        bits.append("**The requested change is in this file, unprinted.**" if part["fixed"]
                    else "**The requested change is not made yet.**")
    return " ".join(bits)


def notes(fam, part, same):
    bits = [part["what"], evidence(part)]
    if part.get("print"):
        bits.append(f"*Print:* {part['print']}.")
    if part.get("script") or part.get("edit"):
        script = part.get("script", fam.get("script"))
        bits.append(f"*Change it:* {link(script, Path(script).name)}, {part.get('edit', fam.get('edit'))}.")
    if part.get("board"):
        bits.append(f"*Board:* {' + '.join(boards(part['board']))}.")
    if part["file"] in same:
        bits.append("Same file as " + ", ".join(Path(m).stem for m in same[part["file"]]) + ".")
    return " ".join(b for b in bits if b)


def family_block(fam, same, hero):
    order = list(STATUS)
    parts = sorted(fam["parts"], key=lambda p: order.index(p["status"]))
    out = [f"### {fam['name']}", ""]
    if hero:
        out += [image(fam, fam["renders"][0]), ""]
    out += [fam["about"], ""]
    facts = [f"**Board:** {' + '.join(boards(fam['board']))}", f"**Material:** {fam['material']}",
             f"**Folder:** {link('stl/' + fam['dir'], fam['dir'] + '/')}"]
    out += [" · ".join(facts), ""]
    out += [f"**Change it:** {link(fam['script'], Path(fam['script']).name)}, {fam['edit']}.", ""]
    more = [link(r, Path(r).stem) for r in fam["renders"][1 if hero else 0:]]
    if fam.get("readme"):
        more.insert(0, link(fam["readme"], "design notes"))
    if more:
        out += ["**More:** " + ", ".join(more), ""]
    if fam.get("also"):
        out += ["**Also print:** " + ", ".join(stl_link(n) for n in fam["also"]), ""]
    out += ["| status | file |", "|---|---|"]
    out += [f"| **{p['status']}** | **{stl_link(p['file'])}**<br>{notes(fam, p, same)} |" for p in parts]
    return out + [""]


def readme(families, same):
    counts = Counter(p["status"] for f in families for p in f["parts"])
    total = sum(counts.values())
    gauges = [f for f in families if f["id"] == "fit-gauges"]
    featured = [f for f in families if f.get("featured")]
    rest = [f for f in families if f not in gauges and f not in featured]
    current = [f for f in rest if any(p["status"] in PRINTED for p in f["parts"])]
    concepts = [f for f in rest if f not in current]
    out = [
        "# Printable files",
        "",
        "<!-- Generated by build_catalog.py from catalog.toml. Edit catalog.toml, then run ./build_all.sh. -->",
        "",
        f"**{total} STLs, every one listed below with its status.** Start with the two fit gauges, then the "
        "featured pocketwatch case and telegraph key stand. Print every file as exported, with no supports, unless its row says otherwise.",
        "",
        "**Layout rule:** everything you print for one design is in one folder under `stl/`. "
        "`fit-gauges/` holds the calibration prints. The first desk stands are split by badge: "
        "`small/` is the 1.28, `large/` the 1.46.",
        "",
        "**Every design is a Python script** you can change and rerun: the *Change it* line under each design names "
        "the script and the class or constants to edit. Pocketwatch designs share `Badge` and `Case` in "
        f"{link('pocketwatch/build_pocketwatch.py', 'build_pocketwatch.py')}. "
        "Run a script from the repo root with the CAD venv; it rewrites its STLs here and prints its checks:",
        "",
        "```sh",
        "~/.venvs/cad/bin/python pocketwatch/stands/hoop/build_hoop_telegraph.py --no-render",
        "```",
        "",
        f"Setup is in {link('docs/TOOLCHAIN.md', 'TOOLCHAIN.md')}. Print results go in "
        f"{link('docs/PRINT-LOG.md', 'PRINT-LOG.md')}, which every status below cites by date.",
        "",
        "| status | files | means |",
        "|---|---|---|",
        *[f"| **{s}** | {counts[s]} | {t} |" for s, t in STATUS.items()],
        "",
        "Old and superseded models were deleted; " + link("archive/NOTE.md", "archive/NOTE.md") +
        " lists them and the commit that still has them.",
        "",
        "## 1. Print these first: fit gauges",
        "",
    ]
    for fam in gauges:
        out += [fam["about"], ""]
        for p in fam["parts"]:
            out += [f"### {stl_link(p['file'])}", "", image(fam, p["render"]), "",
                    f"**{p['status']}.** {evidence(p)}", "",
                    p["what"], "",
                    f"**Sets:** {p['sets']}. **Print:** {p['print']}. "
                    f"**Change it:** {link(p['script'], Path(p['script']).name)}, {p['edit']}.", ""]
    sections = [("2. Featured", featured, True), ("3. Other current designs", current, False),
                ("4. Concepts: never printed", concepts, False)]
    for title, fams, hero in sections:
        out += [f"## {title}", ""]
        if title.startswith("3"):
            out += ["Designs with at least one printed part.", ""]
        if title.startswith("4"):
            out += ["Every file here has passed its script's checks and nothing else. They are ideas, not tested parts. "
                    "A print result from you is the next step for any of them.", ""]
        for fam in fams:
            out += family_block(fam, same, hero)
    return "\n".join(out).rstrip() + "\n"


def main():
    families = load()
    bad, same = problems(families)
    if bad:
        print("stl/catalog.toml: " + str(len(bad)) + " problem(s)")
        print("\n".join("  " + b for b in bad))
        sys.exit(1)
    text = readme(families, same)
    n = sum(len(f["parts"]) for f in families)
    if "--check" in sys.argv:
        if README.read_text() != text:
            sys.exit("stl/README.md is stale: run python3 build_catalog.py")
        print(f"catalog ok: {n} STLs, every one catalogued; stl/README.md is current")
        return
    README.write_text(text)
    print(f"catalog ok: {n} STLs, every one catalogued; wrote stl/README.md")


if __name__ == "__main__":
    main()
