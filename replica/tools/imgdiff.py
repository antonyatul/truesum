"""Layout diff between two screenshots.

python3 imgdiff.py original.png clone.png [--out diff.png] [--json] [--mode layout|pixel] [--name S02]

Layout mode: both images scaled to the same width, turned into edge maps, cut into a
grid; only cells with content in either image are compared. Colour is ignored on
purpose. Pixel mode is exact comparison, for clone-vs-clone regressions.
(Uses Pillow, which this project already depends on through Streamlit.)
"""
from __future__ import annotations

import argparse
import json

from PIL import Image, ImageChops, ImageDraw, ImageFilter

WIDTH = 720
CELL = 24


def edges(img: Image.Image, height: int) -> Image.Image:
    g = img.convert("L").resize((WIDTH, height))
    e = g.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    return e.filter(ImageFilter.MaxFilter(5))


def density(img: Image.Image, x: int, y: int) -> float:
    box = img.crop((x, y, x + CELL, y + CELL))
    hist = box.histogram()
    return hist[255] / (CELL * CELL)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("clone")
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--mode", choices=["layout", "pixel"], default="layout")
    ap.add_argument("--name")
    a = ap.parse_args()

    o, c = Image.open(a.original), Image.open(a.clone)
    ho = round(o.height * WIDTH / o.width)
    hc = round(c.height * WIDTH / c.width)
    h = max(ho, hc)
    height_note = ""
    if abs(ho - hc) / max(ho, 1) > 0.25:
        height_note = f"clone page is {hc / ho:.1f}x the original's height"

    if a.mode == "pixel":
        oo = o.convert("RGB").resize((WIDTH, h))
        cc = c.convert("RGB").resize((WIDTH, h))
        diff = ImageChops.difference(oo, cc).convert("L").point(lambda v: 255 if v > 16 else 0)
        score = 100 * (1 - diff.histogram()[255] / (WIDTH * h))
        regions = []
    else:
        canvas_o = Image.new("L", (WIDTH, h), 0)
        canvas_o.paste(edges(o, ho), (0, 0))
        canvas_c = Image.new("L", (WIDTH, h), 0)
        canvas_c.paste(edges(c, hc), (0, 0))
        compared = matched = 0
        regions = []
        for y in range(0, h - CELL + 1, CELL):
            for x in range(0, WIDTH - CELL + 1, CELL):
                do, dc = density(canvas_o, x, y), density(canvas_c, x, y)
                if do < 0.02 and dc < 0.02:
                    continue
                compared += 1
                if do >= 0.02 and dc >= 0.02:
                    matched += 1
                else:
                    regions.append((x, y))
        score = 100 * matched / compared if compared else 100.0
        diff = Image.merge("RGB", (canvas_c, canvas_o, Image.new("L", (WIDTH, h), 0)))  # red = clone only, green = original only
        draw = ImageDraw.Draw(diff)
        for x, y in regions:
            draw.rectangle((x, y, x + CELL - 1, y + CELL - 1), outline=(255, 255, 0))

    verdict = "matches" if score >= 90 else "close" if score >= 75 else "partly" if score >= 50 else "different"
    scale = o.width / WIDTH
    big = _merge(regions)[:5]
    result = {"name": a.name or a.clone, "mode": a.mode, "score": round(score, 1), "verdict": verdict,
              "height_note": height_note,
              "regions": [[round(x * scale), round(y * scale), round(w * scale), round(hh * scale)] for x, y, w, hh in big]}
    if a.out:
        diff.save(a.out)
    if a.json:
        print(json.dumps(result))
    else:
        print(f"{result['name']}: {score:.0f} ({verdict}) {height_note}")
        for r in result["regions"]:
            print(f"  differs at x={r[0]} y={r[1]} w={r[2]} h={r[3]}")
    return 0


def _merge(cells: list[tuple[int, int]]) -> list[tuple[int, int, int, int]]:
    """Group differing cells into row bands, biggest first."""
    bands: dict[int, list[int]] = {}
    for x, y in cells:
        bands.setdefault(y, []).append(x)
    rects = [(min(xs), y, max(xs) - min(xs) + CELL, CELL) for y, xs in bands.items()]
    merged: list[list[int]] = []
    for x, y, w, h in sorted(rects, key=lambda r: r[1]):
        if merged and merged[-1][1] + merged[-1][3] == y and abs(merged[-1][0] - x) < CELL * 4:
            m = merged[-1]
            m[0], m[2], m[3] = min(m[0], x), max(m[0] + m[2], x + w) - min(m[0], x), m[3] + h
        else:
            merged.append([x, y, w, h])
    return sorted((tuple(m) for m in merged), key=lambda r: r[2] * r[3], reverse=True)


if __name__ == "__main__":
    raise SystemExit(main())
