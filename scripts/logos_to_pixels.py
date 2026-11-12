"""Convert official logos (assets/logos) into 16x16 pixel icons.

    uv run python scripts/logos_to_pixels.py [--preview sheet.png]

Reads ``assets/logos/logos.json`` and writes
``src/adapters/outbound/logo_pixels.json``, which the site renderer inlines as
SVG. Needs Pillow (a dev-only dependency; the site build itself does not).

A logo that cannot survive downsampling can instead be hand-drawn: give its
``logos.json`` entry ``rows`` and ``palette`` and they are used as-is.

Pipeline per logo: crop to the alpha bounding box, pad to a square, downsample
to 16x16 with Lanczos (premultiplied alpha, so no halos), threshold alpha,
then reduce to a small palette. Near-black pixels can be mapped to the page's
"ink" colour so black marks stay visible in dark mode.
"""

from __future__ import annotations

import argparse
import json
import string
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 16
ALPHA_CUTOFF = 128
INK_LUMA = 60

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "assets" / "logos"
OUT_PATH = ROOT / "src" / "adapters" / "outbound" / "logo_pixels.json"


def to_square(img: Image.Image) -> Image.Image:
    """Crop to the visible content, then pad (transparently) to a square."""
    img = img.convert("RGBA")
    bbox = img.getchannel("A").point(lambda a: 255 if a >= ALPHA_CUTOFF else 0).getbbox()
    if bbox is None:
        raise ValueError("logo is fully transparent")
    img = img.crop(bbox)
    side = max(img.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    return canvas


def _luma(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def _dominant_colours(img: Image.Image, colors: int) -> list[tuple[int, int, int]]:
    """Palette picked from a coarse sample of the full-resolution logo.

    Sampling before downscaling keeps the brand's real colours (white stays
    white) instead of the blends that Lanczos produces at edges.
    """
    sample = img.resize((64, 64), Image.Resampling.NEAREST)
    sp = sample.load()
    pixels = [sp[x, y][:3] for y in range(64) for x in range(64) if sp[x, y][3] >= ALPHA_CUTOFF]
    distinct = sorted(set(pixels))
    if len(distinct) <= colors:
        return distinct
    strip = Image.new("RGB", (len(pixels), 1))
    strip.putdata(pixels)
    quant = strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = quant.getpalette() or []
    used = sorted(set(quant.tobytes()))
    return [(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]) for i in used]


def _nearest(
    rgb: tuple[int, int, int], palette: list[tuple[int, int, int]]
) -> tuple[int, int, int]:
    return min(palette, key=lambda c: sum((a - b) ** 2 for a, b in zip(rgb, c, strict=True)))


def convert(
    img: Image.Image,
    colors: int,
    ink: bool = False,
    size: int = SIZE,
    fill_holes: str | None = None,
) -> dict:
    """Return ``{"palette": {char: "#rrggbb" | "ink"}, "rows": [size strings]}``."""
    square = to_square(img)
    palette_rgb = _dominant_colours(square, colors)
    small = square.resize((size, size), Image.Resampling.LANCZOS)
    px = small.load()
    chars = iter(string.ascii_lowercase)
    char_of: dict[str, str] = {}
    palette: dict[str, str] = {}
    grid = [["."] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            r, g, b, a = px[x, y]
            if a < ALPHA_CUTOFF:
                continue
            rep = _nearest((r, g, b), palette_rgb)
            value = "ink" if ink and _luma(rep) < INK_LUMA else "#{:02x}{:02x}{:02x}".format(*rep)
            if value not in char_of:
                char_of[value] = next(chars)
                palette[char_of[value]] = value
            grid[y][x] = char_of[value]
    if fill_holes:
        _fill_holes(grid, palette, char_of, fill_holes, chars)
    return {"palette": palette, "rows": ["".join(r) for r in grid]}


def _fill_holes(grid, palette, char_of, colour, chars) -> None:
    """Paint enclosed transparent areas (e.g. the letters in a logo) with ``colour``."""
    size = len(grid)
    outside: set[tuple[int, int]] = set()
    stack = [
        (y, x) for y in range(size) for x in range(size) if y in (0, size - 1) or x in (0, size - 1)
    ]
    while stack:
        y, x = stack.pop()
        if (y, x) in outside or not (0 <= y < size and 0 <= x < size) or grid[y][x] != ".":
            continue
        outside.add((y, x))
        stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    if colour not in char_of:
        char_of[colour] = next(chars)
        palette[char_of[colour]] = colour
    for y in range(size):
        for x in range(size):
            if grid[y][x] == "." and (y, x) not in outside:
                grid[y][x] = char_of[colour]


def override(cfg: dict, size: int = SIZE) -> dict:
    """Hand-drawn entry: ``rows`` + ``palette`` straight from logos.json (centred, validated)."""
    rows, palette = list(cfg["rows"]), dict(cfg["palette"])
    width = len(rows[0])
    if any(len(r) != width for r in rows) or width > size or len(rows) > size:
        raise ValueError("override rows must be equal-width and at most 16x16")
    unknown = set("".join(rows)) - set(palette) - {"."}
    if unknown:
        raise ValueError(f"override uses characters missing from its palette: {sorted(unknown)}")
    left, top = (size - width) // 2, (size - len(rows)) // 2
    padded = ["." * size] * top
    padded += ["." * left + r + "." * (size - width - left) for r in rows]
    padded += ["." * size] * (size - len(padded))
    return {"palette": palette, "rows": padded}


def build(config_path: Path = SRC_DIR / "logos.json") -> dict:
    config = json.loads(config_path.read_text())
    out = {}
    for name in sorted(config):
        cfg = config[name]
        if "rows" in cfg:
            out[name] = override(cfg)
            continue
        with Image.open(config_path.parent / cfg["src"]) as img:
            out[name] = convert(
                img,
                colors=cfg.get("colors", 4),
                ink=cfg.get("ink", False),
                fill_holes=cfg.get("fill_holes"),
            )
    return out


def preview(logos: dict, path: Path, scale: int = 12) -> None:
    """Contact sheet on light and dark backgrounds, for eyeballing the result."""
    cell = SIZE * scale + 24
    sheet = Image.new("RGB", (cell * len(logos), cell * 2), "white")
    draw = ImageDraw.Draw(sheet)
    for row, (bg, ink) in enumerate(
        (((255, 255, 255), (43, 43, 43)), ((22, 24, 27), (214, 214, 214)))
    ):
        draw.rectangle([0, row * cell, sheet.width, (row + 1) * cell], fill=bg)
        for i, name in enumerate(sorted(logos)):
            data = logos[name]
            for y, line in enumerate(data["rows"]):
                for x, ch in enumerate(line):
                    if ch == ".":
                        continue
                    v = data["palette"][ch]
                    rgb = ink if v == "ink" else tuple(int(v[j : j + 2], 16) for j in (1, 3, 5))
                    x0, y0 = i * cell + 12 + x * scale, row * cell + 12 + y * scale
                    draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=rgb)
    sheet.save(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", type=Path, default=SRC_DIR / "logos.json")
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument("--preview", type=Path, help="write a contact-sheet PNG here")
    args = ap.parse_args(argv)
    logos = build(args.config)
    args.out.write_text(json.dumps(logos, indent=1, sort_keys=True) + "\n")
    if args.preview:
        preview(logos, args.preview)
    print(f"Wrote {args.out} ({len(logos)} logos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
