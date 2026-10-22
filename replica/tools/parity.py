"""Feature parity score from replica/features.csv (standard library only).

python3 parity.py replica/features.csv [--visual diffs/*.json] [--markdown]

Weights: must 3, should 2, could 1. partial = half. 'skip' rows and rows whose
`original` is 'none' (features the original never had) are left out of the score.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict

WEIGHT = {"must": 3, "should": 2, "could": 1}
CREDIT = {"yes": 1.0, "partial": 0.5, "no": 0.0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("features")
    ap.add_argument("--visual", nargs="*", default=[])
    ap.add_argument("--markdown", action="store_true")
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.features, encoding="utf-8")))
    scored = [r for r in rows if r["priority"] in WEIGHT and r["clone"] != "skip"
              and not r["original"].strip().lower().startswith("none")]
    extra = [r for r in rows if r["original"].strip().lower().startswith("none")]
    total = sum(WEIGHT[r["priority"]] for r in scored)
    got = sum(WEIGHT[r["priority"]] * CREDIT[r["clone"]] for r in scored)
    score = got / total * 100 if total else 0.0
    musts = [r for r in scored if r["priority"] == "must"]
    must_done = sum(r["clone"] == "yes" for r in musts)

    areas: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for r in scored:
        areas[r["area"]][0] += WEIGHT[r["priority"]] * CREDIT[r["clone"]]
        areas[r["area"]][1] += WEIGHT[r["priority"]]
    area_scores = sorted(((k, v[0] / v[1] * 100) for k, v in areas.items()), key=lambda x: x[1])
    order = {"must": 0, "should": 1, "could": 2}
    missing = sorted([r for r in scored if r["clone"] != "yes"], key=lambda r: (order[r["priority"]], r["area"]))

    visual = []
    for path in a.visual:
        d = json.load(open(path))
        visual.append((d.get("name", path), d["score"]))

    out = []
    p = out.append
    md = a.markdown
    p(("## " if md else "") + f"Feature parity: {score:.1f}%")
    p(f"Must-haves: {must_done}/{len(musts)}" + ("" if must_done == len(musts) else "  -> NOT SHIPPABLE"))
    p(f"Scored rows: {len(scored)} (skipped: {sum(r['clone'] == 'skip' for r in rows)}, new features not in the original: {len(extra)})")
    p("")
    p(("### " if md else "") + "By area, weakest first")
    for k, v in area_scores:
        p(f"- {k}: {v:.0f}%")
    p("")
    p(("### " if md else "") + "Missing, in build order")
    for r in missing or []:
        p(f"- [{r['priority']}] {r['feature']} ({r['clone']}){' — ' + r['notes'] if r['notes'] else ''}")
    if not missing:
        p("- nothing")
    p("")
    p(("### " if md else "") + "New in the clone (not in the original)")
    for r in extra:
        p(f"- {r['feature']} ({r['clone']})")
    if visual:
        p("")
        p(("### " if md else "") + "Layout")
        for name, s in visual:
            p(f"- {name}: {s:.0f}")
    print("\n".join(out))
    return 0 if must_done == len(musts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
