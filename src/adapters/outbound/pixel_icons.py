"""Tiny 16x16 pixel-art icons rendered as inline, theme-aware SVG.

Each icon is authored as a small character grid (at most 16x16) and padded,
centred, onto a 16x16 canvas. Characters index :data:`PALETTE`; ``.`` is
transparent. Colours are not hard-coded: every palette entry becomes a CSS
class (``ic-<char>``) whose fill is a custom property, so the icons follow the
page's light/dark theme. Icons are decorative (``aria-hidden``).
"""

from __future__ import annotations

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
}

_ART: dict[str, tuple[str, ...]] = {
    "book": (
        ".kkkkk..kkkkk.",
        "kwwwwwkkwwwwwk",
        "kwaaaakkaaaawk",
        "kwwwwwkkwwwwwk",
        "kwaaaakkaaaawk",
        "kwwwwwkkwwwwwk",
        "kwaaaakkaaaawk",
        "kwwwwwkkwwwwwk",
        ".kkkkkkkkkkkk.",
    ),
    "flask": (
        "...kkkkkk...",
        "....kwwk....",
        "....kwwk....",
        "....kwwk....",
        "...kwwwwk...",
        "..kwwwwwwk..",
        ".kwggggggwk.",
        ".kggwgggggk.",
        ".kggggggggk.",
        "..kkkkkkkk..",
    ),
    "cap": (
        "......kk......",
        "....kkaakk....",
        "..kkaaaaaakk..",
        "kkaaaaaaaaaakk",
        ".kkaaaaaaaakk.",
        "...kkwwwwkk...",
        "...kwwwwwwk...",
        "...kkkkkkkk...",
    ),
    "briefcase": (
        "....kkkkkk....",
        "....k....k....",
        "..kkkkkkkkkk..",
        ".knnnnnnnnnnk.",
        ".knnnnnnnnnnk.",
        ".knnnnyynnnnk.",
        ".kkkkkkkkkkkk.",
        ".knnnnnnnnnnk.",
        ".knnnnnnnnnnk.",
        ".knnnnnnnnnnk.",
        "..kkkkkkkkkk..",
    ),
    "chip": (
        "..k.k.k.k...",
        "..k.k.k.k...",
        ".kkkkkkkkkk.",
        ".kaaaaaaaak.",
        "kkaaaaaaaakk",
        ".kaallllaak.",
        "kkaallllaakk",
        ".kaaaaaaaak.",
        ".kkkkkkkkkk.",
        "..k.k.k.k...",
        "..k.k.k.k...",
    ),
    "bulb": (
        "..kkkkkk..",
        ".kyyyyyyk.",
        "kyywyyyyyk",
        "kyywyyyyyk",
        "kyyyyyyyyk",
        ".kyyyyyyk.",
        "..kyyyyk..",
        "...kyyk...",
        "...kkkk...",
        "...kaak...",
        "...kkkk...",
        "....kk....",
    ),
    "heart": (
        "..kkk...kkk..",
        ".krrrk.krrrk.",
        "krwrrrrrrrrrk",
        "krrrrrrrrrrrk",
        "krrrrrrrrrrrk",
        ".krrrrrrrrrk.",
        "..krrrrrrrk..",
        "...krrrrrk...",
        "....krrrk....",
        ".....krk.....",
        "......k......",
    ),
    "shield": (
        "kkkkkkkkkkkk",
        "kaaaaalllllk",
        "kaaaaalllllk",
        "kaaaaalllllk",
        "kaaaaalllllk",
        "kaaaaalllllk",
        ".kaaaallllk.",
        "..kaaalllk..",
        "...kaallk...",
        "....kalk....",
        ".....kk.....",
    ),
    "chart": (
        "k.......aa..",
        "k.......aa..",
        "k.......aa..",
        "k.......aa..",
        "k...ll..aa..",
        "k...ll..aa..",
        "k...ll..aa..",
        "kyy.ll..aa..",
        "kyy.ll..aa..",
        "kkkkkkkkkkkk",
    ),
    "pawn": (
        "....kkk....",
        "...kwwwk...",
        "...kwwwk...",
        "....kwk....",
        "...kwwwk...",
        "..kwwwwwk..",
        "...kwwwk...",
        "...kwwwk...",
        "..kwwwwwk..",
        ".kwwwwwwwk.",
        ".kkkkkkkkk.",
    ),
    "snake": (
        ".kkkkkkkkk..",
        "kgggggggggk.",
        "kgkkkkkkkkk.",
        "kgk.........",
        "kgkkkkkkkkk.",
        "kggggggggwgk",
        ".kkkkkkkkkk.",
    ),
    "controller": (
        "..kkkkkkkkkk..",
        ".kllllllllllk.",
        "kllklllllllylk",
        "klkkklllllrlrk",
        "kllklllllllylk",
        ".kllllllllllk.",
        "..kkkkkkkkkk..",
    ),
    "coin": (
        "...kkkk...",
        "..kyyyyk..",
        ".kyywyyyk.",
        "kyywyyyyyk",
        "kyyyynyyyk",
        "kyyynnnyyk",
        "kyyyynyyyk",
        "kyyyyyyyyk",
        ".kyyyyyyk.",
        "..kyyyyk..",
        "...kkkk...",
    ),
    "mountain": (
        "......kk......",
        ".....kwwk.....",
        "....kwwwwk....",
        "...kaaaaaak...",
        "..kaaaaaaaak..",
        ".kaaaaaaaaaak.",
        "kaaaaaaaaaaaak",
        "kkkkkkkkkkkkkk",
    ),
    "magnifier": (
        "..kkkkk....",
        ".kwwwwwk...",
        "kwwlllwwk..",
        "kwlllllwk..",
        "kwlllllwk..",
        "kwwlllwwk..",
        ".kwwwwwkn..",
        "..kkkkk.nn.",
        "........nn.",
        ".........n.",
    ),
    "pulse": (
        "......r.........",
        ".....r.r........",
        ".....r.r........",
        "....r...r.......",
        "rrrr.....r..rrrr",
        ".........r.r....",
        "..........r.....",
    ),
    "agents": (
        "aaa......aaa",
        "aaa.k..k.aaa",
        "aaa..kk..aaa",
        "....yyyy....",
        "....yyyy....",
        "....yyyy....",
    ),
}

# Fallback icons for section headings / items with no (or an unknown) icon.
DEFAULT_ICON = "chip"
SECTION_ICONS: dict[str, str] = {
    "about": "bulb",
    "publications": "book",
    "research": "flask",
    "education": "cap",
    "experience": "briefcase",
    "projects": "controller",
    "skills": "chip",
}


def icon_names() -> list[str]:
    return sorted(_ART)


def grid(name: str) -> list[str]:
    """Return the icon as exactly ``SIZE`` rows of ``SIZE`` characters."""
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


def svg(name: str | None, fallback: str = DEFAULT_ICON) -> str:
    """Inline decorative SVG for ``name`` (unknown names use ``fallback``)."""
    key = name if name in _ART else fallback
    rows = grid(key)
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
    body = "".join(
        f'<path class="ic-{PALETTE[ch]}" d="{"".join(segs)}"/>' for ch, segs in paths.items()
    )
    return (
        '<svg class="pix" viewBox="0 0 16 16" shape-rendering="crispEdges" '
        f'aria-hidden="true" focusable="false">{body}</svg>'
    )
