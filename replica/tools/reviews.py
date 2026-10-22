"""Rank feedback themes from replica/reviews.csv (standard library only).

python3 reviews.py replica/reviews.csv --themes replica/tools/themes.json --out replica/feedback.md

Rows without a URL are dropped. Each row is matched to themes by keywords in its
excerpt + paraphrase. Weight: rating 1-2 → 3, 3 → 2, 4 → 1.5, 5 or none → 1;
reviews from the last 18 months ×1.5. Themes with < 3 rows or one source are marked thin.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date

TODAY = date(2026, 10, 22)


def weight(row: dict) -> float:
    r = row.get("rating", "").strip()
    w = {"1": 3, "2": 3, "3": 2, "4": 1.5}.get(r[:1], 1.0) if r else 1.0
    try:
        y, m = int(row["date"][:4]), int(row["date"][5:7] or 1)
        if (TODAY.year - y) * 12 + (TODAY.month - m) <= 18:
            w *= 1.5
    except (ValueError, IndexError):
        pass
    return w


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("reviews")
    ap.add_argument("--themes", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    themes: dict[str, list[str]] = json.load(open(a.themes))
    rows = [r for r in csv.DictReader(open(a.reviews, encoding="utf-8")) if r.get("url", "").startswith("http")]
    hits: dict[str, list[dict]] = defaultdict(list)
    unmatched = []
    for r in rows:
        text = f"{r['excerpt']} {r['paraphrase']}".lower()
        matched = [t for t, kws in themes.items() if any(re.search(k, text) for k in kws)]
        for t in matched:
            hits[t].append(r)
        if not matched:
            unmatched.append(r)

    ranked = sorted(hits.items(), key=lambda kv: sum(weight(r) for r in kv[1]), reverse=True)
    out = [f"# Feedback themes\n\nSample: **{len(rows)} comments** from **{len({r['source'] for r in rows})} sources** "
           f"({', '.join(sorted({r['source'] for r in rows}))}). Products discussed: "
           f"{', '.join(sorted({r['product'] for r in rows}))}.\n",
           "| theme | weighted | comments | sources | recent (≤18 mo) | thin? |", "| --- | --- | --- | --- | --- | --- |"]
    for t, rs in ranked:
        srcs = {r["source"] for r in rs}
        recent = sum(weight(r) >= 1.5 and r["date"] >= "2025-04" for r in rs)
        thin = "thin" if len(rs) < 3 or len(srcs) < 2 else ""
        out.append(f"| {t} | {sum(weight(r) for r in rs):.1f} | {len(rs)} | {len(srcs)} | {recent} | {thin} |")
    for t, rs in ranked:
        out.append(f"\n## {t}\n")
        for r in sorted(rs, key=weight, reverse=True)[:6]:
            rating = f"{r['rating']}★ " if r["rating"] else ""
            out.append(f"- {rating}{r['product']}, {r['role'] or r['source']} ({r['date']}): {r['paraphrase']} "
                       f"[{r['source']}]({r['url']})")
    out.append("\n## Not matched to any theme (read by hand)\n")
    for r in unmatched:
        out.append(f"- {r['product']} ({r['date']}): {r['paraphrase']} [{r['source']}]({r['url']})")
    open(a.out, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"{len(rows)} rows, {len(ranked)} themes, {len(unmatched)} unmatched -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
