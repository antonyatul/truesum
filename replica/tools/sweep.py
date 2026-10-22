"""Find any leftover old identity in the project (names, domains, colours).

python3 sweep.py . --config replica/brand.json
Skips .git, caches, node_modules and the replica/ planning folder. Exit 1 if anything is left.
Matches names case-insensitively, also inside identifiers (SmartlyticsHub, smartlytics_core).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP = {".git", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", "replica", ".venv", "build", "dist"}
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".xlsx", ".pdf", ".woff", ".woff2", ".otf", ".ttf", ".pyc"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--config")
    ap.add_argument("--avoid", default="")
    ap.add_argument("--domains", default="")
    ap.add_argument("--colors", default="")
    a = ap.parse_args()
    cfg = json.load(open(a.config)) if a.config else {}
    avoid = cfg.get("avoid", []) + [x for x in a.avoid.split(",") if x]
    domains = cfg.get("domains", []) + [x for x in a.domains.split(",") if x]
    colors = cfg.get("colors", []) + [x for x in a.colors.split(",") if x]
    patterns = [(f"name '{n}'", re.compile(r"[\s_-]*".join(map(re.escape, n.split())), re.I)) for n in avoid]
    patterns += [(f"domain '{d}'", re.compile(re.escape(d), re.I)) for d in domains]
    patterns += [(f"colour {c}", re.compile(re.escape(c), re.I)) for c in colors]

    hits = []
    for path in Path(a.root).rglob("*"):
        if any(part in SKIP for part in path.parts):
            continue
        rel = str(path.relative_to(a.root))
        for label, rx in patterns:
            if rx.search(path.name):
                hits.append(f"{rel}: file name contains {label}")
        if path.is_file() and path.suffix.lower() not in BINARY:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                for label, rx in patterns:
                    if rx.search(line):
                        hits.append(f"{rel}:{i}: {label}: {line.strip()[:100]}")
    for h in hits:
        print(h)
    print("clean" if not hits else f"{len(hits)} leftover(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
