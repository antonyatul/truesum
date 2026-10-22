"""Draw Truesum's brand assets from the design tokens (no external images).

python scripts/make_brand_assets.py
  -> assets/logo.svg, assets/logo.png (512), assets/favicon.png (64),
     assets/app-icon.png (1024, no transparency), assets/og-image.png (1200x630)

The mark: an equals sign whose lower bar ends in a tick — "the sum is true".
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
T = json.loads((ROOT / "replica/design/tokens.json").read_text())["color"]
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_REG = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"


def hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(size: tuple[int, int], a: str, b: str, diagonal: bool = True) -> Image.Image:
    w, h = size
    ca, cb = hex2rgb(a), hex2rgb(b)
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = ((x / w) + (y / h)) / 2 if diagonal else x / w
            px[x, y] = tuple(round(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))
    return img


# geometry in a 100-unit box
BAR_H = 11
TOP = [(24, 33), (76, 33)]
TICK = [(24, 62), (56, 62), (64, 70), (80, 50)]


def draw_mark(size: int, rounded: bool = True) -> Image.Image:
    s = size / 100
    bg = gradient((size, size), T["hero-from"], T["hero-to"])
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=int(22 * s) if rounded else 0, fill=255)
    ink = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(ink)
    w = round(BAR_H * s)
    d.line([(x * s, y * s) for x, y in TOP], fill=hex2rgb(T["text"]), width=w)
    for x, y in (TOP[0], TOP[-1]):
        d.ellipse(((x * s) - w / 2, (y * s) - w / 2, (x * s) + w / 2, (y * s) + w / 2), fill=hex2rgb(T["text"]))
    accent = gradient((size, size), T["accent"], T["accent-2"], diagonal=False).convert("RGBA")
    tick_mask = Image.new("L", (size, size), 0)
    td = ImageDraw.Draw(tick_mask)
    td.line([(x * s, y * s) for x, y in TICK], fill=255, width=w, joint="curve")
    for x, y in (TICK[0], TICK[-1]):
        td.ellipse(((x * s) - w / 2, (y * s) - w / 2, (x * s) + w / 2, (y * s) + w / 2), fill=255)
    out = bg.convert("RGBA")
    out.alpha_composite(ink)
    out.paste(accent, (0, 0), tick_mask)
    out.putalpha(mask)
    return out


def svg() -> str:
    pts = " ".join(f"{x},{y}" for x, y in TICK)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="Truesum">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{T['hero-from']}"/><stop offset="1" stop-color="{T['hero-to']}"/></linearGradient>
    <linearGradient id="tick" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{T['accent']}"/><stop offset="1" stop-color="{T['accent-2']}"/></linearGradient>
  </defs>
  <rect width="100" height="100" rx="22" fill="url(#bg)"/>
  <line x1="{TOP[0][0]}" y1="{TOP[0][1]}" x2="{TOP[1][0]}" y2="{TOP[1][1]}" stroke="{T['text']}" stroke-width="{BAR_H}" stroke-linecap="round"/>
  <polyline points="{pts}" fill="none" stroke="url(#tick)" stroke-width="{BAR_H}" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def og_image() -> Image.Image:
    img = gradient((1200, 630), T["hero-from"], T["hero-to"]).convert("RGBA")
    mark = draw_mark(200)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((68, 213, 272, 417), radius=46, outline=hex2rgb(T["border-input"]), width=2)
    img.alpha_composite(mark, (70, 215))
    d.text((306, 215), "Truesum", font=ImageFont.truetype(FONT_BOLD, 96), fill=hex2rgb(T["text"]))
    d.text((310, 335), "Your sales spreadsheet, explained in plain English.", font=ImageFont.truetype(FONT_REG, 32),
           fill=hex2rgb(T["text-muted"]))
    d.text((310, 390), "Checks the maths · rates every sale · hands back a workbook", font=ImageFont.truetype(FONT_REG, 28),
           fill=hex2rgb(T["accent"]))
    for _y, size, text in ((335, 32, "Your sales spreadsheet, explained in plain English."),
                          (390, 28, "Checks the maths · rates every sale · hands back a workbook")):
        width = d.textlength(text, font=ImageFont.truetype(FONT_REG, size))
        assert 310 + width <= 1160, f"OG text overflows: {text}"
    return img.convert("RGB")


def main() -> None:
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    (out / "logo.svg").write_text(svg())
    big = draw_mark(1024)
    big.resize((512, 512), Image.LANCZOS).save(out / "logo.png", optimize=True)
    big.resize((64, 64), Image.LANCZOS).save(out / "favicon.png", optimize=True)
    icon = draw_mark(1024, rounded=False).convert("RGB")  # iOS: square, no transparency (the OS rounds it)
    icon.save(out / "app-icon.png", optimize=True)
    og_image().save(out / "og-image.png", optimize=True)
    for f in ("logo.svg", "logo.png", "favicon.png", "app-icon.png", "og-image.png"):
        print(f, (out / f).stat().st_size, "bytes")


if __name__ == "__main__":
    main()
