"""Check launch listings: length limits, banned names, and claims that need proof.

python3 listing.py replica/launch/listing.json
Exit 1 on an error (over limit, old/avoided name, unbacked superlative).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

CLAIMS = re.compile(r"\b(best|#1|number one|leading|fastest|most popular|trusted by|award|ai[- ]powered)\b", re.I)


def length(text: str) -> int:
    """Characters as a person counts them (grapheme-ish: combining marks don't count)."""
    return sum(1 for ch in unicodedata.normalize("NFC", text) if not unicodedata.combining(ch))


def main(path: str) -> int:
    data = json.loads(Path(path).read_text())
    brand = json.loads(Path(data.get("avoid_from", "replica/brand.json")).read_text())
    avoid = [a.lower() for a in brand.get("avoid", [])]
    errors = warnings = 0
    for listing, fields in data["listings"].items():
        for field, spec in fields.items():
            text, limit = spec["text"], spec["max"]
            n = length(text)
            status = "ok"
            if n > limit:
                status, errors = f"ERROR over by {n - limit}", errors + 1
            for name in avoid:
                if name in text.lower():
                    status, errors = f"ERROR contains avoided name '{name}'", errors + 1
            if CLAIMS.search(text):
                status, errors = f"ERROR unbacked claim '{CLAIMS.search(text).group(0)}'", errors + 1
            if any(unicodedata.category(c) == "So" for c in text):
                status, warnings = status + " (warning: emoji/symbols)", warnings + 1
            print(f"{listing:20} {field:12} {n:4}/{limit:<4} {status}")
    print(f"\n{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
