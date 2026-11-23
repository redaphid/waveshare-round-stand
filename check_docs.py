"""Check every tracked Markdown file for pointers that lead nowhere.

1. Links and images: every relative target must exist (from the doc's folder).
2. Paths in backticks: a code span that names a file or folder in this repo (it starts with a top-level
   entry, or a folder next to the doc) must exist, unless the same line names the commit that still has
   it (1580ce5) or the line sits under a heading that says "Deleted" (the ledger in archive/NOTE.md).
   Globs must match at least one file; a {a,b} list must match for every choice.

Exit 1 and list every miss. Run from the repo root: python3 check_docs.py
"""
import glob, os, re, subprocess, sys

KEEP = "1580ce5"        # the last commit with every deleted model; a line naming it may point at deleted files
LINK = re.compile(r'!?\[[^\]]*\]\((<[^>]+>|[^)\s]+)')
CODE = re.compile(r'`([^`\n]+)`')


def tracked_docs():
    out = subprocess.run(["git", "ls-files", "-z", "*.md"], capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.split("\0") if p)


def exists(path):
    m = re.search(r"\{([^{}]*)\}", path)
    if m:
        return all(exists(path[:m.start()] + choice + path[m.end():]) for choice in m.group(1).split(","))
    return bool(glob.glob(path)) if any(c in path for c in "*?[") else os.path.exists(path)


def path_like(span, base, tops):
    """A code span that names a repo path: it starts with a top-level entry, or a folder beside the doc."""
    s = span.strip().rstrip("/")
    if not s or s.startswith(("-", "~", "$", "http", "/", ".")) or "…" in s or "<" in s or "=" in s:
        return None
    if " " in s and "/" not in s:
        return None
    head = s.split("/")[0]
    if head in tops or (base and "/" in s and os.path.isdir(os.path.join(base, head))):
        return s
    return None


def main():
    tops = set(os.listdir("."))
    bad = []
    docs = tracked_docs()
    for doc in docs:
        base = os.path.dirname(doc)
        ledger = False
        for n, line in enumerate(open(doc, encoding="utf-8").read().splitlines(), 1):
            for m in LINK.finditer(line):
                t = m.group(1).strip("<>").split("#")[0]
                if not t or t.startswith(("http:", "https:", "mailto:")):
                    continue
                if not os.path.exists(os.path.normpath(os.path.join(base, t))):
                    bad.append(f"{doc}:{n}: link -> {t}")
            if line.startswith("#"):
                ledger = "deleted" in line.lower()
            if KEEP in line or ledger:
                continue
            for m in CODE.finditer(line):
                s = path_like(m.group(1), base, tops)
                if s and not (exists(s) or exists(os.path.join(base, s))):
                    bad.append(f"{doc}:{n}: path `{s}` does not exist (if it was deleted, say it is last in {KEEP})")
    for b in bad:
        print("  BROKEN " + b)
    print(f"  {len(docs)} docs, {len(bad)} broken")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
