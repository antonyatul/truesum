"""WCAG 2.1 contrast check for every pair in tokens.json.

Usage: python3 contrast.py replica/design/tokens.json
Exits 1 if any pair fails AA (body 4.5, large 3.0, ui 3.0).
"""
import json
import sys

MIN = {"body": 4.5, "large": 3.0, "ui": 3.0}


def luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main(path: str) -> int:
    tokens = json.load(open(path))
    palette = {**tokens["color"], **{k: v for k, v in tokens.get("chart", {}).items() if isinstance(v, str)}}
    failures = 0
    for fg, bg, kind in tokens["pairs"]:
        r = ratio(palette[fg], palette[bg])
        ok = r >= MIN[kind]
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {r:5.2f}:1  (min {MIN[kind]})  {fg} on {bg}  [{kind}]")
    print(f"\n{len(tokens['pairs']) - failures}/{len(tokens['pairs'])} pairs pass AA")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
