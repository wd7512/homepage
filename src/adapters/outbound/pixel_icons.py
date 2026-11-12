"""Tiny 16x16 pixel-art icons rendered as inline, theme-aware SVG.

Each icon is authored as a small character grid (at most 16x16) and padded,
centred, onto a 16x16 canvas. Characters index :data:`PALETTE`; ``.`` is
transparent. Colours are not hard-coded: every palette entry becomes a CSS
class (``ic-<char>``) whose fill is a custom property, so the icons follow the
page's light/dark theme. Icons are decorative (``aria-hidden``).
"""

from __future__ import annotations

import json
from pathlib import Path

SIZE = 16

# char -> CSS class suffix. Actual colours live in the page stylesheet.
PALETTE: dict[str, str] = {
    "k": "ink",  # outline
    "w": "paper",  # light fill (inverts in dark mode)
    "a": "blue",  # accent
    "l": "sky",  # light accent
    "y": "gold",
    "g": "green",
    "r": "red",
    "n": "brown",
    "h": "honey",  # light gold
    "o": "orcid",  # ORCID brand green (fixed in both themes)
    "x": "white",  # pure white (fixed in both themes)
}


def _chart() -> tuple[str, ...]:
    """Three bars on an axis, 16 wide x 14 tall."""
    rows = []
    for r in range(13):
        cells = ["k"] + ["."] * 15
        for c0, top, ch in ((2, 7, "y"), (7, 4, "l"), (12, 1, "a")):
            if r >= top:
                cells[c0 : c0 + 4] = [ch] * 4
        rows.append("".join(cells))
    rows.append("k" * 16)
    return tuple(rows)


def _pulse() -> tuple[str, ...]:
    """ECG trace (2px) inside a monitor frame, 16 wide x 9 tall."""
    inner = (
        ".....r........",
        "....r.r.......",
        "....r.r.......",
        "...r...r......",
        "rrr.....r.rrr.",
        ".........r.r..",
        "..........r...",
    )
    thick = []
    for row in inner:
        cells = list(row)
        for i, ch in enumerate(row):
            if ch == "r" and i + 1 < len(row) and cells[i + 1] == ".":
                cells[i + 1] = "r"
        thick.append("".join(cells))
    return ("k" * 16, *("k" + t + "k" for t in thick), "k" * 16)


def _outlined(mask: tuple[str, ...], fill: str = "y") -> tuple[str, ...]:
    """Fill a ``#`` mask with ``fill`` and add a 1px ``k`` outline around it."""
    h, w = len(mask), len(mask[0])
    filled = {(y + 1, x + 1) for y, row in enumerate(mask) for x, c in enumerate(row) if c == "#"}
    rows = []
    for y in range(h + 2):
        row = ""
        for x in range(w + 2):
            if (y, x) in filled:
                row += fill
            elif any((y + dy, x + dx) in filled for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                row += "k"
            else:
                row += "."
        rows.append(row)
    return tuple(rows)


def _climber() -> tuple[str, ...]:
    """A climber on a wall of coloured holds, 16x16."""
    g = [["l"] * 16 for _ in range(16)]
    for i in range(16):
        g[0][i] = g[15][i] = g[i][0] = g[i][15] = "k"
    holds = {
        (2, 3): "g",
        (2, 12): "r",
        (14, 4): "y",
        (14, 11): "g",
        (8, 2): "y",
        (7, 13): "g",
        (10, 13): "r",
        (11, 2): "r",
        (5, 2): "g",
        (4, 13): "y",
    }
    for (y, x), c in holds.items():
        g[y][x] = c
    body = [(4, 7), (4, 8), (5, 7), (5, 8)]  # head
    body += [(y, x) for y in range(6, 10) for x in (7, 8)]  # torso
    body += [(6, 6), (5, 5), (4, 4), (3, 3), (6, 9), (5, 10), (4, 11), (3, 12)]  # arms
    body += [(10, 6), (11, 5), (12, 5), (13, 4), (10, 9), (11, 10), (12, 10), (13, 11)]  # legs
    for y, x in body:
        g[y][x] = "k"
    return tuple("".join(r) for r in g)


# Icons are centred on a 16x16 canvas; whitespace around them is fine.
_ART: dict[str, tuple[str, ...]] = {
    "book": (
        ".kkkkkk..kkkkkk.",
        "kwwwwwwkkwwwwwwk",
        "kwaaaaakkaaaaawk",
        "kwwwwwwkkwwwwwwk",
        "kwaaaaakkaaaaawk",
        "kwwwwwwkkwwwwwwk",
        "kwaaaaakkaaaaawk",
        "kwwwwwwkkwwwwwwk",
        "kwaaaaakkaaaaawk",
        "kwwwwwwkkwwwwwwk",
        ".kkkkkkkkkkkkkk.",
    ),
    "briefcase": (
        "....kkkkkkkk....",
        "....k......k....",
        "kkkkkkkkkkkkkkkk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnyynnnnnnk",
        "kkkkkkkkkkkkkkkk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "knnnnnnnnnnnnnnk",
        "kkkkkkkkkkkkkkkk",
    ),
    "battery": (
        "kkkkkkkkkkkkkk..",
        "kwwwwwwwwwwwwk..",
        "kgggwgggwgggwkkk",
        "kgggwgggwgggwkkk",
        "kgggwgggwgggwkkk",
        "kgggwgggwgggwkkk",
        "kwwwwwwwwwwwwk..",
        "kkkkkkkkkkkkkk..",
    ),
    "satellite": (
        ".......yy.......",
        ".......kk.......",
        ".......kk.......",
        "kkkkk.kkkk.kkkkk",
        "kaaak.kyyk.kaaak",
        "klllkkkyykkklllk",
        "kaaakkkyykkkaaak",
        "klllk.kyyk.klllk",
        "kkkkk.kkkk.kkkkk",
        ".......kk.......",
    ),
    "sock": (
        "..kkkkkkkk......",
        "..kaaaaaak......",
        "..kwwwwwwk......",
        "..kaaaaaak......",
        "..kwwwwwwk......",
        "..kwwwwwwk......",
        "..kwwwwwwk......",
        "..kwwwwwwk......",
        "..kwwwwwwkkkkk..",
        "..kaawwwwwwaak..",
        "..kaawwwwwwaak..",
        "..kaawwwwwwaak..",
        "..kkkkkkkkkkkk..",
    ),
    "wearable": (
        "....kkkkkkkk....",
        "....kaaaaaak....",
        "....kaaaaaak....",
        "....kaaaaaak....",
        "...kkkkkkkkkk...",
        "...kllllllllk...",
        "...klrrllrrlk...",
        "...klrrrrrrlk...",
        "...kllrrrrllk...",
        "...klllrrlllk...",
        "...kkkkkkkkkk...",
        "....kaaaaaak....",
        "....kaaaaaak....",
        "....kaaaaaak....",
        "....kkkkkkkk....",
    ),
    "lightning": _outlined(
        (
            "......####",
            ".....####.",
            "....####..",
            "...####...",
            "..########",
            "..########",
            "....####..",
            "...####...",
            "..####....",
            ".####.....",
            "####......",
        )
    ),
    "canvas": (
        "..kkkkkkkkkkkk..",
        "..kllllllllllk..",
        "..kllllllllyyk..",
        "..kllllllllyyk..",
        "..kllllllllllk..",
        "..kllllllllllk..",
        "..kgggglgggggk..",
        "..kggggggggggk..",
        "..kggggggggggk..",
        "..kkkkkkkkkkkk..",
        "...nn......nn...",
        "...nn..nn..nn...",
        "..nn...nn...nn..",
        "..nn...nn...nn..",
        ".nn....nn....nn.",
    ),
    "bitflip": (
        "kkkkkkk..kkkkkkk",
        "kwaaawk..kwwrwwk",
        "kawwwak..kwrrwwk",
        "kawwwak..kwwrwwk",
        "kawwwakyykwwrwwk",
        "kawwwak..kwwrwwk",
        "kawwwak..kwwrwwk",
        "kwaaawk..kwrrrwk",
        "kkkkkkk..kkkkkkk",
    ),
    "bank": (
        ".......kk.......",
        "......kwwk......",
        ".....kwwwwk.....",
        "....kwwwwwwk....",
        "...kwwwwwwwwk...",
        "..kkkkkkkkkkkk..",
        "...aa..aa..aa...",
        "...aa..aa..aa...",
        "...aa..aa..aa...",
        "...aa..aa..aa...",
        "..kkkkkkkkkkkk..",
        ".kkkkkkkkkkkkkk.",
    ),
    "ingot": (
        "....kkkkkkkk....",
        "...khxxhhhhhk...",
        "..khhhhhhhhhhk..",
        "kkkkkkkkkkkkkkkk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kyyyyyyyyyyyyyyk",
        "kkkkkkkkkkkkkkkk",
    ),
    "cash": (
        "kkkkkkkkkkkkkkkk",
        "kggggggggggggggk",
        "kgxgggxxxxgggxgk",
        "kggggxggggxggggk",
        "kggggxgxxgxggggk",
        "kggggxggggxggggk",
        "kgxgggxxxxgggxgk",
        "kggggggggggggggk",
        "kkkkkkkkkkkkkkkk",
    ),
    "climber": _climber(),
    "bulb": (
        "...kkkkkk...",
        "..kyyyyyyk..",
        ".kyyyyyyyyk.",
        "kyyxxyyyyyyk",
        "kyyxyyyyyyyk",
        "kyyyyyyyyyyk",
        "kyyyyyyyyyyk",
        "kyyyyyyyyyyk",
        ".kyyyyyyyyk.",
        "..kyyyyyyk..",
        "...kyyyyk...",
        "...kkkkkk...",
        "...kaaaak...",
        "...kkkkkk...",
        "....kaak....",
        ".....kk.....",
    ),
    "cap": (
        "......kkkk......",
        "....kkaaaakk....",
        "..kkaaaaaaaakk..",
        "kkaaaaaaaaaaaakk",
        ".kkaaaaaaaaaakk.",
        "..kkkkkkkkkkkky.",
        "....kwwwwwwk..y.",
        "....kwwwwwwk..y.",
        "....kwwwwwwk.yyy",
        "....kkkkkkkk....",
    ),
    "chart": _chart(),
    "chip": (
        "...k.k.k.k.k....",
        "...k.k.k.k.k....",
        "..kkkkkkkkkkkk..",
        "..kaaaaaaaaaak..",
        "kkkaaaaaaaaaakkk",
        "..kaallllllaak..",
        "kkkaallllllaakkk",
        "..kaallllllaak..",
        "kkkaallllllaakkk",
        "..kaaaaaaaaaak..",
        "kkkaaaaaaaaaakkk",
        "..kkkkkkkkkkkk..",
        "...k.k.k.k.k....",
        "...k.k.k.k.k....",
    ),
    "controller": (
        "..kkkkkkkkkkkk..",
        ".kllllllllllllk.",
        "klllkllllllylllk",
        "kllkkkllllrlrllk",
        "klllkllllllylllk",
        "kllllllllllllllk",
        "klllkkkkkkkklllk",
        "kllk........kllk",
        ".kk..........kk.",
    ),
    "doc": (
        "kkkkkkkkk...",
        "kwwwwwwwkk..",
        "kwwwwwwwkwk.",
        "kwwwwwwwkkkk",
        "kwwwwwwwwwwk",
        "kwaaaaaaaawk",
        "kwwwwwwwwwwk",
        "kwaaaaaaaawk",
        "kwwwwwwwwwwk",
        "kwaaaaaaaawk",
        "kwwwwwwwwwwk",
        "kwaaaaaawwwk",
        "kwwwwwwwwwwk",
        "kwaaaaaaaawk",
        "kwwwwwwwwwwk",
        "kkkkkkkkkkkk",
    ),
    "flask": (
        "..kkkkkkkk..",
        "....kwwk....",
        "....kwwk....",
        "....kwwk....",
        "....kwwk....",
        "...kwwwwk...",
        "..kwwwwwwk..",
        ".kwwwwwwwwk.",
        ".kwwggggwwk.",
        "kwggggggggwk",
        "kggxgggggggk",
        "kggggggggggk",
        "kgggggggxggk",
        "kggggggggggk",
        ".kggggggggk.",
        "..kkkkkkkk..",
    ),
    "heart": (
        "..kkkk....kkkk..",
        ".krrrrrkkrrrrrk.",
        "krrxrrrrrrrrrrrk",
        "krrrrrrrrrrrrrrk",
        "krrrrrrrrrrrrrrk",
        ".krrrrrrrrrrrrk.",
        "..krrrrrrrrrrk..",
        "...krrrrrrrrk...",
        "....krrrrrrk....",
        ".....krrrrk.....",
        "......krrk......",
        ".......kk.......",
    ),
    "magnifier": (
        "...kkkkkkk......",
        ".kkwwwwwwwkk....",
        ".kwwwwwwwwwk....",
        "kwwwlllllwwwk...",
        "kwwlllllllwwk...",
        "kwwlllllllwwk...",
        "kwwlllllllwwk...",
        "kwwwlllllwwwk...",
        ".kwwwwwwwwwk....",
        ".kkwwwwwwwkkn...",
        "...kkkkkkk.nn...",
        "............nn..",
        ".............nn.",
        "..............kk",
    ),
    "mail": (
        "kkkkkkkkkkkkkkkk",
        "kkkwwwwwwwwwwkkk",
        "kwwkkwwwwwwkkwwk",
        "kwwwwkkwwkkwwwwk",
        "kwwwwwwkkwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        "kwwwwwwwwwwwwwwk",
        "kkkkkkkkkkkkkkkk",
    ),
    "pawn": (
        "....kkkk....",
        "..kkaaaakk..",
        "..kaaaaaak..",
        "..kaaxaaak..",
        "..kaaaaaak..",
        "...kaaaak...",
        "....kaak....",
        "..kkaaaakk..",
        "...kaaaak...",
        "...kaaaak...",
        "...kaaaak...",
        "..kaaaaaak..",
        ".kaaaaaaaak.",
        ".kaaaaaaaak.",
        "kaaaaaaaaaak",
        "kkkkkkkkkkkk",
    ),
    "pulse": _pulse(),
    "snake": (
        "gggggggggggggg..",
        "gggggggggggggg..",
        "gg..............",
        "gg..............",
        "gggggggggggggg..",
        "gggggggggggggg..",
        "............gg..",
        "............gg..",
        "gggggggggggggxkg",
        "gggggggggggggggr",
    ),
}

# Fallback icons for section headings / items with no (or an unknown) icon.
DEFAULT_ICON = "chip"
LINK_ICONS: dict[str, str] = {
    "email": "mail",
    "cv": "doc",
    "scholar": "scholar",
    "orcid": "orcid",
    "github": "github",
    "linkedin": "linkedin",
}
SECTION_ICONS: dict[str, str] = {
    "about": "bulb",
    "publications": "book",
    "research": "flask",
    "education": "cap",
    "experience": "briefcase",
    "projects": "canvas",
    "skills": "chip",
}


_LOGO_PATH = Path(__file__).with_name("logo_pixels.json")


def _load_logos() -> dict[str, dict]:
    if not _LOGO_PATH.exists():
        return {}
    return json.loads(_LOGO_PATH.read_text())


# Official logos converted by scripts/logos_to_pixels.py (see assets/logos/).
LOGOS: dict[str, dict] = _load_logos()


def icon_names() -> list[str]:
    """Hand-drawn icons (character grids)."""
    return sorted(_ART)


def logo_names() -> list[str]:
    return sorted(LOGOS)


def all_icon_names() -> list[str]:
    return sorted({*_ART, *LOGOS})


def grid(name: str) -> list[str]:
    """Return a hand-drawn icon as exactly ``SIZE`` rows of ``SIZE`` characters."""
    art = _ART[name]
    width = len(art[0])
    if any(len(row) != width for row in art):
        raise ValueError(f"icon {name!r} has ragged rows")
    if width > SIZE or len(art) > SIZE:
        raise ValueError(f"icon {name!r} is larger than {SIZE}x{SIZE}")
    left = (SIZE - width) // 2
    top = (SIZE - len(art)) // 2
    rows = ["." * SIZE] * top
    rows += ["." * left + row + "." * (SIZE - width - left) for row in art]
    rows += ["." * SIZE] * (SIZE - len(rows))
    return rows


def _runs(rows: list[str]) -> dict[str, list[str]]:
    paths: dict[str, list[str]] = {}
    for y, row in enumerate(rows):
        x = 0
        while x < SIZE:
            ch = row[x]
            if ch == ".":
                x += 1
                continue
            start = x
            while x < SIZE and row[x] == ch:
                x += 1
            paths.setdefault(ch, []).append(f"M{start} {y}h{x - start}v1h-{x - start}z")
    return paths


def svg(name: str | None, fallback: str = DEFAULT_ICON) -> str:
    """Inline decorative SVG for ``name`` (unknown names use ``fallback``)."""
    if name in LOGOS:
        data = LOGOS[name]
        body = ""
        for ch, segs in _runs(data["rows"]).items():
            colour = data["palette"][ch]
            attr = 'class="ic-ink"' if colour == "ink" else f'fill="{colour}"'
            body += f'<path {attr} d="{"".join(segs)}"/>'
    else:
        key = name if name in _ART else fallback
        body = "".join(
            f'<path class="ic-{PALETTE[ch]}" d="{"".join(segs)}"/>'
            for ch, segs in _runs(grid(key)).items()
        )
    return (
        '<svg class="pix" viewBox="0 0 16 16" shape-rendering="crispEdges" '
        f'aria-hidden="true" focusable="false">{body}</svg>'
    )
